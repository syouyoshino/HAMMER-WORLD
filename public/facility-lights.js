(() => {
  "use strict";
  const facilityOrder = (a, b) => String(a.id ?? "").localeCompare(String(b.id ?? "")) || String(a.kind ?? "").localeCompare(String(b.kind ?? ""));
  const kindOf = value => String(value || "facility").toLowerCase().replace(/[^a-z0-9_-]/g, "");
  function model({geometry, planetId=geometry?.planet?.id || geometry?.planet_id, settlements=[], facilities=[], turn, provinceLand}={}) {
    if (!geometry?.planet || !Number.isFinite(turn) || !Number.isInteger(turn) || turn < 0) return [];
    const planet = geometry.planet;
    if (!planetId || !Array.isArray(settlements) || !Array.isArray(facilities)) return [];
    const land = provinceLand instanceof Map ? provinceLand : new Map();
    const sites = new Map(settlements.filter(s => s?.owned === true && s.planet_id === planetId && s.id && s.province_id)
      .map(s => [s.id, s]));
    return facilities.filter(f => {
      const active = f?.active_turn;
      return Boolean(f?.id) && f.completed === true && Number.isFinite(active) && Number.isInteger(active) && active >= 0 && active <= turn && sites.has(f.settlement_id);
    }).map(f => {
      const settlement = sites.get(f.settlement_id), province = land.get(settlement.province_id), anchor = province?.anchor;
      if (!anchor || !Number.isFinite(anchor.x) || !Number.isFinite(anchor.y) || anchor.terrain === "ocean" ||
        !(planet.width > 0 && planet.height > 0) || anchor.x + .5 < 0 || anchor.x + .5 >= planet.width ||
        anchor.y + .5 < 0 || anchor.y + .5 >= planet.height) return null;
      return {id: String(f.id ?? ""), kind: kindOf(f.kind), settlementId: settlement.id,
        provinceId: settlement.province_id, x: anchor.x + .5, y: anchor.y + .5};
    }).filter(Boolean).sort(facilityOrder);
  }
  function pattern(kind, index=0) {
    const layouts = {
      factory: [[-.62,-.38],[-.31,-.38],[0,-.38],[.31,-.38],[.62,-.38],[-.62,.38],[-.31,.38],[0,.38],[.31,.38],[.62,.38]],
      refinery: [[-.5,0],[0,0],[.5,0]],
      depot: [[-.65,0],[0,0],[.65,0]],
      settlement: [[-.3,-.3],[.3,-.3],[-.3,.3],[.3,.3]]
    };
    const base = layouts[kind] || [[-.3,0],[.3,0],[0,-.3],[0,.3]];
    return base.map(([x,y], n) => [x,y,n]);
  }
  function paint(ctx, width, height, records, planetWidth, planetHeight) {
    if (!ctx || !(width > 0 && height > 0 && planetWidth > 0 && planetHeight > 0)) return;
    const sx=width/planetWidth, sy=height/planetHeight;
    const groups=new Map();
    for(const record of records){
      // Group by the saved anchor, then give each facility a stable slot inside
      // that anchor. Adding records at another province cannot shift this site.
      const key=`${record.x}:${record.y}`;
      if(!groups.has(key))groups.set(key,[]);
      groups.get(key).push(record);
    }
    const scale=Math.max(1,Math.min(3.2,Math.sqrt(sx*sy))),slot=2.35*scale;
    for(const group of groups.values()){
      group.sort(facilityOrder);
      const columns=Math.min(4,Math.ceil(Math.sqrt(group.length))),rows=Math.ceil(group.length/columns),
        support=(Math.max(columns,rows)-1)*slot/2+1.35*scale;
      const centerX=group[0].x*sx,centerY=group[0].y*sy;
      // Repeat the whole site symbol, with full support, across the longitude seam.
      const copies=[centerX];
      if(centerX-support<0)copies.push(centerX+width);
      if(centerX+support>width)copies.push(centerX-width);
      for(const baseX of copies)group.forEach((record,index)=>{
        const column=index%columns,row=Math.floor(index/columns),
          x=baseX+(column-(columns-1)/2)*slot,y=centerY+(row-(rows-1)/2)*slot,
          halo=.84*scale,kind=record.kind;
        // Small, low-opacity falloff keeps the light cue local and the shapes crisp.
        const glow=ctx.createRadialGradient(x,y,0,x,y,halo);
        glow.addColorStop(0,"rgba(255,179,83,.2)");glow.addColorStop(.55,"rgba(255,146,53,.06)");glow.addColorStop(1,"rgba(255,130,40,0)");
        ctx.fillStyle=glow;ctx.beginPath();ctx.arc(x,y,halo,0,Math.PI*2);ctx.fill();
        ctx.fillStyle="#ffd28d";ctx.strokeStyle="rgba(255,240,203,.88)";ctx.lineWidth=Math.max(.55,.58*scale);
        if(kind==="factory"){
          // Ten compact work bays in paired rows, joined by a visible spine.
          ctx.beginPath();ctx.moveTo(x-.94*scale,y);ctx.lineTo(x+.94*scale,y);ctx.stroke();
          for(const [dx,dy] of pattern(kind))ctx.fillRect(x+dx*scale-.135*scale,y+dy*scale-.1*scale,.27*scale,.2*scale);
        }else if(kind==="refinery"){
          // Three round storage tanks with a short service neck on each.
          for(const [dx,dy] of pattern(kind)){
            const tx=x+dx*scale,ty=y+dy*scale;
            ctx.beginPath();ctx.moveTo(tx,ty-.3*scale);ctx.lineTo(tx,ty-.22*scale);ctx.stroke();
            ctx.beginPath();ctx.arc(tx,ty,.19*scale,0,Math.PI*2);ctx.fill();ctx.stroke();
          }
        }else if(kind==="depot"){
          // Three long, parallel warehouse bars with separated loading bays.
          for(const [dx,dy] of pattern(kind)){
            const wx=x+dx*scale,wy=y+dy*scale;
            ctx.fillRect(wx-.27*scale,wy-.13*scale,.54*scale,.26*scale);
          }
        }else{
          for(const [dx,dy] of pattern(kind)){
            ctx.beginPath();ctx.arc(x+dx*scale,y+dy*scale,.13*scale,0,Math.PI*2);ctx.fill();
          }
        }
      });
    }
  }
  const api={model,pattern,paint};
  if(typeof module!=="undefined"&&module.exports)module.exports=api;
  if(typeof window!=="undefined")window.HWFacilityLights=api;
})();
