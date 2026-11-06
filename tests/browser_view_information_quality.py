"""Recorded context, readable celestial states and visible province targets."""
import hashlib,json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
from tests.browser_planet_orbit import HOOK

CONTRAST='''node=>{const canvas=document.createElement('canvas');canvas.width=canvas.height=1;const ctx=canvas.getContext('2d',{willReadFrequently:true}),colors=new Map();const rgb=s=>{if(colors.has(s))return colors.get(s);ctx.clearRect(0,0,1,1);ctx.fillStyle=s||'transparent';ctx.fillRect(0,0,1,1);const d=ctx.getImageData(0,0,1,1).data,c=[d[0],d[1],d[2],d[3]/255];colors.set(s,c);return c;};function backdrop(el){if(!el)return[8,15,21];const c=rgb(getComputedStyle(el).backgroundColor),a=c[3];if(a===1)return c.slice(0,3);const below=backdrop(el.parentElement);return below.map((v,i)=>v*(1-a)+c[i]*a)}const fg=rgb(getComputedStyle(node).color),bg=backdrop(node),a=fg[3],front=bg.map((v,i)=>v*(1-a)+fg[i]*a);const lum=v=>v.map(c=>{c/=255;return c<=.04045?c/12.92:((c+.055)/1.055)**2.4}).reduce((s,c,i)=>s+c*[.2126,.7152,.0722][i],0);const x=lum(front),y=lum(bg);return(Math.max(x,y)+.05)/(Math.min(x,y)+.05)}'''


def contrast(locator):
    # Focus rendering can replace a resolved node before Playwright evaluates it.
    # Detached elements have empty computed styles; those are not color samples.
    for _ in range(10):
        value=locator.evaluate('node=>node.isConnected?('+CONTRAST+')(node):null')
        if value is not None:
            return value
    raise AssertionError('Contrast target did not remain attached for measurement')

