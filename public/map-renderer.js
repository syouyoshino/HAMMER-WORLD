(() => {
  "use strict";
  const cache = new WeakMap();
  const palettes = {
    orbital: {ocean:"#143142",coast:"#677f67",plains:"#899164",rock:"#958e76",forest:"#395c42",marsh:"#4f7058"},
    survey: {ocean:"#97b5b9",coast:"#bbc09e",plains:"#bab489",rock:"#a59b83",forest:"#738b68",marsh:"#8b9f82"},
  };
  const dryPalettes = {
    orbital: {
      arid:{ocean:"#604b30",coast:"#90704b",plains:"#ae8950",rock:"#82705b",forest:"#70614b",marsh:"#8b7350"},
      barren:{ocean:"#484644",coast:"#7c756c",plains:"#898278",rock:"#6d6861",forest:"#6d6861",marsh:"#79746c"},
      frozen:{ocean:"#676966",coast:"#afb0aa",plains:"#cacbc5",rock:"#9b9d98",forest:"#969791",marsh:"#b6b7b0"},
    },
    survey: {
      arid:{ocean:"#d4c39d",coast:"#c3a779",plains:"#d0b57a",rock:"#aa9571",forest:"#998461",marsh:"#bba174"},
      barren:{ocean:"#d0cec8",coast:"#b9b5ad",plains:"#c8c4bc",rock:"#99958e",forest:"#99958e",marsh:"#aaa69f"},
      frozen:{ocean:"#e2e1db",coast:"#dad9d3",plains:"#eeede7",rock:"#c7c7c1",forest:"#c5c5bf",marsh:"#d8d8d2"},
    },
  };
  function terrainPalette(style, preset) {
    return dryPalettes[style]?.[preset] || palettes[style] || palettes.orbital;
  }
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  function hash(x, y, salt = 0) {
    let n =
      Math.imul(x + salt * 131, 374761393) +
      Math.imul(y + salt * 17, 668265263);
    n = Math.imul(n ^ (n >>> 13), 1274126177);
    return ((n ^ (n >>> 16)) >>> 0) / 4294967295;
  }
  function surfaceFor(geometry) {
    const s = geometry?.surface;
    if (!s || !["planet-v2", "planet-v3", "planet-v4"].includes(s.version) || !Array.isArray(s.elevation))
      return null;
    return s;
  }
  function baseRaster(geometry, style) {
    let map = cache.get(geometry);
    if (!map) { map = new Map(); cache.set(geometry, map); }
    if (map.has(style)) return map.get(style);
    const { width: cols, height: rows } = geometry.planet,
      scale = 24, w = cols * scale, h = rows * scale,
      surface = surfaceFor(geometry), tiles = geometry.tiles,
      survey = style === "survey",
      colors = surface?.hydrology === "none" ? Object.fromEntries(Object.entries(terrainPalette(style,surface.preset)).map(([key,value])=>[key,[parseInt(value.slice(1,3),16),parseInt(value.slice(3,5),16),parseInt(value.slice(5,7),16)]])) : survey ? {
        ocean: [151,181,185], coast: [187,192,158], plains: [186,180,137],
        rock: [165,155,131], forest: [115,139,104], marsh: [139,159,130],
      } : {
        ocean: [20,49,66], coast: [103,127,103], plains: [137,145,100],
        rock: [149,142,118], forest: [57,92,66], marsh: [79,112,88],
      };
    const canvas = document.createElement("canvas");
    canvas.width = w; canvas.height = h;
    const ctx = canvas.getContext("2d"), img = ctx.createImageData(w, h),
      heights = surface?.elevation, sea = surface?.sea_level ?? 400;
    // Cell centres are authoritative. Interpolation rounds only the subcell
    // transition; it cannot introduce islands, ridges or new drainage paths.
    // Horizontal interpolation is shared by every output row. Keeping these
    // temporary scanlines avoids millions of repeated index/weight calculations
    // and per-pixel colour arrays; the persisted samples and palette are identical.
    const interpolateRows = (field, shift = 0) => {
      const result = new Float64Array(w * rows);
      for (let px=0;px<w;px++) {
        const fx=clamp((px+.5)/scale+shift-.5,0,cols-1),
          ix=Math.floor(fx),tx=fx-ix,next=Math.min(cols-1,ix+1);
        for(let y=0;y<rows;y++) result[y*w+px]=field[y*cols+ix]*(1-tx)+field[y*cols+next]*tx;
      }
      return result;
    };
    const land = interpolateRows(tiles.map(t => t.terrain === "ocean" ? 0 : 1)),
      channels = [0,1,2].map(c => interpolateRows(tiles.map(t => (colors[t.terrain] || colors.plains)[c]))),
      elevation = heights ? interpolateRows(heights) : null,
      heightLeft = heights ? interpolateRows(heights,-.35) : null,
      heightRight = heights ? interpolateRows(heights,.35) : null,
      moisture = surface?.moisture ? interpolateRows(surface.moisture) : null,
      temperature = surface?.temperature ? interpolateRows(surface.temperature) : null,
      shoreColor = survey ? [183,204,197] : [60,102,111],
      deepColor = survey ? [126,161,172] : [12,33,51],
      highColor = surface?.preset==="frozen"?[224,224,219]:survey ? [204,195,163] : [178,164,132],
      wetColor = [54,87,61],coldColor=surface?.preset==="frozen"?[218,218,212]:[204,207,192];
    const vertical = (y) => {
      const fy=clamp(y-.5,0,rows-1),iy=Math.floor(fy);
      return [iy*w,Math.min(rows-1,iy+1)*w,fy-iy];
    };
    for (let py = 0; py < h; py++) {
      const y=(py+.5)/scale,[row0,row1,ty]=vertical(y),
        [up0,up1,upT]=vertical(y-.35),[down0,down1,downT]=vertical(y+.35), inv=1-ty;
      for (let px = 0; px < w; px++) {
        const i=row0+px,j=row1+px,cover=land[i]*inv+land[j]*ty,onLand=cover>=.5,
          elev=elevation?elevation[i]*inv+elevation[j]*ty:sea,
          wet=moisture?moisture[i]*inv+moisture[j]*ty:500,
          temp=temperature?temperature[i]*inv+temperature[j]*ty:500;
        let shade=1,high=0,wetMix=0,coldMix=0,depth=0,shore=0;
        if(!onLand) {
          depth=(heights?clamp((sea-elev)/250,0,1):.45)*.35;
          shore=clamp(cover*1.6,0,.65);
        } else if(heights) {
          const dx=(heightRight[i]*inv+heightRight[j]*ty)-(heightLeft[i]*inv+heightLeft[j]*ty),
            dy=(elevation[down0+px]*(1-downT)+elevation[down1+px]*downT)-(elevation[up0+px]*(1-upT)+elevation[up1+px]*upT);
          shade=1+clamp((-dx*.65-dy*.75)/110,-.32,.3)*(survey?.6:1);
          high=clamp((elev-620)/350,0,1)*.44;
          wetMix=surface?.hydrology==="none"?0:clamp((wet-450)/700,0,.24);
          coldMix=clamp((320-temp)/600,0,.3);
        }
        const grain=(hash(px,py,3)-.5)*(survey?2.2:7),off=(py*w+px)*4;
        for(let c=0;c<3;c++) {
          let color;
          if(!onLand) {
            color=Math.round(colors.ocean[c]*(1-shore)+shoreColor[c]*shore);
            color=Math.round(color*(1-depth)+deepColor[c]*depth);
          } else {
            color=(channels[c][i]*inv+channels[c][j]*ty-colors.ocean[c]*(1-cover))/Math.max(.001,cover);
            if(heights) {
              color=Math.round(color*(1-high)+highColor[c]*high);
              color=Math.round(color*(1-wetMix)+wetColor[c]*wetMix);
              color=Math.round(color*(1-coldMix)+coldColor[c]*coldMix)*shade;
            }
          }
          img.data[off+c]=clamp(color+grain,0,255);
        }
        img.data[off+3]=255;
      }
    }
    ctx.putImageData(img,0,0);
    if (surface) {
      // Contours interpolate the persisted elevation field, without decorative
      // hatching or a synthetic relief field.
      if (survey && surface.hydrology !== "none") {
        ctx.strokeStyle="rgba(64,76,52,.24)"; ctx.lineWidth=.7;
        for(const level of [sea+100,sea+200,sea+300,sea+400,sea+500])
          for(let y=0;y<rows-1;y++) for(let x=0;x<cols-1;x++) {
            const coords=[[x+.5,y+.5],[x+1.5,y+.5],[x+1.5,y+1.5],[x+.5,y+1.5]],
              values=coords.map(([a,b])=>heights[Math.floor(b)*cols+Math.floor(a)]),points=[];
            for(const [a,b] of [[0,1],[1,2],[2,3],[3,0]]) if((values[a]<level)!==(values[b]<level)) {
              const t=(level-values[a])/(values[b]-values[a]);
              points.push([coords[a][0]+(coords[b][0]-coords[a][0])*t,coords[a][1]+(coords[b][1]-coords[a][1])*t]);
            }
            for(let i=0;i+1<points.length;i+=2) {
              ctx.beginPath();ctx.moveTo(points[i][0]*scale,points[i][1]*scale);
              ctx.lineTo(points[i+1][0]*scale,points[i+1][1]*scale);ctx.stroke();
            }
          }
      }
      ctx.strokeStyle=survey?"rgba(52,114,140,.9)":"rgba(94,155,173,.9)";
      ctx.lineWidth=survey?1.3:1.65;ctx.lineCap="round";ctx.lineJoin="round";
      for(const river of surface.rivers || []) {
        const points=river.points;
        if(!Array.isArray(points)||points.length<2)continue;
        const xy=points.map(([x,y])=>[(x+.5)*scale,(y+.5)*scale]);
        ctx.beginPath();ctx.moveTo(...xy[0]);
        // Quadratics stay inside the convex corridor of consecutive recorded
        // segments. Endpoints and confluences remain the persisted points.
        for(let i=1;i<xy.length-1;i++) {
          const before=xy[i-1],at=xy[i],after=xy[i+1],t=.19,
            enter=[at[0]+(before[0]-at[0])*t,at[1]+(before[1]-at[1])*t],
            leave=[at[0]+(after[0]-at[0])*t,at[1]+(after[1]-at[1])*t];
          ctx.lineTo(...enter);ctx.quadraticCurveTo(...at,...leave);
        }
        ctx.lineTo(...xy[xy.length-1]);ctx.stroke();
      }
    }
    map.set(style,canvas);return canvas;
  }
  function drawPlanet(
    ctx,
    {
      geometry,
      w,
      h,
      zoom,
      panX,
      panY,
      style = "orbital",
      theme = "light",
      selectedProvince = null,
      overlay = "terrain",
      compact = false,
      sites = [],
      planetId = null,
      safe = null,
      paintOverlay = null,
    },
  ) {
    const { width: cols, height: rows } = geometry.planet,
      bounds = safe || {left:0,right:w,top:0,bottom:h,width:w,height:h},
      tile = Math.min(bounds.width / cols, bounds.height / rows) * zoom,
      gridW = tile * cols,
      gridH = tile * rows,
      ox = (bounds.left + bounds.right - gridW) / 2 + panX,
      oy = (bounds.top + bounds.bottom - gridH) / 2 + panY;
    const surface=surfaceFor(geometry), preset=surface?.hydrology==="none"?surface.preset:null;
    ctx.fillStyle = preset?terrainPalette(style,preset).ocean:style === "survey" ? "#a6bfc1" : "#142f40";
    ctx.fillRect(0, 0, w, h);
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(baseRaster(geometry, style, theme), ox, oy, gridW, gridH);
    if (paintOverlay) paintOverlay(ctx, { tile, ox, oy });
    const tiles = geometry.tiles,
      provinces = geometry.provinces;
    if (overlay === "provinces") {
      const colors = preset === "arid" ? ["#c0a06c","#ab8b59","#d0b783","#987b53","#c6aa75","#a88e64","#d5c091","#b69b6a"] :
        preset === "barren" ? ["#aaa69f","#8e8a83","#c1bdb5","#9b9790","#b4b0a8","#88847d","#c9c5bd","#a29e97"] :
        preset === "frozen" ? ["#e1e1dc","#c9c9c3","#f0f0eb","#d6d6d0","#bcbcb7","#e7e7e2","#cecec8","#f5f5f0"] : [
          "#91a39a",
          "#b1aa88",
          "#82999a",
          "#c0b9a0",
          "#9a9f83",
          "#b3a38f",
          "#8fa8a3",
          "#c0c2af",
        ],
        indices = new Map(
          provinces.map((province, index) => [province.id, index]),
        );
      for (const item of tiles) {
        if (!item.province_id) continue;
        ctx.fillStyle =
          colors[(indices.get(item.province_id) || 0) % colors.length];
        ctx.fillRect(
          ox + item.x * tile,
          oy + item.y * tile,
          Math.ceil(tile),
          Math.ceil(tile),
        );
      }
    }
    ctx.lineWidth = Math.max(0.8, Math.min(1.15, tile * 0.065));
    ctx.strokeStyle =
      overlay === "provinces"
        ? theme === "dark"
          ? "rgba(226,232,216,.72)"
          : "rgba(48,54,48,.66)"
        : theme === "dark"
          ? "rgba(224,229,215,.28)"
          : "rgba(232,229,195,.16)";
    ctx.beginPath();
    for (const t of tiles) {
      if (!t.province_id) continue;
      const x = ox + t.x * tile,
        y = oy + t.y * tile;
      for (const [dx, dy, edge] of [
        [0, -1, "n"],
        [1, 0, "e"],
        [0, 1, "s"],
        [-1, 0, "w"],
      ]) {
        const nx = t.x + dx,
          ny = t.y + dy,
          n =
            nx >= 0 && ny >= 0 && nx < cols && ny < rows
              ? tiles[ny * cols + nx]
              : null;
        if (n?.province_id && n.province_id !== t.province_id || overlay === "provinces" && !n?.province_id) {
          if (edge === "n") {
            ctx.moveTo(x, y);
            ctx.lineTo(x + tile, y);
          } else if (edge === "e") {
            ctx.moveTo(x + tile, y);
            ctx.lineTo(x + tile, y + tile);
          } else if (edge === "s") {
            ctx.moveTo(x, y + tile);
            ctx.lineTo(x + tile, y + tile);
          } else {
            ctx.moveTo(x, y);
            ctx.lineTo(x, y + tile);
          }
        }
      }
    }
    ctx.stroke();
    if (selectedProvince) {
      ctx.strokeStyle = "#90c9ef";
      ctx.lineWidth = Math.max(2.2, Math.min(3.2, tile * 0.15));
      ctx.beginPath();
      for (const t of tiles) {
        if (t.province_id !== selectedProvince || t.terrain === "ocean")
          continue;
        const x = ox + t.x * tile,
          y = oy + t.y * tile;
        for (const [dx, dy, edge] of [
          [0, -1, "n"],
          [1, 0, "e"],
          [0, 1, "s"],
          [-1, 0, "w"],
        ]) {
          const nx = t.x + dx,
            ny = t.y + dy,
            n =
              nx >= 0 && ny >= 0 && nx < cols && ny < rows
                ? tiles[ny * cols + nx]
                : null;
          if (n?.province_id === selectedProvince && n.terrain !== "ocean")
            continue;
          if (edge === "n") {
            ctx.moveTo(x, y);
            ctx.lineTo(x + tile, y);
          } else if (edge === "e") {
            ctx.moveTo(x + tile, y);
            ctx.lineTo(x + tile, y + tile);
          } else if (edge === "s") {
            ctx.moveTo(x, y + tile);
            ctx.lineTo(x + tile, y + tile);
          } else {
            ctx.moveTo(x, y);
            ctx.lineTo(x, y + tile);
          }
        }
      }
      ctx.stroke();
    }
    const labelFont = Math.max(10, Math.min(12, tile * 0.43));
    ctx.font = `700 ${labelFont}px "Noto Instrument Mono",monospace`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    const safeTop = Math.max(compact ? 202 : 190, (safe?.top ?? 0) + 8),
      safeBottom = Math.min(h - 92, (safe?.bottom ?? h) - 8),
      placed = [], provinceTargets = [];
    const annotations = provinces
      .map((province) => {
        const land = tiles.filter(
          (t) =>
            t.province_id === province.id &&
            t.terrain !== "ocean" &&
            ox + (t.x + 1) * tile > 0 &&
            oy + (t.y + 1) * tile > 0 &&
            ox + t.x * tile < w &&
            oy + t.y * tile < h,
        );
        if (!land.length) return null;
        const cx = land.reduce((s, t) => s + t.x + 0.5, 0) / land.length,
          cy = land.reduce((s, t) => s + t.y + 0.5, 0) / land.length,
          anchor = land.reduce(
            (a, t) =>
              Math.hypot(t.x + 0.5 - cx, t.y + 0.5 - cy) <
              Math.hypot(a.x + 0.5 - cx, a.y + 0.5 - cy)
                ? t
                : a,
            land[0],
          ),
          holdings = sites.filter(
            (site) =>
              site.planet_id === planetId && site.province_id === province.id,
          );
        if ((compact || zoom < 1.65 && overlay !== "provinces") && !holdings.length && province.id !== selectedProvince)
          return null;
        const names = holdings.map((site) => site.name || "Settlement"),
          label = names.length
            ? names.join(" + ")
            : province.name;
        return {
          province,
          anchor,
          holdings,
          label,
          x: ox + (anchor.x + 0.5) * tile,
          y: oy + (anchor.y + 0.5) * tile,
        };
      })
      .filter(Boolean)
      .sort(
        (a, b) =>
          Number(b.holdings.length > 0) - Number(a.holdings.length > 0) ||
          Number(b.province.id === selectedProvince) -
            Number(a.province.id === selectedProvince),
      );
    const offsets = compact
      ? [
          [0, 0],
          [0, -17],
          [0, 17],
          [28, -16],
          [-28, -16],
          [0, -36],
        ]
      : [
          [0, 0],
          [0, -17],
          [0, 17],
          [30, -17],
          [-30, -17],
          [30, 17],
          [-30, 17],
          [0, -36],
          [0, 36],
          [58, 0],
          [-58, 0],
          [0, -56],
        ];
    for (const item of annotations) {
      ctx.font = `${item.holdings.length ? "700 12" : "500 10"}px "Noto Instrument Mono",monospace`;
      const label = item.label,
        widthText = ctx.measureText(label).width,
        bw = widthText + 12,
        bh = item.holdings.length ? 23 : 18;
      let chosen = null;
      for (const [dx, dy] of (item.holdings.length ? [[0,-24],[0,24],[44,-24],[-44,-24],...offsets] : offsets)) {
        const x = clamp(item.x + dx, bw / 2 + 6, w - bw / 2 - 6),
          y = clamp(item.y + dy, safeTop + bh / 2, safeBottom - bh / 2),
          box = {
            left: x - bw / 2 - 3,
            right: x + bw / 2 + 3,
            top: y - bh / 2 - 3,
            bottom: y + bh / 2 + 3,
          };
        if (
          placed.some(
            (o) =>
              box.left < o.right &&
              box.right > o.left &&
              box.top < o.bottom &&
              box.bottom > o.top,
          )
        )
          continue;
        chosen = { x, y, box };
        break;
      }
      if (!chosen) continue;
      placed.push(chosen.box);
      provinceTargets.push({provinceId:item.province.id,anchor:item.anchor,label:item.label,
        left:chosen.x-Math.max(bw,44)/2,right:chosen.x+Math.max(bw,44)/2,
        top:chosen.y-22,bottom:chosen.y+22});
      if (item.holdings.length) {
        ctx.fillStyle = "#e4e9cc";ctx.strokeStyle="#1b302e";ctx.lineWidth=2;
        ctx.beginPath();ctx.rect(item.x-4,item.y-4,8,8);ctx.fill();ctx.stroke();
        placed.push({left:item.x-8,right:item.x+8,top:item.y-8,bottom:item.y+8});
      }
      if (Math.hypot(item.x - chosen.x, item.y - chosen.y) > 13) {
        ctx.strokeStyle =
          "rgba(14,28,29,.88)";
        ctx.lineWidth = 2.7;
        ctx.beginPath();
        ctx.moveTo(item.x, item.y);
        ctx.lineTo(chosen.x, chosen.y);
        ctx.stroke();
      }
      ctx.fillStyle =
        item.holdings.length ? "rgba(16,31,34,.94)" : "rgba(24,40,39,.76)";
      ctx.fillRect(chosen.x - bw / 2, chosen.y - bh / 2, bw, bh);
      ctx.strokeStyle =
        item.holdings.length ? "rgba(204,221,198,.58)" : "rgba(231,229,209,.18)";
      ctx.lineWidth = 0.7;
      ctx.strokeRect(chosen.x - bw / 2, chosen.y - bh / 2, bw, bh);
      ctx.fillStyle = "#edf0df";
      ctx.fillText(label, chosen.x, chosen.y);
    }
    return { tile, ox, oy, cols, rows, forceObstacles: placed, provinceTargets };
  }
  function drawHierarchy(
    ctx,
    { w, h, record, safe, zoom, panX, panY, theme = "light", forceControlRect = null },
  ) {
    const dark = theme === "dark";
    ctx.fillStyle = dark ? "#111c27" : "#e5e8e2";
    ctx.fillRect(0, 0, w, h);
    if (dark) {
      ctx.save();
      ctx.beginPath();
      ctx.rect(safe.left, safe.top, safe.width, safe.height);
      ctx.clip();
      ctx.strokeStyle = "rgba(147,179,190,.025)";
      ctx.lineWidth = 1;
      const gap = 96,
        offsetX = ((panX % gap) + gap) % gap,
        offsetY = ((panY % gap) + gap) % gap;
      for (let x = safe.left + offsetX; x < safe.right; x += gap) {
        ctx.beginPath();
        ctx.moveTo(x, safe.top);
        ctx.lineTo(x, safe.bottom);
        ctx.stroke();
      }
      for (let y = safe.top + offsetY; y < safe.bottom; y += gap) {
        ctx.beginPath();
        ctx.moveTo(safe.left, y);
        ctx.lineTo(safe.right, y);
        ctx.stroke();
      }
      for (let i = 0; i < 70; i++) {
        const x = safe.left + hash(i, 3, 19) * safe.width,
          y = safe.top + hash(i, 8, 23) * safe.height;
        ctx.fillStyle = `rgba(196,213,212,${0.09 + hash(i, 12, 31) * 0.18})`;
        ctx.fillRect(x, y, 1.2, 1.2);
      }
      ctx.restore();
    }
    const nodes = [...(record.nodes || []), ...(record.bodies || [])].filter(
      (n) => n.knowledge !== "hidden",
    );
    const located = nodes.filter(
      (n) => Number.isFinite(n.x) && Number.isFinite(n.y),
    );
    const unlocated = nodes.filter(
      (n) => !Number.isFinite(n.x) || !Number.isFinite(n.y),
    );
    const padX = Math.min(110, Math.max(40, safe.width * 0.12)),
      padY = Math.min(90, Math.max(52, safe.height * 0.16)),
      unlocatedCardTop = Math.max(safe.top + 7,
        Number.isFinite(forceControlRect?.bottom) ? forceControlRect.bottom + 8 : safe.top + 42),
      unlocatedCardHeight = 27 + unlocated.length * 22,
      unlocatedCardBottom = unlocatedCardTop + unlocatedCardHeight,
      inner = {
        left: safe.left + padX,
        right: safe.right - padX,
        top: unlocated.length ? Math.max(safe.top + padY, unlocatedCardBottom + 8) : safe.top + padY,
        bottom: safe.bottom - padY,
      };
    const xs = located.map((n) => n.x),
      ys = located.map((n) => n.y),
      minX = xs.length ? Math.min(...xs) : 0,
      maxX = xs.length ? Math.max(...xs) : 1,
      minY = ys.length ? Math.min(...ys) : 0,
      maxY = ys.length ? Math.max(...ys) : 1,
      rx = Math.max(0.2, maxX - minX),
      ry = Math.max(0.2, maxY - minY),
      cx = (safe.left + safe.right) / 2,
      cy = (safe.top + safe.bottom) / 2;
    const positions = located.map((n) => {
      const bx = (inner.left + inner.right) / 2 + ((n.x - (minX + maxX) / 2) / rx) * (inner.right - inner.left),
        by = (inner.top + inner.bottom) / 2 + ((n.y - (minY + maxY) / 2) / ry) * (inner.bottom - inner.top);
      return {
        n,
        x: cx + (bx - cx) * zoom + panX,
        y: cy + (by - cy) * zoom + panY,
      };
    });
    ctx.save();
    ctx.beginPath();
    ctx.rect(safe.left, safe.top, safe.width, safe.height);
    ctx.clip();
    const byId = new Map(positions.map((p) => [p.n.id, p]));
    if (record.links?.length) {
      ctx.strokeStyle = dark ? "rgba(148,180,179,.35)" : "rgba(73,91,90,.34)";
      ctx.lineWidth = 1.1;
      ctx.setLineDash([3, 7]);
      ctx.beginPath();
      for (const edge of record.links) {
        const a = byId.get(edge.a),
          b = byId.get(edge.b);
        if (a && b) {
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
        }
      }
      ctx.stroke();
      ctx.setLineDash([]);
    }
    // Layout symbols separately from their recorded chart anchors. This is
    // presentation displacement only; links and fleet endpoints use positions.
    const symbolRadius = n => n.kind === "star" ? 25 : n.kind === "planet" ? 18 : n.kind === "belt" ? 23 : n.kind === "sector" ? 20 : 14;
    const symbolBoxes = unlocated.length ? [{left:safe.right-238,right:safe.right-8,top:unlocatedCardTop,bottom:unlocatedCardBottom}] : [];
    ctx.font = '600 12px "Noto Instrument Mono",monospace';
    const displayPositions = positions.map(point => {
      const radius=symbolRadius(point.n),half=Math.max(radius+5,ctx.measureText(String(point.n.name||"")).width/2+6);
      if(point.x<safe.left||point.x>safe.right||point.y<safe.top||point.y>safe.bottom)return {...point};
      const offsets=[[0,0]];
      for(let ring=1;ring<=5;ring++) for(const [dx,dy] of [[1,0],[-1,0],[0,-1],[0,1],[1,-1],[-1,-1],[1,1],[-1,1]])offsets.push([dx*ring*80,dy*ring*72]);
      let chosen=null;
      for(const [dx,dy] of offsets){
        const x=clamp(point.x+dx,safe.left+half,safe.right-half),
          y=clamp(point.y+dy,safe.top+radius+6,safe.bottom-radius-34),
          box={left:x-half,right:x+half,top:y-radius-5,bottom:y+radius+30};
        if(symbolBoxes.some(b=>box.left<b.right&&box.right>b.left&&box.top<b.bottom&&box.bottom>b.top))continue;
        chosen={...point,x,y,anchorX:point.x,anchorY:point.y,hitRect:box};symbolBoxes.push(box);break;
      }
      return chosen||{...point};
    });
    const forceObstacles = [];
    if (forceControlRect && [forceControlRect.left,forceControlRect.top,forceControlRect.right,forceControlRect.bottom].every(Number.isFinite))
      forceObstacles.push({...forceControlRect});
    for (const { n, x, y, anchorX = x, anchorY = y } of displayPositions) {
      if(Math.hypot(x-anchorX,y-anchorY)>1) {
        ctx.strokeStyle="rgba(174,193,190,.65)";ctx.lineWidth=1;ctx.beginPath();
        ctx.moveTo(anchorX,anchorY);ctx.lineTo(x,y);ctx.stroke();
        ctx.beginPath();ctx.arc(anchorX,anchorY,2,0,Math.PI*2);ctx.stroke();
      }
      const planet = n.kind === "planet",
        star = n.kind === "star",
        belt = n.kind === "belt",
        r = star ? 25 : planet ? 18 : belt ? 23 : n.kind === "sector" ? 20 : 14;
      ctx.save();
      ctx.translate(x, y);
      if (star) {
        const glow = ctx.createRadialGradient(0, 0, 2, 0, 0, 26);
        glow.addColorStop(0, "rgba(224,174,83,.3)");
        glow.addColorStop(1, "rgba(224,174,83,0)");
        ctx.fillStyle = glow;
        ctx.fillRect(-27, -27, 54, 54);
        ctx.fillStyle = "#b77b33";
        ctx.beginPath();
        ctx.arc(0, 0, 17, 0, Math.PI * 2);
        ctx.fill();
      } else if (planet) {
        const bodyColors={arid:"#a48650",barren:"#77736e",ice:"#d0d0c9",oceanic:"#71808a",terrestrial:"#4f8090"};
        ctx.fillStyle = n.knowledge === "surveyed" ? (bodyColors[n.class]||"#87928a") : "#87928a";
        ctx.beginPath();
        ctx.arc(0, 0, 15, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = n.class==="arid"?"rgba(216,177,98,.5)":n.class==="barren"?"rgba(132,126,117,.5)":n.class==="ice"?"rgba(235,235,229,.75)":"rgba(224,221,185,.55)";
        ctx.beginPath();
        ctx.ellipse(-4, -2, 5, 9, -0.45, 0, Math.PI * 2);
        ctx.fill();
      } else if (belt) {
        ctx.strokeStyle = "#777e74";
        ctx.beginPath();
        ctx.ellipse(0, 0, 23, 8, 0, 0, Math.PI * 2);
        ctx.stroke();
        for (let i = 0; i < 7; i++) {
          const a = (i * Math.PI * 2) / 7;
          ctx.fillStyle = "#8d9584";
          ctx.fillRect(Math.cos(a) * 23 - 1.5, Math.sin(a) * 8 - 1.5, 3, 3);
        }
      } else {
        ctx.fillStyle = "#62777c";
        ctx.beginPath();
        ctx.arc(0, 0, r, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = "#32494c";
        ctx.stroke();
      }
      ctx.restore();
      ctx.fillStyle = dark ? "#e6e7dd" : "#293331";
      ctx.font = '600 12px "Noto Instrument Mono",monospace';
      ctx.textAlign = "center";
      const label = String(n.name || ""),
        lw = ctx.measureText(label).width,
        lx = clamp(x, safe.left + lw / 2 + 4, safe.right - lw / 2 - 4),
        ly = clamp(y + r + 18, safe.top + 14, safe.bottom - 13);
      ctx.fillStyle = dark ? "rgba(23,29,31,.87)" : "rgba(239,240,230,.88)";
      ctx.fillRect(lx - lw / 2 - 4, ly - 10, lw + 8, 17);
      ctx.fillStyle = dark ? "#e6e7dd" : "#293331";
      ctx.fillText(label, lx, ly - 1);
      forceObstacles.push(
        {
          left: x - r - 4,
          right: x + r + 4,
          top: y - r - 4,
          bottom: y + r + 4,
        },
        {
          left: lx - lw / 2 - 5,
          right: lx + lw / 2 + 5,
          top: ly - 12,
          bottom: ly + 7,
        },
      );
    }
    ctx.restore();
    const unlocatedTargets = [];
    if (unlocated.length) {
      const left = safe.right - 238,
        top = unlocatedCardTop,
        width = 230,
        height = unlocatedCardHeight;
      ctx.fillStyle = "rgba(13,25,35,.94)";
      ctx.fillRect(left, top, width, height);
      ctx.strokeStyle = "rgba(167,192,198,.42)";
      ctx.strokeRect(left, top, width, height);
      ctx.textAlign = "left";
      ctx.font = '9px "Noto Instrument Mono",monospace';
      ctx.fillStyle = "#aebfc0";
      ctx.fillText("UNLOCATED · NOT PLACED", left + 9, top + 13);
      unlocated.forEach((n, index) => {
        const rowTop = top + 20 + index * 22,
          target = {
            n,
            uiOnly: true,
            hitRect: {
              left,
              right: left + width,
              top: rowTop - 4,
              bottom: rowTop + 18,
            },
            x: left + width / 2,
            y: rowTop + 7,
          };
        ctx.setLineDash([2, 2]);
        ctx.strokeStyle = "rgba(167,192,198,.42)";
        ctx.strokeRect(left + 7, rowTop - 4, width - 14, 20);
        ctx.setLineDash([]);
        ctx.fillStyle = "#e3e5dd";
        ctx.font = '10px "Noto Instrument Mono",monospace';
        ctx.fillText(`${n.name} · ${n.kind}`, left + 12, rowTop + 9);
        unlocatedTargets.push(target);
      });
      forceObstacles.push({
        left,
        right: left + width,
        top,
        bottom: top + height,
      });
    }
    return {
      hierarchy: true,
      positions,
      hitTargets: [...displayPositions, ...unlocatedTargets],
      safeRect: safe,
      forceObstacles,
    };
  }
  window.HWMapRenderer = {
    drawPlanet,
    drawHierarchy,
    terrainColor(style, key, preset = null) { return terrainPalette(style,preset)[key]; },
    hasSurface(geometry) {
      return Boolean(surfaceFor(geometry));
    },
  };
})();
