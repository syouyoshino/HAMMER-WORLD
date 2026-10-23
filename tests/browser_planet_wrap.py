"""Real desktop cylindrical-map navigation and protected seam-order regression."""
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


def current(page):
    return page.evaluate('''() => {
        const t=window.__wrapTest.t,c=document.querySelector('#planet-map');
        return {tile:t.tile,ox:t.ox,oy:t.oy,cols:t.cols,rows:t.rows,
                width:c.clientWidth,height:c.clientHeight};
    }''')


def circular_error(a, b, period=128):
    return abs((a-b+period/2) % period-period/2)


def covered(page):
    assert page.evaluate('''() => {
        const c=document.querySelector('#planet-map'),blits=window.__wrapTest.blits;
        return [0,c.clientWidth/2,c.clientWidth-.01].every(x=>
            [0,c.clientHeight-.01].every(y=>blits.some(b=>
                x>=b.x-.01&&x<=b.x+b.w+.01&&y>=b.y-.01&&y<=b.y+b.h+.01)));
    }'''), 'Saved-world raster copies do not cover viewport'


def overview_at(page, x, y):
    box = page.locator('#map-overview').bounding_box()
    scale = min(box['width']/128, box['height']/80)
    page.mouse.click(box['x']+(box['width']-128*scale)/2+x*scale,
                     box['y']+(box['height']-80*scale)/2+y*scale)


def label_click(page, label):
    target = page.evaluate('''label=>window.__wrapTest.t.provinceTargets.find(t=>t.label===label)''', label)
    assert target, 'No reachable label for '+label
    page.mouse.click((target['left']+target['right'])/2, (target['top']+target['bottom'])/2)
    try:
        page.wait_for_function('label=>document.querySelector("#inspector-content").textContent.includes(label)', arg=label)
    except Exception:
        diagnostic = page.evaluate("""target=>{
            const x=(target.left+target.right)/2,y=(target.top+target.bottom)/2,
                  hit=document.elementFromPoint(x,y),t=window.__wrapTest;
            return {target,hit:hit?.tagName+'#'+hit?.id,overlay:t.options.overlay,
                safe:t.options.safe,canvas:document.querySelector('#planet-map').getBoundingClientRect().toJSON(),
                selected:document.querySelector('.map-footer').textContent};
        }""", target)
        print('Failed label click:', json.dumps(diagnostic), flush=True)
        out = Path(os.environ.get('WOLD_BROWSER_ARTIFACT_DIR','data/planet-wrap'))
        page.screenshot(path=str(out/'failed-label-click.png'))
        raise


def route_short(page):
    lengths = page.locator('.force-route').evaluate_all('''lines=>lines.map(line=>{
        if(line.tagName.toLowerCase()==='line')return Math.abs(+line.getAttribute('x2')-line.getAttribute('x1'));
        return line.getBBox().width;
    })''')
    assert lengths, 'No recorded connector rendered'
    assert max(lengths) <= current(page)['tile']*64+.1, lengths


def command(page, view):
    page.click('#hw-command')
    page.click(f'#command-menu [data-open={view}]')


def force_controls_clear(page, has_route=False):
    toggle = page.get_by_role('button', name='Forces', exact=True)
    if not page.locator('.force-map-hint').inner_text():
        assert not page.locator('.force-map-hint').is_visible(), 'Empty Forces status creates an unexplained mark'
    toggle.hover()
    ratio = toggle.evaluate(r'''button=>{
        const style=getComputedStyle(button), luminance=color=>{
            const rgb=color.match(/[\d.]+/g).slice(0,3).map(Number).map(v=>{
                v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4;
            });return rgb[0]*.2126+rgb[1]*.7152+rgb[2]*.0722;
        },a=luminance(style.color),b=luminance(style.backgroundColor);
        return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);
    }''')
    assert ratio >= 4.5, ('Active Forces hover loses text contrast', ratio)
    if not has_route:
        return
    legend = page.locator('.force-map-legend').bounding_box()
    overview = page.locator('#map-overview-button').bounding_box()
    assert legend and overview
    assert (legend['x']+legend['width']<=overview['x'] or overview['x']+overview['width']<=legend['x']
            or legend['y']+legend['height']<=overview['y'] or overview['y']+overview['height']<=legend['y'])


