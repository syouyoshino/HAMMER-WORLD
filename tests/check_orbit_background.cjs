const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
let canvasCount=0,uploadCount=0;
global.window = {document:{createElement(type){
  assert.equal(type,'canvas');canvasCount++;
  const canvas={width:0,height:0};
  canvas.getContext=()=>({
    createImageData(width,height){return {width,height,data:new Uint8ClampedArray(width*height*4)};},
    putImageData(pixels){canvas.pixels=pixels;uploadCount++;}
  });
  return canvas;
}}};
for (const file of ['public/planet-orbit.js', 'public/orbit-background.js']) {
  vm.runInThisContext(fs.readFileSync(file, 'utf8'), { filename: file });
}
const { basis } = window.HWPlanetOrbit;
const { projectDirection } = window.HWOrbitBackground;
const rect = { left: 0, top: 190, width: 1440, height: 735 };
const view = { latitude: .31, longitude: -1.42, distance: 2.45 };
const frame = basis(view.latitude, view.longitude);
const direction = frame.N.map((n, i) => -n + .3 * frame.E[i] + .2 * frame.U[i]);
const norm = Math.hypot(...direction);
const unit = direction.map(n => n / norm);
const point = projectDirection(unit, view, rect);
assert(point.x > rect.width / 2 && point.y < rect.top + rect.height / 2);
assert.equal(projectDirection(frame.N, view, rect), null, 'Behind-camera stars must be rejected');
for (const latitude of [-Math.PI / 2, -.9, 0, .9, Math.PI / 2]) {
  const pose = { ...view, latitude };
  const forward = basis(latitude, view.longitude).N.map(n => -n);
  const a = projectDirection(forward, pose, rect);
  assert(Number.isFinite(a.x) && Number.isFinite(a.y));
  assert(Math.abs(a.x - rect.width / 2) < 1e-8);
  assert(Math.abs(a.y - rect.top - rect.height / 2) < 1e-8);
  const b = projectDirection(forward, { ...pose, longitude: pose.longitude + 2 * Math.PI }, rect);
  assert(Math.hypot(a.x - b.x, a.y - b.y) < 1e-7, 'Full orbit must return the same sky');
}
const seam = { ...view, longitude: Math.PI - 1e-7 };
const forward = basis(seam.latitude, seam.longitude).N.map(n => -n);
const left = projectDirection(forward, seam, rect);
const right = projectDirection(forward, { ...seam, longitude: -Math.PI + 1e-7 }, rect);
assert(Math.hypot(left.x - right.x, left.y - right.y) < .001, 'Sky must not jump at longitude seam');
const moved = projectDirection(unit, { ...view, longitude: view.longitude + .1 }, rect);
assert(Math.hypot(point.x - moved.x, point.y - moved.y) > 1);
const zoomed = projectDirection(unit, { ...view, distance: 1.7 }, rect);
assert(Math.hypot(point.x - zoomed.x, point.y - zoomed.y) > .1, 'Zoom response must be perceptible');
assert.deepEqual(projectDirection(unit, view, rect), point, 'Projection cannot depend on elapsed time');
console.log('Sky orientation, poles, seam continuity, zoom response and deterministic return passed');

// Exercise actual ray sampling through a bounded fake canvas, without a test API.
function capture(pose) {
  const operations=[];
  const ctx=new Proxy({}, {
    get(_,name) {
      if(name==='drawImage')return (canvas,...args)=>{
        assert(canvas.width<=128&&canvas.height<=128, 'Scratch bitmap must stay bounded');
        const pixels=Array.from(canvas.pixels.data);
        assert(pixels.some((v,i)=>i%4===0&&v>10), 'Sky must contain visible clouds');
        assert(pixels.every((v,i)=>i%4!==3||v===255), 'Sky bitmap must be opaque');
        operations.push(['bitmap',pixels],['drawImage',...args]);
      };
      return (...args)=>{assert(args.every(v=>typeof v!=='number'||Number.isFinite(v)));operations.push([name,...args]);};
    },
    set(_,name,value){operations.push([name,value]);return true;}
  });
  window.HWOrbitBackground.draw(ctx,1440,1024,pose,rect);
  assert(operations.some(op=>op[0]==='bitmap'));
  return operations;
}
function near(a,b) {
  assert.equal(a.length,b.length);
  for(let i=0;i<a.length;i++) {
    if(Array.isArray(a[i]))near(a[i],b[i]);
    else if(typeof a[i]==='number')assert(Math.abs(a[i]-b[i])<1e-6);
    else assert.equal(a[i],b[i]);
  }
}
for(const latitude of [-Math.PI/2,-.9,0,.9,Math.PI/2]) {
  const pose={...view,latitude};
  const drawn=capture(pose),uploads=uploadCount;
  assert.deepEqual(capture(pose),drawn, 'Drawing must be deterministic');
  assert.equal(uploadCount,uploads, 'Unchanged pose must reuse its bitmap');
  near(drawn,capture({...pose,longitude:pose.longitude+2*Math.PI}));
  capture({...pose,longitude:pose.longitude+.2});
  assert.deepEqual(capture(pose),drawn, 'Returning to a pose must reconstruct identical pixels');
}
near(capture({...view,longitude:Math.PI-1e-12}),capture({...view,longitude:-Math.PI+1e-12}));
assert.equal(canvasCount,1, 'Only one scratch bitmap may be retained');
console.log('Actual sky pixels: bounded canvas, visible clouds, cache, deterministic return, poles and yaw seam passed');
