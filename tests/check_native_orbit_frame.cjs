// Exercise the app's actual direct WebGL layer cache with counted GPU/copy calls.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('public/app.js','utf8');
const helper=source.slice(source.indexOf('  function clearNativeOrbitFrame()'),source.indexOf('  function releaseSystemEntryFrame('));
let renders=0,copies=0,fail=false;
const layer={width:1440,height:1000,style:{}};
const state={contextEpoch:1,campaignId:'campaign',snapshot:{id:'snapshot'},mapStyle:'orbital',overlay:'terrain',orbitCanvas:layer};
const box={state,cancelOrbitFade(){},performance:{now:()=>0},measureOrbitPresentation(){},window:{devicePixelRatio:1},document:{createElement(){return{width:0,height:0,getContext(){return{drawImage(){copies++;}};}};}},ensureOrbitRenderer:()=>({render(){renders++;return!fail;}})};
vm.createContext(box);vm.runInContext(`let nativeOrbitFrame=null,systemEntryCanvas=null,orbitPresentationSample=null,orbitOutputProfile=null,orbitMovingScale=null;${helper};globalThis.cache={render:renderNativeOrbitFrame,clear:clearNativeOrbitFrame,peek:()=>nativeOrbitFrame,alias:()=>systemEntryCanvas};`,box);
const texture={source:{},key:'context:detail:terrain:orbital'},view={latitude:.3,longitude:1.2,distance:2.45,nightReadability:0},rect={left:0,top:160,width:1440,height:750},sun=[1,0,0];
const render=(overrides={})=>box.cache.render(overrides.texture||texture,overrides.w||1440,overrides.h||1000,overrides.view||view,overrides.rect||rect,overrides.sun||sun,overrides.scale||1);
const first=render();assert.strictEqual(render(),first);assert.equal(first,layer,'The visible result must be the mounted WebGL canvas');assert.equal(renders,1);assert.equal(copies,0,'Normal display must not copy WebGL pixels to 2D');
box.cache.render(texture,1440,1000,view,rect,sun,1,true);assert.equal(renders,2,'A return sprite must refresh the WebGL drawing buffer before its one bounded copy');assert.equal(copies,0,'The frame helper itself must not perform CPU copies');
const variants=[{texture:{...texture,key:'other-detail'}},{texture:{...texture,key:'context:detail:provinces:orbital'}},{texture:{...texture,key:'context:detail:terrain:survey'}},{w:1400},{h:900},{scale:.5},{view:{...view,latitude:.4}},{view:{...view,longitude:1.3}},{view:{...view,distance:2.5}},{view:{...view,nightReadability:.1}},{rect:{...rect,left:1}},{rect:{...rect,top:161}},{rect:{...rect,width:1400}},{rect:{...rect,height:740}},{sun:[0,1,0]}];
for(const variant of variants){const baseline=render(),before=renders,next=render(variant);assert.strictEqual(next,layer,'Pose changes keep the same mounted canvas');assert.strictEqual(next,baseline);assert.equal(renders,before+1,'Every changed pose must render directly into the mounted canvas');}
for(const update of [()=>state.contextEpoch++,()=>state.campaignId='other-campaign',()=>state.snapshot.id='other-snapshot',()=>box.window.devicePixelRatio=2,()=>state.mapStyle='survey',()=>state.overlay='provinces']){render();const before=renders;update();render();assert.equal(renders,before+1,'Authorization and viewport identity must discriminate frames');}
const beforeCopies=copies;fail=true;assert.equal(render({view:{...view,distance:3}}),null);assert.equal(box.cache.peek(),null);assert.equal(copies,beforeCopies,'Failed GPU renders cannot return stale pixels');
fail=false;const retained=render();box.cache.clear();assert.equal(retained.width,1);assert.equal(retained.height,1);assert.equal(retained.style.visibility,'hidden');assert.equal(box.cache.peek(),null);assert.equal(box.cache.alias(),null);
// Completing a valid forward bridge must remove only its CSS transform/clip.
const release=source.slice(source.indexOf('  function releaseSystemEntryFrame('),source.indexOf('  function bridgeTicket('));
box.$=()=>({parentElement:{classList:{remove(){}}}});
vm.runInContext(`let systemBridgeSource=null;${release};globalThis.release=releaseSystemEntryFrame;`,box);
render();layer.style.visibility='visible';layer.style.transform='scale(.5)';layer.style.clipPath='circle(20px)';const beforeFinish=renders;
box.release(true);assert.strictEqual(box.cache.peek().canvas,layer);assert.equal(layer.style.visibility,'visible');assert.equal(layer.style.transform,'');assert.equal(layer.style.clipPath,'');render();assert.equal(renders,beforeFinish,'Forward bridge keeps the exact valid native frame');
box.release();assert.equal(box.cache.peek(),null);assert.equal(layer.style.visibility,'hidden','Cancellation/return must invalidate and hide the frame');
console.log('Direct WebGL layer reuse, zero ordinary 2D copies, forced fresh capture, context/pose/sun/viewport discrimination and context clear passed');