def main():
    dsn = os.environ['WOLD_TEST_DATABASE_URL']
    version = os.environ.get('WOLD_TEST_PLANET_GENERATOR', 'planet-v6')
    assert version in ('planet-v6', 'planet-v7', 'planet-v8')
    schema = 'browser_wrap_' + uuid.uuid4().hex
    out = Path(os.environ.get('WOLD_BROWSER_ARTIFACT_DIR', 'data/planet-wrap'))
    out.mkdir(parents=True, exist_ok=True)
    server = None
    with psycopg.connect(dsn, autocommit=True) as c:
        c.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
    try:
        db = Store(dsn, schema=schema)
        def create(cid, preset):
            geology = {'geology':'cratered' if preset in ('arid','barren','frozen') else 'none'} if version in ('planet-v7','planet-v8') else {}
            materials = {}
            if version == 'planet-v8':
                material = 'hydrocarbon' if preset == 'frozen' else 'lava' if preset in ('arid','barren') else 'water'
                materials = {'lake_material':material, 'polar_caps':'none' if material=='lava' else 'water-ice'}
            db.create_demo_v2(cid, seed=741903, planet_generator=version, preset=preset, **geology, **materials)
        for name in PRESETS:
            create('wrap-'+name, name)
        db.create_demo_v2('wrap-old', seed=741903, planet_generator='planet-v5', preset='arid')
        create('wrap-military', 'barren')
        # Real supported recruitment produces two owned forces before the UI
        # drafts/previews/commits one seam deployment. No state rows are patched.
        proposal = db.packet('wrap-military')['example']
        proposal['submission_id'] = 'wrap-recruit-fixture'
        proposal['orders']['actions'] = [{'type':'recruit', 'settlement_id':'wrap-military-forge'}]*2
        db.commit('wrap-military', proposal)
        proposal = db.packet('wrap-military')['example']
        proposal['submission_id'] = 'wrap-age-fixture'
        proposal['orders']['actions'] = []
        db.commit('wrap-military', proposal)
        db.create_pregame()
        ids = ['wrap-'+p for p in PRESETS]+['wrap-old','wrap-military','campaign']
        hashes = {cid:db.current(cid)['snapshot']['state_hash'] for cid in ids if cid!='campaign'}
        gm, player = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        env = dict(os.environ, WOLD_DATABASE_URL=dsn, WOLD_DB_SCHEMA=schema,
                   WOLD_ACCESS_MODE='private', WOLD_GM_TOKEN=gm, WOLD_PLAYER_TOKEN=player,
                   WOLD_PLAYER_CAMPAIGNS=','.join(ids))
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
        base = f'http://127.0.0.1:{port}'
        with tempfile.TemporaryDirectory() as scratch, open(Path(scratch)/'server.log','w') as log:
            server = subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host',
                '127.0.0.1','--port',str(port),'--no-access-log'],env=env,stdout=log,stderr=log)
            for _ in range(100):
                try:
                    if httpx.get(base+'/api/access').status_code==200: break
                except httpx.ConnectError: pass
                time.sleep(.1)
            else: raise RuntimeError('Wrap QA server failed to start')
            with sync_playwright() as pw:
                browser = pw.chromium.launch(executable_path=shutil.which('chromium'),
                    args=['--no-sandbox','--disable-dev-shm-usage'])
                page = browser.new_page(viewport={'width':1440,'height':1024})
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
                errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(base)
                page.evaluate('''() => {
                    const renderer=window.HWMapRenderer,old=renderer.drawPlanet;
                    renderer.drawPlanet=function(ctx,options){
                        const original=ctx.drawImage,blits=[];
                        ctx.drawImage=function(image,...a){
                            if(a.length===4)blits.push({x:a[0],y:a[1],w:a[2],h:a[3]});
                            if(a.length===8)blits.push({x:a[4],y:a[5],w:a[6],h:a[7]});
                            return original.call(ctx,image,...a);
                        };
                        try{const t=old(ctx,options);window.__wrapTest={t,options,blits};return t;}
                        finally{ctx.drawImage=original;}
                    };
                }''')
                page.fill('#access-token',player);page.click('#login-button')
                page.wait_for_selector('#campaign-select option[value="wrap-barren"]',state='attached')
                page.locator('[data-dialog-close]').click()
                canvas=page.locator('#planet-map').element_handle()
                handlers=page.evaluate('window.__mapInputHandlers')
                timings={}
                for name in PRESETS:
                    started=time.monotonic();page.select_option('#campaign-select','wrap-'+name)
                    page.wait_for_function('''({name,version})=>window.__wrapTest?.options.geometry.surface.version===version
                        &&window.__wrapTest.options.geometry.surface.preset===name''',arg={'name':name,'version':version})
                    timings[name]=round((time.monotonic()-started)*1000,1)
                    covered(page)
                    if version == 'planet-v8':
                        materials = page.evaluate('window.__wrapTest.options.geometry.surface.materials')
                        assert len(materials['lake_mask']) == 10240 and '1' in materials['lake_mask']
                        legend = page.locator('#map-legend').inner_text()
                        expected = {'water':'Water lakes','lava':'Lava lakes','hydrocarbon':'Hydrocarbon lakes'}
                        assert expected[materials['lake_material']] in legend, legend
                        assert ('Polar water ice' in legend) == (materials['polar_caps'] == 'water-ice'), legend
                    page.screenshot(path=str(out/f'{name}-regional.png'))
                    for style in ['survey','orbital']:
                        page.select_option('#map-style',style)
                        for dx in (3200,-4700,2100):
                            before=current(page)
                            q=(760-before['ox'])/before['tile']
                            page.mouse.move(760,560);page.mouse.down()
                            page.mouse.move(760+dx,560,steps=10);page.mouse.up()
                            after=current(page)
                            assert circular_error((760-after['ox'])/after['tile'],q-dx/before['tile'])<.02
                            covered(page)
                    assert canvas.evaluate('c=>c===document.querySelector("#planet-map")')
                page.select_option('#campaign-select','wrap-barren')
                page.wait_for_function("window.__wrapTest.options.geometry.surface.preset==='barren'")
                overview_at(page,.5,40)
                page.screenshot(path=str(out/'barren-seam.png'))
                before=current(page)
                point={'x':760,'y':560}
                page.mouse.move(**point);page.mouse.wheel(0,-100);page.wait_for_timeout(100)
                after=current(page)
                assert circular_error((point['x']-before['ox'])/before['tile'],
                    (point['x']-after['ox'])/after['tile'])<.02
                assert abs((point['y']-before['oy'])/before['tile']-
                    (point['y']-after['oy'])/after['tile'])<.02
                # Adjacent cells on opposite sides of the canonical seam must
                # select different, correct canonical province IDs.
                for x,expected in [(127.5,'Province 24'),(.5,'Province 17')]:
                    t=current(page);cx=(t['width']/2-t['ox'])/t['tile']
                    sx=t['width']/2+((x-cx+64)%128-64)*t['tile']
                    sy=t['oy']+40.5*t['tile']
                    page.mouse.click(sx,sy)
                    page.wait_for_function('name=>document.querySelector(".map-footer").textContent.includes(name)',arg=expected)
                    page.keyboard.press('Escape')
                for overlay in ['provinces','population','infrastructure','military','politics','terrain']:
                    page.select_option('#overlay-select',overlay)
                    page.wait_for_function('v=>window.__wrapTest.options.overlay===v',arg=overlay)
                    overview_at(page,8,8)
                    label_click(page,'Forge');page.keyboard.press('Escape')
                selected=page.locator('.map-footer span').first.inner_text()
                context=current(page)
                command(page,'economy');page.wait_for_selector('.local-scope')
                page.locator('.workspace-tabs').get_by_role('button',name='Construction',exact=True).click()
                page.wait_for_selector('.local-construction')
                page.locator('[data-return-map]').click()
                assert current(page)==context
                assert page.locator('.map-footer span').first.inner_text()==selected
                page.screenshot(path=str(out/'barren-return.png'))
                pixels=page.locator('#planet-map').evaluate('c=>c.toDataURL()')
                for mode in ['dark','light']:
                    page.click('#hw-command');page.select_option('#appearance-select',mode);page.click('#hw-command')
                    assert page.locator('#planet-map').evaluate('c=>c.toDataURL()')==pixels
                for size in [{'width':1280,'height':720},{'width':1920,'height':1080}]:
                    page.set_viewport_size(size);page.wait_for_timeout(100);covered(page)
                page.set_viewport_size({'width':1440,'height':1024})

                page.select_option('#campaign-select','wrap-military')
                page.wait_for_function("window.__wrapTest.options.geometry.planet.id.startsWith('wrap-military')")
                page.get_by_role('button',name='Forces',exact=True).click()
                page.wait_for_selector('.force-counter.own')
                page.locator('.force-counter.own').click()
                force_controls_clear(page)
                page.locator('.force-stack-row').first.get_by_role('button',name='Move',exact=True).click()
                state=db.current('wrap-military')['snapshot']['state']
                target=next(p['id'] for p in state['geography']['wrap-military-planet-reach']['provinces']
                            if p['x']==112 and p['y']==0)
                page.get_by_label('Destination province',exact=True).select_option(target)
                page.get_by_label('Supply source',exact=True).select_option('wrap-military-forge')
                page.get_by_role('button',name='Stage movement',exact=True).click()
                page.locator('[data-return-map]').click()
                route_short(page)
                page.screenshot(path=str(out/'seam-draft.png'))
                command(page,'orders')
                packet=db.packet('wrap-military')['example'];packet['submission_id']='wrap-browser-order'
                packet['orders']['actions']=[]
                if not page.locator('#proposal-json').is_visible():
                    page.locator('#proposal-json').locator('xpath=ancestor::details[1]/summary').click()
                page.fill('#proposal-json',json.dumps(packet));page.fill('#gm-token',gm)
                page.get_by_role('button',name='Build proposal from GM packet',exact=True).click()
                built=json.loads(page.locator('#proposal-json').input_value())
                assert built['orders']['actions'][0]['destination_province_id']==target
                page.click('#preview-order')
                page.wait_for_function("document.querySelector('#order-status').textContent.startsWith('Preview validated')")
                page.locator('[data-return-map]').click();route_short(page)
                page.screenshot(path=str(out/'seam-preview.png'))
                command(page,'orders');page.click('#commit-order')
                page.wait_for_function("document.querySelector('#command-turn').textContent==='TURN 3'")
                page.locator('[data-return-map]').click()
                # A horizontal SVG line has zero geometric height; Playwright's
                # visibility predicate is unsuitable for a stroked connector.
                page.wait_for_selector('.force-route:not(.draft):not(.preview)',state='attached')
                assert page.locator('.force-map-layer').is_visible()
                route_short(page)
                force_controls_clear(page, has_route=True)
                page.screenshot(path=str(out/'seam-transit.png'))
                assert len(db.history('wrap-military')[0])==4
                live_hash=db.current('wrap-military')['snapshot']['state_hash']
                command(page,'history')
                page.get_by_role('button',name='Inspect turn 0',exact=True).click()
                page.wait_for_function("!document.querySelector('#historical-badge').hidden")
                page.wait_for_function("version=>window.__wrapTest.options.geometry.surface.version===version",arg=version)
                page.wait_for_selector('#map-overview')
                page.wait_for_function("version=>window.__wrapTest.options.geometry.surface.version===version",arg=version)
                overview_at(page,.5,40);covered(page)
                page.screenshot(path=str(out/'seam-historical.png'))
                command(page,'orders')
                page.wait_for_function("document.querySelector('#orders-panel').textContent.includes('Return to the live campaign revision')")
                commit=page.locator('#commit-order')
                assert commit.count()==0 or commit.is_disabled()
                command(page,'history')
                page.get_by_role('button',name='Return to live',exact=True).click()
                page.wait_for_function("document.querySelector('#historical-badge').hidden&&document.querySelector('#command-turn').textContent==='TURN 3'")
                assert db.current('wrap-military')['snapshot']['state_hash']==live_hash
                for cid,expected in hashes.items():
                    if cid!='wrap-military':assert db.current(cid)['snapshot']['state_hash']==expected
                assert page.evaluate('window.__mapInputHandlers')==handlers
                assert not errors,errors
                result={'result':'PASS','generator':version,'browser':browser.version,'viewport':'desktop only',
                    'campaign_to_first_draw_ms':timings,'page_errors':errors,'checks':[
                        'six periodic presets/both styles across repeated east/west crossings',
                        'saved raster covers viewport through seam', 'pointer zoom modulo canonical longitude',
                        'canonical seam-cell and holding selection on every overlay',
                        'management camera/selection return; theme pixels; desktop resize',
                        'real DRAFT/PREVIEW/commit short seam connectors with canonical orders',
                        'historical wrapped map remains read only and returns to live',
                        'immutable source fixtures; stable canvas/window handlers']}
                (out/'wrap-metrics.json').write_text(json.dumps(result,indent=2)+'\n')
                print(json.dumps(result,indent=2));browser.close()
    finally:
        if server:server.terminate();server.wait(timeout=10)
        with psycopg.connect(dsn,autocommit=True) as c:
            c.execute(sql.SQL('DROP SCHEMA IF EXISTS {} CASCADE').format(sql.Identifier(schema)))


if __name__=='__main__':main()
