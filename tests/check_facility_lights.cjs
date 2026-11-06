const assert=require('node:assert/strict');
const lights=require('../public/facility-lights.js');
const geometry={planet:{id:'p',width:128,height:80}};
const sites=[{id:'a',planet_id:'p',province_id:'pa',owned:true},{id:'b',planet_id:'p',province_id:'pb',owned:false},{id:'c',planet_id:'other',province_id:'pc',owned:true}];
const land=new Map([['pa',{anchor:{x:10,y:12}}],['pb',{anchor:{x:30,y:12}}],['pc',{anchor:{x:40,y:12}}]]);
const facilities=[{id:'f2',settlement_id:'a',kind:'factory',completed:true,active_turn:2},{id:'f1',settlement_id:'a',kind:'depot',completed:true,active_turn:0},{id:'future',settlement_id:'a',kind:'refinery',completed:true,active_turn:4},{id:'incomplete',settlement_id:'a',kind:'factory',completed:false,active_turn:0},{id:'unknown',settlement_id:'a',kind:'factory',completed:true},{id:'enemy',settlement_id:'b',kind:'factory',completed:true,active_turn:0},{id:'other',settlement_id:'c',kind:'factory',completed:true,active_turn:0}];
const before=JSON.stringify({geometry,sites,facilities});
const model=t=>lights.model({geometry,settlements:sites,facilities,turn:t,provinceLand:land});
assert.deepEqual(model(3).map(f=>f.id),['f1','f2']);assert.deepEqual(model(0).map(f=>f.id),['f1']);assert.deepEqual(model(3),lights.model({geometry,settlements:[...sites].reverse(),facilities:[...facilities].reverse(),turn:3,provinceLand:land}));
assert.equal(JSON.stringify({geometry,sites,facilities}),before);
assert.deepEqual(lights.model({geometry,settlements:sites,facilities,turn:3,provinceLand:new Map([['pa',{anchor:{x:NaN,y:12}}]])}),[]);
assert.deepEqual(lights.model({geometry,settlements:sites,facilities,turn:3,provinceLand:new Map([['pa',{anchor:{x:129,y:12}}]])}),[],'Out of bounds anchor cannot create lights');
assert.deepEqual(lights.model({geometry,settlements:sites,facilities,turn:null,provinceLand:land}),[]);
const geometryAlias={planet:{...geometry.planet,id:'geometry-id'}};
assert.deepEqual(lights.model({geometry:geometryAlias,planetId:'p',settlements:sites,facilities,turn:3,provinceLand:land}).map(f=>f.id),['f1','f2'],'Public planet identity must remain distinct from internal terrain ID');
assert.equal(geometryAlias.planet.id,'geometry-id');
const grid=lights.pattern('factory');assert.deepEqual(grid,lights.pattern('factory'));assert.notDeepEqual(grid,lights.pattern('depot'));
assert.deepEqual(model(-1),[]);
const sandbox={window:{}};require('node:vm').runInNewContext(require('node:fs').readFileSync('public/planet-orbit.js','utf8'),sandbox);const orbit=sandbox.window.HWPlanetOrbit;
for(const descent of [1.01,1.12,1.4]){
  assert.equal(orbit.nightReadability(descent,descent),1);
  assert.equal(orbit.nightReadability(2.45,descent),0);
  assert(orbit.nightReadability(1.75,descent)>=.25,'Useful Orbit distance receives analytical night detail');
  let previous=0;
  for(let step=40;step>=0;step--){const lift=orbit.nightReadability(descent+(2.45-descent)*step/40,descent);assert(lift>=previous-1e-12&&lift>=0&&lift<=1);previous=lift;}
}
assert.equal(orbit.nightReadability(NaN,1.1),0);
function painted(records){
  const commands=[],ctx={createRadialGradient:()=>({addColorStop(){}}),beginPath(){},fill(){},stroke(){}};
  for(const method of ['arc','fillRect','moveTo','lineTo'])ctx[method]=(...args)=>commands.push([method,...args]);
  lights.paint(ctx,128,80,records,128,80);return commands;
}
const site=model(3),paintedSite=painted(site);
assert.deepEqual(painted([...site].reverse()),paintedSite,'Input order must not change site glyph slots');
assert.deepEqual(painted([...site,{...site[0],id:'unrelated',x:100,y:40}]).filter(c=>c[1]<64),paintedSite,'Another anchor must not move this site');
assert(painted([{...site[0],x:.1}]).some(c=>c[1]>128),'Site support must repeat across longitude seam');
assert.equal(JSON.stringify({geometry,sites,facilities}),before);
console.log('Owned active facility filtering, immutable stable patterns, historical turn and anchor checks passed');
