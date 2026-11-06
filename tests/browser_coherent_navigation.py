"""Native chart/planet handoff and authorization regression, isolated demo only."""
import hashlib,json,os,time
from pathlib import Path
from playwright.sync_api import sync_playwright
from tests.browser_planet_orbit import HOOK
from tests.browser_navigation_continuity import HOOK_SYSTEM

ATLAS_HOOK='''(()=>{const t=setInterval(()=>{const a=window.HWUniverseView;if(!a)return;clearInterval(t);for(const k of ['draw','drawStrategic']){const f=a[k];a[k]=function(c,o){const textRects=[],original=c.fillText;c.fillText=function(s,x,y,max){if(s==='DESTINATION'||s==='Hearth'||s.startsWith('Origin:')||s.startsWith('Known sectors in ')){const w=Math.min(c.measureText(s).width,max||Infinity),left=c.textAlign==='center'?x-w/2:c.textAlign==='right'?x-w:x;textRects.push(s==='DESTINATION'?{text:s,left:x-3,right:x+109,top:y-11,bottom:y+6}:{text:s,left,right:left+w,top:y-12,bottom:y+3});}return original.apply(this,arguments);};let r;try{r=f.call(this,c,o);}finally{c.fillText=original;}window.__chartAudit={level:o.record.level,theme:o.theme,layout:r,textRects};return r;}}},5)})()'''

