(() => {
  'use strict';
  const $ = (selector, root = document) => root.querySelector(selector);
  const state = {campaigns: [], campaignId: null, campaign: null, snapshot: null, view: 'planet', selectedProvince: null,
    history: [], historyLoading: false, historyTotal: 0, historyOffset: 0, historyPageSize: 50, zoom: 1, panX: 0, panY: 0, drag: null,
    campaignLoadSeq: 0, campaignListSeq: 0, historyLoadSeq: 0, managementSeq:0, mapLoadSeq:0, snapshotLoadSeq:0, contextEpoch:0, selectedEntity:null,
    mapLevel:'planet', mapNodeId:null, mapRecord:null, accessToken:'', privateMode:false, managementSection:null,
    overlay: 'terrain', gmToken: '', previewText: null, previewProposal: null, historyCompare:null, toastTimer: null, managementPanels:new Map(), managementRequests:new Map(), managementContexts:new Map(), managementLoading:new Map(), economyLoading:null};
  const palette = {ocean:'#eff0ed',coast:'#d9dcd7',plains:'#c9cdc8',rock:'#adb3b0',forest:'#989f9d',marsh:'#bbc1bd'};
  const terrainLabels = {ocean:'Open water',coast:'Coastal shelf',plains:'Plains',rock:'Rocklands',forest:'Forest',marsh:'Marsh'};

  function text(node, value) { node.textContent = value == null ? '' : String(value); }
  function el(tag, className, value) { const node=document.createElement(tag); if(className) node.className=className; if(value!==undefined) text(node,value); return node; }
  function fmt(value) { return Number(value).toLocaleString('en-US'); }
  function formatSnapshotTime(value){return new Date(value).toLocaleString('en-AU',{timeZone:'Australia/Melbourne',dateStyle:'medium',timeStyle:'short'});}
  function liveState() { return state.snapshot && state.snapshot.state; }
  function isHistorical() { return Boolean(state.snapshot && state.snapshot._historical); }
  function notify(message, error=false) { let n=$('.toast'); if(!n){n=el('div','toast'); document.body.append(n);} n.className=error?'toast error':'toast'; text(n,message); clearTimeout(state.toastTimer); state.toastTimer=setTimeout(()=>n.remove(),4200); }
  async function api(url, options={}) {
    const headers={...(options.headers||{})};
    const token=state.accessToken||state.gmToken;
    if(token&&!headers.Authorization)headers.Authorization=`Bearer ${token}`;
    const response=await fetch(url,{...options,headers}); let data;
    const type=response.headers.get('content-type')||'';
    if(type.includes('application/json')) data=await response.json(); else data=await response.text();
    if(!response.ok) throw new Error(typeof data==='string'?data:(data.detail||data.message||`HTTP ${response.status}`));
    return data;
  }
  function authHeaders(json=false) { const headers={}; if(state.gmToken) headers.Authorization=`Bearer ${state.gmToken}`; if(json) headers['Content-Type']='application/json'; return headers; }

  async function loadCampaigns(preferred) {
    const request=++state.campaignListSeq;
    const epoch=state.contextEpoch;let campaigns;
    try{campaigns=await api('/api/player/campaigns');}catch(error){if(epoch===state.contextEpoch&&request===state.campaignListSeq)throw error;return;}
    if(request!==state.campaignListSeq||epoch!==state.contextEpoch)return;
    state.campaigns=campaigns;
    const select=$('#campaign-select'); select.replaceChildren(new Option('Select campaign…',''));
    for(const campaign of campaigns){const option=el('option','',`${campaign.id} · ${campaign.kind==='demo'?'fictional demo':'pre-game'}`); option.value=campaign.id; select.append(option);}
    if(!campaigns.length){state.campaignId=null;state.campaign=null;state.snapshot=null;return;}
    const preferredId = preferred && campaigns.some(c=>c.id===preferred) ? preferred : null;
    const currentId = campaigns.some(c=>c.id===state.campaignId) ? state.campaignId : null;
    state.campaignId = preferredId || currentId || null;
    select.value=state.campaignId||'';
    if(state.campaignId)await loadCampaign();
  }
  async function loadCampaign() {
    if(!state.campaignId)return;
    const campaignId=state.campaignId;
    const preserveMap=state.campaignId===campaignId&&Boolean(state.campaign)&&!isHistorical();
    const prior={level:state.mapLevel,nodeId:state.mapNodeId,province:state.selectedProvince,entity:state.selectedEntity,panX:state.panX,panY:state.panY,zoom:state.zoom,mapRecord:state.mapRecord};
    const request=++state.campaignLoadSeq,epoch=state.contextEpoch;
    let data;try{data=await api(`/api/player/campaigns/${encodeURIComponent(campaignId)}`);}catch(error){if(request===state.campaignLoadSeq&&epoch===state.contextEpoch&&campaignId===state.campaignId)throw error;return;}
    if(request!==state.campaignLoadSeq||epoch!==state.contextEpoch||campaignId!==state.campaignId)return;
    state.campaign=data;state.snapshot=data.state?{id:data.snapshot_id,turn:data.turn,state:data.state,archive_status:data.archive_status,created_at:data.created_at}:null;
    if(preserveMap){state.selectedProvince=prior.province;state.selectedEntity=prior.entity;state.mapLevel=prior.level;state.mapNodeId=prior.nodeId;state.mapRecord=prior.mapRecord;state.panX=prior.panX;state.panY=prior.panY;state.zoom=prior.zoom;}
    else{state.selectedProvince=null;state.selectedEntity=null;const surveyedPlanet=data.state?.nodes?.find(n=>n.kind==='planet'&&n.knowledge==='surveyed');state.mapLevel=surveyedPlanet?'planet':'galactic';state.mapNodeId=surveyedPlanet?.id||null;state.mapRecord=null;state.panX=0;state.panY=0;state.zoom=1;}
    render();
    if(data.state)await loadMap();
    for(const [id,item] of window.HWDesktop?.windows||[])if(item.shown&&id!=='campaign'&&id!=='inspector'&&id!=='turn'&&id!=='log')onWindowOpen(id);
  }
  async function loadHistory(offset=0) {
    const campaignId=state.campaignId;
    if(!campaignId)return;const request=++state.historyLoadSeq,epoch=state.contextEpoch;
    state.historyLoading=true;
    try {
      const data=await api(`/api/player/campaigns/${encodeURIComponent(campaignId)}/history?offset=${offset}&limit=${state.historyPageSize}`);
      if(request!==state.historyLoadSeq||epoch!==state.contextEpoch||campaignId!==state.campaignId)return;
      state.history=data.items;state.historyTotal=data.total;state.historyOffset=data.offset;
    } catch(error){if(request===state.historyLoadSeq&&epoch===state.contextEpoch&&campaignId===state.campaignId)throw error;
    } finally {
      if(request===state.historyLoadSeq&&epoch===state.contextEpoch&&campaignId===state.campaignId)state.historyLoading=false;
    }
    if(request===state.historyLoadSeq&&epoch===state.contextEpoch)renderHistory();
  }
  async function selectHistorical(snapshotId) {
    const campaignId=state.campaignId,epoch=state.contextEpoch;
    const request=++state.snapshotLoadSeq;
    let data;try{data=await api(`/api/player/snapshots/${encodeURIComponent(snapshotId)}`);}catch(error){if(epoch===state.contextEpoch&&request===state.snapshotLoadSeq&&campaignId===state.campaignId)throw error;return;}
    if(request!==state.snapshotLoadSeq||epoch!==state.contextEpoch||campaignId!==state.campaignId||data.campaign_id!==campaignId)return;
    const campaign=state.campaign,history=state.history.slice(),historyTotal=state.historyTotal,historyOffset=state.historyOffset,historyCompare=state.historyCompare;clearCampaignContext();state.campaign=campaign;state.campaignId=campaignId;state.snapshot={...data,_historical:true};state.history=history;state.historyTotal=historyTotal;state.historyOffset=historyOffset;state.historyCompare=historyCompare;state.selectedProvince=null;state.mapRecord=null;state.panX=0;state.panY=0;state.zoom=1;state.mapLevel='planet';state.mapNodeId=data.state?.nodes?.find(n=>n.kind==='planet'&&n.knowledge==='surveyed')?.id||null;render();setView('planet');if(state.history.length)renderHistory();for(const [id,item] of window.HWDesktop?.windows||[])if(item.shown&&id!=='campaign'&&id!=='inspector'&&id!=='turn'&&id!=='log')onWindowOpen(id);
  }
  function render() {
    const campaign=state.campaign;const snapshot=state.snapshot;const s=liveState();
    text($('#campaign-kind'),campaign?(campaign.kind==='demo'?'FICTIONAL DEMO':'PRE-GAME · UNSET'):'NO CAMPAIGN');
    $('#campaign-kind').className=campaign&&campaign.kind==='demo'?'demo-ribbon':'turn-badge';
    text($('#turn-badge'),snapshot?`TURN ${snapshot.turn}`:'TURN —');
    text($('#verified-at'),snapshot?.created_at?`DB SNAPSHOT · ${formatSnapshotTime(snapshot.created_at)}`:'DB SNAPSHOT · UNKNOWN');
    $('#historical-badge').hidden=!isHistorical();
    text($('#status-turn'),snapshot?`TURN ${snapshot.turn}`:'TURN —');
    text($('#archive-label'),snapshot?`Archive ${snapshot.archive_status||'unknown'}`:'No snapshot');
    const archive=$('#archive-label');archive.className=snapshot&&snapshot.archive_status==='verified'?'archive-verified':snapshot&&snapshot.archive_status==='pending'?'archive-pending':'';
    renderResources(s,campaign);renderInspector(s,campaign);renderReport(s);renderLog(s);
    window.HWDesktop?.refreshIndicators({campaign:campaign?(campaign.kind==='demo'?'FICTIONAL DEMO':'PRE-GAME · UNSET'):'UNSELECTED',turn:snapshot?.turn,historical:isHistorical(),pending:snapshot?.archive_status==='pending',snapshotTime:snapshot?.created_at?`SAVED ${formatSnapshotTime(snapshot.created_at)}`:null,previewReady:Boolean(state.previewText&&state.previewText===$('#proposal-json')?.value)});
    window.HWDesktop?.setScope(selectedScope(state.view));
    const name=s?(state.mapRecord?.selected_planet?.name||state.mapRecord?.parent?.name||s.nodes?.find(n=>n.kind==='planet'&&n.knowledge==='surveyed')?.name||'Campaign overview'):(campaign?campaign.id:'Campaign unavailable');
    $('#map-level').value=state.mapLevel;
    $('#live-banner').hidden=!isHistorical();if(isHistorical())text($('#live-banner'),`Historical snapshot · turn ${snapshot.turn} · read only. Orders cannot be submitted against this revision.`);
    drawMap();renderMapLegend();renderMapBreadcrumbs();if(state.mapRecord)renderMapHeading();
  }
  function titleCase(value){return String(value).replace(/[-_]/g,' ').replace(/\b\w/g,c=>c.toUpperCase());}
  function selectedScope(view=state.view){
    if(state.selectedEntity&&['inspector','planet'].includes(view))return `Selected record · ${state.selectedEntity.name||state.selectedEntity.id}`;
    const geo=state.mapRecord?.geometry,province=state.selectedProvince&&geo?.provinces?.find(x=>x.id===state.selectedProvince),planet=state.mapRecord?.selected_planet||state.mapRecord?.parent;
    const locality=province?`${province.name}${planet?.name?` · ${planet.name}`:''}`:null;
    const retained=locality?` · selection retained: ${locality}`:'';
    if(view==='economy'||view==='construction'){
      const panel=document.querySelector(view==='economy'?'#economy-panel':'#management-construction');
      const localActive=panel?.querySelector('[data-scope=local].active');
      return localActive&&locality?`Local · ${locality}`:`Campaign-wide ${view}${retained}`;
    }
    if(view==='orders')return `Campaign-wide order preview${retained}`;
    if(view==='history'||view==='turn'||view==='log')return `Campaign ${view==='history'?'history':view==='turn'?'turn report':'command log'}${retained}`;
    if(view==='inspector'||view==='planet')return locality?`Selected locality · ${locality}`:'Campaign-wide recorded view';
    return `Campaign-wide ${titleCase(view||'recorded view')}${retained}`;
  }
  function isManagementView(view){return Boolean(reportSections?.[view]||reportAliases?.[view]);}
  function renderResources(s,campaign) {
    const root=$('#resource-strip');root.replaceChildren();
    const m=economyTotals(s);const items=[['POPULATION',m?fmt(m.population):'UNKNOWN','people'],['FOOD',m?fmt(m.food):'UNKNOWN','stock units'],['ORE',m?fmt(m.ore):'UNKNOWN','stock units'],['ENERGY',m?fmt(m.energy):'UNKNOWN','stock units']];
    for(const [name,value,note] of items){const card=el('div','resource-card');card.append(el('span','resource-name',name),el('strong','resource-value',value),el('span','resource-note',s?note:(campaign&&campaign.kind==='pregame'?'Awaiting approved baseline':'No saved snapshot')));root.append(card);}
  }
  function economyTotals(s){if(!s)return null;if(s.owned_totals)return {population:s.owned_totals.population,...s.owned_totals.resources};if(s.settlements){const owned=s.settlements.filter(x=>x.owned);const totals={population:owned.reduce((a,x)=>a+(x.civilians||0),0)+(s.units||[]).filter(x=>x.owner==='player').reduce((a,x)=>a+(x.strength||0),0)+(s.fleets||[]).filter(x=>x.owner==='player').reduce((a,x)=>a+(x.crew||0),0)+(s.expeditions||[]).filter(x=>x.kind==='colonize').reduce((a,x)=>a+(x.settlers||0),0)};for(const k of ['food','ore','energy','materiel','data','metals','promethium','credits'])totals[k]=owned.reduce((a,x)=>a+(x.stocks?.[k]||0),0);for(const f of s.fleets||[])if(f.owner==='player'){totals.food+=f.food_reserve||0;totals.promethium+=f.promethium_reserve||0;}for(const u of s.units||[])if(u.owner==='player'){totals.food+=u.food_reserve||0;totals.food+=u.transit_food||0;}for(const sh of s.shipments||[])totals[sh.resource]=(totals[sh.resource]||0)+sh.quantity;for(const m of s.expeditions||[])if(m.kind==='colonize')totals.food+=m.food_cargo||0;return totals;}return {population:s.population,food:s.food,ore:s.ore,energy:s.energy};}
  function renderInspector(s,campaign) {
    const root=$('#inspector-content');root.replaceChildren();
    if(!campaign){root.append(el('div','inspector-planet','No campaign'));root.append(el('div','note-box','Initialize the local database with the CLI to create isolated demo and pre-game campaigns.'));return;}
    if(!s){root.append(el('div','inspector-planet',campaign.kind==='pregame'?'Pre-game':'No snapshot'));root.append(el('div','inspector-sub',campaign.kind==='pregame'?'CANONICAL VALUES UNKNOWN':'WAITING FOR INITIAL SNAPSHOT'));for(const [label,value]of [['Ruler','Unknown'],['Government','Unknown'],['Campaign date','Unknown'],['GDP','Unknown'],['Approval','Unknown'],['Discovery risk','Unknown'],['DB checksum-verified saved update','Unknown'],['Archive','Unconfigured']])row(root,label,value);root.append(el('div','note-box','No numeric baseline has been approved. Unknown values are left unassigned.'));return;}
    if(state.selectedEntity){renderSelectedEntity(root,state.selectedEntity);return;}
    const geo=state.mapRecord?.geometry;const p=state.selectedProvince&&geo?.provinces.find(x=>x.id===state.selectedProvince);const selectedPlanet=state.mapRecord?.selected_planet||state.mapRecord?.parent;
    root.append(el('div','inspector-planet',p?p.name:(selectedPlanet?.name||campaign.id)));root.append(el('div','inspector-sub',p?'PROVINCE INSPECTION':geo?`${geo.planet.width} × ${geo.planet.height} SURVEY GRID`:'CAMPAIGN RECORD'));
    if(p){
      const planet=state.mapRecord?.selected_planet||state.mapRecord?.parent;
      const settlements=(s.settlements||[]).filter(x=>x.planet_id===planet?.id&&x.province_id===p.id);
      const record=state.mapRecord.records?.find(x=>x.province_id===p.id);
      row(root,'Main terrain',titleCase(provinceTerrain(geo,p)));
      row(root,'Province total',record?.population==null?'Unknown':fmt(record.population));
      root.append(el('div','inspector-section','LOCAL SETTLEMENTS'));
      if(settlements.length){
        for(const settlement of settlements){
          const local=el('section','inspector-settlement');
          local.append(el('div','inspector-planet',settlement.name||'Recorded settlement'));
          local.append(el('div','inspector-sub','SETTLEMENT · SELECTED PROVINCE'));
          row(local,'Local population',settlement.local_population==null?'Unknown':fmt(settlement.local_population));
          row(local,'Civilians',settlement.civilians==null?'Unknown':fmt(settlement.civilians));
          if(settlement.local_crew!==undefined)row(local,'Local crew',fmt(settlement.local_crew));
          if(settlement.local_soldiers!==undefined)row(local,'Local soldiers',fmt(settlement.local_soldiers));
          if(settlement.housing!==undefined)row(local,'Housing',fmt(settlement.housing));
          if(settlement.unrest!==undefined)row(local,'Unrest',fmt(settlement.unrest));
          if(settlement.stocks?.food!==undefined)row(local,'Food stock',fmt(settlement.stocks.food));
          const ids=el('details','record-identifiers');ids.append(el('summary','','Record identifiers'));
          row(ids,'Planet ID',settlement.planet_id);row(ids,'Province ID',settlement.province_id);row(ids,'Settlement ID',settlement.id);local.append(ids);root.append(local);
        }
      }else root.append(el('div','empty-note','No recorded settlement in this planet and province.'));
      const actions=el('div','inspector-actions');
      const economy=el('button','button small','Economy');economy.onclick=()=>setView('economy');
      const construction=el('button','button small','Construction');construction.onclick=()=>setView('construction');
      actions.append(economy,construction);root.append(actions);
      root.append(el('div','note-box','Settlement records are local to their saved planet and province. The province total is shown only when recorded.'));
    }
    else{
      const totals=economyTotals(s);row(root,'Campaign',state.campaignId);row(root,'Turn',fmt(s.turn));row(root,'Archive',snapshotArchive());
      row(root,'Saved',state.snapshot?.created_at?formatSnapshotTime(state.snapshot.created_at):'Unknown');
      if(totals)row(root,'Owned population',fmt(totals.population));
      if(state.mapRecord?.level&&state.mapRecord.level!=='planet'){row(root,'Map level',titleCase(state.mapRecord.level));row(root,'Context',state.mapRecord.parent?.name||'The Reach');row(root,'Visible records',(state.mapRecord.nodes||[]).length);}
      root.append(el('div','inspector-section','WORLD RECORD'));
      root.append(el('div','note-box',campaign.kind==='demo'?'Fictional demo values use demo-v2 rules. Surveyed geography is deterministic and saved with each snapshot.':'This pre-game campaign has no approved baseline or generated geography.'));
    }
    if(isHistorical())root.append(el('div','note-box','Historical inspection is read only. Use “Live” to return to the current revision.'));
  }
  function snapshotArchive(){return state.snapshot?state.snapshot.archive_status||'unknown':'unknown';}
  function renderSelectedEntity(root,record){const isCharacter=record.role!==undefined&&record.experience!==undefined;root.append(el('div','inspector-planet',isCharacter?`Character · ${titleCase(record.role)}`:record.name||record.id||'Selected record'),el('div','inspector-sub','RECORDED ENTITY · READ ONLY'));if(isCharacter){row(root,'Role',titleCase(record.role));row(root,'Assignment',record.assignment==null?'Unassigned':safeValue(record.assignment));row(root,'Experience',safeValue(record.experience));root.append(el('div','inspector-section','RELATIONSHIPS'));root.append(el('div','note-box','Relationships are not recorded in the saved character data. No relationship map is available for this character.'));const ids=el('details','record-identifiers');ids.append(el('summary','','Record identifiers'));row(ids,'Character',record.id);root.append(ids);}else for(const [key,value]of Object.entries(record)){if(value&&typeof value==='object'&&!Array.isArray(value)){root.append(el('div','inspector-section',titleCase(key)));for(const [sub,nested]of Object.entries(value))row(root,titleCase(sub),safeValue(nested));}else if(Array.isArray(value)){root.append(el('div','inspector-section',titleCase(key)));for(const item of value)row(root,'Record',safeValue(item));}else row(root,titleCase(key),safeValue(value));}const back=el('button','button small','Clear selection');back.onclick=()=>{state.selectedEntity=null;renderInspector(liveState(),state.campaign);};root.append(back);}
  function selectEntity(record){state.selectedEntity=record;const inspector=$('#inspector-content');inspector.replaceChildren();renderSelectedEntity(inspector,record);window.HWDesktop?.open('inspector');}
  function row(root,label,value){const r=el('div','inspector-row');r.append(el('span','',label),el('b','',value));root.append(r);}
  function provinceTerrain(geo,p){const counts={};for(const t of geo?.tiles||[])if(t.province_id===p.id)counts[t.terrain]=(counts[t.terrain]||0)+1;return Object.entries(counts).sort((a,b)=>b[1]-a[1])[0]?.[0]||'No land tiles';}
  function renderReport(s){const root=$('#turn-report');root.replaceChildren();text($('#report-turn'),s?`TURN ${s.turn}`:'—');const o=s?.latest_outcome||s?.outcomes?.at(-1);if(!o){root.append(el('div','empty-note',s?'No turn has been resolved yet.':'No recorded report.'));return;}const prod=o.production?Object.values(o.production).reduce((a,x)=>{for(const [k,v]of Object.entries(x))a[k]=(a[k]||0)+v;return a;},{}):{};const cons=o.consumption?Object.values(o.consumption).reduce((a,x)=>{for(const [k,v]of Object.entries(x))a[k]=(a[k]||0)+v;return a;},{}):{};const consumedFood=o.total_consumption?.food??cons.food??o.food_consumed;const populationLost=Array.isArray(o.deaths)?o.deaths.reduce((a,x)=>a+x.count,0):o.population_lost;for(const [k,v]of [['Food produced',prod.food??o.food_produced],['Food consumed',consumedFood],['Ore produced',prod.ore??o.ore_produced],['Energy produced',prod.energy??o.energy_produced],['Population lost',populationLost]]){const line=el('div','report-line');line.append(el('span','',k),el('b','',v==null?'Unknown':fmt(v)));root.append(line);}}
  function renderLog(s){const root=$('#command-log');root.replaceChildren();if(!s){root.append(el('div','empty-note','No events recorded.'));return;}if(s.narrative)root.append(el('div','',s.narrative));else root.append(el('div','empty-note',s.turn===0?'Initial demonstration state committed.':'No narrative supplied for this turn.'));}

  async function loadMap(){const campaignId=state.campaignId,s=liveState();if(!campaignId||!s){drawMap();return;}const request=++state.mapLoadSeq,epoch=state.contextEpoch,snapshotId=state.snapshot?.id,overlay=state.overlay,level=state.mapLevel;const parentId=state.mapNodeId,priorProvince=state.selectedProvince,priorEntity=state.selectedEntity;if(!s.nodes){state.mapLevel='planet';$('#map-level').value='planet';state.mapRecord={level:'planet',selected_planet:s.planet,geometry:{planet:s.planet,provinces:s.provinces,tiles:s.tiles},records:[]};drawMap();renderMapLegend();renderMapBreadcrumbs();renderMapHeading();renderInspector(s,state.campaign);return;}const historical=isHistorical()?`&snapshot_id=${encodeURIComponent(state.snapshot.id)}`:'';let query=`level=${encodeURIComponent(level)}${historical}`;if(level!=='galactic'&&parentId)query+=`&node_id=${encodeURIComponent(parentId)}`;try{const data=await api(`/api/player/campaigns/${encodeURIComponent(campaignId)}/map?${query}&overlay=${encodeURIComponent(overlay)}`);if(request!==state.mapLoadSeq||epoch!==state.contextEpoch||campaignId!==state.campaignId||snapshotId!==state.snapshot?.id||level!==state.mapLevel||parentId!==state.mapNodeId||overlay!==state.overlay)return;state.mapRecord=data;state.selectedProvince=priorProvince&&data.geometry?.provinces?.some(x=>x.id===priorProvince)?priorProvince:null;state.selectedEntity=priorEntity;drawMap();renderMapBreadcrumbs();renderMapHeading();renderMapLegend();renderInspector(s,state.campaign);}catch(error){if(epoch===state.contextEpoch&&campaignId===state.campaignId&&request===state.mapLoadSeq)notify(error.message,true);}}
  function renderMapHeading(){const record=state.mapRecord;if(!record)return;const level=record.level||'planet';const subject=level==='galactic'?'The Reach':record.selected_planet?.name||record.parent?.name||'Map';text($('.section-title h1'),`${subject} · ${titleCase(level)}`);text($('.eyebrow'),`${titleCase(level).toUpperCase()} CARTOGRAPHY`);text($('#map-coordinates'),`${titleCase(level).toUpperCase()} CARTOGRAPHY · ${record.parent?.name||subject}`);const geometry=record.geometry?.planet;text($('#map-scale'),geometry?`${geometry.width} × ${geometry.height} GRID`:`${(record.nodes||[]).length} RECORDED`);const hints=[...document.querySelectorAll('.map-footer span')];if(hints.length){text(hints[0],level==='planet'?'◉ Select a province to inspect':'◉ Select a recorded body to descend');text(hints[1],level==='planet'?'Drag to pan · wheel or buttons to zoom':'Click a known marker · drag to pan · wheel to zoom');}}
  function mapNodes(record){return record?.level==='galactic'?(record.nodes||[]):(record?.nodes||[]);}
  function renderMapBreadcrumbs(){const root=$('#map-breadcrumbs');if(!root)return;root.replaceChildren();const names=[['galactic','The Reach',null]];let nodeId=state.mapNodeId;const s=liveState();if(nodeId&&s){const chain=[];let node=s.nodes.find(n=>n.id===nodeId);while(node){chain.unshift(node);node=s.nodes.find(n=>n.id===node.parent_id);}for(const [index,n] of chain.entries()){const sameRoot=index===0&&n.name===names[0][1]&&(n.kind==='galaxy'||n.kind==='region');if(sameRoot||n.kind==='region'&&/reach/i.test(n.name))continue;const level=n.kind==='region'||n.kind==='galaxy'?'galactic':n.kind==='sector'?'sector':n.kind==='system'?'system':'planet';names.push([level,n.name,n.id]);}}
    for(const [index,item] of names.entries()){if(index)root.append(document.createTextNode(' › '));const button=el('button','link-button',item[1]);button.type='button';button.dataset.mapContext=item[2]||'';button.onclick=()=>{const level=item[0];state.mapLevel=level;state.mapNodeId=item[2];$('#map-level').value=level;loadMap();};root.append(button);}}
  function setMapLevel(level){state.mapLevel=level;$('#map-level').value=level;const s=liveState();let nodeId=null;if(level==='sector')nodeId=(s?.nodes||[]).find(n=>n.kind==='sector'&&n.knowledge!=='hidden')?.id||null;else if(level==='system')nodeId=(s?.nodes||[]).find(n=>n.kind==='system'&&n.knowledge==='surveyed')?.id||null;else if(level==='planet')nodeId=(s?.nodes||[]).find(n=>n.kind==='planet'&&n.knowledge==='surveyed')?.id||null;state.mapNodeId=nodeId;state.panX=state.panY=0;state.zoom=1;loadMap();}
  function drawMap(){const canvas=$('#planet-map'),ctx=canvas.getContext('2d'),frame=canvas.parentElement,s=liveState(),placeholder=$('#map-placeholder');const dpr=window.devicePixelRatio||1;const w=frame.clientWidth,h=frame.clientHeight;canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,w,h);placeholder.hidden=Boolean(s&&state.mapRecord);if(!s||!state.mapRecord)return;
    if(state.mapRecord.level!=='planet'){drawHierarchyMap(ctx,w,h,state.mapRecord,hierarchySafeRect(frame,w,h));return;}
    const geometry=state.mapRecord.geometry;if(!geometry){placeholder.hidden=false;return;}const planet=geometry.planet;const cols=planet.width,rows=planet.height;
    const tile=Math.min(w/cols,h/rows)*state.zoom,gridW=tile*cols,gridH=tile*rows,ox=(w-gridW)/2+state.panX,oy=(h-gridH)/2+state.panY;state.transform={tile,ox,oy,cols,rows};
    ctx.fillStyle='#f1f2ee';ctx.fillRect(0,0,w,h);
    const provColors=['#aeb4b2','#c0c5c2','#9da4a2','#d0d4d0','#858d8d','#b7bdb9','#c7cbc8','#929998'];const tiles=geometry.tiles;const provinceIndex=new Map(geometry.provinces.map((p,i)=>[p.id,i]));
    for(const t of tiles){const px=ox+t.x*tile,py=oy+t.y*tile;if(px+tile<0||py+tile<0||px>w||py>h)continue;let color=palette[t.terrain]||'#aab0ae';if(state.overlay==='provinces'&&t.province_id)color=provColors[(provinceIndex.get(t.province_id)||0)%provColors.length];ctx.fillStyle=color;ctx.fillRect(px,py,Math.ceil(tile),Math.ceil(tile));if(t.terrain!=='ocean'&&((t.x*17+t.y*31)%7===0)){ctx.fillStyle='rgba(255,255,255,.2)';ctx.fillRect(px+tile*.25,py+tile*.25,Math.max(1,tile*.18),Math.max(1,tile*.18));}}
    if(state.overlay!=='terrain'&&state.overlay!=='provinces')drawRecordedOverlay(ctx,geometry,tiles,ox,oy,tile,state.mapRecord.records||[],s);
    // Draw stepped province edges only along land boundaries; open water stays continuous.
    ctx.lineWidth=Math.max(1,Math.min(1.4,tile*.1));ctx.strokeStyle=state.overlay==='provinces'?'rgba(48,54,56,.88)':'rgba(64,70,72,.44)';ctx.beginPath();for(const t of tiles){if(!t.province_id)continue;for(const [dx,dy,edge] of [[0,-1,'n'],[1,0,'e'],[0,1,'s'],[-1,0,'w']]){const nx=t.x+dx,ny=t.y+dy,neighbor=nx>=0&&ny>=0&&nx<cols&&ny<rows?tiles[ny*cols+nx]:null;if(!neighbor?.province_id||neighbor.province_id!==t.province_id){const x=ox+t.x*tile,y=oy+t.y*tile;if(edge==='n'){ctx.moveTo(x,y);ctx.lineTo(x+tile,y);}else if(edge==='e'){ctx.moveTo(x+tile,y);ctx.lineTo(x+tile,y+tile);}else if(edge==='s'){ctx.moveTo(x,y+tile);ctx.lineTo(x+tile,y+tile);}else{ctx.moveTo(x,y);ctx.lineTo(x,y+tile);}}}}ctx.stroke();
    if(state.selectedProvince){
      const p=geometry.provinces.find(x=>x.id===state.selectedProvince);if(p){
        ctx.strokeStyle='#252b2d';ctx.lineWidth=Math.max(2,Math.min(3,tile*.18));ctx.beginPath();
        for(const t of tiles){if(t.province_id!==p.id||t.terrain==='ocean')continue;const x=ox+t.x*tile,y=oy+t.y*tile;
          for(const [dx,dy,edge] of [[0,-1,'n'],[1,0,'e'],[0,1,'s'],[-1,0,'w']]){const nx=t.x+dx,ny=t.y+dy,neighbor=nx>=0&&ny>=0&&nx<cols&&ny<rows?tiles[ny*cols+nx]:null;if(neighbor?.province_id===p.id&&neighbor.terrain!=='ocean')continue;
            if(edge==='n'){ctx.moveTo(x,y);ctx.lineTo(x+tile,y);}else if(edge==='e'){ctx.moveTo(x+tile,y);ctx.lineTo(x+tile,y+tile);}else if(edge==='s'){ctx.moveTo(x,y+tile);ctx.lineTo(x+tile,y+tile);}else{ctx.moveTo(x,y);ctx.lineTo(x,y+tile);}
          }
        }ctx.stroke();
      }
    }
    const compactMap=w<=780||h<=500,planetId=state.mapRecord?.selected_planet?.id||state.mapRecord?.parent?.id||geometry.planet.id;
    const labelFont=Math.max(11,Math.min(13,tile*.46));ctx.font=`700 ${labelFont}px "Noto Instrument Mono",monospace`;ctx.textAlign='center';ctx.textBaseline='middle';
    const safeTop=compactMap?202:190,safeBottom=h-92,placed=[];
    const annotations=geometry.provinces.map(province=>{
      const land=tiles.filter(t=>t.province_id===province.id&&t.terrain!=='ocean'&&ox+(t.x+1)*tile>0&&oy+(t.y+1)*tile>0&&ox+t.x*tile<w&&oy+t.y*tile<h);
      if(!land.length)return null;
      const settlements=(s.settlements||[]).filter(item=>item.planet_id===planetId&&item.province_id===province.id);
      if(compactMap&&!settlements.length&&province.id!==state.selectedProvince)return null;
      const cx=land.reduce((sum,t)=>sum+t.x+.5,0)/land.length,cy=land.reduce((sum,t)=>sum+t.y+.5,0)/land.length;
      const anchor=land.reduce((best,t)=>Math.hypot(t.x+.5-cx,t.y+.5-cy)<Math.hypot(best.x+.5-cx,best.y+.5-cy)?t:best,land[0]);
      const names=settlements.map(item=>item.name||'Settlement');
      const label=names.length?(compactMap&&names.length>1?`${names.length} holdings · ${province.name}`:`${names.join(' + ')} · ${province.name}`):province.name;
      return {province,anchor,settlements,label,holding:names.length>0,selected:province.id===state.selectedProvince,x:ox+(anchor.x+.5)*tile,y:oy+(anchor.y+.5)*tile};
    }).filter(Boolean).sort((a,b)=>Number(b.holding)-Number(a.holding)||Number(b.selected)-Number(a.selected));
    const offsets=compactMap?[[0,0],[0,-18],[0,18],[30,-18],[-30,-18],[30,18],[-30,18],[0,-38],[0,38]]:[[0,0],[0,-18],[0,18],[30,-18],[-30,-18],[30,18],[-30,18],[0,-38],[0,38],[58,0],[-58,0],[0,-58],[0,58],[88,-24],[-88,-24],[88,24],[-88,24]];
    for(const item of annotations){
      const textWidth=ctx.measureText(item.label).width,boxWidth=textWidth+10,boxHeight=20;
      let chosen=null;
      for(const [dx,dy]of offsets){
        const x=Math.max(boxWidth/2+6,Math.min(w-boxWidth/2-6,item.x+dx)),y=Math.max(safeTop+boxHeight/2,Math.min(safeBottom-boxHeight/2,item.y+dy));
        const box={left:x-boxWidth/2-4,right:x+boxWidth/2+4,top:y-boxHeight/2-3,bottom:y+boxHeight/2+3};
        if(placed.some(other=>box.left<other.right&&box.right>other.left&&box.top<other.bottom&&box.bottom>other.top))continue;
        chosen={x,y,box};break;
      }
      if(!chosen)continue;
      placed.push(chosen.box);
      if(Math.hypot(item.x-chosen.x,item.y-chosen.y)>12){ctx.strokeStyle='rgba(37,43,45,.62)';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(item.x,item.y);ctx.lineTo(chosen.x,chosen.y);ctx.stroke();}
      ctx.fillStyle='rgba(248,248,244,.96)';ctx.fillRect(chosen.x-boxWidth/2-4,chosen.y-boxHeight/2,boxWidth+8,boxHeight);
      ctx.fillStyle='#252b2d';ctx.fillText(item.label,chosen.x,chosen.y);
    }
  }
  function drawRecordedOverlay(ctx,geometry,tiles,ox,oy,tile,records,s){
    const byProvince=new Map(records.map(record=>[record.province_id,record]));
    for(const province of geometry.provinces){
      const record=byProvince.get(province.id);let known=false,color=null;
      if(state.overlay==='population'&&record&&typeof record.population==='number'){known=true;color=record.population===0?'rgba(240,241,237,.5)':`rgba(55,62,64,${Math.min(.54,.12+Math.log10(record.population+1)*.15)})`;}
      if(state.overlay==='politics'&&record&&typeof record.unrest==='number'){known=true;color=`rgba(55,62,64,${Math.min(.58,.12+record.unrest*.004)})`;}
      const ownedSettlement=(s.settlements||[]).find(x=>x.owned&&x.province_id===province.id);
      const hasFacilities=state.overlay==='infrastructure'&&Array.isArray(record?.facilities)&&record.facilities.length>0;
      const knownEmptyInfrastructure=state.overlay==='infrastructure'&&ownedSettlement&&Array.isArray(record?.facilities);
      const units=state.overlay==='military'&&Array.isArray(record?.units)?record.units:[];
      for(const t of tiles){if(t.province_id!==province.id||t.terrain==='ocean')continue;const x=ox+t.x*tile,y=oy+t.y*tile;
        if(known&&color){ctx.fillStyle=color;ctx.fillRect(x,y,Math.ceil(tile),Math.ceil(tile));}
        else if((state.overlay==='population'||state.overlay==='politics'||(state.overlay==='infrastructure'&&!hasFacilities&&!knownEmptyInfrastructure)||(state.overlay==='military'&&!units.length))&&((t.x+t.y)%3===0)){ctx.strokeStyle='rgba(65,71,73,.62)';ctx.lineWidth=Math.max(1,tile*.1);ctx.beginPath();ctx.moveTo(x+tile*.18,y+tile*.82);ctx.lineTo(x+tile*.82,y+tile*.18);ctx.stroke();}
      }
      const cx=ox+(province.x+province.width/2)*tile,cy=oy+(province.y+province.height/2)*tile;
      if(state.overlay==='infrastructure'&&(hasFacilities||knownEmptyInfrastructure)){const count=hasFacilities?record.facilities.length:0;ctx.fillStyle='#343b3d';ctx.fillRect(cx-7,cy-7,14,14);ctx.fillStyle='#f7f8f4';ctx.fillRect(cx-4,cy-4,Math.max(3,Math.min(8,count*2)),8);if(tile>10){ctx.fillStyle='#fff';ctx.font='8px monospace';ctx.textAlign='center';ctx.fillText(String(count),cx,cy+13);}}
      if(state.overlay==='military'&&units.length){units.slice(0,5).forEach((unit,index)=>{ctx.fillStyle=unit.owner==='player'?'#343b3d':unit.owner==='foreign'?'#899092':'#aeb4b3';ctx.fillRect(cx-7+(index%3)*5,cy-5+Math.floor(index/3)*5,4,4);});}
    }
  }
  function hierarchySafeRect(frame,w,h){
    const frameRect=frame.getBoundingClientRect();
    const visibleRect=selector=>{const node=document.querySelector(selector);if(!node||node.hidden)return null;const style=getComputedStyle(node);if(style.display==='none'||style.visibility==='hidden')return null;const rect=node.getBoundingClientRect();return rect.width&&rect.height?rect:null;};
    const topNodes=['.commandbar','#resource-shell','#view-title','#map-breadcrumbs','#live-banner'];
    const bottomNodes=['.map-caption','#map-legend','.map-footer'];
    const top=Math.max(0,...topNodes.map(selector=>visibleRect(selector)).filter(Boolean).map(rect=>rect.bottom-frameRect.top+16));
    const bottom=Math.min(h,...bottomNodes.map(selector=>visibleRect(selector)).filter(Boolean).map(rect=>rect.top-frameRect.top-16));
    return{left:0,top:Math.min(top,h),right:w,bottom:Math.max(Math.min(bottom,h),Math.min(top,h)),width:w,height:Math.max(0,bottom-top)};
  }
  function drawHierarchyMap(ctx,w,h,record,safe){
    ctx.fillStyle='#f1f2ee';ctx.fillRect(0,0,w,h);
    const nodes=mapNodes(record).filter(n=>n.knowledge!=='hidden'),bodies=record.bodies||[],all=[...nodes,...bodies];
    const padX=Math.min(24,Math.max(8,safe.width*.06)),padY=Math.min(26,Math.max(8,safe.height*.14));
    const inner={left:safe.left+padX,right:safe.right-padX,top:safe.top+padY,bottom:safe.bottom-padY};
    if(inner.right<inner.left||inner.bottom<inner.top){inner.right=inner.left;inner.bottom=inner.top;}
    const xs=all.map(n=>Number.isFinite(n.x)?n.x:0),ys=all.map(n=>Number.isFinite(n.y)?n.y:0);
    const minX=Math.min(0,...xs),maxX=Math.max(1,...xs),minY=Math.min(0,...ys),maxY=Math.max(1,...ys),rangeX=Math.max(.2,maxX-minX),rangeY=Math.max(.2,maxY-minY);
    const cx=(safe.left+safe.right)/2,cy=(safe.top+safe.bottom)/2;
    const base=all.map((n,i)=>({n,x:inner.left+((Number.isFinite(n.x)?n.x:(i+1)/(all.length+1))-minX)/rangeX*(inner.right-inner.left),y:inner.top+((Number.isFinite(n.y)?n.y:.5)-minY)/rangeY*(inner.bottom-inner.top)}));
    const positions=base.map(item=>({...item,x:cx+(item.x-cx)*state.zoom+state.panX,y:cy+(item.y-cy)*state.zoom+state.panY}));
    ctx.save();ctx.beginPath();ctx.rect(safe.left,safe.top,safe.width,safe.height);ctx.clip();
    if(record.links?.length){const byId=new Map(positions.map(p=>[p.n.id,p]));ctx.strokeStyle='#9ca3a2';ctx.lineWidth=1;ctx.setLineDash([5,4]);ctx.beginPath();for(const edge of record.links){const a=byId.get(edge.a),b=byId.get(edge.b);if(a&&b){ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);}}ctx.stroke();ctx.setLineDash([]);}
    if(record.level==='galactic'){
      const groups=record.groups||[],rxLimit=Math.max(0,Math.min(inner.right-cx,cx-inner.left)-8),ryLimit=Math.max(0,Math.min(inner.bottom-cy,cy-inner.top)-8);
      for(const [i,g]of groups.entries()){
        const bx=groups.length===1?cx:inner.left+8+i*(inner.right-inner.left-16)/Math.max(1,groups.length-1),x=cx+(bx-cx)*state.zoom+state.panX,y=cy+12*state.zoom+state.panY;
        const rx=Math.max(0,Math.min(inner.width||safe.width,rxLimit)*.72*state.zoom),ry=Math.max(0,Math.min(inner.height||safe.height,ryLimit)*.72*state.zoom);
        ctx.strokeStyle='#b7bdb9';ctx.setLineDash([3,5]);ctx.beginPath();ctx.ellipse(x,y,rx,ry,0,0,Math.PI*2);ctx.stroke();ctx.setLineDash([]);
        const label=String(g.region?.name||'');if(label){ctx.fillStyle='#4b5355';ctx.font='11px monospace';ctx.textAlign='center';const width=ctx.measureText(label).width;ctx.fillText(label,Math.max(safe.left+width/2+4,Math.min(safe.right-width/2-4,x)),safe.top+13);}
      }
    }
    for(const {n,x,y}of positions){const radius=record.level==='system'?10:8;ctx.fillStyle=n.kind==='star'?'#5c6466':n.kind==='belt'?'#a8aeac':n.kind==='planet'?'#858d8d':n.knowledge==='surveyed'?'#626a6c':'#b5bbba';ctx.fillRect(x-radius,y-radius,radius*2,radius*2);ctx.strokeStyle='#3e4547';ctx.strokeRect(x-radius,y-radius,radius*2,radius*2);ctx.fillStyle='#303638';ctx.font='11px monospace';ctx.textAlign='center';const label=String(n.name||'');const labelWidth=ctx.measureText(label).width,labelX=Math.max(safe.left+labelWidth/2+3,Math.min(safe.right-labelWidth/2-3,x));let labelY=y+radius+14;if(labelY>safe.bottom-2)labelY=y-radius-5;ctx.fillText(label,labelX,labelY);}
    ctx.restore();state.transform={hierarchy:true,positions,safeRect:safe};
  }
  function renderMapLegend(){
    const root=$('#map-legend');root.replaceChildren();let entries;
    const unknown='repeating-linear-gradient(135deg,#343b3d 0 1.5px,#f1f2ee 1.5px 4px)';
    if(state.mapLevel!=='planet')entries=[['#626a6c',state.mapLevel==='galactic'?'Known sectors':state.mapLevel==='sector'?'Known systems':'Recorded bodies']];
    else if(state.overlay==='terrain')entries=[['ocean','Open water'],['coast','Coastal shelf'],['plains','Plains'],['rock','Rocklands'],['forest','Forest'],['marsh','Marsh']];
    else if(state.overlay==='population')entries=[['#555d5f','Recorded residents'],['#e4e6e2','Recorded zero'],[unknown,'Unknown / unrecorded']];
    else if(state.overlay==='infrastructure')entries=[['#343b3d','Recorded facilities'],['#d7dad6','Owned site · none recorded'],[unknown,'Unknown / unrecorded']];
    else if(state.overlay==='military')entries=[['#343b3d','Owned forces'],['#858d8d','Observed foreign forces'],[unknown,'No current observation']];
    else if(state.overlay==='politics')entries=[['#555d5f','Recorded unrest'],[unknown,'Unknown / unrecorded']];
    else entries=[['#555d5f','Province boundaries'],['#aeb5b1','Surveyed land']];
    for(const [key,label]of entries){const item=el('span','legend-key');const sw=el('i','swatch');sw.style.background=palette[key]||key;item.append(sw,document.createTextNode(label));root.append(item);}
  }
  function canvasPoint(event){const r=event.currentTarget.getBoundingClientRect();return{x:event.clientX-r.left,y:event.clientY-r.top};}
  function tileAt(point){const t=state.transform;if(!t||t.hierarchy)return null;const x=Math.floor((point.x-t.ox)/t.tile),y=Math.floor((point.y-t.oy)/t.tile);if(x<0||x>=t.cols||y<0||y>=t.rows)return null;return state.mapRecord?.geometry?.tiles[y*t.cols+x]||null;}

  async function renderEconomy(){
    const root=$('#economy-panel'),campaignId=state.campaignId,turn=liveState()?.turn,epoch=state.contextEpoch;
    const localKey=`${state.selectedProvince||''}|${state.mapRecord?.selected_planet?.id||''}`,context=`${epoch}|${campaignId}|${state.snapshot?.id||''}|${turn}|${localKey}`;
    if(root.dataset.context===context&&(root.dataset.ready==='true'||state.economyLoading?.context===context))return;
    root.dataset.context=context;root.dataset.ready='false';root.replaceChildren();
    const s=liveState();
    if(!s)root.append(el('p','view-sub','No approved numerical baseline is available.'));
    if(!s){root.append(el('div','note-box',state.campaign?'Economic fields stay unknown until a baseline is approved.':'Choose a campaign to view its economy.'));root.dataset.ready='true';return;}
    const geo=state.mapRecord?.geometry,planet=state.mapRecord?.selected_planet||state.mapRecord?.parent;
    const province=state.selectedProvince&&geo?.provinces?.find(x=>x.id===state.selectedProvince);
    const settlements=province?(s.settlements||[]).filter(x=>x.planet_id===planet?.id&&x.province_id===province.id):[];
    const local=Boolean(province),scope=el('nav','scope-tabs');scope.setAttribute('aria-label','Economy scope');
    const localButton=el('button','',province?`Local · ${province.name}`:'Local holdings');localButton.type='button';localButton.disabled=!province;localButton.dataset.scope='local';
    const campaignButton=el('button','','Campaign totals');campaignButton.type='button';campaignButton.dataset.scope='campaign';scope.append(localButton,campaignButton);root.append(scope);
    const localPane=el('section','scope-pane local-scope'),campaignPane=el('section','scope-pane campaign-scope');localPane.hidden=!local;campaignPane.hidden=local;
    if(province){
      localPane.append(el('div','scope-provenance',`Turn ${s.turn} · Saved ${state.snapshot?.created_at?formatSnapshotTime(state.snapshot.created_at):'time unknown'}`));
      if(!settlements.length)localPane.append(el('div','empty-note','No recorded settlement matches this planet and province.'));
      for(const settlement of settlements){
        const group=el('section','report-group economy-settlement');
        group.append(el('h3','report-group-title',settlement.name||'Recorded settlement'));
        const vitalGrid=el('dl','local-vital-grid');
        for(const [label,value] of [
          ['Local population',settlement.local_population],['Civilians',settlement.civilians],['Local crew',settlement.local_crew],
          ['Local soldiers',settlement.local_soldiers],['Housing',settlement.housing],['Unrest',settlement.unrest]
        ]){
          if(value===undefined)continue;
          const vital=el('div',`local-vital${label==='Local population'?' local-vital-primary':''}`);vital.append(el('dt','',label),el('dd','',value==null?'Unknown':fmt(value)));vitalGrid.append(vital);
        }
        group.append(vitalGrid);
        const outcome=s.latest_outcome,production=outcome?.production?.[settlement.id],consumption=outcome?.consumption?.[settlement.id];
        const deaths=(outcome?.deaths||[]).filter(x=>x.settlement_id===settlement.id).reduce((sum,x)=>sum+(x.count||0),0);
        if(production||consumption){
          const producedFood=Number.isFinite(production?.food)&&production.food>=0?production.food:null,consumedFood=Number.isFinite(consumption?.food)&&consumption.food>=0?consumption.food:null;
          group.append(resourceFlowChart(producedFood,consumedFood));
          if(deaths){const losses=el('div','inspector-row');losses.append(el('span','','Recorded deaths this turn'),el('b','',fmt(deaths)));group.append(losses);}
        }else group.append(el('div','note-box condition-note','No local production or consumption outcome is recorded yet. Main economic issue and forecast are unrecorded.'));
        const facilities=(s.facilities||[]).filter(x=>x.settlement_id===settlement.id),projects=(s.projects||[]).filter(x=>x.settlement_id===settlement.id);
        row(group,'Recorded facilities',fmt(facilities.length));row(group,'Recorded projects',fmt(projects.length));
        group.append(el('div','inspector-section','RECORDED STOCKS'));
        const stocks=el('dl','economy-stock-grid');
        for(const [key,value] of Object.entries(settlement.stocks||{})){const reading=el('div','stock-reading');reading.append(el('dt','',titleCase(key)),el('dd','',fmt(value)));stocks.append(reading);}
        group.append(stocks);
        const details=el('details','record-identifiers');details.append(el('summary','','Record identifiers'));
        row(details,'Planet',settlement.planet_id);row(details,'Province',settlement.province_id);row(details,'Settlement ID',settlement.id);group.append(details);
        localPane.append(group);
      }
    }
    else localPane.append(el('div','note-box','Select a planet province to view recorded local holdings.'));
    campaignPane.append(el('div','inspector-section','CAMPAIGN-WIDE TOTALS'));
    const totals=economyTotals(s),grid=el('div','economy-grid');
    for(const [name,key]of [['POPULATION','population'],['FOOD','food'],['ORE','ore'],['ENERGY','energy'],['METALS','metals'],['MATERIEL','materiel'],['PROMETHIUM','promethium'],['CREDITS','credits']]){const box=el('div','economy-box');box.append(el('small','',name),el('strong','',totals[key]==null?'Unknown':fmt(totals[key])));grid.append(box);}campaignPane.append(grid);
    const chart=el('div','chart-box');const chartHead=el('div','economy-history-head');const stockHeading=el('div','inspector-section','CAMPAIGN STOCK HISTORY');chartHead.append(stockHeading);const metricLabel=el('label','economy-metric-label','RESOURCE '),metric=el('select','economy-metric');for(const [value,label]of [['food','Food'],['energy','Energy'],['ore','Ore']]){const option=el('option','',label);option.value=value;metric.append(option);}metric.value=state.economyHistoryMetric||'food';metricLabel.append(metric);chartHead.append(metricLabel);chart.append(chartHead);const chartPlot=el('div','economy-history-plot');chart.append(chartPlot);campaignPane.append(chart);root.append(localPane,campaignPane);
    const choose=(value)=>{const showLocal=value==='local'&&Boolean(province);localPane.hidden=!showLocal;campaignPane.hidden=showLocal;localButton.classList.toggle('active',showLocal);campaignButton.classList.toggle('active',!showLocal);window.HWDesktop?.setScope(selectedScope('economy'));};localButton.onclick=()=>choose('local');campaignButton.onclick=()=>choose('campaign');choose(local?'local':'campaign');
    const loading={context,chart},status={failed:false};state.economyLoading=loading;
    try{
      let stockRenderSeq=0;const renderStock=async(initial=false)=>{
      const selectedMetric=metric.value,seq=++stockRenderSeq;state.economyHistoryMetric=selectedMetric;stockHeading.textContent=`${titleCase(selectedMetric)} stock history · stock units`;chartPlot.replaceChildren();if(initial)metric.disabled=true;const svg=await historyChart(selectedMetric,null,'economy',status,status.items);
      if(seq!==stockRenderSeq||selectedMetric!==metric.value||epoch!==state.contextEpoch||state.campaignId!==campaignId||liveState()?.turn!==turn||managementContext()!==context||root!==$('#economy-panel')||root.dataset.context!==context||!chart.isConnected||!root.contains(chart))return;
      metric.disabled=false;
      if(svg)chartPlot.append(svg);else chartPlot.append(el('div','empty-note',status.failed?`${titleCase(selectedMetric)} stock history is unavailable. Reopen Economy to retry.`:turn===0?'One committed baseline is recorded. A second turn is needed to chart stock.':`No recorded ${selectedMetric} stock series is available yet.`));
      root.dataset.ready=String(!status.failed);
      };
      metric.onchange=()=>{status.failed=false;renderStock().catch(showError);};await renderStock(true);
    }finally{if(state.economyLoading===loading)state.economyLoading=null;}
  }
  function resourceFlowChart(produced,consumed){
    const box=el('div','resource-flow-chart');box.append(el('div','inspector-section','FOOD FLOW · THIS TURN'));
    const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 440 96');svg.setAttribute('role','img');svg.setAttribute('aria-label',`Recorded food production ${produced===null?'unknown':fmt(produced)} and consumption ${consumed===null?'unknown':fmt(consumed)}`);
    const max=Math.max(1,produced??0,consumed??0);const rows=[['Production',produced,'var(--apple-system-mint)'],['Consumption',consumed,'var(--apple-system-orange)']];
    rows.forEach(([label,value,color],i)=>{const y=20+i*38;const name=document.createElementNS(svg.namespaceURI,'text');name.setAttribute('x','0');name.setAttribute('y',String(y+12));name.setAttribute('fill','#343b3d');name.setAttribute('font-size','15');name.textContent=label;svg.append(name);const track=document.createElementNS(svg.namespaceURI,'rect');track.setAttribute('x','128');track.setAttribute('y',String(y));track.setAttribute('width','210');track.setAttribute('height','14');track.setAttribute('fill','#e2e5df');svg.append(track);if(value!==null){const bar=document.createElementNS(svg.namespaceURI,'rect');bar.setAttribute('x','128');bar.setAttribute('y',String(y));bar.setAttribute('width',String(Math.max(value>0?1:0,210*value/max)));bar.setAttribute('height','14');bar.setAttribute('fill',color);svg.append(bar);}const valueText=document.createElementNS(svg.namespaceURI,'text');valueText.setAttribute('x','350');valueText.setAttribute('y',String(y+12));valueText.setAttribute('fill','#343b3d');valueText.setAttribute('font-size','15');valueText.textContent=value===null?'Unknown':fmt(value);svg.append(valueText);});box.append(svg);return box;
  }
  async function historyChart(metric='food',comparison=null,source='economy',status=null,series=null) {
    const s=liveState();
    if(!s||!state.campaignId)return null;
    const epoch=state.contextEpoch,campaignId=state.campaignId,snapshotId=state.snapshot?.id;
    let items;
    if(source==='history'){
      const selectedTurn=state.snapshot?.turn??s.turn;
      items=state.history.filter(item=>item.turn<=selectedTurn);
    }else if(Array.isArray(series)){items=series.filter(item=>item.turn<=s.turn);
    }else{
      let first;try{first=await api(`/api/player/campaigns/${encodeURIComponent(campaignId)}/history?limit=1&offset=0`);}catch(_){if(status)status.failed=true;return null;}if(epoch!==state.contextEpoch||campaignId!==state.campaignId||snapshotId!==state.snapshot?.id)return null;
      if(!first.items.length){if(status)status.items=[];return null;}
      const visibleCount=Math.max(1,s.turn-first.items[0].turn+1),offset=Math.max(0,visibleCount-100);let data;
      try{data=await api(`/api/player/campaigns/${encodeURIComponent(campaignId)}/history?limit=100&offset=${offset}`);}catch(_){if(status)status.failed=true;return null;}if(epoch!==state.contextEpoch||campaignId!==state.campaignId||snapshotId!==state.snapshot?.id)return null;
      items=data.items.filter(item=>item.turn<=s.turn);if(status)status.items=items;
    }
    if(epoch!==state.contextEpoch||campaignId!==state.campaignId||snapshotId!==state.snapshot?.id)return null;
    if(!items.length)return null;
    const valid=items.filter(item=>Number.isFinite(item.metrics?.[metric]));
    if(valid.length<2)return null;
    const vals=valid.map(item=>item.metrics[metric]),peak=Math.max(1,...vals);
    const magnitude=10**Math.floor(Math.log10(peak/4));
    const tickStep=[1,2,5,10].find(step=>step*magnitude>=peak/4)*magnitude,max=tickStep*4;
    const graph=el('div','recorded-history-chart');
    if(comparison){const a=items.find(x=>x.turn===comparison[0]),b=items.find(x=>x.turn===comparison[1]);if(a&&b&&Number.isFinite(a.metrics?.[metric])&&Number.isFinite(b.metrics?.[metric]))graph.append(el('div','history-comparison',`Turn ${b.turn} vs ${a.turn}: ${fmt(b.metrics[metric]-a.metrics[metric])}`));}
    const plot=el('div','history-plot-grid'),axis=el('div','history-value-axis');axis.style.minWidth=`${Math.max(4,...Array.from({length:5},(_,y)=>fmt(max-y*tickStep).length))}ch`;axis.setAttribute('aria-hidden','true');
    const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
    svg.setAttribute('viewBox','0 0 640 144');svg.setAttribute('preserveAspectRatio','none');svg.setAttribute('role','img');svg.setAttribute('aria-label',`Recorded ${titleCase(metric.replaceAll('_',' '))} history, turns ${valid[0].turn} to ${valid.at(-1).turn}, scale 0 to ${fmt(max)}`);svg.dataset.metric=metric;
    for(let y=0;y<=4;y++){
      const label=el('span','',fmt(max-y*tickStep));label.style.top=`${y*25}%`;axis.append(label);
      const line=document.createElementNS(svg.namespaceURI,'line');
      line.setAttribute('x1','0');line.setAttribute('x2','640');line.setAttribute('y1',String(y*36));line.setAttribute('y2',String(y*36));line.setAttribute('stroke','#a4aaa6');line.setAttribute('vector-effect','non-scaling-stroke');svg.append(line);
    }
    const color=metric==='food'?'var(--apple-system-mint-contrast)':metric==='energy'?'var(--apple-system-blue-contrast)':metric==='ore'?'var(--apple-system-indigo-contrast)':'#343b3d';
    const points=valid.map((item,i)=>`${i*640/(valid.length-1)},${144-(item.metrics[metric]/max)*144}`).join(' ');
    const poly=document.createElementNS(svg.namespaceURI,'polyline');
    poly.setAttribute('points',points);poly.setAttribute('fill','none');poly.setAttribute('stroke',color);poly.setAttribute('stroke-width','2');poly.setAttribute('vector-effect','non-scaling-stroke');svg.append(poly);
    const turns=el('div','history-turn-axis');turns.append(el('span','',`Turn ${valid[0].turn}`),el('span','',`Turn ${valid.at(-1).turn}`));
    plot.append(axis,svg,turns);graph.append(plot);return graph;
  }

  async function renderHistory(){
    const campaignId=state.campaignId,snapshotId=state.snapshot?.id;
    const root=$('#history-panel');root.replaceChildren();root.setAttribute('aria-busy',String(state.historyLoading));
    root.append(el('h2','view-heading','Historical record'),el('p','view-sub','Immutable snapshots · compare recorded metrics, inspect a turn, or create a separate branch.'));
    const controls=el('div','history-controls');
    const prev=el('button','button small','← Earlier');prev.disabled=state.historyOffset===0;prev.onclick=()=>loadHistory(Math.max(0,state.historyOffset-state.historyPageSize)).catch(showError);
    const next=el('button','button small','Later →');next.disabled=state.historyOffset+state.history.length>=state.historyTotal;next.onclick=()=>loadHistory(state.historyOffset+state.historyPageSize).catch(showError);
    const grow=el('span','grow');const live=el('button','button small','Return to live');live.onclick=()=>loadCampaign().catch(showError);
    controls.append(prev,next,grow,el('span','',`${state.historyTotal?state.historyOffset+1:0}–${Math.min(state.historyOffset+state.history.length,state.historyTotal)} of ${state.historyTotal}`),live);root.append(controls);
    const metricRow=el('div','metric-controls');const metricLabel=el('label','','METRIC ');const metric=el('select');metric.id='history-metric';
    const metricLabels={population:'Owned population',food:'Food stock',ore:'Ore stock',energy:'Energy stock',treasury:'Credits',metals:'Metals stock',materiel:'Materiel stock',promethium:'Promethium stock',data:'Data stock',food_produced:'Food produced',energy_produced:'Energy produced',food_consumed:'Food consumed',energy_consumed:'Energy consumed',tax_revenue:'Tax receipts',trade_revenue:'Trade receipts',action_credit_spending:'Action credit spending',trade_spending:'Trade spending (included above)',military:'Active units and fleets',military_personnel:'Military personnel',projects:'Active projects',research:'Completed technologies',territories:'Owned settlements',facilities:'Facilities'};
    for(const [value,name]of Object.entries(metricLabels)){const option=el('option','',name);option.value=value;metric.append(option);}metric.value=state.historyMetric||'population';metricLabel.append(metric);
    const compareLabel=el('label','','COMPARE TURNS ');const from=el('select');from.id='history-compare-from';const to=el('select');to.id='history-compare-to';
    for(const item of state.history){for(const select of [from,to]){const option=el('option','',`Turn ${item.turn}`);option.value=item.turn;select.append(option);}}
    if(state.history.length){const turns=state.history.map(item=>item.turn);from.value=String(state.historyCompare&&turns.includes(state.historyCompare[0])?state.historyCompare[0]:turns[0]);to.value=String(state.historyCompare&&turns.includes(state.historyCompare[1])?state.historyCompare[1]:turns[turns.length-1]);}
    compareLabel.append(from,document.createTextNode(' → '),to);metricRow.append(metricLabel,compareLabel);root.append(metricRow);
    const chart=el('div','chart-box');chart.id='history-chart';root.append(chart);
    const redraw=()=>renderHistoryChart(root);metric.onchange=()=>{state.historyMetric=metric.value;redraw();};from.onchange=to.onchange=()=>{state.historyCompare=[Number(from.value),Number(to.value)];redraw();};if(state.historyLoading)root.querySelectorAll('button,select').forEach(control=>control.disabled=true);await redraw();
    if(!chart.isConnected||campaignId!==state.campaignId||snapshotId!==state.snapshot?.id)return;
    const wrap=el('div','table-wrap');const table=el('table','history-table');const thead=el('thead');const tr=el('tr');
    for(const h of ['TURN','POPULATION','FOOD','ORE','ENERGY','OUTCOME / NARRATIVE','ARCHIVE','VIEW'])tr.append(el('th','',h));thead.append(tr);table.append(thead);
    const tbody=el('tbody');
    for(const item of state.history){const row=el('tr');row.append(el('td','',fmt(item.turn)));for(const key of ['population','food','ore','energy'])row.append(el('td','',item.economy[key]==null?'Unknown':fmt(item.economy[key])));
      const outcome=el('td','narrative');outcome.append(el('span','',outcomeSummary(item.outcome)));if(item.narrative)outcome.append(el('div','',item.narrative));row.append(outcome,el('td','',item.archive_status||'—'));
      const view=el('td');const button=el('button','link-button','Inspect');button.setAttribute('aria-label',`Inspect turn ${item.turn}`);button.onclick=()=>selectHistorical(item.id).catch(showError);view.append(button);
      if(state.campaign?.kind==='demo'){view.append(document.createTextNode(' · '));const branch=el('button','link-button','Branch');branch.setAttribute('aria-label',`Restore turn ${item.turn} into a new branch`);branch.onclick=()=>restoreSnapshot(item.id,item.turn);view.append(branch);}row.append(view);tbody.append(row);}
    if(!state.history.length){const row=el('tr');const cell=el('td','','No committed snapshots yet.');cell.colSpan=8;row.append(cell);tbody.append(row);}table.append(tbody);wrap.append(table);root.append(wrap);if(state.historyLoading)root.querySelectorAll('button,select').forEach(control=>control.disabled=true);
  }
  async function renderHistoryChart(root){
    const chart=root.querySelector('#history-chart');if(!chart)return;chart.replaceChildren();
    const epoch=state.contextEpoch,campaignId=state.campaignId,snapshotId=state.snapshot?.id;
    const metric=$('#history-metric')?.value||'population';const from=Number($('#history-compare-from')?.value),to=Number($('#history-compare-to')?.value);
    const svg=await historyChart(metric,[from,to],'history');if(epoch!==state.contextEpoch||campaignId!==state.campaignId||snapshotId!==state.snapshot?.id||root!==$('#history-panel')||chart!==root.querySelector('#history-chart')||root.closest('.desk-window')?.hidden)return;
    const turns=state.history.filter(item=>item.turn<=(state.snapshot?.turn??Infinity)).map(item=>item.turn);
    chart.append(svg||el('div','empty-note',turns.length<2?'One committed baseline is recorded. A second turn is needed to compare points on a chart.':`No recorded ${metric} series is available for this snapshot page.`));
    const range=turns.length?`Turns ${Math.min(...turns)}–${Math.max(...turns)}.`:'No turns on this page.';const note=el('p','chart-note',`${range} ${metric==='military'?'Counts owned active units and fleets.':metric==='military_personnel'?'Counts owned ground strength and fleet crews.':metric==='projects'?'Counts active owned projects.':metric==='research'?'Counts completed technologies.':metric==='trade_spending'?'Trade spending is included in action credit spending.':'Values come from stored snapshot summaries.'}`);chart.append(note);
  }
  const reportSections={overview:'overview',economy:'economy',budget:'budget',logistics:'logistics',construction:'construction',research:'research',military:'military',diplomacy:'diplomacy',intelligence:'intelligence',exploration:'exploration',colonies:'colonies',characters:'characters',orders:'orders'};
  const reportAliases={industry:['economy','construction'],fleet:['military'],politics:['overview','diplomacy'],trade:['logistics','diplomacy'],factions:['diplomacy']};
  function managementPanel(view){let panel=state.managementPanels.get(view);if(panel)return panel;panel=el('section','view-panel');panel.id=`management-${view}`;state.managementPanels.set(view,panel);return panel;}
  function managementContext(){return `${state.contextEpoch}|${state.campaignId}|${state.snapshot?.id||''}|${liveState()?.turn??''}|${state.selectedProvince||''}|${state.mapRecord?.selected_planet?.id||''}`;}
  async function loadManagement(view){
    const campaignId=state.campaignId,snapshotId=state.snapshot?.id,turn=liveState()?.turn,epoch=state.contextEpoch,context=managementContext();
    const panel=managementPanel(view);if(state.managementContexts.get(view)===context||state.managementLoading.get(view)?.context===context)return;
    const request=(state.managementRequests.get(view)||0)+1;state.managementRequests.set(view,request);
    panel.replaceChildren();
    const s=liveState();if(!s){panel.append(el('div','note-box',state.campaign?'No approved pre-game baseline exists. All numerical and canonical values remain Unknown.':'Choose a campaign to view its records.'));state.managementContexts.set(view,context);return;}
    if(!s.settlements){panel.append(el('div','note-box','This section uses world-v2 management records. The selected world-v1 rules remain available through its map, economy, history and handoff views.'));state.managementContexts.set(view,context);return;}
    const sections=reportAliases[view]||[reportSections[view]||'overview'];let records=[];
    const loading={context,request};state.managementLoading.set(view,loading);
    try{records=await Promise.all(sections.map(section=>api(`/api/player/campaigns/${encodeURIComponent(campaignId)}/systems?section=${encodeURIComponent(section)}${snapshotId?`&snapshot_id=${encodeURIComponent(snapshotId)}`:''}`)));}
    catch(error){if(request===state.managementRequests.get(view)&&epoch===state.contextEpoch&&campaignId===state.campaignId&&snapshotId===state.snapshot?.id&&turn===liveState()?.turn&&managementContext()===context)panel.append(el('div','note-box',`Management records are unavailable: ${error.message}`));return;}
    finally{if(state.managementLoading.get(view)===loading)state.managementLoading.delete(view);}
    if(request!==state.managementRequests.get(view)||epoch!==state.contextEpoch||campaignId!==state.campaignId||snapshotId!==state.snapshot?.id||turn!==liveState()?.turn||managementContext()!==context)return;
    if(view==='construction'){
      const province=state.selectedProvince&&state.mapRecord?.geometry?.provinces?.find(x=>x.id===state.selectedProvince);
      const scopes=el('nav','scope-tabs');scopes.setAttribute('aria-label','Construction scope');
      const localButton=el('button','',province?`Local · ${province.name}`:'Local construction');localButton.type='button';localButton.dataset.scope='local';localButton.disabled=!province;
      const campaignButton=el('button','','Campaign construction');campaignButton.type='button';campaignButton.dataset.scope='campaign';scopes.append(localButton,campaignButton);panel.append(scopes);
      const localPane=el('section','scope-pane local-scope local-construction'),campaignPane=el('section','scope-pane campaign-scope');localPane.hidden=!province;campaignPane.hidden=Boolean(province);panel.append(localPane,campaignPane);
      renderLocalConstruction(localPane,records);
      campaignPane.append(el('div','inspector-section','CAMPAIGN-WIDE FACILITIES & PROJECTS · ALL SETTLEMENTS'));
      for(let i=0;i<records.length;i++){const data=records[i].records;if(sections[i]!==view)campaignPane.append(el('div','inspector-section',titleCase(sections[i])));renderRecord(campaignPane,data,view);}
      const choose=value=>{const local=value==='local'&&Boolean(province);localPane.hidden=!local;campaignPane.hidden=local;localButton.classList.toggle('active',local);campaignButton.classList.toggle('active',!local);window.HWDesktop?.setScope(selectedScope('construction'));};localButton.onclick=()=>choose('local');campaignButton.onclick=()=>choose('campaign');choose(province?'local':'campaign');
    }else for(let i=0;i<records.length;i++){const data=records[i].records;if(sections[i]!==view)panel.append(el('div','inspector-section',titleCase(sections[i])));renderRecord(panel,data,view);}
    if(view==='budget')panel.append(el('div','note-box','Trade spending is included in total action credit spending. Treat it as a breakdown, not an additional deduction.'));
    if(view==='orders')panel.append(el('div','note-box','Order envelopes are imported, previewed and committed in the separate Orders & handoff view. The backend owns every calculation.'));
    if(isHistorical())panel.append(el('div','note-box','Historical report · read only · values come from this selected snapshot.'));
    state.managementContexts.set(view,context);
  }
  function renderLocalConstruction(panel,records){
    const s=liveState(),geo=state.mapRecord?.geometry,province=state.selectedProvince&&geo?.provinces?.find(x=>x.id===state.selectedProvince),planet=state.mapRecord?.selected_planet||state.mapRecord?.parent;
    if(!province){panel.append(el('div','note-box','Select a mapped province to see its recorded facilities and projects. Campaign construction is available in the Campaign construction tab.'));return;}
    const settlements=(s?.settlements||[]).filter(x=>x.planet_id===planet?.id&&x.province_id===province.id),ids=new Set(settlements.map(x=>x.id));
    panel.append(el('div','scope-provenance',`Turn ${s?.turn??'Unknown'} · Saved ${state.snapshot?.created_at?formatSnapshotTime(state.snapshot.created_at):'time unknown'}`));
    if(!settlements.length){panel.append(el('div','empty-note','No recorded settlement matches this planet and province.'));return;}
    const facilities=(s?.facilities||[]).filter(x=>ids.has(x.settlement_id)),projects=(s?.projects||[]).filter(x=>ids.has(x.settlement_id));
    panel.append(el('div','scope-counts',`${facilities.length} recorded facilit${facilities.length===1?'y':'ies'} · ${projects.length} recorded project${projects.length===1?'':'s'}`));
    for(const settlement of settlements){
      const group=el('div','local-record-group');group.append(el('h3','local-record-title',settlement.name||'Recorded settlement'));
      for(const facility of facilities.filter(x=>x.settlement_id===settlement.id)){
        const item=el('div','local-record-row');const heading=el('strong','',titleCase(facility.kind||'Facility'));const status=el('span','local-record-status',facility.completed===true?'Complete':facility.completed===false?'In progress':'Status unknown');item.append(heading,status);
        const details=el('details','record-identifiers');details.append(el('summary','','Record IDs'));row(details,'Facility',facility.id);row(details,'Settlement',settlement.id);item.append(details);group.append(item);
      }
      const localProjects=projects.filter(x=>x.settlement_id===settlement.id);
      if(localProjects.length){group.append(el('div','inspector-section','PROJECTS'));for(const project of localProjects){const item=el('div','local-record-row');const heading=el('strong','',project.facility_kind?`${titleCase(project.facility_kind)} construction`:titleCase(project.kind||project.name||'Construction project'));item.append(heading);if(Number.isFinite(project.work_done)&&Number.isFinite(project.work_required)&&project.work_required>0&&project.work_done>=0&&project.work_done<=project.work_required){const progress=el('div','project-progress local-project-progress');const bar=document.createElement('progress');bar.max=project.work_required;bar.value=project.work_done;bar.setAttribute('aria-label',`Project work ${fmt(project.work_done)} of ${fmt(project.work_required)}`);progress.append(el('span','','WORK'),bar,el('strong','',`${fmt(project.work_done)} / ${fmt(project.work_required)}`));item.append(progress);}else item.append(el('div','view-sub local-project-progress-unknown','Work progress is not recorded.'));const details=el('details','record-identifiers');details.append(el('summary','','Record IDs'));row(details,'Project',project.id);row(details,'Settlement',settlement.id);item.append(details);group.append(item);}}
      panel.append(group);
    }
    if(!facilities.length&&!projects.length)panel.append(el('div','empty-note','No facilities or projects are recorded for the matching settlement IDs.'));
  }
  function safeValue(value){if(value===null||value===undefined)return 'Unknown';if(typeof value==='boolean')return value?'Yes':'No';if(typeof value==='object')return JSON.stringify(value);return String(value);}
  function resolveRecordReference(value){
    if(typeof value!=='string')return safeValue(value);
    const s=liveState(),records=[...(s?.nodes||[]),...(s?.settlements||[]),...(s?.facilities||[]),...(s?.projects||[]),...(state.mapRecord?.nodes||[]),...(state.mapRecord?.bodies||[]),...(state.mapRecord?.geometry?.provinces||[])];
    const match=records.find(record=>record.id===value);
    return match?.name||match?.title||(match?.kind?titleCase(match.kind):'No public label recorded');
  }
  function recordTitle(item){
    if(item.name||item.title)return String(item.name||item.title);
    if(item.role!==undefined)return `Character · ${titleCase(item.role)}`;
    if(item.kind)return titleCase(item.kind);
    if(item.type)return titleCase(item.type);
    return 'Recorded record';
  }
  function renderRecordCards(root,items,view='',section=''){
    if(!items.length){root.append(el('div','empty-note','No records are available for this view.'));return;}
    const visible=['kind','type','role','assignment','owner','status','location_id','system_id','planet_id','settlement_id','strength','crew','readiness','capacity','food_reserve','promethium_reserve','work_done','work_required','completed','experience','population','turn'];
    const relation=/^(location|system|planet|settlement)_id$/;
    for(const item of items){
      if(!item||typeof item!=='object'){root.append(el('div','record-summary',safeValue(item)));continue;}
      const forces=['military','fleet'].includes(view)||['units','fleets'].includes(section);
      const card=el('article',`record-summary${forces?' force-record':''}`);
      const recordLabel=section==='projects'&&item.facility_kind?`${titleCase(item.facility_kind)} construction`:recordTitle(item);
      const heading=el('header','force-record-head');const title=el('h3','record-summary-title',recordLabel);if(forces){const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('class','command-icon');svg.setAttribute('viewBox','0 0 24 24');svg.setAttribute('aria-hidden','true');const path=document.createElementNS('http://www.w3.org/2000/svg','path');path.setAttribute('d',section==='fleets'||view==='fleet'?'M2 15h20l-3 5H6zM5 12h14M8 9h8M11 3h2v9':'M12 3 20 7v5c0 5-4 8-8 10-4-2-8-5-8-10V7z');svg.append(path);title.replaceChildren(svg,document.createTextNode(` ${recordLabel}`));}heading.append(title);
      const locationKey=['location_id','system_id','planet_id','settlement_id'].find(key=>item[key]!==undefined&&item[key]!==null);
      if(forces){const identity=[item.owner&&titleCase(safeValue(item.owner)),item.status&&titleCase(safeValue(item.status)),locationKey&&resolveRecordReference(item[locationKey])].filter(Boolean).join(' · ');if(identity)heading.append(el('span','force-identity',identity));}
      card.append(heading);
      const facts=el('dl','record-facts');let shown=0;
      const fieldOrder=forces?[...['strength','crew','readiness'],...visible.filter(key=>!['strength','crew','readiness'].includes(key))]:visible;
      for(const key of fieldOrder){if(!(key in item)||key==='kind'&&recordTitle(item)===titleCase(item.kind)||forces&&(['owner','status'].includes(key)||key===locationKey))continue;
        if(item[key]===null||item[key]===undefined)continue;
        const value=relation.test(key)?resolveRecordReference(item[key]):key==='readiness'&&Number.isFinite(item[key])?`${safeValue(item[key])}%`:(['kind','type','role','owner','status','assignment'].includes(key)?titleCase(safeValue(item[key])):safeValue(item[key]));
        const fact=el('div',`record-fact fact-${key}`);fact.append(el('dt','',titleCase(key.replace(/_id$/,''))),el('dd','',value));if(key==='readiness'&&Number.isFinite(item.readiness)&&item.readiness>=0&&item.readiness<=100){const gauge=document.createElement('progress');gauge.max=100;gauge.value=item.readiness;gauge.setAttribute('aria-label',`Readiness ${item.readiness}%`);fact.append(gauge);}if(['strength','crew','readiness'].includes(key))fact.classList.add('force-primary');if(['food_reserve','promethium_reserve','capacity','location_id','system_id','planet_id','settlement_id'].includes(key))fact.classList.add('force-secondary');facts.append(fact);shown++;
      }
      if(section==='projects'){
        if(Number.isFinite(item.work_done)&&Number.isFinite(item.work_required)&&item.work_required>0&&item.work_done>=0&&item.work_done<=item.work_required){const progress=el('div','project-progress');const bar=document.createElement('progress');bar.max=item.work_required;bar.value=item.work_done;bar.setAttribute('aria-label',`Project work ${fmt(item.work_done)} of ${fmt(item.work_required)}`);progress.append(el('span','','WORK'),bar,el('strong','',`${fmt(item.work_done)} / ${fmt(item.work_required)}`));card.append(progress);}
        else card.append(el('div','view-sub project-progress-unknown','Work progress not recorded.'));
      }
      if(shown)card.append(facts);
      if(item.id){const inspect=el('button','link-button entity-select','Inspect record');inspect.type='button';inspect.onclick=()=>selectEntity(item);card.append(inspect);}
      const details=el('details','record-identifiers');details.append(el('summary','','All recorded fields'));
      for(const [key,value] of Object.entries(item))row(details,titleCase(key),safeValue(value));
      card.append(details);root.append(card);
    }
  }
  function renderRecord(root,data,view){
    if(data===null||data===undefined){root.append(el('div','empty-note','No recorded values for this turn.'));return;}
    if(Array.isArray(data)){renderRecordCards(root,data,view,view);return;}
    if(typeof data!=='object'){row(root,'Value',safeValue(data));return;}
    const entries=Object.entries(data);if(!entries.length){root.append(el('div','empty-note','No recorded values.'));return;}
    if(view==='fleet')entries.sort(([a],[b])=>(a==='fleets'?-1:0)-(b==='fleets'?-1:0));
    for(const [key,value] of entries){if(Array.isArray(value)){if(titleCase(key)!==titleCase(view))root.append(el('div','inspector-section',titleCase(key)));renderRecordCards(root,value,view,key);}
      else if(value&&typeof value==='object'){const box=el('div','report-group');box.append(el('div','report-group-title',titleCase(key)));for(const [sub,val]of Object.entries(value)){if(Array.isArray(val)){box.append(el('div','inspector-section',titleCase(sub)));renderTable(box,val,true);}else row(box,titleCase(sub),safeValue(val));}root.append(box);}
      else row(root,titleCase(key),safeValue(value));}
  }
  function renderTable(root,items,selectable=false){
    if(!items.length){root.append(el('div','empty-note','No records.'));return;}
    const cols=[...new Set(items.flatMap(item=>item&&typeof item==='object'?Object.keys(item):['record']))];const wrap=el('div','table-wrap');const table=el('table','history-table');const head=el('thead');const header=el('tr');for(const key of cols)header.append(el('th','',titleCase(key)));head.append(header);table.append(head);const body=el('tbody');
    for(const item of items){const tr=el('tr');if(selectable&&item&&typeof item==='object'&&item.id){tr.classList.add('selectable-record');tr.tabIndex=0;tr.setAttribute('aria-label',`Inspect ${item.name||item.id}`);tr.onclick=()=>selectEntity(item);tr.onkeydown=event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();selectEntity(item);}};}for(const key of cols){const cell=el('td','');const value=item&&typeof item==='object'?item[key]:item;if(selectable&&key==='id'&&item&&typeof item==='object'){const button=el('button','link-button entity-select',safeValue(value));button.type='button';button.onclick=event=>{event.stopPropagation();selectEntity(item);};cell.append(button);}else if(key==='work_done'&&item&&Number.isFinite(item.work_required)&&Number.isFinite(item.work_done)){const bar=document.createElement('progress');bar.max=Math.max(1,item.work_required);bar.value=Math.min(bar.max,item.work_done);bar.setAttribute('aria-label',`Project progress ${item.work_done} of ${item.work_required}`);cell.append(bar,document.createTextNode(` ${fmt(item.work_done)}/${fmt(item.work_required)}`));}else text(cell,safeValue(value));tr.append(cell);}body.append(tr);}table.append(body);wrap.append(table);root.append(wrap);
  }
  async function restoreSnapshot(snapshotId,turn){
    if(!state.gmToken){notify('Enter the GM token in Orders & handoff before restoring.',true);setView('orders');return;}
    if(!window.confirm(`Create a new demo branch from historical turn ${turn}? The existing campaign remains unchanged.`))return;
    const suggested=`${state.campaignId}-branch-${turn}`;const newId=window.prompt('New branch campaign ID',suggested);if(!newId)return;
    const campaignId=state.campaignId,epoch=state.contextEpoch;try{const data=await api(`/api/admin/campaigns/${encodeURIComponent(campaignId)}/restore`,{method:'POST',headers:authHeaders(true),body:JSON.stringify({snapshot_id:snapshotId,new_campaign_id:newId})});if(epoch!==state.contextEpoch||campaignId!==state.campaignId)return;clearCampaignContext();state.campaignId=data.campaign_id;setView('planet');await loadCampaigns(data.campaign_id);notify(`New branch created from turn ${turn}.`);}catch(e){if(epoch===state.contextEpoch&&campaignId===state.campaignId)showError(e);}
  }
  function outcomeSummary(o){if(!o)return 'Initial state';if(o.total_consumption){const production=Object.values(o.production||{}).reduce((sum,v)=>sum+(v.food||0),0);return `Food +${fmt(production)} / −${fmt(o.total_consumption.food||0)} · ${o.battles?.length||0} battles`;}return `Food −${fmt(o.food_consumed)} · Ore +${fmt(o.ore_produced)} · Energy +${fmt(o.energy_produced)}`;}

  function renderOrders(){
    const root=$('#orders-panel');root.replaceChildren();
    if(!state.campaign||state.campaign.kind!=='demo'){root.append(el('div','note-box','This pre-game campaign has no numeric rules baseline. Decision packets and turn submission are disabled.'));return;}
    if(isHistorical()){root.append(el('div','note-box','Return to the live campaign revision before preparing an order packet.'));return;}
    const grid=el('div','orders-grid'),left=el('div');
    const status=el('div','order-status');status.id='order-status';status.setAttribute('role','status');
    status.textContent=state.previewText?'Preview validated · Review the backend response before commit.':'No proposal loaded · Export a packet or load an example.';left.append(status);
    const actions=el('div','orders-actions');const packet=el('button','button','Export decision packet');packet.onclick=exportPacket;const example=el('button','button','Load example proposal');example.onclick=loadExample;actions.append(packet,example);left.append(actions);
    const source=el('details','order-source');source.append(el('summary','','Token and proposal JSON'));
    const token=el('div','form-row'),tokenLabel=el('label','','GM token · kept in page memory');tokenLabel.htmlFor='gm-token';token.append(tokenLabel);
    const input=el('input');input.type='password';input.id='gm-token';input.autocomplete='off';input.value=state.gmToken;input.placeholder='Set WOLD_GM_TOKEN on the server';input.oninput=()=>state.gmToken=input.value;token.append(input);source.append(token);
    const file=el('div','form-row'),fileLabel=el('label','','Import proposal file');fileLabel.htmlFor='proposal-file';file.append(fileLabel);
    const upload=el('input');upload.type='file';upload.id='proposal-file';upload.accept='application/json,.json';upload.onchange=async()=>{const fileRef=upload.files[0],epoch=state.contextEpoch,area=$('#proposal-json');if(!fileRef||!area)return;const value=await fileRef.text();if(epoch!==state.contextEpoch||!area.isConnected||area!==$('#proposal-json'))return;area.value=value;area.closest('details').open=true;invalidatePreview();};file.append(upload);source.append(file);
    const proposal=el('div','form-row'),proposalLabel=el('label','','Proposal JSON');proposalLabel.htmlFor='proposal-json';proposal.append(proposalLabel);
    const area=el('textarea');area.id='proposal-json';area.spellcheck=false;area.placeholder='Paste a proposal, or load an example.';area.oninput=invalidatePreview;proposal.append(area);source.append(proposal);left.append(source);
    const buttons=el('div','orders-actions'),preview=el('button','button','Preview');preview.id='preview-order';preview.onclick=previewOrder;
    const commit=el('button','button','Commit validated turn');commit.id='commit-order';commit.disabled=!state.previewText||state.previewText!==area.value;commit.onclick=commitOrder;buttons.append(preview,commit);left.append(buttons);
    const right=el('div');const box=el('div','gm-explainer','Export the current packet, load or paste its returned JSON, then preview the backend calculation. Commit only after reviewing it. Editing the proposal invalidates its preview.');
    right.append(box,el('div','inspector-section','BACKEND RESPONSE'),Object.assign(el('pre','result-box'),{id:'order-result',textContent:'No request yet.'}));grid.append(left,right);root.append(grid);
  }
  async function exportPacket(){const campaignId=state.campaignId,epoch=state.contextEpoch;try{const packet=await api(`/api/admin/campaigns/${encodeURIComponent(campaignId)}/packet`,{headers:authHeaders()});if(epoch!==state.contextEpoch||campaignId!==state.campaignId)return;const blob=new Blob([JSON.stringify(packet,null,2)],{type:'application/json'});const link=document.createElement('a');link.href=URL.createObjectURL(blob);link.download=`${state.campaignId}-decision-packet-turn-${packet.turn}.json`;link.click();URL.revokeObjectURL(link.href);setOrderStatus(`Packet exported · turn ${packet.turn} · load or paste the returned proposal.`);text($('#order-result'),`Packet exported · turn ${packet.turn} · hash ${packet.base_hash}`);}catch(e){if(epoch===state.contextEpoch&&campaignId===state.campaignId)showError(e);}}
  async function loadExample(){const campaignId=state.campaignId,epoch=state.contextEpoch;try{const packet=await api(`/api/admin/campaigns/${encodeURIComponent(campaignId)}/packet`,{headers:authHeaders()});if(epoch!==state.contextEpoch||campaignId!==state.campaignId)return;$('#proposal-json').value=JSON.stringify(packet.example,null,2);$('#proposal-json').closest('details').open=true;invalidatePreview();}catch(e){if(epoch===state.contextEpoch&&campaignId===state.campaignId)showError(e);}}
  function setOrderStatus(message){const status=$('#order-status');if(status)text(status,message);}
  function invalidatePreview(){state.previewText=null;state.previewProposal=null;window.HWDesktop?.setPreviewReady(false);const b=$('#commit-order');if(b)b.disabled=true;const result=$('#order-result');if(result&&state.view==='orders')text(result,'Proposal changed. Preview it again before committing.');if($('#proposal-json')?.value)setOrderStatus('Draft changed · Preview to validate before commit.');else setOrderStatus('No proposal loaded · Export a packet or load an example.');}
  function previewSummary(data) {
    if(data.duplicate)return {duplicate:true,snapshot_id:data.snapshot_id,turn:data.turn,state_hash:data.state_hash,outcome:data.outcome};
    const s=data.state;const totals=s?.owned_totals;
    return {duplicate:false,state_hash:data.state_hash,balances:s?{turn:s.turn,population:totals?.population??s.population,food:totals?.resources?.food??s.food,ore:totals?.resources?.ore??s.ore,energy:totals?.resources?.energy??s.energy,credits:totals?.resources?.credits}:undefined,outcome:data.outcome};
  }
  function renderPreviewSummary(data){
    const root=$('#order-result');if(!root)return;root.replaceChildren();const summary=previewSummary(data);
    const balances=summary.balances;
    root.append(el('strong','preview-summary-title',summary.duplicate?'Existing committed submission':'Backend preview · calculated result'));
    if(balances){const values=el('dl','preview-balances');for(const [key,value]of Object.entries(balances)){if(value!==undefined){const item=el('div','preview-balance');item.append(el('dt','',titleCase(key)),el('dd','',safeValue(value)));values.append(item);}}root.append(values);}
    if(summary.outcome&&typeof summary.outcome==='object'){
      const outcome=summary.outcome,outcomes=el('dl','preview-outcomes');
      root.append(el('div','preview-outcome-label','Preview outcome'));
      for(const [key,value]of Object.entries(outcome)){
        if(value&&typeof value==='object'&&!Array.isArray(value))continue;
        const item=el('div','preview-outcome');
        const label=Array.isArray(value)?`${titleCase(key)} records`:titleCase(key);
        const display=Array.isArray(value)?(value.length?`${value.length} recorded`:'None'):safeValue(value);
        item.append(el('dt','',label),el('dd','',display));outcomes.append(item);
      }
      root.append(outcomes);
      for(const key of ['production','consumption']){
        const records=outcome[key];if(!records||typeof records!=='object'||Array.isArray(records))continue;
        const breakdown=el('details','record-identifiers');
        breakdown.append(el('summary','',`${titleCase(key)} by settlement`));
        if(!Object.keys(records).length)breakdown.append(el('p','empty-note','None recorded.'));
        for(const [settlementId,resources]of Object.entries(records)){
          const saved=liveState()?.settlements?.find(item=>item.id===settlementId);
          const group=el('section','record-summary');group.append(el('h3','record-summary-title',saved?.name||'Settlement · name unrecorded'));
          const values=el('dl','preview-balances');
          if(resources&&typeof resources==='object'&&!Array.isArray(resources))for(const [resource,value]of Object.entries(resources)){
            if(value&&typeof value==='object')continue;
            const item=el('div','preview-balance');item.append(el('dt','',titleCase(resource)),el('dd','',safeValue(value)));values.append(item);
          }
          group.append(values);breakdown.append(group);
        }
        root.append(breakdown);
      }
    }
    const details=el('details','record-identifiers');details.append(el('summary','','Full backend response'));const raw=el('pre','result-box',JSON.stringify(data,null,2));details.append(raw);root.append(details);
  }
  async function previewOrder(){const campaignId=state.campaignId,epoch=state.contextEpoch;try{const area=$('#proposal-json');const parsed=JSON.parse(area.value);const data=await api(`/api/admin/campaigns/${encodeURIComponent(campaignId)}/preview`,{method:'POST',headers:authHeaders(true),body:JSON.stringify(parsed)});if(epoch!==state.contextEpoch||campaignId!==state.campaignId)return;state.previewText=area.value;state.previewProposal=parsed;$('#commit-order').disabled=false;window.HWDesktop?.setPreviewReady(true);setOrderStatus('Preview validated · Review the backend response before commit.');renderPreviewSummary(data);}catch(e){if(epoch!==state.contextEpoch||campaignId!==state.campaignId)return;state.previewText=null;window.HWDesktop?.setPreviewReady(false);$('#commit-order').disabled=true;setOrderStatus('Preview failed · Correct the proposal and try again.');showError(e);}}
  async function commitOrder(){const campaignId=state.campaignId,epoch=state.contextEpoch;const area=$('#proposal-json');if(!state.previewText||state.previewText!==area.value){invalidatePreview();return;}try{const data=await api(`/api/admin/campaigns/${encodeURIComponent(campaignId)}/commit`,{method:'POST',headers:authHeaders(true),body:JSON.stringify(state.previewProposal)});if(epoch!==state.contextEpoch||campaignId!==state.campaignId)return;state.previewText=null;window.HWDesktop?.setPreviewReady(false);$('#commit-order').disabled=true;text($('#order-result'),JSON.stringify(data,null,2));clearCampaignContext();state.campaignId=campaignId;await loadCampaign();notify(`Turn committed · archive ${data.archive_status||'pending'}`);}catch(e){if(epoch===state.contextEpoch&&campaignId===state.campaignId)showError(e);}}
  function showError(error){text($('#status-text'),error.message||String(error));notify(error.message||String(error),true);}

  function setView(view){window.HWDesktop?.open(view);}
  function startClock(){const update=()=>text($('#clock'),new Date().toLocaleTimeString('en-AU', {timeZone:'Australia/Melbourne',hour:'2-digit',minute:'2-digit',hour12:false}));update();setInterval(update,15000);}
  function initMap(){
    const canvas=$('#planet-map');
    canvas.addEventListener('pointerdown',e=>{if(e.button!==0)return;canvas.setPointerCapture(e.pointerId);state.drag={x:e.clientX,y:e.clientY,startX:state.panX,startY:state.panY,moved:false};window.HWDesktop?.setGesture(true);});
    canvas.addEventListener('pointermove',e=>{
      const point=canvasPoint(e);if(state.drag){const dx=e.clientX-state.drag.x,dy=e.clientY-state.drag.y;if(Math.abs(dx)+Math.abs(dy)>3)state.drag.moved=true;state.panX=state.drag.startX+dx;state.panY=state.drag.startY+dy;drawMap();return;}
      const tip=$('#map-tooltip');
      if(state.transform?.hierarchy){const hit=nearestMapNode(point);if(!hit){tip.hidden=true;return;}tip.hidden=false;text(tip,`${hit.n.name} · ${titleCase(hit.n.knowledge)} · click to inspect`);tip.style.left=`${Math.min(point.x+12,canvas.clientWidth-190)}px`;tip.style.top=`${Math.min(point.y+12,canvas.clientHeight-35)}px`;return;}
      const tile=tileAt(point);if(!tile){tip.hidden=true;return;}tip.hidden=false;const p=tile.province_id&&state.mapRecord?.geometry?.provinces.find(x=>x.id===tile.province_id);text(tip,`Hovered terrain: ${terrainLabels[tile.terrain]||tile.terrain} · ${p?p.name:'Open water'} · ${tile.x}, ${tile.y}`);tip.style.left=`${Math.min(point.x+12,canvas.clientWidth-240)}px`;tip.style.top=`${Math.min(point.y+12,canvas.clientHeight-35)}px`;
    });
    canvas.addEventListener('pointerup',e=>{if(!state.drag)return;const drag=state.drag;state.drag=null;window.HWDesktop?.setGesture(false);if(drag.moved)return;const point=canvasPoint(e);if(state.transform?.hierarchy){const hit=nearestMapNode(point);if(hit){const next={sector:'sector',system:'system',planet:'planet'}[hit.n.kind];if(next){state.mapLevel=next;state.mapNodeId=hit.n.id;$('#map-level').value=next;state.zoom=1;state.panX=state.panY=0;loadMap();}}return;}const tile=tileAt(point);state.selectedEntity=null;state.selectedProvince=tile?.province_id||null;renderInspector(liveState(),state.campaign);if(tile?.province_id){window.HWDesktop?.positionInspector(e.clientX);window.HWDesktop?.open('inspector');}drawMap();});
    const cancel=()=>{state.drag=null;window.HWDesktop?.setGesture(false);};canvas.addEventListener('pointercancel',cancel);canvas.addEventListener('lostpointercapture',cancel);canvas.addEventListener('pointerleave',()=>$('#map-tooltip').hidden=true);canvas.addEventListener('wheel',e=>{e.preventDefault();zoomMap(e.deltaY<0?1.15:1/1.15);},{passive:false});let drawFrame=0;const observer=new ResizeObserver(()=>{if(drawFrame)return;drawFrame=requestAnimationFrame(()=>{drawFrame=0;drawMap();});});const observed=[canvas.parentElement,...document.querySelectorAll('.commandbar,#resource-shell,#view-title,#map-breadcrumbs,#live-banner,.map-caption,#map-legend,.map-footer')];for(const node of new Set(observed))if(node)observer.observe(node);
  }
  function nearestMapNode(point){const{positions=[],safeRect}=state.transform||{};if(safeRect&&(point.x<safeRect.left||point.x>safeRect.right||point.y<safeRect.top||point.y>safeRect.bottom))return null;let found=null,distance=Infinity;for(const item of positions){if(safeRect&&(item.x<safeRect.left||item.x>safeRect.right||item.y<safeRect.top||item.y>safeRect.bottom))continue;const d=Math.hypot(item.x-point.x,item.y-point.y);if(d<distance){found=item;distance=d;}}return distance<26?found:null;}
  function resetPaneLayout(){window.HWDesktop?.resetLayout();notify('Window positions and sizes reset.');}

  function zoomMap(mult){state.zoom=Math.max(1,Math.min(5,state.zoom*mult));if(state.zoom===1)state.panX=state.panY=0;text($('#zoom-reset'),`${Math.round(state.zoom*100)}%`);drawMap();}
  function installNavIcons(){const colors=['var(--apple-system-blue)','var(--apple-system-mint)','var(--apple-system-teal)','var(--apple-system-indigo)'];document.querySelectorAll('.nav-item').forEach((button,index)=>{const view=button.dataset.view;button.title=titleCase(view);button.setAttribute('aria-label',`Open ${titleCase(view)} report`);if(button.querySelector('.nav-icon'))return;const icon=el('span','nav-icon');icon.setAttribute('aria-hidden','true');const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 16 16');svg.setAttribute('aria-hidden','true');const base=colors[index%colors.length];const shapes=[[[2,2],[3,2],[2,3],[3,3]],[[1,1],[2,1],[3,1],[1,2],[3,2],[1,3],[2,3],[3,3]],[[1,3],[2,2],[3,1],[3,2],[3,3]],[[1,1],[2,1],[3,1],[1,2],[2,2],[3,2],[2,3],[2,4]]][index%4];for(const [x,y]of shapes){const rect=document.createElementNS(svg.namespaceURI,'rect');rect.setAttribute('x',String(x*2));rect.setAttribute('y',String(y*2));rect.setAttribute('width','2');rect.setAttribute('height','2');rect.setAttribute('fill',base);svg.append(rect);}const frame=document.createElementNS(svg.namespaceURI,'rect');frame.setAttribute('x','1');frame.setAttribute('y','1');frame.setAttribute('width','14');frame.setAttribute('height','14');frame.setAttribute('fill','none');frame.setAttribute('stroke','#283743');frame.setAttribute('stroke-width','1');svg.append(frame);icon.append(svg);button.insertBefore(icon,button.firstChild);});}
  function clearCampaignContext(){state.contextEpoch++;state.campaignLoadSeq++;state.campaignListSeq++;state.historyLoadSeq++;state.mapLoadSeq++;state.snapshotLoadSeq++;for(const [view,seq]of state.managementRequests)state.managementRequests.set(view,seq+1);state.campaign=null;state.snapshot=null;state.history=[];state.historyLoading=false;state.historyTotal=0;state.historyOffset=0;state.selectedProvince=null;state.selectedEntity=null;state.mapRecord=null;state.mapNodeId=null;state.mapLevel='galactic';state.panX=state.panY=0;state.zoom=1;state.previewText=null;state.previewProposal=null;state.managementContexts.clear();state.managementLoading.clear();state.economyLoading=null;state.historyMetric='population';state.historyCompare=null;for(const panel of state.managementPanels.values())panel.replaceChildren();for(const id of ['economy-panel','history-panel','orders-panel'])$( `#${id}`).replaceChildren();$('#orders-panel').dataset.ready='';$('#campaign-kind').textContent='NO CAMPAIGN';$('#turn-badge').textContent='TURN —';$('#historical-badge').hidden=true;render();}
  function createManagementWindow(view){let panel=managementPanel(view);const labels={industry:'Industry',fleet:'Fleet',politics:'Politics',trade:'Trade',factions:'Factions',budget:'Budget',logistics:'Logistics',construction:'Construction',research:'Research',military:'Military',diplomacy:'Diplomacy',intelligence:'Intelligence',exploration:'Exploration',colonies:'Colonies',characters:'Characters'};const i=[...document.querySelectorAll('.sidebar .nav-item')].find(button=>button.dataset.view===view);const index=i?[...document.querySelectorAll('.sidebar .nav-item')].indexOf(i):4;return window.HWDesktop.createWindow(view,labels[view]||titleCase(view),panel,{x:Math.max(12,90+(index%6)*30),y:Math.max(12,55+(index%5)*28),w:520,h:460});}
  function onWindowOpen(view){state.view=view;window.HWDesktop?.setScope(selectedScope(view));if(view==='planet'){if(state.campaign&&liveState()&&!state.mapRecord)loadMap().catch(showError);}else if(view==='economy')renderEconomy().catch(showError);else if(view==='history'){if(!state.history.length&&!state.historyLoading)loadHistory(0).catch(showError);else renderHistory();}else if(view==='orders'){if(!$('#orders-panel').dataset.ready){renderOrders();$('#orders-panel').dataset.ready='true';}}else if(isManagementView(view))loadManagement(view).catch(showError);}
  function wire(){
    installNavIcons();$('#campaign-select').addEventListener('change',async e=>{const id=e.target.value||null;if(!id)return;clearCampaignContext();state.campaignId=id;state.view='planet';$('#map-level').value='galactic';render();window.HWDesktop.close('campaign');const epoch=state.contextEpoch;try{await loadCampaign();}catch(error){if(epoch===state.contextEpoch&&state.campaignId===id)showError(error);}});$('#refresh-button').onclick=()=>loadCampaigns(state.campaignId).catch(showError);
    $('#overlay-select').onchange=e=>{state.overlay=e.target.value;loadMap();};$('#map-level').onchange=e=>setMapLevel(e.target.value);$('#zoom-in').onclick=()=>zoomMap(1.2);$('#zoom-out').onclick=()=>zoomMap(1/1.2);$('#zoom-reset').onclick=()=>{state.zoom=1;state.panX=state.panY=0;text($('#zoom-reset'),'100%');drawMap();};$('#reset-layout').onclick=resetPaneLayout;$('#login-button').onclick=login;$('#logout-button').onclick=logout;$('#status-text').textContent='Connecting';
    window.HWDesktop.init();window.HWDesktop.setOnOpen(onWindowOpen);window.HWDesktop.setOnFocus(view=>{state.view=view;});window.HWDesktop.setOnCreate(createManagementWindow);
  }
  async function login(){const token=$('#access-token').value.trim();if(!token){notify('Enter an access token.',true);return;}clearCampaignContext();state.campaignId=null;state.accessToken=token;state.gmToken=token;const epoch=state.contextEpoch;$('#logout-button').hidden=false;$('#login-button').hidden=true;text($('#status-text'),'Checking private access');try{await loadCampaigns();if(epoch!==state.contextEpoch)return;text($('#status-text'),'Private access verified · choose a campaign');notify('Signed in for this page session.');}catch(error){if(epoch!==state.contextEpoch)return;state.accessToken='';state.gmToken='';$('#logout-button').hidden=true;$('#login-button').hidden=false;notify(error.message,true);}}
  function logout(){clearCampaignContext();state.accessToken='';state.gmToken='';state.campaigns=[];state.campaignId=null;$('#campaign-select').replaceChildren(new Option('Select campaign…',''));$('#access-token').value='';$('#logout-button').hidden=true;$('#login-button').hidden=false;render();window.HWDesktop.open('campaign');text($('#status-text'),'Sign in required');}
  async function boot(){wire();initMap();startClock();$('#campaign-select').append(new Option('Select campaign…',''));window.HWDesktop.open('campaign');try{const access=await api('/api/access');state.privateMode=access.login_required;$('#access-box').hidden=!state.privateMode;if(state.privateMode){text($('#status-text'),'Sign in required');return;}await loadCampaigns();text($('#status-text'),state.campaignId?'Connected to local campaign database':'Choose a campaign');}catch(e){text($('#status-text'),`API unavailable · ${e.message}`);notify(`Backend unavailable: ${e.message}`,true);} }
  boot();
})();
