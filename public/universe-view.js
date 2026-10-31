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

  function hash(value) {
    let h = 2166136261;
    for (const char of String(value)) h = Math.imul(h ^ char.charCodeAt(0), 16777619);
    return h >>> 0;
  }
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

  function draw(ctx, {w,h,record,safe,zoom=1,panX=0,panY=0,theme='dark',selectedContactId=null,originContactIds=[],time=0}) {
    const dark = theme === 'dark', cx = (safe.left + safe.right) / 2, cy = (safe.top + safe.bottom) / 2;
    const contacts = record?.contacts || [], regions = contacts.filter(c => c.contactLevel === 'region'), sectors = contacts.filter(c => c.contactLevel === 'sector');
    const compact = safe.height < 340;
    const content = {left:safe.left, right:safe.right, top:safe.top + 48, bottom:safe.bottom};
    const project = (x,y) => ({x:cx + (x-cx)*zoom + panX, y:cy + (y-cy)*zoom + panY});
    const bounded = rect => { const r={left:Math.max(content.left,rect.left),right:Math.min(content.right,rect.right),top:Math.max(content.top,rect.top),bottom:Math.min(content.bottom,rect.bottom)}; return r.left<r.right&&r.top<r.bottom?r:null; };
    const positions = [], contactAnchors = [], regionLayout = new Map(), sectorLayout = new Map();
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
      contacts.forEach((contact, i) => {
        const row = Math.floor(i / columns), x = safe.left + cell * (i % columns + .5), y = content.top + 25 + row * 91 + (contact.contactLevel === 'sector' ? 12 : 0);
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
      const detected = n.knowledge === 'detected', color = origin ? (dark ? '#8fc8ee' : '#28668b') : level === 'region' ? (dark ? '#f1c777' : '#7b5930') : detected ? (dark ? '#e0b56d' : '#805b20') : (dark ? '#9dd7e1' : '#426d77');
      const label = n.name || `${level === 'region' ? 'Region' : 'Sector'} · name unrecorded`;
      const type = level === 'region' ? `Region · ${detected ? 'Detected · Position unknown' : 'Surveyed'}` : `Sector · ${detected ? 'Detected · unlocated' : 'Surveyed'}`;
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
      ctx.font='10px "Noto Instrument Mono",monospace'; ctx.fillStyle=detected?(dark?'#e1c18a':'#77571f'):(dark?'#b5cbd1':'#4f6971');
      const typeWidth=ctx.measureText(type).width; ctx.fillText(type,p.x,p.y+(level==='region'?49:35),maxLabel);
      let parentWidth=0;
      if (level==='sector') {
        const parent=regions.find(contact=>contact.n.id===slot.contact.regionId)?.n;
        const parentLine=`Within ${parent?.name||'Region · name unrecorded'}`;
        ctx.font='10px "Noto Instrument Mono",monospace';ctx.fillStyle=dark?'#a4bac4':'#596f76';
        parentWidth=ctx.measureText(parentLine).width;ctx.fillText(parentLine,p.x,p.y+50,maxLabel);
      }
      const width=Math.min(maxLabel,Math.max(112,nameWidth+12,typeWidth+12,parentWidth+12)), frameRect={left:Math.max(safe.left,p.x-width/2-6),right:Math.min(safe.right,p.x+width/2+6),top:Math.max(content.top,p.y-(level==='region'?30:23)),bottom:Math.min(content.bottom,p.y+60)}, hit=bounded(frameRect);
      if (selected) {
        const color=dark?'rgba(244,249,251,.96)':'rgba(31,61,71,.94)',arm=8;
        ctx.strokeStyle=color;ctx.lineWidth=1.4;ctx.beginPath();
        for(const [x,y,sx,sy] of [[frameRect.left,frameRect.top,1,1],[frameRect.right,frameRect.top,-1,1],[frameRect.left,frameRect.bottom,1,-1],[frameRect.right,frameRect.bottom,-1,-1]]){ctx.moveTo(x+sx*arm,y);ctx.lineTo(x,y);ctx.lineTo(x,y+sy*arm);}
        ctx.stroke();
        const tagX=p.x+(level==='region'?23:14),tagY=Math.max(content.top+12,Math.min(content.bottom-4,p.y-(level==='region'?20:16)));
        ctx.fillStyle=dark?'rgba(5,14,22,.9)':'rgba(245,248,246,.94)';ctx.fillRect(tagX-3,tagY-11,37,14);
        ctx.fillStyle=color;ctx.textAlign='left';ctx.font='700 9px "Noto Instrument Mono",monospace';ctx.fillText('DEST',tagX,tagY);
      }
      const target={id:n.id,n,...p,baseX:slot.x,baseY:slot.y,anchorX:p.x,anchorY:p.y,radius:level==='region'?17:12,frameRect,hitRect:hit,contactLevel:level,regionId:slot.contact.regionId||n.id};
      contactAnchors.push(target);
      if(hit) positions.push(target);
    };
    for (const slot of regionLayout.values()) drawContact(slot,'region');
    for (const slot of sectorLayout.values()) drawContact(slot,'sector');
    if (!contacts.length) { ctx.textAlign='center'; ctx.font='600 13px "Noto Instrument Mono",monospace'; ctx.fillStyle=dark?'#d2dbdf':'#34464a'; ctx.fillText('No regions or sectors are recorded',cx,cy-7); }
    ctx.restore();
    return {hierarchy:true,universe:true,positions,hitTargets:positions,contactAnchors,safeRect:safe,sceneRect:safe,model:{contacts}};
  }

  const api = {fromGalactic, draw};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (typeof window !== 'undefined') window.HWUniverseView = api;
})();
