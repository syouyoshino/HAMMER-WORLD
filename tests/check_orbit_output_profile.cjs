// Exercise the actual runtime pixel policy with measured completion costs.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const box={window:{}};vm.createContext(box);vm.runInContext(fs.readFileSync('public/planet-orbit.js','utf8'),box);
const create=box.window.HWPlanetOrbit.createOutputProfile;
const fast=create();for(let i=0;i<20;i++)fast.observe(1440000,33);
assert.equal(fast.scale(1440,1000,1,1),1);assert.equal(fast.scale(1440,1000,1,.5),.5,'Fast devices keep existing moving quality');
const slow=create();for(let i=0;i<30;i++)slow.observe(4000,10000);
assert.equal(slow.scale(1440,1000,1,1),.45,'Stable output cannot collapse below 450 physical pixels on its short side');
assert.equal(slow.scale(1440,1000,1,.5),.16,'Moving output cannot collapse below 160 physical pixels on its short side');
// Physical floors are independent of DPR and cannot exceed requested quality.
const dpr2=slow.scale(1440,1000,2,1),base2=Math.sqrt(2097152/1440000);
assert.ok(Math.abs(1000*base2*dpr2-450)<1e-8);
assert.equal(slow.scale(200,100,1,.5),.5);
const recover=create();recover.observe(1440000,1632);
const before=recover.scale(1440,1000,1,.5);for(let i=0;i<35;i++)recover.observe(1440000,40);
assert.ok(recover.scale(1440,1000,1,.5)>before,'Fast recent observations must recover quality');
assert.equal(recover.scale(1440,1000,1,1),1,'Recovery can regain full quality');
recover.observe(1440000,10000);assert.equal(recover.scale(1440,1000,1,1),1,'One isolated stall cannot erase recent fast observations');
recover.observe(0,500);recover.observe(100,NaN);assert.equal(recover.scale(1440,1000,1,1),1);
assert.equal(create().scale(1440,1000,1,1),1,'A fresh runtime profile has no cross-session degradation');
console.log('Measured output policy preserves fast quality, physical detail floors, recent-median robustness and recovery');
// Actual scheduling helper waits past presentation and rejects changed identities.
const app=fs.readFileSync('public/app.js','utf8'),helper=app.slice(app.indexOf('  function measureOrbitPresentation('),app.indexOf('  function clearNativeOrbitFrame('));
const callbacks=[],observed=[],frame={clientWidth:1440,clientHeight:1000},state={contextEpoch:1,campaignId:'one',snapshot:{id:'saved'},mapRecord:{},mapStyle:'orbital',overlay:'terrain',orbitCanvas:{width:648,height:450}};
Object.assign(box,{state,$:()=>({parentElement:frame}),document:{visibilityState:'visible'},performance:{now:()=>1600},requestAnimationFrame:fn=>callbacks.push(fn)});
vm.runInContext(`let orbitPresentationSample=null,orbitPresentationGeneration=0,orbitOutputProfile={observe:(...args)=>globalThis.record(...args)};${helper};globalThis.measure=measureOrbitPresentation;`,Object.assign(box,{record:(...args)=>observed.push(args)}));
const measure=()=>box.measure(0,291600,1440,1000),flush=()=>{while(callbacks.length)callbacks.shift()();};
measure();assert.equal(callbacks.length,1);callbacks.shift()();assert.equal(observed.length,0);callbacks.shift()();assert.equal(observed.length,1);
for(const mutate of [()=>state.contextEpoch++,()=>state.campaignId+='x',()=>state.snapshot={id:'next'},()=>state.mapRecord={},()=>state.mapStyle='survey',()=>state.overlay='provinces',()=>frame.clientWidth--,()=>frame.clientHeight--,()=>box.window.devicePixelRatio=2,()=>state.orbitCanvas.width--]){
  frame.clientWidth=1440;frame.clientHeight=1000;measure();callbacks.shift()();const before=observed.length;mutate();flush();assert.equal(observed.length,before,'Changed authorization, record, rendering style or viewport invalidates the sample');
}
frame.clientWidth=1440;frame.clientHeight=1000;measure();callbacks.shift()();measure();flush();assert.equal(observed.length,2,'A newer presentation must discard the old generation and train only once');
box.document.visibilityState='hidden';measure();assert.equal(callbacks.length,0);
console.log('Presentation samples wait two RAFs and reject obsolete generations, authorization, record/style/viewport and hidden starts');
