"""Actual Orbit/Surface presentation and raster-work regression; requires4213fixture."""
import json,time,hashlib,os
from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path(os.environ.get('WOLD_FADE_MOTION_OUT','data/motion-fix/candidate-d/fade-motion'));out.mkdir(parents=True,exist_ok=True)
hook=r'''(()=>{const d=window.__fadeDiag={phase:'idle',samples:[],renders:[],clears:[],backdrops:[]};const clear=CanvasRenderingContext2D.prototype.clearRect;CanvasRenderingContext2D.prototype.clearRect=function(...a){if(d.phase!=='idle'&&this.canvas.id==='planet-map')d.clears.push({phase:d.phase,time:performance.now()});return clear.apply(this,a);};const t=setInterval(()=>{const api=window.HWPlanetOrbit;if(!api||!window.HWOrbitBackground)return;clearInterval(t);const bg=HWOrbitBackground.draw;HWOrbitBackground.draw=function(...a){if(d.phase!=='idle')d.backdrops.push({phase:d.phase,time:performance.now()});return bg.apply(this,a);};const create=api.create;api.create=function(...a){const r=create(...a);if(!r)return r;window.__orbitEngine=r;const render=r.render;r.render=function(...a){const v={phase:d.phase,start:performance.now(),view:{...a[4]},rect:{...a[5]},scale:a[7],moving:a[8]};const result=render.apply(this,a);v.end=performance.now();if(d.phase!=='idle')d.renders.push(v);return result;};return r;};},5);function frame(now){const c=window.__orbitEngine?.canvas;if(c&&d.phase!=='idle'){const group=c.closest('.planet-orbit-presentation');d.samples.push({phase:d.phase,time:performance.now(),raf:now,opacity:Number(group?.style.opacity||c.style.opacity||1),childOpacity:Number(c.style.opacity||1),visible:getComputedStyle(c).visibility,width:c.width,height:c.height,mode:document.querySelector('#orbit-toggle')?.textContent,detailHidden:document.querySelector('#detail-status')?.hidden});const opacity=d.samples.at(-1).opacity,key=d.phase+':'+opacity;if(d.lastMark!==key){performance.mark('motion-fade:'+key);d.lastMark=key;}}requestAnimationFrame(frame);}requestAnimationFrame(frame);})()'''
files=['public/app.js','public/planet-orbit.js','public/desktop-shell.css'];hashes=lambda:{f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in files};initial=hashes()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage']);page=b.new_page(viewport={'width':1440,'height':1000},reduced_motion='no-preference');page.add_init_script(hook);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));base='http://127.0.0.1:4213';page.goto(base);page.wait_for_selector('#campaign-select option[value="nav-demo"]',state='attached');page.locator('[data-dialog-close]').click();before=page.request.get(base+'/api/player/campaigns/nav-demo').json();page.select_option('#campaign-select','nav-demo');page.wait_for_function('window.__orbitEngine?.uploaded',timeout=90000);page.wait_for_timeout(1000);cdp=page.context.new_cdp_session(page);cdp.send('Tracing.start',{'categories':'devtools.timeline,blink.user_timing,cc,viz,input,latencyInfo,benchmark','transferMode':'ReturnAsStream'})
 for phase,mode in [('exit','Orbit'),('enter','Surface')]:
  page.evaluate('p=>{__fadeDiag.phase=p;__fadeDiag[p+"Click"]=performance.now();performance.mark("motion-fade:"+p+":click")}',phase);page.locator('#orbit-toggle').click();page.wait_for_function('s=>document.querySelector("#orbit-toggle").textContent===s',arg=mode);page.wait_for_timeout(1400)
 data=page.evaluate('()=>{__fadeDiag.phase="idle";return __fadeDiag}');data.update(source_hashes=initial,source_unchanged=initial==hashes(),page_errors=errors,records_unchanged=before==page.request.get(base+'/api/player/campaigns/nav-demo').json());(out/'report.json').write_text(json.dumps(data,indent=2));done=[];cdp.on('Tracing.tracingComplete',lambda r:done.append(r));cdp.send('Tracing.end');deadline=time.monotonic()+30
 while not done and time.monotonic()<deadline:page.wait_for_timeout(25)
 handle=done[0]['stream'];chunks=[]
 while True:
  r=cdp.send('IO.read',{'handle':handle});chunks.append(r['data'])
  if r.get('eof'):break
 cdp.send('IO.close',{'handle':handle});(out/'trace.json').write_text(''.join(chunks));page.screenshot(path=str(out/'settled.png'));assert data['source_unchanged'] and data['records_unchanged'] and not errors,data;print(json.dumps({p:[{'time':round(x['time']-data[p+'Click'],1),'opacity':round(x['opacity'],3),'visible':x['visible']} for x in data['samples'] if x['phase']==p][:18] for p in ['exit','enter']},indent=2));b.close()

summary=[]
for phase in ['exit','enter']:
 rows=[x for x in data['samples'] if x['phase']==phase]
 def progress(x):
  if x['visible']=='hidden':return 1.0 if phase=='exit' else 0.0
  return 1-x['opacity'] if phase=='exit' else x['opacity']
 moving=[{**x,'progress':progress(x)} for x in rows if .01<progress(x)<.99]
 assert len(moving)>=8,(phase,'Need actual intermediate poses',len(moving),rows[:15])
 gaps=[b['time']-a['time'] for a,b in zip(moving,moving[1:])]
 steps=[b['progress']-a['progress'] for a,b in zip(moving,moving[1:])]
 assert max(gaps,default=0)<=80,(phase,'Late publication stalls movement',gaps)
 assert max(steps,default=0)<=.2 and min(steps,default=0)>=-.001,(phase,steps)
 start,end=moving[0]['time'],moving[-1]['time']
 work={key:sum(x.get('phase')==phase and start<x.get('time',x.get('start',0))<end for x in data[key]) for key in ['renders','clears','backdrops']}
 assert not any(work.values()),(phase,'Raster work inside opacity ticks',work)
 assert all(x['childOpacity']==1 for x in moving),'Group owns opacity, not nested globe alpha'
 summary.append({'phase':phase,'intermediate_samples':len(moving),'max_moving_gap_ms':max(gaps,default=0),'max_progress_step':max(steps,default=0),'work_during_opacity_ticks':work})
(out/'summary.json').write_text(json.dumps({'checks':summary,'source_unchanged':data['source_unchanged'],'records_unchanged':data['records_unchanged'],'page_errors':errors,'limits':'Actual DOM/RAF and renderer-work observations; not physical-display FPS. Preparation is retained in raw trace rather than consumed as animation time.'},indent=2))
print(json.dumps(summary,indent=2))
