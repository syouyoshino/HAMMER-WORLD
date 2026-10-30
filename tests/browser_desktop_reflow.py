"""Actual desktop control reachability, reflow and map input at CSS zoom.

Uses the same isolated surveyed static-v1 fixture as browser_body_focus.py.
CSS zoom is explicitly separate from native browser zoom and Safari coverage.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tests.browser_planet_orbit import HOOK


def main():
    base=os.environ.get('WOLD_BODY_FOCUS_BASE','http://127.0.0.1:4213')
    campaign=os.environ.get('WOLD_BODY_FOCUS_CAMPAIGN','nav-demo')
    out=Path(os.environ.get('WOLD_REFLOW_OUT',ROOT/'data/terrain-finish/reflow'));out.mkdir(parents=True,exist_ok=True)
    sources=['public/app.js','public/style.css','public/desktop-shell.css','public/desktop-shell.js']
    hashes=lambda:{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in sources}
    initial=hashes();errors=[];rows=[]
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
        page=b.new_page(viewport={'width':1280,'height':720});page.add_init_script(HOOK);page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(base);page.wait_for_selector(f'#campaign-select option[value="{campaign}"]',state='attached')
        if page.locator('[data-dialog-close]').is_visible():page.locator('[data-dialog-close]').click()
        before=page.request.get(f'{base}/api/player/campaigns/{campaign}').json();page.select_option('#campaign-select',campaign)
        page.wait_for_function('window.__orbitAudit?.result',timeout=90000);canvas=page.locator('#planet-map').element_handle()
        for width,height,z in [(1280,720,1),(1280,720,1.5),(1280,720,2),(1920,1080,1)]:
            label=f'{width}-{height}-{z}';page.set_viewport_size({'width':width,'height':height});page.evaluate('z=>document.documentElement.style.zoom=z',z);page.wait_for_timeout(800)
            page.screenshot(path=str(out/f'{label}.png'))
            (out/f'{label}.yml').write_text(page.locator('body').aria_snapshot())
            rects={}
            for selector in ['#hw-command','#campaign-select','#command-turn','#command-pending','#refresh-button','#map-level','#overlay-select','#map-style','#orbit-toggle','#orbit-star-locate','#feature-name-toggle','#feature-list-button','#zoom-in','#zoom-out','#zoom-reset','#map-recenter']:
                node=page.locator(selector)
                assert node.count()==1,(label,selector,'Missing or duplicate control')
                if not node.is_visible():continue
                r=node.bounding_box();assert r and r['width']>0 and r['height']>0,(label,selector,r)
                assert r['x']>=-1 and r['y']>=-1 and r['x']+r['width']<=width+1 and r['y']+r['height']<=height+1,(label,selector,r)
                rects[selector]=r
            def overlap(a,b):return min(a['x']+a['width'],b['x']+b['width'])-max(a['x'],b['x'])>1 and min(a['y']+a['height'],b['y']+b['height'])-max(a['y'],b['y'])>1
            keys=['#hw-command','#campaign-select','#command-turn','#command-pending','#refresh-button']
            for i,a in enumerate(keys):
                for c in keys[i+1:]:
                    if a in rects and c in rects:assert not overlap(rects[a],rects[c]),(label,a,c,rects)
            zoom_rows=[rects[k]['y'] for k in ['#zoom-out','#zoom-reset','#zoom-in','#map-recenter']]
            assert max(zoom_rows)-min(zoom_rows)<2,(label,'Zoom controls split across rows',zoom_rows)
            title=page.locator('#view-title').bounding_box();crumb=page.locator('#map-breadcrumbs').bounding_box()
            assert crumb['y']>=title['y']+title['height']-1,(label,title,crumb)
            point=page.evaluate('''()=>{for(let y=innerHeight*.55;y<innerHeight-100;y+=35)for(let x=innerWidth*.2;x<innerWidth*.8;x+=40)if(document.elementFromPoint(x,y)?.id==='planet-map')return{x,y};return null}''')
            assert point,(label,'No exposed map input')
            pose=page.evaluate('__orbitAudit.view');page.mouse.move(point['x'],point['y']);page.mouse.down();page.mouse.move(point['x']+35,point['y']+12,steps=5);page.mouse.up();page.wait_for_timeout(250)
            assert pose!=page.evaluate('__orbitAudit.view'),(label,'Map drag had no effect')
            page.locator('#hw-command').click();page.wait_for_selector('#command-menu:visible');page.locator('#command-menu [data-open="economy"]').click();page.wait_for_selector('#command-workspace:visible');page.locator('[data-return-map]').click();page.wait_for_selector('#command-workspace',state='hidden')
            assert canvas.evaluate('c=>c===document.querySelector("#planet-map")')
            rows.append({'viewport':[width,height],'css_zoom':z,'control_bounds':rects,'map_drag_and_management_return':True,'zoom_group_same_row':True})
        after=page.request.get(f'{base}/api/player/campaigns/{campaign}').json();assert before==after;assert not errors;assert initial==hashes()
        report={'browser':b.version,'rows':rows,'records_unchanged':True,'same_canvas':True,'page_errors':errors,'source_hashes':hashes(),'limits':'Desktop CSS zoom only; no native browser zoom or Safari claim.'}
        (out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));b.close()

if __name__=='__main__':main()