// A held gesture keeps its tier even when presentation observations change.
const scales=[],modes=[];let policyCalls=0,clock=0,idle=null,idleDraws=0;
box.performance.now=()=>clock;
box.ensureOrbitRenderer=()=>({render(...args){scales.push(args[7]);modes.push(args[8]);renders++;return true;}});
box.window.HWPlanetOrbit={createOutputProfile:()=>({scale:()=>.2+(++policyCalls)*.01})};
box.setTimeout=callback=>{idle=callback;return 1;};box.clearTimeout=()=>{idle=null;};
box.drawMap=()=>{idleDraws++;render();};state.orbitActive=true;state.drag={orbit:true};
const note=source.slice(source.indexOf('  function noteOrbitMotion('),source.indexOf('  function schedulePointerMapDraw('));
vm.runInContext(`let orbitQualityUntil=0,orbitQualityTimer=0;${note};globalThis.noteMotion=noteOrbitMotion;`,box);
box.cache.clear();box.noteMotion();render({scale:.5,view:{...view,longitude:2}});const movingTier=scales.at(-1);assert.equal(modes.at(-1),true,'Only reduced moving output requests the bounded kernel');
clock=260;idle(); // Timer fires while the pointer is stationary but still held.
box.noteMotion();render({scale:.5,view:{...view,longitude:2.1}});
assert.equal(scales.at(-1),movingTier,'Held drag must retain its moving tier after an idle-length pause');
assert.equal(policyCalls,1,'A gesture samples the output policy once');
state.drag=null;clock=500;idle();assert.equal(idleDraws,1,'Release permits one idle refinement');
assert.equal(modes.at(-1),false,'Idle refinement keeps the original kernel');
const afterIdle=renders;render();assert.equal(renders,afterIdle,'Unchanged settled redraw reuses the idle refinement');
box.noteMotion();render({scale:.5,view:{...view,longitude:2.2}});
assert.notEqual(scales.at(-1),movingTier,'A new gesture may select a newly measured output tier');
const beforeViewport=policyCalls;render({scale:.5,w:1300,view:{...view,longitude:2.3}});
assert.equal(policyCalls,beforeViewport+1,'Viewport changes must choose a valid new output size');
console.log('Held-drag tier pinning, single idle refinement, fresh gesture and viewport re-selection passed');

// A fast device at its requested moving quality retains the exact full kernel.
vm.runInContext('orbitOutputProfile={scale:(w,h,dpr,requested)=>requested};orbitMovingScale=null;',box);
render({scale:.5,view:{...view,longitude:2.4}});assert.equal(modes.at(-1),false);
console.log('Slow moving output opts into bounded filtering; full-quality motion and idle retain original filtering');
