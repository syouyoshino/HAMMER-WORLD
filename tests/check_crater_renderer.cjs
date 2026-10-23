// Observe private helpers in an isolated VM; production exports stay unchanged.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
let src=fs.readFileSync('public/map-renderer.js','utf8');
assert(src.includes('    wrapsX,'));
src=src.replace('    wrapsX,','    _qaResidual: craterResidualRaster,\n    _qaRaster: baseRaster,\n    wrapsX,');
assert(src.includes('if(!onLand) {'));
src=src.replace('if(!onLand) {','if(!onLand) { window._qaOceanPixels++;');
const sandbox={window:{_qaOceanPixels:0},document:{createElement:()=>({getContext:()=>({
 createImageData:(w,h)=>({data:new Uint8ClampedArray(w*h*4)}),putImageData:()=>{}
})})}};
vm.createContext(sandbox);vm.runInContext(src,sandbox);
const cols=128,rows=80,scale=11,w=cols*scale,h=rows*scale;
const vertical=y=>{const f=Math.max(0,Math.min(rows-1,y-.5)),i=Math.floor(f);return[i*w,Math.min(rows-1,i+1)*w,f-i];};
const interpolate=field=>{
 const result=new Float64Array(w*rows);
 for(let px=0;px<w;px++){
  const raw=(px+.5)/scale-.5,f=((raw%cols)+cols)%cols,i=Math.floor(f),t=f-i;
  for(let y=0;y<rows;y++)result[y*w+px]=field[y*cols+i]*(1-t)+field[y*cols+(i+1)%cols]*t;
 }
 return result;
};
let maxError=0;
for(const center of [4,1024,2044]){
 const surface={craters:[{id:'seam-fixture',x_q:center,y_q:648,radius_q:160,depth:120,rim_height:60}]};
 const residual=sandbox.window.HWMapRenderer._qaResidual(surface,cols,rows,w,h,scale,interpolate,vertical,true);
 for(let y=0;y<rows;y++)for(let x=0;x<cols;x++){
  const value=Math.abs(residual[(y*scale+5)*w+x*scale+5]);maxError=Math.max(maxError,value);
  assert(value<.00002,`Canonical sample changed at ${x},${y}; center ${center}: ${value}`);
 }
}
// Dry lowlands remain land even if subcell relief falls below the old sea datum.
const size=cols*rows,geometry={planet:{width:cols,height:rows},
 tiles:Array.from({length:size},(_,i)=>({x:i%cols,y:Math.floor(i/cols),terrain:'rock'})),
 surface:{version:'planet-v7',topology:'cylinder-x',preset:'barren',geology:'cratered',
  hydrology:'none',sea_level:null,elevation:Array(size).fill(401),
  moisture:Array(size).fill(0),temperature:Array(size).fill(500),rivers:[],
  craters:[{id:'dry-lowland',x_q:1024,y_q:648,radius_q:160,depth:120,rim_height:60}]}};
sandbox.window.HWMapRenderer._qaRaster(geometry,'orbital');
assert.strictEqual(sandbox.window._qaOceanPixels,0,'Waterless terrain entered ocean rendering');
console.log(JSON.stringify({result:'PASS',checks:'Canonical samples and both seams preserved; dry lowlands never render as ocean',max_error:maxError}));
