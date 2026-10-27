"""Read-only browser regression for campaign access and report quality-control fixes.

Uses the configured local campaign and a pre-game campaign through public UI/API reads.
Set WOLD_QC_BASE, WOLD_QC_CAMPAIGN, and WOLD_QC_PREGAME to select the fixture.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
from urllib.parse import quote

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.browser_planet_orbit import HOOK


def source_hashes():
    paths = ('public/app.js', 'public/desktop-shell.js', 'public/index.html', 'public/style.css')
    return {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in paths}


def save_dom(page, out, label):
    """Save a fresh serialized DOM immediately before each user interaction."""
    (out / f'{label}-before.html').write_text(page.content(), encoding='utf-8')


def act(page, out, label, operation):
    save_dom(page, out, label)
    operation()


def api_json(page, url):
    response = page.request.get(url)
    assert response.ok, f'Public read failed: {url} ({response.status})'
    return response.json()


def campaign_state(page, base, campaign):
    return api_json(page, f'{base}/api/player/campaigns/{quote(campaign)}')


def enter_campaign_from_dialog(page, out, campaign, label):
    if page.locator('#command-dialog').is_hidden():
        act(page, out, f'{label}-open-menu', lambda: page.locator('#hw-command').click())
        act(page, out, f'{label}-open-access',
            lambda: page.locator('#command-menu [data-open="campaign"]').click())
    page.wait_for_selector('#command-dialog[aria-labelledby="command-dialog-title"]:visible')
    assert page.get_by_role('dialog', name='CAMPAIGN & ACCESS').is_visible()
    act(page, out, f'{label}-choose-campaign',
        lambda: page.locator('#dialog-campaign-select').select_option(campaign))


def open_workspace(page, out, view, label):
    if page.locator('#command-workspace').is_visible():
        tab = page.locator(f'.workspace-tabs [data-tab="{view}"]')
        if tab.count() and tab.is_visible():
            act(page, out, f'{label}-open-{view}', lambda: tab.click())
            return
        act(page, out, f'{label}-return-map', lambda: page.locator('[data-return-map]:visible').click())
    act(page, out, f'{label}-menu', lambda: page.locator('#hw-command').click())
    act(page, out, f'{label}-open-{view}',
        lambda: page.locator(f'#command-menu [data-open="{view}"]').click())
    page.wait_for_function('document.querySelector("#command-workspace")?.hidden === false')


def select_settlement_province(page, out, settlement):
    """Select the saved province through its visible settlement landmark."""
    province_id = settlement['province_id']
    orbit = page.locator('#orbit-toggle')
    if orbit.is_visible() and orbit.inner_text().strip() == 'Orbit':
        act(page, out, '07-enter-orbit-for-landmark', lambda: orbit.click())
    page.wait_for_selector('.orbit-landmark:visible', timeout=90000)
    marker = page.locator(f'.orbit-landmark[data-province-id="{province_id}"]:visible').first
    marker.wait_for(state='visible', timeout=90000)
    act(page, out, '08-select-settlement-landmark', lambda: marker.click())
    page.wait_for_function('p => window.__surfaceAudit?.o?.selectedProvince === p', arg=province_id)
    page.wait_for_function('document.querySelector("#orbit-toggle")?.getAttribute("aria-pressed")==="false"')
    return province_id


def facility_signature(record):
    return json.dumps({k: v for k, v in record.items() if k != 'id'}, sort_keys=True, separators=(',', ':'))


def main():
    base = os.environ.get('WOLD_QC_BASE', 'http://127.0.0.1:4203').rstrip('/')
    campaign = os.environ.get('WOLD_QC_CAMPAIGN', 'material-water')
    pregame = os.environ.get('WOLD_QC_PREGAME', 'campaign')
    out = Path(os.environ.get('WOLD_QC_OUT', ROOT / 'data/quality-control/regression'))
    out.mkdir(parents=True, exist_ok=True)
    before_hashes = source_hashes()
    page_errors = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/usr/bin/chromium',
                                     args=['--no-sandbox', '--disable-dev-shm-usage'])
        context = browser.new_context(viewport={'width': 1440, 'height': 1024})
        page = context.new_page()
        page.add_init_script(HOOK)
        page.on('pageerror', lambda error: page_errors.append(str(error)))
        page.goto(base)
        page.wait_for_selector(f'#campaign-select option[value="{campaign}"]', state='attached')
        page.wait_for_selector('#command-dialog[aria-labelledby="command-dialog-title"]:visible')
        dialog = page.get_by_role('dialog', name='CAMPAIGN & ACCESS')
        assert dialog.is_visible()
        page.wait_for_function('''() => {
          const d=document.querySelector('#command-dialog');
          return d && d.contains(document.activeElement);
        }''')
        focusables = page.evaluate('''() => [...document.querySelector('#command-dialog').querySelectorAll(
          'button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),[tabindex]:not([tabindex="-1"])'
        )].filter(n=>n.getClientRects().length>0).map(n=>n.id || n.getAttribute('data-dialog-close') || n.tagName)''')
        assert focusables, 'Campaign dialog has no visible focusable control'
        act(page, out, '01-dialog-shift-tab', lambda: page.evaluate('''() => {
          const d=document.querySelector('#command-dialog');
          const f=[...d.querySelectorAll('button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),[tabindex]:not([tabindex="-1"])')].filter(n=>n.getClientRects().length>0);
          f[0].focus();
        }'''))
        act(page, out, '02-dialog-tab-wrap', lambda: page.keyboard.press('Shift+Tab'))
        assert page.evaluate('''() => {const d=document.querySelector('#command-dialog');
          const f=[...d.querySelectorAll('button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),[tabindex]:not([tabindex="-1"])')].filter(n=>n.getClientRects().length>0);
          return document.activeElement===f.at(-1)}''')
        act(page, out, '03-dialog-tab-forward', lambda: page.keyboard.press('Tab'))
        assert page.evaluate('''() => {const d=document.querySelector('#command-dialog');
          const f=[...d.querySelectorAll('button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),[tabindex]:not([tabindex="-1"])')].filter(n=>n.getClientRects().length>0);
          return document.activeElement===f[0]}''')
        act(page, out, '04-dialog-escape', lambda: page.keyboard.press('Escape'))
        assert page.locator('#command-dialog').is_hidden()
        assert page.evaluate('document.activeElement?.id') == 'hw-command', 'Escape did not restore focus'

        initial = page.evaluate('''() => ({heading:document.querySelector('.section-title h1')?.textContent,
          scale:document.querySelector('#map-scale')?.textContent,
          scaleTitle:document.querySelector('#map-scale')?.title,
          controls:[...document.querySelectorAll('.map-tools button,.map-tools select,#map-level,#overlay-select,#map-style,#zoom-out,#zoom-reset,#zoom-in,#map-recenter,.force-map-controls button')].filter(n=>!n.disabled).map(n=>n.id||n.className),
          text:document.body.innerText})''')
        assert 'No campaign' in initial['heading']
        assert not any(token in initial['text'] for token in ('Kestrel', 'LOADING ACTIVE CAMPAIGN', '64 × 40 GRID'))
        assert not any(token in (initial['scale'] + ' ' + (initial['scaleTitle'] or '')).lower()
                       for token in ('64 × 40', '1024 × 640', 'grid', 'saved detail'))
        assert not initial['controls'], f'Map-only controls enabled without geography: {initial["controls"]}'

        # Select through the visible dialog control, as a player does.
        enter_campaign_from_dialog(page, out, campaign, '05-demo')
        page.wait_for_function('''() => document.querySelector('#map-placeholder').hidden &&
          window.__surfaceAudit?.o?.geometry?.planet''', timeout=90000)
        page.wait_for_function('''() => {
          const b=document.querySelector('#orbit-toggle');
          return b && (b.textContent.trim()==='Surface' || b.textContent.trim()==='Orbit');
        }''', timeout=90000)
        if page.locator('#orbit-toggle').is_visible() and page.locator('#orbit-toggle').inner_text().strip() == 'Surface':
            act(page, out, '06-enter-surface', lambda: page.locator('#orbit-toggle').click())
            page.wait_for_function('document.querySelector("#orbit-toggle")?.textContent.trim()==="Orbit"')
        before = campaign_state(page, base, campaign)
        saved_state = before['state']
        geometry = page.evaluate('window.__surfaceAudit.o.geometry')
        map_provinces = {province['id'] for province in geometry.get('provinces', [])}
        settlements = [item for item in saved_state.get('settlements', [])
                      if item.get('province_id') in map_provinces and item.get('owned') is not False]
        assert settlements, f'{campaign} has no owned settlement among the visible map province IDs'
        settlement = settlements[0]
        page.wait_for_function('''() => {
          const b=document.querySelector('#orbit-toggle');
          return b && !b.hidden && !b.disabled && (b.textContent.trim()==='Surface' || b.textContent.trim()==='Orbit');
        }''', timeout=90000)
        selected_province = select_settlement_province(page, out, settlement)
        page.screenshot(path=str(out / '08-selected-settlement.png'))
        if page.locator('#command-inspector').is_visible():
            act(page, out, '11-close-selection-inspector',
                lambda: page.locator('[data-inspector-close]').click())
            page.wait_for_timeout(100)
        camera = page.evaluate('''() => {const t=window.__surfaceAudit.t;return {ox:t.ox,oy:t.oy,tile:t.tile};}''')
        assert settlement['name'] in page.locator('#inspector-content').inner_text()
        assert selected_province in page.locator('#inspector-content').inner_text()

        open_workspace(page, out, 'economy', '08-economy')
        page.wait_for_selector('#economy-panel .scope-tabs [data-scope="local"]')
        local_button = page.locator('#economy-panel [data-scope="local"]')
        campaign_button = page.locator('#economy-panel [data-scope="campaign"]')
        assert local_button.get_attribute('aria-pressed') == 'true'
        assert campaign_button.get_attribute('aria-pressed') == 'false'
        assert page.locator('#economy-panel .local-scope').is_visible()
        assert settlement['name'] in page.locator('#economy-panel .local-scope').inner_text()
        economy_text = page.locator('#economy-panel .local-scope').inner_text()
        assert 'STOCK UNITS' in economy_text.upper()
        if settlement.get('housing') is not None:
            assert 'Housing capacity (people)' in economy_text
        if settlement.get('unrest') is not None:
            assert 'Unrest (0–100 scale)' in economy_text
        for theme in ('light', 'dark'):
            act(page, out, f'09-economy-theme-{theme}',
                lambda value=theme: page.evaluate('v=>window.HWTheme.set(v)', value))
            assert page.locator('html').get_attribute('data-theme') == theme
            page.screenshot(path=str(out / f'economy-{theme}.png'))
        act(page, out, '09-economy-campaign-scope', lambda: campaign_button.click())
        assert campaign_button.get_attribute('aria-pressed') == 'true'
        assert page.locator('#economy-panel .campaign-scope').is_visible()
        assert page.locator('#economy-panel .local-scope').is_hidden()
        act(page, out, '10-economy-local-scope', lambda: local_button.click())
        assert local_button.get_attribute('aria-pressed') == 'true'
        assert page.locator('#economy-panel .local-scope').is_visible()
        assert settlement['name'] in page.locator('#economy-panel .local-scope').inner_text()

        # Related-view button state follows the currently open report.
        economy_tab = page.locator('.workspace-tabs [data-tab="economy"]')
        construction_tab = page.locator('.workspace-tabs [data-tab="construction"]')
        assert economy_tab.get_attribute('aria-pressed') == 'true'
        act(page, out, '11-open-construction', lambda: construction_tab.click())
        page.wait_for_selector('#management-construction .scope-tabs [data-scope="local"]')
        assert construction_tab.get_attribute('aria-pressed') == 'true'
        assert economy_tab.get_attribute('aria-pressed') == 'false'
        construction_data = api_json(page, f'{base}/api/player/campaigns/{quote(campaign)}/systems?section=construction')
        all_facilities = [r for r in construction_data['records'].get('facilities', [])
                          if r.get('settlement_id') == settlement['id']]
        all_projects = [r for r in construction_data['records'].get('projects', [])
                        if r.get('settlement_id') == settlement['id']]
        expected_ids = {r['id'] for r in all_facilities}
        expected_project_ids = {r['id'] for r in all_projects}
        groups = page.locator('#management-construction .local-record-group')
        selected_group = groups.filter(has=page.get_by_role('heading', name=settlement['name']))
        assert selected_group.count() == 1
        rendered = selected_group.locator('details.record-identifiers .inspector-row').evaluate_all(
            "rows=>rows.map(r=>({label:r.children[0]?.textContent.trim(),value:r.children[1]?.textContent.trim()}))")
        rendered_facility_ids = {r['value'] for r in rendered if r['label'] == 'Facility'}
        rendered_project_ids = {r['value'] for r in rendered if r['label'] == 'Project'}
        assert rendered_facility_ids == expected_ids, f'Grouped construction rows must preserve every saved facility ID: rendered={sorted(rendered_facility_ids)}, expected={sorted(expected_ids)}'
        assert rendered_project_ids == expected_project_ids, f'Construction project IDs differ from the saved records: rendered={sorted(rendered_project_ids)}, expected={sorted(expected_project_ids)}'
        expected_groups = len({facility_signature(r) for r in all_facilities})
        # Count facility rows directly from the facility marker to the project marker.
        rendered_group_count = selected_group.evaluate('''group=>{
          const children=[...group.children], start=children.findIndex(n=>n.classList.contains('inspector-section')&&n.textContent.trim()==='FACILITIES');
          if(start<0)return 0;
          const end=children.findIndex((n,i)=>i>start&&n.classList.contains('inspector-section')&&n.textContent.trim()==='PROJECTS');
          return children.slice(start+1,end<0?undefined:end).filter(n=>n.classList.contains('local-record-row')).length;
        }''')
        assert rendered_group_count == expected_groups, 'Identical facility records should share one displayed row'
        if not all_projects:
            assert selected_group.get_by_text('No recorded projects for this settlement.', exact=True).is_visible()
        else:
            assert expected_project_ids <= rendered_project_ids

        local_construction = page.locator('#management-construction [data-scope="local"]')
        campaign_construction = page.locator('#management-construction [data-scope="campaign"]')
        assert local_construction.get_attribute('aria-pressed') == 'true'
        act(page, out, '12-construction-campaign-scope', lambda: campaign_construction.click())
        assert campaign_construction.get_attribute('aria-pressed') == 'true'
        assert page.locator('#management-construction .campaign-scope').is_visible()
        assert page.locator('#management-construction .local-construction').is_hidden()
        act(page, out, '13-construction-local-scope', lambda: local_construction.click())
        assert local_construction.get_attribute('aria-pressed') == 'true'
        assert page.locator('#management-construction .local-construction').is_visible()
        assert settlement['name'] in page.locator('#management-construction .local-construction').inner_text()
        act(page, out, '14-return-map', lambda: page.locator('[data-return-map]:visible').click())
        assert page.evaluate('''() => {const t=window.__surfaceAudit?.t;return t?{ox:t.ox,oy:t.oy,tile:t.tile}:null;}''') == camera
        assert page.evaluate('window.__surfaceAudit.o.selectedProvince') == selected_province

        pregame_before = campaign_state(page, base, pregame)
        enter_campaign_from_dialog(page, out, pregame, '15-pregame')
        page.wait_for_function('document.querySelector("#campaign-kind")?.textContent.includes("PRE-GAME")')
        pregame_data = campaign_state(page, base, pregame)
        assert pregame_data.get('state') is None
        page.wait_for_function('''() => {
          const placeholder=document.querySelector('#map-placeholder');
          return placeholder && !placeholder.hidden;
        }''')
        page.screenshot(path=str(out / '16-pregame-empty-map.png'))
        pregame_view = page.evaluate('''() => ({heading:document.querySelector('.section-title h1')?.textContent,
          scale:document.querySelector('#map-scale')?.textContent, title:document.querySelector('#map-scale')?.title,
          footer:document.querySelector('.map-footer span:last-child')?.textContent,
          controls:[...document.querySelectorAll('.map-tools button,.map-tools select,#map-level,#overlay-select,#map-style,#zoom-out,#zoom-reset,#zoom-in,#map-recenter,.force-map-controls button')].filter(n=>!n.disabled).map(n=>n.id||n.className),
          resources:document.querySelector('#resource-strip')?.innerText, text:document.body.innerText})''')
        assert not pregame_view['controls'], f'Pre-game map controls enabled: {pregame_view["controls"]}'
        assert pregame_view['footer'] == 'This campaign has no recorded geography'
        assert not any(token in pregame_view['text'] for token in ('Kestrel', 'LOADING ACTIVE CAMPAIGN', '64 × 40 GRID'))
        assert 'UNKNOWN' in pregame_view['resources'].upper()
        assert not any(token in ((pregame_view['scale'] or '') + ' ' + (pregame_view['title'] or '')).lower()
                       for token in ('64 × 40', '1024 × 640', 'grid', 'saved detail'))
        after = campaign_state(page, base, campaign)
        pregame_after = campaign_state(page, base, pregame)
        assert before['snapshot_id'] == after['snapshot_id']
        assert before['state'] == after['state'], 'Browser workflow mutated the demo campaign'
        assert pregame_before == pregame_after, 'Browser workflow mutated the pre-game campaign'
        assert not page_errors, page_errors
        after_hashes = source_hashes()
        assert before_hashes == after_hashes, 'Source changed while browser regression was running'
        report = {'chromium': browser.version, 'campaign': campaign, 'pre_game': pregame,
                  'selected_settlement': settlement['id'], 'selected_province': selected_province,
                  'economy_scope_roundtrip': True, 'construction_scope_roundtrip': True,
                  'facility_ids_preserved': sorted(expected_ids), 'project_ids': sorted(expected_project_ids),
                  'dialog_focus_contained_and_restored': True, 'initial_empty_map_truthful': True,
                  'pre_game_unknown_and_controls_disabled': True, 'camera_and_selection_preserved': True,
                  'campaign_state_unchanged': True, 'page_errors': page_errors,
                  'source_hashes': after_hashes, 'source_hashes_unchanged': True}
        (out / 'workflow.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(report, indent=2))
        browser.close()


if __name__ == '__main__':
    main()
