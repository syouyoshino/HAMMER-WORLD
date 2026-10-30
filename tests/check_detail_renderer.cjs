// Exercise native recorded geography, its display cache and strategic projection.
const fs=require('fs'),vm=require('vm'),assert=require('assert'),crypto=require('crypto');
const pixelHash=canvas=>crypto.createHash('sha256').update(canvas.pixels.data).update(canvas.layer?.pixels?.data||new Uint8Array()).digest('hex');
let source=fs.readFileSync('public/map-renderer.js','utf8');
source=source.replace('    detailAt,','    detailAt,\n    _qaBaseRaster:baseRaster, _qaLighting:dryLightingHeight, _qaCraterNormals:dryCraterDerivatives, _qaProfile:craterProfile, _qaFineRaster:fineRaster, _qaFineGeometry:fineGeometry, _qaBoundary:fineFeatureBoundary, _qaCopy:drawPlanetCopy,');
const canvases=[];
const sandbox={window:{},document:{createElement:()=>{
  const canvas={},context={canvas,createImageData:(w,h)=>({width:w,height:h,data:new Uint8ClampedArray(w*h*4)}),
    putImageData:image=>canvas.pixels=image,drawImage:layer=>canvas.layer=layer};
  for(const name of ['save','restore','beginPath','moveTo','lineTo','quadraticCurveTo','stroke','translate'])context[name]=()=>{};
  canvas.strokes=[];context.stroke=function(){canvas.strokes.push({width:this.lineWidth,style:this.strokeStyle});};
  canvas.getContext=()=>context;canvases.push(canvas);return canvas;
}}};
vm.createContext(sandbox);vm.runInContext(source,sandbox);
const renderer=sandbox.window.HWMapRenderer,w=1024,h=640,size=w*h;
// Orbital Survey keeps recorded terrain categories and rivers, but omits chart contours.
const chartGeometry={planet:{width:16,height:8},tiles:Array.from({length:128},(_,i)=>({x:i%16,y:Math.floor(i/16),terrain:i%16<8?'plains':'rock'})),
  surface:{version:'planet-v9',topology:'cylinder-x',hydrology:'ocean-draining',sea_level:400,elevation:Array.from({length:128},(_,i)=>420+(i%16)*30),rivers:[]}},
  chart=renderer._qaBaseRaster(chartGeometry,'survey'),chartBefore=pixelHash(chart),
  albedoChart=renderer._qaBaseRaster(chartGeometry,'survey',true);
assert(chart.strokes.length>0&&albedoChart.strokes.length===0,'Orbital Survey retained chart contour ink');
assert.strictEqual(pixelHash(chart),chartBefore,'Albedo construction changed strategic chart bytes');
const chartPixel=x=>Array.from(albedoChart.pixels.data.slice((4*24*albedoChart.width+x*24)*4,(4*24*albedoChart.width+x*24)*4+3));
assert.notDeepStrictEqual(chartPixel(4),chartPixel(12),'Orbital albedo discarded recorded terrain categories');
const detail={version:'planet-detail-v2',width:w,height:h,terrain_grid:'p'.repeat(size),elevation:Array(size).fill(620),
  materials:'0'.repeat(size),feature_index:Array(size).fill(0),feature_ids:['ocean','river','branch','lake'],
  hydrography:{version:'hydrography-v2',features:[{id:'ocean',kind:'ocean',name:'Ocean',anchor:0},
    {id:'river',kind:'river',name:'Main',anchor:50*w+20},{id:'branch',kind:'river',name:'Branch',anchor:49*w+22},
    {id:'lake',kind:'lake',name:'Lake',anchor:100*w+100}]},
  rivers:[{id:'river',points:[50*w+20,50*w+21,50*w+22,50*w+23]},
    {id:'branch',points:[49*w+22,50*w+22,50*w+23]}],province_anchors:[{province_id:'p',cell:40*w+80}],craters:[]};
