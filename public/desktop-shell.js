(() => {
  'use strict';
  const entries = new Map();
  const shell = {active:null,workspace:null,inspector:null,dialog:null,dialogReturnFocus:null,onOpen:null,onCreate:null,gesture:false,touchMenu:false,edgeEnabled:false,edgeTimers:{show:null,hide:null}};
  function register(id,title,node,options={}) {
    let entry=entries.get(id);
    if(entry){if(node)entry.node=node;entry.title=title||entry.title;return entry;}
    entry={id,title,node:node||null,options,shown:false,minimized:false};entries.set(id,entry);return entry;
  }
  function setActive(id) {
    let item=entries.get(id);
    if(!item&&shell.onCreate)item=shell.onCreate(id);
    if(!item)return;
    const prior=entries.get(shell.active);if(prior&&prior.id!==id)prior.shown=false;
    item.shown=true;item.minimized=false;
    if(id==='planet'){returnToMap();return;}
    if(id==='campaign'){showDialog(item);return;}
    if(id==='inspector'){showInspector(item);return;}
    const previous=entries.get(shell.active);if(previous&&shell.workspace.querySelector('.workspace-content'))previous.scrollTop=shell.workspace.querySelector('.workspace-content').scrollTop;
    shell.active=id;
    const body=shell.workspace.querySelector('.workspace-content');
    for(const node of body.children)node.hidden=true;
    if(item.node){if(item.node.parentElement!==body)body.append(item.node);item.node.removeAttribute('hidden');}
    body.scrollTop=item.scrollTop||0;
    shell.workspace.hidden=false;shell.workspace.querySelector('.workspace-title').textContent=item.title;
    updateTabs(id);
    hideInspector();closeDialog();
    body.focus();
    if(shell.onOpen)shell.onOpen(id);
  }
  function hideWorkspace(){if(shell.workspace)shell.workspace.hidden=true;if(shell.active){const old=entries.get(shell.active);if(old)old.shown=false;}shell.active=null;}
  function returnToMap(){hideWorkspace();hideInspector();closeDialog();const menu=document.querySelector('#command-menu');if(menu){menu.hidden=true;document.querySelector('#hw-command').setAttribute('aria-expanded','false');}document.querySelector('#hw-command')?.focus();if(shell.onOpen)shell.onOpen('planet');}
  function hideInspector(){if(shell.inspector)shell.inspector.hidden=true;const item=entries.get('inspector');if(item)item.shown=false;}
  function collapseInspector(){hideInspector();document.querySelector('#hw-command')?.focus();if(shell.onOpen)shell.onOpen('planet');}
  function showInspector(item){shell.inspector.hidden=false;item.shown=true;hideWorkspace();closeDialog();shell.inspector.focus();}
  function showDialog(item){shell.dialogReturnFocus=document.querySelector('#hw-command');shell.dialog.hidden=false;document.querySelector('.command-backdrop').hidden=false;item.shown=true;hideWorkspace();hideInspector();if(shell.onOpen)shell.onOpen('campaign');const first=[...shell.dialog.querySelectorAll('button:not([disabled]),select:not([disabled]),input:not([type=hidden]):not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])')].find(node=>node.getClientRects().length&&!node.closest('[hidden]'));(first||shell.dialog).focus();}
  function closeDialog(){const wasOpen=shell.dialog&&!shell.dialog.hidden;if(shell.dialog)shell.dialog.hidden=true;const backdrop=document.querySelector('.command-backdrop');if(backdrop)backdrop.hidden=true;const item=entries.get('campaign');if(item)item.shown=false;if(wasOpen){const target=shell.dialogReturnFocus?.isConnected&&!shell.dialogReturnFocus.closest('[hidden]')?shell.dialogReturnFocus:document.querySelector('#hw-command');target?.focus();}shell.dialogReturnFocus=null;}
  const relatedGroups=[['economy','construction','industry','budget'],['military','fleet','logistics'],['politics','diplomacy','factions','trade'],['intelligence','exploration'],['history','turn','log'],['research'],['colonies'],['characters'],['orders']];
  const iconFor={
    map:'M3 5 9 3l6 2 6-2v16l-6 2-6-2-6 2zM9 3v16M15 5v16',inspector:'M3 4h18v13H3zM8 21h8M12 17v4M7 8h10M7 12h6',campaign:'M4 21V5l8-3 8 3v16l-8-3zM12 2v16M8 8h1M15 8h1',
    economy:'M3 12h18M5 8h14M7 4h10M7 16h10M9 20h6',construction:'M4 20 12 4l8 16M7 14h10',industry:'M4 20V9l5 4V7l5 5V4l6 4v12z',budget:'M12 3v18M17 7.5c0-2-2-3-5-3s-5 1-5 3 2 3 5 4 5 2 5 4.5-2 4-5 4-5-1.5-5-4',
    military:'M12 3 20 7v5c0 5-4 8-8 10-4-2-8-5-8-10V7z',fleet:'M2 15h20l-3 5H6zM5 12h14M8 9h8M11 3h2v9',logistics:'M3 6h11v11H3zM14 10h4l3 4v3h-7zM7 20h.01M18 20h.01',
    politics:'M3 21h18M5 18V9h3v9M10 18V5h4v13M16 18v-6h3v6M3 8l9-5 9 5',diplomacy:'M3 8h7l2 2 2-2h7M5 8v8l7 5 7-5V8M8 12l4 3 4-3',factions:'M12 3 14.7 8.5 21 9.4l-4.5 4.4 1.1 6.2L12 17l-5.6 3 1.1-6.2L3 9.4l6.3-.9z',trade:'M7 7h14l-3-3M17 17H3l3 3M21 7l-4 4M3 17l4-4',
    intelligence:'M2 12s3-7 10-7 10 7 10 7-3 7-10 7S2 12 2 12zM12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6',exploration:'M12 2v20M2 12h20M5 5l14 14M19 5 5 19M12 2l3 7-3 3-3-3z',research:'M9 3h6M10 3v6l-5 9a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-9V3M8 15h8',
    colonies:'M3 20h18M5 20v-7l4-3 4 3v7M13 20v-9l3-3 3 3v9M7 14h1M16 12h1',characters:'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8M4 21a8 8 0 0 1 16 0M18 4h4M20 2v4',history:'M3 12a9 9 0 1 0 3-6M3 4v5h5M12 7v5l4 2',turn:'M4 7h16M4 12h11M4 17h7M17 10l3 2-3 2',log:'M5 3h14v18H5zM8 7h8M8 11h8M8 15h5',orders:'M4 5h16M4 12h11M4 19h7M17 16l3 3-3 3',default:'M4 5h16v14H4zM8 9h8M8 13h8M8 16h5'};
  const iconFamily={economy:'mint',industry:'mint',budget:'mint',trade:'mint',construction:'orange',logistics:'orange',colonies:'orange',military:'indigo',fleet:'indigo',research:'teal',intelligence:'teal',exploration:'teal',politics:'blue',diplomacy:'blue',factions:'blue',characters:'blue',history:'blue',turn:'blue',log:'blue',orders:'blue',campaign:'blue',inspector:'blue',map:'blue'};
  function labelWithIcon(label,id){const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('class',`command-icon icon-${iconFamily[id]||'blue'}`);svg.setAttribute('viewBox','0 0 24 24');svg.setAttribute('aria-hidden','true');const path=document.createElementNS(svg.namespaceURI,'path');path.setAttribute('d',iconFor[id]||iconFor.default);svg.append(path);const span=document.createElement('span');span.textContent=label;return [svg,span];}
  const tabButtons=new Map();
  function updateTabs(id){const group=relatedGroups.find(items=>items.includes(id))||[id];const root=shell.workspace.querySelector('.workspace-tabs');root.replaceChildren();for(const key of group){const tab=tabButtons.get(key);if(tab){tab.classList.toggle('active',key===id);tab.setAttribute('aria-pressed',String(key===id));root.append(tab);}}}
  function close(id){if(id==='inspector'){hideInspector();return;}if(id==='campaign'){closeDialog();return;}if(id==='planet')return;if(shell.active===id)hideWorkspace();const item=entries.get(id);if(item)item.shown=false;}
  function clear(){hideWorkspace();hideInspector();closeDialog();const menu=document.querySelector('#command-menu');if(menu){menu.hidden=true;document.querySelector('#hw-command').setAttribute('aria-expanded','false');}}
  function build(){
    const root=document.createElement('div');root.id='desktop-shell';
    root.innerHTML='<div id="map-backdrop"></div><header class="commandbar"><button id="hw-command" type="button" aria-label="Open command menu" aria-expanded="false"><span aria-hidden="true">☰</span><b>MENU</b></button><div class="command-brand">HAMMER WORLD <span>STRATEGIC COMMAND</span></div><div class="campaign-indicator"><label for="campaign-select">CAMPAIGN</label><span id="command-campaign">UNSELECTED</span></div><div class="command-indicators"><span id="command-turn">TURN —</span><span id="command-snapshot" hidden></span><span id="command-history" hidden>HISTORICAL</span><span id="command-pending" hidden>ARCHIVE PENDING</span></div></header><div id="resource-shell"></div><nav id="command-menu" hidden aria-label="Strategic command menu"><div class="menu-head"><strong>COMMANDS</strong><button class="button small" data-menu-close>Close</button></div><div class="menu-map"><button data-open="planet">Map overview</button><button data-open="inspector">Inspect selection</button></div><div class="menu-grid"></div></nav><section id="command-workspace" hidden aria-label="Management workspace"><header class="workspace-head"><button class="button small" data-return-map>← Map</button><div><small>COMMAND STATION</small><strong class="workspace-title"></strong><span class="workspace-scope"></span></div><button class="button small" data-workspace-inspect aria-label="Inspect selected record">Inspect</button><button class="button small" data-workspace-close aria-label="Return to map">×</button></header><nav class="workspace-tabs" aria-label="Related views"></nav><div class="workspace-content" tabindex="-1"></div></section><aside id="command-inspector" hidden aria-label="Selected record"><header><strong>SELECTED RECORD</strong><button class="button small" data-inspector-close aria-label="Collapse inspector">×</button></header><div class="inspector-holder"></div></aside><section id="command-dialog" hidden role="dialog" aria-modal="true" aria-labelledby="command-dialog-title" tabindex="-1"><div class="dialog-title"><strong id="command-dialog-title">CAMPAIGN & ACCESS</strong><button class="button small" data-dialog-close>Close</button></div><div class="dialog-content"></div></section><div class="command-backdrop" hidden></div>';
    document.body.append(root);
    const frame=document.querySelector('.map-frame'), tools=document.querySelector('.map-tools'),crumb=document.querySelector('#map-breadcrumbs'),panel=document.querySelector('#map-panel'),title=document.querySelector('#view-title');
    const map=document.createElement('div');map.className='map-command-layer';map.append(title,crumb,panel);root.querySelector('#map-backdrop').append(frame,map);
    const review=document.createElement('div');review.className='map-review-placeholder';review.setAttribute('aria-label','Temporary map artwork, unrelated to recorded map data');
    review.innerHTML='<div class="review-center"><strong>TEMPORARY MAP ARTWORK</strong><span>UI review only · unrelated to recorded map</span></div>';
    review.hidden=new URLSearchParams(location.search).get('map')!=='placeholder';root.querySelector('#map-backdrop').append(review);
    const resources=document.querySelector('#resource-strip');root.querySelector('#resource-shell').append(resources);
    const camp=document.createElement('div');camp.className='campaign-dialog-body';const summary=document.createElement('section');summary.className='campaign-current-summary';const summaryTitle=document.createElement('div');summaryTitle.className='inspector-section';summaryTitle.textContent='CURRENT CAMPAIGN STATUS';summary.append(summaryTitle);const campaignLabel=document.createElement('label');campaignLabel.className='campaign-dialog-select-label';campaignLabel.htmlFor='dialog-campaign-select';campaignLabel.textContent='Campaign';const dialogCampaignSelect=document.createElement('select');dialogCampaignSelect.id='dialog-campaign-select';dialogCampaignSelect.disabled=true;dialogCampaignSelect.append(new Option('Select campaign…',''));dialogCampaignSelect.onchange=()=>{const main=document.querySelector('#campaign-select');main.value=dialogCampaignSelect.value;main.dispatchEvent(new Event('change',{bubbles:true}));};const dialogRefresh=document.createElement('button');dialogRefresh.type='button';dialogRefresh.id='dialog-refresh-campaigns';dialogRefresh.className='button small';dialogRefresh.textContent='Refresh campaigns';dialogRefresh.disabled=true;dialogRefresh.onclick=()=>document.querySelector('#refresh-button')?.click();summary.append(campaignLabel,dialogCampaignSelect,dialogRefresh);const summaryFacts=document.createElement('dl');for(const [key,label,value]of [['campaign','Campaign','Unknown'],['turn','Turn','Unknown'],['view','View','No snapshot'],['archive','Archive','Unknown'],['access','Access','Unknown']]){const fact=document.createElement('div'),dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=label;dd.dataset.summary=key;dd.textContent=value;fact.append(dt,dd);summaryFacts.append(fact);}summary.append(summaryFacts);camp.append(summary,document.querySelector('.campaign-ribbon'),document.querySelector('.access-box'));root.querySelector('#command-dialog .dialog-content').append(camp);
    shell.workspace=root.querySelector('#command-workspace');shell.inspector=root.querySelector('#command-inspector');shell.dialog=root.querySelector('#command-dialog');shell.inspector.tabIndex=-1;
    register('planet','Map',map);register('campaign','Campaign & access',camp);
    const inspector=document.createElement('div');inspector.className='inspector-holder-inner';inspector.append(document.querySelector('#inspector-content'));shell.inspector.querySelector('.inspector-holder').append(inspector);register('inspector','Selected record',inspector);
    const tabs=[['economy','Economy'],['industry','Industry'],['construction','Construction'],['research','Research'],['military','Military'],['fleet','Fleet'],['logistics','Logistics'],['budget','Budget'],['politics','Politics'],['trade','Trade'],['diplomacy','Diplomacy'],['factions','Factions'],['intelligence','Intelligence'],['exploration','Exploration'],['colonies','Colonies'],['characters','Characters'],['history','History'],['orders','Orders & handoff'],['turn','Turn report'],['log','Command log']];
    for(const [id,label] of tabs){let node=document.querySelector(`#${id}-panel`);if(id==='turn')node=document.querySelector('#turn-window');if(id==='log')node=document.querySelector('#log-window');const registerHere=['economy','history','orders','turn','log'].includes(id);if(registerHere)register(id,label,node);
      const tab=document.createElement('button');tab.type='button';tab.append(...labelWithIcon(label,id));tab.dataset.tab=id;tab.onclick=()=>setActive(id);tabButtons.set(id,tab);
    }
    for(const item of entries.values())if(item.node&&['economy','history','orders','turn','log'].includes(item.id)){item.node.hidden=true;shell.workspace.querySelector('.workspace-content').append(item.node);}
    const campaignSelect=document.querySelector('#campaign-select'), refresh=document.querySelector('#refresh-button');
    root.querySelector('.campaign-indicator').append(campaignSelect);refresh.textContent='↻';refresh.setAttribute('aria-label','Refresh campaign');root.querySelector('.command-indicators').append(refresh);
    const zoomControls=document.createElement('div');zoomControls.className='map-zoom-controls';
    zoomControls.append(...['zoom-out','zoom-reset','zoom-in','map-recenter'].map(id=>document.getElementById(id)));tools.append(zoomControls);
    // Keep chart chrome in document flow; its height changes with content and zoom.
    const heading=document.createElement('div');heading.id='chart-heading';
    heading.append(root.querySelector('.commandbar'),root.querySelector('#resource-shell'),title,crumb,document.querySelector('#live-banner'));root.append(heading);
    const readouts=document.createElement('div');readouts.id='chart-readouts';
    readouts.append(panel.querySelector('.map-caption'),panel.querySelector('#map-legend'),panel.querySelector('.map-footer'));panel.append(readouts);
    const measureHeading=()=>root.style.setProperty('--chart-heading-height',`${heading.offsetHeight}px`);
    new ResizeObserver(measureHeading).observe(heading);measureHeading();
    const menu=root.querySelector('#command-menu'),menuGrid=menu.querySelector('.menu-grid');
    const previewStatus=document.createElement('span');previewStatus.id='command-preview';previewStatus.textContent='PREVIEW READY';previewStatus.hidden=true;root.querySelector('.command-indicators').insertBefore(previewStatus,root.querySelector('#command-history'));
    const appearanceLabel=document.createElement('label');appearanceLabel.className='appearance-setting';appearanceLabel.htmlFor='appearance-select';appearanceLabel.append(document.createTextNode('Appearance'));const appearanceSelect=document.createElement('select');appearanceSelect.id='appearance-select';appearanceSelect.setAttribute('aria-label','Appearance');for(const [value,label] of [['system','System'],['light','Light'],['dark','Dark']])appearanceSelect.append(new Option(label,value));appearanceSelect.value=window.HWTheme?.preference||'system';appearanceSelect.onchange=()=>window.HWTheme?.set(appearanceSelect.value);appearanceLabel.append(appearanceSelect);menu.append(appearanceLabel);
    const edgeLabel=document.createElement('label');edgeLabel.className='edge-setting';const edgeToggle=document.createElement('input');edgeToggle.type='checkbox';edgeToggle.id='edge-shortcut';edgeLabel.append(edgeToggle,document.createTextNode(' Reveal menu at screen edge'));menu.append(edgeLabel);
    const mapLabel=document.createElement('label');mapLabel.className='edge-setting';const mapToggle=document.createElement('input');mapToggle.type='checkbox';mapToggle.id='temporary-map-toggle';mapToggle.checked=!review.hidden;mapLabel.append(mapToggle,document.createTextNode(' Temporary map artwork'));menu.append(mapLabel);
    mapToggle.onchange=()=>{review.hidden=!mapToggle.checked;};
    try{shell.edgeEnabled=localStorage.getItem('hw.command.edge.v1')==='true';}catch{shell.edgeEnabled=false;}edgeToggle.checked=shell.edgeEnabled;
    const menuGroups=[
      ['Campaign',[['campaign','Campaign & access']]],
      ['Economy',[['economy','Economy'],['construction','Construction'],['industry','Industry'],['budget','Budget']]],
      ['Forces',[['military','Military'],['fleet','Fleet'],['logistics','Logistics']]],
      ['Politics & trade',[['politics','Politics'],['diplomacy','Diplomacy'],['factions','Factions'],['trade','Trade']]],
      ['Intelligence',[['intelligence','Intelligence'],['exploration','Exploration'],['research','Research']]],
      ['Records',[['colonies','Colonies'],['characters','Characters'],['history','History & turn log'],['orders','Orders & handoff']]]
    ];
    for(const [group,items] of menuGroups){const section=document.createElement('section');section.className=`menu-group${group==='Campaign'?' menu-group-campaign':''}`;section.append(Object.assign(document.createElement('h3'),{className:'menu-group-title',textContent:group}));const links=document.createElement('div');links.className='menu-group-links';for(const [id,label]of items){const b=document.createElement('button');b.append(...labelWithIcon(label,id));b.dataset.open=id;b.onclick=()=>{menu.hidden=true;root.querySelector('#hw-command').setAttribute('aria-expanded','false');shell.touchMenu=false;setActive(id);};links.append(b);}section.append(links);menuGrid.append(section);}
    for(const [id,label]of [['planet','Map overview'],['inspector','Inspect selection']]){const button=root.querySelector(`[data-open="${id}"]`);button.replaceChildren(...labelWithIcon(label,id));}
    root.querySelectorAll('[data-open="planet"]').forEach(b=>b.onclick=returnToMap);
    root.querySelector('[data-open="inspector"]').onclick=()=>{menu.hidden=true;root.querySelector('#hw-command').setAttribute('aria-expanded','false');showInspector(entries.get('inspector'));shell.inspector.focus();};
    const cancelEdgeTimers=()=>{clearTimeout(shell.edgeTimers.show);clearTimeout(shell.edgeTimers.hide);shell.edgeTimers.show=shell.edgeTimers.hide=null;};
    const setMenu=open=>{cancelEdgeTimers();menu.hidden=!open;root.querySelector('#hw-command').setAttribute('aria-expanded',String(open));if(!open)shell.touchMenu=false;if(open)menu.querySelector('button')?.focus();};
    edgeToggle.onchange=()=>{shell.edgeEnabled=edgeToggle.checked;try{localStorage.setItem('hw.command.edge.v1',String(shell.edgeEnabled));}catch{}cancelEdgeTimers();};
    root.querySelector('#hw-command').addEventListener('pointerdown',event=>{shell.touchMenu=event.pointerType==='touch';});
    root.querySelector('#hw-command').onclick=()=>setMenu(menu.hidden);
    root.querySelectorAll('[data-menu-close]').forEach(b=>b.onclick=()=>{setMenu(false);root.querySelector('#hw-command').focus();});
    root.querySelectorAll('[data-return-map],[data-workspace-close]').forEach(b=>b.onclick=returnToMap);
    root.querySelector('[data-workspace-inspect]').onclick=()=>{showInspector(entries.get('inspector'));};
    root.querySelector('[data-inspector-close]').onclick=collapseInspector;
    root.querySelector('[data-dialog-close]').onclick=closeDialog;
    const backdrop=root.querySelector('.command-backdrop');backdrop.onclick=closeDialog;
    document.addEventListener('pointermove',event=>{if(!shell.edgeEnabled||shell.gesture||event.pointerType==='touch'||shell.touchMenu)return;if(event.clientX<=3){clearTimeout(shell.edgeTimers.hide);clearTimeout(shell.edgeTimers.show);if(menu.hidden)shell.edgeTimers.show=setTimeout(()=>setMenu(true),240);}else if(!menu.matches(':hover')){clearTimeout(shell.edgeTimers.show);clearTimeout(shell.edgeTimers.hide);if(!menu.hidden)shell.edgeTimers.hide=setTimeout(()=>setMenu(false),460);}});
    menu.addEventListener('pointerenter',()=>clearTimeout(shell.edgeTimers.hide));menu.addEventListener('pointerleave',()=>{if(shell.edgeEnabled&&!shell.gesture&&!shell.touchMenu)shell.edgeTimers.hide=setTimeout(()=>setMenu(false),460);});
    document.addEventListener('keydown',e=>{
      if(!shell.dialog.hidden&&e.key==='Tab'){
        const focusable=[...shell.dialog.querySelectorAll('button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),[tabindex]:not([tabindex="-1"])')].filter(node=>node.getClientRects().length>0);
        if(focusable.length){const first=focusable[0],last=focusable.at(-1);if(!shell.dialog.contains(document.activeElement)){e.preventDefault();first.focus();}else if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}
        else{e.preventDefault();shell.dialog.focus();}
      }
      if(e.key==='Escape'){setMenu(false);if(!shell.dialog.hidden)closeDialog();else if(!shell.workspace.hidden)returnToMap();else collapseInspector();}
    });
    window.addEventListener('resize',()=>{});
    shell.open=setActive;shell.createWindow=register;
  }
  window.HWDesktop={init:build,open:id=>shell.open?.(id),close,clear,resetLayout(){},setOnOpen(fn){shell.onOpen=fn;},setOnFocus(){},setOnCreate(fn){shell.onCreate=fn;},setGesture(value){shell.gesture=Boolean(value);if(shell.gesture){clearTimeout(shell.edgeTimers.show);clearTimeout(shell.edgeTimers.hide);}},setPinned(){},get gesture(){return shell.gesture;},get windows(){return entries;},createWindow:(...args)=>shell.createWindow(...args),has(id){return entries.has(id);},returnMap:returnToMap,positionInspector(x){shell.inspector.classList.toggle('dock-left',Number.isFinite(x)&&x>innerWidth/2);},setPreviewReady(value){const p=document.querySelector('#command-preview');if(p)p.hidden=!value;},refreshIndicators({campaign,campaignSummary,hasSnapshot,kind,turn,historical,pending,snapshotTime,previewReady,archive,access}={}){const c=document.querySelector('#command-campaign');if(c)c.textContent=campaign||'UNSELECTED';const t=document.querySelector('#command-turn');if(t)t.textContent=turn==null?'TURN —':`TURN ${turn}`;const d=document.querySelector('#command-snapshot');if(d){d.textContent=snapshotTime||'';d.hidden=!snapshotTime;}const h=document.querySelector('#command-history');if(h)h.hidden=!historical;const p=document.querySelector('#command-pending');if(p)p.hidden=!pending;const pr=document.querySelector('#command-preview');if(pr)pr.hidden=!previewReady;const summary=document.querySelector('.campaign-current-summary');if(summary){summary.querySelector('[data-summary="campaign"]').textContent=campaignSummary||'No campaign selected';summary.querySelector('[data-summary="turn"]').textContent=turn==null?'Unknown':String(turn);summary.querySelector('[data-summary="view"]').textContent=!hasSnapshot?'No snapshot':historical?'Historical · read only':'Live revision';summary.querySelector('[data-summary="archive"]').textContent=archive||'unknown';summary.querySelector('[data-summary="access"]').textContent=access||'Unknown';}},setScope(value){const n=document.querySelector('.workspace-scope');if(n)n.textContent=value||'';}};
})();
