(() => {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';

  function setup(frame) {
    const bar = document.createElement('div');
    bar.className = 'force-map-controls';
    const toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'button small';
    toggle.textContent = 'Forces';
    toggle.setAttribute('aria-pressed', 'false');
    const cancelButton = document.createElement('button');
    cancelButton.type = 'button';
    cancelButton.className = 'button small force-target-cancel';
    cancelButton.textContent = 'Cancel map targeting';
    cancelButton.hidden = true;
    const hint = document.createElement('span');
    hint.className = 'force-map-hint';
    hint.setAttribute('role', 'status');

    const layer = document.createElement('div');
    layer.className = 'force-map-layer';
    layer.hidden = true;
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('aria-hidden', 'true');
    const defs = document.createElementNS(NS, 'defs');
    const marker = document.createElementNS(NS, 'marker');
    marker.id = 'force-route-arrow';
    marker.setAttribute('viewBox', '0 0 10 10');
    marker.setAttribute('refX', '9');
    marker.setAttribute('refY', '5');
    marker.setAttribute('markerWidth', '5');
    marker.setAttribute('markerHeight', '5');
    marker.setAttribute('orient', 'auto-start-reverse');
    const arrow = document.createElementNS(NS, 'path');
    arrow.setAttribute('d', 'M 0 0 L 10 5 L 0 10 z');
    arrow.setAttribute('fill', 'var(--apple-system-blue)');
    marker.append(arrow);
    defs.append(marker);
    svg.append(defs);
    const routeReadout = document.createElement('div');
    routeReadout.className = 'force-route-readout';
    const list = document.createElement('div');
    list.className = 'force-map-list';
    const counters = document.createElement('div');
    counters.className = 'force-map-counters';
    const legend = document.createElement('div');
    legend.className = 'force-map-legend';
    legend.textContent = 'Recorded connectors · solid transit · dotted draft · dashed validated preview';
    const panels = document.createElement('div');
    panels.className = 'force-map-panels';
    panels.append(routeReadout, list);
    layer.append(svg, legend, counters, panels);
    frame.append(bar, layer);
    bar.append(toggle, cancelButton, hint);

    let visible = false;
    let targeting = null;
    let emptyMessage = '';
    let cancelTargetCallback = () => {};
    toggle.onclick = () => {
      visible = !visible;
      toggle.setAttribute('aria-pressed', String(visible));
      layer.hidden = !visible;
      hint.textContent = visible ? emptyMessage : '';
    };
    cancelButton.onclick = () => {
      targeting = null;
      cancelButton.hidden = true;
      frame.classList.remove('force-targeting');
      hint.textContent = '';
      cancelTargetCallback();
    };
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && targeting) {
        event.preventDefault();
        cancelButton.click();
      }
    });

    function render({width, height, forces = [], routes = [], drafts = [], positions = {}, obstacles = [], emptyMessage: emptyStatus = '', clipToViewport = false, onSelectForce, onMove, onCancelTarget}) {
      cancelTargetCallback = onCancelTarget || (() => {});
      const hasMap = forces.length > 0 || routes.length > 0 || drafts.length > 0;
      emptyMessage = hasMap ? '' : emptyStatus;
      layer.hidden = !visible || !hasMap;
      svg.replaceChildren(defs);
      list.replaceChildren();
      counters.replaceChildren();
      routeReadout.replaceChildren();
      routeReadout.hidden = !routes.length && !drafts.length;
      legend.hidden = !routes.length && !drafts.length;
      if (!targeting) hint.textContent = visible && !hasMap ? emptyMessage : '';
      svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
      svg.setAttribute('width', width);
      svg.setAttribute('height', height);
      svg.style.overflow = clipToViewport ? 'hidden' : '';

      for (const route of [...routes, ...drafts]) {
        const from = positions[route.from];
        const to = positions[route.to];
        const positioned = from && to && [from.x,from.y,to.x,to.y].every(Number.isFinite);
        const readout = document.createElement('div');
        readout.className = 'force-route-readout-item';
        readout.textContent = `${route.label} · ${route.fromLabel || 'Recorded origin'} → ${route.toLabel || 'Recorded destination'}${positioned ? '' : ' · Position unavailable'}`;
        routeReadout.append(readout);
        if (!positioned) continue;
        const segments=Array.isArray(route.segments)?route.segments:[{x1:from.x,y1:from.y,x2:to.x,y2:to.y}];
        for(const segment of segments){
          const line = document.createElementNS(NS, 'line');
          line.setAttribute('x1', segment.x1);
          line.setAttribute('y1', segment.y1);
          line.setAttribute('x2', segment.x2);
          line.setAttribute('y2', segment.y2);
          line.setAttribute('class', route.preview ? 'force-route preview' : route.draft ? 'force-route draft' : 'force-route');
          line.setAttribute('marker-end', 'url(#force-route-arrow)');
          svg.append(line);
        }
      }

      const groups = new Map();
      for (const force of forces) {
        const point = positions[force.anchor];
        if (!point) continue;
        const key = force.anchor;
        if (!groups.has(key)) groups.set(key, {point, items: []});
        groups.get(key).items.push(force);
      }
      // Counter positions are presentation only: stems retain the recorded origin.
      // Reserve the visible chrome and map anchors before trying nearby positions.
      const frameRect = frame.getBoundingClientRect();
      const blocked = obstacles.map(box => ({...box}));
      // Reserve the visible route explanations even before Forces first opens.
      for (const explanation of [routeReadout, legend]) {
        if (explanation.hidden) continue;
        const wasHidden = layer.hidden;
        layer.hidden = false;
        const box = explanation.getBoundingClientRect();
        layer.hidden = wasHidden;
        blocked.push({left:box.left-frameRect.left-4,right:box.right-frameRect.left+4,
          top:box.top-frameRect.top-4,bottom:box.bottom-frameRect.top+4});
      }
      for (const point of Object.values(positions)) blocked.push({
        left:point.x-16, right:point.x+16, top:point.y-16, bottom:point.y+30
      });
      let headerBottom = 0;
      let footerTop = height;
      for (const selector of ['.commandbar', '#resource-shell', '#view-title', '#map-breadcrumbs', '#live-banner', '.map-caption', '#map-legend', '.map-footer', '.force-map-controls']) {
        const node = document.querySelector(selector);
        if (!node || node.hidden || !node.getClientRects().length) continue;
        const box = node.getBoundingClientRect();
        if (['.commandbar','#resource-shell','#view-title','#map-breadcrumbs','#live-banner'].includes(selector)) headerBottom = Math.max(headerBottom,box.bottom-frameRect.top+8);
        if (['.map-caption','#map-legend','.map-footer'].includes(selector)) footerTop = Math.min(footerTop,box.top-frameRect.top-8);
        blocked.push({left:box.left-frameRect.left-6,right:box.right-frameRect.left+6,
          top:box.top-frameRect.top-6,bottom:box.bottom-frameRect.top+6});
      }
      blocked.push({left:0,right:width,top:0,bottom:headerBottom},{left:0,right:width,top:footerTop,bottom:height});
      const overlaps = (a, b) => a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;
      function placeCounter(point, counterWidth) {
        const candidates = [];
        // The same ordered candidates produce a stable arrangement on every redraw.
        for (const radius of [48, 76, 104, 132, 160, 208]) {
          for (let i = 0; i < 16; i++) {
            const angle = -Math.PI/2 + i*Math.PI/8;
            candidates.push({x:point.x+Math.cos(angle)*radius,y:point.y+Math.sin(angle)*radius});
          }
        }
        // Bounded viewport fallback also handles anchors near or beyond an edge.
        for (let y = 30; y < height-25; y += 52) for (let x = counterWidth/2+8; x < width-counterWidth/2-8; x += counterWidth+8) candidates.push({x,y});
        candidates.sort((a,b) => Math.hypot(a.x-point.x,a.y-point.y)-Math.hypot(b.x-point.x,b.y-point.y));
        for (const candidate of candidates) {
          const box = {left:candidate.x-counterWidth/2-4,right:candidate.x+counterWidth/2+4,
            top:candidate.y-26,bottom:candidate.y+26};
          if (box.left < 4 || box.right > width-4 || box.top < 4 || box.bottom > height-4 || blocked.some(other => overlaps(box,other))) continue;
          blocked.push(box);
          return candidate;
        }
        return null;
      }
      for (const [, {point, items}] of [...groups.entries()].sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0)) {
        const owners = new Set(items.map(item => item.owner));
        const counterWidth = Math.max(50, 34 + String(items.length).length*11);
        const placed = placeCounter(point, counterWidth);
        if (!placed) {
          // A fully occupied viewport still exposes each recorded force in the picker.
          showStack(forces, list, onSelectForce, onMove);
          break;
        }
        const {x, y} = placed;
        const stem = document.createElementNS(NS, 'line');
        stem.setAttribute('x1', point.x);
        stem.setAttribute('y1', point.y);
        stem.setAttribute('x2', x);
        stem.setAttribute('y2', y);
        stem.setAttribute('class', `force-counter-stem ${owners.size > 1 ? 'mixed' : owners.has('player') ? 'own' : 'observed'}`);
        svg.append(stem);

        const counter = document.createElement('button');
        counter.type = 'button';
        counter.className = `force-counter ${owners.size > 1 ? 'mixed' : owners.has('player') ? 'own' : 'observed'}`;
        counter.style.width = `${counterWidth}px`;
        counter.style.left = `${x}px`;
        counter.style.top = `${y}px`;
        counter.setAttribute('aria-label', `${items.length} recorded forces: ${items.map(item => `${forceType(item)} ${item.label}`).join(', ')}`);
        const glyph = document.createElement('span');
        glyph.className = items.some(item => item.transport) ? 'transport-glyph' : items.some(item => item.fleet) ? 'fleet-glyph' : 'ground-glyph';
        glyph.setAttribute('aria-hidden', 'true');
        const count = document.createElement('b');
        count.textContent = String(items.length);
        counter.append(glyph, count);
        counter.onclick = () => showStack(items, list, onSelectForce, onMove);
        counters.append(counter);
      }
      if (targeting) {
        cancelButton.hidden = false;
        hint.textContent = 'Choose a destination on the map. Escape cancels.';
        frame.classList.add('force-targeting');
      }
    }

    function showStack(items, root, onSelectForce, onMove) {
      root.replaceChildren();
      const close = document.createElement('button');
      close.type = 'button';
      close.className = 'button small';
      close.textContent = 'Close force list';
      close.onclick = () => root.replaceChildren();
      root.append(close);
      for (const item of items) {
        const card = document.createElement('article');
        card.className = 'force-stack-card';
        const row = document.createElement('div');
        row.className = 'force-stack-row';
        const inspect = document.createElement('button');
        inspect.type = 'button';
        inspect.className = 'force-stack-item';
        inspect.textContent = `${forceType(item)} · ${item.label} · ${item.owner === 'player' ? 'Owned' : item.owner === 'foreign' ? 'Observed' : 'Owner unknown'}`;
        inspect.title = `Recorded ID: ${item.id}`;
        inspect.onclick = () => { root.replaceChildren(); onSelectForce(item); };
        row.append(inspect);
        if (item.canMove) {
          const move = document.createElement('button');
          move.type = 'button';
          move.className = 'button small';
          move.textContent = 'Move';
          move.onclick = () => { root.replaceChildren(); onMove(item); };
          row.append(move);
        }
        card.append(row);
        const facts = [];
        if (Number.isFinite(item.record.strength)) facts.push(`${item.fleet ? 'Strength' : 'Ground strength'} ${item.record.strength}`);
        if (Number.isFinite(item.record.crew)) facts.push(`Crew ${item.record.crew}`);
        if (Number.isFinite(item.record.readiness)) facts.push(`Readiness ${item.record.readiness}%`);
        if (facts.length) {
          const metadata = document.createElement('small');
          metadata.className = 'force-stack-facts';
          metadata.textContent = facts.join(' · ');
          card.append(metadata);
        }
        const details = document.createElement('details');
        details.className = 'force-stack-id';
        const summary = document.createElement('summary');
        summary.textContent = 'Recorded ID';
        const id = document.createElement('code');
        id.textContent = item.id;
        details.append(summary, id);
        card.append(details);
        root.append(card);
      }
    }

    function forceType(item) {
      return item.transport ? 'Transport' : item.fleet ? 'Fleet' : 'Ground';
    }

    return {
      render,
      beginTarget(item) {
        targeting = item;
        visible = true;
        toggle.setAttribute('aria-pressed', 'true');
        layer.hidden = false;
        cancelButton.hidden = false;
        hint.textContent = 'Choose a destination on the map. Escape cancels.';
        frame.classList.add('force-targeting');
      },
      cancelTarget() {
        targeting = null;
        cancelButton.hidden = true;
        frame.classList.remove('force-targeting');
        hint.textContent = '';
      },
      targeting() { return targeting; },
      completeTarget() {
        targeting = null;
        cancelButton.hidden = true;
        frame.classList.remove('force-targeting');
      }
    };
  }

  window.HWMilitaryMap = {setup};
})();