def main():
    out=Path(os.environ.get('WOLD_VIEW_QUALITY_OUT','data/deep-critique/view-quality'));out.mkdir(parents=True,exist_ok=True)
    files=['public/app.js','public/body-focus.js','public/style.css','public/desktop-shell.css','public/planet-orbit.js','public/system-view.js','public/universe-view.js','public/map-renderer.js'];hashes=lambda:{f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in files};initial=hashes();errors=[];ratios={}
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage']);page=b.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce');page.add_init_script(HOOK);page.on('pageerror',lambda e:errors.append(str(e)));base='http://127.0.0.1:4213';page.goto(base);page.wait_for_selector('#campaign-select option[value="nav-demo"]',state='attached');page.locator('[data-dialog-close]').click();before=page.request.get(base+'/api/player/campaigns/nav-demo').json();moon=next(n for n in before['state']['nodes'] if n['kind']=='moon' and n['parent_id']=='nav-demo-planet-reach');page.select_option('#campaign-select','nav-demo');page.wait_for_function('window.__orbitAudit?.result',timeout=90000)
        for theme in ['dark','light']:
            page.evaluate('(t)=>HWTheme.set(t)',theme)
            scope=page.locator('#map-breadcrumbs .map-level-step').first;scope.hover();scope_hover=contrast(scope.locator('small'));page.mouse.move(20,20);scope.focus();page.keyboard.press('Tab');scope_focus=contrast(page.locator('#map-breadcrumbs .map-level-step:focus-visible small'))
            page.locator('#orbit-star-locate').click();page.wait_for_selector('.orbit-star-marker:visible');camera=page.evaluate('({...__orbitAudit.view})');page.locator('.orbit-star-marker:visible').click();page.wait_for_selector('#body-focus-view:visible')
            assert 'Cinder Star' in page.locator('#map-breadcrumbs').inner_text(),'Focused star needs its own ancestry, not a Reach-ending source breadcrumb'
            for selector in ['#overlay-select','#map-style','#map-level']:
                assert page.locator(selector).is_hidden(),selector
            page.wait_for_timeout(250)
            assert page.locator('#body-focus-view h2').evaluate('node=>node===document.activeElement'),'Opening a body must retain heading focus after queued redraws'
            page.keyboard.press('Tab')
            back=page.locator('#body-focus-back');label=back.inner_text().lower();assert 'reach' in label and 'orbit' in label,label
            assert back.evaluate('node=>node===document.activeElement'),'Tab from the focused heading must reach its named return'
            page.set_viewport_size({'width':1430,'height':1000});page.wait_for_timeout(250)
            assert back.evaluate('node=>node===document.activeElement'),'Incidental resize redraw must preserve focused record controls'
            page.set_viewport_size({'width':1440,'height':1000});page.wait_for_timeout(250)
            assert back.evaluate('node=>node===document.activeElement'),'Restored viewport must preserve focused record controls'
            selected=page.locator('.known-body-row[aria-current="true"]');name=selected.locator('.known-body-name');meta=selected.locator('.known-body-meta');ratios[theme]={'selected_name':contrast(name),'selected_meta':contrast(meta),'scope_kind_hover':scope_hover,'scope_kind_focus':scope_focus}
            other=page.locator('.known-body-row[data-body-id="nav-demo-planet-ash"]');ratios[theme]['normal_name']=contrast(other.locator('.known-body-name'));ratios[theme]['normal_meta']=contrast(other.locator('.known-body-meta'));other.hover();ratios[theme]['hover_name']=contrast(other.locator('.known-body-name'));ratios[theme]['hover_meta']=contrast(other.locator('.known-body-meta'))
            assert all(value>=4.5 for value in ratios[theme].values()),ratios[theme]
            page.mouse.move(30,20);page.screenshot(path=str(out/(theme+'-star.png')))
            page.locator('#body-focus-view [data-body-id="'+moon['id']+'"]').click();page.wait_for_function('id=>document.querySelector("#body-focus-view").dataset.bodyId===id',arg=moon['id']);crumb=page.locator('#map-breadcrumbs').inner_text();assert 'Reach' in crumb and (moon.get('name') or 'Unknown') in crumb,crumb
            assert 'Unknown' in page.locator('#body-focus-view').inner_text();page.screenshot(path=str(out/(theme+'-moon.png')));back.click();page.wait_for_function('document.querySelector("#body-focus-view").hidden');assert page.evaluate('__orbitAudit.view')==camera,'Named return must still restore the complete recorded source view'
        # Recenter onto the recorded settlement/night-side terrain. Useful Orbit
        # must offer analytical illumination before the final surface threshold.
        page.evaluate("HWTheme.set('dark')");page.locator('#map-recenter').click()
        # Locate deliberately pulled back to 4.2 radii; Recenter preserves scale.
        # Exercise analytical lighting at a useful strategic distance via controls.
        page.locator('#zoom-reset').click()
        for _ in range(2):
            page.locator('#zoom-in').click()
        page.wait_for_function('__orbitAudit.view.distance<=1.75')
        assert page.locator('#orbit-toggle').inner_text()=='Surface','Useful strategic zoom must remain in Orbit'
        night=page.evaluate('({...__orbitAudit.view})');assert night['nightReadability']>.25,night;page.screenshot(path=str(out/'night-readable.png'))
        page.locator('#orbit-toggle').click();page.wait_for_function('document.querySelector("#orbit-toggle").textContent==="Orbit"');page.wait_for_timeout(600)
        assert page.locator('.planet-orbit-layer').evaluate('node=>getComputedStyle(node).visibility==="hidden"'),'Reduced-motion Surface must hide the native globe layer'
        point=page.evaluate('''()=>{const o=__surfaceAudit.o,t=__surfaceAudit.t,g=o.geometry;for(const entry of HWMapRenderer.provinceLand(g).values()){const a=entry.anchor;if(!a)continue;const x=t.ox+(a.x+.5)*t.tile,y=t.oy+(a.y+.5)*t.tile;if(x>40&&x<innerWidth-40&&y>210&&y<innerHeight-120&&document.elementFromPoint(x,y)?.id==='planet-map')return{x,y};}return null;}''');assert point,'Need a visible recorded land anchor'
        page.mouse.move(30,20);page.wait_for_timeout(100);page.evaluate('window.__beforeHover=__permanentCanvas=document.querySelector("#planet-map");window.__beforeHoverPixels=__permanentCanvas.getContext("2d").getImageData(0,0,__permanentCanvas.width,__permanentCanvas.height).data')
        page.mouse.move(point['x'],point['y']);page.wait_for_timeout(200);changed=page.evaluate('''()=>{const after=__permanentCanvas.getContext('2d').getImageData(0,0,__permanentCanvas.width,__permanentCanvas.height).data;let n=0;for(let i=0;i<after.length;i+=4)if(after[i]!==__beforeHoverPixels[i]||after[i+1]!==__beforeHoverPixels[i+1]||after[i+2]!==__beforeHoverPixels[i+2])n++;return n}''');assert changed>=50,'Province hover must reveal its actual map target, not only a floating tooltip';page.screenshot(path=str(out/'surface-province-hover.png'))
        assert page.locator('.planet-orbit-layer').evaluate('node=>getComputedStyle(node).visibility==="hidden"'),'Surface hover must not reveal a cached native globe'
        tip=page.locator('#map-tooltip');assert tip.is_visible();a=tip.bounding_box();b_marker=page.locator('#entry-focus-marker').bounding_box();assert b_marker and not (a['x']<b_marker['x']+b_marker['width'] and a['x']+a['width']>b_marker['x'] and a['y']<b_marker['y']+b_marker['height'] and a['y']+a['height']>b_marker['y']),'Surface tooltip must avoid the actual entry anchor'
        page.emulate_media(reduced_motion='no-preference');page.locator('#orbit-toggle').click();page.wait_for_function('document.querySelector("#orbit-toggle").textContent==="Surface"');page.wait_for_timeout(600)
        page.locator('#orbit-toggle').click();page.wait_for_function('document.querySelector("#orbit-toggle").textContent==="Orbit"');page.wait_for_function('getComputedStyle(document.querySelector(".planet-orbit-layer")).visibility==="hidden"');page.mouse.move(30,20);page.mouse.move(point['x'],point['y']);page.wait_for_timeout(200)
        assert page.locator('.planet-orbit-layer').evaluate('node=>getComputedStyle(node).visibility==="hidden"'),'Normal-motion Surface hover must keep the completed fade hidden';page.screenshot(path=str(out/'surface-normal-motion.png'))
        assert before==page.request.get(base+'/api/player/campaigns/nav-demo').json();assert not errors and initial==hashes(),errors
        report={'browser':b.version,'celestial_selected_and_hover_contrast':ratios,'focused_ancestry_and_named_return':True,'complete_source_camera_return':True,'celestial_keyboard_focus_retained':True,'night_readability':night,'province_hover_changed_pixels':changed,'records_unchanged':True,'page_errors':errors,'source_hashes':hashes(),'limits':'Computed control contrast and exercised input are targeted product checks, not an accessibility-compliance certification. One recorded fixture, software Chromium.'};(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));b.close()

if __name__=='__main__':main()
