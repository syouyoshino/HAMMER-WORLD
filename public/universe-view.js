(() => {
  'use strict';

  // Universe is a schematic projection of the public galactic response. Its layout
  // encodes hierarchy only; it never interprets saved coordinates as distances.
  function fromGalactic(record) {
    const contacts = [];
    for (const group of record?.groups || []) {
      const region = group?.region;
      if (!region || region.knowledge === 'hidden') continue;
      contacts.push({n: region, regionId: region.id, contactLevel: 'region'});
      for (const sector of group.sectors || []) {
        if (!sector || sector.knowledge === 'hidden') continue;
        contacts.push({n: sector, regionId: region.id, contactLevel: 'sector'});
      }
    }
    return {...record, sourceLevel: record?.level, level: 'universe', nodes: contacts.map(contact => contact.n), contacts};
  }

  function draw(ctx, {w,h,record,safe,zoom=1,panX=0,panY=0,theme='dark',selectedContactId=null}) {
    const dark=theme==='dark',cx=(safe.left+safe.right)/2,cy=(safe.top+safe.bottom)/2;
    ctx.fillStyle=dark?'#101923':'#e9ebe6';ctx.fillRect(0,0,w,h);
    const contacts=record?.contacts||[],regions=contacts.filter(c=>c.contactLevel==='region'),sectors=contacts.filter(c=>c.contactLevel==='sector');
    const compact=safe.height<340,columns=Math.max(1,Math.min(contacts.length,Math.floor(safe.width/230))),cellWidth=safe.width/columns;
    const gap=compact?cellWidth:Math.max(220,(safe.width-80)/Math.max(1,regions.length)),span=(regions.length-1)*gap,groups=new Map(),layout=new Map(),positions=[];
    const content={left:safe.left,right:safe.right,top:safe.top+48,bottom:safe.bottom};
    const compactSlots=new Map();
    if(compact)contacts.forEach((contact,index)=>compactSlots.set(contact.n.id,{x:safe.left+cellWidth*(index%columns+.5),y:content.top+34+Math.floor(index/columns)*104+(contact.contactLevel==='sector'?18:0)}));
    regions.forEach((contact,index)=>groups.set(contact.n.id,{contact,...(compact?compactSlots.get(contact.n.id):{x:cx-span/2+index*gap,y:cy-105}),children:sectors.filter(s=>s.regionId===contact.n.id)}));
    const project=(x,y)=>({x:cx+(x-cx)*zoom+panX,y:cy+(y-cy)*zoom+panY});
    const bounded=rect=>{const r={left:Math.max(content.left,rect.left),right:Math.min(content.right,rect.right),top:Math.max(content.top,rect.top),bottom:Math.min(content.bottom,rect.bottom)};return r.left<r.right&&r.top<r.bottom?r:null;};
    ctx.save();ctx.beginPath();ctx.rect(safe.left,safe.top,safe.width,safe.height);ctx.clip();
    const mist=ctx.createLinearGradient(safe.left,safe.top,safe.right,safe.bottom);
    mist.addColorStop(0,dark?'rgba(38,51,59,.82)':'rgba(177,186,184,.82)');mist.addColorStop(.34,dark?'rgba(22,34,42,.62)':'rgba(199,206,201,.65)');mist.addColorStop(.7,dark?'rgba(33,45,52,.76)':'rgba(185,194,191,.76)');mist.addColorStop(1,dark?'rgba(45,55,59,.86)':'rgba(169,180,179,.86)');
    ctx.fillStyle=mist;ctx.fillRect(safe.left,safe.top,safe.width,safe.height);
    // Fine low contrast diagonal grain supplies a qualitative fog texture without an edge or boundary.
    ctx.strokeStyle=dark?'rgba(192,204,200,.055)':'rgba(60,74,75,.055)';ctx.lineWidth=1;
    for(let x=safe.left-safe.height;x<safe.right;x+=13){ctx.beginPath();ctx.moveTo(x,safe.top);ctx.lineTo(x+safe.height,safe.bottom);ctx.stroke();}
    ctx.textAlign='center';ctx.font='12px "Noto Instrument Mono",monospace';ctx.fillStyle=dark?'#aebdbc':'#526366';
    ctx.fillText('UNCHARTED SPACE · EMPTY SPACE HAS NO GEOGRAPHIC MEANING',cx,safe.top+22);
    ctx.textAlign='left';ctx.font='11px "Noto Instrument Mono",monospace';ctx.fillText('RECORDED HIERARCHY · NOT TRAVEL LINKS',safe.left+12,safe.top+41);
    ctx.save();ctx.beginPath();ctx.rect(content.left,content.top,safe.width,Math.max(0,content.bottom-content.top));ctx.clip();
    const line=dark?'rgba(157,182,182,.44)':'rgba(66,91,92,.42)';ctx.strokeStyle=line;ctx.lineWidth=1;ctx.setLineDash([3,5]);
    for(const group of groups.values()){
      const root=project(group.x,group.y+(compact?-23:17)),trunkX=group.x-22,lastY=cy+48+(group.children.length-1)*76;
      if(!compact&&group.children.length){const junction=project(trunkX,group.y+17),trunkEnd=project(trunkX,lastY);ctx.beginPath();ctx.moveTo(root.x,root.y);ctx.lineTo(junction.x,junction.y);ctx.lineTo(trunkEnd.x,trunkEnd.y);ctx.stroke();}
      group.children.forEach((sector,index)=>{const slot=compact?compactSlots.get(sector.n.id):{x:group.x,y:cy+48+index*76}, {x,y}=slot;layout.set(sector.n.id,{x,y,trunkX});const point=project(x,y);ctx.beginPath();if(compact){const bend=project(x,group.y-23);ctx.moveTo(root.x,root.y);ctx.lineTo(bend.x,bend.y);ctx.lineTo(point.x,point.y-12);}else{const junction=project(trunkX,y);ctx.moveTo(junction.x,junction.y);ctx.lineTo(point.x-10,point.y);}ctx.stroke();});
    }
    ctx.setLineDash([]);
    for(const group of groups.values()){
      const n=group.contact.n,p=project(group.x,group.y),name=n.name||'Region · name unrecorded',selected=n.id===selectedContactId,type=`${selected?'Selected · ':''}Region · ${n.knowledge==='detected'?'Detected · Position unknown':'Surveyed'}`;
      ctx.strokeStyle=dark?'#c3a66f':'#76633e';ctx.lineWidth=1.5;ctx.beginPath();ctx.arc(p.x,p.y,17,0,Math.PI*2);ctx.stroke();ctx.beginPath();ctx.arc(p.x,p.y,5,0,Math.PI*2);ctx.fillStyle=dark?'#c3a66f':'#76633e';ctx.fill();
      if(selected){ctx.strokeStyle=dark?'#d8e4df':'#385b61';ctx.setLineDash([2,3]);ctx.beginPath();ctx.arc(p.x,p.y,23,0,Math.PI*2);ctx.stroke();ctx.setLineDash([]);}
      ctx.textAlign='center';ctx.font='600 13px "Noto Instrument Mono",monospace';const nameWidth=ctx.measureText(name).width;ctx.fillStyle=dark?'#e0e6e2':'#26343a';ctx.fillText(name,p.x,p.y+39,Math.max(120,gap-24));
      ctx.font='11px "Noto Instrument Mono",monospace';ctx.fillStyle=dark?'#bac8c5':'#526366';const typeWidth=ctx.measureText(type).width;ctx.fillText(type,p.x,p.y+55,gap-24);
      const width=Math.min(gap-16,Math.max(128,nameWidth+12,typeWidth+12)),frameRect={left:p.x-width/2,right:p.x+width/2,top:p.y-23,bottom:p.y+60},hit=bounded(frameRect);
      if(hit)positions.push({n,...p,anchorX:p.x,anchorY:p.y,radius:18,frameRect,hitRect:hit,contactLevel:'region'});
    }
    for(const sector of sectors){
      const slot=layout.get(sector.n.id);if(!slot)continue;const n=sector.n,p=project(slot.x,slot.y),detected=n.knowledge==='detected',selected=n.id===selectedContactId,name=n.name||'Sector · name unrecorded',type=`${selected?'Selected · ':''}Sector · ${detected?'Detected · Position unknown':'Surveyed'}`;
      ctx.lineWidth=1.5;ctx.strokeStyle=detected?(dark?'#d3aa68':'#8a6223'):(dark?'#8da6a6':'#607574');
      if(detected)ctx.strokeRect(p.x-5,p.y-5,10,10);else{ctx.fillStyle=ctx.strokeStyle;ctx.fillRect(p.x-4,p.y-4,8,8);}
      if(selected){ctx.strokeStyle=dark?'#d8e4df':'#385b61';ctx.strokeRect(p.x-9,p.y-9,18,18);}
      ctx.textAlign='center';ctx.font='600 12px "Noto Instrument Mono",monospace';const nameWidth=ctx.measureText(name).width;ctx.fillStyle=dark?'#d5dfdc':'#354448';ctx.fillText(name,p.x,p.y+21,Math.max(130,gap-20));
      ctx.font='11px "Noto Instrument Mono",monospace';ctx.fillStyle=detected?(dark?'#e0bd84':'#79591f'):(dark?'#aebdbc':'#526366');const typeWidth=ctx.measureText(type).width;ctx.fillText(type,p.x,p.y+37,gap-24);
      const width=Math.min(gap-16,Math.max(132,nameWidth+16,typeWidth+12)),frameRect={left:p.x-width/2,right:p.x+width/2,top:p.y-12,bottom:p.y+43},hit=bounded(frameRect);
      if(hit)positions.push({n,...p,anchorX:p.x,anchorY:p.y,radius:12,frameRect,hitRect:hit,contactLevel:'sector'});
    }
    if(!contacts.length){ctx.textAlign='center';ctx.font='600 13px "Noto Instrument Mono",monospace';ctx.fillStyle=dark?'#d2dbd9':'#34464a';ctx.fillText('No regions or sectors are recorded',cx,cy-7);}
    ctx.restore();ctx.restore();
    return {hierarchy:true,universe:true,positions,hitTargets:positions,safeRect:safe,sceneRect:safe,model:{contacts}};
  }

  const api = {fromGalactic, draw};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (typeof window !== 'undefined') window.HWUniverseView = api;
})();
