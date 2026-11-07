"""Read-only fixed-buffer GPU comparison against the committed eight-tap renderer."""
import base64,hashlib,json,os,subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

HOOK=r'''(()=>{const t=setInterval(()=>{const api=window.HWPlanetOrbit;if(!api)return;clearInterval(t);const create=api.create;window.__filterCreate=create;api.create=function(...a){const r=create(...a);if(!r)return r;const render=r.render;r.render=function(...args){window.__filterInput=args;return render.apply(this,args);};return r;};},5)})()'''
BENCH=r'''({baseline,overlay})=>{
 const current=HWPlanetOrbit,seed=__filterInput;window.eval(baseline);const reference=HWPlanetOrbit;window.HWPlanetOrbit=current;
 const old=reference.create(document.createElement('canvas')),next=__filterCreate(document.createElement('canvas'));
 if(!old||!next)throw Error('Both real GPU programs must compile');
 const [source,revision]=seed,rect={left:0,top:220,right:1440,bottom:920,width:1440,height:700},sun=seed[6];
 const read=(r,pose,moving)=>{if(!r.render(source,revision,1440,1000,pose,rect,sun,.16,moving))throw Error('GPU draw failed');r.gl.finish();const p=new Uint8Array(r.canvas.width*r.canvas.height*4);r.gl.readPixels(0,0,r.canvas.width,r.canvas.height,r.gl.RGBA,r.gl.UNSIGNED_BYTE,p);if(r.gl.getError())throw Error('GL error');return p;};
 const poses=[['equator',0,-2.93,1.7,0],['coast',.35,-2.7,1.5,0],['north-pole',Math.PI/2,0,2.45,0],['south-pole',-Math.PI/2,0,2.45,0],['seam-east',0,Math.PI-.001,1.7,0],['seam-west',0,-Math.PI+.001,1.7,0],['night',.1,-1.7,1.7,0],['analytical',.1,-1.7,1.7,.7]];
 const stats=[],images=[];
 for(const [name,latitude,longitude,distance,nightReadability]of poses){
  const pose={latitude,longitude,distance,nightReadability},before=read(old,pose,false),idle=read(next,pose,false),moving=read(next,pose,true),restored=read(next,pose,false),diff=[];let idleMax=0,alphaMax=0,restoreMax=0,changed=0,opaque=0,sum=0;
  for(let i=0;i<before.length;i++){idleMax=Math.max(idleMax,Math.abs(before[i]-idle[i]));restoreMax=Math.max(restoreMax,Math.abs(before[i]-restored[i]));if(i%4===3){alphaMax=Math.max(alphaMax,Math.abs(before[i]-moving[i]));continue;}if(before[i-i%4+3]>240){const v=Math.abs(before[i]-moving[i]);diff.push(v);sum+=v;opaque++;if(v)changed++;}}
  diff.sort((a,b)=>a-b);const timings={};
  for(const mode of [false,true]){const times=[];for(let i=0;i<7;i++){const start=performance.now();read(next,pose,mode);times.push(performance.now()-start);}timings[mode?'moving_ms':'full_ms']=times.slice(2).sort((a,b)=>a-b)[2];}
  stats.push({overlay,name,idle_max_byte_error:idleMax,restored_max_byte_error:restoreMax,moving_alpha_max_error:alphaMax,moving_max_byte_error:diff.at(-1)||0,moving_p99_byte_error:diff[Math.floor(diff.length*.99)]||0,moving_mean_byte_error:sum/Math.max(1,opaque),changed_channels:changed,...timings});
  if(name==='equator'||name==='north-pole'){read(old,pose,false);images.push({name:name+'-reference',png:old.canvas.toDataURL()});read(next,pose,true);images.push({name:name+'-moving',png:next.canvas.toDataURL()});}
 }
 for(const r of [old,next])r.gl.getExtension('WEBGL_lose_context')?.loseContext();
 return{stats,images,buffer:[230,160],derivatives:Boolean(next.gl.getExtension('OES_standard_derivatives'))};
}'''

def main():
    out=Path(os.environ.get('WOLD_FILTER_QUALITY_OUT','data/motion-fix/candidate-c/filter-quality'));out.mkdir(parents=True,exist_ok=True)
    files=['public/app.js','public/planet-orbit.js'];hashes=lambda:{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in files};initial=hashes();baseline=subprocess.check_output(['git','show','f547851:public/planet-orbit.js'],text=True);errors=[];results=[]
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage']);page=b.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce');page.add_init_script(HOOK);page.on('pageerror',lambda e:errors.append(str(e)));base='http://127.0.0.1:4213';page.goto(base);page.wait_for_selector('#campaign-select option[value="nav-demo"]',state='attached');page.locator('[data-dialog-close]').click();before=page.request.get(base+'/api/player/campaigns/nav-demo').json();page.select_option('#campaign-select','nav-demo');page.wait_for_function('window.__filterInput?.[0]',timeout=90000)
        for overlay in ['terrain','provinces']:
            if overlay!='terrain':page.select_option('#overlay-select',overlay);page.wait_for_function('window.__filterInput?.[1].includes(":provinces:")',timeout=90000)
            r=page.evaluate(BENCH,{'baseline':baseline,'overlay':overlay});results.extend(r['stats'])
            for item in r['images']:(out/(overlay+'-'+item['name']+'.png')).write_bytes(base64.b64decode(item['png'].split(',',1)[1]))
        assert before==page.request.get(base+'/api/player/campaigns/nav-demo').json();assert hashes()==initial and not errors,errors
        report={'browser':b.version,'reference_commit':'f547851','source_hashes':initial,'source_unchanged':True,'records_unchanged':True,'page_errors':errors,'results':results,'limits':'Real WebGL fixed230x160 public-fixture comparison; gl.finish/readPixels timing is isolated GPU completion work, not physical display FPS. Moving quality differs only where filter gate allows; idle is tested separately.'};(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));b.close()
    assert all(r['idle_max_byte_error']==0 and r['restored_max_byte_error']==0 and r['moving_alpha_max_error']==0 for r in results),'Idle pixels and geometric coverage must match the original exactly'
    assert all(r['moving_p99_byte_error']<=4 and r['moving_mean_byte_error']<=1 for r in results),'Reject visible moving filter degradation'

if __name__=='__main__':main()
