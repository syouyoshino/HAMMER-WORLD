(() => {
  'use strict';
  const definitions = {
    campaign: {title: 'Campaign selection', x: 18, y: 42, w: 390, h: 210, singleton: true},
    planet: {title: 'Cartography', x: 85, y: 52, w: 560, h: 225, singleton: true},
    inspector: {title: 'Selected record', x: 760, y: 84, w: 330, h: 390, singleton: true},
    economy: {title: 'Economy ledger', x: 170, y: 115, w: 520, h: 470},
    history: {title: 'Historical record', x: 760, y: 70, w: 650, h: 580},
    orders: {title: 'Orders & handoff', x: 180, y: 90, w: 760, h: 600},
    turn: {title: 'Last turn report', x: 24, y: 410, w: 310, h: 190},
    log: {title: 'Command log', x: 350, y: 410, w: 330, h: 190}
  };
  const shell = {windows: new Map(), z: 10, pinned: false, gesture: false, touchLauncher: false, onOpen: null, edgeTimers:null};
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(v, hi));
  function button(label, title, action) {
    const b=document.createElement('button'); b.className='button small'; b.type='button'; b.textContent=label; b.title=title; b.onclick=action; return b;
  }
  function createWindow(id, title, node, options={}) {
    const spec={...definitions[id],...options};
    const win=document.createElement('section'); win.className='desk-window'; win.dataset.window=id; win.setAttribute('aria-label',title);
    const bar=document.createElement('header'); bar.className='desk-titlebar';
    const caption=document.createElement('strong'); caption.className='desk-caption'; caption.textContent=title;
    const controls=document.createElement('div'); controls.className='desk-controls';
    const minimize=button('−',`Minimize ${title}`,()=>minimizeWindow(id));
    const maximize=button('□',`Maximize ${title}`,()=>toggleMaximize(id));
    const close=button('×',`Close ${title}`,()=>closeWindow(id));
    controls.append(minimize,maximize,close); bar.append(caption,controls);
    const body=document.createElement('div'); body.className='desk-window-body'; if(node){node.removeAttribute('hidden');body.append(node);}
    win.append(bar,body); win.hidden=true; document.querySelector('#desktop-windows').append(win);
    const item={id,title,spec,win,body,bar,shown:false,minimized:false,maximized:false,rect:null,normalRect:null};
    const saved=readGeometry()[id]; item.rect=saved?{...spec,...saved}:{x:spec.x,y:spec.y,w:spec.w,h:spec.h};
    applyRect(item); shell.windows.set(id,item); wireDrag(item); win.addEventListener('pointerdown',()=>{front(id);if(shell.onFocus)shell.onFocus(id);});
    return item;
  }
  function readStorage(key,fallback=''){try{return localStorage.getItem(key)??fallback}catch{return fallback}}
  function writeStorage(key,value){try{localStorage.setItem(key,value)}catch{}}
  function readGeometry(){try{const value=JSON.parse(readStorage('hw.desktop.geometry','{}'));return value&&typeof value==='object'?value:{}}catch{return {}}}
  function persist(item){const all=readGeometry(),rect=item.maximized&&item.normalRect?item.normalRect:item.rect;all[item.id]={x:rect.x,y:rect.y,w:rect.w,h:rect.h};writeStorage('hw.desktop.geometry',JSON.stringify(all));}
  function applyRect(item){const r=item.rect; item.win.style.left=`${r.x}px`;item.win.style.top=`${r.y}px`;item.win.style.width=`${r.w}px`;item.win.style.height=`${r.h}px`;}
  function fit(item){const r=item.rect,vw=innerWidth,vh=innerHeight;const minW=Math.min(250,vw-16),minH=Math.min(170,vh-16);for(const key of ['x','y','w','h'])if(!Number.isFinite(r[key]))r[key]=item.spec[key]||8;r.w=clamp(r.w,minW,Math.max(minW,vw-16));r.h=clamp(r.h,minH,Math.max(minH,vh-16));r.x=clamp(r.x,8,Math.max(8,vw-r.w-8));r.y=clamp(r.y,8,Math.max(8,vh-r.h-8));applyRect(item);}
  function front(id){const item=shell.windows.get(id);if(item){for(const other of shell.windows.values())other.win.classList.toggle('desk-active',other===item);item.win.style.zIndex=++shell.z;}}
  function open(id){let item=shell.windows.get(id);if(!item&&shell.onCreate)item=shell.onCreate(id);if(!item)return;item.shown=true;item.minimized=false;item.win.hidden=false;fit(item);front(id);renderMinimized();if(shell.onOpen)shell.onOpen(id);}
  function closeWindow(id){const item=shell.windows.get(id);if(!item)return;item.shown=false;item.minimized=false;item.win.hidden=true;persist(item);renderMinimized();}
  function minimizeWindow(id){const item=shell.windows.get(id);if(!item)return;item.minimized=true;item.win.hidden=true;renderMinimized();}
  function toggleMaximize(id){const item=shell.windows.get(id);if(!item)return;if(!item.maximized){item.normalRect={...item.rect};item.maximized=true;item.rect={x:8,y:8,w:innerWidth-16,h:innerHeight-16};}else{item.maximized=false;item.rect=item.normalRect||item.rect;fit(item);}applyRect(item);}
  function renderMinimized(){const root=document.querySelector('#desktop-minimized');root.replaceChildren();for(const item of shell.windows.values())if(item.minimized){const b=button(item.title,`Restore ${item.title}`,()=>open(item.id));root.append(b);}}
  function wireDrag(item){let drag=null;item.bar.addEventListener('pointerdown',e=>{if(e.button!==0||e.target.closest('button'))return;front(item.id);if(item.maximized)return;drag={id:e.pointerId,x:e.clientX,y:e.clientY,left:item.rect.x,top:item.rect.y};setGesture(true);item.bar.setPointerCapture(e.pointerId);e.preventDefault();});item.bar.addEventListener('pointermove',e=>{if(!drag||drag.id!==e.pointerId)return;item.rect.x=drag.left+e.clientX-drag.x;item.rect.y=drag.top+e.clientY-drag.y;fit(item);});const done=e=>{if(drag?.id!==e.pointerId)return;drag=null;setGesture(false);persist(item);};item.bar.addEventListener('pointerup',done);item.bar.addEventListener('pointercancel',done);item.bar.addEventListener('lostpointercapture',()=>{drag=null;setGesture(false);});
    const grip=document.createElement('div');grip.className='desk-resize-grip';grip.setAttribute('aria-label',`Resize ${item.title}`);item.win.append(grip);let resizing=null;grip.addEventListener('pointerdown',e=>{if(e.button!==0||item.maximized)return;resizing={id:e.pointerId,x:e.clientX,y:e.clientY,w:item.rect.w,h:item.rect.h};setGesture(true);grip.setPointerCapture(e.pointerId);e.preventDefault();e.stopPropagation();});grip.addEventListener('pointermove',e=>{if(!resizing||resizing.id!==e.pointerId)return;item.rect.w=resizing.w+e.clientX-resizing.x;item.rect.h=resizing.h+e.clientY-resizing.y;fit(item);});const finish=e=>{if(resizing?.id!==e.pointerId)return;resizing=null;setGesture(false);persist(item);};grip.addEventListener('pointerup',finish);grip.addEventListener('pointercancel',finish);grip.addEventListener('lostpointercapture',()=>{resizing=null;setGesture(false);});
  }
  function launcher(open){cancelEdgeTimers();const root=document.querySelector('#desktop-launcher');root.hidden=!open;if(!open)shell.touchLauncher=false;document.querySelector('#hw-command').setAttribute('aria-expanded',String(open));}
  function cancelEdgeTimers(){if(!shell.edgeTimers)return;clearTimeout(shell.edgeTimers.show);clearTimeout(shell.edgeTimers.hide);shell.edgeTimers.show=null;shell.edgeTimers.hide=null;}
  function setGesture(value){shell.gesture=Boolean(value);if(shell.gesture)cancelEdgeTimers();}
  function clearDesktop(){cancelEdgeTimers();for(const item of shell.windows.values())closeWindow(item.id);launcher(false);}
  function resetLayout(){for(const item of shell.windows.values()){item.maximized=false;item.normalRect=null;item.rect={x:item.spec.x,y:item.spec.y,w:item.spec.w,h:item.spec.h};fit(item);persist(item);}}
  function build(){
    const root=document.createElement('div');root.id='desktop-shell';root.innerHTML='<div id="map-backdrop"></div><button id="hw-command" type="button" aria-expanded="false" aria-label="Open Hammer World command launcher">HW</button><aside id="desktop-launcher" hidden><div class="launcher-head"><b>HAMMER WORLD</b><button id="launcher-pin" class="button small" type="button">Pin</button><button id="launcher-clear" class="button small" type="button">Clear</button></div><div id="launcher-commands"></div><div id="desktop-minimized"></div></aside><div id="desktop-windows"></div>';
    document.body.append(root);
    const mapframe=document.querySelector('.map-frame'); document.querySelector('#map-backdrop').append(mapframe);
    const shellMap=document.createElement('div');shellMap.className='shell-map-panel';const tools=document.querySelector('.map-tools'),crumb=document.querySelector('#map-breadcrumbs'),panel=document.querySelector('#map-panel');shellMap.append(tools,crumb,panel);createWindow('planet','Cartography',shellMap);
    const campaign=document.createElement('div');campaign.className='campaign-window-content';campaign.append(document.querySelector('.campaign-ribbon'),document.querySelector('.access-box'));createWindow('campaign','Campaign selection',campaign);
    const inspector=document.createElement('section');inspector.className='inspector';inspector.id='inspector';inspector.append(document.querySelector('.inspector-title'),document.querySelector('#inspector-content'));createWindow('inspector','Selected record',inspector);
    for(const [id,title,selector] of [['economy','Economy ledger','#economy-panel'],['history','Historical record','#history-panel'],['orders','Orders & handoff','#orders-panel']])createWindow(id,title,document.querySelector(selector));
    for(const [id,title,selector] of [['turn','Last turn report','#turn-window'],['log','Command log','#log-window']])createWindow(id,title,document.querySelector(selector));
    const commandRoot=document.querySelector('#launcher-commands');const nav=document.querySelector('.sidebar');const buttons=[...nav.querySelectorAll('.nav-item')];for(const b of buttons){const clone=b.cloneNode(true);clone.classList.remove('active');clone.onclick=()=>{const view=b.dataset.view;open(view);launcher(false);};commandRoot.append(clone);}const campaignButton=button('Campaign selection','Choose a campaign or sign in',()=>{open('campaign');launcher(false);});campaignButton.classList.add('nav-item');campaignButton.dataset.windowOpen='campaign';const campIcon=document.createElement('span');campIcon.className='nav-icon';campIcon.setAttribute('aria-hidden','true');campIcon.textContent='▣';campaignButton.prepend(campIcon);commandRoot.prepend(campaignButton);
    for(const [id,label,icon] of [['inspector','Selected record','◉'],['turn','Last turn report','▤'],['log','Command log','≡']]){const command=button(label,`Open ${label}`,()=>{open(id);launcher(false);});command.classList.add('nav-item');command.dataset.windowOpen=id;const glyph=document.createElement('span');glyph.className='nav-icon';glyph.setAttribute('aria-hidden','true');glyph.textContent=icon;command.prepend(glyph);commandRoot.append(command);}const choose=document.createElement('div');choose.className='launcher-actions';choose.append(button('Clear desktop','Hide open windows',clearDesktop));commandRoot.prepend(choose);
    const hwCommand=document.querySelector('#hw-command');let commandPointerType='';hwCommand.addEventListener('pointerdown',e=>{commandPointerType=e.pointerType;});hwCommand.onclick=e=>{shell.touchLauncher=(e.pointerType||commandPointerType)==='touch';commandPointerType='';launcher(root.querySelector('#desktop-launcher').hidden);};document.querySelector('#launcher-clear').onclick=clearDesktop;document.querySelector('#launcher-pin').onclick=()=>{cancelEdgeTimers();shell.pinned=!shell.pinned;writeStorage('hw.desktop.pinned',String(shell.pinned));document.querySelector('#launcher-pin').textContent=shell.pinned?'Unpin':'Pin';};shell.pinned=readStorage('hw.desktop.pinned')==='true';document.querySelector('#launcher-pin').textContent=shell.pinned?'Unpin':'Pin';
    let showTimer,hideTimer;shell.edgeTimers={get show(){return showTimer},set show(value){showTimer=value},get hide(){return hideTimer},set hide(value){hideTimer=value}};document.addEventListener('pointermove',e=>{if(shell.gesture||e.pointerType==='touch'||shell.touchLauncher)return;if(e.clientX<=4){clearTimeout(hideTimer);clearTimeout(showTimer);showTimer=setTimeout(()=>launcher(true),240);}else if(!root.querySelector('#desktop-launcher').matches(':hover')&&!shell.pinned){clearTimeout(showTimer);clearTimeout(hideTimer);hideTimer=setTimeout(()=>launcher(false),460);}});root.querySelector('#desktop-launcher').addEventListener('pointerenter',e=>{if(e.pointerType!=='touch'&&!shell.touchLauncher)clearTimeout(hideTimer);});root.querySelector('#desktop-launcher').addEventListener('pointerleave',e=>{if(!shell.gesture&&e.pointerType!=='touch'&&!shell.touchLauncher&&!shell.pinned)hideTimer=setTimeout(()=>launcher(false),460);});document.addEventListener('keydown',e=>{if(e.key==='Escape'){cancelEdgeTimers();launcher(false);}});window.addEventListener('resize',()=>{for(const item of shell.windows.values())if(item.maximized){item.rect={x:8,y:8,w:innerWidth-16,h:innerHeight-16};applyRect(item);}else if(item.shown)fit(item);});
    shell.open=open;shell.createWindow=createWindow;shell.clear=clearDesktop;shell.launcher=launcher;shell.resetLayout=resetLayout;
  }
  window.HWDesktop={init:build,open:(id)=>shell.open?.(id),close:(id)=>closeWindow(id),clear:()=>shell.clear?.(),resetLayout:()=>shell.resetLayout?.(),setOnOpen(fn){shell.onOpen=fn;},setOnFocus(fn){shell.onFocus=fn;},setOnCreate(fn){shell.onCreate=fn;},setGesture,setPinned(value){shell.pinned=Boolean(value);writeStorage('hw.desktop.pinned',String(shell.pinned));},get gesture(){return shell.gesture;},get windows(){return shell.windows;},createWindow:(...args)=>shell.createWindow(...args),has(id){return shell.windows.has(id);}};
})();
