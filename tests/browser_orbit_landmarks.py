"""Read-only orbital annotation checks against explicitly supplied V10 fixtures."""
import hashlib
import json
import math
import os
from pathlib import Path
import sys
from urllib.parse import quote

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.browser_planet_orbit import HOOK


def hashes():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [ROOT / 'public/app.js', ROOT / 'public/orbit-landmarks.js',
                      ROOT / 'public/style.css', ROOT / 'public/index.html']}


def main():
    base = os.environ['WOLD_ORBIT_TEST_BASE'].rstrip('/')
    campaign = os.environ['WOLD_ORBIT_TEST_CAMPAIGN']
    other = os.environ.get('WOLD_ORBIT_TEST_OTHER')
    out = Path(os.environ.get('WOLD_ORBIT_TEST_OUT', ROOT / 'data/orbit-orientation/browser'))
    out.mkdir(parents=True, exist_ok=True)
    before_hashes = hashes()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/usr/bin/chromium',
                                     args=['--no-sandbox', '--disable-dev-shm-usage'])
        context = browser.new_context(viewport={'width': 1440, 'height': 1024}, has_touch=True)
        page = context.new_page()
        page.add_init_script(HOOK)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(base)
        page.wait_for_selector(f'#campaign-select option[value="{campaign}"]', state='attached')
        page.locator('[data-dialog-close]').click()
        page.select_option('#campaign-select', campaign)
        page.wait_for_selector('.orbit-landmark:visible', timeout=90000)
        page.wait_for_timeout(500)
        before = page.request.get(f'{base}/api/player/campaigns/{quote(campaign)}').json()
        assert page.locator('#feature-name-toggle').inner_text().startswith('Hydro names')
        page.screenshot(path=str(out / '01-orbit-landmarks.png'))
        button = page.locator('.orbit-landmark:visible').first
        province = button.get_attribute('data-province-id')
        assert 'recorded province anchor' in button.get_attribute('aria-label')
        expected = page.evaluate('''province=>{const {geometry:g,detail:d}=window.__surfaceAudit.o,
          cell=d.province_anchors.find(item=>item.province_id===province).cell;
          return {x:(cell%d.width+.5)*g.planet.width/d.width,
                  y:(Math.floor(cell/d.width)+.5)*g.planet.height/d.height};}''', province)
        button.focus()
        page.set_viewport_size({'width': 1400, 'height': 1024})
        page.wait_for_timeout(250)
        assert page.evaluate('document.activeElement?.dataset.provinceId') == province
        button.press('Enter')
        page.wait_for_function('document.querySelector("#orbit-toggle").getAttribute("aria-pressed")==="false"')
        page.wait_for_timeout(500)
        assert page.locator('#command-inspector').is_visible()
        assert page.evaluate('window.__surfaceAudit.o.selectedProvince') == province
        assert 'PROVINCE INSPECTION' in page.locator('#inspector-content').inner_text()
        projection = page.evaluate('''a=>{const t=window.__surfaceAudit.t,ref=(t.viewportWidth/2-t.ox)/t.tile,
          x=HWMapRenderer.nearestX(a.x,ref,t.cols);return{x:t.ox+x*t.tile,y:t.oy+a.y*t.tile};}''', expected)
        assert page.evaluate('p=>!document.elementFromPoint(p.x,p.y)?.closest("#command-inspector")', projection)
        page.screenshot(path=str(out / '02-selected-surface.png'))
        camera = page.evaluate('({ox:__surfaceAudit.t.ox,oy:__surfaceAudit.t.oy,tile:__surfaceAudit.t.tile})')
        for _ in range(2):
            page.locator('#hw-command').click()
            page.locator('#command-menu [data-open="economy"]').click()
            page.locator('[data-return-map]:visible').click()
        assert camera == page.evaluate('({ox:__surfaceAudit.t.ox,oy:__surfaceAudit.t.oy,tile:__surfaceAudit.t.tile})')
        if page.locator('#command-inspector').is_visible():
            page.locator('[data-inspector-close]').click()
        page.locator('#orbit-toggle').click()
        page.wait_for_selector('.orbit-landmark:visible')
        page.wait_for_timeout(500)
        button = page.locator(f'.orbit-landmark[data-province-id="{province}"]')
        marker = button.locator('.orbit-landmark-marker').bounding_box()
        hit = {'x': marker['x'] + marker['width']/2, 'y': marker['y'] + marker['height']/2}
        assert page.evaluate('p=>document.elementFromPoint(p.x,p.y)?.closest("button")?.dataset.provinceId', hit) == province
        page.touchscreen.tap(hit['x'], hit['y'])
        page.wait_for_timeout(500)
        assert page.locator('#command-inspector').is_visible()
        assert page.evaluate('window.__surfaceAudit.o.selectedProvince') == province
        if page.locator('#command-inspector').is_visible():
            page.locator('[data-inspector-close]').click()
        page.locator('#orbit-toggle').click()
        page.wait_for_selector('.orbit-landmark:visible')
        page.wait_for_timeout(500)
        original_label = button.bounding_box()
        audit = page.evaluate('window.__orbitAudit')
        rect, view = audit['rect'], audit['view']
        focal = min(rect['width'], rect['height']) * .36
        cx, cy = rect['left'] + rect['width']/2, rect['top'] + rect['height']/2
        page.mouse.move(cx, cy)
        page.mouse.down()
        page.mouse.move(cx + math.pi*focal, cy-view['latitude']*focal, steps=15)
        page.mouse.up()
        page.wait_for_timeout(250)
        assert page.locator('#orbit-toggle').get_attribute('aria-pressed') == 'true'
        assert button.is_hidden(), 'Backside settlement remains visible/clickable'
        assert page.locator('#command-inspector').is_hidden(), 'Drag activated a settlement'
        stale_point = {'x': original_label['x']+original_label['width']/2,
                       'y': original_label['y']+original_label['height']/2}
        assert not page.evaluate('p=>document.elementFromPoint(p.x,p.y)?.closest(".orbit-landmark")', stale_point)
        page.mouse.click(stale_point['x'], stale_point['y'])
        page.wait_for_timeout(500)
        assert page.locator('#command-inspector').is_hidden(), 'Former label selected its hidden settlement'
        page.screenshot(path=str(out / '03-backside-no-stale-hit.png'))
        if other:
            page.select_option('#campaign-select', other)
            page.wait_for_selector('.orbit-landmark:visible', timeout=90000)
            allowed = {s['province_id'] for s in page.request.get(f'{base}/api/player/campaigns/{quote(other)}').json()['state']['settlements']}
            ids = page.locator('.orbit-landmark').evaluate_all('(buttons)=>buttons.map(b=>b.dataset.provinceId)')
            assert all(pid in allowed for pid in ids) and province not in ids
        page.evaluate('window.__orbitEngine.gl.getExtension("WEBGL_lose_context").loseContext()')
        page.wait_for_timeout(300)
        assert page.locator('.orbit-landmark:visible').count() == 0
        after = page.request.get(f'{base}/api/player/campaigns/{quote(campaign)}').json()
        assert before['snapshot_id'] == after['snapshot_id'] and before['state'] == after['state']
        assert not errors, errors
        report = {'browser': browser.version, 'keyboard_activation': True, 'resize_preserves_focus': True,
                  'symbol_touch_activation': True, 'canonical_province': province, 'saved_anchor': expected,
                  'selected_anchor_unobscured': True, 'management_camera_preserved': True,
                  'backside_hidden_and_old_hit_inactive': True, 'drag_does_not_activate': True,
                  'campaign_isolation': bool(other), 'webgl_fallback_clears_labels': True,
                  'campaign_state_unchanged': True, 'page_errors': errors,
                  'source_hashes': hashes(), 'source_hashes_unchanged': hashes() == before_hashes}
        assert report['source_hashes_unchanged']
        (out / 'workflow.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps(report, indent=2))
        browser.close()


if __name__ == '__main__':
    main()
