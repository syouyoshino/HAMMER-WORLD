(() => {
  'use strict';
  const root=typeof window==='undefined'?globalThis:window;
  const TAU=Math.PI*2,clamp=(value,min,max)=>Math.max(min,Math.min(max,value));
  const finiteVector=value=>Array.isArray(value)&&value.length===3&&value.every(Number.isFinite);
  const radiusFor=kind=>kind==='star'?42:kind==='planet'?24:kind==='moon'?12:16;
  const fit=()=>({yaw:-.55,pitch:.62,distance:2.2,panX:0,panY:0,contactScroll:0});

  function model(record){
    const contacts=[],seen=new Set();
    const add=node=>{if(!node||node.knowledge==='hidden'||!node.id||seen.has(node.id))return;seen.add(node.id);contacts.push(node);};
    for(const body of record?.bodies||[])add(body);
    for(const planet of record?.nodes||[]){add(planet);for(const moon of planet.moons||[])add(moon);}
    const astronomy=record?.astronomy,systemId=record?.parent?.id;
    const valid=astronomy?.version==='static-v1'&&astronomy?.motion==='frozen'&&astronomy?.frame==='system-xyz-v1'&&astronomy?.position_unit==='micro-AU'&&astronomy?.systems?.[systemId]?.bodies;
    const saved=valid?astronomy.systems[systemId].bodies:{};
    const star=contacts.find(item=>item.kind==='star'&&item.knowledge==='surveyed');
    const starRecord=star&&saved[star.id],hasOrigin=Boolean(starRecord&&finiteVector(starRecord.position)),origin=hasOrigin?starRecord.position:[0,0,0];
    const located=[];
    for(const node of contacts){
      const row=node.knowledge==='surveyed'?saved[node.id]:null;
      if(!hasOrigin||!finiteVector(row?.position)){continue;}
      const relative=row.position.map((value,index)=>value-origin[index]);
      if(relative.every(Number.isFinite))located.push({n:node,relative,radiusKm:row.radius_km});
    }
    const normalizer=Math.max(0,...located.map(item=>Math.hypot(...item.relative)));
    const scale=normalizer>0?normalizer:1;
    for(const item of located)item.normalized=item.relative.map(value=>value/scale);
    const locatedIds=new Set(located.map(item=>item.n.id));
    const unlocated=contacts.filter(item=>!locatedIds.has(item.id));
    return{supported:Boolean(valid&&hasOrigin),systemId,normalizer,contacts,located,unlocated,starId:star?.id||null};
  }

  function project(record,view={},viewport={}){
    const data=model(record),safe=viewport.safeRect||{left:0,top:0,right:viewport.width||0,bottom:viewport.height||0},w=Math.max(0,safe.right-safe.left),h=Math.max(0,safe.bottom-safe.top);
    const railWidth=data.unlocated.length?Math.min(264,Math.max(100,w*.36)):0,railGap=railWidth?12:0,visibleRows=Math.max(1,Math.floor(Math.max(38,h-64)/38)),maxScroll=Math.max(0,data.unlocated.length-visibleRows),contactScroll=clamp(Math.floor(view.contactScroll||0),0,maxScroll),contactsShown=data.unlocated.slice(contactScroll,contactScroll+visibleRows),railHeight=40+contactsShown.length*38;
    const railAt=(left,top=safe.top+8)=>({left,top,right:left+railWidth,bottom:top+railHeight});
    let rail=railWidth?railAt(safe.right-railWidth-8):null;
    if(rail&&viewport.forceControlRect){const overlaps=(a,b)=>a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top;const left=railAt(safe.left+8);if(overlaps(rail,viewport.forceControlRect)&&!overlaps(left,viewport.forceControlRect))rail=left;else if(overlaps(rail,viewport.forceControlRect)&&overlaps(left,viewport.forceControlRect)){const top=clamp(viewport.forceControlRect.bottom+8,safe.top+8,safe.bottom-railHeight-4);rail=railAt(rail.left,top);}}
    const railAtLeft=Boolean(rail&&rail.left<safe.left+w/2),scene={left:railAtLeft?rail.right+railGap:safe.left+8,top:safe.top+8,right:rail?(railAtLeft?safe.right-8:rail.left-railGap):safe.right-8,bottom:safe.bottom-8};
    if(scene.right<scene.left+80){scene.left=safe.left+4;scene.right=safe.right-4;}
    const initial=fit(),yaw=Number.isFinite(view.yaw)?view.yaw:initial.yaw,pitch=clamp(Number.isFinite(view.pitch)?view.pitch:initial.pitch,-1.45,1.45),distance=clamp(Number.isFinite(view.distance)?view.distance:initial.distance,1.25,20),panX=clamp(Number.isFinite(view.panX)?view.panX:0,-w*.8,w*.8),panY=clamp(Number.isFinite(view.panY)?view.panY:0,-h*.8,h*.8),cy=Math.cos(yaw),sy=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch),focal=Math.max(1,Math.min(scene.right-scene.left,scene.bottom-scene.top)*.72),cx=(scene.left+scene.right)/2+panX,centerY=(scene.top+scene.bottom)/2+panY;
    const projectVector=vector=>{const [x,y,z]=vector,xr=x*cy-z*sy,zr=x*sy+z*cy,yr=y*cp-zr*sp,depth=distance-(y*sp+zr*cp);if(!Number.isFinite(depth)||depth<=.2)return null;const px=cx+xr*focal/depth,py=centerY-yr*focal/depth;return Number.isFinite(px)&&Number.isFinite(py)?{x:px,y:py,depth}:null;};
    const positions=[];
    if(data.supported){for(const item of data.located){const projected=projectVector(item.normalized);if(!projected||projected.x<scene.left||projected.x>scene.right||projected.y<scene.top||projected.y>scene.bottom)continue;positions.push({n:item.n,...projected,worldX:item.normalized[0],worldY:item.normalized[1],worldZ:item.normalized[2],normalized:item.normalized,relative:item.relative,radiusKm:item.radiusKm});}}
    const measure=typeof viewport.measureText==='function'?viewport.measureText:value=>String(value).length*6.1;
    const labelItems=[...positions].sort((a,b)=>a.depth-b.depth),occupied=positions.map(point=>{const r=radiusFor(point.n.kind);return{left:point.x-r-4,right:point.x+r+4,top:point.y-r-4,bottom:point.y+r+4};});
    for(const point of labelItems){const label=String(point.n.name||point.n.kind),radius=radiusFor(point.n.kind),secondary=point.n.kind==='star'?'Host star':point.n.kind==='planet'?`${(Math.hypot(...point.relative)/1_000_000).toFixed(3)} AU from host star`:'',labelWidth=Math.min(190,Math.max(42,measure(label)+12,secondary?measure(secondary)+12:0)),labelHeight=secondary?32:18,gap=7,candidates=[[point.x-labelWidth/2,point.y+radius+gap],[point.x-labelWidth/2,point.y-radius-gap-labelHeight],[point.x+radius+gap,point.y-labelHeight/2],[point.x-radius-gap-labelWidth,point.y-labelHeight/2],[point.x+radius*.7,point.y-radius-gap-labelHeight],[point.x-radius*.7-labelWidth,point.y+radius+gap]];let labelRect=null;
      for(const [left,top]of candidates){const x=clamp(left,scene.left+2,scene.right-labelWidth-2),y=clamp(top,scene.top+2,scene.bottom-labelHeight-2),box={left:x,top:y,right:x+labelWidth,bottom:y+labelHeight};if(occupied.some(other=>box.left<other.right+3&&box.right>other.left-3&&box.top<other.bottom+3&&box.bottom>other.top-3))continue;labelRect=box;break;}
      if(!labelRect){const left=clamp(point.x-labelWidth/2,scene.left+2,scene.right-labelWidth-2),top=clamp(point.y+radius+gap,scene.top+2,scene.bottom-labelHeight-2);labelRect={left,top,right:left+labelWidth,bottom:top+labelHeight};}
      point.labelPrimary=label;point.labelSecondary=secondary;point.labelRect=labelRect;point.radius=radius;occupied.push(labelRect);point.hitRect={left:Math.min(point.x-radius-5,labelRect.left),top:Math.min(point.y-radius-5,labelRect.top),right:Math.max(point.x+radius+5,labelRect.right),bottom:Math.max(point.y+radius+5,labelRect.bottom)};
    }
    const hits=[...positions].sort((a,b)=>a.depth-b.depth);
    const gridLines=[];if(data.supported&&data.normalizer>0){for(let i=-4;i<=4;i++){const u=i/4,a=projectVector([-1,0,u]),b=projectVector([1,0,u]),c=projectVector([u,0,-1]),d=projectVector([u,0,1]);if(a&&b)gridLines.push({a,b,axis:i===0?'X':null});if(c&&d)gridLines.push({a:c,b:d,axis:i===0?'Z':null});}}
    const contactsById=new Map(data.contacts.map(node=>[node.id,node]));
    const unlocatedTargets=contactsShown.map((node,index)=>{const top=rail.top+31+index*38,parent=contactsById.get(node.parent_id),displayName=parent?.kind==='planet'?`${parent.name||'Unknown planet'} / ${node.name||'Unknown moon'}`:`${node.name||'Unknown body'} · ${node.kind}`;return{n:node,displayName,uiOnly:true,status:'Position unrecorded',contactIndex:contactScroll+index,x:(rail.left+rail.right)/2,y:top+7,hitRect:{left:rail.left+7,right:rail.right-7,top:top-5,bottom:top+33}};});
    const forceObstacles=[];if(railWidth)forceObstacles.push(rail);for(const target of hits)forceObstacles.push(target.hitRect);
    return{hierarchy:true,system:true,supported:data.supported,normalizer:data.normalizer,positions:positions.map(point=>({n:point.n,x:point.x,y:point.y,depth:point.depth,radius:point.radius,worldX:point.worldX,worldY:point.worldY,worldZ:point.worldZ,normalized:point.normalized,relative:point.relative,labelPrimary:point.labelPrimary,labelSecondary:point.labelSecondary,labelRect:point.labelRect,hitRect:point.hitRect})),hitTargets:[...hits,...unlocatedTargets],safeRect:safe,sceneRect:scene,railRect:railWidth?rail:null,gridLines,forceObstacles,contactRange:{start:contactScroll,end:contactScroll+contactsShown.length,total:data.unlocated.length,maxScroll},model:data};
  }

  function draw(ctx,{w,h,record,view={},safeRect,theme='dark',forceControlRect=null}={}){
    const safe=safeRect||{left:0,top:0,right:w,bottom:h},dark=theme==='dark';ctx.font='10px "Noto Instrument Mono",monospace';
    const layout=project(record,view,{width:w,height:h,safeRect:safe,forceControlRect,measureText:value=>ctx.measureText(value).width});
    const background=ctx.createLinearGradient(0,safe.top,0,safe.bottom);background.addColorStop(0,dark?'#0b1722':'#dce5e5');background.addColorStop(1,dark?'#111d27':'#e9ece6');ctx.fillStyle=background;ctx.fillRect(0,0,w,h);
    if(root.HWOrbitBackground?.draw)root.HWOrbitBackground.draw(ctx,w,h,{latitude:view.pitch??.62,longitude:view.yaw??-.55,distance:2.45},{left:layout.sceneRect.left,top:layout.sceneRect.top,width:layout.sceneRect.right-layout.sceneRect.left,height:layout.sceneRect.bottom-layout.sceneRect.top});
    ctx.save();ctx.beginPath();ctx.rect(layout.sceneRect.left,layout.sceneRect.top,layout.sceneRect.right-layout.sceneRect.left,layout.sceneRect.bottom-layout.sceneRect.top);ctx.clip();
    const data=layout.model,starPoint=layout.positions.find(item=>item.n.kind==='star');ctx.font='10px "Noto Instrument Mono",monospace';
    for(const line of layout.gridLines){ctx.strokeStyle=line.axis?(dark?'rgba(175,203,205,.30)':'rgba(47,78,83,.30)'):(dark?'rgba(158,190,198,.11)':'rgba(56,89,94,.13)');ctx.lineWidth=line.axis?1.15:.7;ctx.beginPath();ctx.moveTo(line.a.x,line.a.y);ctx.lineTo(line.b.x,line.b.y);ctx.stroke();if(line.axis){ctx.fillStyle=dark?'#aebfc0':'#4c5d60';ctx.font='9px "Noto Instrument Mono",monospace';ctx.textAlign='left';ctx.fillText(line.axis,line.b.x+3,line.b.y-3);}}
    const angle=(value)=>`${Math.round(value*180/Math.PI)}°`,readout=`SYSTEM FRAME · YAW ${angle(Number.isFinite(view.yaw)?view.yaw:-.55)} · PITCH ${angle(Number.isFinite(view.pitch)?view.pitch:.62)}`;
    ctx.fillStyle=dark?'rgba(10,21,30,.78)':'rgba(240,245,240,.84)';ctx.fillRect(layout.sceneRect.left+8,layout.sceneRect.top+7,Math.min(250,readout.length*6+14),21);ctx.fillStyle=dark?'#aebfc0':'#4c5d60';ctx.textAlign='left';ctx.fillText(readout,layout.sceneRect.left+15,layout.sceneRect.top+21,240);
    for(const point of [...layout.positions].sort((a,b)=>b.depth-a.depth)){
      const node=point.n,r=radiusFor(node.kind);ctx.save();ctx.translate(point.x,point.y);
      if(node.kind==='star'){
        const glow=ctx.createRadialGradient(0,0,r*.2,0,0,58);glow.addColorStop(0,'rgba(255,220,153,.68)');glow.addColorStop(.28,'rgba(245,174,82,.28)');glow.addColorStop(1,'rgba(245,174,82,0)');ctx.fillStyle=glow;ctx.beginPath();ctx.arc(0,0,58,0,TAU);ctx.fill();
        const disc=ctx.createRadialGradient(-7,-8,2,0,0,r);disc.addColorStop(0,'#fff1c2');disc.addColorStop(.42,'#f6c76e');disc.addColorStop(1,'#b96c32');ctx.fillStyle=disc;ctx.beginPath();ctx.arc(0,0,r,0,TAU);ctx.fill();
      }else{
        const palette={arid:['#d3ae72','#72502e'],barren:['#c7c0b2','#56534f'],ice:['#f2f5f1','#687e8d'],oceanic:['#79c0d3','#203d67'],terrestrial:['#8cae8c','#334f5e']},colors=palette[node.class]||['#b1b7a8','#49575c'];
        let lx=-.4,ly=-.7;if(starPoint){lx=clamp((starPoint.x-point.x)/Math.max(1,Math.hypot(starPoint.x-point.x,starPoint.y-point.y)),-1,1)*.6;ly=clamp((starPoint.y-point.y)/Math.max(1,Math.hypot(starPoint.x-point.x,starPoint.y-point.y)),-1,1)*.6;}
        const globe=ctx.createRadialGradient(lx*r,ly*r,r*.05,0,0,r*1.15);globe.addColorStop(0,colors[0]);globe.addColorStop(.62,colors[0]);globe.addColorStop(1,colors[1]);ctx.fillStyle=globe;ctx.beginPath();ctx.arc(0,0,r,0,TAU);ctx.fill();
        ctx.strokeStyle=dark?'rgba(232,241,239,.58)':'rgba(28,48,55,.62)';ctx.lineWidth=1;ctx.stroke();
      }
      ctx.restore();
      const box=point.labelRect,tx=clamp(point.x,box.left+4,box.right-4),ty=point.y<box.top?box.top:box.bottom;
      if(Math.hypot(tx-point.x,ty-point.y)>r+5){ctx.strokeStyle=dark?'rgba(178,199,198,.42)':'rgba(55,79,82,.42)';ctx.lineWidth=.8;ctx.beginPath();ctx.moveTo(point.x+(tx-point.x)*r/Math.max(1,Math.hypot(tx-point.x,ty-point.y)),point.y+(ty-point.y)*r/Math.max(1,Math.hypot(tx-point.x,ty-point.y)));ctx.lineTo(tx,ty);ctx.stroke();}
      ctx.fillStyle=dark?'rgba(13,25,35,.88)':'rgba(241,245,239,.9)';ctx.fillRect(box.left,box.top,box.right-box.left,box.bottom-box.top);ctx.strokeStyle=dark?'rgba(174,197,200,.35)':'rgba(53,76,79,.32)';ctx.strokeRect(box.left,box.top,box.right-box.left,box.bottom-box.top);ctx.fillStyle=dark?'#edf1e8':'#223239';ctx.font='10px "Noto Instrument Mono",monospace';ctx.textAlign='center';ctx.fillText(point.labelPrimary,(box.left+box.right)/2,box.top+12,box.right-box.left-8);if(point.labelSecondary){ctx.fillStyle=dark?'#aebfc0':'#526468';ctx.font='8px "Noto Instrument Mono",monospace';ctx.fillText(point.labelSecondary,(box.left+box.right)/2,box.top+26,box.right-box.left-8);}
    }
    ctx.restore();
    if(layout.railRect){const rail=layout.railRect;ctx.fillStyle=dark?'rgba(12,23,32,.92)':'rgba(241,244,238,.94)';ctx.fillRect(rail.left,rail.top,rail.right-rail.left,rail.bottom-rail.top);ctx.strokeStyle=dark?'rgba(160,186,190,.48)':'rgba(61,80,80,.42)';ctx.strokeRect(rail.left,rail.top,rail.right-rail.left,rail.bottom-rail.top);ctx.fillStyle=dark?'#bdc9c8':'#4d5b5c';ctx.font='8px "Noto Instrument Mono",monospace';ctx.textAlign='left';const range=layout.contactRange;ctx.fillText(`${layout.supported?'UNLOCATED':'POSITIONS UNKNOWN'} · ${range.start+1}–${range.end}/${range.total} · WHEEL`,rail.left+9,rail.top+16,rail.right-rail.left-18);for(const target of layout.hitTargets.filter(item=>item.uiOnly)){const r=target.hitRect;ctx.fillStyle=dark?'rgba(26,40,49,.72)':'rgba(255,255,255,.54)';ctx.fillRect(r.left,r.top,r.right-r.left,r.bottom-r.top);ctx.fillStyle=dark?'#e3e8e4':'#26383e';ctx.font='10px "Noto Instrument Mono",monospace';ctx.fillText(target.displayName,r.left+7,r.top+12,Math.max(12,r.right-r.left-14));ctx.fillStyle=dark?'#9cabad':'#59696b';ctx.font='8px "Noto Instrument Mono",monospace';ctx.fillText('Position unrecorded',r.left+7,r.top+27,Math.max(12,r.right-r.left-14));}}
    const note=layout.supported?`MAX DIST ${(data.normalizer/1_000_000).toFixed(3)} AU · SYMBOLS ENLARGED · SKY DECORATIVE`:'POSITIONS UNRECORDED · SKY DECORATIVE';ctx.fillStyle=dark?'rgba(10,21,30,.82)':'rgba(240,245,240,.86)';ctx.fillRect(layout.sceneRect.left+8,safe.bottom-24,Math.max(10,layout.sceneRect.right-layout.sceneRect.left-16),18);ctx.fillStyle=dark?'#aebfc0':'#4c5d60';ctx.font='8px "Noto Instrument Mono",monospace';ctx.textAlign='left';ctx.fillText(note,layout.sceneRect.left+14,safe.bottom-12,Math.max(10,layout.sceneRect.right-layout.sceneRect.left-28));
    return layout;
  }
  root.HWSystemView={model,project,draw,fit};
  if(typeof module!=='undefined'&&module.exports)module.exports=root.HWSystemView;
})();
