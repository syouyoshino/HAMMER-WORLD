(() => {
  'use strict';

  // Universe is a public, schematic contact chart. Its artwork is decorative and
  // never supplies physical locations or distances for recorded contacts.
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

  function strategicRecordLabel(record) {
    const galactic=record?.level==='galactic',kind=galactic?'sector':'system';
    let entries=null;
    if(galactic&&Array.isArray(record.groups)){
      const groups=record.groups.filter(group=>group?.region&&group.region.knowledge!=='hidden');
      if(groups.every(group=>Array.isArray(group.sectors)))entries=groups.flatMap(group=>group.sectors);
    }else if(record?.level==='sector'&&Array.isArray(record.nodes))entries=record.nodes;
    if(entries===null)return `${kind.toUpperCase()} RECORDS UNKNOWN`;
    const count=entries.filter(node=>node&&node.knowledge!=='hidden'&&node.kind===kind).length;
    return `${count} ${kind.toUpperCase()} ${count===1?'RECORD':'RECORDS'}`;
  }

  function hash(value) {
    let h = 2166136261;
    for (const char of String(value)) h = Math.imul(h ^ char.charCodeAt(0), 16777619);
    return h >>> 0;
  }
  const hasChartLocation = node => node && node.knowledge !== 'hidden' && node.knowledge !== 'detected' && Number.isFinite(node?.x) && Number.isFinite(node?.y);
  function random(seed) {
    let x = seed >>> 0;
    return () => { x = (Math.imul(x, 1664525) + 1013904223) >>> 0; return x / 4294967296; };
  }
  // Bounded decorative textures: built once per theme, independent of records.
  const artwork = new Map();
  function galaxyTexture(dark) {
    if (artwork.has(dark)) return artwork.get(dark);
    if (typeof document === 'undefined') return null;
    const canvas = document.createElement('canvas'); canvas.width = 1400; canvas.height = 900;
    const c = canvas.getContext('2d'), rng = random(0x51a7a);
    const normal = () => Math.sqrt(-2 * Math.log(Math.max(.00001, rng()))) * Math.cos(rng() * Math.PI * 2);
    // Local elliptical puffs fade monotonically to transparency. Overlapping small
    // clouds leave broken, feathery edges rather than a bounded oval or stroked arm.
    const puff = (x,y,r,color,alpha,flat=1) => {
      c.save(); c.translate(x,y); c.scale(1,flat);
      const g = c.createRadialGradient(0,0,0,0,0,r);
      g.addColorStop(0,`rgba(${color},${alpha})`);
      g.addColorStop(.35,`rgba(${color},${alpha*.52})`);
      g.addColorStop(.7,`rgba(${color},${alpha*.12})`);
      g.addColorStop(1,`rgba(${color},0)`);
      c.fillStyle=g; c.fillRect(-r,-r,r*2,r*2); c.restore();
    };
    c.translate(700,450); c.rotate(-.34);
    const colors = dark ? ['73,112,159','108,105,151','58,120,140'] : ['89,126,143','130,115,145','88,137,145'];
    for (let i=0;i<230;i++) {
      const t=rng(), angle=t*5.6+(i%3)*Math.PI*2/3, radius=35+t*540;
      const x=Math.cos(angle)*radius+normal()*40, y=Math.sin(angle)*radius*.42+normal()*22;
      puff(x,y,35+rng()*105,colors[i%3],dark?.08:.055,.5+rng()*.4);
    }
    // Dust lanes are gaps between thousands of irregularly scattered fine points.
    // The drawing is scenery only: none of these points are navigable objects.
    for (let i=0;i<20000;i++) {
      const t=Math.pow(rng(),.72), angle=t*5.6+(i%3)*Math.PI*2/3+normal()*(.11+t*.16);
      const radius=18+t*540, x=Math.cos(angle)*radius+normal()*14, y=Math.sin(angle)*radius*.42+normal()*9;
      const size=.22+rng()*.85;
      c.globalAlpha=(.035+rng()*.32)*(1-t*.65)*(dark?1:.5);
      c.fillStyle=dark?(i%5?'#c0d6e7':'#e9d4b1'):(i%5?'#46667a':'#967961');
      c.fillRect(x,y,size,size);
    }
    c.globalAlpha=1;
    puff(-7,0,155,dark?'154,168,191':'148,156,153',dark?.17:.09,.5);
    puff(-7,0,76,dark?'235,216,178':'255,246,220',dark?.22:.17,.55);
    puff(-7,0,28,dark?'255,242,215':'255,251,232',dark?.25:.24,.65);
    artwork.set(dark,canvas); return canvas;
  }
  function drawArtwork(ctx, {safe, dark, time, panX, panY}) {
    const {left, right, top, bottom, width, height} = safe;
    const cx=(left+right)/2, cy=(top+bottom)/2;
    ctx.fillStyle=dark?'#040a13':'#e3e9e9'; ctx.fillRect(left,top,width,height);
    const texture=galaxyTexture(dark);
    if (texture) {
      const scale=Math.max(width/1400,height/900)*1.1;
      ctx.save();
      ctx.translate(cx+panX*.035+Math.sin(time*.000018)*width*.008,cy+panY*.035+Math.cos(time*.000015)*height*.006);
      ctx.rotate(Math.sin(time*.000009)*.008);
      ctx.drawImage(texture,-700*scale,-450*scale,1400*scale,900*scale); ctx.restore();
    }
    // Sparse foreground stars have several slow parallax depths. The dense cloud
    // above is cached; no gradients or particle populations are rebuilt per frame.
    const rng=random(0x81a7a);
    const count=Math.max(100,Math.min(280,Math.floor(width*height/4500)));
    for (let i=0;i<count;i++) {
      const x0=rng()*width,y0=rng()*height,depth=.018+rng()*.16;
      const x=left+(((x0+panX*depth+time*depth*.0015)%width)+width)%width;
      const y=top+(((y0+panY*depth+time*depth*.00065)%height)+height)%height;
      const radius=.3+rng()*.8;
      ctx.globalAlpha=.18+rng()*.55;ctx.fillStyle=dark?(i%7?'#dbe8ed':'#f2d9aa'):(i%7?'#526d7b':'#9c7351');
      ctx.beginPath();ctx.arc(x,y,radius,0,Math.PI*2);ctx.fill();
    }
    ctx.globalAlpha=1;
  }

  function draw(ctx, {w,h,record,safe,zoom=1,panX=0,panY=0,theme='dark',selectedContactId=null,originContactIds=[],originName='system',time=0}) {
    const dark = theme === 'dark', cx = (safe.left + safe.right) / 2, cy = (safe.top + safe.bottom) / 2;
    const contacts = [...(record?.contacts || [])].sort((a,b)=>String(a.contactLevel).localeCompare(String(b.contactLevel))||String(a.n?.id).localeCompare(String(b.n?.id))), allRegions=contacts.filter(c=>c.contactLevel==='region'), regionById=new Map(allRegions.map(c=>[c.n.id,c])), regions = allRegions.filter(c => hasChartLocation(c.n)), sectors = contacts.filter(c => c.contactLevel === 'sector' && hasChartLocation(c.n) && hasChartLocation(regionById.get(c.regionId)?.n));
    const compact = safe.height < 340;
    const content = {left:safe.left, right:safe.right, top:safe.top + 48, bottom:safe.bottom};
    const project = (x,y) => ({x:cx + (x-cx)*zoom + panX, y:cy + (y-cy)*zoom + panY});
    const bounded = rect => { const r={left:Math.max(content.left,rect.left),right:Math.min(content.right,rect.right),top:Math.max(content.top,rect.top),bottom:Math.min(content.bottom,rect.bottom)}; return r.left<r.right&&r.top<r.bottom?r:null; };
    const positions = [], contactAnchors = [], hitTargets = [], regionLayout = new Map(), sectorLayout = new Map();
    ctx.save(); ctx.beginPath(); ctx.rect(safe.left,safe.top,safe.width,safe.height); ctx.clip();
    drawArtwork(ctx, {safe, dark, time, zoom, panX, panY});

    const caption = 'Known-space atlas · schematic · distances unknown';
    ctx.font = '11px "Noto Instrument Mono",monospace'; ctx.textAlign = 'left';
    const capWidth = Math.min(safe.width - 24, ctx.measureText(caption).width + 18);
    ctx.fillStyle = dark ? 'rgba(4,13,24,.72)' : 'rgba(245,248,246,.8)';
    ctx.fillRect(safe.left + 12, safe.top + 10, capWidth, 24);
    ctx.fillStyle = dark ? '#c3d1d5' : '#344b56'; ctx.fillText(caption, safe.left + 21, safe.top + 26, capWidth - 18);

    if (compact) {
      const columns = Math.max(1, Math.min(contacts.length, Math.floor(safe.width / 205))), cell = safe.width / columns;
      [...regions,...sectors].forEach((contact, i) => {
        const row = Math.floor(i / columns), x = safe.left + cell * (i % columns + .5), y = content.top + 25 + row * 140 + (contact.contactLevel === 'sector' ? 12 : 0);
        (contact.contactLevel === 'region' ? regionLayout : sectorLayout).set(contact.n.id, {x,y,contact});
      });
    } else {
      const orbitX = Math.min(safe.width * .31, Math.max(140, safe.width * .28));
      const orbitY = Math.min(safe.height * .23, Math.max(80, safe.height * .21));
      regions.forEach((contact, i) => {
        const angle = -Math.PI / 2 + (Math.PI * 2 * i / Math.max(1, regions.length)) + .12;
        const x = cx + Math.cos(angle) * orbitX, y = cy + 20 + Math.sin(angle) * orbitY;
        regionLayout.set(contact.n.id, {x,y,contact,angle});
        const children = sectors.filter(s => s.regionId === contact.n.id);
        const radiusX = Math.min(safe.width * .24, Math.max(150, safe.width * .17));
        const radiusY = Math.min(safe.height * .22, Math.max(100, safe.height * .18));
        const horizontalInset = Math.min(110, safe.width / 2);
        children.forEach((sector, j) => {
          const spread = Math.min(Math.PI * .9, .62 + children.length * .22);
          const a = angle + Math.PI + (children.length === 1 ? 0 : ((j / (children.length - 1)) - .5) * spread);
          const sx = Math.max(safe.left + horizontalInset, Math.min(safe.right - horizontalInset, x + Math.cos(a) * radiusX));
          const sy = Math.max(content.top + 62, Math.min(content.bottom - 58, y + Math.sin(a) * radiusY));
          sectorLayout.set(sector.n.id, {x:sx, y:sy, contact:sector});
        });
      });
    }

    // An open bracket labels a list of children, never a territorial footprint.
    if (!compact) {
      for (const region of regions) {
        const children = sectors.filter(sector => sector.regionId === region.n.id).map(sector => sectorLayout.get(sector.n.id)).filter(Boolean).map(slot => project(slot.x, slot.y));
        if (!children.length) continue;
        const left = Math.min(...children.map(point => point.x)) - 115, right = Math.max(...children.map(point => point.x)) + 115, top = Math.min(...children.map(point => point.y)) - 41;
        ctx.strokeStyle = dark ? 'rgba(169,199,205,.48)' : 'rgba(58,83,90,.45)'; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(left,top+8); ctx.lineTo(left,top); ctx.lineTo(right,top); ctx.lineTo(right,top+8); ctx.stroke();
        ctx.fillStyle = dark ? '#d7c69e' : '#675638'; ctx.font = '12px "Noto Instrument Mono",monospace'; ctx.textAlign = 'center';
        ctx.fillText(`Known sectors in ${region.n.name || 'Region'}`, (left+right)/2, top-9, Math.max(180,right-left+60));
      }
    }

    // One restrained focus sweep can frame a selected region or its selected sector.
    if (!compact && selectedContactId) {
      const selectedSector = sectors.find(contact => contact.n.id === selectedContactId);
      const focusedRegion = regionLayout.get(selectedSector?.regionId || selectedContactId);
      if (focusedRegion) {
        const p = project(focusedRegion.x, focusedRegion.y);
        ctx.strokeStyle = dark ? 'rgba(132,180,202,.2)' : 'rgba(71,119,139,.2)'; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.ellipse(p.x,p.y,48,28,0,0,Math.PI*2); ctx.stroke();
      }
    }

    const drawContact = (slot, level) => {
      const {n} = slot.contact, p = project(slot.x, slot.y), selected = n.id === selectedContactId, origin = originContactIds.includes(n.id);
      const detected = n.knowledge === 'detected', located=hasChartLocation(n), color = origin ? (dark ? '#8fc8ee' : '#28668b') : level === 'region' ? (dark ? '#f1c777' : '#7b5930') : detected ? (dark ? '#e0b56d' : '#805b20') : (dark ? '#9dd7e1' : '#426d77');
      const label = n.name || `${level === 'region' ? 'Region' : 'Sector'} · name unrecorded`;
      const knowledge=detected?'Detected':n.knowledge==='surveyed'?'Surveyed':'Knowledge unknown',position=located?'':' · Position unknown';
      const type = `${level === 'region' ? 'Region' : 'Sector'} · ${knowledge}${position}`;
      ctx.save(); ctx.shadowColor = color; ctx.shadowBlur = dark ? (level === 'region' ? 15 : 8) : 4;
      ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = level === 'region' ? 1.7 : 1.4;
      if (level === 'region') { ctx.beginPath(); ctx.arc(p.x,p.y,7,0,Math.PI*2); ctx.fill(); ctx.beginPath(); ctx.arc(p.x,p.y,14,0,Math.PI*2); ctx.stroke(); }
      else if (detected) { ctx.strokeRect(p.x-5,p.y-5,10,10); }
      else { ctx.fillRect(p.x-4,p.y-4,8,8); }
      if (origin) { ctx.beginPath();ctx.arc(p.x,p.y,level==='region'?19:13,0,Math.PI*2);ctx.stroke(); }
      ctx.restore();
      ctx.textAlign='center'; ctx.font=`600 ${level==='region'?13:12}px "Noto Instrument Mono",monospace`; ctx.fillStyle=dark?'#f0f4f3':'#233941';
      const nameWidth = ctx.measureText(label).width, maxLabel = Math.max(110, Math.min(220, safe.width / (compact ? 2 : Math.max(2, regions.length))));
      ctx.fillText(label,p.x,p.y+(level==='region'?34:20),maxLabel);
      ctx.font='11px "Noto Instrument Mono",monospace'; ctx.fillStyle=detected?(dark?'#e1c18a':'#77571f'):(dark?'#b5cbd1':'#4f6971');
      const typeWidth=ctx.measureText(type).width; ctx.fillText(type,p.x,p.y+(level==='region'?49:35),maxLabel);
      let parentWidth=0;
      if (level==='sector') {
        const parent=regionById.get(slot.contact.regionId)?.n;
        const parentLine=`Within ${parent?.name||'Region · name unrecorded'}`;
        ctx.font='11px "Noto Instrument Mono",monospace';ctx.fillStyle=dark?'#a4bac4':'#596f76';
        parentWidth=ctx.measureText(parentLine).width;ctx.fillText(parentLine,p.x,p.y+50,maxLabel);
      }
      const width=Math.min(maxLabel,Math.max(112,nameWidth+12,typeWidth+12,parentWidth+12)), frameRect={left:Math.max(safe.left,p.x-width/2-6),right:Math.min(safe.right,p.x+width/2+6),top:Math.max(content.top,p.y-(level==='region'?30:23)),bottom:Math.min(content.bottom,p.y+60)}, hit=bounded(frameRect);
      if (selected) {
        const color=dark?'rgba(244,249,251,.96)':'rgba(31,61,71,.94)',arm=8;
        ctx.strokeStyle=color;ctx.lineWidth=1.4;ctx.beginPath();
        for(const [x,y,sx,sy] of [[frameRect.left,frameRect.top,1,1],[frameRect.right,frameRect.top,-1,1],[frameRect.left,frameRect.bottom,1,-1],[frameRect.right,frameRect.bottom,-1,-1]]){ctx.moveTo(x+sx*arm,y);ctx.lineTo(x,y);ctx.lineTo(x,y+sy*arm);}
        ctx.stroke();
        const tagX=Math.max(content.left+3,Math.min(content.right-109,p.x+28)),tagY=Math.max(content.top+12,Math.min(content.bottom-6,p.y-2));
        ctx.fillStyle=dark?'rgba(5,14,22,.9)':'rgba(245,248,246,.94)';ctx.fillRect(tagX-3,tagY-11,112,17);
        ctx.fillStyle=color;ctx.textAlign='left';ctx.font='700 11px "Noto Instrument Mono",monospace';ctx.fillText('DESTINATION',tagX,tagY,108);
      }
      if (origin) {
        ctx.font='600 11px "Noto Instrument Mono",monospace';ctx.fillStyle=dark?'#8fc8ee':'#28668b';
        const x=Math.max(content.left,Math.min(content.right,p.x-28)),available=x-content.left;
        ctx.textAlign='right';ctx.fillText(`Origin: ${originName}`,x,p.y+4,Math.max(1,Math.min(220,available)));
      }
      const target={id:n.id,n,...p,baseX:slot.x,baseY:slot.y,anchorX:p.x,anchorY:p.y,radius:level==='region'?17:12,frameRect,hitRect:hit,contactLevel:level,regionId:slot.contact.regionId||n.id};
      contactAnchors.push(target);
      if(hit && p.x>=content.left && p.x<=content.right && p.y>=content.top && p.y<=content.bottom) positions.push(target);
    };
    for (const slot of regionLayout.values()) drawContact(slot,'region');
    for (const slot of sectorLayout.values()) drawContact(slot,'sector');
    // Detected contacts have no known chart position. Keep them selectable from
    // an explicit list, without creating a coordinate anchor for the chart.
    const unlocated=contacts.filter(contact=>!hasChartLocation(contact.n)||(contact.contactLevel==='sector'&&!hasChartLocation(regionById.get(contact.regionId)?.n)));
    if (unlocated.length) {
      const width=Math.min(310,safe.width-24),left=safe.right-width-12,top=safe.top+49,row=48;
      const bottom=Math.min(safe.bottom-8,top+30+row*unlocated.length);
      ctx.fillStyle=dark?'rgba(4,13,24,.95)':'rgba(245,248,246,.97)';ctx.fillRect(left,top,width,bottom-top);
      ctx.strokeStyle=dark?'rgba(224,181,109,.55)':'rgba(128,91,32,.5)';ctx.strokeRect(left,top,width,bottom-top);
      ctx.textAlign='left';ctx.font='600 12px "Noto Instrument Mono",monospace';ctx.fillStyle=dark?'#e1c18a':'#77571f';ctx.fillText('UNLOCATED · POSITION UNKNOWN',left+12,top+20,width-24);
      unlocated.forEach((contact,index)=>{
        const y=top+30+index*row;if(y+row>bottom)return;
        const parent=contact.contactLevel==='sector'?(regionById.get(contact.regionId)?.n.name||'Region unknown'):'Parent unknown';
        ctx.font='12px "Noto Instrument Mono",monospace';ctx.fillStyle=dark?'#f0f4f3':'#233941';ctx.fillText(contact.n.name||`${contact.contactLevel} · name unknown`,left+12,y+16,width-24);
        ctx.font='11px "Noto Instrument Mono",monospace';ctx.fillStyle=dark?'#c1b291':'#665a45';ctx.fillText(`${contact.contactLevel} · in ${parent}`,left+12,y+33,width-24);
        hitTargets.push({id:contact.n.id,n:contact.n,uiOnly:true,x:left+width/2,y:y+row/2,hitRect:{left:left+4,right:left+width-4,top:y,bottom:y+row}});
      });
    }
    if (!contacts.length) { ctx.textAlign='center'; ctx.font='600 13px "Noto Instrument Mono",monospace'; ctx.fillStyle=dark?'#d2dbdf':'#34464a'; ctx.fillText('No regions or sectors are recorded',cx,cy-7); }
    ctx.restore();
    return {hierarchy:true,universe:true,positions,hitTargets:[...positions,...hitTargets],contactAnchors,safeRect:safe,sceneRect:safe,model:{contacts}};
  }

  function drawStrategic(ctx,{w,h,record,publicState,safe,zoom=1,panX=0,panY=0,theme='dark',forceControlRect=null}) {
    const dark=theme==='dark',level=record?.level==='sector'?'sector':'galactic',short=safe.height<420;
    const nodes=(publicState?.nodes||[]).filter(node=>node.knowledge!=='hidden'),byId=new Map(nodes.map(node=>[node.id,node]));
    const parent=record?.parent||byId.get(record?.parent_id)||null;
    const descendants=id=>nodes.filter(node=>node.kind==='system'&&node.parent_id===id);
    const rawGroups=level==='galactic'?(record?.groups||[]).filter(group=>group.region&&group.region.knowledge!=='hidden'):[{region:byId.get(parent?.parent_id),sectors:[parent]}];
    const allSectors=rawGroups.flatMap(group=>(group.sectors||[]).filter(node=>node&&node.knowledge!=='hidden').map(sector=>({sector,region:group.region})));
    const isLocated=entry=>hasChartLocation(entry.sector)&&(level==='sector'||hasChartLocation(entry.region));
    const groups=allSectors.filter(isLocated).map(entry=>({...entry,systems:descendants(entry.sector.id)})).sort((a,b)=>String(a.sector.id).localeCompare(String(b.sector.id)));
    const systems=allSectors.flatMap(entry=>descendants(entry.sector.id));
    const unlocated=[...new Map(allSectors.flatMap(entry=>isLocated(entry)?descendants(entry.sector.id).filter(node=>!hasChartLocation(node)):[entry.sector,...descendants(entry.sector.id)]).map(node=>[node.id,node])).values()];
    const links=(publicState?.links||record?.links||[]).filter(link=>byId.get(link.a)?.kind==='system'&&byId.get(link.b)?.kind==='system');
    const bright=dark?'#edf3f1':'#263d43',muted=dark?'#b8cbd0':'#52676c',edge=dark?'rgba(169,199,205,.43)':'rgba(58,83,90,.4)';
    const centerX=(safe.left+safe.right)/2,centerY=(safe.top+safe.bottom)/2;
    const project=(x,y)=>({x:centerX+(x-centerX)*zoom+panX,y:centerY+(y-centerY)*zoom+panY});
    const bounded=rect=>{const r={left:Math.max(safe.left,rect.left),right:Math.min(safe.right,rect.right),top:Math.max(safe.top,rect.top),bottom:Math.min(safe.bottom,rect.bottom)};return r.left<r.right&&r.top<r.bottom?r:null;};
    ctx.fillStyle=dark?'#07111c':'#e7ecea';ctx.fillRect(0,0,w,h);ctx.save();ctx.beginPath();ctx.rect(safe.left,safe.top,safe.width,safe.height);ctx.clip();
    drawArtwork(ctx,{safe,dark,time:0,panX,panY});
    ctx.fillStyle=dark?'rgba(4,10,19,.83)':'rgba(227,233,233,.83)';ctx.fillRect(safe.left,safe.top,safe.width,safe.height);
    const trayWidth=Math.min(330,Math.max(220,safe.width*.27)),trayLeft=safe.right-trayWidth-12;
    const trayTop=Math.max(safe.top+18,forceControlRect&&forceControlRect.right>trayLeft?forceControlRect.bottom+12:safe.top+18);
    const chartRight=unlocated.length&&safe.width>650?trayLeft-28:safe.right-24;
    const chartWidth=Math.max(150,chartRight-safe.left-24),cols=Math.max(1,Math.floor(chartWidth/360));
    const regionGroups=[...new Set(groups.map(group=>group.region?.id||'unknown'))].map(id=>({region:groups.find(group=>(group.region?.id||'unknown')===id)?.region,sectors:groups.filter(group=>(group.region?.id||'unknown')===id)}));
    const frameW=Math.min(520,chartWidth/Math.min(cols,Math.max(1,groups.length))),frameH=Math.max(short?128:300,...groups.map(group=>(short?24:170)+Math.ceil(group.systems.filter(hasChartLocation).length/Math.max(1,Math.ceil(Math.sqrt(group.systems.filter(hasChartLocation).length))))*(short?128:170)));
    const contentWidth=Math.min(chartWidth,frameW*Math.min(cols,Math.max(1,groups.length))),contentLeft=safe.left+24+(chartWidth-contentWidth)/2;
    const blockHeight=block=>(short?30:65)+Math.ceil(block.sectors.length/cols)*frameH;
    const totalHeight=regionGroups.reduce((sum,block)=>sum+blockHeight(block),0),layout=new Map();
    let blockTop=safe.top+(short?18:65)+Math.max(0,(safe.height-(short?30:85)-totalHeight)/2);
    const coords=new Map(),positions=[],contactAnchors=[],forceObstacles=[];
    for(const block of regionGroups){
      const start=project(contentLeft,blockTop),height=blockHeight(block),width=contentWidth*zoom;
      ctx.fillStyle=dark?'rgba(13,32,45,.85)':'rgba(233,242,241,.94)';ctx.fillRect(start.x-14,start.y-24,width+28,height*zoom-12);
      ctx.strokeStyle=edge;ctx.lineWidth=1;ctx.strokeRect(start.x-14,start.y-24,width+28,height*zoom-12);
      ctx.textAlign='left';ctx.font=`700 ${short?15:20}px "Noto Instrument Mono",monospace`;ctx.fillStyle=bright;
      ctx.fillText(level==='galactic'?`${block.region?.name||'Region unknown'} · REGION`:`${parent?.name||'Sector unknown'} · SECTOR`,start.x,start.y,width-20);
      if(!short){ctx.font='12px "Noto Instrument Mono",monospace';ctx.fillStyle=muted;ctx.fillText(level==='galactic'?`${block.sectors.length} charted ${block.sectors.length===1?'sector':'sectors'} · known containment`:`Within ${block.region?.name||'Region unknown'} · recorded systems`,start.x,start.y+23,width-20);}
      block.sectors.forEach((group,index)=>layout.set(group,{left:contentLeft+(index%cols)*frameW,top:blockTop+(short?30:65)+Math.floor(index/cols)*frameH}));
      const obstacle=bounded({left:start.x-14,right:start.x+width+14,top:start.y-24,bottom:start.y+30});if(obstacle)forceObstacles.push(obstacle);
      blockTop+=height;
    }
    if(!short){ctx.textAlign='left';ctx.font='700 12px "Noto Instrument Mono",monospace';ctx.fillStyle=bright;
    ctx.fillText(level==='galactic'?'GALACTIC · REGIONS CONTAIN SECTORS':'SECTOR · RECORDED SYSTEMS',safe.left+24,safe.top+21,Math.max(160,chartWidth));
    ctx.font='11px "Noto Instrument Mono",monospace';ctx.fillStyle=muted;ctx.fillText('KNOWN CONTACTS · SCHEMATIC · DISTANCES UNKNOWN',safe.left+24,safe.top+39,Math.max(160,chartWidth));}
    groups.forEach((group,index)=>{
      const {left,top}=layout.get(group);
      const p=project(left,top),count=group.systems.filter(node=>node.knowledge==='surveyed').length;
      ctx.font='600 15px "Noto Instrument Mono",monospace';ctx.fillStyle=bright;ctx.textAlign='left';
      if(!short||level==='galactic')ctx.fillText(level==='galactic'?`${group.sector.name||'Name unknown'} · SECTOR`:'RECORDED SYSTEMS',p.x,p.y,frameW-30);
      ctx.font='12px "Noto Instrument Mono",monospace';ctx.fillStyle=muted;
      if(!short){ctx.fillText(`${count} surveyed ${count===1?'system':'systems'}`,p.x,p.y+22,frameW-30);
      ctx.strokeStyle=edge;ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(p.x,p.y+34);ctx.lineTo(p.x+Math.min(360,frameW-30)*zoom,p.y+34);ctx.stroke();}
      const children=group.systems.filter(hasChartLocation).sort((a,b)=>String(a.id).localeCompare(String(b.id))),columns=Math.max(1,Math.ceil(Math.sqrt(children.length)));
      children.forEach((node,i)=>{
        const x=left+Math.min(360*columns,frameW-30)*(i%columns+.5)/columns,y=top+(short?24:100)+Math.floor(i/columns)*(short?128:170),point=project(x,y);
        const labelWidth=Math.min(300,Math.max(130,frameW/columns-20));
        const hitRect=bounded({left:point.x-labelWidth/2-8,right:point.x+labelWidth/2+8,top:point.y-25,bottom:point.y+(short?88:124)});
        const anchor={id:node.id,n:node,...point,baseX:x,baseY:y,anchorX:point.x,anchorY:point.y,radius:16,contactLevel:'system',regionId:group.sector.id,labelWidth,hitRect};
        coords.set(node.id,anchor);contactAnchors.push(anchor);
        if(hitRect&&point.x>=safe.left&&point.x<=safe.right&&point.y>=safe.top&&point.y<=safe.bottom)positions.push(anchor);
      });
    });
    // Only located systems have geometric endpoints. A known link to an
    // unlocated contact is described in the list, never drawn into its UI row.
    ctx.strokeStyle=dark?'rgba(139,190,207,.76)':'rgba(52,112,130,.76)';ctx.lineWidth=1.5;ctx.beginPath();
    for(const link of links){const a=coords.get(link.a),b=coords.get(link.b);if(a&&b){ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);}}ctx.stroke();
    for(const point of positions){
      const {n,x,y,labelWidth}=point;
      const childPlanets=nodes.filter(node=>node.kind==='planet'&&node.parent_id===n.id);
      const childLines=[];
      for(const [knowledge,label] of [['surveyed','Surveyed planets'],['detected','Detected planets']]) {
        const children=childPlanets.filter(node=>node.knowledge===knowledge);
        if(children.length)childLines.push(`${label} · ${children.map(node=>node.name||'Name unrecorded').join(', ')}`);
      }
      const otherChildren=childPlanets.filter(node=>!['surveyed','detected'].includes(node.knowledge));
      if(otherChildren.length)childLines.push(`Known planets · ${otherChildren.map(node=>node.name||'Name unrecorded').join(', ')}`);
      if(!childLines.length)childLines.push('No public planet records');
      // This is an annotated system symbol. Child names are a public record
      // list, never planetary positions or a claim of a complete system census.
      ctx.fillStyle=dark?'rgba(4,13,24,.88)':'rgba(245,248,246,.92)';
      ctx.fillRect(x-labelWidth/2-6,y+(short?12:20),labelWidth+12,short?75:103);
      ctx.strokeStyle=dark?'#9dd7e1':'#426d77';ctx.fillStyle=ctx.strokeStyle;ctx.lineWidth=1.5;
      ctx.beginPath();ctx.arc(x,y,13,0,Math.PI*2);ctx.stroke();
      ctx.beginPath();ctx.arc(x,y,6,0,Math.PI*2);ctx.stroke();ctx.fillRect(x-2,y-2,4,4);
      ctx.fillRect(x-21,y-.5,5,1);ctx.fillRect(x+16,y-.5,5,1);ctx.fillRect(x-.5,y-21,1,5);ctx.fillRect(x-.5,y+16,1,5);
      ctx.font='600 15px "Noto Instrument Mono",monospace';ctx.textAlign='center';ctx.fillStyle=bright;
      ctx.fillText(n.name||'System · name unknown',x,y+(short?28:39),labelWidth);
      ctx.font='11px "Noto Instrument Mono",monospace';ctx.fillStyle=muted;
      ctx.fillText(`System · ${n.knowledge==='surveyed'?'Surveyed':'Known'}`,x,y+(short?44:57),labelWidth);
      ctx.font='12px "Noto Instrument Mono",monospace';
      childLines.slice(0,short?1:2).forEach((line,index)=>{
        let visible=line;
        while(visible.length>1&&ctx.measureText(visible).width>labelWidth-8)visible=visible.slice(0,-1);
        if(visible!==line)visible=visible.slice(0,-1)+'…';
        ctx.fillText(visible,x,y+(short?61:78)+index*17,labelWidth);
      });
      ctx.font='600 12px "Noto Instrument Mono",monospace';ctx.fillStyle=dark?'#a7d3e0':'#356f80';
      ctx.fillText('Open system ›',x,y+(short?80:115),labelWidth);
      if(n.id===record?.selected_id){ctx.strokeStyle=dark?'#f1c777':'#7b5930';ctx.lineWidth=1;ctx.strokeRect(point.hitRect.left,point.hitRect.top,point.hitRect.right-point.hitRect.left,point.hitRect.bottom-point.hitRect.top);}
      forceObstacles.push(point.hitRect);
    }
    const hitTargets=positions.slice();
    if(unlocated.length){
      const left=trayLeft,width=trayWidth,top=trayTop;
      const rows=unlocated.map(node=>{const knownLinks=links.filter(link=>link.a===node.id||link.b===node.id).map(link=>byId.get(link.a===node.id?link.b:link.a)).filter(Boolean);return{node,knownLinks,height:knownLinks.length?72:52};});
      const height=Math.min(safe.bottom-top-10,40+rows.reduce((total,row)=>total+row.height,0));
      ctx.fillStyle=dark?'rgba(4,13,24,.95)':'rgba(245,248,246,.97)';ctx.fillRect(left,top,width,height);
      ctx.strokeStyle=dark?'rgba(224,181,109,.55)':'rgba(128,91,32,.5)';ctx.strokeRect(left,top,width,height);
      ctx.textAlign='left';ctx.font='600 12px "Noto Instrument Mono",monospace';ctx.fillStyle=dark?'#e1c18a':'#77571f';ctx.fillText('UNLOCATED · POSITION UNKNOWN',left+12,top+23,width-24);
      let y=top+38;
      for(const row of rows){
        if(y+row.height>top+height)break;
        const {node,knownLinks}=row,parentNode=byId.get(node.parent_id)||allSectors.find(entry=>entry.sector.id===node.id)?.region;
        ctx.font='12px "Noto Instrument Mono",monospace';ctx.fillStyle=bright;ctx.fillText(node.name||`${node.kind} · name unknown`,left+12,y+15,width-24);
        ctx.font='11px "Noto Instrument Mono",monospace';ctx.fillStyle=muted;ctx.fillText(`${node.kind} · in ${parentNode?.name||'Parent unknown'}`,left+12,y+32,width-24);
        if(knownLinks.length){ctx.fillStyle=dark?'#a7d3e0':'#356f80';ctx.fillText(`Known link: ${knownLinks.map(item=>item.name||'Unnamed system').join(', ')}`,left+12,y+50,width-24);}
        const hitRect=bounded({left:left+4,right:left+width-4,top:y,bottom:y+row.height});
        if(hitRect)hitTargets.push({n:node,id:node.id,uiOnly:true,x:left+width/2,y:y+row.height/2,hitRect});
        y+=row.height;
      }
      forceObstacles.push({left,right:left+width,top,bottom:top+height});
    }
    if(!groups.length){ctx.font='600 13px "Noto Instrument Mono",monospace';ctx.textAlign='left';ctx.fillStyle=bright;ctx.fillText(level==='galactic'?'No located sectors are recorded':'No located systems are recorded',safe.left+24,safe.top+75,chartWidth);}
    ctx.restore();if(forceControlRect)forceObstacles.push(forceControlRect);
    return{hierarchy:true,positions,hitTargets,safeRect:safe,sceneRect:safe,contactAnchors,forceObstacles,model:{groups,systems,links}};
  }

  function galacticContext(nodes=[],nodeId=null){
    const visible=nodes.filter(node=>node.knowledge!=='hidden'),byId=new Map(visible.map(node=>[node.id,node])),chain=[],seen=new Set();
    let node=byId.get(nodeId);
    while(node&&!seen.has(node.id)){seen.add(node.id);chain.unshift(node);node=byId.get(node.parent_id);}
    const galaxies=visible.filter(node=>node.kind==='galaxy'),galaxy=chain.find(node=>node.kind==='galaxy')||(galaxies.length===1?galaxies[0]:null);
    return {galaxy,chain,name:galaxy?.name||(galaxies.length>1?'Known galaxies':'Galactic chart')};
  }
  const api = {fromGalactic, draw, drawStrategic, galacticContext, strategicRecordLabel};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (typeof window !== 'undefined') window.HWUniverseView = api;
})();