detail.terrain_grid='o'+detail.terrain_grid.slice(1,8)+'r'+detail.terrain_grid.slice(9);
for(const i of [0,50*w,50*w+w-1])detail.feature_index[i]=1;
detail.feature_index[100*w+100]=4;
for(let y=0;y<5;y++)for(let x=30;x<=34;x++)detail.elevation[y*w+x]=401;
const geometry={planet:{width:128,height:80},tiles:[],provinces:[{id:'p',name:'Province'}],
  surface:{version:'planet-v10',topology:'cylinder-x',hydrology:'ocean-draining',sea_level:400,preset:'continental',geology:'none',lake_material:'none',polar_caps:'none'}};
assert.strictEqual(renderer.provinceLand(geometry).size,0,'Unloaded V10 invented a province anchor');
geometry.province_anchors=detail.province_anchors;geometry.province_anchor_grid={width:w,height:h};
const anchor=renderer.provinceLand(geometry).get('p').anchor;
assert.strictEqual(anchor.x+.5,80.5/8,'Province ignored saved fine longitude');
assert.strictEqual(anchor.y+.5,40.5/8,'Province ignored saved fine latitude');
const entry=renderer._qaFineGeometry(detail,geometry);
assert.strictEqual(entry.geometry.surface.elevation,detail.elevation,'Native heights were rescaled or derived from coarse fields');
assert.strictEqual(entry.geometry.surface.rivers.length,0,'Compositor added an extra drainage pass');
assert.strictEqual(entry.paths.get('branch')[0].length,3,'Native shared river trunk was truncated');
assert.strictEqual(entry.owners.get(50*w+22),2,'Shared trunk lost label ownership exclusion');
assert.strictEqual(renderer._qaFineGeometry(detail,geometry),entry,'Display proxy was rebuilt');
const raster=renderer._qaFineRaster(detail,geometry,'orbital'),scale=raster.width/w;
assert.strictEqual(raster.width,1536,'Output raster exceeded its bounded display resolution');
const px=(x,y=0)=>{const off=(Math.floor((y+.5)*scale)*raster.width+Math.floor((x+.5)*scale))*4;return Array.from(raster.pixels.data.slice(off,off+3));};
assert.notDeepStrictEqual(px(8),px(9),'Saved fine terrain did not affect material appearance');
assert(Math.max(...px(32,2))<180,'Near-sea land gained an amplified neon colour from the height threshold');
const widths=raster.strokes.map(stroke=>stroke.width);
assert(Math.max(...widths)>Math.min(...widths)*1.3,'Shared saved trunks are indistinguishable from tributaries');
assert(Math.min(...widths)>=.4&&Math.max(...widths)<=1.65,'Recorded network hierarchy exceeded bounded gameplay ink');
assert.strictEqual(renderer._qaFineRaster(detail,geometry,'orbital'),raster,'Fine raster cache was lost');
assert.strictEqual(renderer.detailAt(geometry,detail,0,0).featureId,'ocean','Recorded feature ID was lost');
assert.strictEqual(renderer.detailAt(geometry,detail,-.0625,1).x,1023,'Negative longitude did not wrap');
assert.strictEqual(renderer.detailAt(geometry,detail,128.0625,1).x,0,'Positive longitude did not wrap');
assert.strictEqual(renderer.detailAt(geometry,detail,1,80),null,'Out-of-range latitude gained fake terrain');
const outline=renderer._qaBoundary(detail,geometry,'ocean'),seam=outline.filter(segment=>segment[1]>=50);
assert.strictEqual(seam.length,6,'Fine body gained a false seam or coarse boundary');
assert(!seam.some(segment=>segment[0]===segment[2]&&(segment[0]===0||segment[0]===w)),'Joined body gained a longitude-seam outline');
assert.strictEqual(renderer._qaBoundary(detail,geometry,'ocean'),outline,'Fine outline cache was rebuilt');
const labelCtx={measureText:text=>({width:text.length*6})};
for(const key of ['save','restore','beginPath','moveTo','lineTo','quadraticCurveTo','stroke','translate','rect','clip','rotate','fillRect','strokeRect','strokeText','fillText','closePath','fill'])labelCtx[key]=()=>{};
renderer._qaCopy(labelCtx,{geometry,detail,w:1440,h:1024,zoom:2,panX:0,panY:0,selectedFeatureId:'lake',featureNamesVisible:true,renderPhase:'labels'});
const labelOptions={geometry,detail,w:1440,h:1024,zoom:2,
  panX:720-(1440-128*22.5)/2-(80.5/8)*22.5,
  panY:512-(1024-80*22.5)/2-(40.5/8)*22.5,renderPhase:'labels'};
