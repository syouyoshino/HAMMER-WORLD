const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const app=fs.readFileSync('public/app.js','utf8');
assert(!app.includes('(now-start-55)/420'),'Bridge clock must start after its zero-progress frame is presented');
assert.match(app,/Math\.max\(0,Math\.min\(1,\(now-start\)\/420\)\)/,'Bridge progress must begin at zero without an arrival delay heuristic');
const system=require('../public/system-view.js');
const sandbox={window:{}};vm.createContext(sandbox);vm.runInContext(fs.readFileSync('public/planet-orbit.js','utf8'),sandbox);const orbit=sandbox.window.HWPlanetOrbit;
for(const rect of [{left:0,top:212,width:1440,height:640},{left:70,top:100,width:540,height:800}]){
 for(const distance of [1.1,2.45,4.2]){
  const circle=system.orbitCircle(rect,distance),angle=Math.acos(1/distance)-1e-7;
  const tangent=orbit.screenPoint(0,angle,{latitude:0,longitude:0,distance},rect);
  assert(Math.abs(tangent.x-circle.x-circle.radius)<1e-6,'Bridge radius must agree with the native perspective tangent');
  const from={x:177,y:438,radius:24};
  assert.deepEqual(system.bridgeCircle(from,circle,0),from);
  const arrived=system.bridgeCircle(from,circle,1);
  for(const key of ['x','y','radius'])assert(Math.abs(arrived[key]-circle[key])<1e-10);
  for(const t of [.1,.5,.9]){const forward=system.bridgeCircle(from,circle,t),reverse=system.bridgeCircle(circle,from,1-t);for(const key of ['x','y','radius'])assert(Math.abs(forward[key]-reverse[key])<1e-10);}
 }
}
const star={id:'star',kind:'star',knowledge:'surveyed'},planet={id:'planet',kind:'planet',knowledge:'surveyed'};
const record={parent:{id:'system'},bodies:[star],nodes:[planet],astronomy:{version:'static-v1',motion:'frozen',frame:'system-xyz-v1',position_unit:'micro-AU',systems:{system:{bodies:{star:{position:[0,0,0]},planet:{position:[100,0,0]}}}}}};
const gradient={addColorStop(){}},thumbnail={},images=[],labels=[];
const ctx=new Proxy({measureText:s=>({width:String(s).length*6}),createLinearGradient:()=>gradient,createRadialGradient:()=>gradient,drawImage:image=>images.push(image),fillText:s=>labels.push(s)},{get:(o,k)=>k in o?o[k]:()=>{}});
const opts={w:1000,h:800,record,view:{...system.fit(),selectedBodyId:'planet'},thumbnailsMap:new Map([['planet',thumbnail]]),safeRect:{left:0,right:1000,top:0,bottom:800}};
const before=system.draw(ctx,opts);assert(images.includes(thumbnail));images.length=0;
const suppressed=system.draw(ctx,{...opts,suppressBodyId:'planet'});
assert(!images.includes(thumbnail),'Bridge source must not contain a second selected globe');
assert.deepEqual(suppressed.positions,before.positions,'Suppressing paint must preserve layout and hit contracts');
console.log('Native silhouette agreement, exact/reversible bridge endpoints and single-globe System painting passed');

// Run the real bridge scheduler with callbacks deliberately delivered out of order.
const callbacks=new Map(),painted=[];let nextRaf=0,clock=1000,cancels=0,finished=0;
const state={systemSurfaceEntry:null,orbitActive:true};
const box={state,cancelOrbitFade(){},performance:{now:()=>clock},matchMedia:()=>({matches:false}),
 requestAnimationFrame:fn=>{callbacks.set(++nextRaf,fn);return nextRaf;},
 bridgeValid:t=>state.systemSurfaceEntry===t&&t.valid,renderMapHeading(){},drawMap(){},
 cancelSystemSurfaceEntry(){cancels++;state.systemSurfaceEntry=null;},releaseSystemEntryFrame(){},
 drawSystemBridge:t=>{painted.push(t.progress);return true;}};
