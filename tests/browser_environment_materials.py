"""Read-only material and hydrography presentation check for one QC campaign."""
import json
import os
from pathlib import Path
import sys
from urllib.parse import quote

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.browser_planet_orbit import HOOK
from tests.browser_quality_control import act, capture_theme_pair, source_hashes, stable_paint


def wait_mode(page, label):
    page.wait_for_function('label=>document.querySelector("#orbit-toggle")?.textContent.trim()===label', arg=label)
    # Native orbit fades last 420 ms; controls update before the fade completes.
    page.wait_for_timeout(500)
    stable_paint(page)


def selected_anchor_visibility(page, feature):
    """Project the canonical saved cell through the actual renderer transform."""
    return page.evaluate('''feature=>{
      const {o,t}=window.__surfaceAudit, g=o.geometry, d=o.detail,
        canvas=document.querySelector('#planet-map'), rect=canvas.getBoundingClientRect(),
        fine=Boolean(d&&g.surface?.version==='planet-v10'),
        width=fine?d.width:g.planet.width, height=fine?d.height:g.planet.height,
        x=(feature.anchor%width+.5)*g.planet.width/width,
        y=(Math.floor(feature.anchor/width)+.5)*g.planet.height/height,
        worldX=window.HWMapRenderer.wrapsX(g)?window.HWMapRenderer.nearestX(x,(rect.width/2-t.ox)/t.tile,g.planet.width):x,
        px=t.ox+worldX*t.tile, py=t.oy+y*t.tile,
        clientX=rect.left+px, clientY=rect.top+py,
        hit=document.elementFromPoint(clientX,clientY), safe=t.safeRect;
      return {anchor:feature.anchor, detailWidth:width, detailHeight:height,
        x:clientX,y:clientY, hit:hit?{tag:hit.tagName,id:hit.id,classes:hit.className}:null,
        insideCanvas:px>=0&&px<rect.width&&py>=0&&py<rect.height,
        insideSafe:!safe||(px>=safe.left&&px<=safe.right&&py>=safe.top&&py<=safe.bottom),
        exposed:hit===canvas};
    }''', feature)


def surface_camera(page):
    return page.evaluate('''()=>{const t=window.__surfaceAudit.t;return {ox:t.ox,oy:t.oy,tile:t.tile}}''')


