// Verify derived lighting preserves saved geography and liquid surfaces.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
let source=fs.readFileSync('public/map-renderer.js','utf8').replace('    buildOrbitTexture,','    buildOrbitTexture,\n    _qaRelief:deriveOrbitReliefField,');
const sandbox={window:{},Uint8ClampedArray,document:{createElement(){const c={};c.getContext=()=>({createImageData:(w,h)=>({data:new Uint8ClampedArray(w*h*4)}),putImageData:d=>c.pixels=d});return c;}}};
vm.createContext(sandbox);vm.runInContext(source,sandbox);
const derive=sandbox.window.HWMapRenderer._qaRelief,w=64,h=40,size=w*h;
assert.strictEqual(typeof derive,'function');
const geometry={planet:{width:8,height:5},surface:{version:'planet-v11',preset:'continental',topology:'cylinder-x',hydrology:'ocean-draining',sea_level:400,geology:'none',lake_material:'none',polar_caps:'none'}};
function fixture(height=()=>600){return {version:'planet-detail-v2',width:w,height:h,terrain_grid:'p'.repeat(size),materials:'0'.repeat(size),elevation:Array.from({length:size},(_,i)=>height(i%w,Math.floor(i/w))),rivers:[],craters:[],feature_ids:[],feature_index:Array(size).fill(0),hydrography:{version:'hydrography-v2',features:[]}};}
function pixel(field,x,y){return [...field.data.slice((y*w+x)*4,(y*w+x)*4+2)];}
const flat=fixture(),savedFlat=JSON.stringify(flat),savedGeometry=JSON.stringify(geometry),f=derive(flat,geometry);
assert.strictEqual(f.width,w);assert.strictEqual(f.height,h);assert.strictEqual(f.data.length,size*4);
for(let i=0;i<size;i++)assert.deepStrictEqual([...f.data.slice(i*4,i*4+2)],[128,128],'Flat terrain acquired fictional relief');
assert.deepStrictEqual([...derive(flat,geometry).data],[...f.data],'Identical recorded detail produced different slopes');
const east=fixture(x=>600+Math.round(Math.sin(x/w*2*Math.PI)*90)),savedEast=JSON.stringify(east),e=derive(east,geometry);
assert(pixel(e,0,20)[0]<128,'Eastward uphill should tilt normal west');
assert(pixel(e,w/2,20)[0]>128,'Westward uphill should tilt normal east');
assert.strictEqual(pixel(e,w/4,20)[0],128,'Periodic crest has a spurious eastward tilt');
const dryGeometry={...geometry,surface:{...geometry.surface,preset:'barren',hydrology:'none',sea_level:null}};const steep=derive(fixture(x=>x<=20?0:x>=24?1000:(x-20)*250),geometry);const steepTilt=Math.atan(Math.hypot(...pixel(steep,22,20).map(v=>(v-128)/127)))*180/Math.PI;assert(steepTilt>24&&steepTilt<26,'The declared 25 degree cap was not preserved');
const north=fixture((x,y)=>500+y*5),n=derive(north,geometry);
assert(pixel(n,32,20)[1]>128,'Southward uphill should tilt normal north');
let max=0;for(let i=0;i<size;i++)max=Math.max(max,Math.hypot((e.data[i*4]-128)/127,(e.data[i*4+1]-128)/127));
assert(max<=Math.tan(Math.PI/6)+.02,'Cartographic tilt exceeded 30 degrees');
assert(Math.abs(pixel(e,0,0)[0]-128)<=Math.abs(pixel(e,0,20)[0]-128),'Polar tilt was amplified');
const liquids=fixture(),chars=[...liquids.terrain_grid],materials=[...liquids.materials];
for(let y=0;y<h;y++)for(let x=32;x<w;x++){const i=y*w+x;liquids.elevation[i]=50;chars[i]='o';}
for(const [x,c]of [[10,'w'],[16,'h'],[22,'l']])for(let y=0;y<h;y++){materials[y*w+x]=c;liquids.elevation[y*w+x]=40;}
liquids.terrain_grid=chars.join('');liquids.materials=materials.join('');const savedLiquids=JSON.stringify(liquids),l=derive(liquids,geometry);
for(let y=0;y<h;y++)for(let x=0;x<w;x++)if(chars[y*w+x]==='o'||'whl'.includes(materials[y*w+x]))assert.deepStrictEqual(pixel(l,x,y),[128,128],'Liquid acquired terrain relief');
for(const x of [9,11,15,17,21,23,31,0])assert.deepStrictEqual(pixel(l,x,20),[128,128],'Liquid neighbour manufactured a land cliff');
const dryLiquids=derive(liquids,dryGeometry);for(const x of [9,11,15,17,21,23,31,0])assert.deepStrictEqual(pixel(dryLiquids,x,20),[128,128],'Dry lighting filter leaked liquid height into land cliffs');
assert.strictEqual(JSON.stringify(flat),savedFlat);assert.strictEqual(JSON.stringify(east),savedEast);assert.strictEqual(JSON.stringify(liquids),savedLiquids);assert.strictEqual(JSON.stringify(geometry),savedGeometry);
console.log(JSON.stringify({result:'PASS',checks:'Bounded deterministic signed slopes, exact neutral flat/liquid cells, wet-neighbour exclusion, periodic derivative and orientation, tilt cap, polar taper and immutable inputs',maxTiltDegrees:Math.atan(max)*180/Math.PI}));
