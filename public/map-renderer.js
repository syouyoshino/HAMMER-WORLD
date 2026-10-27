(() => {
  "use strict";
  const cache = new WeakMap();
  const detailRasterCache = new WeakMap();
  const dryLightingCache = new WeakMap();
  const featureCellCache = new WeakMap();
  const provinceCache = new WeakMap();
  const provinceAnchorSource = new WeakMap();
  // Geometry records are immutable; index recorded land once per response.
  function provinceLand(geometry) {
    if(geometry.surface?.version==="planet-v10"){
      const grid=geometry.province_anchor_grid,source=provinceAnchorSource.get(geometry),
        width=grid?.width,height=grid?.height;
      if(provinceCache.has(geometry)&&source?.anchors===geometry.province_anchors&&source.width===width&&source.height===height)return provinceCache.get(geometry);
      const index=new Map();
      if(width>0&&height>0)for(const record of geometry.province_anchors||[]){
        if(!Number.isInteger(record.cell))continue;
        const x=(record.cell%width+.5)*geometry.planet.width/width,y=(Math.floor(record.cell/width)+.5)*geometry.planet.height/height,
          anchor={x:x-.5,y:y-.5,province_id:record.province_id,terrain:"land"},
          tiles=(geometry.tiles||[]).filter(t=>t.province_id===record.province_id);
        index.set(record.province_id,{x,y,anchor,tiles:tiles.length?tiles:[anchor]});
      }
      provinceAnchorSource.set(geometry,{anchors:geometry.province_anchors,width,height});provinceCache.set(geometry,index);return index;
    }
    if (provinceCache.has(geometry)) return provinceCache.get(geometry);
    const index = new Map();
    for (const tile of geometry.tiles || []) {
      if (!tile.province_id || tile.terrain === "ocean") continue;
      let entry = index.get(tile.province_id);
      if (!entry) { entry = {tiles:[],x:0,y:0,anchor:null}; index.set(tile.province_id,entry); }
      entry.tiles.push(tile); entry.x += tile.x + .5; entry.y += tile.y + .5;
    }
    for (const entry of index.values()) {
      entry.x /= entry.tiles.length; entry.y /= entry.tiles.length;
      let distance = Infinity;
      for (const tile of entry.tiles) {
        const next = (tile.x+.5-entry.x)**2 + (tile.y+.5-entry.y)**2;
        if (next < distance) { distance = next; entry.anchor = tile; }
      }
    }
    provinceCache.set(geometry,index);
    return index;
  }
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
    if(s?.version==="planet-v10")return s;
    if (!s || !["planet-v2", "planet-v3", "planet-v4", "planet-v5", "planet-v6", "planet-v7", "planet-v8", "planet-v9"].includes(s.version) || !Array.isArray(s.elevation))
      return null;
    return s;
  }
  const wrapsX = geometry => ["planet-v6", "planet-v7", "planet-v8", "planet-v9", "planet-v10"].includes(geometry?.surface?.version) && geometry.surface.topology === "cylinder-x";
  const nearestX = (x, reference, width) => x + Math.round((reference-x)/width)*width;
  function featureAt(geometry,index){
    const surface=geometry?.surface;if(surface?.version!=="planet-v9"||surface.hydrography?.version!=="hydrography-v1"||!Number.isInteger(index))return null;
    let lookup=featureCellCache.get(geometry);if(!lookup){lookup=new Map();const rank={ocean:1,sea:1,river:2,lake:3};
      for(const feature of surface.hydrography.features||[])for(const cell of feature.cells||[]){const prior=lookup.get(cell),score=rank[feature.kind]||0;
        if(!prior||score>prior.score||score===prior.score&&feature.kind==="river"&&feature.cells.length>prior.feature.cells.length)lookup.set(cell,{feature,score});}
      featureCellCache.set(geometry,lookup);}
    return lookup.get(index)?.feature||null;
  }
  function craterProfile(distanceQ, radiusQ, depth, rimHeight) {
    const scaled = distanceQ * 4;
    if (scaled > radiusQ * 5) return 0;
    if (scaled <= radiusQ * 3) {
      const t = scaled / (radiusQ * 3);
      return -depth * (1 - t * t);
    }
    if (scaled <= radiusQ * 4) return rimHeight * (scaled - radiusQ * 3) / radiusQ;
    return rimHeight * (radiusQ * 5 - scaled) / radiusQ;
  }
  function craterResidualRaster(surface, cols, rows, w, h, scale, interpolateRows, vertical, cylinder) {
    const samples = new Float64Array(cols * rows), continuous = new Float32Array(w * h);
    const addAt = (target, x, y, xq, yq, crater) => {
      const dx = xq - crater.x_q, dy = yq - crater.y_q,
        radius = crater.radius_q, support = radius * 1.25;
      if (Math.abs(dx) > support || Math.abs(dy) > support) return;
      const distance = Math.hypot(dx, dy);
      if (distance > support) return;
      target[y * (target === samples ? cols : w) + x] += craterProfile(distance, radius, crater.depth, crater.rim_height);
    };
    for (const crater of surface.craters) {
      const support = crater.radius_q * 1.25,
        firstY = Math.max(0, Math.floor((crater.y_q - support - 8) / 16)),
        lastY = Math.min(rows - 1, Math.ceil((crater.y_q + support - 8) / 16));
      for (let y = firstY; y <= lastY; y++) {
        const yq = y * 16 + 8;
        const firstX = Math.floor((crater.x_q - support - 8) / 16),
          lastX = Math.ceil((crater.x_q + support - 8) / 16);
        for (let rawX = firstX; rawX <= lastX; rawX++) {
          const x = cylinder ? ((rawX % cols) + cols) % cols : clamp(rawX, 0, cols - 1);
          if (!cylinder && (rawX < 0 || rawX >= cols)) continue;
          // Keep the unwrapped sample coordinate near the crater centre while
          // writing to its canonical wrapped column.
          addAt(samples, x, y, rawX * 16 + 8, yq, crater);
        }
      }
      const cx = crater.x_q / 16 * scale - .5, cy = crater.y_q / 16 * scale - .5,
        radiusPx = support / 16 * scale,
        firstPy = Math.max(0, Math.floor(cy - radiusPx - 1)), lastPy = Math.min(h - 1, Math.ceil(cy + radiusPx + 1)),
        firstPx = Math.floor(cx - radiusPx - 1), lastPx = Math.ceil(cx + radiusPx + 1);
      for (let py = firstPy; py <= lastPy; py++) {
        const yq = (py + .5) / scale * 16, dy = yq - crater.y_q;
        if (Math.abs(dy) > support) continue;
        for (let rawPx = firstPx; rawPx <= lastPx; rawPx++) {
          const xq = (rawPx + .5) / scale * 16, dx = xq - crater.x_q;
          if (dx * dx + dy * dy > support * support) continue;
          const targetX = cylinder ? ((rawPx % w) + w) % w : rawPx;
          if (targetX < 0 || targetX >= w) continue;
          addAt(continuous, targetX, py, xq, yq, crater);
        }
      }
    }
    const interpolated = interpolateRows(samples);
    for (let py = 0; py < h; py++) {
      const y = (py + .5) / scale, [row0, row1, ty] = vertical(y);
      for (let px = 0; px < w; px++) {
        const index = py * w + px;
        continuous[index] -= interpolated[row0 + px] * (1 - ty) + interpolated[row1 + px] * ty;
      }
    }
    return continuous;
  }
  // Lighting alone uses a low-pass background. Recorded heights, colours and
  // material masks remain authoritative and are never replaced by this field.
  function dryLightingHeight(heights, craters, cols, rows, cylinder) {
    const background = Float64Array.from(heights);
    for (const crater of craters || []) {
      const support=crater.radius_q*1.25;
      for(let y=Math.max(0,Math.floor((crater.y_q-support-8)/16));y<=Math.min(rows-1,Math.ceil((crater.y_q+support-8)/16));y++)
        for(let rawX=Math.floor((crater.x_q-support-8)/16);rawX<=Math.ceil((crater.x_q+support-8)/16);rawX++) {
          if(!cylinder&&(rawX<0||rawX>=cols))continue;
          const x=(rawX%cols+cols)%cols,distance=Math.hypot(rawX*16+8-crater.x_q,y*16+8-crater.y_q);
          background[y*cols+x]-=craterProfile(distance,crater.radius_q,crater.depth,crater.rim_height);
        }
    }
    const gaussian = sigma => {
      const radius=Math.ceil(sigma*3),weights=[];let sum=0;
      for(let d=-radius;d<=radius;d++){const weight=Math.exp(-d*d/(2*sigma*sigma));weights.push(weight);sum+=weight;}
      for(let k=0;k<weights.length;k++)weights[k]/=sum;
      const horizontal=new Float64Array(cols*rows),result=new Float64Array(cols*rows);
      for(let y=0;y<rows;y++)for(let x=0;x<cols;x++){
        let value=0;for(let d=-radius;d<=radius;d++)value+=background[y*cols+(cylinder?((x+d)%cols+cols)%cols:clamp(x+d,0,cols-1))]*weights[d+radius];
        horizontal[y*cols+x]=value;
      }
      for(let y=0;y<rows;y++)for(let x=0;x<cols;x++){
        let value=0;for(let d=-radius;d<=radius;d++)value+=horizontal[clamp(y+d,0,rows-1)*cols+x]*weights[d+radius];
        result[y*cols+x]=value;
      }
      return result;
    };
    const near=gaussian(1.5),broad=gaussian(4);
    for(let i=0;i<near.length;i++)near[i]=near[i]*.8+broad[i]*.2;
    return near;
  }
  function dryCraterDerivatives(craters, cols, rows, w, h, scale, cylinder) {
    const dx=new Float32Array(w*h),dy=new Float32Array(w*h);
    for(const crater of craters||[]){
      const support=crater.radius_q*1.25+16,
        firstY=Math.max(0,Math.floor((crater.y_q-support)/16*scale-.5)),lastY=Math.min(h-1,Math.ceil((crater.y_q+support)/16*scale-.5));
      for(let py=firstY;py<=lastY;py++)for(let rawPx=Math.floor((crater.x_q-support)/16*scale-.5);rawPx<=Math.ceil((crater.x_q+support)/16*scale-.5);rawPx++){
        if(!cylinder&&(rawPx<0||rawPx>=w))continue;
        const x=(rawPx+.5)/scale*16-crater.x_q,y=(py+.5)/scale*16-crater.y_q,
          at=(a,b)=>craterProfile(Math.hypot(a,b),crater.radius_q,crater.depth,crater.rim_height),i=py*w+(rawPx%w+w)%w;
        // Same two-native-cell stencil as the filtered background derivatives.
        dx[i]+=at(x+16,y)-at(x-16,y);dy[i]+=at(x,y+16)-at(x,y-16);
      }
    }
    return {dx,dy};
  }
  function lakeInterior(mask, cols, rows) {
    // Distance into the saved mask supplies a shallow shore transition. This
    // derives no new features and wraps through the same cylindrical seam.
    const distance=new Float32Array(cols*rows),queue=[];
    for(let i=0;i<distance.length;i++) {
      distance[i]=mask[i]==="1"?cols+rows:0;
      if(mask[i]!=="1")queue.push(i);
    }
    for(let q=0;q<queue.length;q++) {
      const i=queue[q],x=i%cols,y=Math.floor(i/cols),next=distance[i]+1;
      for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++) {
        const ny=y+dy;if(ny<0||ny>=rows)continue;
        const j=ny*cols+(x+dx+cols)%cols;
        if(distance[j]>next){distance[j]=next;queue.push(j);}
      }
    }
    return distance;
  }
  function riverShorePoints(surface, points, cols, cylinder) {
    if(!surface.elevation || surface.sea_level===null)return points;
    const sea=surface.sea_level,heights=surface.elevation,result=[];
    const at=([x,y])=>heights[y*cols+(cylinder?((x%cols)+cols)%cols:x)];
    for(let i=0;i<points.length;i++) {
      const point=points[i],height=at(point);
      if(height<=sea) {
        if(result.length) {
          const previous=result[result.length-1],before=at(points[i-1]),
            t=clamp((before-sea)/(before-height),0,1),
            endX=cylinder?nearestX(point[0],previous[0],cols):point[0];
          result.push([previous[0]+(endX-previous[0])*t,previous[1]+(point[1]-previous[1])*t]);
        }
        break;
      }
      result.push(point);
    }
    return result;
  }
  function projectRiverPoints(points, cols, cylinder, tile, ox, oy) {
    // Unwrap in saved-grid coordinates before applying any camera translation.
    const world=[];
    for(const [x,y] of points)world.push([world.length&&cylinder?nearestX(x,world[world.length-1][0],cols):x,y]);
    return world.map(([x,y])=>[ox+(x+.5)*tile,oy+(y+.5)*tile]);
  }
  function riverLabelCandidates(points, rawPoints, owners, cols, bounds, textWidth) {
    const runs=[];let run=null,previousAngle=null;
    for(let i=1;i<Math.min(points.length,rawPoints.length);i++){
      const cell=([x,y])=>y*cols+((x%cols)+cols)%cols,
        a=points[i-1],b=points[i],angle=Math.atan2(b[1]-a[1],b[0]-a[0]),
        unique=owners.get(cell(rawPoints[i-1]))===1&&owners.get(cell(rawPoints[i]))===1,
        readable=Math.abs(Math.sin(angle))<.82,
        turn=previousAngle===null?0:Math.abs(Math.atan2(Math.sin(angle-previousAngle),Math.cos(angle-previousAngle)));
      if(!unique||!readable){run=null;previousAngle=null;continue;}
      if(!run||turn>Math.PI/4+.001){run={first:i-1,last:i};runs.push(run);}else run.last=i;
      previousAngle=angle;
    }
    const candidates=[],cx=(bounds.left+bounds.right)/2,cy=(bounds.top+bounds.bottom)/2;
    for(const {first,last} of runs){
      // Measure only the part of this unshared run that intersects the viewport.
      let visibleSpan=0;
      for(let i=first+1;i<=last;i++){
        const a=points[i-1],b=points[i],dx=b[0]-a[0],dy=b[1]-a[1];let lo=0,hi=1;
        for(const [p,q] of [[-dx,a[0]-bounds.left],[dx,bounds.right-a[0]],[-dy,a[1]-bounds.top],[dy,bounds.bottom-a[1]]]){
          if(p===0){if(q<0){hi=-1;break;}continue;}
          const t=q/p;if(p<0)lo=Math.max(lo,t);else hi=Math.min(hi,t);
        }
        if(hi>=lo)visibleSpan+=Math.hypot(dx,dy)*(hi-lo);
      }
      if(visibleSpan<textWidth+12)continue;
      for(let step=first*2;step<=last*2;step++){
        const index=step/2,low=Math.floor(index),high=Math.ceil(index),
          x=(points[low][0]+points[high][0])/2,y=(points[low][1]+points[high][1])/2;
        if(x<bounds.left||x>bounds.right||y<bounds.top||y>bounds.bottom)continue;
        const a=points[Math.max(first,Math.ceil(index-1))],b=points[Math.min(last,Math.floor(index+1))];let angle=Math.atan2(b[1]-a[1],b[0]-a[0]);
        if(Math.abs(Math.sin(angle))>=.82)continue;
        // The full name must have unique recorded course on both sides.
        const ux=Math.cos(angle),uy=Math.sin(angle),before=(x-points[first][0])*ux+(y-points[first][1])*uy,
          after=(points[last][0]-x)*ux+(points[last][1]-y)*uy;
        if(before<textWidth/2+6||after<textWidth/2+6)continue;
        if(angle>Math.PI/2)angle-=Math.PI;else if(angle< -Math.PI/2)angle+=Math.PI;
        candidates.push({x,y,angle,visibleSpan,distance:Math.hypot(x-cx,y-cy),index});
      }
    }
    return candidates.sort((a,b)=>b.visibleSpan-a.visibleSpan||a.distance-b.distance||a.index-b.index);
  }
  function baseRaster(geometry, style, orbitLighting = false) {
    let map = cache.get(geometry);
    if (!map) { map = new Map(); cache.set(geometry, map); }
    const rasterKey=orbitLighting?`${style}:orbit`:style;
    if (map.has(rasterKey)) return map.get(rasterKey);
    const { width: cols, height: rows } = geometry.planet,
      scale = Math.min(24, 1536 / cols), w = Math.round(cols * scale), h = Math.round(rows * scale),
      surface = surfaceFor(geometry), tiles = geometry.tiles,
      survey = style === "survey",
      nativeFrozen = surface?.version === "planet-v10" && surface.hydrology === "none" && surface.preset === "frozen",
      colors = nativeFrozen ? (survey ? {
        ocean:[120,138,150],coast:[162,177,187],plains:[173,186,194],
        rock:[139,152,161],forest:[139,154,164],marsh:[160,175,184],
      } : {
        ocean:[91,113,128],coast:[140,159,172],plains:[153,170,181],
        rock:[105,124,138],forest:[110,130,143],marsh:[138,157,170],
      }) : surface?.hydrology === "none" ? Object.fromEntries(Object.entries(terrainPalette(style,surface.preset)).map(([key,value])=>[key,[parseInt(value.slice(1,3),16),parseInt(value.slice(3,5),16),parseInt(value.slice(5,7),16)]])) : survey ? {
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
    const cylinder = wrapsX(geometry), interpolateRows = (field, shift = 0) => {
      const result = new Float64Array(w * rows);
      for (let px=0;px<w;px++) {
        const raw=(px+.5)/scale+shift-.5,
          fx=cylinder?((raw%cols)+cols)%cols:clamp(raw,0,cols-1),
          ix=Math.floor(fx),tx=fx-ix,next=cylinder?(ix+1)%cols:Math.min(cols-1,ix+1);
        for(let y=0;y<rows;y++) result[y*w+px]=field[y*cols+ix]*(1-tx)+field[y*cols+next]*tx;
      }
      return result;
    };
    const materials = ["planet-v8","planet-v9","planet-v10"].includes(surface?.version) ? surface.materials : null,
      lakeField = materials?.lake_material !== "none" && materials?.lake_mask
        ? interpolateRows(Array.from(materials.lake_mask, Number)) : null,
      lakeDepth = lakeField ? interpolateRows(lakeInterior(materials.lake_mask, cols, rows)) : null,
      iceField = materials?.polar_caps !== "none" && materials?.ice_mask
        ? interpolateRows(Array.from(materials.ice_mask, Number)) : null,
      composition = lakeField || iceField ? ctx.createImageData(w, h) : null;
    const cratered = ["planet-v7", "planet-v8", "planet-v9", "planet-v10"].includes(surface?.version) && surface.geology === "cratered" && surface.craters?.length,
      dryLighting = surface?.version==="planet-v10" && surface.hydrology==="none" && heights,
      gradientStep = dryLighting ? 1 : cratered ? 1 / scale : .35,
      lightingHeight = dryLighting ? (dryLightingCache.get(geometry)?.height || dryLightingHeight(heights, cratered ? surface.craters : [], cols, rows, cylinder)) : heights;
    const land = interpolateRows(tiles.map(t => t.terrain === "ocean" ? 0 : 1)),
      channels = [0,1,2].map(c => interpolateRows(tiles.map(t => surface?.version==="planet-v10"&&t.terrain==="ocean"?0:(colors[t.terrain] || colors.plains)[c]))),
      elevation = heights ? interpolateRows(heights) : null,
      heightLeft = heights ? interpolateRows(lightingHeight,-gradientStep) : null,
      heightRight = heights ? interpolateRows(lightingHeight,gradientStep) : null,
      lightingElevation = dryLighting ? interpolateRows(lightingHeight) : elevation,
      moisture = surface?.moisture ? interpolateRows(surface.moisture) : null,
      temperature = surface?.temperature ? interpolateRows(surface.temperature) : null,
      shoreColor = survey ? [183,204,197] : [60,102,111],
      deepColor = survey ? [126,161,172] : [12,33,51],
      highColor = nativeFrozen ? [182,196,204] : surface?.preset==="frozen"?[224,224,219]:survey ? [204,195,163] : [178,164,132],
      wetColor = [54,87,61],coldColor=nativeFrozen ? [180,194,202] : surface?.preset==="frozen"?[218,218,212]:[204,207,192];
    const vertical = (y) => {
      const fy=clamp(y-.5,0,rows-1),iy=Math.floor(fy);
      return [iy*w,Math.min(rows-1,iy+1)*w,fy-iy];
    };
    const craterResidual = cratered
      ? craterResidualRaster(surface, cols, rows, w, h, scale, interpolateRows, vertical, cylinder)
      : null;
    const craterNormals = dryLighting && cratered ? (dryLightingCache.get(geometry)?.craters || dryCraterDerivatives(surface.craters, cols, rows, w, h, scale, cylinder)) : null;
    if(dryLighting)dryLightingCache.set(geometry,{height:lightingHeight,craters:craterNormals});
    for (let py = 0; py < h; py++) {
      const y=(py+.5)/scale,[row0,row1,ty]=vertical(y),
        [up0,up1,upT]=vertical(y-gradientStep),[down0,down1,downT]=vertical(y+gradientStep), inv=1-ty;
      for (let px = 0; px < w; px++) {
        const i=row0+px,j=row1+px,
          sampledElevation=elevation?elevation[i]*inv+elevation[j]*ty:sea,
          correction=craterResidual?.[py*w+px]||0,
          elev=sampledElevation+correction,
          heightContour=["planet-v7","planet-v8","planet-v9","planet-v10"].includes(surface?.version)&&surface.hydrology==="ocean-draining"&&surface.sea_level!==null&&heights,
          cover=heightContour?clamp((elev-sea+18)/36,0,1):land[i]*inv+land[j]*ty,
          terrainCover=land[i]*inv+land[j]*ty,
          onLand=heightContour?(surface?.version==="planet-v10"?elev>sea+1e-9&&terrainCover>1e-9:elev>=sea):cover>=.5,
          wet=moisture?moisture[i]*inv+moisture[j]*ty:500,
          temp=temperature?temperature[i]*inv+temperature[j]*ty:500;
        let shade=1,high=0,wetMix=0,coldMix=0,depth=0,shore=0;
        if(!onLand) {
          depth=(heights?clamp((sea-elev)/250,0,1):.45)*.35;
          shore=heightContour?clamp((elev-(sea-14))/14,0,1)*.09:clamp(cover*1.2,0,.22);
        } else if(heights) {
          let dx=(heightRight[i]*inv+heightRight[j]*ty)-(heightLeft[i]*inv+heightLeft[j]*ty),
            dy=(lightingElevation[down0+px]*(1-downT)+lightingElevation[down1+px]*downT)-(lightingElevation[up0+px]*(1-upT)+lightingElevation[up1+px]*upT);
          if(craterNormals){dx+=craterNormals.dx[py*w+px];dy+=craterNormals.dy[py*w+px];}
          if(craterResidual && !dryLighting){
            const left=craterResidual[py*w+(cylinder?(px+w-1)%w:Math.max(0,px-1))],
              right=craterResidual[py*w+(cylinder?(px+1)%w:Math.min(w-1,px+1))],
              up=craterResidual[Math.max(0,py-1)*w+px],down=craterResidual[Math.min(h-1,py+1)*w+px];
            // Differentiate the complete corrected height with one matching
            // stencil, so the subtracted bilinear crater field cancels.
            dx+=right-left;dy+=down-up;
          }
          if(surface?.version==="planet-v10"&&surface.hydrology==="none"){
            // Match the filtered background and separate analytic crater stencil.
            // Normalize native-cell derivatives to the displayed world grid.
            const reliefScale=surface.renderReliefScale||1,
              nx=dx*reliefScale/(2*gradientStep*140),ny=dy*reliefScale/(2*gradientStep*140),
              illumination=(nx*.5+ny*.6+.75)/Math.sqrt(1+nx*nx+ny*ny);
            shade=(.3+.9*Math.max(0,illumination))/(.3+.9*.75);
            if(survey)shade=1+(shade-1)*.85;
          }else if(craterResidual){
            const nx=dx/(2*gradientStep*140),ny=dy/(2*gradientStep*140),
              // Normal (-gx,-gy,1) under northwest light (-.5,-.6,.75).
              illumination=(nx*.5+ny*.6+.75)/Math.sqrt(1+nx*nx+ny*ny);
            shade=.95+.065*illumination;
            if(survey)shade=1+(shade-1)*.6;
          }else shade=1+clamp((-dx*.65-dy*.75)/110,-.32,.3)*(survey?.6:1);
          high=clamp((elev-620)/350,0,1)*(craterResidual?.18:.44);
          wetMix=surface?.hydrology==="none"?0:clamp((wet-450)/700,0,.24);
          coldMix=clamp((320-temp)/600,0,.3);
        }
        // The sphere lights its own geometry. Its texture is albedo, without
        // Cartesian chart hillshade or native dry elevation relief tint.
        if(orbitLighting){shade=1;if(dryLighting)high=0;}
        const grain=(hash(px,py,3)-.5)*(survey?2.2:7),off=(py*w+px)*4;
        for(let c=0;c<3;c++) {
          let color;
          if(!onLand) {
            color=Math.round(colors.ocean[c]*(1-shore)+shoreColor[c]*shore);
            color=Math.round(color*(1-depth)+deepColor[c]*depth);
          } else {
            // Native channels contain only saved land contributions. Dividing
            // by their matching coverage avoids cancellation near tiny shores;
            // exact-sea ocean samples never enter this land branch.
            const sampledChannel=channels[c][i]*inv+channels[c][j]*ty;
            color=surface?.version==="planet-v10"?sampledChannel/terrainCover:
              (sampledChannel-colors.ocean[c]*(1-cover))/Math.max(.001,cover);
            if(heights) {
              color=Math.round(color*(1-high)+highColor[c]*high);
              color=Math.round(color*(1-wetMix)+wetColor[c]*wetMix);
              color=Math.round(color*(1-coldMix)+coldColor[c]*coldMix)*shade;
            }
            if(heightContour){const landColor=color,coastal=clamp((14-(elev-sea))/14,0,1)*.035;color=shoreColor[c]*coastal+landColor*(1-coastal);}
          }
          img.data[off+c]=clamp(color+grain,0,255);
        }
        img.data[off+3]=255;
        if(composition) {
          // Interpolate only recorded binary masks at cell centres, with the
          // same periodic longitude stencil as the saved elevation field.
          const lakeCover=lakeField ? lakeField[i]*inv+lakeField[j]*ty : 0,
            iceCover=iceField ? iceField[i]*inv+iceField[j]*ty : 0,
            iceAlpha=clamp((iceCover-.35)/.3,0,1),
            // Broad, inward transition softens the sampled shore without an
            // outside outline. Every painted pixel still derives from its mask.
            lakeT=clamp((lakeCover-.35)/.6,0,1),
            lakeAlpha=lakeT*lakeT*(3-2*lakeT);
          if(iceAlpha>0) {
            // Native ice retains the saved slope contrast with room below white.
            const relief=dryLighting?clamp(shade,.57,1.18):clamp(1+(shade-1)*.75,.8,1.13),
              iceColor=dryLighting?(survey?[176,194,204]:[164,185,198]):survey?[229,237,233]:[217,229,226];
            for(let c=0;c<3;c++)composition.data[off+c]=clamp(iceColor[c]*relief+grain*.3,0,255);
            composition.data[off+3]=Math.round(iceAlpha*255);
          } else if(lakeAlpha>0) {
            // No hillshade: tone comes from mask depth, recorded elevation and
            // the existing fine surface grain. Lava has dark cooling crust at
            // its margin and warmer liquid inward, never a luminous keyline.
            const lava=materials.lake_material==="lava", hydrocarbon=materials.lake_material==="hydrocarbon",
              depth=lakeDepth[i]*inv+lakeDepth[j]*ty,
              innerT=clamp((depth-.4)/1.1,0,1),inner=innerT*innerT*(3-2*innerT),
              body=lava?[153,70,32]:hydrocarbon?[58,45,28]:survey?[61,111,133]:[28,74,99],
              shore=lava?[61,53,44]:hydrocarbon?[91,77,49]:survey?[100,133,130]:[65,103,108],
              tone=1+(orbitLighting&&surface.hydrology==="none"?0:clamp((sampledElevation-550)/1800,-.07,.09))-clamp(depth-2,0,6)*.006;
            for(let c=0;c<3;c++)composition.data[off+c]=
              (shore[c]*(1-inner)+body[c]*inner)*tone+grain*(lava?.9:.65);
            composition.data[off+3]=Math.round(lakeAlpha*255);
          }
        }
      }
    }
    ctx.putImageData(img,0,0);
    if (surface) {
      // Contours interpolate the persisted elevation field, without decorative
      // hatching or a synthetic relief field.
      if (survey && !orbitLighting && surface.hydrology !== "none" && heights) {
        ctx.strokeStyle="rgba(64,76,52,.24)"; ctx.lineWidth=.7;
        for(const level of [sea+100,sea+200,sea+300,sea+400,sea+500])
          for(let y=0;y<rows-1;y++) for(let x=0;x<(cylinder?cols:cols-1);x++) {
            const coords=[[x+.5,y+.5],[x+1.5,y+.5],[x+1.5,y+1.5],[x+.5,y+1.5]],
              nx=(x+1)%cols,
              values=[heights[y*cols+x],heights[y*cols+nx],heights[(y+1)*cols+nx],heights[(y+1)*cols+x]],points=[];
            for(const [a,b] of [[0,1],[1,2],[2,3],[3,0]]) if((values[a]<level)!==(values[b]<level)) {
              const t=(level-values[a])/(values[b]-values[a]);
              points.push([coords[a][0]+(coords[b][0]-coords[a][0])*t,coords[a][1]+(coords[b][1]-coords[a][1])*t]);
            }
            for(let i=0;i+1<points.length;i+=2) {
              const draw=(shift)=>{ctx.beginPath();ctx.moveTo(points[i][0]*scale+shift,points[i][1]*scale);
                ctx.lineTo(points[i+1][0]*scale+shift,points[i+1][1]*scale);ctx.stroke();};
              if(cylinder){draw(-w);draw(0);draw(w);}else draw(0);
            }
          }
      }
      ctx.strokeStyle=survey?"rgba(48,113,143,.96)":"rgba(78,151,179,.98)";
      ctx.lineWidth=survey?1.3:1.65;ctx.lineCap="round";ctx.lineJoin="round";
      const inkedRiverSegments=new Set();
      for(const river of surface.rivers || []) {
        const points=riverShorePoints(surface,river.points||[],cols,cylinder);
        if(!Array.isArray(points)||points.length<2)continue;
        const xy=projectRiverPoints(points,cols,cylinder,scale,0,0);
        const trace=(shift=0)=>{
          const flowAt=index=>{
            const x=((Math.round(xy[index][0]/scale-.5)%cols)+cols)%cols,
              y=clamp(Math.round(xy[index][1]/scale-.5),0,rows-1);
            return surface.accumulation?.[y*cols+x]||1;
          }, widthAt=index=>surface.accumulation?.length
            ?clamp(.5+Math.sqrt(flowAt(index))*.042,survey?.65:.7,survey?1.05:1.2)
            :survey?1:1.2;
          const midpoint=(a,b)=>[(a[0]+b[0])/2,(a[1]+b[1])/2],segments=[];
          if(xy.length===2)segments.push({start:xy[0],end:xy[1],width:(widthAt(0)+widthAt(1))/2});
          else{
            segments.push({start:xy[0],end:midpoint(xy[0],xy[1]),width:widthAt(0)});
            for(let i=1;i<xy.length-1;i++)segments.push({start:midpoint(xy[i-1],xy[i]),control:xy[i],end:midpoint(xy[i],xy[i+1]),width:widthAt(i)});
            segments.push({start:midpoint(xy[xy.length-2],xy[xy.length-1]),end:xy[xy.length-1],width:widthAt(xy.length-1)});
          }
          for(const segment of segments){
            const key=JSON.stringify([shift,segment.start,segment.control,segment.end]);
            if(inkedRiverSegments.has(key))continue;inkedRiverSegments.add(key);
            const path=()=>{ctx.beginPath();ctx.moveTo(...segment.start);if(segment.control)ctx.quadraticCurveTo(...segment.control,...segment.end);else ctx.lineTo(...segment.end);};
            // Both ink passes trace exactly the same recorded midpoint course.
            ctx.save();path();ctx.strokeStyle=survey?"rgba(234,242,231,.35)":"rgba(9,34,43,.35)";ctx.lineWidth=segment.width+.65;ctx.stroke();ctx.restore();
            path();ctx.lineWidth=segment.width;ctx.stroke();
          }
        };
        if(cylinder){trace();ctx.save();ctx.translate(-w,0);trace(-w);ctx.restore();ctx.save();ctx.translate(w,0);trace(w);ctx.restore();}else trace();
      }
    }
    if(composition) {
      // Cover river/contour ink beneath recorded surface materials. The ice
      // colour already carries saved relief; liquids have no terrain hillshade.
      const layer=document.createElement("canvas");layer.width=w;layer.height=h;
      layer.getContext("2d").putImageData(composition,0,0);ctx.drawImage(layer,0,0);
    }
    map.set(rasterKey,canvas);return canvas;
  }
  // This proxy is a rendering view of the immutable recorded detail, never a
  // replacement for strategic geometry or an authority for picking/simulation.
  function fineGeometry(detail, geometry) {
    let entry=detailRasterCache.get(detail);
    if(entry)return entry;
    const cols=detail.width,terrain={o:"ocean",c:"coast",p:"plains",r:"rock",f:"forest",m:"marsh"},
      metadata=geometry.surface,
      proxy={planet:{width:cols,height:detail.height},
        tiles:Array.from(detail.terrain_grid,(c,i)=>({terrain:terrain[c],x:i%cols,y:Math.floor(i/cols)})),
        surface:{...metadata,elevation:detail.elevation,craters:detail.craters,rivers:[],renderReliefScale:detail.width/geometry.planet.width,
          materials:{lake_material:metadata.lake_material,polar_caps:metadata.polar_caps,
            lake_mask:Array.from(detail.materials,c=>"whl".includes(c)?"1":"0").join(""),
            ice_mask:Array.from(detail.materials,c=>c==="i"?"1":"0").join("")}}},
      paths=new Map(),owners=new Map();
    for(const river of detail.rivers){
      const raw=river.points.map(i=>[i%cols,Math.floor(i/cols)]);
      paths.set(river.id,[riverShorePoints(proxy.surface,raw,cols,wrapsX(geometry))]);
      for(const cell of new Set(river.points))owners.set(cell,(owners.get(cell)||0)+1);
    }
    entry={geometry:proxy,paths,owners,boundaries:new Map(),rasters:new Map()};detailRasterCache.set(detail,entry);return entry;
  }
  function fineFeatureBoundary(detail, geometry, id) {
    const entry=fineGeometry(detail,geometry);
    if(entry.boundaries.has(id))return entry.boundaries.get(id);
    const value=detail.feature_ids.indexOf(id)+1,segments=[],cols=detail.width,rows=detail.height,
      cylinder=wrapsX(geometry),field=detail.feature_index;
    if(value>0)for(let y=0;y<rows;y++)for(let x=0;x<cols;x++){
      const i=y*cols+x;if(field[i]!==value)continue;
      if((x===0&&!cylinder)||field[y*cols+(x-1+cols)%cols]!==value)segments.push([x,y,x,y+1]);
      if((x===cols-1&&!cylinder)||field[y*cols+(x+1)%cols]!==value)segments.push([x+1,y,x+1,y+1]);
      if(y===0||field[i-cols]!==value)segments.push([x,y,x+1,y]);
      if(y===rows-1||field[i+cols]!==value)segments.push([x,y+1,x+1,y+1]);
    }
    entry.boundaries.set(id,segments);return segments;
  }
  function fineRaster(detail, geometry, style, orbitLighting = false) {
    if (!detail || detail.version!=="planet-detail-v2" ||
        !Number.isInteger(detail.width)||!Number.isInteger(detail.height)||detail.width<1||detail.height<1||detail.width>1024||detail.height>640||
        typeof detail.terrain_grid !== "string" || detail.terrain_grid.length !== detail.width*detail.height ||
        !Array.isArray(detail.elevation) || detail.elevation.length !== detail.width*detail.height) return null;
    const entry=fineGeometry(detail,geometry);
    const rasterKey=orbitLighting?`${style}:orbit`:style;
    if(entry.rasters.has(rasterKey))return entry.rasters.get(rasterKey);
    const canvas=baseRaster(entry.geometry,style,orbitLighting),ctx=canvas.getContext("2d"),scale=canvas.width/detail.width;
    const survey=style==="survey",inked=new Set();
    ctx.strokeStyle=survey?"rgba(48,103,124,.87)":"rgba(66,127,149,.86)";
    ctx.lineCap="round";ctx.lineJoin="round";
    for(const courses of entry.paths.values())for(const course of courses){
      const points=projectRiverPoints(course,detail.width,wrapsX(geometry),scale,0,0),
        middle=(a,b)=>[(a[0]+b[0])/2,(a[1]+b[1])/2],segments=[],
        support=i=>entry.owners.get(Math.round(course[i][1])*detail.width+((Math.round(course[i][0])%detail.width)+detail.width)%detail.width)||1;
      if(points.length===2)segments.push({start:points[0],end:points[1],count:Math.min(support(0),support(1))});
      else if(points.length>2){
        segments.push({start:points[0],end:middle(points[0],points[1]),count:support(0)});
        for(let i=1;i<points.length-1;i++)segments.push({start:middle(points[i-1],points[i]),control:points[i],end:middle(points[i],points[i+1]),count:support(i)});
        segments.push({start:middle(points[points.length-2],points[points.length-1]),end:points[points.length-1],count:support(points.length-1)});
      }
      for(const segment of segments){
        const key=JSON.stringify([segment.start,segment.control,segment.end]);if(inked.has(key))continue;inked.add(key);
        // Width expresses only distinct saved courses sharing this location;
        // no physical discharge or simulated flow value is inferred.
        ctx.lineWidth=clamp((survey?.48:.55)+Math.log2(segment.count)*(survey?.25:.3),survey?.48:.55,survey?1.4:1.65);
        const draw=shift=>{ctx.save();ctx.translate(shift,0);ctx.beginPath();ctx.moveTo(...segment.start);
          if(segment.control)ctx.quadraticCurveTo(...segment.control,...segment.end);else ctx.lineTo(...segment.end);
          ctx.stroke();ctx.restore();};
        draw(0);if(wrapsX(geometry)){draw(-canvas.width);draw(canvas.width);}
      }
    }
    entry.rasters.set(rasterKey,canvas);return canvas;
  }
  function buildOrbitTexture({geometry,detail=null,style="orbital",overlay="terrain",paintOverlay=null}) {
    const source=fineRaster(detail,geometry,style,true)||baseRaster(geometry,style,true),canvas=document.createElement("canvas");
    canvas.width=source.width;canvas.height=source.height;
    const ctx=canvas.getContext("2d");ctx.drawImage(source,0,0);
    if(paintOverlay)paintOverlay(ctx,{tile:canvas.width/geometry.planet.width,ox:0,oy:0,overlay});
    return canvas;
  }
  function traceRiver(ctx,points) {
    if(points.length<2)return;
    const middle=(a,b)=>[(a[0]+b[0])/2,(a[1]+b[1])/2];
    ctx.beginPath();ctx.moveTo(...points[0]);
    if(points.length===2)ctx.lineTo(...points[1]);else{
      ctx.lineTo(...middle(points[0],points[1]));
      for(let i=1;i<points.length-1;i++)ctx.quadraticCurveTo(...points[i],...middle(points[i],points[i+1]));
      ctx.lineTo(...points[points.length-1]);
    }
  }
  function detailAt(geometry, detail, x, y) {
    if (!detail || detail.version!=="planet-detail-v2" || !Number.isFinite(x) || !Number.isFinite(y)) return null;
    const cols=geometry.planet.width,rows=geometry.planet.height;
    if(wrapsX(geometry))x=((x%cols)+cols)%cols;else if(x<0||x>=cols)return null;
    if(y<0||y>=rows)return null;
    const ix=clamp(Math.floor(x*detail.width/cols),0,detail.width-1),
      iy=clamp(Math.floor(y*detail.height/rows),0,detail.height-1),i=iy*detail.width+ix,
      id=detail.feature_ids?.[(detail.feature_index?.[i]||0)-1]||null;
    return {x:ix,y:iy,terrain:detail.terrain_grid[i],elevation:detail.elevation[i],material:detail.materials?.[i]||"0",featureId:id};
  }
  function drawPlanetCopy(
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
      selectedFeatureId = null,
      featureNamesVisible = false,
      overlay = "terrain",
      compact = false,
      sites = [],
      planetId = null,
      safe = null,
      paintOverlay = null,
      labelObstacles = [],
      featureLabelIds = new Set(),
      copyIndex = 0,
      detail = null,
      clearCanvas = true,
      renderPhase = "all",
    },
  ) {
    const { width: cols, height: rows } = geometry.planet,
      bounds = {left:0,right:w,top:0,bottom:h,width:w,height:h},
      tile = Math.min(bounds.width / cols, bounds.height / rows) * zoom,
      gridW = tile * cols,
      gridH = tile * rows,
      ox = (bounds.left + bounds.right - gridW) / 2 + panX + copyIndex*gridW,
      oy = (bounds.top + bounds.bottom - gridH) / 2 + panY;
    const surface=surfaceFor(geometry), preset=surface?.hydrology==="none"?surface.preset:null,
      cylinder=wrapsX(geometry),nativeDetail=detail?.version==="planet-detail-v2",v7=["planet-v7","planet-v8","planet-v9","planet-v10"].includes(surface?.version),
      labelZoom=v7?tile/Math.max(w/cols,h/rows):zoom;
    const detailImage=nativeDetail?fineRaster(detail,geometry,style):null;
    const tiles = geometry.tiles, provinces = geometry.provinces;
    if (renderPhase !== "labels") {
    if(clearCanvas){ctx.fillStyle = preset?terrainPalette(style,preset).ocean:style === "survey" ? "#a6bfc1" : "#142f40";ctx.fillRect(0, 0, w, h);}
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(detailImage || baseRaster(geometry, style), ox, oy, gridW, gridH);
    if (paintOverlay) paintOverlay(ctx, { tile, ox, oy });
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
    ctx.lineWidth = overlay==="provinces"?Math.max(1,Math.min(1.45,tile*.08)):
      v7?Math.max(.4,Math.min(.65,tile*.035)):Math.max(0.8,Math.min(1.15,tile*0.065));
    ctx.strokeStyle =
      overlay === "provinces"
        ? theme === "dark"
          ? "rgba(226,232,216,.72)"
          : "rgba(48,54,48,.66)"
        : v7
          ? theme==="dark"?"rgba(224,229,215,.08)":"rgba(48,54,48,.075)"
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
        const nx = cylinder && dx ? (t.x + dx + cols) % cols : t.x + dx,
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
    if (!(v7 && overlay === "terrain")) ctx.stroke();
    if (selectedProvince && !selectedFeatureId) {
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
          const nx = cylinder && dx ? (t.x + dx + cols) % cols : t.x + dx,
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
    }
    if (renderPhase === "base") return null;
    const labelFont = Math.max(10, Math.min(12, tile * 0.43));
    ctx.font = `700 ${labelFont}px "Noto Instrument Mono",monospace`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    const safeLeft=safe?.left??0,safeRight=safe?.right??w,
      safeTop = (safe?.top ?? 0) + 8,
      safeBottom = Math.min(h - 92, (safe?.bottom ?? h) - 8),
      placed = labelObstacles.map(rect=>({...rect})), provinceTargets = [];
    const clipAnnotations=["planet-v8","planet-v9","planet-v10"].includes(surface?.version);
    if(clipAnnotations){ctx.save();ctx.beginPath();ctx.rect(safeLeft,safeTop,safeRight-safeLeft,Math.max(0,safeBottom-safeTop));ctx.clip();}
    const features=nativeDetail?detail.hydrography.features:surface?.version==="planet-v9"&&surface.hydrography?.version==="hydrography-v1"
      ?surface.hydrography.features:[], selectedFeature=features.find(item=>item.id===selectedFeatureId);
    const riverFor=feature=>surface?.rivers?.find(item=>item.id===feature?.id);
    const fineEntry=detailImage?fineGeometry(detail,geometry):null,
      riverGridCols=fineEntry?detail.width:cols,
      riverScreenPaths=feature=>{
        if(fineEntry)return (fineEntry.paths.get(feature.id)||[]).map(raw=>({raw,points:projectRiverPoints(raw,detail.width,cylinder,tile*cols/detail.width,ox,oy)
          .map(([x],i)=>[x,oy+(raw[i][1]+.5)*tile*rows/detail.height])}));
        const river=riverFor(feature);if(!river)return [];
        const raw=riverShorePoints(surface,river.points||[],cols,cylinder);
        return [{raw,points:projectRiverPoints(raw,cols,cylinder,tile,ox,oy)}];
      };
    if(selectedFeature){
      if(selectedFeature.kind==="river"){
        for(const {points} of riverScreenPaths(selectedFeature))if(points.length>1){ctx.save();ctx.strokeStyle="rgba(43,137,194,.92)";ctx.lineWidth=Math.max(1.9,Math.min(3,tile*.13));ctx.lineCap="round";ctx.lineJoin="round";traceRiver(ctx,points);ctx.stroke();ctx.restore();}
      }else if(fineEntry){
        ctx.save();ctx.strokeStyle="rgba(54,142,198,.92)";ctx.lineWidth=Math.max(1.6,tile*.13);ctx.beginPath();
        const fineTile=tile*cols/detail.width,fineTileY=tile*rows/detail.height;
        for(const [x1,y1,x2,y2] of fineFeatureBoundary(detail,geometry,selectedFeature.id)){
          ctx.moveTo(ox+x1*fineTile,oy+y1*fineTileY);ctx.lineTo(ox+x2*fineTile,oy+y2*fineTileY);
        }
        ctx.stroke();ctx.restore();
      }else{
        const cells=new Set(selectedFeature.cells);ctx.save();ctx.strokeStyle="rgba(54,142,198,.92)";ctx.lineWidth=Math.max(1.6,tile*.13);ctx.beginPath();
        for(const index of selectedFeature.cells){const x=index%cols,y=Math.floor(index/cols),left=ox+x*tile,top=oy+y*tile;
          if(!cells.has(y*cols+(x-1+cols)%cols)||!cylinder&&x===0){ctx.moveTo(left,top);ctx.lineTo(left,top+tile);}
          if(!cells.has(y*cols+(x+1)%cols)||!cylinder&&x===cols-1){ctx.moveTo(left+tile,top);ctx.lineTo(left+tile,top+tile);}
          if(y===0||!cells.has((y-1)*cols+x)){ctx.moveTo(left,top);ctx.lineTo(left+tile,top);}
          if(y===rows-1||!cells.has((y+1)*cols+x)){ctx.moveTo(left,top+tile);ctx.lineTo(left+tile,top+tile);}
        }ctx.stroke();ctx.restore();
      }
    }
    const featureTargets=[];
    if(featureNamesVisible&&features.length){
      const ordered=[...features].filter(item=>typeof item.name==="string"&&item.name.length)
        .sort((a,b)=>Number(b.id===selectedFeatureId)-Number(a.id===selectedFeatureId)||Number(a.kind==="river")-Number(b.kind==="river")||(nativeDetail?a.anchor-b.anchor:a.cells[0]-b.cells[0]));
      const riverOwners=fineEntry?.owners||new Map();
      if(!fineEntry)for(const item of features)if(item.kind==="river")for(const cell of item.cells)riverOwners.set(cell,(riverOwners.get(cell)||0)+1);
      for(const feature of ordered){
        if(featureLabelIds.has(feature.id))continue;
        const anchorIndex=feature.anchor,anchorCols=nativeDetail?detail.width:cols,anchorTile=nativeDetail?tile*cols/detail.width:tile,anchorTileY=nativeDetail?tile*rows/detail.height:tile,
          anchorX=anchorIndex%anchorCols,anchorY=Math.floor(anchorIndex/anchorCols),cellSet=feature.kind==="river"||nativeDetail?null:new Set(feature.cells),
          font=feature.kind==="river"?11:Math.max(11,Math.min(13,tile*.92));
        ctx.save();ctx.font=`${feature.id===selectedFeatureId?700:500} ${font}px "Noto Instrument Mono",monospace`;
        const textWidth=ctx.measureText(feature.name).width,boxHeight=font+4,
          plans=feature.kind==="river"?riverScreenPaths(feature).flatMap(({points,raw})=>riverLabelCandidates(points,raw,riverOwners,riverGridCols,
            {left:safeLeft+3,right:safeRight-3,top:safeTop+3,bottom:safeBottom-3},textWidth)):[{x:ox+(anchorX+.5)*anchorTile,y:oy+(anchorY+.5)*anchorTileY,angle:0}];
        for(const {x,y,angle} of plans){
          const cos=Math.abs(Math.cos(angle)),sin=Math.abs(Math.sin(angle)),aabbWidth=cos*textWidth+sin*boxHeight,aabbHeight=sin*textWidth+cos*boxHeight;
          if(feature.kind!=="river"){
            let fits=true;
            if(!nativeDetail){
            let runX=1,runY=1;for(let d=1;d<cols&&cellSet.has(anchorY*cols+((anchorX+d)%cols));d++)runX++;for(let d=1;d<cols&&cellSet.has(anchorY*cols+((anchorX-d+cols)%cols));d++)runX++;
            for(let d=1;d<rows&&anchorY+d<rows&&cellSet.has((anchorY+d)*cols+anchorX);d++)runY++;for(let d=1;d<rows&&anchorY-d>=0&&cellSet.has((anchorY-d)*cols+anchorX);d++)runY++;
            if(runX*tile<textWidth+8||runY*tile<boxHeight+4){continue;}
            // Every cell under the complete body label must belong to its saved mask.
            for(let cy=Math.floor((y-boxHeight/2-2-oy)/tile);cy<=Math.floor((y+boxHeight/2+2-oy)/tile)&&fits;cy++)
              for(let cx=Math.floor((x-textWidth/2-4-ox)/tile);cx<=Math.floor((x+textWidth/2+4-ox)/tile);cx++)
                if(cy<0||cy>=rows||!cylinder&&(cx<0||cx>=cols)||!cellSet.has(cy*cols+((cx%cols)+cols)%cols)){fits=false;break;}
            }
            if(fits&&fineEntry){
              const fineTile=tile*cols/detail.width,fineTileY=tile*rows/detail.height,owner=detail.feature_ids.indexOf(feature.id)+1;
              for(let fy=Math.floor((y-boxHeight/2-2-oy)/fineTileY);fy<=Math.floor((y+boxHeight/2+2-oy)/fineTileY)&&fits;fy++)
                for(let fx=Math.floor((x-textWidth/2-4-ox)/fineTile);fx<=Math.floor((x+textWidth/2+4-ox)/fineTile);fx++)
                  if(fy<0||fy>=detail.height||!cylinder&&(fx<0||fx>=detail.width)||detail.feature_index[fy*detail.width+((fx%detail.width)+detail.width)%detail.width]!==owner){fits=false;break;}
            }
            if(!fits){continue;}
          }
          const box={left:x-aabbWidth/2-2,right:x+aabbWidth/2+2,top:y-aabbHeight/2-2,bottom:y+aabbHeight/2+2};
          if(box.left<safeLeft+3||box.right>safeRight-3||box.top<safeTop+3||box.bottom>safeBottom-3||placed.some(o=>box.left<o.right&&box.right>o.left&&box.top<o.bottom&&box.bottom>o.top)){continue;}
          placed.push(box);featureLabelIds.add(feature.id);featureTargets.push({id:feature.id,left:box.left,right:box.right,top:box.top,bottom:box.bottom});
          ctx.translate(x,y);ctx.rotate(feature.kind==="river"?angle:0);
          if(feature.id===selectedFeatureId){ctx.fillStyle="rgba(20,42,53,.72)";ctx.fillRect(-textWidth/2-4,-boxHeight/2-3,textWidth+8,boxHeight+6);}
          ctx.lineWidth=2.2;ctx.strokeStyle=feature.kind==="river"?"rgba(9,29,38,.86)":"rgba(18,36,42,.78)";ctx.textAlign="center";ctx.textBaseline="middle";ctx.strokeText(feature.name,0,0);
          ctx.fillStyle=feature.id===selectedFeatureId?"#ffffff":"#f0f1df";ctx.fillText(feature.name,0,0);break;
        }
        ctx.restore();
      }
    }
    const annotations = provinces
      .map((province) => {
        const recorded = provinceLand(geometry).get(province.id);
        if (!recorded || !recorded.tiles.some(t =>
          ox + (t.x + 1) * tile > 0 && oy + (t.y + 1) * tile > 0 &&
          ox + t.x * tile < w && oy + t.y * tile < h)) return null;
        const anchor = recorded.anchor,
          anchorX=ox+(anchor.x+.5)*tile,anchorY=oy+(anchor.y+.5)*tile;
        // Omit other world copies whose anchor is outside the viewport. A
        // north/south occluded holding gets an explicit edge arrow below.
        if(clipAnnotations && (anchorX<safeLeft+8 || anchorX>safeRight-8)) return null;
        const holdings = sites.filter(
            (site) =>
              site.planet_id === planetId && site.province_id === province.id,
          );
        if(surface?.version==="planet-v10"&&overlay!=="provinces"&&!holdings.length&&province.id!==selectedProvince)return null;
        if (overlay !== "provinces" && (compact || labelZoom < (v7?2.5:1.65)) && !holdings.length && province.id !== selectedProvince)
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
          edge:clipAnnotations?(anchorY<safeTop+8?-1:anchorY>safeBottom-8?1:0):0,
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
        if(bw+12>safeRight-safeLeft)continue;
        const x = clamp(item.x + dx, safeLeft+bw/2+6, safeRight-bw/2-6),
          y = clamp(item.y + dy, safeTop + (item.edge===-1?34:bh/2), safeBottom - (item.edge===1?34:bh/2)),
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
        top:Math.max(safeTop,chosen.y-22),bottom:Math.min(safeBottom,chosen.y+22),
        offscreenDirection:item.edge===-1?"north":item.edge===1?"south":null});
      if (item.holdings.length) {
        ctx.fillStyle = "#e4e9cc";ctx.strokeStyle="#1b302e";ctx.lineWidth=2;
        const markerY=item.edge===-1?safeTop+9:item.edge===1?safeBottom-9:item.y;
        ctx.beginPath();
        if(item.edge){ctx.moveTo(item.x,markerY+item.edge*6);ctx.lineTo(item.x-5,markerY-item.edge*3);ctx.lineTo(item.x+5,markerY-item.edge*3);ctx.closePath();}
        else ctx.rect(item.x-4,markerY-4,8,8);
        ctx.fill();ctx.stroke();
        placed.push({left:item.x-8,right:item.x+8,top:markerY-8,bottom:markerY+8});
      }
      if (Math.hypot(item.x - chosen.x, item.y - chosen.y) > 13) {
        if(cylinder){ctx.save();ctx.beginPath();ctx.rect(safeLeft,safeTop,safeRight-safeLeft,Math.max(0,safeBottom-safeTop));ctx.clip();}
        ctx.strokeStyle =
          "rgba(14,28,29,.88)";
        ctx.lineWidth = 2.7;
        ctx.beginPath();
        ctx.moveTo(item.x, item.y);
        ctx.lineTo(chosen.x, chosen.y);
        ctx.stroke();
        if(cylinder)ctx.restore();
      }
      ctx.fillStyle =
        item.holdings.length ? "rgba(16,31,34,.94)" : "rgba(24,40,39,.48)";
      ctx.fillRect(chosen.x - bw / 2, chosen.y - bh / 2, bw, bh);
      ctx.strokeStyle =
        item.holdings.length ? "rgba(204,221,198,.58)" : "rgba(231,229,209,.18)";
      ctx.lineWidth = 0.7;
      ctx.strokeRect(chosen.x - bw / 2, chosen.y - bh / 2, bw, bh);
      ctx.fillStyle = "#edf0df";
      ctx.fillText(label, chosen.x, chosen.y);
    }
    if(clipAnnotations)ctx.restore();
    return { tile, ox, oy, cols, rows, safeRect:safe||bounds, gridW, gridH, viewportWidth:w, viewportHeight:h, forceObstacles: placed, provinceTargets, featureTargets, detailActive:Boolean(detailImage) };
  }
  function drawPlanet(ctx, options) {
    const {geometry,w,h,zoom,panX,panY}=options;
    if(!wrapsX(geometry))return drawPlanetCopy(ctx,options);
    const cols=geometry.planet.width,rows=geometry.planet.height,
      tile=Math.min(w/cols,h/rows)*zoom,gridW=tile*cols,
      baseOx=(w-gridW)/2+panX,
      first=Math.floor(-baseOx/gridW),last=Math.ceil((w-baseOx)/gridW)-1,
      copies=[];
    for(let k=first;k<=last;k++)copies.push(k);
    // Paint every world strip before annotations, which may extend across a
    // strip edge. Share annotation reservations across the visible copies.
    copies.forEach((copyIndex,index)=>drawPlanetCopy(ctx,{...options,copyIndex,clearCanvas:index===0,renderPhase:"base"}));
    const featureLabelIds=new Set(),labelObstacles=[...(options.labelObstacles||[])],
      results=copies.map(copyIndex=>{
        const result=drawPlanetCopy(ctx,{...options,copyIndex,clearCanvas:false,renderPhase:"labels",labelObstacles,featureLabelIds});
        labelObstacles.splice(0,labelObstacles.length,...result.forceObstacles);
        return result;
      }),
      primaryIndex=Math.round((w/2-(baseOx+gridW/2))/gridW),
      primary=results[Math.max(0,copies.indexOf(primaryIndex))]||results[0];
    return {...primary,ox:baseOx,visibleCopies:copies.map(k=>baseOx+k*gridW),
      provinceTargets:results.flatMap(result=>result.provinceTargets||[]),
      featureTargets:results.flatMap(result=>result.featureTargets||[]),
      forceObstacles:results.flatMap(result=>result.forceObstacles||[])};
  }
  function drawOverview(ctx,{geometry,w,h,transform,style="orbital",detail=null}) {
    const {width:cols,height:rows}=geometry.planet,scale=Math.min(w/cols,h/rows),drawW=cols*scale,drawH=rows*scale,
      left=(w-drawW)/2,top=(h-drawH)/2;
    ctx.clearRect(0,0,w,h);ctx.fillStyle="#142f40";ctx.fillRect(0,0,w,h);
    ctx.imageSmoothingEnabled=true;ctx.drawImage(fineRaster(detail,geometry,style)||baseRaster(geometry,style),left,top,drawW,drawH);
    if(transform&&transform.tile>0){
      const rawLeft=(0-transform.ox)/transform.tile,rawRight=(transform.viewportWidth-transform.ox)/transform.tile,
        rect={left:clamp(rawLeft,0,cols),
        top:clamp((0-transform.oy)/transform.tile,0,rows),
        right:clamp(rawRight,0,cols),
        bottom:clamp((transform.viewportHeight-transform.oy)/transform.tile,0,rows)};
      ctx.fillStyle="rgba(245,244,229,.13)";ctx.strokeStyle="#f3f1df";ctx.lineWidth=1.5;
      const drawRect=(x0,x1)=>{if(x1<=x0)return;ctx.fillRect(left+x0*scale,top+rect.top*scale,(x1-x0)*scale,(rect.bottom-rect.top)*scale);ctx.strokeRect(left+x0*scale,top+rect.top*scale,(x1-x0)*scale,(rect.bottom-rect.top)*scale);};
      if(wrapsX(geometry)){
        const span=Math.min(cols,rawRight-rawLeft),start=((rawLeft%cols)+cols)%cols,end=start+span;
        if(end<=cols)drawRect(start,end);else{drawRect(start,cols);drawRect(0,end-cols);}
      }else drawRect(rect.left,rect.right);
    }
    return {left,top,width:drawW,height:drawH,cols,rows};
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
    buildOrbitTexture,
    provinceLand,
    drawHierarchy,
    drawOverview,
    terrainColor(style, key, preset = null) { return terrainPalette(style,preset)[key]; },
    hasSurface(geometry) {
      return Boolean(surfaceFor(geometry));
    },
    wrapsX,
    nearestX,
    featureAt,
    detailAt,
  };
})();
