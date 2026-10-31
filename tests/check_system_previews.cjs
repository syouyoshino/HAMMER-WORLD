// Recorded previews must remain bounded, surveyed-only and context isolated.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),crypto=require('node:crypto');
let builds=0,updates=0;
class Canvas{
 constructor(){this.width=1;this.height=1;}
 getContext(kind){assert.equal(kind,'2d','Previews must not allocate WebGL contexts');const canvas=this;return{
  drawImage(){},getImageData(x,y,w,h){return{data:new Uint8ClampedArray(w*h*4).fill(255)};},
  createImageData(w,h){return{data:new Uint8ClampedArray(w*h*4)};},putImageData(image){canvas.pixels=image.data;}
 };}
}
const sandbox={window:{},document:{createElement(kind){assert.equal(kind,'canvas');return new Canvas();}},AbortController,console};
sandbox.window.HWMapRenderer={buildOrbitTexture(){builds++;const c=new Canvas();c.width=1024;c.height=640;return c;}};
vm.createContext(sandbox);
for(const file of ['public/system-view.js','public/system-previews.js'])vm.runInContext(fs.readFileSync(file,'utf8'),sandbox,{filename:file});
const record=ids=>({parent:{id:'sys'},bodies:[{id:'s',kind:'star',knowledge:'surveyed'}],nodes:[...ids.map(id=>({id,kind:'planet',knowledge:'surveyed'})),{id:'unknown',kind:'planet',knowledge:'detected'}],
 astronomy:{version:'static-v1',motion:'frozen',frame:'system-xyz-v1',position_unit:'micro-AU',systems:{sys:{bodies:Object.fromEntries([['s',{position:[0,0,0]}],...ids.map((id,i)=>[id,{position:[1000+i,0,500]}])])}}}});
const calls=[],ref=id=>({version:'planet-detail-v2',sha256:crypto.createHash('sha256').update(id).digest('hex'),width:1024,height:640,byte_length:123});
let blocked=null,release=null,wrong=false;
async function api(path){
 calls.push(path);const url=new URL(path,'http://fixture'),cid=decodeURIComponent(path.split('/')[4]),snapshot=url.searchParams.get('snapshot_id'),id=url.searchParams.get('node_id')||url.searchParams.get('planet_id');
 let result=url.pathname.endsWith('/map')?{campaign_id:wrong?'wrong':cid,snapshot_id:snapshot,level:'planet',selected_planet:{id,knowledge:'surveyed'},geometry:{planet:{id},detail_ref:ref(id)}}:
  {planet_id:id,snapshot_id:snapshot,detail_ref:ref(id),detail:{version:'planet-detail-v2',width:1024,height:640}};
 if(blocked===cid){blocked=null;return new Promise(resolve=>release=()=>resolve(result));}return result;
}
const service=sandbox.window.HWSystemPreviews.create(api,()=>updates++);
const context=(epoch,campaignId,snapshotId)=>({epoch,campaignId,snapshotId});
async function until(predicate){for(let i=0;i<1000;i++){if(predicate())return;await new Promise(resolve=>setTimeout(resolve,1));}throw Error('Preview work did not settle');}
(async()=>{
 service.setContext(context(1,'a','snap-a'),record(['p']));await until(()=>service.stateFor('p')==='ready');
 const p=service.get('p');assert.equal(p.sourceSha,ref('p').sha256);assert.equal(p.sprite.width,128);assert.equal(p.sprite.height,128);
 assert(p.sprite.pixels.some((v,i)=>i%4===3&&v===0));assert(p.sprite.pixels.some((v,i)=>i%4===3&&v===255));
 assert.equal(service.get('unknown'),null);assert(!calls.some(s=>s.includes('unknown')));assert.equal(builds,1);
 // A delayed old response must not publish into a new login/campaign sharing body IDs.
 service.clear();blocked='old';service.setContext(context(2,'old','snap-old'),record(['same']));await until(()=>release);
 service.setContext(context(3,'new','snap-new'),record(['same']));release();await until(()=>service.stateFor('same')==='ready');
 assert.equal(service.get('p'),null);assert.equal(builds,2);assert(service.get('same'));assert(updates>=2);
 service.clear();assert.equal(service.get('same'),null);
 wrong=true;const before=builds;service.setContext(context(4,'bad','snap-bad'),record(['bad']));await until(()=>service.stateFor('bad')==='unavailable');
 assert.equal(service.get('bad'),null);assert.equal(builds,before);wrong=false;
 service.clear();const ids=Array.from({length:26},(_,i)=>'bound-'+i);service.setContext(context(5,'bounded','snap-bounded'),record(ids));
 await until(()=>ids.every(id=>service.stateFor(id)!=='loading'));
 const count=ids.filter(id=>service.get(id)).length;assert(count<=24&&count>0,'Cache must be capped at24 sprites');
 service.clear();assert.equal(service.thumbnails(record(ids)).size,0);
 console.log('Survey isolation, stale response rejection, bad-context refusal, sprite pixels and cache bounds passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
