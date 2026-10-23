"""Desktop regression for actual saved V5 terrain and finite chart navigation.

Uses a disposable PostgreSQL schema. Renderer instrumentation observes the
transform used by the application; no campaign or camera state is injected.
"""
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import uuid

import httpx
import psycopg
from psycopg import sql
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.store import Store

PRESETS = ('continental', 'archipelago', 'oceanic', 'arid', 'barren', 'frozen')


def transform(page):
    return page.evaluate('window.__mapTest.transform')


def covered(page):
    result = page.evaluate('''() => {
        const t=window.__mapTest.transform,c=document.querySelector('#planet-map');
        return {left:t.ox,top:t.oy,right:t.ox+t.cols*t.tile-c.clientWidth,
                bottom:t.oy+t.rows*t.tile-c.clientHeight};
    }''')
    assert result['left'] <= .1 and result['top'] <= .1, result
    assert result['right'] >= -.1 and result['bottom'] >= -.1, result


def main():
    dsn = os.environ['WOLD_TEST_DATABASE_URL']
    schema = 'browser_navigation_' + uuid.uuid4().hex
    out = Path(os.environ.get('WOLD_BROWSER_ARTIFACT_DIR', 'data/continuous-map'))
    out.mkdir(parents=True, exist_ok=True)
    server = None
    with psycopg.connect(dsn, autocommit=True) as c:
        c.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
    try:
        db = Store(dsn, schema=schema)
        for name in PRESETS:
            db.create_demo_v2('nav-'+name, seed=741903, planet_generator='planet-v5', preset=name)
        db.create_demo_v2('nav-legacy', seed=741903, planet_generator='planet-v4', preset='arid')
        db.create_pregame()
        ids = ['nav-'+p for p in PRESETS] + ['nav-legacy', 'campaign']
        hashes = {cid: db.current(cid)['snapshot']['state_hash'] for cid in ids if cid != 'campaign'}
        player = secrets.token_urlsafe(32)
        env = dict(os.environ, WOLD_DATABASE_URL=dsn, WOLD_DB_SCHEMA=schema,
                   WOLD_ACCESS_MODE='private', WOLD_GM_TOKEN=secrets.token_urlsafe(32),
                   WOLD_PLAYER_TOKEN=player, WOLD_PLAYER_CAMPAIGNS=','.join(ids))
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
        base = f'http://127.0.0.1:{port}'
        with tempfile.TemporaryDirectory() as scratch, open(Path(scratch)/'server.log', 'w') as log:
            server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app',
                                       '--host', '127.0.0.1', '--port', str(port), '--no-access-log'],
                                      env=env, stdout=log, stderr=log)
            for _ in range(100):
                try:
                    if httpx.get(base+'/api/access').status_code == 200: break
                except httpx.ConnectError:
                    pass
                time.sleep(.1)
            else:
                raise RuntimeError('Navigation server failed to start')
            with sync_playwright() as pw:
                browser = pw.chromium.launch(executable_path=shutil.which('chromium'),
                                            args=['--no-sandbox', '--disable-dev-shm-usage'])
                page = browser.new_page(viewport={'width':1440, 'height':1024})
                page.add_init_script('''
                    window.__mapInputHandlers={};
                    const add=EventTarget.prototype.addEventListener;
                    EventTarget.prototype.addEventListener=function(type,...args){
                        if(this===window||this instanceof HTMLCanvasElement&&this.id==='planet-map'){
                            const key=(this===window?'window':'map')+':'+type;
                            window.__mapInputHandlers[key]=(window.__mapInputHandlers[key]||0)+1;
                        }
                        return add.call(this,type,...args);
                    };
                ''')
                errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto(base)
                page.evaluate('''() => {
                    const renderer=window.HWMapRenderer, draw=renderer.drawPlanet;
                    renderer.drawPlanet=function(ctx,options) {
                        const t=draw(ctx,options);
                        window.__mapTest={transform:t,geometry:options.geometry,options,
                            draws:(window.__mapTest?.draws||0)+1};
                        return t;
                    };
                }''')
                page.fill('#access-token', player); page.click('#login-button')
                page.wait_for_selector('#campaign-select option[value="nav-barren"]', state='attached')
                page.locator('[data-dialog-close]').click()
                canvas = page.locator('#planet-map').element_handle()
                handlers = page.evaluate('window.__mapInputHandlers')
                timings = {}
                for name in PRESETS:
                    start = time.monotonic()
                    page.select_option('#campaign-select', 'nav-'+name)
                    page.wait_for_function('''name=>window.__mapTest?.geometry.surface.preset===name
                        &&window.__mapTest.geometry.surface.version==='planet-v5' ''', arg=name)
                    timings[name] = round((time.monotonic()-start)*1000, 1)
                    covered(page)
                    assert transform(page)['cols'] == 128 and transform(page)['rows'] == 80
                    assert transform(page)['tile'] >= max(1440/64, 1024/40)-.01, 'Expected regional initial camera'
                    assert page.locator('#zoom-reset').inner_text() == '200%'
                    page.screenshot(path=str(out/f'{name}-regional.png'))
                    for style in ['survey', 'orbital']:
                        page.select_option('#map-style', style)
                        covered(page)
                    assert canvas.evaluate('c=>c===document.querySelector("#planet-map")')

                # A central point is sufficiently far from finite chart limits:
                # pointer-anchored zoom preserves its inverse projected cell.
                page.select_option('#campaign-select', 'nav-arid')
                page.wait_for_function("window.__mapTest.geometry.surface.preset==='arid'")
                overview = page.locator('#map-overview').bounding_box()
                overview_scale = min(overview['width']/128, overview['height']/80)
                page.mouse.click(overview['x']+(overview['width']-128*overview_scale)/2+128*overview_scale*.65,
                                 overview['y']+overview['height']*.5)
                at = transform(page)
                center = page.locator('#planet-map').bounding_box()
                assert abs((center['width']/2-at['ox'])/at['tile']-128*.65) < 1
                page.locator('#map-overview-button').focus(); page.keyboard.press('Enter')
                at = transform(page)
                assert abs((center['width']/2-at['ox'])/at['tile']-64) < 1
                page.click('#map-recenter')
                before = transform(page)
                point = {'x':760, 'y':560}
                page.mouse.move(**point); page.mouse.wheel(0, -100)
                page.wait_for_timeout(100)
                after = transform(page)
                for axis, origin in [('x','ox'), ('y','oy')]:
                    a = (point[axis]-before[origin])/before['tile']
                    b = (point[axis]-after[origin])/after['tile']
                    assert abs(a-b) < .01, (axis, a, b)
                covered(page)
                page.mouse.move(760,560); page.mouse.down()
                assert page.locator('#planet-map').evaluate("c=>getComputedStyle(c).cursor") == 'grabbing'
                page.mouse.move(920,640,steps=10); page.mouse.up()
                shifted = transform(page)
                assert abs(shifted['ox']-after['ox']) > 20
                assert page.locator('#planet-map').evaluate("c=>getComputedStyle(c).cursor") == 'grab'
                page.screenshot(path=str(out/'arid-panned.png'))
                # Continued drags to all four limits cannot expose canvas backing.
                for dx,dy in [(12000,0),(-12000,0),(0,12000),(0,-12000)]:
                    page.mouse.move(760,560); page.mouse.down()
                    page.mouse.move(760+dx,560+dy,steps=4); page.mouse.up()
                    covered(page)
                page.screenshot(path=str(out/'arid-chart-limit.png'))
                page.click('#map-recenter'); covered(page)

                # Actual label target after panning/zooming uses same terrain transform.
                target = page.evaluate("window.__mapTest.transform.provinceTargets.find(t=>t.label.includes('Forge'))")
                assert target, 'Forge label not reachable after recenter'
                page.mouse.click((target['left']+target['right'])/2, (target['top']+target['bottom'])/2)
                page.wait_for_function("document.querySelector('#inspector-content').textContent.includes('Forge')")
                context = transform(page)
                selection_hint = page.locator('.map-footer span').first.inner_text()
                page.locator('#inspector-content').get_by_role('button', name='Economy', exact=True).click()
                page.wait_for_selector('.local-scope')
                page.screenshot(path=str(out/'arid-local-economy.png'))
                page.keyboard.press('Escape')
                # Labels and control obstacles may reflow as panels collapse;
                # the strategic camera and selection must remain unchanged.
                returned = transform(page)
                assert {k:returned[k] for k in ('tile','ox','oy','cols','rows')} == {
                    k:context[k] for k in ('tile','ox','oy','cols','rows')}
                assert page.locator('.map-footer span').first.inner_text() == selection_hint
                assert canvas.evaluate('c=>c===document.querySelector("#planet-map")')
                for overlay in ['provinces','population','infrastructure','military','politics','terrain']:
                    page.select_option('#overlay-select', overlay)
                    page.wait_for_function('value=>window.__mapTest.options.overlay===value', arg=overlay)
                    target = page.evaluate("window.__mapTest.transform.provinceTargets.find(t=>t.label.includes('Forge'))")
                    assert target, overlay
                    page.mouse.click((target['left']+target['right'])/2, (target['top']+target['bottom'])/2)
                    page.wait_for_function("document.querySelector('#inspector-content').textContent.includes('Forge')")
                    page.keyboard.press('Escape')
                for size in [{'width':1280,'height':720}, {'width':1920,'height':1080}]:
                    page.set_viewport_size(size); page.wait_for_timeout(100); covered(page)
                    assert page.evaluate('''()=>{
                        const frame=document.querySelector('#planet-map').getBoundingClientRect();
                        const r=document.querySelector('.force-map-controls').getBoundingClientRect();
                        const box={left:r.left-frame.left,right:r.right-frame.left,
                                   top:r.top-frame.top,bottom:r.bottom-frame.top};
                        return window.__mapTest.transform.provinceTargets.every(t=>
                            t.right<=box.left||t.left>=box.right||t.bottom<=box.top||t.top>=box.bottom);
                    }'''), 'Forces controls obscure a province label'
                page.set_viewport_size({'width':1440,'height':1024})
                page.select_option('#campaign-select', 'nav-legacy')
                page.wait_for_function("window.__mapTest.geometry.surface.version==='planet-v4'")
                covered(page)
                page.click('#zoom-reset')
                assert page.locator('#zoom-reset').inner_text() == '100%'
                target = page.evaluate("window.__mapTest.transform.provinceTargets.find(t=>t.label.includes('Forge'))")
                assert target, 'Legacy holding hidden beneath persistent chrome'
                page.mouse.click((target['left']+target['right'])/2, (target['top']+target['bottom'])/2)
                page.wait_for_function("document.querySelector('#inspector-content').textContent.includes('Forge')")
                page.keyboard.press('Escape')
                page.screenshot(path=str(out/'legacy-arid-cover.png'))
                page.select_option('#campaign-select', 'campaign')
                page.wait_for_function("document.querySelector('h1').textContent==='No recorded geography'")
                assert not errors, errors
                assert page.evaluate('window.__mapInputHandlers') == handlers, 'Map/window handlers accumulated'
                for cid, expected in hashes.items():
                    assert db.current(cid)['snapshot']['state_hash'] == expected
                result = {'result':'PASS', 'browser':browser.version, 'viewport':'desktop only',
                          'campaign_to_first_draw_ms':timings, 'page_errors':errors,
                          'checks':['six V5 presets and both styles cover viewport',
                                    'pointer zoom inverse world point invariant', 'drag and all four chart limits',
                                    'overview pointer navigation and keyboard center',
                                    'cover-relative zoom readout and reset', 'Forge label selection on every overlay',
                                    'label selection and local economy preserve camera/canvas',
                                    'desktop resize', 'legacy cover and immutable hashes',
                                    'stable canvas and map/window handler counts', 'pregame clears context']}
                (out/'navigation-metrics.json').write_text(json.dumps(result, indent=2)+'\n')
                print(json.dumps(result, indent=2)); browser.close()
    finally:
        if server:
            server.terminate(); server.wait(timeout=10)
        with psycopg.connect(dsn, autocommit=True) as c:
            c.execute(sql.SQL('DROP SCHEMA IF EXISTS {} CASCADE').format(sql.Identifier(schema)))


if __name__ == '__main__':
    main()