vm.createContext(box);
vm.runInContext(app.slice(app.indexOf('  function animateSystemBridge('),app.indexOf('  function completeSystemReturn('))+';globalThis.animate=animateSystemBridge;',box);
const ticket=()=>({valid:true,from:{x:0},to:{x:1},direction:'enter',destination:'orbit'});
const run=(id,time=clock)=>{const fn=callbacks.get(id);assert(fn,'Every scheduled stage has a recorded handle');callbacks.delete(id);clock=time;fn(time);};
let t=ticket();state.systemSurfaceEntry=t;box.animate(t,()=>finished++);
assert.equal(painted.at(-1),0);run(t.raf);assert.equal(painted.at(-1),0);run(t.raf);
assert.equal(painted.at(-1),0,'Publication RAFs cannot spend the motion clock');
run(t.raf,1016);assert(painted.at(-1)>0&&painted.at(-1)<.01,'Bridge should accelerate gently from the published source');
run(t.raf,1042);assert(Math.abs(painted.at(-1)-.028)<1e-10);
run(t.raf,1210);assert(Math.abs(painted.at(-1)-.5)<1e-10);
run(t.raf,1378);assert(Math.abs(painted.at(-1)-.972)<1e-10,'Bridge should decelerate symmetrically toward its destination');
run(t.raf,1420);assert.equal(painted.at(-1),1);assert.equal(finished,1);
for(const stage of [0,1,2]){
 t=ticket();state.systemSurfaceEntry=t;box.animate(t);for(let i=0;i<stage;i++)run(t.raf);
 const stale=callbacks.get(t.raf),replacement=ticket();state.systemSurfaceEntry=replacement;box.animate(replacement);
 const before=painted.length,handle=replacement.raf;stale(clock+16);
 assert.equal(state.systemSurfaceEntry,replacement,'Stale publication/tick must not cancel its replacement');
 assert.equal(replacement.raf,handle);assert.equal(painted.length,before);
}
t=ticket();state.systemSurfaceEntry=t;box.animate(t);t.valid=false;run(t.raf);
assert.equal(cancels,1,'Invalid current ticket must still cancel and clean up');
// Destination publication also stores and validates both pending RAF handles.
const destination=app.slice(app.indexOf('  function completeSystemSurfaceEntry('),app.indexOf('  function enterInitialOrbit('));
const destinationRecord={geometry:{detail_ref:{sha256:'saved'}},selected_planet:{id:'planet'}};let prepared=0,animated=0;
Object.assign(box,{$:()=>({hidden:false}),orbitTextureFor(){},renderMapBreadcrumbs(){},renderMapLegend(){},renderOrbitControl(){},prepareSystemEntryFrame(){prepared++;return true;},animateSystemBridge(){animated++;}});
vm.runInContext(destination+';globalThis.complete=completeSystemSurfaceEntry;',box);
// The declaration above owns animateSystemBridge; replace its binding for this isolated phase check.
vm.runInContext('animateSystemBridge=()=>globalThis.didAnimate();',Object.assign(box,{didAnimate:()=>animated++}));
state.detailAsset={};state.mapRecord=destinationRecord;
for(const stage of [0,1]){
 const entry={...ticket(),direction:'enter',mapRequest:4,planetId:'planet',preview:{sourceSha:'saved',orientation:{}}};
 state.systemSurfaceEntry=entry;assert.equal(box.complete(destinationRecord,{request:4}),true);
 if(stage)run(entry.raf);
 const stale=callbacks.get(entry.raf),replacement=ticket();state.systemSurfaceEntry=replacement;stale(clock+16);
 assert.equal(state.systemSurfaceEntry,replacement);assert.equal(prepared,0);assert.equal(animated,0);
}
const entry={...ticket(),direction:'enter',mapRequest:4,planetId:'planet',preview:{sourceSha:'saved',orientation:{}}};
state.systemSurfaceEntry=entry;box.complete(destinationRecord,{request:4});run(entry.raf);run(entry.raf);
assert.equal(prepared,1);assert.equal(animated,1);
console.log('Actual bridge/destination publication clock, owned RAF handles and stale-callback isolation passed');
// A saved-camera route uses validated detail even when the preview raw entry was evicted.
const savedPose={latitude:.41,longitude:-1.2,distance:1.87},savedEntry={...ticket(),direction:'enter',destination:'orbit',mapRequest:5,planetId:'planet',savedCamera:{orbitView:savedPose}};
state.systemSurfaceEntry=savedEntry;state.pendingOrbitRestore={camera:savedEntry.savedCamera};
assert.equal(box.complete(destinationRecord,{request:5}),true);
assert.deepEqual({...state.orbitView},savedPose,'Saved camera must not be replaced by canonical preview pose');
assert.equal(state.pendingOrbitRestore,null);run(savedEntry.raf);run(savedEntry.raf);
assert.equal(prepared,2);assert.equal(animated,2);
console.log('Saved-camera destination accepts validated detail without preview and preserves exact pose');
