// Verify public settlement grouping and collision-safe spherical HUD placement.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const sandbox={window:{devicePixelRatio:1},document:{createElement:()=>({getContext:()=>null})}};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync('public/planet-orbit.js','utf8'),sandbox);
vm.runInContext(fs.readFileSync('public/orbit-landmarks.js','utf8'),sandbox);
const {groupsFor,layout}=sandbox.window.HWOrbitLandmarks,orbit=sandbox.window.HWPlanetOrbit;
const planet={width:64,height:32},rect={left:0,top:0,width:900,height:600},safeRect={left:20,top:20,right:880,bottom:580},view={latitude:0,longitude:0,distance:2.45};
const provinceLand=new Map();for(let i=0;i<15;i++)provinceLand.set(`p${i}`,{anchor:{x:32+i,y:15}});
const settlements=[
  {id:'b',name:'Bastion',planet_id:'planet-a',province_id:'p1'},
  {id:'a',name:'Landing',planet_id:'planet-a',province_id:'p1',owned:true},
  {id:'wrong-planet',name:'Wrong planet',planet_id:'planet-b',province_id:'p2'},
  {id:'missing-province',name:'Unanchored',planet_id:'planet-a',province_id:'gone'},
  ...Array.from({length:15},(_,i)=>({id:`site-${String(i).padStart(2,'0')}`,name:`Site ${i}`,planet_id:'planet-a',province_id:`p${i}`})),
];
const groups=groupsFor(settlements,'planet-a',provinceLand,'p8',planet);
assert.strictEqual(groups.length,15,'all prioritized candidates reach projection before the display cap');
assert.strictEqual(groups[0].provinceId,'p8','selected province is prioritized');
assert.strictEqual(groups.find(g=>g.provinceId==='p1').settlements.length,3,'same province settlements share the canonical anchor');
assert(groups.every(g=>!g.settlements.some(s=>s.planet_id!=='planet-a')),'other planets are excluded');
assert(!groups.some(g=>g.provinceId==='gone'),'settlements without canonical land anchors are excluded');
assert(groups.find(g=>g.provinceId==='p1').title.includes('recorded province anchor'),'label states the coordinate is the province anchor');

const items=layout(groups,{planet,view,rect,safeRect,screenPoint:orbit.screenPoint});
assert(items.length>0,'front-facing canonical anchors are projected');
assert(items.every(item=>item.point.depth>1/view.distance+.035),'near-horizon points are culled with margin');
assert(items.every(item=>item.labelRect.left>=safeRect.left&&item.labelRect.right<=safeRect.right),'labels remain inside the HUD safe rectangle');
for(let i=0;i<items.length;i++)for(let j=i+1;j<items.length;j++){
 const a=items[i].labelRect,b=items[j].labelRect;
 assert(!(a.left<b.right+5&&a.right>b.left-5&&a.top<b.bottom+5&&a.bottom>b.top-5),'labels do not collide');
}
for(const item of items){
 assert.strictEqual(item.leader.x1,item.point.x,'leader starts at exact recorded projected anchor');
 assert.strictEqual(item.leader.y1,item.point.y);
 const r=item.labelRect,p=item.leader;
 assert(p.x2>=r.left&&p.x2<=r.right&&p.y2>=r.top&&p.y2<=r.bottom&&(p.x2===r.left||p.x2===r.right||p.y2===r.top||p.y2===r.bottom),'leader ends at the nearest label edge');
}
const sample=items[0];assert(sample.point.x!==sample.labelRect.left||sample.point.y!==sample.labelRect.top,'text label offset remains distinct from canonical marker anchor');
const blocked=layout(groups,{planet,view,rect,safeRect,obstacles:[{left:0,top:0,right:900,bottom:600}],screenPoint:orbit.screenPoint});
assert.strictEqual(blocked.length,0,'UI obstruction suppresses covered marker anchors');
const back=layout([{...groups[0],anchor:{x:0,y:15}}],{planet,view,rect,safeRect,screenPoint:orbit.screenPoint});
assert.strictEqual(back.length,0,'back-facing markers are omitted');
// A full cap of higher-priority backside sites must not starve a visible site.
const backsideLand=new Map(Array.from({length:12},(_,i)=>[`back-${i}`,{anchor:{x:i/10,y:15}}]));
backsideLand.set('front',{anchor:{x:32,y:15}});
const backsideSites=[...backsideLand.keys()].map(id=>({id,name:id,planet_id:'planet-a',province_id:id,owned:id!=='front'}));
const backsideGroups=groupsFor(backsideSites,'planet-a',backsideLand,null,planet);
assert.strictEqual(backsideGroups.length,13);
assert.deepStrictEqual(Array.from(layout(backsideGroups,{planet,view,rect,safeRect,screenPoint:orbit.screenPoint}),item=>item.provinceId),['front'],'twelve rejected backside groups do not consume the placement cap');
const selectedGroups=groupsFor(backsideSites,'planet-a',backsideLand,'front',planet);
assert.strictEqual(selectedGroups[0].provinceId,'front','visible selected site precedes owned backside sites');

