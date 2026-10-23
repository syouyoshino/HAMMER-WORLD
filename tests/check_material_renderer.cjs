// Exercise saved-mask interpolation through the actual raster without DOM exports.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
let source=fs.readFileSync('public/map-renderer.js','utf8');
source=source.replace('    wrapsX,','    _qaRaster: baseRaster,\n    _qaInterior: lakeInterior,\n    _qaShore: riverShorePoints,\n    _qaLabels: drawPlanetCopy,\n    wrapsX,');
const canvases=[];
const sandbox={window:{},document:{createElement:()=>{
 const canvas={};
 const context={createImageData:(w,h)=>({width:w,height:h,data:new Uint8ClampedArray(w*h*4)}),
   putImageData:image=>canvas.pixels=image,drawImage:layer=>canvas.layer=layer};
 canvas.getContext=()=>context;canvases.push(canvas);return canvas;
}}};
vm.createContext(sandbox);vm.runInContext(source,sandbox);
const renderer=sandbox.window.HWMapRenderer,cols=128,rows=80,size=cols*rows,scale=12,w=cols*scale;
function fixture(lake){
 return {planet:{width:cols,height:rows},tiles:Array.from({length:size},(_,i)=>({x:i%cols,y:Math.floor(i/cols),terrain:'rock'})),
  surface:{version:'planet-v8',topology:'cylinder-x',preset:'barren',geology:'none',craters:[],hydrology:'none',sea_level:null,
   elevation:Array.from({length:size},(_,i)=>450+(i%cols)*3),moisture:Array(size).fill(0),temperature:Array(size).fill(500),rivers:[],
   materials:{lake_material:lake,polar_caps:'water-ice',
    lake_mask:Array.from({length:size},(_,i)=>i%cols===0&&i/cols>=35&&i/cols<45?'1':'0').join(''),
    ice_mask:Array.from({length:size},(_,i)=>Math.floor(i/cols)<8||Math.floor(i/cols)>=72?'1':'0').join('')}}};
}
function pixel(img,x,y){return Array.from(img.data.slice((y*img.width+x)*4,(y*img.width+x)*4+4));}
const geo=fixture('water'),raster=renderer._qaRaster(geo,'orbital'),layer=raster.layer.pixels;
assert(renderer.wrapsX(geo),'V8 must retain cylindrical topology');
assert.strictEqual(renderer._qaRaster(geo,'orbital'),raster,'Raster cache lost');
assert.strictEqual(pixel(layer,6,40*scale+6)[3],255,'Saved lake cell centre lost');
assert(pixel(layer,w-1,40*scale+6)[3]>0,'Mask failed to interpolate across longitude seam');
assert.strictEqual(pixel(layer,w-7,40*scale+6)[3],0,'Outside saved mask grew an extra feature');
assert.strictEqual(pixel(layer,500,0)[3],255,'Polar ice is not solid at pole');
assert.strictEqual(pixel(layer,500,40*scale)[3],0,'Unmarked interior acquired a material');
const ice=pixel(layer,500,0);assert(ice[0]>180&&ice[1]>180&&ice[2]>180,'Ice lost pale relief colour');
const water=pixel(layer,6,40*scale+6);assert(water[2]>water[0]&&water[1]>water[0],'Water lake lost blue appearance');
const lava=fixture('lava');lava.surface.materials.polar_caps='none';lava.surface.materials.ice_mask='0'.repeat(size);
const lavaLayer=renderer._qaRaster(lava,'orbital').layer.pixels;
const orange=pixel(lavaLayer,6,40*scale+6);assert(orange[0]>orange[1]*1.5&&orange[1]>orange[2],'Lava lost restrained orange appearance');
const steep=fixture('lava');steep.surface.materials.polar_caps='none';steep.surface.materials.ice_mask='0'.repeat(size);
steep.surface.elevation=Array(size).fill(450);
for(let y=0;y<rows;y++){steep.surface.elevation[y*cols+1]=900;steep.surface.elevation[y*cols+127]=100;}
const steepPixel=pixel(renderer._qaRaster(steep,'orbital').layer.pixels,6,40*scale+6);
assert(orange.slice(0,3).every((v,i)=>Math.abs(v-steepPixel[i])<=3),'Liquid inherited adjacent terrain hillshade');
const first=pixel(lavaLayer,6,37*scale+6),last=pixel(lavaLayer,6,42*scale+6);
assert(first.slice(0,3).every((v,i)=>Math.abs(v-last[i])<8),'Liquid body acquired strong terrain hillshade');
assert.notDeepStrictEqual(first,last,'Liquid interior lost restrained existing grain');
// Recorded sea crossing truncates a terminal ocean segment at the actual
// height interpolation, also for an outlet crossing the cylindrical seam.
const shoreSurface={sea_level:400,elevation:Array(size).fill(500)};
shoreSurface.elevation[10*cols+2]=300;
assert.deepStrictEqual(Array.from(renderer._qaShore(shoreSurface,[[1,10],[2,10]],cols,true).at(-1)),[1.5,10]);
shoreSurface.elevation[10*cols]=300;
assert.deepStrictEqual(Array.from(renderer._qaShore(shoreSurface,[[127,10],[0,10]],cols,true).at(-1)),[127.5,10]);
const ctx={measureText:text=>({width:text.length*7}),beginPath(){},rect(){},fill(){},stroke(){},
 save(){},restore(){},clip(){},closePath(){},moveTo(){},lineTo(){},fillRect(){},strokeRect(){},fillText(){}};
const labelGeo=fixture('water');labelGeo.provinces=[{id:'p',name:'Province 01'}];
for(const tile of labelGeo.tiles)tile.province_id=tile.x<16&&tile.y<16?'p':null;
const options={geometry:labelGeo,w:1440,h:1024,zoom:2,panX:1271.25,panY:0,style:'orbital',
 safe:{left:0,top:190,right:1440,bottom:925},sites:[{name:'Forge',planet_id:'planet',province_id:'p'}],planetId:'planet',renderPhase:'labels'};
const baseY=(1024-80*22.5)/2+7.5*22.5;
let labels=renderer._qaLabels(ctx,{...options,panY:100-baseY});
assert.strictEqual(labels.provinceTargets.length,1,'Offscreen holding lost its reachable edge label');
assert.strictEqual(labels.provinceTargets[0].offscreenDirection,'north','Hidden holding lost its explicit north indicator');
assert(labels.provinceTargets[0].top>=190,'Offscreen label target intrudes into UI bars');
labels=renderer._qaLabels(ctx,{...options,panY:250-baseY});
assert.strictEqual(labels.provinceTargets.length,1,'Visible holding lost its reachable label');
assert(labels.provinceTargets[0].top>=190,'Holding label hit target intrudes into UI bars');
console.log(JSON.stringify({result:'PASS',checks:'V8 cached saved masks preserve cell centres, seam interpolation, solid pale poles, blue water, textured flat lava, recorded river shore crossings and visible holding anchors'}));
