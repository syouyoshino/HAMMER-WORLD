"""Actual GPU emission, night readability and recorded infrastructure isolation."""
import hashlib,json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
from tests.browser_planet_orbit import HOOK

LIGHT_HOOK='''(()=>{const timer=setInterval(()=>{const r=window.__orbitEngine;if(!r||r.__nightWrapped)return;clearInterval(timer);r.__nightWrapped=true;const draw=r.render;r.render=function(source,revision,w,h,view,rect,star,scale){window.__nightSource=source;window.__nightRevision=revision;window.__nightFrames||=[];__nightFrames.push({view:{...view},star:star?[...star]:null});return draw.apply(this,arguments);};},5)})()'''
TIMING_HOOK='''(()=>{const timer=setInterval(()=>{const a=window.HWFacilityLights;if(!a)return;clearInterval(timer);const paint=a.paint;window.__lightPaintMs=[];a.paint=function(){const start=performance.now();try{return paint.apply(this,arguments);}finally{__lightPaintMs.push(performance.now()-start);}};},5)})()'''


def main():
    out=Path(os.environ.get('WOLD_NIGHT_OUT','data/night-infrastructure/candidate'));out.mkdir(parents=True,exist_ok=True)
    files=['public/app.js','public/map-renderer.js','public/planet-orbit.js','public/facility-lights.js','public/index.html'];hashes=lambda:{f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in files};initial=hashes();errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage']);context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce');context.tracing.start(screenshots=True,snapshots=True);page=context.new_page()
        for h in [HOOK,LIGHT_HOOK,TIMING_HOOK]:page.add_init_script(h)
        page.on('pageerror',lambda e:errors.append(str(e)));base='http://127.0.0.1:4213';page.goto(base);page.wait_for_selector('#campaign-select option[value="nav-demo"]',state='attached');page.locator('[data-dialog-close]').click()
        before=page.request.get(base+'/api/player/campaigns/nav-demo').json();page.select_option('#campaign-select','nav-demo');page.wait_for_function('window.__orbitAudit?.result',timeout=90000);canvas=page.locator('#planet-map').element_handle();page.evaluate("HWTheme.set('dark')");page.wait_for_timeout(100)
        page.locator('#map-recenter').click();page.wait_for_function('window.__nightSource?.hwOrbitEmission');page.wait_for_timeout(300)
        mask=page.evaluate('''()=>{const c=__nightSource.hwOrbitEmission,d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;return {width:c.width,height:c.height,facilities:__nightSource.hwOrbitFacilityCount,litPixels:Array.from(d).filter((v,i)=>i%4<3&&v>20).length}}''')
        pid=next(n['id'] for n in before['state']['nodes'] if n['kind']=='planet' and n['knowledge']=='surveyed')
        owned={s['id'] for s in before['state']['settlements'] if s.get('owned') and s.get('planet_id')==pid}
        eligible=[f for f in before['state']['facilities'] if f['settlement_id'] in owned and f.get('completed') is True and isinstance(f.get('active_turn'),int) and f['active_turn']<=before['turn']]
        assert mask['facilities']==len(eligible) and mask['litPixels']>0,mask
        assert 'schematic' in page.locator('.map-footer').inner_text().lower()
        page.screenshot(path=str(out/'01-night-infrastructure.png'));far=page.evaluate('__orbitAudit.view');sun=page.evaluate('__orbitAudit.starDirection')
        for _ in range(5):
            if page.evaluate('__orbitAudit.view.nightReadability')>.65:break
            page.locator('#zoom-in').click();page.wait_for_timeout(120)
            assert page.locator('#orbit-toggle').inner_text()=='Surface','Readability must improve before descent'
        near=page.evaluate('__orbitAudit.view');assert near['nightReadability']>far['nightReadability']+.5,(far,near)
        assert page.evaluate('__orbitAudit.starDirection')==sun,'Zoom cannot move the saved sun'
        page.screenshot(path=str(out/'02-close-readable.png'));page.locator('#orbit-toggle').click();page.wait_for_function('document.querySelector("#orbit-toggle").textContent==="Orbit"');page.screenshot(path=str(out/'03-surface.png'))
        # Direct GPU fixtures isolate light masking from synthetic terrain/albedo.
        gpu=page.evaluate('''()=>{const r=__orbitEngine,g=r.gl,s=document.createElement('canvas');s.width=128;s.height=64;const c=s.getContext('2d');c.fillStyle='#808080';c.fillRect(0,0,128,64);const e=document.createElement('canvas');e.width=128;e.height=64;e.getContext('2d').fillStyle='rgb(255,150,70)';e.getContext('2d').fillRect(0,0,128,64);let n=0;
          function sample(mask,sun,read=0,longitude=0){s.hwOrbitEmission=mask;const size=192;r.render(s,'night-gpu-'+n++,size,size,{latitude:0,longitude,distance:2.45,nightReadability:read},{left:0,top:0,width:size,height:size},sun);g.finish();const p=new Uint8Array(4),all=new Uint8Array(size*size*4);g.readPixels(size/2,size/2,1,1,g.RGBA,g.UNSIGNED_BYTE,p);g.readPixels(0,0,size,size,g.RGBA,g.UNSIGNED_BYTE,all);return{center:Array.from(p),alpha:Array.from(all.filter((v,i)=>i%4===3))};}
          const day=sample(e,[0,0,1]),night=sample(e,[0,0,-1]),noMask=sample(null,[0,0,-1]),closeNight=sample(null,[0,0,-1],1),closeDay=sample(null,[0,0,1],1);
          const faint=document.createElement('canvas');faint.width=128;faint.height=64;faint.getContext('2d').fillStyle='rgba(255,150,70,.1)';faint.getContext('2d').fillRect(0,0,128,64);const faintNight=sample(faint,[0,0,-1]);
          const patch=document.createElement('canvas');patch.width=128;patch.height=64;patch.getContext('2d').fillStyle='#ff9646';patch.getContext('2d').fillRect(56,24,16,16);const front=sample(patch,[0,0,-1]),back=sample(patch,[0,0,-1],0,Math.PI),backClear=sample(null,[0,0,-1],0,Math.PI);
          return {day:day.center,night:night.center,faintNight:faintNight.center,noMask:noMask.center,closeNight:closeNight.center,closeDay:closeDay.center,patchFront:front.center,patchBack:back.center,patchBackClear:backClear.center,sameCoverage:day.alpha.every((v,i)=>v===night.alpha[i]&&v===noMask.alpha[i]&&v===closeNight.alpha[i]),outsideClear:day.alpha[0]===0,glError:g.getError()};}''')
        assert gpu['night'][0]>gpu['day'][0]+80,gpu
        assert gpu['noMask'][0]<15 and gpu['closeNight'][0]>100,gpu
        assert gpu['noMask'][0]<gpu['faintNight'][0]<gpu['night'][0]*.3,gpu
        assert gpu['closeDay'][0]>=gpu['day'][0]-1,gpu
        assert gpu['sameCoverage'] and gpu['outsideClear'] and gpu['glError']==0,gpu
        assert gpu['patchFront'][0]>240 and gpu['patchBack']==gpu['patchBackClear'],gpu
        # A different surveyed world owns no facilities: emission must clear.
        page.select_option('#map-level','system');page.wait_for_function('document.querySelector("#view-title h1").textContent.includes("System")');other=next(n for n in before['state']['nodes'] if n['kind']=='planet' and n['knowledge']=='surveyed' and n['id']!=pid)
        page.select_option('#system-body-select',other['id']);page.locator('#system-orbit').click();page.wait_for_function('id=>window.__nightRevision?.includes(id)&&document.querySelector("#orbit-toggle").textContent==="Surface"',arg=other['id'],timeout=90000)
        assert page.evaluate('__nightSource.hwOrbitFacilityCount')==0
        # Historical facility eligibility comes from that selected snapshot's state.
        page.locator('#hw-command').click();page.locator('#command-menu [data-open="history"]').click();page.get_by_role('button',name='Inspect turn 0',exact=True).click();page.wait_for_function('!document.querySelector("#historical-badge").hidden');page.wait_for_function('window.__orbitAudit?.revision.includes("nav-demo:")&&document.querySelector("#orbit-toggle").textContent==="Surface"',timeout=90000)
        page.locator('#map-recenter').click();page.wait_for_timeout(200);historical=page.request.get(base+'/api/player/campaigns/nav-demo/history?limit=50').json()['items'][0]
        snapshot=page.request.get(base+'/api/player/snapshots/'+historical['id']).json();state=snapshot['state'];owned0={s['id'] for s in state['settlements'] if s.get('owned') and s.get('planet_id')==pid};expected0=sum(f['settlement_id'] in owned0 and f.get('completed') is True and isinstance(f.get('active_turn'),int) and f['active_turn']<=state['turn'] for f in state['facilities'])
        assert historical['id'] in page.evaluate('__nightRevision');assert page.evaluate('__nightSource.hwOrbitFacilityCount')==expected0
        page.screenshot(path=str(out/'04-historical-lights.png'))
        assert canvas.evaluate('n=>n===document.querySelector("#planet-map")');assert before==page.request.get(base+'/api/player/campaigns/nav-demo').json();assert not errors and initial==hashes(),errors
        context.tracing.stop(path=str(out/'workflow-trace.zip'));report={'browser':browser.version,'emission':mask,'far_view':far,'near_view':near,'recorded_sun_unchanged':True,'gpu':gpu,'other_world_emission_cleared':True,'historical_eligible_count':expected0,'same_canvas':True,'paint_ms':page.evaluate('__lightPaintMs'),'renderer':page.evaluate('navigator.userAgent'),'records_unchanged':True,'page_errors':errors,'source_hashes':hashes(),'limits':'Schematic facility patterns at saved province anchors; synthetic GPU fixtures isolate shader behavior. Software Chromium, no hardware/Safari or exact building-footprint claim.'};(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));browser.close()


if __name__=='__main__':main()