assert.strictEqual(renderer._qaCopy(labelCtx,labelOptions).provinceTargets.length,0,'Terrain view showed an unselected empty province chip');
assert.strictEqual(renderer._qaCopy(labelCtx,{...labelOptions,overlay:'provinces'}).provinceTargets.length,1,'Province overlay lost its empty province chip');
const selected=renderer._qaCopy(labelCtx,{...labelOptions,selectedProvince:'p'}).provinceTargets;
assert.strictEqual(selected.length,1,'Selected province became unreachable');
assert.strictEqual(selected[0].anchor.x,anchor.x,'Selection relocated the canonical anchor');
const holdingOptions={...labelOptions,planetId:'planet',sites:[{planet_id:'planet',province_id:'p',name:'Forge'}]};
assert.strictEqual(renderer._qaCopy(labelCtx,holdingOptions).provinceTargets[0].label,'Forge','Terrain view hid a recorded settlement');
const edge=renderer._qaCopy(labelCtx,{...holdingOptions,panY:labelOptions.panY-412,safe:{left:0,right:1440,top:190,bottom:925}}).provinceTargets;
assert.strictEqual(edge[0].offscreenDirection,'north','Offscreen holding lost its clear direction');
geometry.province_anchors=[{province_id:'p',cell:null}];
assert.strictEqual(renderer.provinceLand(geometry).size,0,'Updated saved anchors did not invalidate the cache');
// Exact sea-level ocean and mixed shores must stay valid across both styles,
// including interpolation through the periodic longitude join.
const seaTerrain=Array(size).fill('o'),seaHeights=Array(size).fill(400);
for(let y=40;y<=45;y++)for(const x of [w-2,w-1,0,1]){seaTerrain[y*w+x]='c';seaHeights[y*w+x]=500;}
seaTerrain[30*w+100]='c';seaHeights[30*w+100]=401;
const seaDetail={...detail,terrain_grid:seaTerrain.join(''),elevation:seaHeights,rivers:[],province_anchors:[]};
for(const style of ['orbital','survey']){
  const seaRaster=renderer._qaFineRaster(seaDetail,geometry,style),pixels=seaRaster.pixels.data;
  for(let off=0;off<pixels.length;off+=4){
    assert.strictEqual(pixels[off+3],255,'Sea-level raster lost opacity');
    assert(Math.max(pixels[off],pixels[off+1],pixels[off+2])>12,`${style} exact-sea or mixed shore produced an opaque black block`);
  }
  const at=(x,y)=>{const off=(Math.floor((y+.5)*scale)*seaRaster.width+Math.floor((x+.5)*scale))*4;return Array.from(pixels.slice(off,off+3));};
  const ocean=at(500,200);
  assert(ocean[2]>ocean[0]&&ocean[1]>ocean[0],`${style} exact sea-level ocean became land`);
  const west=at(0,42),east=at(w-1,42);
  assert(west.every((v,i)=>Math.abs(v-east[i])<12),`${style} matched coastal samples split at the periodic seam`);
}
// Filter the lighting background, preserving a linear interior slope while
// suppressing quantization-scale alternation; wrap exactly at the cylinder seam.
const normalW=64,normalH=48,normalSize=normalW*normalH,
  linear=Array.from({length:normalSize},(_,i)=>500+(i%normalW)*3+Math.floor(i/normalW)*2),
  filtered=renderer._qaLighting(linear,[],normalW,normalH,false),
  center=24*normalW+32;
assert(Math.abs(filtered[center+1]-filtered[center-1]-6)<1e-8,'Filtering changed the interior linear longitude normal');
assert(Math.abs(filtered[center+normalW]-filtered[center-normalW]-4)<1e-8,'Filtering changed the interior linear latitude normal');
const noisy=Array.from({length:normalSize},(_,i)=>500+((i%normalW)%2?8:-8)),
  smooth=renderer._qaLighting(noisy,[],normalW,normalH,true);
