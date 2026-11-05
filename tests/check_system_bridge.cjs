const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
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
