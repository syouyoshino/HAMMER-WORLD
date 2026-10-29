(() => {
  "use strict";
  const root=typeof window==='undefined'?globalThis:window,TAU=Math.PI*2;
  const clamp=(v,lo,hi)=>Math.max(lo,Math.min(hi,v));
  const dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
  function hash(n){const x=Math.sin(n*127.1+311.7)*43758.5453;return x-Math.floor(x);}
  function direction(y,lon){const r=Math.sqrt(1-y*y);return [r*Math.sin(lon),y,r*Math.cos(lon)];}
  // Fixed world directions: camera rotation changes the field without reseeding it.
  const starTints=[[190,207,219],[171,194,211],[211,201,181],[199,207,210]];
  const stars=Array.from({length:220},(_,i)=>{
    const tint=starTints[Math.floor(hash(i+1301)*starTints.length)],rank=hash(i+701);
    const bright=rank>.975,clear=rank>.88;
    return {direction:direction(2*hash(i+1)-1,TAU*hash(i+211)),radius:bright?1.18:clear?.75:.3+hash(i+431)*.36,color:`rgba(${tint.join(',')},${(bright?.86:clear?.5:.12+rank*.19).toFixed(3)})`};
  });
  // Public decorative noise, unrelated to campaign generation. Cartesian samples
  // stay continuous through yaw seams and poles without a latitude texture seam.
  const lattice=Uint8Array.from({length:32768},(_,i)=>Math.floor(hash(i+1901)*256));
  const smooth=t=>t*t*(3-2*t),mix=(a,b,t)=>a+(b-a)*t;
  const ramp=(a,b,v)=>smooth(clamp((v-a)/(b-a),0,1));
  function noise(x,y,z){
    const ix=Math.floor(x),iy=Math.floor(y),iz=Math.floor(z);
    const u=smooth(x-ix),v=smooth(y-iy),w=smooth(z-iz);
    const x0=ix&31,x1=(ix+1)&31,y0=(iy&31)*32,y1=((iy+1)&31)*32,z0=(iz&31)*1024,z1=((iz+1)&31)*1024;
    return mix(mix(mix(lattice[x0+y0+z0],lattice[x1+y0+z0],u),mix(lattice[x0+y1+z0],lattice[x1+y1+z0],u),v),mix(mix(lattice[x0+y0+z1],lattice[x1+y0+z1],u),mix(lattice[x0+y1+z1],lattice[x1+y1+z1],u),v),w)/255;
  }
  // One bounded scratch bitmap and its last pose; never retain app composites.
  let skyCanvas,skyContext,skyPixels,lastSkyKey;
  function drawHaze(ctx,w,h,p){
    if(!root.document||w<=0||h<=0)return;
    if(!skyCanvas){skyCanvas=root.document.createElement('canvas');skyContext=skyCanvas.getContext('2d');}
    if(!skyContext)return;
    const width=Math.max(1,Math.round(128*w/Math.max(w,h))),height=Math.max(1,Math.round(128*h/Math.max(w,h)));
    const key=[w,h,p.cx,p.cy,p.scale,...p.frame.N,...p.frame.E,...p.frame.U].join(',');
    if(key!==lastSkyKey){
      if(skyCanvas.width!==width||skyCanvas.height!==height){
        skyCanvas.width=width;skyCanvas.height=height;skyPixels=skyContext.createImageData(width,height);
      }
      const pixels=skyPixels.data,{E,U,N}=p.frame;
      for(let y=0;y<height;y++){
        const v=(p.cy-(y+.5)*h/height)/p.scale;
        for(let x=0;x<width;x++){
          const u=((x+.5)*w/width-p.cx)/p.scale;
          let dx=E[0]*u+U[0]*v-N[0],dy=E[1]*u+U[1]*v-N[1],dz=E[2]*u+U[2]*v-N[2];
          const length=Math.hypot(dx,dy,dz);dx/=length;dy/=length;dz/=length;
          const field=.52*noise(dx*1.6+7.1,dy*1.6+13.2,dz*1.6+4.7)+.27*noise(dx*3.2+7.1,dy*3.2+13.2,dz*3.2+4.7)+.14*noise(dx*6.4+7.1,dy*6.4+13.2,dz*6.4+4.7)+.07*noise(dx*12.8+7.1,dy*12.8+13.2,dz*12.8+4.7);
          const support=ramp(.36,.64,noise(dx*1.1+18.3,dy*1.1+5.7,dz*1.1+23.1));
          const occlusion=ramp(.48,.68,noise(dx*4.5+2.8,dy*4.5+21.4,dz*4.5+11.6));
          const light=support*ramp(.43,.65,field)*(1-.65*occlusion),i=(y*width+x)*4;
          pixels[i]=7+32*light;pixels[i+1]=11+40*light;pixels[i+2]=16+48*light;pixels[i+3]=255;
        }
      }
      skyContext.putImageData(skyPixels,0,0);lastSkyKey=key;
    }
    ctx.imageSmoothingEnabled=true;ctx.drawImage(skyCanvas,0,0,w,h);
  }
  function projection(view,rect,frame){return {frame,cx:rect.left+rect.width/2,cy:rect.top+rect.height/2,scale:Math.min(rect.width,rect.height)*.48*(1+.12*clamp((2.45-(view.distance??2.45))/1.45,-1,1))};}
  function project(direction,p,minDepth=.16){
    const depth=-dot(direction,p.frame.N);if(depth<=minDepth)return null;
    return {x:p.cx+p.scale*dot(direction,p.frame.E)/depth,y:p.cy-p.scale*dot(direction,p.frame.U)/depth,depth};
  }
  function projectDirection(direction,view,rect){
    const frame=root.HWPlanetOrbit?.basis(view.latitude,view.longitude);
    return frame?project(direction,projection(view,rect,frame)):null;
  }
  function drawRecordedStar(ctx,star,p,view,rect,w,h){
    if(!star?.direction)return null;
    const point=root.HWPlanetOrbit?.projectRecordedStar(star,view,rect);
    if(!point||point.x<0||point.x>w||point.y<0||point.y>h)return null;
    const orbit=root.HWPlanetOrbit;
    if(orbit?.inversePoint&&orbit.inversePoint(point.x,point.y,view,rect))return null;
    const x=point.x,y=point.y;
    ctx.save();
    const halo=ctx.createRadialGradient?ctx.createRadialGradient(x,y,2,x,y,24):null;
    if(halo){halo.addColorStop(0,'rgba(255,204,131,.32)');halo.addColorStop(.34,'rgba(255,174,91,.12)');halo.addColorStop(1,'rgba(255,174,91,0)');ctx.fillStyle=halo;ctx.beginPath();ctx.arc(x,y,24,0,TAU);ctx.fill();}
    ctx.fillStyle='rgba(255,198,121,.28)';ctx.beginPath();ctx.arc(x,y,7,0,TAU);ctx.fill();
    ctx.fillStyle='#ffd59a';ctx.beginPath();ctx.arc(x,y,3.2,0,TAU);ctx.fill();
    ctx.restore();
    return point;
  }
  function draw(ctx,w,h,view,rect={left:0,top:0,width:w,height:h},star=null){
    ctx.save();ctx.fillStyle="#070b10";ctx.fillRect(0,0,w,h);
    const frame=root.HWPlanetOrbit?.basis(view.latitude,view.longitude);
    if(!frame){ctx.restore();return;}
    const p=projection(view,rect,frame);
    drawHaze(ctx,w,h,p);
    for(const star of stars){
      const point=project(star.direction,p);
      if(!point||point.x< -star.radius||point.x>w+star.radius||point.y< -star.radius||point.y>h+star.radius)continue;
      ctx.fillStyle=star.color;ctx.beginPath();ctx.arc(point.x,point.y,star.radius,0,TAU);ctx.fill();
    }
    const point=drawRecordedStar(ctx,star,p,view,rect,w,h);
    ctx.restore();
    return point;
  }
  root.HWOrbitBackground={draw,projectDirection};
  if(typeof module!=='undefined'&&module.exports)module.exports=root.HWOrbitBackground;
})();
