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
const record=ids=>({parent:{id:'sys'},bodies:[{id:'s',kind:'star',knowledge:'surveyed'}],nodes:[...ids.map(id=>({id,parent_id:'sys',kind:'planet',knowledge:'surveyed'})),{id:'unknown',parent_id:'sys',kind:'planet',knowledge:'detected'}],
 astronomy:{version:'static-v1',motion:'frozen',frame:'system-xyz-v1',position_unit:'micro-AU',systems:{sys:{bodies:Object.fromEntries([['s',{position:[0,0,0]}],...ids.map((id,i)=>[id,{position:[1000+i,0,500]}])])}}}});
let refBytes=123,fault=null;
const calls=[],ref=id=>({version:'planet-detail-v2',sha256:crypto.createHash('sha256').update(id).digest('hex'),width:1024,height:640,byte_length:refBytes});
let blocked=null,release=null,wrong=false;
async function api(path){
 calls.push(path);const url=new URL(path,'http://fixture'),cid=decodeURIComponent(path.split('/')[4]),snapshot=url.searchParams.get('snapshot_id'),id=url.searchParams.get('node_id')||url.searchParams.get('planet_id');
 let result=url.pathname.endsWith('/map')?{campaign_id:wrong?'wrong':cid,snapshot_id:snapshot,level:'planet',parent:{id,parent_id:'sys',kind:'planet'},selected_planet:{id,parent_id:'sys',knowledge:'surveyed'},geometry:{planet:{id:'geography-'+id},detail_ref:ref(id)}}:
  {planet_id:id,snapshot_id:snapshot,detail_ref:ref(id),detail:{version:'planet-detail-v2',width:1024,height:640}};
 if(fault==='detail-sha'&&url.pathname.endsWith('/detail'))result.detail_ref={...result.detail_ref,sha256:'0'.repeat(64)};
 if(fault==='detail-snapshot'&&url.pathname.endsWith('/detail'))result.snapshot_id='other-snapshot';
 if(fault==='map-parent'&&url.pathname.endsWith('/map'))result.selected_planet.parent_id='wrong-system';
 if(fault==='map-ref'&&url.pathname.endsWith('/map'))result.geometry.detail_ref={...result.geometry.detail_ref,byte_length:17*1024*1024};
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
 const retained=ids.map(id=>service.getPlanet(id)).filter(Boolean);
 assert.equal(retained.length,2,'Only two full geometry/detail assets may remain retained');
 for(const id of ids){const item=service.get(id);if(item){assert(!('geometry' in item));assert(!('detail' in item));assert(!('ref' in item));}}
 const saved=retained[0],callsBefore=calls.length,buildsBefore=builds;
 assert.strictEqual(await service.ensurePlanet(saved.id),saved,'Native handoff must reuse the exact retained asset object');
 assert.strictEqual(service.getPlanet(saved.id,'orbital',saved.sourceSha),saved);
 assert.equal(service.getPlanet(saved.id,'orbital','f'.repeat(64)),null);
 assert.equal(calls.length,callsBefore);assert.equal(builds,buildsBefore);
 service.suspend();assert.strictEqual(service.getPlanet(saved.id),saved,'Suspension preserves authorized native handoff assets');
 service.clear();assert.equal(service.thumbnails(record(ids)).size,0);
 // Automatic queued and in-flight work must be the same promise as explicit preparation.
 blocked='coalesce';release=null;service.setContext(context(6,'coalesce','s6'),record(['first','queued']));
 await until(()=>release);
 const inflight=service.ensurePlanet('first'),same=service.ensurePlanet('first');assert.strictEqual(inflight,same);
 const queued=service.ensurePlanet('queued');assert.strictEqual(queued,service.ensurePlanet('queued'));
 const coalesceStart=calls.length;release();const [firstAsset,queuedAsset]=await Promise.all([inflight,queued]);
 assert.strictEqual(service.getPlanet('first'),firstAsset);assert.strictEqual(service.getPlanet('queued'),queuedAsset);
 assert.equal(calls.filter(path=>path.includes('node_id=first')).length,1,'Automatic in-flight map fetch must not duplicate');
 assert.equal(calls.slice(coalesceStart).filter(path=>path.includes('node_id=queued')).length,1,'Automatic queued fetch must not duplicate');
 // Explicit preparation rejects unknown and mismatched-parent contacts without a request.
 const badRecord=record(['good']);badRecord.nodes.push({id:'wrong-parent',parent_id:'other',kind:'planet',knowledge:'surveyed'});
 service.setContext(context(7,'members','s7'),badRecord);const membershipCalls=calls.length;
 await assert.rejects(service.ensurePlanet('unknown'));await assert.rejects(service.ensurePlanet('wrong-parent'));await assert.rejects(service.ensurePlanet('absent'));
 assert(!calls.slice(membershipCalls).some(path=>/unknown|wrong-parent|absent/.test(path)));
 await service.ensurePlanet('good');
 // A held promise settles on an authorization change, even if the old transport ignores abort.
 blocked='held';release=null;service.setContext(context(8,'held','s8'),record(['same']));await until(()=>release);
 const held=service.ensurePlanet('same'),heldOutcome=held.then(()=>false,()=>true),oldRelease=release;
 service.setContext(context(9,'fresh','s9'),record(['same']));assert(await heldOutcome);
 const fresh=await service.ensurePlanet('same');oldRelease();await new Promise(resolve=>setTimeout(resolve,0));
 assert.strictEqual(service.getPlanet('same'),fresh);assert.equal(service.getPlanet('first'),null);
 // Invalid saved references and snapshot responses settle all coalesced waiters.
 for(const [index,mode] of ['detail-sha','detail-snapshot','map-ref','map-parent'].entries()){
  fault=mode;service.setContext(context(10+index,'failure-'+index,'failure-snap'),record(['bad']));
  const one=service.ensurePlanet('bad'),two=service.ensurePlanet('bad');assert.strictEqual(one,two);
  const settled=await Promise.allSettled([one,two]);assert(settled.every(item=>item.status==='rejected'));
  assert.equal(service.getPlanet('bad'),null);assert.equal(service.get('bad'),null);
 }
 fault=null;refBytes=8*1024*1024;service.setContext(context(14,'bytes','byte-snap'),record(['byte-a','byte-b','byte-c']));
 await service.ensurePlanet('byte-c');await until(()=>['byte-a','byte-b','byte-c'].every(id=>service.stateFor(id)!=='loading'));
 const assets=['byte-a','byte-b','byte-c'].map(id=>service.getPlanet(id)).filter(Boolean);
 assert(assets.length<=2);assert(assets.reduce((sum,item)=>sum+item.ref.byte_length,0)<=16*1024*1024);
 // Suspending an active request rejects its public promise and cannot republish late.
 blocked='suspended';release=null;service.setContext(context(15,'suspended','s15'),record(['stop']));await until(()=>release);
 const stopped=service.ensurePlanet('stop'),stopOutcome=stopped.then(()=>false,()=>true),stopRelease=release;
 service.suspend();assert(await stopOutcome);stopRelease();await new Promise(resolve=>setTimeout(resolve,0));assert.equal(service.getPlanet('stop'),null);
 service.clear();
 console.log('Preview membership, coalescing, retained identity, asset/byte bounds, cancellation, snapshot validation and sprite isolation passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
