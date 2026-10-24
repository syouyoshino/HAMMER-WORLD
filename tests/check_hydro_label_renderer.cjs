// Observe actual renderer placement without adding production exports or a DOM dependency.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
let source=fs.readFileSync('public/map-renderer.js','utf8');
source=source.replace('    wrapsX,','    _qaProject:projectRiverPoints, _qaLabels:drawPlanetCopy,\n    wrapsX,');
const sandbox={window:{}};vm.createContext(sandbox);vm.runInContext(source,sandbox);
const renderer=sandbox.window.HWMapRenderer,cols=128,rows=80;
function context(){
 const strokes=[],stack=[],ctx={strokes,font:'',strokeStyle:'',save(){stack.push({font:this.font,strokeStyle:this.strokeStyle});},restore(){Object.assign(this,stack.pop());},
  beginPath(){this.path=[];},moveTo(x,y){this.path.push([x,y]);},lineTo(x,y){this.path.push([x,y]);},quadraticCurveTo(x,y,u,v){this.path.push([x,y],[u,v]);},
  stroke(){strokes.push({style:this.strokeStyle,points:this.path.slice()});},measureText(text){return{width:text.length*6.6};}};
 for(const key of ['rect','clip','translate','rotate','fillRect','strokeText','fillText'])ctx[key]=()=>{};
 return ctx;
}
function geometry(points,id='river-test',name='TestRiver'){
 const cells=[...new Set(points.map(([x,y])=>y*cols+((x%cols)+cols)%cols))];
 return {planet:{width:cols,height:rows},tiles:[],provinces:[],surface:{version:'planet-v9',topology:'cylinder-x',hydrology:'none',sea_level:null,elevation:Array(cols*rows).fill(450),
  rivers:[{id,points}],hydrography:{version:'hydrography-v1',features:[{id,kind:'river',material:'water',cells,anchor:cells[0],name}]}}};
}
const seam=[[126,36],[127,36],[0,36],[1,36],[2,36]],tile=25.6;
for(const ox of [-7000,-2467.5282051282056,0,809.2717948717946,6000]){
 const projected=renderer._qaProject(seam,cols,true,tile,ox,-420.1025641025641);
 for(let i=0;i<projected.length;i++)assert(Math.abs(projected[i][0]-(ox+(126+i+.5)*tile))<1e-9,'Camera translation changed longitude unwrapping');
 const ctx=context(),g=geometry(seam),zoom=tile/(1440/cols),panX=ox-(1440-cols*tile)/2;
 renderer._qaLabels(ctx,{geometry:g,w:1440,h:1024,zoom,panX,panY:0,selectedFeatureId:'river-test',featureNamesVisible:false,renderPhase:'labels'});
 const highlight=ctx.strokes.find(s=>s.style==='rgba(43,137,194,.92)');assert(highlight,'Selected river lost its stroke');
 for(let i=1;i<highlight.points.length;i++)assert(Math.abs(highlight.points[i][0]-highlight.points[i-1][0])<=tile+1e-9,'Selected course jumps across a world');
}
// The visible end of a long run must work even when its global midpoint is offscreen.
const partial=[[20,47],[21,47],[21,46],[21,45],...Array.from({length:29},(_,i)=>[22+i,45])],g=geometry(partial,'river-6036','IlyothLun'),ox=809.2717948717946,oy=-420.1025641025641;
const options={geometry:g,w:1440,h:1024,zoom:tile/(1440/cols),panX:ox-(1440-cols*tile)/2,panY:oy-(1024-rows*tile)/2,
 featureNamesVisible:true,renderPhase:'labels',safe:{left:0,right:1440,top:190.5,bottom:925.5}};
let result=renderer._qaLabels(context(),options),target=result.featureTargets.find(t=>t.id==='river-6036');
assert(target,'Partially visible unique course lost its name');assert(target.left>1350&&target.right<1437,'Rotated label bounds extend outside the visible chart');
// A collision with the preferred center must try a different candidate on the same course.
const straight=geometry(Array.from({length:51},(_,i)=>[20+i,30]));
const base={geometry:straight,w:1280,h:800,zoom:1,panX:0,panY:0,featureNamesVisible:true,renderPhase:'labels'};
const preferred=renderer._qaLabels(context(),base).featureTargets[0];assert(preferred);
result=renderer._qaLabels(context(),{...base,labelObstacles:[{left:preferred.left-8,right:preferred.right+8,top:preferred.top-8,bottom:preferred.bottom+8}]});
assert(result.featureTargets.length===1,'Collision discarded the whole river instead of trying another visible position');
assert(Math.abs(result.featureTargets[0].left-preferred.left)>preferred.right-preferred.left,'Fallback still overlaps the preferred label');
// Shared trunk cells cannot provide a name, and a vertical course remains unlabelled.
const shared=geometry(straight.surface.rivers[0].points);shared.surface.hydrography.features.push({...shared.surface.hydrography.features[0],id:'shared-river'});
assert.strictEqual(renderer._qaLabels(context(),{...base,geometry:shared}).featureTargets.length,0);
const vertical=geometry(Array.from({length:30},(_,i)=>[45,20+i]));
assert.strictEqual(renderer._qaLabels(context(),{...base,geometry:vertical}).featureTargets.length,0);
// Two visible periodic copies retain one canonical target for a feature.
const ids=new Set(),periodic={...base,w:3000,featureLabelIds:ids};
assert.strictEqual(renderer._qaLabels(context(),periodic).featureTargets.length,1);
assert.strictEqual(renderer._qaLabels(context(),{...periodic,copyIndex:1}).featureTargets.length,0);
console.log(JSON.stringify({result:'PASS',checks:'Positive/negative pan and seam projection; continuous selected course; partial-run names; collision fallback; shared-trunk/vertical exclusion; periodic deduplication'}));
