"""Capture the actual fictional-demo journey; no generated transition frames."""
import hashlib,json,os,time
from pathlib import Path
from playwright.sync_api import sync_playwright
from tests.browser_planet_orbit import HOOK
from tests.browser_navigation_continuity import HOOK_SYSTEM

MOTION='''(()=>{const t=setInterval(()=>{const a=window.HWSystemView;if(!a?.bridgeCircle)return;clearInterval(t);const f=a.bridgeCircle;window.__bridgeFrames=[];a.bridgeCircle=function(from,to,p){__bridgeFrames.push({from:{...from},to:{...to},progress:p,time:performance.now()});return f.apply(this,arguments);};},5)})()'''

def main():
    out=Path(os.environ.get('WOLD_JOURNEY_OUT','data/coherent-navigation/motion'));out.mkdir(parents=True,exist_ok=True)
    files=['public/app.js','public/system-view.js','public/system-previews.js','public/universe-view.js','public/orbit-background.js'];hashes=lambda:{f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in files};initial=hashes();scenes=[];errors=[]
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
        c=b.new_context(viewport={'width':1440,'height':1000},reduced_motion='no-preference',record_video_dir=str(out/'raw'),record_video_size={'width':1440,'height':1000});started=time.monotonic();page=c.new_page()
        for hook in [HOOK,HOOK_SYSTEM,MOTION]:page.add_init_script(hook)
        page.on('pageerror',lambda e:errors.append(str(e)))
        def level(value):page.wait_for_function('v=>document.querySelector("#map-level").value===v&&document.querySelector("#view-title h1").textContent.includes(v[0].toUpperCase()+v.slice(1))',arg=value,timeout=90000)
        def mark(name):
            page.wait_for_timeout(300);scenes.append({'name':name,'raw_seconds':round(time.monotonic()-started,2)});page.screenshot(path=str(out/(name+'.png')));print(json.dumps(scenes[-1]),flush=True);page.wait_for_timeout(900)
        def pull_out(target):
            for _ in range(40):
                if page.locator('#map-level').input_value()==target:break
                page.locator('#zoom-out').click();page.wait_for_timeout(380)
            level(target)
        base='http://127.0.0.1:4213';page.goto(base);page.wait_for_selector('#campaign-select option[value="nav-demo"]',state='attached');page.locator('[data-dialog-close]').click();page.evaluate("HWTheme.set('dark')")
        before=page.request.get(base+'/api/player/campaigns/nav-demo').json();page.select_option('#campaign-select','nav-demo');page.wait_for_function('window.__orbitAudit?.result',timeout=90000)
        page.select_option('#map-level','universe');level('universe');mark('01-universe')
        page.select_option('#universe-contact-select','nav-demo-region-01');page.wait_for_timeout(400);page.locator('#universe-open').click();level('galactic');mark('02-galactic')
        page.select_option('#map-level','sector');level('sector');mark('03-sector')
        page.select_option('#map-level','system');level('system');page.wait_for_function('HWSystemPreviewService.stateFor("nav-demo-planet-reach")==="ready"&&HWSystemPreviewService.stateFor("nav-demo-planet-ash")==="ready"',timeout=90000);mark('04-solar-system')
        page.select_option('#system-body-select','nav-demo-planet-reach');page.locator('#system-focus').click();page.wait_for_timeout(600);mark('05-focus-planet')
        page.locator('#system-orbit').click();level('planet');page.wait_for_function('document.querySelector("#orbit-toggle").textContent==="Surface"&&!document.querySelector("#zoom-in").disabled',timeout=90000);mark('06-enter-orbit')
        page.mouse.move(630,550);page.mouse.down();page.mouse.move(715,580,steps=16);page.mouse.up();page.wait_for_timeout(500)
        page.locator('#orbit-star-locate').click();page.wait_for_selector('.orbit-star-marker:visible');page.wait_for_timeout(500);page.locator('.orbit-star-marker:visible').click();page.wait_for_selector('#body-focus-view:visible');mark('07-sun')
        moon=next(n for n in before['state']['nodes'] if n['kind']=='moon' and n['parent_id']=='nav-demo-planet-reach');page.locator('#body-focus-view [data-body-id="'+moon['id']+'"]').click();page.wait_for_function('id=>document.querySelector("#body-focus-view").dataset.bodyId===id',arg=moon['id']);mark('08-moon-contact')
        page.locator('#body-focus-back').click();page.wait_for_function('document.querySelector("#body-focus-view").hidden');page.locator('#map-recenter').click();mark('09-return-planet')
        for _ in range(5):
            if page.evaluate('__orbitAudit.view.nightReadability')>.65:break
            page.locator('#zoom-in').click();page.wait_for_timeout(450)
        mark('10-close-orbit');page.locator('#orbit-toggle').click();page.wait_for_function('document.querySelector("#orbit-toggle").textContent==="Orbit"');mark('11-surface')
        page.mouse.move(610,540);page.mouse.down();page.mouse.move(735,580,steps=16);page.mouse.up();mark('12-surface-pan')
        page.locator('#orbit-toggle').click();page.wait_for_function('document.querySelector("#orbit-toggle").textContent==="Surface"');page.wait_for_timeout(500)
        page.select_option('#map-level','system');level('system');page.wait_for_function('!document.querySelector("#zoom-in").disabled');mark('13-close-orbit-return-system')
        page.select_option('#map-level','planet');level('planet');page.wait_for_function('document.querySelector("#orbit-toggle").textContent==="Surface"&&!document.querySelector("#zoom-in").disabled',timeout=90000);mark('14-restored-close-orbit')
        pull_out('system');page.wait_for_function('!document.querySelector("#zoom-in").disabled');mark('15-zoom-out-system')
        pull_out('universe');mark('16-zoom-out-universe')
        page.select_option('#universe-contact-select','nav-demo-sector-hearth');page.wait_for_timeout(500);mark('17-select-sector');page.locator('#universe-open').click();level('sector');mark('18-enter-sector')
        page.evaluate("HWTheme.set('light')");mark('19-light-sector');page.select_option('#map-level','system');level('system');mark('20-light-system')
        frames=page.evaluate('__bridgeFrames');assert not errors,errors;assert before==page.request.get(base+'/api/player/campaigns/nav-demo').json();assert hashes()==initial
        video=page.video;c.close();report={'browser':b.version,'raw_video':video.path(),'trim_start_seconds':max(0,scenes[0]['raw_seconds']-1),'scenes':scenes,'bridge_frames':frames,'page_errors':errors,'records_unchanged':True,'source_hashes':hashes(),'limits':'Actual normal-motion software Chromium capture, not hardware or physical-phone validation. Moon contact has no recorded terrain. No generated in-between frames.'};(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps({'video':report['raw_video'],'bridge_frames':len(frames),'errors':errors}));b.close()

if __name__=='__main__':main()
