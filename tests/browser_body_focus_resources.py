"""Read-only focus resource lifetime and desktop CSS-zoom regression.

Requires the same surveyed static-astronomy fixture as browser_body_focus.py.
CSS zoom coverage is not a claim of native browser zoom or physical GPU FPS.
"""
import sys,json,time,statistics,os,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from playwright.sync_api import sync_playwright
from tests.browser_planet_orbit import HOOK
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage']);page=b.new_page(viewport={'width':1440,'height':1024});page.add_init_script(HOOK);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 base=os.environ.get('WOLD_BODY_FOCUS_BASE','http://127.0.0.1:4213');campaign=os.environ.get('WOLD_BODY_FOCUS_CAMPAIGN','nav-demo')
 page.goto(base);page.wait_for_selector(f'#campaign-select option[value="{campaign}"]',state='attached')
 if page.locator('[data-dialog-close]').is_visible():page.locator('[data-dialog-close]').click()
 page.select_option('#campaign-select',campaign);page.wait_for_function('window.__orbitAudit?.result',timeout=90000);page.locator('#orbit-star-locate').click();page.wait_for_selector('.orbit-star-marker:visible');page.wait_for_timeout(700)
 canvas=page.locator('#planet-map').element_handle();page.evaluate('window.__resourceOrbit=__orbitEngine')
 cdp=page.context.new_cdp_session(page);cdp.send('Performance.enable')
 metrics=lambda:{m['name']:m['value'] for m in cdp.send('Performance.getMetrics')['metrics'] if m['name'] in ['JSEventListeners','Nodes','JSHeapUsedSize']}
 for i in range(3):page.locator('.orbit-star-marker').click();page.locator('#body-focus-back').click()
 cdp.send('HeapProfiler.collectGarbage');before=metrics();times=[]
 for i in range(20):
  t=time.monotonic();page.locator('.orbit-star-marker').click();page.locator('#body-focus-back').click();times.append((time.monotonic()-t)*1000)
 cdp.send('HeapProfiler.collectGarbage');after=metrics();assert before['JSEventListeners']==after['JSEventListeners'],(before,after)
 assert canvas.evaluate('c=>c===document.querySelector("#planet-map")') and page.evaluate('__resourceOrbit===__orbitEngine')
 print(json.dumps({'cycles':20,'before':before,'after':after,'median_ms':statistics.median(times),'max_ms':max(times),'same_canvas_renderer':True}),flush=True)
 sizes=[]
 for width,height,zoom in [(1280,720,1),(1920,1080,1),(1280,720,1.5),(1440,1024,2)]:
  page.set_viewport_size({'width':width,'height':height});page.evaluate('z=>document.documentElement.style.zoom=z',zoom);page.wait_for_timeout(700);page.locator('.orbit-star-marker').click();page.wait_for_timeout(700);focus=page.locator('#body-focus-view').bounding_box();assert 0<=focus['x'] and focus['x']+focus['width']<=width+1 and 0<=focus['y']<height,focus;page.locator('#body-focus-back').scroll_into_view_if_needed();r=page.locator('#body-focus-back').bounding_box();assert 0<=r['x']<width and 0<=r['y']<height,r;page.locator('#body-focus-back').click();sizes.append([width,height,zoom])
 assert not errors
 report={'cycles':20,'warm_before':before,'after':after,'roundtrip_median_ms':round(statistics.median(times),1),'roundtrip_max_ms':round(max(times),1),'same_canvas_and_orbit_renderer':True,'desktop_sizes_css_zoom':sizes,'browser':b.version,'page_errors':errors,'limits':'Shared Linux two-CPU quota; browser automation wall time, no GPU/FPS claim. CSS zoom only, not native browser zoom.'}
 report['source_hashes']={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['public/app.js','public/body-focus.js','public/style.css']}
 out=Path(os.environ.get('WOLD_BODY_FOCUS_RESOURCE_REPORT',ROOT/'data/scale-focus/resource-check.json'));out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2));print(json.dumps(report));b.close()