def check_feature_camera_edges(page, out, features, chosen):
    """Exercise saved north/south anchors using catalog controls at three scales."""
    width = page.evaluate('''()=>{const o=window.__surfaceAudit.o;
      return o.geometry.surface?.version==='planet-v10'?o.detail.width:o.geometry.planet.width}''')
    samples = {'north': min(features, key=lambda f: f['anchor'] // width),
               'south': max(features, key=lambda f: f['anchor'] // width), 'chosen': chosen}
    results = []
    for scale in ('regional', 'minimum', 'detail'):
        if scale == 'minimum':
            act(page, out, 'edges-minimum-reset', lambda: page.locator('#zoom-reset').click())
            stable_paint(page)
        elif scale == 'detail':
            for step in range(32):
                previous = surface_camera(page)['tile']
                act(page, out, f'edges-detail-zoom-{step}', lambda: page.locator('#zoom-in').click())
                stable_paint(page)
                if surface_camera(page)['tile'] == previous:
                    break
            else:
                raise AssertionError('Surface detail zoom did not reach its bounded maximum')
        for direction, feature in samples.items():
            label = f'edges-{scale}-{direction}'
            act(page, out, f'{label}-open-list', lambda: page.locator('#feature-list-button').click())
            row = page.locator(f'.hydro-feature-row[data-hydro-feature-id="{feature["id"]}"]')
            assert row.is_visible(), f'Saved feature missing from catalog: {feature["id"]}'
            if feature.get('name'):
                assert feature['name'] in row.inner_text()
            act(page, out, f'{label}-select', lambda: row.click())
            page.wait_for_function('id=>window.__surfaceAudit.o.selectedFeatureId===id', arg=feature['id'])
            stable_paint(page)
            anchor = selected_anchor_visibility(page, feature)
            coverage = page.evaluate('''()=>{const t=window.__surfaceAudit.t;return {
              top:t.oy,bottom:t.oy+t.gridH,safeTop:t.safeRect.top,safeBottom:t.safeRect.bottom}}''')
            result = {'scale': scale, 'direction': direction, 'feature_id': feature['id'],
                      'feature_name': feature.get('name'), 'anchor': anchor, 'coverage': coverage,
                      'camera': surface_camera(page)}
            results.append(result)
            (out / 'feature-camera-edges.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
            page.screenshot(path=str(out / f'{label}.png'))
            assert anchor['insideCanvas'] and anchor['insideSafe'] and anchor['exposed'], f'Selected anchor is occluded: {result}'
            assert coverage['top'] <= coverage['safeTop'] + 1e-6 and coverage['bottom'] >= coverage['safeBottom'] - 1e-6, f'Terrain does not cover the safe viewport: {result}'

    # Presentation controls must preserve the camera; collapse retains selection.
    camera = surface_camera(page)
    selected = page.evaluate('window.__surfaceAudit.o.selectedFeatureId')
    act(page, out, 'edges-toggle-names', lambda: page.locator('#feature-name-toggle').click())
    stable_paint(page)
    assert surface_camera(page) == camera, 'Feature-name toggle changed camera'
    assert page.evaluate('window.__surfaceAudit.o.selectedFeatureId') == selected
    act(page, out, 'edges-collapse-inspector', lambda: page.locator('[data-inspector-close]').click())
    stable_paint(page)
    assert page.locator('#command-inspector').is_hidden()
    assert surface_camera(page) == camera, 'Collapsing inspector changed camera'
    assert page.evaluate('window.__surfaceAudit.o.selectedFeatureId') == selected
    act(page, out, 'edges-reopen-inspector', lambda: page.locator('#feature-list-button').click())
    stable_paint(page)
    assert surface_camera(page) == camera, 'Reopening inspector changed camera'
    clear = page.locator('#inspector-content').get_by_role('button', name='Return to province', exact=True)
    if not clear.count():
        clear = page.locator('#inspector-content').get_by_role('button', name='Clear surface selection', exact=True)
    clear_available = clear.count() == 1 and clear.is_visible()
    if clear_available:
        act(page, out, 'edges-clear-selection', lambda: clear.click())
        stable_paint(page)
        assert page.evaluate('window.__surfaceAudit.o.selectedFeatureId') is None
        assert surface_camera(page) == camera, 'Clearing feature selection changed camera'
    else:
        assert page.evaluate('window.__surfaceAudit.o.selectedFeatureId') == selected
    return results, clear_available


def main():
    base = os.environ.get('WOLD_QC_BASE', 'http://127.0.0.1:4203').rstrip('/')
    campaign = os.environ.get('WOLD_QC_CAMPAIGN', 'material-water')
    out = Path(os.environ.get('WOLD_QC_OUT', ROOT / 'data/quality-control/regression')) / 'materials'
    out.mkdir(parents=True, exist_ok=True)
    before_hashes, captures, errors = source_hashes(), [], []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/usr/bin/chromium',
                                     args=['--no-sandbox', '--disable-dev-shm-usage'])
        page = browser.new_page(viewport={'width': 1440, 'height': 1024})
        page.add_init_script(HOOK)
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(base)
        page.wait_for_selector(f'#campaign-select option[value="{campaign}"]', state='attached')
        if page.locator('#command-dialog').is_visible():
            act(page, out, 'initial-close-dialog', lambda: page.locator('[data-dialog-close]').click())
        before = page.request.get(f'{base}/api/player/campaigns/{quote(campaign)}')
        assert before.ok, f'Campaign read failed: {before.status}'
        before = before.json()
        act(page, out, 'select-campaign', lambda: page.select_option('#campaign-select', campaign))
        page.wait_for_function('window.__surfaceAudit?.o?.geometry?.planet', timeout=90000)
        page.wait_for_selector('.orbit-landmark:visible', timeout=90000)
        if page.locator('#orbit-toggle').inner_text().strip() == 'Surface':
            act(page, out, 'initial-enter-surface', lambda: page.locator('#orbit-toggle').click())
            wait_mode(page, 'Orbit')
        act(page, out, 'enter-orbit', lambda: page.locator('#orbit-toggle').click())
        wait_mode(page, 'Surface')
        page.wait_for_selector('.orbit-landmark:visible', timeout=90000)
        initial = page.evaluate('window.__orbitAudit?.view')
        assert initial, 'Native orbit view did not load'
        drag_start = page.evaluate('''()=>{
          const canvas=document.querySelector('#planet-map'), box=canvas.getBoundingClientRect(), r=window.__orbitAudit.rect;
          for(const [dx,dy] of [[0,0],[-.15,0],[.15,0],[0,-.15],[0,.15],[-.2,-.2],[.2,.2]]){
            const x=box.left+r.left+r.width*(.5+dx), y=box.top+r.top+r.height*(.5+dy);
            if(document.elementFromPoint(x,y)===canvas)return {x,y,hit:'planet-map'};
          }
          return null;
        }''')
        assert drag_start, 'No exposed native canvas point is available for orbit drag'
        cx, cy = drag_start['x'], drag_start['y']
        act(page, out, 'orbit-drag', lambda: (page.mouse.move(cx, cy), page.mouse.down(),
            page.mouse.move(cx + 90, cy - 65, steps=12), page.mouse.up()))
        page.wait_for_timeout(250)
        rotated = page.evaluate('window.__orbitAudit?.view')
        assert any(abs(rotated[key] - initial[key]) > 0.001 for key in ('longitude', 'latitude')), 'Actual orbit drag did not change orientation'
        landmark_count = page.locator('.orbit-landmark:visible').count()
        theme_state = {'orbit': capture_theme_pair(page, out, '01-orbit-dragged', captures)}

        act(page, out, 'return-surface', lambda: page.locator('#orbit-toggle').click())
        wait_mode(page, 'Orbit')
        act(page, out, 'recenter', lambda: page.locator('#map-recenter').click())
        page.wait_for_timeout(200)
        geometry = page.evaluate('window.__surfaceAudit.o.geometry')
        surface = geometry.get('surface', {})
        catalog = geometry.get('detailHydrography') or surface.get('hydrography') or {}
        features = catalog.get('features', [])
        materials = surface.get('materials', {})
        lake_material = surface.get('lake_material', materials.get('lake_material'))
        polar_caps = surface.get('polar_caps', materials.get('polar_caps'))
        hydrology = surface.get('hydrology')
        assert hydrology != 'none' or not any(f.get('kind') == 'river' for f in features), 'Dry hydrology contains a river feature'
        lakes = [f for f in features if f.get('kind') == 'lake']
        if lake_material == 'none':
            assert not lakes, 'No-lake material choice produced lake features'
        else:
            assert lakes and all(f.get('material') == lake_material for f in lakes), 'Lake feature material differs from the saved choice'
        if polar_caps not in (None, 'none') and lake_material != 'water':
            assert not any(f.get('kind') == 'lake' and f.get('material') == 'water' for f in features), 'Polar ice appeared as a water lake'

        act(page, out, 'open-feature-list', lambda: page.locator('#feature-list-button').click())
        page.wait_for_selector('#hydrography-feature-list')
        anchor_visibility = None
        if not features:
            empty_message = 'No water bodies or river courses are recorded for this surface.'
            assert page.get_by_text(empty_message, exact=True).is_visible(), 'Empty hydrography catalog is not explained'
            assert page.get_by_text(empty_message, exact=True).count() == 1
            assert page.locator('#hydro-feature-search').count() == 0, 'Empty catalog exposes a search control'
            assert page.get_by_text('No recorded features match this search.', exact=True).count() == 0, 'Empty catalog duplicates the filtered-empty message'
            theme_state['empty_catalog'] = capture_theme_pair(page, out, '02-empty-catalog', captures)
        else:
            target = next((f for f in features if f.get('kind') == 'lake'), features[0])
            row = page.locator(f'.hydro-feature-row[data-hydro-feature-id="{target["id"]}"]')
            assert row.is_visible(), f'Saved feature missing from catalog: {target["id"]}'
            act(page, out, 'select-saved-feature', lambda: row.click())
            page.wait_for_function('id=>window.__surfaceAudit?.o?.selectedFeatureId===id', arg=target['id'])
            inspector = page.locator('#inspector-content')
            assert inspector.get_attribute('data-selected-hydro-feature') == target['id']
            assert target['material'].lower() in inspector.inner_text().lower(), 'Inspector material differs from saved feature'
            stable_paint(page)
            anchor_visibility = selected_anchor_visibility(page, target)
            (out / 'selected-anchor.json').write_text(json.dumps(anchor_visibility, indent=2) + '\n', encoding='utf-8')
            page.screenshot(path=str(out / 'selected-anchor.png'))
            assert anchor_visibility['insideCanvas'] and anchor_visibility['insideSafe'] and anchor_visibility['exposed'], f'Selected saved feature anchor is not exposed on the map: {anchor_visibility}'
            act(page, out, 'toggle-feature-names', lambda: page.locator('#feature-name-toggle').click())
            assert page.locator('#feature-name-toggle').get_attribute('aria-pressed') == 'true'
            theme_state['feature_inspector'] = capture_theme_pair(page, out, '02-feature-inspector', captures)

        camera = page.evaluate('''()=>{const t=window.__surfaceAudit?.t;return t?{ox:t.ox,oy:t.oy,tile:t.tile}:null}''')
        selected = page.evaluate('window.__surfaceAudit?.o?.selectedFeatureId')
        box = page.locator('#command-inspector').bounding_box()
        if box:
            act(page, out, 'inspector-wheel', lambda: (
                page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2),
                page.mouse.wheel(0, 500)))
            page.wait_for_timeout(200)
        after_wheel = page.evaluate('''()=>{const t=window.__surfaceAudit?.t;return t?{ox:t.ox,oy:t.oy,tile:t.tile}:null}''')
        assert after_wheel == camera, 'Inspector wheel changed map camera'
        assert page.evaluate('window.__surfaceAudit?.o?.selectedFeatureId') == selected, 'Inspector wheel changed feature selection'
        edge_checks, clear_available = check_feature_camera_edges(page, out, features, target) if features else ([], None)
        after_response = page.request.get(f'{base}/api/player/campaigns/{quote(campaign)}')
        assert after_response.ok and after_response.json() == before, 'Materials presentation changed campaign state'
        assert not errors, errors
        after_hashes = source_hashes()
        assert before_hashes == after_hashes, 'Product source changed during the presentation check'
        report = {'browser': browser.version, 'campaign': campaign, 'captures': captures,
                  'theme_restorations': theme_state, 'orbit_drag_changed_view': True,
                  'orbit_drag_start': drag_start, 'initial_orientation': initial, 'rotated_orientation': rotated,
                  'selected_anchor_visibility': anchor_visibility,
                  'feature_camera_edges': edge_checks,
                  'presentation_controls_preserve_camera': bool(edge_checks),
                  'clear_selection_control_available': clear_available,
                  'visible_landmarks_after_drag': landmark_count, 'recentered': True,
                  'hydrology': hydrology, 'lake_material': lake_material, 'polar_caps': polar_caps,
                  'feature_count': len(features), 'camera_and_selection_survive_inspector_wheel': True,
                  'campaign_state_unchanged': True, 'page_errors': errors,
                  'source_hashes': after_hashes, 'source_hashes_unchanged': True}
        (out / 'workflow.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(report, indent=2))
        browser.close()


if __name__ == '__main__':
    main()
