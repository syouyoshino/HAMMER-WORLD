"""Actual WebGL relief, immutable-record, cache and geometric-lighting checks.

Uses the same isolated surveyed static-v1 demo as browser_body_focus.py. Manual
render comparisons test the shader on its recorded texture, not simulated events.
"""
import hashlib,json,os,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tests.browser_planet_orbit import HOOK
AUDIT='''(()=>{const timer=setInterval(()=>{const m=window.HWMapRenderer,o=window.HWPlanetOrbit;if(!m||!o)return;clearInterval(timer);
 const build=m.buildOrbitTexture;m.buildOrbitTexture=function(...args){const source=build(...args);window.__reliefSource=source;window.__reliefBuildMeta={overlay:args[0].overlay,style:args[0].style};return source;};
 const create=o.create;o.create=function(...args){const r=create(...args);if(!r)return r;const gl=r.gl,a=window.__reliefGpu={uploads:0,extraTextures:0};
 const upload=gl.texImage2D;gl.texImage2D=function(...v){a.uploads++;return upload.apply(this,v);};
 const alloc=gl.createTexture;gl.createTexture=function(...v){a.extraTextures++;return alloc.apply(this,v);};return r;};},5)})()'''


def main():
    base=os.environ.get('WOLD_BODY_FOCUS_BASE','http://127.0.0.1:4213');campaign=os.environ.get('WOLD_BODY_FOCUS_CAMPAIGN','nav-demo')
    out=Path(os.environ.get('WOLD_RELIEF_OUT',ROOT/'data/terrain-finish/orbit-relief'));out.mkdir(parents=True,exist_ok=True)
    files=['public/map-renderer.js','public/planet-orbit.js','public/app.js','public/desktop-shell.js','public/desktop-shell.css']
    hashes=lambda:{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files};initial=hashes();errors=[]
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage']);page=b.new_page(viewport={'width':1440,'height':1024})
        if os.environ.get('WOLD_RELIEF_NO_GRADIENT')=='1':
            page.add_init_script('''(()=>{const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(type,...args){const gl=original.call(this,type,...args);if(type==='webgl'&&gl&&!gl.__qaNoGradient){const extension=gl.getExtension;gl.getExtension=function(name){return ['OES_standard_derivatives','EXT_shader_texture_lod'].includes(name)?null:extension.call(this,name);};gl.__qaNoGradient=true;}return gl;};})()''')
        page.add_init_script(HOOK);page.add_init_script(AUDIT);page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(base);page.wait_for_selector(f'#campaign-select option[value="{campaign}"]',state='attached')
        if page.locator('[data-dialog-close]').is_visible():page.locator('[data-dialog-close]').click()
        before=page.request.get(f'{base}/api/player/campaigns/{campaign}').json();page.select_option('#campaign-select',campaign);page.wait_for_function('window.__orbitAudit?.result',timeout=90000);page.wait_for_timeout(600)
        assert page.evaluate('!!__reliefSource.hwOrbitRelief'),'Recorded terrain did not supply relief'
        page.evaluate('window.__firstRelief=__reliefSource.hwOrbitRelief')
        page.screenshot(path=str(out/'recorded-relief.png'))
        result=page.evaluate('''()=>{
          const r=__orbitEngine,s=__reliefSource,original=__orbitAudit,normal=s.hwOrbitRelief,gl=r.gl,api=HWPlanetOrbit;
          const width=512,height=384,rect={left:0,top:0,width,height},view={...original.view},light=original.starDirection;
          if(!light)throw Error('Use a saved-astronomy fixture for directional lighting');
          const sourcePixels=s.getContext('2d').getImageData(0,0,s.width,s.height).data,ceiling=[0,0,0];for(let i=0;i<sourcePixels.length;i+=4)for(let k=0;k<3;k++)ceiling[k]=Math.max(ceiling[k],sourcePixels[i+k]);
          const pixels=()=>{gl.finish();const data=new Uint8Array(width*height*4);gl.readPixels(0,0,width,height,gl.RGBA,gl.UNSIGNED_BYTE,data);return data;};
          if(!r.render(s,'qa-relief',width,height,view,rect,light))throw Error('Relief render failed');const lit=pixels();
          delete s.hwOrbitRelief;if(!r.render(s,'qa-neutral',width,height,view,rect,light))throw Error('Neutral fallback render failed');const flat=pixels(),neutralTimes=[];for(let i=0;i<12;i++){const t=performance.now();if(!r.render(s,'qa-neutral',width,height,{...view,longitude:view.longitude+i*.025},rect,light))throw Error('Neutral repeated render failed');gl.readPixels(0,0,1,1,gl.RGBA,gl.UNSIGNED_BYTE,new Uint8Array(4));neutralTimes.push(performance.now()-t);}s.hwOrbitRelief=normal;
          let changed=0,alphaChanged=0,nightChecked=0,nightChanged=0,overAlbedoCeilingPixels=0;
          for(let i=0;i<lit.length;i+=4){if(lit[i+3]>127&&[0,1,2].some(k=>lit[i+k]>ceiling[k]+2))overAlbedoCeilingPixels++;if(lit[i+3]!==flat[i+3])alphaChanged++;if(lit[i+3]&&Math.max(...[0,1,2].map(k=>Math.abs(lit[i+k]-flat[i+k])))>1)changed++;}
          const length=Math.hypot(...light),unitLight=light.map(x=>x/length);
          for(let y=5;y<height;y+=8)for(let x=5;x<width;x+=8){const hit=api.inversePoint(x+.5,y+.5,view,rect);if(!hit)continue;const n=api.unit(hit.latitude,hit.longitude);if(n.reduce((a,v,i)=>a+v*unitLight[i],0)>-.12)continue;
            const i=((height-1-y)*width+x)*4;if(!lit[i+3])continue;nightChecked++;if([0,1,2].some(k=>Math.abs(lit[i+k]-flat[i+k])>1))nightChanged++;}
          const times=[];if(!r.render(s,'qa-relief-warm',width,height,view,rect,light))throw Error('Warm render failed');gl.finish();const uploads=__reliefGpu.uploads,textures=__reliefGpu.extraTextures;
          for(let i=0;i<12;i++){const t=performance.now();if(!r.render(s,'qa-relief-warm',width,height,{...view,longitude:view.longitude+i*.025},rect,light))throw Error('Repeated render failed');gl.finish();gl.readPixels(0,0,1,1,gl.RGBA,gl.UNSIGNED_BYTE,new Uint8Array(4));times.push(performance.now()-t);}
          const stableUploads=__reliefGpu.uploads===uploads,stableTextures=__reliefGpu.extraTextures===textures;
          r.render(s,original.revision,original.w,original.h,original.view,original.rect,light);gl.finish();
          return {overAlbedoCeilingPixels,sourceChannelCeiling:ceiling,changedPixels:changed,alphaChanged,nightChecked,nightChanged,stableUploads,stableTextures,warmFrameReadbackMs:times,neutralFrameReadbackMs:neutralTimes,normalSize:[normal.width,normal.height],testFramebuffer:[width,height],glError:gl.getError(),contextLost:gl.isContextLost()};
        }''')
        assert result['changedPixels']>50 and result['overAlbedoCeilingPixels']==0,result
        assert result['alphaChanged']==0 and result['nightChecked']>10 and result['nightChanged']==0,result
        assert result['stableUploads'] and result['stableTextures'] and result['glError']==0,result
        page.select_option('#map-style','survey');page.wait_for_function('window.__reliefBuildMeta?.style==="survey"',timeout=90000)
        assert page.evaluate('__firstRelief===__reliefSource.hwOrbitRelief'),'Palette switch rebuilt relief field'
        page.select_option('#overlay-select','population');page.wait_for_function('window.__reliefBuildMeta?.overlay==="population"',timeout=90000);assert page.evaluate('!__reliefSource.hwOrbitRelief'),'Relief changed a statistical overlay'
        page.select_option('#overlay-select','terrain');page.wait_for_function('window.__reliefBuildMeta?.overlay==="terrain"',timeout=90000);assert page.evaluate('__firstRelief===__reliefSource.hwOrbitRelief')
        after=page.request.get(f'{base}/api/player/campaigns/{campaign}').json();assert before==after;assert not errors;assert hashes()==initial
        result.update(gradient_probe_disabled=os.environ.get('WOLD_RELIEF_NO_GRADIENT')=='1',browser=b.version,records_unchanged=True,palette_cache=True,statistical_overlay_unchanged=True,page_errors=errors,source_hashes=hashes(),limits='SwiftShader/shared Linux. One-pixel synchronous readback timings at512x384 include rendering/driver/readback on a shared software renderer; not production FPS.')
        (out/'report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));b.close()

if __name__=='__main__':main()
