"""Real movement drafting/authority regression on a disposable PostgreSQL fixture."""
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
from app.engine_v2 import ALLOCATIONS
from tests.browser_strategic import descend_hierarchy, click_map_marker


def main():
    dsn = os.environ['WOLD_TEST_DATABASE_URL']
    schema = 'browser_movement_' + uuid.uuid4().hex
    out = Path(os.environ.get('WOLD_BROWSER_ARTIFACT_DIR', 'data/movement-candidate'))
    out.mkdir(parents=True, exist_ok=True)
    with psycopg.connect(dsn, autocommit=True) as c:
        c.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
    server = None
    try:
        db = Store(dsn, schema=schema)
        db.create_demo_v2()
        db.create_pregame()
        proposal = db.packet('demo-v2')['example']
        proposal['orders']['actions'] = [{'type':'recruit', 'settlement_id':'demo-v2-forge'}] * 2
        db.commit('demo-v2', proposal)
        original = db.current('demo-v2')['snapshot']
        unit = next(u for u in original['state']['units'] if u['owner'] == 'player')
        enemy = next(u for u in original['state']['units'] if u['owner'] == 'enemy')
        gm, player = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        env = dict(os.environ, WOLD_DATABASE_URL=dsn, WOLD_DB_SCHEMA=schema,
                   WOLD_ACCESS_MODE='private', WOLD_GM_TOKEN=gm,
                   WOLD_PLAYER_TOKEN=player, WOLD_PLAYER_CAMPAIGNS='demo-v2,campaign')
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        base = f'http://127.0.0.1:{port}'
        with tempfile.TemporaryDirectory() as scratch, open(Path(scratch)/'server.log', 'w') as log:
            server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app',
                                       '--host', '127.0.0.1', '--port', str(port), '--no-access-log'],
                                      env=env, stdout=log, stderr=log)
            for _ in range(100):
                try:
                    if httpx.get(base+'/api/access').status_code == 200:
                        break
                except httpx.ConnectError:
                    pass
                time.sleep(.1)
            else:
                raise RuntimeError('Movement QA server failed to start')
            with sync_playwright() as pw:
                browser = pw.chromium.launch(executable_path=shutil.which('chromium'),
                                            args=['--no-sandbox', '--disable-dev-shm-usage'])
                page = browser.new_page(viewport={'width':1280, 'height':900}, has_touch=True)
                errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto(base)
                page.fill('#access-token', player)
                page.click('#login-button')
                page.wait_for_function("document.querySelectorAll('#campaign-select option').length===3")
                page.locator('[data-dialog-close]').click()
                page.select_option('#campaign-select', 'demo-v2')
                page.wait_for_function("document.querySelector('#command-turn').textContent==='TURN 1'")
                descend_hierarchy(page, ['Hearth', 'Cinder', 'Reach'])
                canvas = page.locator('#planet-map').element_handle()
                page.get_by_role('button', name='Forces', exact=True).click()
                page.wait_for_selector('.force-counter.own')
                assert page.locator('.force-counter.own b').inner_text() == '2'
                assert page.locator('.force-counter.observed').count() == 1
                page.locator('.force-counter.own').click()
                assert page.locator('.force-stack-row').count() == 2
                page.screenshot(path=str(out/'ground-stack.png'))
                page.get_by_role('button', name='Close force list', exact=True).click()
                page.set_viewport_size({'width':390,'height':844})
                page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
                owned = page.locator('.force-counter.own').bounding_box()
                observed = page.locator('.force-counter.observed').bounding_box()
                assert owned['height'] >= 44 and observed['height'] >= 44
                assert (owned['x']+owned['width']+7 <= observed['x'] or observed['x']+observed['width']+7 <= owned['x'] or
                        owned['y']+owned['height']+7 <= observed['y'] or observed['y']+observed['height']+7 <= owned['y']), (owned, observed)
                for selector, count in [('.force-counter.own',2),('.force-counter.observed',1)]:
                    page.locator(selector).tap()
                    assert page.locator('.force-stack-row').count() == count
                    page.get_by_role('button', name='Close force list', exact=True).tap()
                page.screenshot(path=str(out/'ground-phone.png'))
                page.set_viewport_size({'width':1280,'height':900})
                page.locator('.force-counter.own').click()
                page.locator('.force-stack-row').first.get_by_role('button', name='Move', exact=True).click()
                page.locator('.order-source summary').click()
                page.fill('#proposal-json', '{unsent draft')
                page.get_by_label('Destination province', exact=True).select_option(enemy['location_id'])
                page.get_by_label('Supply source', exact=True).select_option('demo-v2-forge')
                page.get_by_role('button', name='Stage movement', exact=True).click()
                assert page.locator('#proposal-json').input_value() == '{unsent draft'
                page.fill('#proposal-json', '')
                assert page.locator('.movement-request-list li').count() == 1
                with page.expect_download() as download:
                    page.get_by_role('button', name='Export movement requests', exact=True).click()
                request = json.loads(Path(download.value.path()).read_text())
                assert len(request['requests']) == 1 and 'base_hash' not in request
                page.get_by_role('button', name='Build proposal from GM packet', exact=True).click()
                page.wait_for_function("document.querySelector('.toast')?.textContent.includes('GM packet required')")
                assert page.locator('#proposal-json').input_value() == ''
                # Invalid unsent text survives failed insertion, then append to a real packet.
                page.fill('#proposal-json', '{invalid draft')
                page.get_by_role('button', name='Build proposal from GM packet', exact=True).click()
                assert page.locator('#proposal-json').input_value() == '{invalid draft'
                malformed = '{"orders":{"actions":[null]}}'
                page.fill('#proposal-json', malformed)
                page.get_by_role('button', name='Build proposal from GM packet', exact=True).click()
                assert page.locator('#proposal-json').input_value() == malformed
                packet = db.packet('demo-v2')['example']
                packet['submission_id'] = 'browser-movement-' + uuid.uuid4().hex
                packet['narrative'] = 'Preserved narrative'
                packet['orders']['allocations'] = [{'settlement_id':'demo-v2-forge', **{k:0 for k in ALLOCATIONS}, 'farmers':300}]
                packet['orders']['actions'] = [{'type':'build','settlement_id':'demo-v2-forge','facility_kind':'farm'}]
                page.fill('#proposal-json', json.dumps(packet))
                page.fill('#gm-token', gm)
                page.click('#preview-order')
                page.wait_for_function("document.querySelector('#order-status').textContent.startsWith('Preview validated')")
                page.locator('[data-return-map]').click()
                assert page.locator('.force-route.draft').count() == 1
                assert page.locator('.force-route.preview').count() == 0
                page.click('#hw-command')
                page.locator('#command-menu [data-open=orders]').click()
                page.get_by_role('button', name='Build proposal from GM packet', exact=True).click()
                assert page.locator('.movement-request-list li').count() == 0
                built = json.loads(page.locator('#proposal-json').input_value())
                assert built['narrative'] == packet['narrative']
                assert built['orders']['allocations'] == packet['orders']['allocations']
                assert built['orders']['actions'][0] == packet['orders']['actions'][0]
                assert built['orders']['actions'][1] == request['requests'][0]
                page.fill('#gm-token', player)
                page.click('#preview-order')
                page.wait_for_function("document.querySelector('#order-status').textContent.startsWith('Preview failed')")
                assert page.locator('#commit-order').is_disabled()
                page.fill('#gm-token', gm)
                # A response to earlier text cannot validate text edited while pending.
                held = []
                page.route('**/api/admin/campaigns/demo-v2/preview', lambda route: held.append(route))
                page.click('#preview-order')
                page.wait_for_timeout(100)
                assert len(held) == 1
                changed = dict(built, narrative='Edited while preview pending')
                page.fill('#proposal-json', json.dumps(changed))
                with page.expect_response('**/api/admin/campaigns/demo-v2/preview'):
                    held[0].continue_()
                page.wait_for_timeout(100)
                assert page.locator('#commit-order').is_disabled()
                assert not page.locator('#order-status').inner_text().startswith('Preview validated')
                page.unroute('**/api/admin/campaigns/demo-v2/preview')
                page.click('#preview-order')
                page.wait_for_function("document.querySelector('#order-status').textContent.startsWith('Preview validated')")
                assert page.locator('#commit-order').is_enabled()
                page.screenshot(path=str(out/'validated-orders.png'))
                page.locator('[data-return-map]').click()
                assert canvas.evaluate('el=>el===document.querySelector("#planet-map")')
                assert page.locator('.force-route.preview').count() == 1
                page.screenshot(path=str(out/'validated-ground.png'))
                # Repeated pan/zoom redraws must replace counters, preserving the canvas.
                cdp = page.context.new_cdp_session(page)
                cdp.send('HeapProfiler.collectGarbage')
                before = cdp.send('Memory.getDOMCounters')
                started = time.monotonic()
                for _ in range(12):
                    page.click('#zoom-in')
                    page.click('#zoom-out')
                redraw_ms = (time.monotonic()-started)*1000/24
                assert page.locator('.force-counter').count() == 2
                assert page.locator('.force-map-controls').count() == 1
                cdp.send('HeapProfiler.collectGarbage')
                after = cdp.send('Memory.getDOMCounters')
                assert after['jsEventListeners'] <= before['jsEventListeners']
                page.click('#hw-command')
                page.locator('#command-menu [data-open=orders]').click()
                page.click('#commit-order')
                page.wait_for_function("document.querySelector('#command-turn').textContent==='TURN 2'")
                page.locator('[data-return-map]').click()
                committed = db.current('demo-v2')['snapshot']
                assert len(db.history('demo-v2')[0]) == 3
                assert any(u.get('destination_province_id') == enemy['location_id'] for u in committed['state']['units'])
                descend_hierarchy(page, ['Hearth', 'Cinder', 'Reach'])
                page.wait_for_selector('.force-route:not(.draft):not(.preview)')
                page.screenshot(path=str(out/'committed-transit.png'))
                page.select_option('#map-level', 'galactic')
                page.wait_for_function("document.querySelector('#map-coordinates').textContent.startsWith('GALACTIC')")
                click_map_marker(page, 'Hearth')
                page.wait_for_selector('.force-counter.mixed')
                page.locator('.force-counter.mixed').click()
                assert page.locator('.force-stack-row').count() == 2
                assert page.locator('.force-stack-row').get_by_role('button', name='Move', exact=True).count() == 1
                page.locator('.force-stack-row').get_by_role('button', name='Move', exact=True).click()
                page.get_by_role('button', name='Target on map', exact=True).click()
                assert page.locator('#command-workspace').is_hidden()
                page.get_by_role('button', name='Cancel map targeting', exact=True).click()
                assert page.locator('#command-workspace').is_visible()
                assert page.get_by_label('Destination system', exact=True).count() == 0
                page.locator('[data-return-map]').click()
                page.locator('.force-counter.mixed').click()
                page.locator('.force-stack-row').get_by_role('button', name='Move', exact=True).click()
                page.get_by_label('Supply source', exact=True).select_option('__none')
                page.get_by_role('button', name='Target on map', exact=True).click()
                click_map_marker(page, 'Unsurveyed System', touch=True)
                page.click('#hw-command')
                page.locator('#command-menu [data-open=orders]').click()
                assert page.locator('.movement-request-list li').count() == 1
                page.get_by_role('button', name='Build proposal from GM packet', exact=True).click()
                page.wait_for_function("document.querySelector('#proposal-json').value.includes('fleet_move')")
                fleet_proposal = json.loads(page.locator('#proposal-json').input_value())
                assert fleet_proposal['orders']['actions'] == [{'type':'fleet_move','fleet_id':'demo-v2-transport-01','destination_system_id':'demo-v2-system-glimmer','source_id':None}]
                page.click('#preview-order')
                page.wait_for_function("document.querySelector('#order-status').textContent.startsWith('Preview validated')")
                page.click('#commit-order')
                page.wait_for_function("document.querySelector('#command-turn').textContent==='TURN 3'")
                page.locator('[data-return-map]').click()
                page.select_option('#map-level', 'galactic')
                page.wait_for_function("document.querySelector('#map-coordinates').textContent.startsWith('GALACTIC')")
                click_map_marker(page, 'Hearth')
                page.wait_for_selector('.force-route:not(.draft):not(.preview)')
                page.screenshot(path=str(out/'fleet-transit.png'))
                page.click('#hw-command')
                page.select_option('#appearance-select', 'dark')
                page.click('#hw-command')
                page.screenshot(path=str(out/'fleet-dark.png'))
                page.set_viewport_size({'width':390,'height':844})
                page.screenshot(path=str(out/'fleet-phone.png'))
                assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
                page.set_viewport_size({'width':1280,'height':900})
                page.locator('.force-counter.mixed').click()
                page.locator('.force-stack-item').filter(has_text='Owned').click()
                moving_row = page.locator('#inspector-content .inspector-row').filter(has=page.locator('span', has_text='Moving Until'))
                assert moving_row.locator('b').inner_text() == '5'
                page.click('#hw-command')
                page.locator('#command-menu [data-open=orders]').click()
                page.get_by_role('button', name='Load example proposal', exact=True).click()
                page.wait_for_function("JSON.parse(document.querySelector('#proposal-json').value||'{}').base_turn===3")
                page.click('#preview-order')
                page.wait_for_function("/^Preview (validated|failed)/.test(document.querySelector('#order-status').textContent)")
                assert page.locator('#order-status').inner_text().startswith('Preview validated'), page.locator('body').inner_text()[-2000:]
                old_text = page.locator('#proposal-json').input_value()
                for _ in range(2):
                    external = db.packet('demo-v2')['example']
                    external['submission_id'] = 'external-refresh-' + uuid.uuid4().hex
                    db.commit('demo-v2', external)
                page.click('#refresh-button')
                page.wait_for_function("document.querySelector('#command-turn').textContent==='TURN 5'")
                assert page.locator('#commit-order').is_disabled()
                assert page.locator('#proposal-json').input_value() == old_text
                assert moving_row.locator('b').inner_text() == 'Unknown'
                page.click('#hw-command')
                page.locator('#command-menu [data-open=history]').click()
                page.get_by_role('button', name='Inspect turn 1', exact=True).click()
                page.wait_for_function("!document.querySelector('#historical-badge').hidden")
                page.wait_for_selector('.force-counter.own')
                page.locator('.force-counter.own').click()
                assert page.locator('.force-stack-row').get_by_role('button', name='Move', exact=True).count() == 0
                # Campaign clear removes the in-memory movement UI and all proposal text.
                page.select_option('#campaign-select', 'campaign')
                page.wait_for_function("document.querySelector('#command-turn').textContent==='TURN —'")
                assert page.locator('.force-counter').count() == 0
                assert page.locator('#proposal-json').count() == 0
                assert not errors, errors
                (out/'movement-results.json').write_text(json.dumps({
                    'result':'PASS', 'browser':browser.version, 'viewport':[1280,900],
                    'redraw_click_to_completion_mean_ms':round(redraw_ms,1),
                    'cdp_before':before, 'cdp_after':after,
                    'checks':['owned stack/observed counter','player unsigned export and GM rejection',
                              'invalid JSON preservation','allocations/actions/narrative preservation',
                              'GM exact preview and commit','recorded transit connector',
                              'pending preview edit rejected',
                              'unsigned moves never inherit unrelated preview',
                              'fleet GM packet/null-source preview/commit',
                              'map targeting touch and visible cancel',
                              'phone owned/observed counter separation and center taps',
                              'historical forces have no move controls','dark/phone layout',
                              'new snapshot refresh invalidates preview and preserves JSON',
                              'selected fleet inspector refreshes through recorded arrival',
                              '24 redraws bounded DOM and canvas identity','campaign clear','no page errors']}, indent=2))
                browser.close()
    finally:
        if server:
            server.terminate()
            server.wait(timeout=10)
        with psycopg.connect(dsn, autocommit=True) as c:
            c.execute(sql.SQL('DROP SCHEMA IF EXISTS {} CASCADE').format(sql.Identifier(schema)))


if __name__ == '__main__':
    main()