const invalidLand=new Map([['negative',{anchor:{x:-1,y:0}}],['east',{anchor:{x:64,y:15}}],['south',{anchor:{x:32,y:32}}],['nan',{anchor:{x:NaN,y:15}}],['fine-edge',{anchor:{x:-.25,y:15}}]]);
const invalidSites=[...invalidLand.keys()].map(id=>({id,planet_id:'planet-a',province_id:id}));
assert.deepStrictEqual(Array.from(groupsFor(invalidSites,'planet-a',invalidLand,null,planet),g=>g.provinceId),['fine-edge'],'invalid world coordinates are excluded while valid fine-grid tile centers remain allowed');
assert.strictEqual(layout([{provinceId:'bad',anchor:{x:64,y:15},label:'bad'}],{planet,view,rect,safeRect,screenPoint:()=>{throw Error('invalid anchor projected');}}).length,0,'layout independently rejects out-of-world anchors');

// Controlled projection tests both collision directions, anchor crosses, and cap order.
const controlledPlanet={width:100,height:100},controlledSafe={left:0,top:0,right:2000,bottom:1000};
const positions=new Map(),controlledGroups=[];
function controlledGroup(id,x,y){const index=controlledGroups.length;positions.set(index,{x,y,depth:1});const group={provinceId:id,anchor:{x:index,y:50},label:id};controlledGroups.push(group);return group;}
controlledGroup('selected',300,300);
controlledGroup('later-anchor',340,280); // Inside the first label candidate of the selected site.
controlledGroup('near-cross',310,300); // Marker crosses overlap; the earlier priority wins.
const controlledProjection=(latitude,longitude)=>positions.get(Math.round((longitude+Math.PI)/(2*Math.PI)*100-.5));
const controlledOptions={planet:controlledPlanet,view,rect,safeRect:controlledSafe,screenPoint:controlledProjection,measure:()=>({width:76,height:24})};
const collisionItems=layout(controlledGroups,controlledOptions);
assert.strictEqual(collisionItems[0].provinceId,'selected','priority survives competing anchors');
assert(!collisionItems.some(item=>item.provinceId==='near-cross'),'overlapping anchor crosses are suppressed');
assert(collisionItems[0].labelRect.left!==313||collisionItems[0].labelRect.top!==268,'label moves away from the later marker rather than covering it');
for(const item of collisionItems)for(const other of collisionItems){
 const a=item.labelRect,b=other.markerRect;
 assert(!(a.left<b.right+2&&a.right>b.left-2&&a.top<b.bottom+2&&a.bottom>b.top-2),'labels do not cross any displayed marker');
}
assert.strictEqual(JSON.stringify(layout(controlledGroups,controlledOptions)),JSON.stringify(collisionItems),'collision choices are deterministic');
positions.clear();controlledGroups.length=0;
for(let i=0;i<15;i++)controlledGroup(`cap-${i}`,100+i%5*300,100+Math.floor(i/5)*250);
const capped=layout(controlledGroups,controlledOptions);
assert.strictEqual(capped.length,12,'only successful placements count toward the visible cap');
assert.strictEqual(capped[0].provinceId,'cap-0');
assert.strictEqual(capped[11].provinceId,'cap-11');
console.log('orbit settlement grouping, visible cap, anchor validity, priority and deterministic label/marker collision checks passed');
