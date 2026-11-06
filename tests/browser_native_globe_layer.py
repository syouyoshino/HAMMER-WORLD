"""Actual direct-globe presentation, input and authority lifecycle regression."""
import hashlib,json,os,time
from pathlib import Path
from playwright.sync_api import sync_playwright
from tests.browser_planet_orbit import HOOK

COPY_HOOK='''(()=>{window.__globeCopies=[];const p=CanvasRenderingContext2D.prototype,f=p.drawImage;p.drawImage=function(source,...args){if(source===window.__orbitEngine?.canvas)__globeCopies.push({time:performance.now(),target:[this.canvas.width,this.canvas.height]});return f.call(this,source,...args);};})()'''

def main():
    out=Path(os.environ.get('WOLD_NATIVE_LAYER_OUT','data/deep-critique/native-layer'));out.mkdir(parents=True,exist_ok=True)
    files=['public/app.js','public/planet-orbit.js','public/desktop-shell.css'];hashes=lambda:{f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in files};initial=hashes();errors=[]
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage']);c=b.new_context(viewport={'width':1440,'height':1000},reduced_motion='no-preference');page=c.new_page()
        page.add_init_script(HOOK);page.add_init_script(COPY_HOOK);page.on('pageerror',lambda e:errors.append(str(e)));base='http://127.0.0.1:4213';page.goto(base);page.wait_for_selector('#campaign-select option[value="nav-demo"]',state='attached');page.locator('[data-dialog-close]').click();before=page.request.get(base+'/api/player/campaigns/nav-demo').json();page.select_option('#campaign-select','nav-demo');page.wait_for_function('window.__orbitAudit?.result',timeout=90000);page.wait_for_timeout(700)
        page.evaluate('window.__permanentMap=document.querySelector("#planet-map");window.__nativeGlobe=__orbitEngine.canvas')
        visible='getComputedStyle(__nativeGlobe).visibility!=="hidden"&&getComputedStyle(__nativeGlobe).display!=="none"&&Number(getComputedStyle(__nativeGlobe).opacity)>0'
        assert page.evaluate(visible),'A separate visible native globe must be presented'
        assert page.evaluate('getComputedStyle(__nativeGlobe).pointerEvents')=='none'
        assert page.evaluate('document.elementFromPoint(720,550)===__permanentMap'),'The globe must not capture map input'
        assert page.evaluate('__globeCopies.length')==0,'Ordinary orbit must not copy the globe into 2D'
        page.screenshot(path=str(out/'01-native-orbit.png'))
        start=page.evaluate('({...__orbitAudit.view})');page.evaluate('window.__motionStart=performance.now();window.__motionRafs=[];window.__measureMotion=true;function tick(t){if(!__measureMotion)return;__motionRafs.push(t);requestAnimationFrame(tick)};requestAnimationFrame(tick)')
        began=time.monotonic();page.mouse.move(650,540);page.mouse.down();page.mouse.move(815,580,steps=20);page.mouse.up();page.wait_for_timeout(900);elapsed=time.monotonic()-began;page.evaluate('__measureMotion=false');after=page.evaluate('({...__orbitAudit.view})');assert after['longitude']!=start['longitude'];assert page.evaluate('__globeCopies.length')==0,'Dragging must stay on the direct native presentation path'
        rafs=page.evaluate('__motionRafs');gaps=[b-a for a,b in zip(rafs,rafs[1:])];assert len(gaps)>2
        page.screenshot(path=str(out/'02-dragged-orbit.png'))
        page.locator('#orbit-toggle').click();page.wait_for_function('document.querySelector("#orbit-toggle").textContent==="Orbit"');page.wait_for_timeout(700);assert not page.evaluate(visible),'Surface must hide the globe after its fade';page.screenshot(path=str(out/'03-surface.png'))
        page.locator('#orbit-toggle').click();page.wait_for_function('document.querySelector("#orbit-toggle").textContent==="Surface"');page.wait_for_timeout(700);assert page.evaluate(visible)
        page.locator('#orbit-star-locate').click();page.wait_for_selector('.orbit-star-marker:visible');page.locator('.orbit-star-marker:visible').click();page.wait_for_selector('#body-focus-view:visible');assert not page.evaluate(visible),'Unmapped celestial focus cannot leave an old planet exposed';page.locator('#body-focus-back').click();page.wait_for_function('document.querySelector("#body-focus-view").hidden');page.wait_for_timeout(700);assert page.evaluate(visible)
        page.select_option('#map-level','system');page.wait_for_function('document.querySelector("#view-title h1").textContent.includes("System")');page.wait_for_timeout(800);assert not page.evaluate(visible),'Completed System return must hide the native globe';assert page.evaluate('document.querySelectorAll(".planet-orbit-layer").length')==1
        page.select_option('#map-level','planet');page.wait_for_function('document.querySelector("#view-title h1").textContent.includes("Planet")&&!document.querySelector("#zoom-in").disabled',timeout=90000);page.wait_for_timeout(700)
        assert page.evaluate('__nativeGlobe===__orbitEngine.canvas&&__permanentMap===document.querySelector("#planet-map")')
        # Context clearing must not retain a previous world's displayed pixels.
        page.select_option('#campaign-select','legacy-demo');page.wait_for_timeout(200);assert not page.evaluate(visible),'Campaign clearing must immediately hide previous globe pixels'
        assert before==page.request.get(base+'/api/player/campaigns/nav-demo').json()
        # A high-DPR desktop must not multiply output work without a bound.
        dense=b.new_context(viewport={'width':1440,'height':1000},device_scale_factor=2,reduced_motion='reduce');d=dense.new_page();d.add_init_script(HOOK);d.on('pageerror',lambda e:errors.append(str(e)));d.goto(base);d.wait_for_selector('#campaign-select option[value="nav-demo"]',state='attached');d.locator('[data-dialog-close]').click();d.select_option('#campaign-select','nav-demo');d.wait_for_function('window.__orbitAudit?.result',timeout=90000)
        buffer=d.evaluate('({width:__orbitEngine.canvas.width,height:__orbitEngine.canvas.height})');assert max(buffer.values())<=2048 and buffer['width']*buffer['height']<=2_097_152,buffer
        d.screenshot(path=str(out/'04-dpr2-orbit.png'))
        d.evaluate('__orbitEngine.gl.getExtension("WEBGL_lose_context").loseContext()');d.wait_for_function('getComputedStyle(__orbitEngine.canvas).visibility==="hidden"');d.wait_for_timeout(200);assert d.locator('#orbit-toggle').is_hidden(),'Lost context must expose the surface fallback';dense.close()
        assert not errors and hashes()==initial,errors
        report={'browser':b.version,'same_map_and_renderer_canvas':True,'native_pointer_passthrough':True,'zero_continuous_globe_copies':True,'surface_focus_system_campaign_layer_isolation':True,'dpr2_buffer':buffer,'context_loss_surface_fallback':True,'drag_elapsed_seconds':elapsed,'raf_gap_ms_median':sorted(gaps)[len(gaps)//2],'raf_gap_ms_max':max(gaps),'raf_samples':len(rafs),'copies':page.evaluate('__globeCopies'),'records_unchanged':True,'page_errors':errors,'source_hashes':hashes(),'limits':'One software Chromium fixture. RAF cadence is main-thread scheduling, not presented hardware FPS; screenshots and native recording establish visible composition separately.'};(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));b.close()

if __name__=='__main__':main()