assert(Math.abs(smooth[center+1]-smooth[center])<.05,'Fine quantization alternation survived the background lighting filter');
const wave=Array.from({length:normalSize},(_,i)=>500+20*Math.cos(2*Math.PI*(i%normalW+.5)/normalW)),
  periodic=renderer._qaLighting(wave,[],normalW,normalH,true);
assert(Math.abs(periodic[24*normalW]-periodic[25*normalW-1])<1e-9,'Lighting filter split equal periodic seam samples');
const smallCrater={x_q:8,y_q:24*16,radius_q:3*16,depth:80,rim_height:25},
  craterField=Array.from({length:normalSize},(_,i)=>{
    let x=(i%normalW)*16+8-smallCrater.x_q;x-=Math.round(x/(normalW*16))*normalW*16;
    return 500+renderer._qaProfile(Math.hypot(x,Math.floor(i/normalW)*16+8-smallCrater.y_q),smallCrater.radius_q,80,25);
  }),background=renderer._qaLighting(craterField,[smallCrater],normalW,normalH,true),
  craterNormals=renderer._qaCraterNormals([smallCrater],normalW,normalH,normalW,normalH,1,true);
assert(Array.from(background).every(v=>Math.abs(v-500)<1e-8),'Recorded crater profile leaked into the filtered background');
assert(Math.max(...craterNormals.dx)>20&&Math.min(...craterNormals.dx)<-20,'Small recorded crater lost separate directional normals');
assert(craterNormals.dx[24*normalW+normalW-1]!==0,'Crater normal failed to cross the periodic seam');
let overlayCall;
const orbit=renderer.buildOrbitTexture({geometry,detail,overlay:'resources',paintOverlay:(ctx,projection)=>{overlayCall=projection;}});
assert.strictEqual(orbit.width,raster.width,'Orbit texture changed the saved map resolution');
assert.strictEqual(orbit.layer,renderer._qaFineRaster(detail,geometry,'orbital',true),'Orbit texture did not copy its cached saved-map variant');
assert.strictEqual(renderer._qaFineRaster(detail,geometry,'orbital'),raster,'Orbit texture invalidated the strategic raster');
assert.strictEqual(overlayCall.tile,raster.width/geometry.planet.width,'Orbit overlay projection differs from the flat map');
assert.strictEqual(overlayCall.overlay,'resources','Orbit overlay mode was lost');
assert.notStrictEqual(orbit,raster,'Orbit painting can mutate the cached terrain raster');
// A saved gray ridge, a steep unlit face and an analytic crater exercise dry
// relief without adding cartographic features or lighting liquid materials.
const ridgeHeights=Array.from({length:size},(_,i)=>{const x=i%w;
  if(x>=200&&x<240)return 500+(x-200)*5;
  if(x>=240&&x<280)return 700-(x-240)*5;
  if(x>=600&&x<610)return 500+(x-600)*45;
  if(x>=610&&x<620)return 950-(x-610)*45;
  return 500;
});
const crater={id:'known-crater',x_q:800*16,y_q:400*16,radius_q:40*16,depth:120,rim_height:50};
for(let y=350;y<=450;y++)for(let x=750;x<=850;x++){
  const distance=Math.hypot((x+.5)*16-crater.x_q,(y+.5)*16-crater.y_q)/crater.radius_q;
  ridgeHeights[y*w+x]+=distance<=.75?-120*(1-(distance/.75)**2):distance<=1?50*(distance-.75)/.25:distance<=1.25?50*(1.25-distance)/.25:0;
}
const ridgeMaterials=Array(size).fill('0');
for(let y=0;y<12;y++)for(let x=208;x<272;x++)ridgeMaterials[y*w+x]='i';
for(let y=100;y<180;y++)for(let x=208;x<272;x++)ridgeMaterials[y*w+x]='i';
for(let y=300;y<380;y++)for(let x=208;x<272;x++)ridgeMaterials[y*w+x]='l';
const ridgeDetail={...detail,terrain_grid:'r'.repeat(size),elevation:ridgeHeights,materials:ridgeMaterials.join(''),rivers:[],craters:[crater]},
  ridgeGeometry={...geometry,surface:{...geometry.surface,hydrology:'none',sea_level:null,preset:'barren',geology:'cratered',lake_material:'lava',polar_caps:'water-ice'}};
