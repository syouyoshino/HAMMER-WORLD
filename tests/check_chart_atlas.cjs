const assert=require('node:assert/strict');
const view=require('../public/universe-view.js');
const region={id:'r',parent_id:'g',kind:'region',name:'Reach',knowledge:'surveyed',x:1,y:2};
const sector={id:'s',parent_id:'r',kind:'sector',name:'Hearth',knowledge:'surveyed',x:2,y:3};
const system={id:'a',parent_id:'s',kind:'system',name:'Cinder',knowledge:'surveyed',x:4,y:5};
const unlocated={id:'b',parent_id:'s',kind:'system',name:'Unknown',knowledge:'detected',x:100,y:100};
const otherSector={id:'t',parent_id:'r',kind:'sector',name:'Detected sector',knowledge:'detected',x:10,y:10};
const nested={id:'c',parent_id:'t',kind:'system',name:'Known child',knowledge:'surveyed',x:2,y:2};
const nonfinite={id:'d',parent_id:'s',kind:'system',name:'Invalid position',knowledge:'surveyed',x:Infinity,y:1};
const hidden={id:'secret',parent_id:'s',kind:'system',name:'Hidden',knowledge:'hidden',x:1,y:1};
const publicState={nodes:[region,sector,system,unlocated,otherSector,nested,nonfinite,hidden],links:[{a:'a',b:'b'}]};
const record={level:'galactic',groups:[{region,sectors:[sector,otherSector]}]};
const safe={left:10,right:1210,top:150,bottom:850,width:1200,height:700};
const text=[],lines=[];
const ctx=new Proxy({measureText:s=>({width:String(s).length*7}),fillText:s=>text.push(s),moveTo:(x,y)=>lines.push(['move',x,y]),lineTo:(x,y)=>lines.push(['line',x,y])},{get:(o,k)=>k in o?o[k]:()=>{}});
const before=JSON.stringify({record,publicState});
for(const theme of ['light','dark']){
 const layout=view.drawStrategic(ctx,{w:1240,h:900,record,publicState,safe,theme,forceControlRect:{left:1140,right:1210,top:150,bottom:180}});
 assert.deepEqual(layout.contactAnchors.map(p=>p.id),['a'],'Detected, nonfinite and unlocated-parent records cannot have spatial anchors');
 assert.deepEqual(layout.positions.map(p=>p.id),['a']);
 assert.deepEqual(layout.hitTargets.filter(p=>p.uiOnly).map(p=>p.id).sort(),['b','c','d','t']);
 for(const p of layout.hitTargets){assert(p.hitRect.left>=safe.left&&p.hitRect.right<=safe.right&&p.hitRect.top>=safe.top&&p.hitRect.bottom<=safe.bottom);}
 assert(text.includes('Known link: Cinder'),'Unlocated connection must be described without geometry');
 assert(text.includes('2 surveyed systems'),'Survey count is grammatical and public');
 assert(text.includes('Reach · REGION')&&text.includes('Hearth · SECTOR'),'Actual region and sector containment must be prominent');
 assert(text.indexOf('Reach · REGION')<text.indexOf('Hearth · SECTOR'),'Region is the parent presentation group');
 assert(layout.contactAnchors[0].baseX>safe.left+safe.width*.2,'Actionable system group is composed toward the chart center');
 const offscreen=view.drawStrategic(ctx,{w:1240,h:900,record,publicState,safe,theme,panX:5000});
 assert.equal(offscreen.positions.length,0);assert.deepEqual(offscreen.contactAnchors.map(p=>p.id),['a']);
 assert(offscreen.hitTargets.every(p=>p.uiOnly));
}
assert.equal(JSON.stringify({record,publicState}),before,'Drawing cannot mutate public state');
const universe=view.fromGalactic(record);
for(const height of [180,700]){
 const layout=view.draw(ctx,{w:1240,h:900,record:universe,safe:{...safe,height,bottom:safe.top+height},originContactIds:['r','s']});
 assert.deepEqual(layout.contactAnchors.map(p=>p.id).sort(),['r','s']);
 assert(layout.hitTargets.some(p=>p.id==='t'&&p.uiOnly));
 assert(!layout.positions.some(p=>p.id==='t'));
}
assert(text.includes('Origin: system'));
assert(text.includes('Known sectors in Reach'));
// With no located pair, the only chart line is the sector heading rule.
const lineStart=lines.length;
view.drawStrategic(ctx,{w:1240,h:900,record,publicState,safe});
assert.equal(lines.slice(lineStart).filter(item=>item[0]==='line').length,1,'Do not draw spatial links into a tray');
const textStart=text.length;
const planetState={...publicState,nodes:[...publicState.nodes,
 {id:'p',parent_id:'a',kind:'planet',knowledge:'surveyed',name:'Reach'},
 {id:'q',parent_id:'a',kind:'planet',knowledge:'surveyed',name:'Ash'},
 {id:'detected',parent_id:'a',kind:'planet',knowledge:'detected',name:null},
 {id:'secret-planet',parent_id:'a',kind:'planet',knowledge:'hidden',name:'Hidden canary'},
 {id:'unrelated',parent_id:'b',kind:'planet',knowledge:'surveyed',name:'Unrelated canary'}]};
const annotation=view.drawStrategic(ctx,{w:1240,h:900,record,publicState:planetState,safe});
const labels=text.slice(textStart);
assert(labels.includes('Surveyed planets · Reach, Ash'));
assert(labels.includes('Detected planets · Name unrecorded'));
assert(labels.includes('Open system ›'));
assert(!labels.some(line=>line.includes('canary')),'Only visible direct-child planets appear in system annotations');
assert.deepEqual(annotation.positions.map(point=>point.n.id),['a'],'Planet names do not become spatial positions');
const systemHit=annotation.hitTargets.find(point=>point.id==='a');
assert(systemHit.hitRect.bottom>=systemHit.y+115,'Open system cue must share the clickable system hit target');
console.log('Atlas location semantics, public links, clipping, themes and immutability passed');

const galaxy={id:'galaxy-review',kind:'galaxy',name:'Fictional Review Galaxy',knowledge:'surveyed'};
const reviewRegion={...region,parent_id:galaxy.id,name:'Fictional Review Region'};
const scope=view.galacticContext([galaxy,reviewRegion,sector,system],system.id);
assert.equal(scope.name,'Fictional Review Galaxy');
assert.deepEqual(scope.chain.map(node=>node.name),['Fictional Review Galaxy','Fictional Review Region','Hearth','Cinder']);
assert.equal(scope.chain.filter(node=>node.id===galaxy.id).length,1,'Actual galaxy appears once');
assert.equal(view.galacticContext([galaxy,{...galaxy,id:'other',name:'Other'}]).name,'Known galaxies','Do not choose an arbitrary galaxy');
assert.equal(view.galacticContext([{...galaxy,knowledge:'hidden'}]).name,'Galactic chart','Hidden roots are excluded');
