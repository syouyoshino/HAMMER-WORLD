// Verify spherical projection, inverse picking and bounded texture sizing.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const sandbox={window:{devicePixelRatio:1},document:{createElement:()=>({getContext:()=>null})}};
vm.createContext(sandbox);vm.runInContext(fs.readFileSync('public/planet-orbit.js','utf8'),sandbox);
const orbit=sandbox.window.HWPlanetOrbit,rect={left:0,top:0,width:1200,height:800},view={latitude:.23,longitude:Math.PI-.03,distance:2.45};
const near=(a,b,tol=1e-8)=>assert(Math.abs(a-b)<tol,`${a} differs from ${b}`);
for(const point of [[.1,Math.PI-.04],[-.2,-Math.PI+.02],[.6,Math.PI+.1],[-.8,Math.PI-.12],[0,Math.PI]]){
  const projected=orbit.screenPoint(...point,view,rect);assert(projected,'front hemisphere point was culled');
  const back=orbit.inversePoint(projected.x,projected.y,view,rect);assert(back,'projected surface point did not pick');
  near(back.latitude,point[0]);near(Math.atan2(Math.sin(back.longitude-point[1]),Math.cos(back.longitude-point[1])),0);
}
assert.strictEqual(orbit.screenPoint(0,0,view,rect),null,'back hemisphere point was projected');
assert.strictEqual(orbit.inversePoint(0,0,view,rect),null,'outside background produced a surface coordinate');
const polarView={...view,latitude:1.35},pole=orbit.screenPoint(Math.PI/2,polarView.longitude,polarView,rect);assert(pole,'visible north pole was culled');
const poleBack=orbit.inversePoint(pole.x,pole.y,polarView,rect);near(poleBack.latitude,Math.PI/2,1e-7);
const seamA=orbit.screenPoint(0,Math.PI-.001,view,rect),seamB=orbit.screenPoint(0,-Math.PI+.001,view,rect);
assert(seamA&&seamB,'wrapped longitude seam lost a visible point');
const fit=orbit.focusFlatCamera(1200,800,128,80,64,40);assert(fit.tile>0&&Number.isFinite(fit.panX)&&Number.isFinite(fit.panY));
for(const [w,h] of [[1024,640],[8192,4096],[100000,30000]]){const size=orbit.powerOfTwoSize(w,h);assert(size.width<=2048&&size.height<=2048&&size.width*size.height<=2_097_152);assert((size.width&(size.width-1))===0&&(size.height&(size.height-1))===0);}
assert.strictEqual(orbit.create({getContext:()=>null}),null,'missing WebGL did not report flat-renderer fallback');
console.log('orbit projection, inverse picking, seam, poles, occlusion and resource bounds passed');

// HUD-safe viewports use the same offset projection for navigation and drawing.
const inset={left:35,top:180,width:1130,height:560};
for(const coordinates of [[.23,Math.PI-.03],[.5,2.8]]){
 const projected=orbit.screenPoint(...coordinates,view,inset);
 const picked=orbit.inversePoint(projected.x,projected.y,view,inset);
 near(picked.latitude,coordinates[0],1e-7);
 near(Math.atan2(Math.sin(picked.longitude-coordinates[1]),Math.cos(picked.longitude-coordinates[1])),0,1e-7);
}

// Enter the strategic view at its native 12 CSS pixels per fine sample limit.
for(const viewport of [rect,inset,{left:0,top:190.5,width:1440,height:735}]){
 const rows=80,cols=128,fineWidth=1024,maxTile=12*fineWidth/cols;
 const distance=orbit.distanceForTile(viewport,rows,maxTile);
 const endpoint=orbit.focusFlatCamera(viewport.width,viewport.height,cols,rows,64,40,distance);
 near(endpoint.tile,maxTile,1e-8);
 const epsilon=1e-6,centerView={latitude:0,longitude:0,distance};
 const north=orbit.screenPoint(epsilon,0,centerView,viewport),south=orbit.screenPoint(-epsilon,0,centerView,viewport);
 near((south.y-north.y)/(2*epsilon)*Math.PI/rows,maxTile,1e-5);
}

// Unique pole rows use linear-light means and ignore RGB of transparent pixels.
const averaged=orbit.rowMeans(new Uint8ClampedArray([0,0,0,255,255,255,255,255,255,0,0,0,0,255,0,255]),2,2);
assert(averaged[0]>180&&averaged[0]<190,'pole mean averaged gamma-encoded bytes');
assert.strictEqual(averaged[4],0);assert.strictEqual(averaged[5],255);assert.strictEqual(averaged[7],128);