for(const style of ['orbital','survey']){
  const ridge=renderer._qaFineRaster(ridgeDetail,ridgeGeometry,style),
    sample=(x,y,material=false)=>{const image=material?ridge.layer.pixels:ridge.pixels,
      off=(Math.floor((y+.5)*scale)*ridge.width+Math.floor((x+.5)*scale))*4;return Array.from(image.data.slice(off,off+3));},
    mean=rgb=>rgb.reduce((a,b)=>a+b)/3,
    patch=(x,y,material=false)=>[-2,0,2].flatMap(dx=>[-2,0,2].map(dy=>mean(sample(x+dx,y+dy,material)))).reduce((a,b)=>a+b)/9,
    flat=patch(100,240),lit=patch(220,240),shadow=patch(260,240),unlit=patch(615,240);
  assert(lit>flat*1.01&&shadow<flat*.99,`${style} saved gray slopes lost subtle directional relief`);
  assert(lit<flat*1.08&&shadow>flat*.92,`${style} background shading competed with material identity`);
  assert(unlit>flat*.9&&unlit<flat*1.2,`${style} background folds became dark liquid-like channels`);
  const craterLight=[780,800,820,840].map(x=>patch(x,400));
  assert(Math.max(...craterLight)-Math.min(...craterLight)>flat*.03,`${style} quiet background erased recorded crater form`);
  const beforeOrbit=pixelHash(ridge),globe=renderer.buildOrbitTexture({geometry:ridgeGeometry,detail:ridgeDetail,style}).layer,
    orbitSample=(x,y,material=false)=>{const image=material?globe.layer.pixels:globe.pixels,
      off=(Math.floor((y+.5)*scale)*globe.width+Math.floor((x+.5)*scale))*4;return Array.from(image.data.slice(off,off+3));};
  assert.strictEqual(pixelHash(ridge),beforeOrbit,`${style} orbit lighting changed strategic raster bytes`);
  assert.strictEqual(renderer._qaFineRaster(ridgeDetail,ridgeGeometry,style),ridge,`${style} orbit lighting displaced strategic raster cache`);
  assert(mean(sample(220,0))>mean(sample(260,0))+3,`${style} fixture lost its subtle polar chart light`);
  assert(Math.abs(mean(orbitSample(220,0))-mean(orbitSample(260,0)))<8,`${style} orbit pole retained baked directional terrain light`);
  assert(Math.abs(mean(orbitSample(220,h-1))-mean(orbitSample(260,h-1)))<8,`${style} south orbit pole retained baked directional light`);
  assert(orbitSample(220,0,true).every((v,i)=>Math.abs(v-orbitSample(260,0,true)[i])<2),`${style} orbit pole ice retained baked directional light`);
  const albedoFlat=orbitSample(100,240);
  for(const [x,y] of [[220,240],[260,240],[609,240],[615,240],[800,400],[840,400]])
    assert(orbitSample(x,y).every((v,i)=>Math.abs(v-albedoFlat[i])<8),`${style} orbit albedo retained slope, height or crater lighting`);
  assert(orbitSample(220,140,true).every((v,i)=>Math.abs(v-orbitSample(260,140,true)[i])<2),`${style} equatorial ice retained chart hillshade`);
  const orbitLava=orbitSample(220,340,true),orbitLavaOpposite=orbitSample(260,340,true);
  assert(orbitLava[0]>orbitLava[1]*1.5&&orbitLava[1]>orbitLava[2],`${style} orbital albedo lost its recorded lava material`);
  assert(orbitLava.every((v,i)=>Math.abs(v-orbitLavaOpposite[i])<7),`${style} orbital liquid albedo retained chart relief`);
  for(let off=3;off<globe.layer.pixels.data.length;off+=4)
    assert.strictEqual(globe.layer.pixels.data[off],ridge.layer.pixels.data[off],`${style} orbit lighting changed a recorded material boundary`);
  const iceLit=sample(220,140,true),iceShadow=sample(260,140,true);
  assert(Math.max(...iceLit)<251,`${style} ice highlights clipped saved relief`);
  assert(patch(220,140,true)>patch(260,140,true)+3,`${style} saved ice slope relief became featureless`);
  assert(mean(iceShadow)>shadow+20,`${style} polar ice became indistinguishable from gray rock`);
  const lavaLit=sample(220,340,true),lavaShadow=sample(260,340,true);
  assert(lavaLit.every((v,i)=>Math.abs(v-lavaShadow[i])<7),`${style} lava inherited terrain lighting`);
  assert(lavaLit[0]>lavaLit[1]*1.5&&lavaLit[1]>lavaLit[2],`${style} lava lost its recorded orange material`);
}
// Native frozen land also needs tonal headroom: it sits outside the separate
// polar mask on frozen worlds and previously saturated under Survey lighting.
const frozenDetail={...ridgeDetail},frozenGeometry={...ridgeGeometry,surface:{...ridgeGeometry.surface,preset:'frozen',lake_material:'hydrocarbon'}};
for(const style of ['orbital','survey']){
  const frozen=renderer._qaFineRaster(frozenDetail,frozenGeometry,style),
    prior=renderer._qaFineRaster(ridgeDetail,ridgeGeometry,style),
    sample=(x,y,material=false)=>{const pixels=material?frozen.layer.pixels.data:frozen.pixels.data,
      off=(Math.floor((y+.5)*scale)*frozen.width+Math.floor((x+.5)*scale))*4;return Array.from(pixels.slice(off,off+3));},
    mean=rgb=>rgb.reduce((a,b)=>a+b)/3,
    flat=sample(100,240),lit=sample(220,240),shadow=sample(260,240),
    iceLit=sample(220,140,true),iceShadow=sample(260,140,true);
  assert(flat[2]>flat[0]+12&&mean(flat)<205,`${style} native frozen ground lost blue-gray headroom`);
  const patch=(x,y)=>[-2,0,2].flatMap(dx=>[-2,0,2].map(dy=>mean(sample(x+dx,y+dy)))).reduce((a,b)=>a+b)/9,
    flatPatch=patch(100,240),litPatch=patch(220,240),shadowPatch=patch(260,240);
  assert(litPatch>flatPatch*1.01&&shadowPatch<flatPatch*.99,`${style} frozen subtle slopes ${JSON.stringify({flatPatch,litPatch,shadowPatch})}`);
  assert(litPatch<flatPatch*1.08&&shadowPatch>flatPatch*.92,`${style} frozen background overwhelmed material identity`);
  assert(mean(iceLit)>mean(iceShadow)+3,`${style} native polar ice lost subtle saved relief`);
  assert(Math.max(...iceLit)<245&&iceLit[2]>iceLit[0]+15,`${style} polar ice lost blue-gray highlight headroom`);
  for(let off=3;off<frozen.layer.pixels.data.length;off+=4){
    const px=((off-3)/4)%frozen.width,py=Math.floor((off-3)/4/frozen.width);
    // Hydrocarbon intentionally has a sharper opacity transition than lava.
    // Ice and every pixel outside that saved lake's half-cell margin stay exact.
    if(px>=(208-.5)*scale&&px<=(272+.5)*scale&&py>=(300-.5)*scale&&py<=(380+.5)*scale)continue;
    assert.strictEqual(frozen.layer.pixels.data[off],prior.layer.pixels.data[off],'Ice or unrelated material alpha changed');
  }
  for(const x of [207,208,270,271,272])for(const y of [299,300,378,379,380]){
    const off=(Math.floor((y+.5)*scale)*frozen.width+Math.floor((x+.5)*scale))*4+3;
    assert.strictEqual(frozen.layer.pixels.data[off]>127,ridgeMaterials[y*w+x]==='l','Hydrocarbon transition changed saved cell identity');
  }
}
console.log(JSON.stringify({result:'PASS',checks:'native1024 saved fields, bounded raster/cache, shared explicit courses, fine catalog/body boundaries/seam, fine picking and saved province anchors, supported river widths and honest province label visibility, exact-sea/mixed-shore colours in both styles and periodic join, filtered native dry background linear normals, quantization attenuation, analytic small crater/seam, orbit texture copy/overlay, quiet dry gray/ice background, separately legible recorded craters, material separation and flat lava fills, native frozen blue-gray headroom, exact ice/unrelated alpha and canonical liquid cell identity, globally unlit orbital albedo without height/slope/crater light and unchanged strategic bytes/material boundaries'}));
