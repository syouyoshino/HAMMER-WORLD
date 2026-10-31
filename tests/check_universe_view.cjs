const assert=require('node:assert/strict');
const view=require('../public/universe-view.js');
const region={id:'r',parent_id:'g',kind:'region',knowledge:'surveyed',name:'Known region',x:9,y:8};
const a={id:'a',parent_id:'r',kind:'sector',knowledge:'surveyed',name:'A long recorded sector name',x:1,y:2};
const b={id:'b',parent_id:'r',kind:'sector',knowledge:'detected',name:'Unsurveyed Sector',x:null,y:null};
const hidden={id:'hidden',kind:'sector',knowledge:'hidden',name:'Hidden canary',x:2,y:3};
const input={campaign_id:'c',snapshot_id:'s',turn:3,level:'galactic',groups:[{region,sectors:[a,b,hidden]}],nodes:[a,b],links:[],records:[]};
const before=JSON.stringify(input),record=view.fromGalactic(input);
assert.equal(JSON.stringify(input),before,'Derivation must not change the public input');
assert.equal(record.level,'universe');assert.equal(record.campaign_id,'c');assert.equal(record.snapshot_id,'s');
assert.deepEqual(record.nodes.map(n=>n.id),['r','a','b']);
assert.deepEqual(record.nodes.find(n=>n.id==='b'),b,'Unknown coordinates must remain unknown');
assert.deepEqual(record.nodes.find(n=>n.id==='r'),region,'Chart coordinates must not become universal distances');
assert(!view.fromGalactic({groups:[{region:{...region,knowledge:'hidden'},sectors:[a]}]}).nodes.length);
const gradient={addColorStop(){}};const ctx=new Proxy({measureText:s=>({width:String(s).length*7}),createRadialGradient:()=>gradient,createLinearGradient:()=>gradient},{get:(o,k)=>k in o?o[k]:()=>{}});
for(const theme of ['light','dark']){
 const prior=JSON.stringify(record),layout=view.draw(ctx,{w:1440,h:1000,record,safe:{left:12,right:1428,top:220,bottom:920,width:1416,height:700},zoom:1,panX:0,panY:0,theme});
 assert.equal(JSON.stringify(record),prior,'Drawing must not mutate contact records');
 assert.deepEqual(new Set(layout.positions.map(p=>p.n.id)),new Set(['r','a','b']));
 assert(layout.positions.every(p=>Number.isFinite(p.x)&&Number.isFinite(p.y)));
 const hiddenTargets=layout.hitTargets.filter(p=>p.n.id==='hidden');assert.equal(hiddenTargets.length,0);
 const second=view.draw(ctx,{w:1440,h:1000,record:view.fromGalactic({...input,groups:[{region:{...region,x:999999,y:-999999},sectors:[{...a,x:-88,y:23},b]}]}),safe:{left:12,right:1428,top:220,bottom:920,width:1416,height:700},zoom:1,panX:0,panY:0,theme});
 assert.deepEqual(layout.positions.map(p=>[p.x,p.y]),second.positions.map(p=>[p.x,p.y]),'Schematic must not imply parent-local coordinates are universal');
}
for(const theme of ['light','dark']){
 const safe={left:0,right:800,top:218,bottom:398,width:800,height:180};
 const layout=view.draw(ctx,{w:800,h:480,record,safe,zoom:1,panX:0,panY:0,theme});
 assert.equal(layout.positions.length,3);
 for(const point of layout.positions){const r=point.frameRect;assert(r);assert(r.top>=safe.top+48&&r.bottom<=safe.bottom&&r.left>=safe.left&&r.right<=safe.right,'Full label frames must fit below captions on short desktop');}
 const boxes=layout.positions.map(p=>p.frameRect);
 for(let i=0;i<boxes.length;i++)for(let j=i+1;j<boxes.length;j++){const a=boxes[i],b=boxes[j];assert(!(a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top),'Compact contact labels overlap');}
}
const empty=view.fromGalactic({groups:[],level:'galactic'});assert.deepEqual(empty.nodes,[]);
view.draw(ctx,{w:1280,h:720,record:empty,safe:{left:10,right:1270,top:180,bottom:680,width:1260,height:500}});
console.log('Universe authorized contact derivation, unknown positions, immutable schematic layout and themes passed');
