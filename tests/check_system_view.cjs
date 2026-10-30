const assert=require('node:assert/strict');
const view=require('../public/system-view.js');
const star={id:'s',kind:'star',name:'Star',knowledge:'surveyed'};
const a={id:'a',kind:'planet',name:'Inner',knowledge:'surveyed'};
const b={id:'b',kind:'planet',name:'Outer',knowledge:'surveyed'};
const unknown={id:'u',kind:'moon',parent_id:'a',name:'Contact',knowledge:'detected'};
const hidden={id:'h',kind:'planet',name:'Hidden',knowledge:'hidden'};
const record={level:'system',parent:{id:'sys'},bodies:[star],nodes:[{...a,moons:[unknown]},b,hidden],
 astronomy:{version:'static-v1',motion:'frozen',frame:'system-xyz-v1',position_unit:'micro-AU',systems:{sys:{bodies:{
 s:{position:[100,0,100]},a:{position:[110,0,100]},b:{position:[120,0,100]},u:{position:[100,10,100]},h:{position:[120,4,100]}}}}}};
const before=JSON.stringify(record),model=view.model(record);
assert(model.supported);assert.equal(model.normalizer,20);
assert.deepEqual(model.located.find(p=>p.n.id==='a').normalized,[.5,0,0]);
assert.deepEqual(model.located.find(p=>p.n.id==='b').normalized,[1,0,0]);
assert.deepEqual(model.unlocated.map(n=>n.id),['u']);
const viewport={width:1280,height:720,safeRect:{left:10,top:100,right:1270,bottom:670}};
const p0=view.project(record,{yaw:0,pitch:.55,distance:3.4},viewport);
const p1=view.project(record,{yaw:1,pitch:.2,distance:3.4},viewport);
assert.notDeepEqual(p0.positions,p1.positions,'Free orbit must change projection');
const full=view.project(record,{yaw:Math.PI*2,pitch:.55,distance:3.4},viewport);
for(let i=0;i<p0.positions.length;i++)assert(Math.hypot(p0.positions[i].x-full.positions[i].x,p0.positions[i].y-full.positions[i].y)<1e-7,'Full yaw must return same projection');
const dock=p0.hitTargets.find(p=>p.n.id==='u');assert(dock?.uiOnly);
assert(dock.displayName.includes('Inner'),'Unlocated moon must identify its parent world');
assert(p0.hitTargets.find(p=>p.n.id==='a').labelSecondary.includes('AU from host star'));
assert(!p0.positions.some(p=>p.n.id==='u'||p.n.id==='h'));
for(const v of [{yaw:NaN,pitch:Infinity,distance:0},{yaw:1e10,pitch:-4,distance:Infinity},{}]){
 const layout=view.project(record,v,viewport);
 for(const p of layout.positions)assert(Number.isFinite(p.x)&&Number.isFinite(p.y));
}
const missing=structuredClone(record);delete missing.astronomy;
const absent=view.model(missing);assert(!absent.supported);assert.equal(absent.located.length,0);assert.equal(absent.unlocated.length,4);
const invalid=structuredClone(record);invalid.astronomy.systems.sys.bodies.s.position=[NaN,0,0];
assert.equal(view.model(invalid).located.length,0,'Invalid host origin must not locate contacts');
assert.equal(view.model(invalid).unlocated.length,4);
assert.equal(JSON.stringify(record),before,'Renderer must not mutate recorded data');
const context=new Proxy({}, {get(_,name){
 if(name==='measureText')return value=>({width:String(value).length*6});
 if(name==='createLinearGradient'||name==='createRadialGradient')return ()=>({addColorStop(){}});
 return (...args)=>{for(const value of args)if(typeof value==='number')assert(Number.isFinite(value),name+' must draw finite coordinates');};
},set(){return true;}});
view.draw(context,{w:1280,h:720,record,view:view.fit(),safeRect:viewport.safeRect});
view.draw(context,{w:1280,h:720,record:missing,view:view.fit(),safeRect:viewport.safeRect});
console.log('System position ratios, unknown isolation, free projection, numeric guards and immutable records passed');
