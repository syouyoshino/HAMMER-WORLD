"""Read-only camera, compositing and resource checks for the adaptive orbital sky."""
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
from tests.browser_quality_control import act

SKY_HOOK = '''(()=>{const timer=setInterval(()=>{const sky=window.HWOrbitBackground;if(!sky)return;
 clearInterval(timer);const draw=sky.draw,a=window.__skyAudit={calls:0,times:[],targets:new Set(),peak:0,original:draw};
 sky.draw=function(ctx,w,h,view,rect){const start=performance.now();a.calls++;a.targets.add(ctx.canvas);
 if(!ctx.canvas.isConnected)a.peak=Math.max(a.peak,ctx.canvas.width*ctx.canvas.height);
 a.last={w,h,view:{...view},rect:{...rect}};const r=draw(ctx,w,h,view,rect);a.times.push(performance.now()-start);return r;};},5)})()'''


def main():
    base = os.environ.get('WOLD_QC_BASE', 'http://127.0.0.1:4203').rstrip('/')
    campaign = os.environ.get('WOLD_QC_CAMPAIGN', 'material-caps')
    out = Path(os.environ.get('WOLD_SKY_OUT', ROOT / 'data/space-background/browser'))
    out.mkdir(parents=True, exist_ok=True)
    paths = ['public/app.js', 'public/index.html', 'public/orbit-background.js']
    hashes = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}
    initial_hashes, errors = hashes(), []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox', '--disable-dev-shm-usage'])
        page = browser.new_page(viewport={'width': 1440, 'height': 1024})
        page.add_init_script(HOOK); page.add_init_script(SKY_HOOK)
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(base)
        page.wait_for_selector(f'#campaign-select option[value="{campaign}"]', state='attached')
        act(page, out, 'close-access', lambda: page.locator('[data-dialog-close]').click())
        before = page.request.get(f'{base}/api/player/campaigns/{quote(campaign)}').json()
        act(page, out, 'select-campaign', lambda: page.select_option('#campaign-select', campaign))
        page.wait_for_selector('.orbit-landmark:visible', timeout=90000)
        page.wait_for_function('window.__skyAudit?.calls>0'); page.wait_for_timeout(800)
        canvas = page.locator('#planet-map').element_handle()

        def pose(): return page.evaluate('window.__orbitAudit.view')
        def space_hash():
            return page.evaluate('''()=>{const c=document.querySelector('#planet-map'),ctx=c.getContext('2d'),
              d=ctx.getImageData(20,250,280,500).data;let hash=2166136261;
              for(let i=0;i<d.length;i+=4)hash=Math.imul(hash^d[i]^d[i+1]^d[i+2],16777619);
              return hash>>>0}''')
        def capture(name):
            page.wait_for_timeout(600); page.screenshot(path=str(out / f'{name}.png'))
            (out / f'{name}-aria.yml').write_text(page.locator('body').aria_snapshot())

        calls = page.evaluate('__skyAudit.calls'); page.wait_for_timeout(400)
        assert page.evaluate('__skyAudit.calls') == calls, 'Idle sky unexpectedly redraws'
        original, first = pose(), space_hash(); capture('01-orbit')
        rect = page.evaluate('__orbitAudit.rect')
        cx, cy = rect['left'] + rect['width']/2, rect['top'] + rect['height']/2
        start = next({'x': cx+dx, 'y': cy+dy} for dx, dy in [(140,40),(-140,70),(180,-90)]
                     if page.evaluate('p=>document.elementFromPoint(p.x,p.y)?.id==="planet-map"', {'x':cx+dx,'y':cy+dy}))
        act(page, out, 'orbit-drag', lambda: (page.mouse.move(start['x'],start['y']), page.mouse.down(),
            page.mouse.move(start['x']+160,start['y']+55,steps=18),page.mouse.up()))
        page.wait_for_timeout(200); rotated, second = pose(), space_hash()
        assert rotated != original and second != first, 'Orbit must change the visible background'
        capture('02-rotated')
        act(page, out, 'pull-back', lambda: page.locator('#zoom-out').click())
        page.wait_for_timeout(200); third = space_hash()
        assert pose()['distance'] > rotated['distance'] and third != second
        view = pose(); capture('03-pullback')
        act(page, out, 'dark-mode', lambda: page.evaluate('HWTheme.set("dark")'))
        page.wait_for_timeout(150)
        assert space_hash() == third, 'Interface theme must not recolor physical space'
        capture('04-dark')
        act(page, out, 'menu', lambda: page.locator('#hw-command').click())
        act(page, out, 'economy', lambda: page.locator('#command-menu [data-open="economy"]').click())
        act(page, out, 'return-map', lambda: page.locator('[data-return-map]:visible').click())
        page.wait_for_timeout(600); assert pose() == view

        # Sample real transitional frames, retaining the full viewport for review.
        for cycle in range(5):
            act(page, out, f'surface-{cycle}', lambda: page.locator('#orbit-toggle').click())
            if cycle == 0:
                page.wait_for_timeout(100); page.screenshot(path=str(out/'05-surface-transition.png'))
            page.wait_for_timeout(650)
            n = page.evaluate('__skyAudit.calls'); page.wait_for_timeout(100)
            assert page.evaluate('__skyAudit.calls') == n, 'Sky draws after the surface transition ends'
            if cycle == 0: capture('06-surface')
            act(page, out, f'orbit-{cycle}', lambda: page.locator('#orbit-toggle').click())
            if cycle == 0:
                page.wait_for_timeout(100); page.screenshot(path=str(out/'07-orbit-transition.png'))
            page.wait_for_timeout(650)
            assert page.locator('#orbit-toggle').get_attribute('aria-pressed') == 'true'
        capture('08-orbit-return')
        resources = page.evaluate('''()=>({offscreenActive:[...__skyAudit.targets].filter(c=>!c.isConnected&&c.width*c.height>1).length,
          peakCompositePixels:__skyAudit.peak,skyCalls:__skyAudit.calls,drawMs:__skyAudit.times})''')
        assert resources['offscreenActive'] == 0, 'Transition composite retained pixels after settling'
        assert 0 < resources['peakCompositePixels'] <= 2097152
        assert canvas.evaluate('c=>c===document.querySelector("#planet-map")')

        # Verify missing optional sky module still provides a clean orbital backdrop.
        act(page, out, 'disable-sky-module', lambda: page.evaluate('window.HWOrbitBackground=undefined'))
        act(page, out, 'fallback-redraw', lambda: page.locator('#zoom-out').click())
        capture('09-module-fallback')
        after = page.request.get(f'{base}/api/player/campaigns/{quote(campaign)}').json()
        assert before == after and not errors and initial_hashes == hashes()
        report = {'browser':browser.version,'viewport':[1440,1024], 'orbit_background_pixels_change':True,
                  'zoom_background_pixels_change':True,'theme_preserves_space':True,'idle_has_no_sky_frames':True,
                  'map_canvas_retained':True,'surface_orbit_cycles':5,'resources':resources,
                  'campaign_records_unchanged':True,'optional_module_fallback':True,'page_errors':errors,'source_hashes':hashes()}
        (out/'workflow.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:v for k,v in report.items() if k!='resources'},indent=2));browser.close()

if __name__ == '__main__': main()
