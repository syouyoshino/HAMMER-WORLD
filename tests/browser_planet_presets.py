"""Actual six-preset presentation and immutable generation-choice regression."""
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
from tests.browser_strategic import province_point, descend_hierarchy

PRESETS = ('continental', 'archipelago', 'oceanic', 'arid', 'barren', 'frozen')
DRY = {'arid', 'barren', 'frozen'}


def main():
    dsn = os.environ['WOLD_TEST_DATABASE_URL']
    schema = 'browser_presets_' + uuid.uuid4().hex
    out = Path(os.environ.get('WOLD_BROWSER_ARTIFACT_DIR', 'data/planet-presets'))
    out.mkdir(parents=True, exist_ok=True)
    with psycopg.connect(dsn, autocommit=True) as c:
        c.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
    server = None
    try:
        db = Store(dsn, schema=schema)
        ids = ['preset-' + name for name in PRESETS]
        for name, cid in zip(PRESETS, ids):
            db.create_demo_v2(cid, seed=741903, planet_generator='planet-v4', preset=name)
        db.create_demo_v2('legacy-preset-check', seed=741903, planet_generator='planet-v3')
        db.create_pregame()
        ids += ['legacy-preset-check', 'campaign']
        hashes = {cid: db.current(cid)['snapshot']['state_hash'] for cid in ids if cid != 'campaign'}
        gm, player = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        env = dict(os.environ, WOLD_DATABASE_URL=dsn, WOLD_DB_SCHEMA=schema,
                   WOLD_ACCESS_MODE='private', WOLD_GM_TOKEN=gm, WOLD_PLAYER_TOKEN=player,
                   WOLD_PLAYER_CAMPAIGNS=','.join(ids))
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
        base = 'http://127.0.0.1:' + str(port)
        with tempfile.TemporaryDirectory() as scratch, open(Path(scratch)/'server.log', 'w') as log:
            server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app', '--host',
                                       '127.0.0.1', '--port', str(port), '--no-access-log'],
                                      env=env, stdout=log, stderr=log)
            for _ in range(100):
                try:
                    if httpx.get(base+'/api/access').status_code == 200: break
                except httpx.ConnectError: pass
                time.sleep(.1)
            else: raise RuntimeError('Preset browser server failed to start')
            public = {}
            for name in PRESETS:
                cid = 'preset-' + name
                response = httpx.get(base+'/api/player/campaigns/'+cid,
                                     headers={'Authorization': 'Bearer '+player})
                response.raise_for_status(); public[name] = response.json()['state']
                encoded = json.dumps(public[name])
                assert '_private' not in encoded and 'planet_presets' not in encoded and 'seed' not in encoded
                assert len(public[name]['geography']) == 1
                geo = next(iter(public[name]['geography'].values()))
                assert geo['surface']['version'] == 'planet-v4'
                assert geo['surface']['preset'] == name
                assert geo['surface']['hydrology'] == ('none' if name in DRY else 'ocean-draining')
                if name in DRY:
                    assert geo['surface']['rivers'] == []
                    assert all(t['terrain'] not in ('ocean','coast','forest','marsh') for t in geo['tiles'])
            with sync_playwright() as pw:
                browser = pw.chromium.launch(executable_path=shutil.which('chromium'),
                                            args=['--no-sandbox', '--disable-dev-shm-usage'])
                page = browser.new_page(viewport={'width':1440,'height':1024})
                errors, requests, captures = [], [], []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.on('request', lambda r: requests.append(r.url))
                page.goto(base); page.fill('#access-token', player); page.click('#login-button')
                page.wait_for_selector('#campaign-select option[value="preset-barren"]', state='attached')
                page.locator('[data-dialog-close]').click()
                canvas = page.locator('#planet-map').element_handle()
                for name in PRESETS:
                    page.select_option('#campaign-select', 'preset-'+name)
                    page.wait_for_function("name=>document.querySelector('#map-coordinates').textContent.toLowerCase().includes(name)", arg=name)
                    page.wait_for_selector('.toast', state='hidden', timeout=10000)
                    for mode in ['light','dark']:
                        page.click('#hw-command'); page.select_option('#appearance-select', mode); page.click('#hw-command')
                        for style in ['orbital','survey']:
                            page.select_option('#map-style', style)
                            legend = page.locator('#map-legend').inner_text().lower()
                            if name in DRY:
                                assert not any(word in legend for word in ['open water','coastal','forest','marsh']), (name, legend)
                            path = out/f'{name}-{mode}-{style}.png'
                            page.screenshot(path=str(path)); captures.append(path.name)
                    page.select_option('#map-style', 'orbital')
                    pixels = page.locator('#planet-map').evaluate('c=>c.toDataURL()')
                    count = len(requests)
                    for mode in ['light','dark','system']:
                        page.click('#hw-command'); page.select_option('#appearance-select', mode); page.click('#hw-command')
                        assert page.locator('#planet-map').evaluate('c=>c.toDataURL()') == pixels
                    assert len(requests) == count
                    state = public[name]
                    geo = next(iter(state['geography'].values()))
                    forge = next(s for s in state['settlements'] if s['name'] == 'Forge')
                    land = [t for t in geo['tiles'] if t['province_id'] == forge['province_id'] and t['terrain'] != 'ocean']
                    selected = False
                    for tile in land[:16]:
                        page.keyboard.press('Escape')
                        point = province_point(page, dict(x=tile['x'], y=tile['y'], width=1, height=1))
                        page.mouse.click(point['x'], point['y'])
                        if 'Forge' in page.locator('#inspector-content').inner_text():
                            selected = True; break
                    assert selected, name
                    page.screenshot(path=str(out/f'{name}-selection.png'))
                    page.keyboard.press('Escape')
                    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
                    for selector in ['#map-level','#map-style','#zoom-in','#zoom-out','#zoom-reset']:
                        assert page.locator(selector).evaluate('e=>{const r=e.getBoundingClientRect();return r.x>=0&&r.right<=innerWidth&&r.y>=0&&r.bottom<=innerHeight}')
                    if name in ('barren','archipelago'):
                        page.select_option('#map-level','system')
                        page.wait_for_function("document.querySelector('#map-coordinates').textContent.startsWith('SYSTEM CHART')")
                        page.screenshot(path=str(out/f'{name}-desktop-system.png'))
                        descend_hierarchy(page, ['Hearth','Cinder','Reach'])
                        page.wait_for_function("name=>document.querySelector('#map-coordinates').textContent.toLowerCase().includes(name)", arg=name)
                    assert canvas.evaluate('c=>c===document.querySelector("#planet-map")')
                page.select_option('#campaign-select','legacy-preset-check')
                page.wait_for_function("document.querySelector('#map-coordinates').textContent.includes('PLANET-V3')")
                page.screenshot(path=str(out/'legacy-v3.png'))
                page.select_option('#campaign-select','campaign')
                page.wait_for_function("document.querySelector('h1').textContent==='No recorded geography'")
                assert page.locator('#map-style').is_disabled()
                assert not errors, errors
                for cid, expected in hashes.items():
                    assert db.current(cid)['snapshot']['state_hash'] == expected
                result = {'result':'PASS','browser':browser.version,'presets':list(PRESETS),
                          'captures':captures,'page_errors':errors,'checks':[
                              'six distinct recorded generation presets in both styles and themes',
                              'dry public geography and legends contain no water or vegetation',
                              'surveyed-only preset metadata; no seeds/private mapping',
                              'UI themes preserve canvas pixels and make zero requests',
                              'real public land-tile selection reaches Forge on every preset',
                              'desktop controls/actual marker hierarchy and retained canvas',
                              'legacy V3 remains readable; unknown campaign clears context',
                              'all source snapshot hashes unchanged'],
                          'source_hashes':{str(p):hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in [Path('public/map-renderer.js'),Path('public/app.js'),Path('app/planet_generation.py')]}}
                (out/'metrics.json').write_text(json.dumps(result,indent=2)); browser.close()
    finally:
        if server:
            server.terminate(); server.wait(timeout=10)
        with psycopg.connect(dsn, autocommit=True) as c:
            c.execute(sql.SQL('DROP SCHEMA IF EXISTS {} CASCADE').format(sql.Identifier(schema)))


if __name__ == '__main__': main()