def main():
    base='http://127.0.0.1:4213';out=Path(os.environ.get('WOLD_COHERENT_OUT','data/coherent-navigation/candidate'));out.mkdir(parents=True,exist_ok=True)
    files=['public/app.js','public/universe-view.js','public/system-previews.js','public/system-view.js','public/orbit-background.js']
    hashes=lambda:{f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in files};initial=hashes();errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
        context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='no-preference');context.tracing.start(screenshots=True,snapshots=True)
        page=context.new_page()
        for h in [HOOK,HOOK_SYSTEM,ATLAS_HOOK]:page.add_init_script(h)
        page.on('pageerror',lambda e:errors.append(str(e)))
        def level(value):page.wait_for_function('v=>document.querySelector("#map-level").value===v&&document.querySelector("#view-title h1").textContent.includes(v[0].toUpperCase()+v.slice(1))',arg=value,timeout=90000)
        def snapshot(name):page.screenshot(path=str(out/(name+'.png')))
        page.goto(base);page.wait_for_selector('#campaign-select option[value="nav-demo"]',state='attached');page.locator('[data-dialog-close]').click();page.evaluate("HWTheme.set('dark')")
        before=page.request.get(base+'/api/player/campaigns/nav-demo').json();page.select_option('#campaign-select','nav-demo');page.wait_for_function('window.__orbitAudit?.result',timeout=90000);canvas=page.locator('#planet-map').element_handle()
        for value in ['universe','galactic','sector']:
            page.select_option('#map-level',value);level(value);page.wait_for_function('v=>window.__chartAudit?.level===v',arg=value)
            layout=page.evaluate('__chartAudit.layout');assert all(not t.get('uiOnly') for t in layout['contactAnchors'])
            assert all(t['n']['knowledge']!='detected' for t in layout['positions'])
            for control in ['#feature-name-toggle','#feature-list-button','#map-style']:assert page.locator(control).is_hidden(),control
            snapshot('01-'+value)
            if value=='universe':
                hearth=next(n for n in before['state']['nodes'] if n.get('name')=='Hearth' and n['kind']=='sector');page.select_option('#universe-contact-select',hearth['id'])
                for theme in ['light','dark']:
                    page.evaluate('(t)=>HWTheme.set(t)',theme);page.wait_for_function('t=>__chartAudit.theme===t',arg=theme);rects=page.evaluate('__chartAudit.textRects');origins=[r for r in rects if r['text'].startswith('Origin:')];parents=[r for r in rects if r['text'].startswith('Known sectors in ')];assert origins and parents
                    for a in origins:
                        for b in parents:assert not (a['left']<b['right'] and a['right']>b['left'] and a['top']<b['bottom'] and a['bottom']>b['top']),(a,b)
                    destination=next(r for r in rects if r['text']=='DESTINATION');selected=next(p for p in page.evaluate('__chartAudit.layout.positions') if p['n']['id']==hearth['id']);safe=page.evaluate('__chartAudit.layout.safeRect');assert safe['left']<=destination['left']<destination['right']<=safe['right'] and safe['top']<=destination['top']<destination['bottom']<=safe['bottom']
                    for other in parents+origins+[r for r in rects if r['text']=='Hearth']:
                        assert not (destination['left']<other['right'] and destination['right']>other['left'] and destination['top']<other['bottom'] and destination['bottom']>other['top']),(destination,other)
                    dx=selected['x']-max(destination['left'],min(selected['x'],destination['right']));dy=selected['y']-max(destination['top'],min(selected['y'],destination['bottom']));assert dx*dx+dy*dy>selected['radius']**2
                    snapshot('01-universe-'+theme)
        assert 'Kestrel Reach' in page.locator('#map-breadcrumbs').inner_text()
        page.evaluate("HWTheme.set('light')");page.wait_for_function('__chartAudit.theme==="light"');snapshot('02-light-sector');page.evaluate("HWTheme.set('dark')")
        page.select_option('#map-level','system');level('system');page.wait_for_function('window.__systemAudit?.layout.supported');page.wait_for_function('HWSystemPreviewService.stateFor("nav-demo-planet-reach")==="ready"&&HWSystemPreviewService.stateFor("nav-demo-planet-ash")==="ready"',timeout=90000)
        page.select_option('#system-body-select','nav-demo-planet-reach');page.wait_for_timeout(200);origin=page.evaluate('__systemAudit.view');snapshot('03-system')
        # The existing source stays authorized while preparation runs; a warm
        # entry must not download the same terrain again.
        requests=[];page.on('request',lambda r:requests.append(r.url) if '/detail?' in r.url and 'planet_id=nav-demo-planet-reach' in r.url else None)
        started=time.monotonic();page.locator('#system-orbit').click();level('planet');page.wait_for_function('document.querySelector("#orbit-toggle").textContent==="Surface"&&!document.querySelector("#zoom-in").disabled',timeout=90000);arrival=time.monotonic()-started
        assert not requests,'Ready detail must be reused during the handoff'
        assert page.locator('#zoom-in').is_enabled();snapshot('04-orbit-arrival')
        page.wait_for_timeout(1100)
        assert page.locator('#orbit-toggle').inner_text()=='Surface','Enter orbit must remain in orbit without an unsolicited surface descent'
        page.locator('#zoom-in').click();page.wait_for_timeout(400);assert page.locator('#zoom-out').is_enabled()
        page.locator('#orbit-toggle').click();page.wait_for_function('document.querySelector("#orbit-toggle").textContent==="Orbit"');snapshot('05-surface')
        page.locator('#orbit-toggle').click();page.wait_for_function('document.querySelector("#orbit-toggle").textContent==="Surface"')
        page.select_option('#map-level','system');level('system');page.wait_for_timeout(500);assert page.evaluate('__systemAudit.view')==origin,'Return must restore the exact saved System camera';snapshot('06-return-system')
        page.evaluate("HWTheme.set('light')");page.wait_for_timeout(350);snapshot('07-light-system')
        # A cold second browser holds the other planet's terrain while entry is
        # requested, then changes campaign before that old response is released.
        cold=browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce');cold.on('pageerror',lambda e:errors.append(str(e)));held=[]
        cold.goto(base);cold.wait_for_selector('#campaign-select option[value="nav-demo"]',state='attached');cold.locator('[data-dialog-close]').click();cold.select_option('#campaign-select','nav-demo');cold.wait_for_function('document.querySelector("#view-title h1").textContent.includes("Planet")')
        def hold(route):
            if 'planet_id=nav-demo-planet-ash' in route.request.url:held.append((route,route.fetch()))
            else:route.continue_()
        cold.route('**/detail?*',hold);cold.select_option('#map-level','system');cold.wait_for_function('document.querySelector("#view-title h1").textContent.includes("System")');cold.select_option('#system-body-select','nav-demo-planet-ash');cold.locator('#system-orbit').click()
        deadline=time.monotonic()+90
        while not held and time.monotonic()<deadline:cold.wait_for_timeout(100)
        assert held,'Expected the selected planet preparation request';cold.wait_for_timeout(150);assert cold.locator('#map-level').input_value()=='system','Loading must retain source chart and heading'
        cold.select_option('#campaign-select','legacy-demo');cold.wait_for_timeout(300)
        for route,response in held:
            try:route.fulfill(response=response)
            except Exception:pass  # An aborted request has already been safely cancelled.
        cold.wait_for_timeout(600);assert 'Ash' not in cold.locator('#view-title h1').inner_text();cold.close()
        assert canvas.evaluate('n=>n===document.querySelector("#planet-map")');assert before==page.request.get(base+'/api/player/campaigns/nav-demo').json();assert not errors and initial==hashes(),errors
        context.tracing.stop(path=str(out/'workflow-trace.zip'));report={'browser':browser.version,'warm_entry_seconds':arrival,'warm_detail_requests':len(requests),'direct_entry_zoom_enabled':True,'exact_system_camera_return':True,'loading_source_retained':True,'late_campaign_completion_rejected':True,'same_canvas':True,'records_unchanged':True,'page_errors':errors,'source_hashes':hashes(),'limits':'One fictional fixture, software Chromium. Stills do not establish smoothness; full motion capture and frame timing assessed separately.'};(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));browser.close()

if __name__=='__main__':main()
