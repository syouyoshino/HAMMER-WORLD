(() => {
  'use strict';
  const entries = new Map();
  const shell = {active:null,workspace:null,inspector:null,dialog:null,onOpen:null,onCreate:null,gesture:false,touchMenu:false,edgeEnabled:false,edgeTimers:{show:null,hide:null}};
  function register(id,title,node,options={}) {
    let entry=entries.get(id);
    if(entry){if(node)entry.node=node;entry.title=title||entry.title;return entry;}
    entry={id,title,node:node||null,options,shown:false,minimized:false};entries.set(id,entry);return entry;
  }
  function setActive(id) {
    let item=entries.get(id);
    if(!item&&shell.onCreate)item=shell.onCreate(id);
    if(!item)return;
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
  function showDialog(item){shell.dialog.hidden=false;document.querySelector('.command-backdrop').hidden=false;item.shown=true;hideWorkspace();hideInspector();if(shell.onOpen)shell.onOpen('campaign');shell.dialog.querySelector('input:not([type=hidden])')?.focus();}
  function closeDialog(){if(shell.dialog)shell.dialog.hidden=true;const backdrop=document.querySelector('.command-backdrop');if(backdrop)backdrop.hidden=true;const item=entries.get('campaign');if(item)item.shown=false;document.querySelector('#hw-command')?.focus();}
  const relatedGroups=[['economy','construction','industry','budget'],['military','fleet','logistics'],['politics','diplomacy','factions','trade'],['intelligence','exploration'],['history','turn','log'],['research'],['colonies'],['characters'],['orders']];
  const tabButtons=new Map();
  function updateTabs(id){const group=relatedGroups.find(items=>items.includes(id))||[id];const root=shell.workspace.querySelector('.workspace-tabs');root.replaceChildren();for(const key of group){const tab=tabButtons.get(key);if(tab){tab.classList.toggle('active',key===id);root.append(tab);}}}
  function close(id){if(id==='inspector'){hideInspector();return;}if(id==='campaign'){closeDialog();return;}if(id==='planet')return;if(shell.active===id)hideWorkspace();const item=entries.get(id);if(item)item.shown=false;}
  function clear(){hideWorkspace();hideInspector();closeDialog();const menu=document.querySelector('#command-menu');if(menu){menu.hidden=true;document.querySelector('#hw-command').setAttribute('aria-expanded','false');}}
  function build(){
    const root=document.createElement('div');root.id='desktop-shell';
    root.innerHTML='<div id="map-backdrop"></div><header class="commandbar"><button id="hw-command" type="button" aria-label="Open command menu" aria-expanded="false"><span aria-hidden="true">☰</span><b>MENU</b></button><div class="command-brand">HAMMER WORLD <span>STRATEGIC COMMAND</span></div><div class="campaign-indicator"><label for="campaign-select">CAMPAIGN</label><span id="command-campaign">UNSELECTED</span></div><div class="command-indicators"><span id="command-turn">TURN —</span><span id="command-snapshot" hidden></span><span id="command-history" hidden>HISTORICAL</span><span id="command-pending" hidden>ARCHIVE PENDING</span></div></header><div id="resource-shell"></div><nav id="command-menu" hidden aria-label="Strategic command menu"><div class="menu-head"><strong>COMMANDS</strong><button class="button small" data-menu-close>Close</button></div><div class="menu-map"><button data-open="planet">Map overview</button><button data-open="inspector">Inspect selection</button></div><div class="menu-grid"></div></nav><section id="command-workspace" hidden aria-label="Management workspace"><header class="workspace-head"><button class="button small" data-return-map>← Map</button><div><small>COMMAND WORKSPACE</small><strong class="workspace-title"></strong><span class="workspace-scope"></span></div><button class="button small" data-workspace-inspect>Inspect selection</button><button class="button small" data-workspace-close aria-label="Return to map">×</button></header><nav class="workspace-tabs" aria-label="Related views"></nav><div class="workspace-content" tabindex="-1"></div></section><aside id="command-inspector" hidden aria-label="Selected record"><header><strong>SELECTED RECORD</strong><button class="button small" data-inspector-close aria-label="Collapse inspector">×</button></header><div class="inspector-holder"></div></aside><section id="command-dialog" hidden role="dialog" aria-modal="true"><div class="dialog-title"><strong>CAMPAIGN & ACCESS</strong><button class="button small" data-dialog-close>Close</button></div><div class="dialog-content"></div></section><div class="command-backdrop" hidden></div>';
    document.body.append(root);
    const frame=document.querySelector('.map-frame'), tools=document.querySelector('.map-tools'),crumb=document.querySelector('#map-breadcrumbs'),panel=document.querySelector('#map-panel'),title=document.querySelector('#view-title');
    const map=document.createElement('div');map.className='map-command-layer';map.append(title,crumb,panel);root.querySelector('#map-backdrop').append(frame,map);
    const resources=document.querySelector('#resource-strip');root.querySelector('#resource-shell').append(resources);
    const camp=document.createElement('div');camp.className='campaign-dialog-body';camp.append(document.querySelector('.campaign-ribbon'),document.querySelector('.access-box'));root.querySelector('#command-dialog .dialog-content').append(camp);
    shell.workspace=root.querySelector('#command-workspace');shell.inspector=root.querySelector('#command-inspector');shell.dialog=root.querySelector('#command-dialog');shell.inspector.tabIndex=-1;
    register('planet','Map',map);register('campaign','Campaign & access',camp);
    const inspector=document.createElement('div');inspector.className='inspector-holder-inner';inspector.append(document.querySelector('#inspector-content'));shell.inspector.querySelector('.inspector-holder').append(inspector);register('inspector','Selected record',inspector);
    const tabs=[['economy','Economy'],['industry','Industry'],['construction','Construction'],['research','Research'],['military','Military'],['fleet','Fleet'],['logistics','Logistics'],['budget','Budget'],['politics','Politics'],['trade','Trade'],['diplomacy','Diplomacy'],['factions','Factions'],['intelligence','Intelligence'],['exploration','Exploration'],['colonies','Colonies'],['characters','Characters'],['history','History'],['orders','Orders & handoff'],['turn','Turn report'],['log','Command log']];
    for(const [id,label] of tabs){let node=document.querySelector(`#${id}-panel`);if(id==='turn')node=document.querySelector('#turn-window');if(id==='log')node=document.querySelector('#log-window');const registerHere=['economy','history','orders','turn','log'].includes(id);if(registerHere)register(id,label,node);
      const tab=document.createElement('button');tab.type='button';tab.textContent=label;tab.dataset.tab=id;tab.onclick=()=>setActive(id);tabButtons.set(id,tab);
    }
    for(const item of entries.values())if(item.node&&['economy','history','orders','turn','log'].includes(item.id)){item.node.hidden=true;shell.workspace.querySelector('.workspace-content').append(item.node);}
    const campaignSelect=document.querySelector('#campaign-select'), refresh=document.querySelector('#refresh-button');
    root.querySelector('.campaign-indicator').append(campaignSelect);refresh.textContent='↻';refresh.setAttribute('aria-label','Refresh campaign');root.querySelector('.command-indicators').append(refresh);
    const menu=root.querySelector('#command-menu'),menuGrid=menu.querySelector('.menu-grid');
    const previewStatus=document.createElement('span');previewStatus.id='command-preview';previewStatus.textContent='PREVIEW READY';previewStatus.hidden=true;root.querySelector('.command-indicators').insertBefore(previewStatus,root.querySelector('#command-history'));
    const edgeLabel=document.createElement('label');edgeLabel.className='edge-setting';const edgeToggle=document.createElement('input');edgeToggle.type='checkbox';edgeToggle.id='edge-shortcut';edgeLabel.append(edgeToggle,document.createTextNode(' Reveal menu at screen edge'));menu.append(edgeLabel);
    try{shell.edgeEnabled=localStorage.getItem('hw.command.edge.v1')==='true';}catch{shell.edgeEnabled=false;}edgeToggle.checked=shell.edgeEnabled;
    const menuItems=[['campaign','Campaign & access'],['economy','Economy'],['construction','Construction'],['industry','Industry'],['research','Research'],['military','Military'],['fleet','Fleet'],['logistics','Logistics'],['budget','Budget'],['politics','Politics'],['trade','Trade'],['diplomacy','Diplomacy'],['factions','Factions'],['intelligence','Intelligence'],['exploration','Exploration'],['colonies','Colonies'],['characters','Characters'],['history','History & turn log'],['orders','Orders & handoff']];
    for(const [id,label] of menuItems){const b=document.createElement('button');b.textContent=label;b.dataset.open=id;b.onclick=()=>{menu.hidden=true;root.querySelector('#hw-command').setAttribute('aria-expanded','false');shell.touchMenu=false;setActive(id);};menuGrid.append(b);}
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
    document.addEventListener('keydown',e=>{if(e.key==='Escape'){setMenu(false);if(!shell.dialog.hidden)closeDialog();else if(!shell.workspace.hidden)returnToMap();else collapseInspector();}});
    window.addEventListener('resize',()=>{});
    shell.open=setActive;shell.createWindow=register;
  }
  window.HWDesktop={init:build,open:id=>shell.open?.(id),close,clear,resetLayout(){},setOnOpen(fn){shell.onOpen=fn;},setOnFocus(){},setOnCreate(fn){shell.onCreate=fn;},setGesture(value){shell.gesture=Boolean(value);if(shell.gesture){clearTimeout(shell.edgeTimers.show);clearTimeout(shell.edgeTimers.hide);}},setPinned(){},get gesture(){return shell.gesture;},get windows(){return entries;},createWindow:(...args)=>shell.createWindow(...args),has(id){return entries.has(id);},returnMap:returnToMap,positionInspector(x){shell.inspector.classList.toggle('dock-left',Number.isFinite(x)&&x>innerWidth/2);},setPreviewReady(value){const p=document.querySelector('#command-preview');if(p)p.hidden=!value;},refreshIndicators({campaign,turn,historical,pending,snapshotTime,previewReady}={}){const c=document.querySelector('#command-campaign');if(c)c.textContent=campaign||'UNSELECTED';const t=document.querySelector('#command-turn');if(t)t.textContent=turn==null?'TURN —':`TURN ${turn}`;const d=document.querySelector('#command-snapshot');if(d){d.textContent=snapshotTime||'';d.hidden=!snapshotTime;}const h=document.querySelector('#command-history');if(h)h.hidden=!historical;const p=document.querySelector('#command-pending');if(p)p.hidden=!pending;const pr=document.querySelector('#command-preview');if(pr)pr.hidden=!previewReady;},setScope(value){const n=document.querySelector('.workspace-scope');if(n)n.textContent=value||'';}};
})();
