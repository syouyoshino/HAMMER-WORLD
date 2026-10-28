(() => {
  "use strict";
  const root=typeof window==='undefined'?globalThis:window,TAU=Math.PI*2;
  const clamp=(v,lo,hi)=>Math.max(lo,Math.min(hi,v));
  const dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
  function hash(n){const x=Math.sin(n*127.1+311.7)*43758.5453;return x-Math.floor(x);}
  function direction(y,lon){const r=Math.sqrt(1-y*y);return [r*Math.sin(lon),y,r*Math.cos(lon)];}
  // Fixed world directions: camera rotation changes the field without reseeding it.
  const stars=Array.from({length:150},(_,i)=>({direction:direction(2*hash(i+1)-1,TAU*hash(i+211)),radius:.45+hash(i+431)*.7,color:`rgba(190,207,219,${(.25+hash(i+701)*.48).toFixed(3)})`}));
  const clouds=Array.from({length:24},(_,i)=>({direction:direction(1-2*(i+.5)/24,i*2.399963229728653),strength:.065+.12*hash(i+811),spread:.74+.4*hash(i+911)}));
  function projection(view,rect,frame){return {frame,cx:rect.left+rect.width/2,cy:rect.top+rect.height/2,scale:Math.min(rect.width,rect.height)*.48*(1+.12*clamp((2.45-(view.distance??2.45))/1.45,-1,1))};}
  function project(direction,p,minDepth=.16){
    const depth=-dot(direction,p.frame.N);if(depth<=minDepth)return null;
    return {x:p.cx+p.scale*dot(direction,p.frame.E)/depth,y:p.cy-p.scale*dot(direction,p.frame.U)/depth,depth};
  }
  function projectDirection(direction,view,rect){
    const frame=root.HWPlanetOrbit?.basis(view.latitude,view.longitude);
    return frame?project(direction,projection(view,rect,frame)):null;
  }
  function draw(ctx,w,h,view,rect={left:0,top:0,width:w,height:h}){
    ctx.save();ctx.fillStyle="#070b10";ctx.fillRect(0,0,w,h);
    const frame=root.HWPlanetOrbit?.basis(view.latitude,view.longitude);
    if(!frame){ctx.restore();return;}
    const p=projection(view,rect,frame);
    for(const cloud of clouds){
      const point=project(cloud.direction,p,.025);if(!point)continue;
      const radius=p.scale*cloud.spread/point.depth,alpha=cloud.strength*clamp((point.depth-.025)/.2,0,1);
      const haze=ctx.createRadialGradient(point.x,point.y,0,point.x,point.y,radius);
      haze.addColorStop(0,`rgba(110,121,131,${alpha})`);haze.addColorStop(.48,`rgba(89,101,113,${alpha*.58})`);haze.addColorStop(1,"rgba(75,88,102,0)");
      ctx.fillStyle=haze;ctx.fillRect(0,0,w,h);
    }
    for(const star of stars){
      const point=project(star.direction,p);
      if(!point||point.x< -star.radius||point.x>w+star.radius||point.y< -star.radius||point.y>h+star.radius)continue;
      ctx.fillStyle=star.color;ctx.beginPath();ctx.arc(point.x,point.y,star.radius,0,TAU);ctx.fill();
    }
    ctx.restore();
  }
  root.HWOrbitBackground={draw,projectDirection};
  if(typeof module!=='undefined'&&module.exports)module.exports=root.HWOrbitBackground;
})();
