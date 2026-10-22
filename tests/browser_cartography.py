"""Generated/legacy geography, four-level navigation and presentation regression."""
import hashlib
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
from tests.browser_strategic import descend_hierarchy


def main():
    dsn = os.environ['WOLD_TEST_DATABASE_URL']
    schema = 'browser_cartography_' + uuid.uuid4().hex
    out = Path(os.environ.get('WOLD_BROWSER_ARTIFACT_DIR', 'data/map-release'))
    out.mkdir(parents=True, exist_ok=True)
    with psycopg.connect(dsn, autocommit=True) as c:
        c.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
    server = None
    try:
        db = Store(dsn, schema=schema)
        for cid, version in [('map-v3-demo','planet-v3'),('legacy-demo','planet-v1')]:
            db.create_demo_v2(cid, seed=741903, planet_generator=version)
            proposal = db.packet(cid)['example']
            proposal['orders']['actions'] = [{'type':'recruit','settlement_id':cid+'-forge'}]*2
            db.commit(cid, proposal)
        db.create_pregame()
        gm, player = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        env = dict(os.environ, WOLD_DATABASE_URL=dsn, WOLD_DB_SCHEMA=schema, WOLD_ACCESS_MODE='private',
                   WOLD_GM_TOKEN=gm, WOLD_PLAYER_TOKEN=player,
                   WOLD_PLAYER_CAMPAIGNS='map-v3-demo,legacy-demo,campaign')
        originals = {cid:db.current(cid)['snapshot']['state_hash'] for cid in ['map-v3-demo','legacy-demo']}
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0))
            base = 'http://127.0.0.1:' + str(sock.getsockname()[1])
        with tempfile.TemporaryDirectory() as scratch, open(Path(scratch)/'server.log','w') as log:
            server = subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1',
                                       '--port',base.rsplit(':',1)[1],'--no-access-log'],env=env,stdout=log,stderr=log)
            for _ in range(100):
                try:
                    if httpx.get(base+'/api/access').status_code == 200:
                        break
                except httpx.ConnectError:
                    pass
                time.sleep(.1)
            else:
                raise RuntimeError('Cartography QA server failed to start')
            headers = {'Authorization':'Bearer '+player}
            public = httpx.get(base+'/api/player/campaigns/map-v3-demo',headers=headers).json()
            assert len(public['state']['geography']) == 1
            assert '_private' not in json.dumps(public) and 'seed' not in json.dumps(public)
            geo = next(iter(public['state']['geography'].values()))
            assert geo['surface']['version'] == 'planet-v3'
            with sync_playwright() as pw:
                browser = pw.chromium.launch(executable_path=shutil.which('chromium'),
                                            args=['--no-sandbox','--disable-dev-shm-usage'])
                page = browser.new_page(viewport={'width':1440,'height':1024},has_touch=True)
                errors, requests = [], []
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.on('request',lambda r:requests.append(r.url))
                page.goto(base)
                page.fill('#access-token',player)
                page.click('#login-button')
                page.wait_for_function("document.querySelectorAll('#campaign-select option').length===4")
                page.locator('[data-dialog-close]').click()
                page.select_option('#campaign-select','map-v3-demo')
                page.wait_for_function("document.querySelector('#command-turn').textContent==='TURN 1'")
                canvas = page.locator('#planet-map').element_handle()
                for mode in ['light','dark']:
                    page.click('#hw-command');page.select_option('#appearance-select',mode);page.click('#hw-command')
                    for level in ['galactic','sector','system','planet']:
                        page.select_option('#map-level',level)
                        page.wait_for_function("x=>document.querySelector('#map-coordinates').textContent.startsWith(x.toUpperCase()+' ')",arg=level)
                        page.screenshot(path=str(out/f'{mode}-{level}.png'))
                descend_hierarchy(page,['Hearth','Cinder','Reach'])
                page.select_option('#map-style','orbital')
                orbital = page.locator('#planet-map').evaluate('c=>c.toDataURL()')
                request_count = len(requests)
                page.select_option('#map-style','survey')
                survey = page.locator('#planet-map').evaluate('c=>c.toDataURL()')
                assert survey != orbital
                page.screenshot(path=str(out/'survey.png'))
                page.select_option('#map-style','orbital')
                assert page.locator('#planet-map').evaluate('c=>c.toDataURL()') == orbital
                for mode in ['light','dark','system']:
                    page.click('#hw-command');page.select_option('#appearance-select',mode);page.click('#hw-command')
                    assert page.locator('#planet-map').evaluate('c=>c.toDataURL()') == orbital
                assert len(requests) == request_count
                cdp = page.context.new_cdp_session(page)
                cdp.send('HeapProfiler.collectGarbage')
                before = cdp.send('Memory.getDOMCounters')
                started = time.monotonic()
                for _ in range(12):
                    page.select_option('#map-style','survey')
                    page.select_option('#map-style','orbital')
                style_ms = (time.monotonic()-started)*1000/24
                cdp.send('HeapProfiler.collectGarbage')
                after = cdp.send('Memory.getDOMCounters')
                assert after['jsEventListeners'] <= before['jsEventListeners']
                assert canvas.evaluate('c=>c===document.querySelector("#planet-map")')
                page.get_by_role('button',name='Forces',exact=True).click()
                page.wait_for_selector('.force-counter.own')
                page.locator('.force-counter.own').click()
                assert page.locator('.force-stack-row').count() == 2
                page.get_by_role('button',name='Close force list',exact=True).click()
                page.set_viewport_size({'width':390,'height':844})
                page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
                for selector in ['#map-level','#map-style','#overlay-select','#zoom-in','#zoom-out','#zoom-reset']:
                    assert page.locator(selector).is_visible()
                    assert page.locator(selector).evaluate('e=>{const r=e.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth&&r.top>=0&&r.bottom<=innerHeight;}'),selector
                page.locator('.force-counter.own').tap()
                assert page.locator('.force-stack-row').count() == 2
                page.get_by_role('button',name='Close force list',exact=True).tap()
                page.screenshot(path=str(out/'phone.png'))
                assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
                page.set_viewport_size({'width':1440,'height':1024})
                page.select_option('#campaign-select','legacy-demo')
                page.wait_for_function("document.querySelector('#map-coordinates').textContent.includes('PLANET')")
                page.wait_for_load_state('networkidle')
                page.screenshot(path=str(out/'legacy.png'))
                legacy = httpx.get(base+'/api/player/campaigns/legacy-demo',headers=headers).json()
                assert all('surface' not in g for g in legacy['state']['geography'].values())
                page.select_option('#campaign-select','campaign')
                page.wait_for_function("document.querySelector('#command-turn').textContent==='TURN —'")
                page.wait_for_function("document.querySelector('h1').textContent==='No recorded geography'")
                assert page.locator('.force-counter').count() == 0
                assert 'No recorded geography' in page.locator('h1').inner_text()
                assert not errors,errors
                for cid,state_hash in originals.items():
                    assert db.current(cid)['snapshot']['state_hash'] == state_hash
                (out/'metrics.json').write_text(json.dumps({'result':'PASS','browser':browser.version,
                    'surface_version':'planet-v3','style_action_mean_ms':round(style_ms,2),
                    'cdp_before':before,'cdp_after':after,'page_errors':errors,
                    'checks':['four map levels/two modes','actual marker descent','different deterministic map styles',
                              'UI-only theme with zero requests and stable pixels','24 style changes bounded handlers',
                              'same canvas','generated ground stack','phone controls/touch stack',
                              'legacy geography unchanged','unknown campaign clearing','snapshot hashes unchanged']},indent=2))
                browser.close()
    finally:
        if server:
            server.terminate();server.wait(timeout=10)
        with psycopg.connect(dsn,autocommit=True) as c:
            c.execute(sql.SQL('DROP SCHEMA IF EXISTS {} CASCADE').format(sql.Identifier(schema)))


if __name__ == '__main__':
    main()
