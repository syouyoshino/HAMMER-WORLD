// Exercise the app's actual bounded native-frame helper with counted GPU/copy calls.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('public/app.js','utf8');
const helper=source.slice(source.indexOf('  function clearNativeOrbitFrame()'),source.indexOf('  function releaseSystemEntryFrame()'));
let renders=0,copies=0,fail=false;
const state={contextEpoch:1,campaignId:'campaign',snapshot:{id:'snapshot'},mapStyle:'orbital',overlay:'terrain',orbitCanvas:{width:1440,height:1000}};
const box={state,window:{devicePixelRatio:1},document:{createElement(){return{width:0,height:0,getContext(){return{drawImage(){copies++;}};}};}},ensureOrbitRenderer:()=>({render(){renders++;return!fail;}})};
vm.createContext(box);vm.runInContext(`let nativeOrbitFrame=null,systemEntryCanvas=null;${helper};globalThis.cache={render:renderNativeOrbitFrame,clear:clearNativeOrbitFrame,peek:()=>nativeOrbitFrame,alias:()=>systemEntryCanvas};`,box);
const texture={source:{},key:'context:detail:terrain:orbital'},view={latitude:.3,longitude:1.2,distance:2.45,nightReadability:0},rect={left:0,top:160,width:1440,height:750},sun=[1,0,0];
const render=(overrides={})=>box.cache.render(overrides.texture||texture,overrides.w||1440,overrides.h||1000,overrides.view||view,overrides.rect||rect,overrides.sun||sun,overrides.scale||1);
const first=render();assert.strictEqual(render(),first);assert.equal(renders,1);assert.equal(copies,1,'Identical native frames must never copy WebGL twice');
const variants=[{texture:{...texture,key:'other-detail'}},{texture:{...texture,key:'context:detail:provinces:orbital'}},{texture:{...texture,key:'context:detail:terrain:survey'}},{w:1400},{h:900},{scale:.5},{view:{...view,latitude:.4}},{view:{...view,longitude:1.3}},{view:{...view,distance:2.5}},{view:{...view,nightReadability:.1}},{rect:{...rect,left:1}},{rect:{...rect,top:161}},{rect:{...rect,width:1400}},{rect:{...rect,height:740}},{sun:[0,1,0]}];
for(const variant of variants){const baseline=render(),before=renders,next=render(variant);assert.notStrictEqual(next,baseline);assert.equal(renders,before+1);assert.equal(baseline.width,1,'The previous full frame must be released on key mismatch');}
for(const update of [()=>state.contextEpoch++,()=>state.campaignId='other-campaign',()=>state.snapshot.id='other-snapshot',()=>box.window.devicePixelRatio=2,()=>state.mapStyle='survey',()=>state.overlay='provinces']){render();const before=renders;update();render();assert.equal(renders,before+1,'Authorization and viewport identity must discriminate frames');}
const beforeCopies=copies;fail=true;assert.equal(render({view:{...view,distance:3}}),null);assert.equal(box.cache.peek(),null);assert.equal(copies,beforeCopies,'Failed GPU renders cannot return stale pixels');
fail=false;const retained=render();box.cache.clear();assert.equal(retained.width,1);assert.equal(box.cache.peek(),null);assert.equal(box.cache.alias(),null);
console.log('Native frame reuse, one GPU-to-2D copy, context/pose/sun/viewport discrimination and bounded release passed');
