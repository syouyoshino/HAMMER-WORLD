// Crossing ink follows recorded elevations and keeps cylindrical topology.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
let source=fs.readFileSync('public/map-renderer.js','utf8').replace('    buildOrbitTexture,','    buildOrbitTexture,\n    _qaShore:nativeShoreCrossings,');
const context={window:{}};vm.createContext(context);vm.runInContext(source,context);const crossings=context.window.HWMapRenderer._qaShore;
const make=elevation=>({elevation,sea_level:400});
assert.strictEqual(crossings(make([600,600,600,600]),2,2,false).length,0);
assert.strictEqual(crossings(make([400,400,400,400]),2,2,false).length,0,'Exact sea created a fictional island');
const s=make([600,200,600,200]),before=JSON.stringify(s),a=crossings(s,2,2,false);
assert.strictEqual(a.length,1);assert.deepStrictEqual(JSON.parse(JSON.stringify(a[0])),[[1,.5],[1,1.5]]);
const seam=crossings(s,2,2,true);assert.strictEqual(seam.length,2);assert(seam[1].every(p=>p[0]===2),'Periodic join lost its recorded crossing');
const exact=crossings(make([600,400,600,400]),2,2,false);assert(exact[0].every(p=>p[0]===1.5),'Sea endpoint was silently relocated');
assert.strictEqual(JSON.stringify(s),before,'Derived shore ink changed recorded heights');
console.log('Recorded shore crossings, exact-sea identity, periodic join and immutable inputs passed');
