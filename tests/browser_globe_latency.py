"""Trusted input and Chromium presentation trace; timing is not hardware FPS."""
import hashlib,json,sys,time,os
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from playwright.sync_api import sync_playwright

def main():
    OUT=Path(os.environ.get('WOLD_GLOBE_TRACE_OUT','data/deep-critique/motion-correction'));OUT.mkdir(parents=True,exist_ok=True)
    FILES=['public/app.js','public/planet-orbit.js','public/desktop-shell.css']
    def hashes(): return {f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in FILES}
    HOOK=r'''(()=>{
     const d=window.__motionDiag={active:false,events:[],renders:[],rafs:[],longtasks:[],loafs:[],sequence:0};
     for(const type of ['pointerdown','pointermove','pointerup','pointercancel','lostpointercapture'])document.addEventListener(type,e=>{
      if(!d.active)return;const record={type,now:performance.now(),stamp:e.timeStamp,trusted:e.isTrusted,id:e.pointerId,buttons:e.buttons,x:e.clientX,y:e.clientY,sequence:++d.sequence};d.events.push(record);queueMicrotask(()=>record.afterHandlers=performance.now());
     },true);
     try{new PerformanceObserver(list=>{if(d.active)for(const e of list.getEntries())d.longtasks.push({start:e.startTime,duration:e.duration,name:e.name});}).observe({type:'longtask',buffered:true});}catch{}
     try{new PerformanceObserver(list=>{if(d.active)for(const e of list.getEntries())d.loafs.push(e.toJSON());}).observe({type:'long-animation-frame',buffered:true});}catch{}
     const install=setInterval(()=>{if(!window.HWPlanetOrbit)return;clearInterval(install);const create=HWPlanetOrbit.create;HWPlanetOrbit.create=function(...args){const r=create(...args);if(!r)return r;window.__orbitEngine=r;const render=r.render;r.render=function(...a){const record={start:performance.now(),sequence:d.sequence,scale:a[7]??1,view:{...a[4]},before:[r.canvas.width,r.canvas.height]};const result=render.apply(this,a);record.end=performance.now();record.after=[r.canvas.width,r.canvas.height];record.result=result;if(d.active)d.renders.push(record);window.__orbitAudit={result,view:a[4]};return result;};return r;};},5);
     function tick(t){if(d.active)d.rafs.push({timestamp:t,now:performance.now(),sequence:d.sequence});requestAnimationFrame(tick);}requestAnimationFrame(tick);
    })();'''

    initial=hashes();errors=[]
    with sync_playwright() as p:
     b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
     c=b.new_context(viewport={'width':1440,'height':1000},reduced_motion='no-preference');page=c.new_page();page.add_init_script(HOOK);page.on('pageerror',lambda e:errors.append(str(e)))
     page.goto('http://127.0.0.1:4213');page.wait_for_selector('#campaign-select option[value="nav-demo"]',state='attached');page.locator('[data-dialog-close]').click();page.select_option('#campaign-select','nav-demo');page.wait_for_function('window.__orbitAudit?.result',timeout=90000);page.wait_for_timeout(1000)
     cdp=c.new_cdp_session(page);cdp.send('Tracing.start',{'categories':'devtools.timeline,blink.user_timing,cc,viz,input,latencyInfo,benchmark','transferMode':'ReturnAsStream'})
     page.evaluate('__motionDiag.active=true;__motionDiag.start=performance.now()')
     began=time.monotonic();rpc=[]
     def act(name,fn):
      t=time.monotonic();fn();rpc.append({'name':name,'start_seconds':t-began,'duration_seconds':time.monotonic()-t})
     act('hover',lambda:page.mouse.move(650,540));act('down',lambda:page.mouse.down())
     for i in range(1,21):act(f'move-{i}',lambda i=i:page.mouse.move(650+165*i/20,540+40*i/20))
     act('up',lambda:page.mouse.up());act('wait-900ms',lambda:page.wait_for_timeout(900))
     drag_elapsed=time.monotonic()-began
     page.evaluate('__motionDiag.dragEnd=performance.now()');page.select_option('#map-level','system');page.wait_for_function('document.querySelector("#view-title h1").textContent.includes("System")');page.wait_for_function('HWSystemPreviewService.stateFor("nav-demo-planet-reach")==="ready"&&HWSystemPreviewService.stateFor("nav-demo-planet-ash")==="ready"',timeout=90000);page.wait_for_timeout(700);page.select_option('#system-body-select','nav-demo-planet-reach');page.wait_for_timeout(200)
     page.evaluate('__motionDiag.entryStart=performance.now()');entry_start=time.monotonic();page.locator('#system-orbit').click();page.wait_for_function('document.querySelector("#map-level").value==="planet"&&document.querySelector("#orbit-toggle").textContent==="Surface"&&!document.querySelector("#zoom-in").disabled',timeout=90000);entry_elapsed=time.monotonic()-entry_start;page.evaluate('__motionDiag.entryControlsReady=performance.now()');page.wait_for_timeout(800)
     d=page.evaluate('''()=>{__motionDiag.active=false;__motionDiag.end=performance.now();return __motionDiag}''');d['rpc']=rpc;d['drag_elapsed_seconds']=drag_elapsed;d['entry_elapsed_seconds']=entry_elapsed;d['elapsed_seconds']=time.monotonic()-began;d['source_hashes']=initial;d['source_unchanged']=hashes()==initial;d['page_errors']=errors
     (OUT/'report.json').write_text(json.dumps(d,indent=2))
     completed=[];cdp.on('Tracing.tracingComplete',lambda params:completed.append(params));cdp.send('Tracing.end')
     deadline=time.monotonic()+30
     while not completed and time.monotonic()<deadline:page.wait_for_timeout(50)
     handle=completed[0]['stream'];chunks=[]
     while True:
      chunk=cdp.send('IO.read',{'handle':handle});chunks.append(chunk['data'])
      if chunk.get('eof'):break
     cdp.send('IO.close',{'handle':handle});(OUT/'chromium-trace.json').write_text(''.join(chunks))
     assert d['source_unchanged'] and not errors,errors
     (OUT/'report.json').write_text(json.dumps(d,indent=2))
     print(json.dumps({'elapsed_seconds':d['elapsed_seconds'],'source_unchanged':d['source_unchanged'],'events':len(d['events']),'renders':len(d['renders']),'longtasks':len(d['longtasks']),'loafs':len(d['loafs']),'rpc':rpc,'errors':errors},indent=2))
     # Capture only after timing/trace completion; capture work cannot train or
     # contaminate the measured moving/entry samples.
     page.screenshot(path=str(OUT/'native-arrival.png'))
     b.close()

if __name__=="__main__": main()
