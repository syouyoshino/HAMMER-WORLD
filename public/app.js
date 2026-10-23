(() => {
  'use strict';
  const $ = (selector, root = document) => root.querySelector(selector);
  const state = {campaigns: [], campaignId: null, campaign: null, snapshot: null, view: 'planet', selectedProvince: null,
    history: [], historyLoading: false, historyTotal: 0, historyOffset: 0, historyPageSize: 50, zoom: 1, panX: 0, panY: 0, drag: null,
    campaignLoadSeq: 0, campaignListSeq: 0, historyLoadSeq: 0, managementSeq:0, mapLoadSeq:0, snapshotLoadSeq:0, contextEpoch:0, selectedEntity:null,
    mapLevel:'planet', mapNodeId:null, mapRecord:null, accessToken:'', privateMode:false, accessStatus:'checking', managementSection:null,
    overlay: 'terrain', mapStyle: 'orbital', gmToken: '', previewText: null, previewProposal: null, historyCompare:null, toastTimer: null, managementPanels:new Map(), managementRequests:new Map(), managementContexts:new Map(), managementLoading:new Map(), economyLoading:null};
  let forceMap;
  let movementIntent=null;
  const movementRequests=[];
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
    try{campaigns=await api('/api/player/campaigns');}catch(error){if(epoch===state.contextEpoch&&request===state.campaignListSeq){state.accessStatus='unavailable';updateCampaignSummary();throw error;}return false;}
    if(request!==state.campaignListSeq||epoch!==state.contextEpoch)return false;
    state.campaigns=campaigns;state.accessStatus='ready';
    const select=$('#campaign-select'); select.replaceChildren(new Option('Select campaign…',''));
    for(const campaign of campaigns){const option=el('option','',`${campaign.id} · ${campaign.kind==='demo'?'fictional demo':'pre-game'}`); option.value=campaign.id; select.append(option);}
    if(!campaigns.length){state.campaignId=null;state.campaign=null;state.snapshot=null;updateCampaignSummary();return true;}
    const preferredId = preferred && campaigns.some(c=>c.id===preferred) ? preferred : null;
    const currentId = campaigns.some(c=>c.id===state.campaignId) ? state.campaignId : null;
    state.campaignId = preferredId || currentId || null;
    select.value=state.campaignId||'';updateCampaignSummary();
    if(state.campaignId)await loadCampaign();
    return request===state.campaignListSeq&&epoch===state.contextEpoch;
  }
  async function loadCampaign() {
    if(!state.campaignId)return;
    const campaignId=state.campaignId;
    const preserveMap=state.campaignId===campaignId&&Boolean(state.campaign)&&!isHistorical();
    const priorSnapshotId=state.snapshot?.id;
    const prior={level:state.mapLevel,nodeId:state.mapNodeId,province:state.selectedProvince,entity:state.selectedEntity,panX:state.panX,panY:state.panY,zoom:state.zoom,mapRecord:state.mapRecord};
    const request=++state.campaignLoadSeq,epoch=state.contextEpoch;
    let data;try{data=await api(`/api/player/campaigns/${encodeURIComponent(campaignId)}`);}catch(error){if(request===state.campaignLoadSeq&&epoch===state.contextEpoch&&campaignId===state.campaignId)throw error;return;}
    if(request!==state.campaignLoadSeq||epoch!==state.contextEpoch||campaignId!==state.campaignId)return;
    state.campaign=data;state.snapshot=data.state?{id:data.snapshot_id,turn:data.turn,state:data.state,archive_status:data.archive_status,created_at:data.created_at}:null;if(state.previewText&&priorSnapshotId!==state.snapshot?.id)invalidatePreview();
    if(preserveMap){state.selectedProvince=prior.province;state.selectedEntity=prior.entity?Object.values(data.state||{}).filter(Array.isArray).flat().find(item=>item?.id===prior.entity.id)||null:null;state.mapLevel=prior.level;state.mapNodeId=prior.nodeId;state.mapRecord=prior.mapRecord;state.panX=prior.panX;state.panY=prior.panY;state.zoom=prior.zoom;}
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
    updateCampaignSummary();
    window.HWDesktop?.setScope(selectedScope(state.view));
    const name=s?(state.mapRecord?.selected_planet?.name||state.mapRecord?.parent?.name||s.nodes?.find(n=>n.kind==='planet'&&n.knowledge==='surveyed')?.name||'Campaign overview'):(campaign?campaign.id:'Campaign unavailable');
    $('#map-level').value=state.mapLevel;
    $('#live-banner').hidden=!isHistorical();if(isHistorical())text($('#live-banner'),`Historical snapshot · turn ${snapshot.turn} · read only. Orders cannot be submitted against this revision.`);
    drawMap();renderMapLegend();renderMapBreadcrumbs();renderMapHeading();
  }
  function updateCampaignSummary(){
    const campaign=state.campaign,snapshot=state.snapshot;
    for(const id of ['refresh-button','dialog-refresh-campaigns']){const refresh=$(`#${id}`);if(refresh)refresh.disabled=state.accessStatus==='checking';}
    const modalSelect=$('#dialog-campaign-select'),mainSelect=$('#campaign-select');
    if(modalSelect&&mainSelect){
      const options=[...mainSelect.options];
      if(options.length!==modalSelect.options.length||options.some((option,index)=>option.value!==modalSelect.options[index]?.value||option.textContent!==modalSelect.options[index]?.textContent))modalSelect.replaceChildren(...options.map(option=>option.cloneNode(true)));
      modalSelect.value=mainSelect.value;modalSelect.disabled=options.length<2||state.accessStatus!=='ready'||Boolean(state.privateMode&&!state.accessToken);
    }
    const kind=campaign?.kind==='demo'?'Fictional demo':campaign?.kind==='pregame'?'Pre-game · values unset':campaign?.kind?titleCase(campaign.kind):'Kind unknown';
    const campaignName=campaign?(campaign.name&&campaign.name!==campaign.id?`${campaign.name} · ${campaign.id}`:campaign.id):state.campaignId;
    const access=state.accessStatus==='checking'?'Checking access':state.accessStatus==='unavailable'?'Access unavailable':state.privateMode?(state.accessToken?'Private access verified':'Sign in required'):'Local access';
    window.HWDesktop?.refreshIndicators({campaign:campaign?(campaign.kind==='demo'?'FICTIONAL DEMO':'PRE-GAME · UNSET'):'UNSELECTED',campaignSummary:campaignName?`${campaignName} · ${kind}`:'No campaign selected',kind:campaign?.kind,hasSnapshot:Boolean(snapshot?.state),turn:snapshot?.turn,historical:isHistorical(),archive:snapshot?.archive_status||'unknown',access,pending:snapshot?.archive_status==='pending',snapshotTime:snapshot?.created_at?`SAVED ${formatSnapshotTime(snapshot.created_at)}`:null,previewReady:Boolean(state.previewText&&state.previewText===$('#proposal-json')?.value)});
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
    for(const [name,value,note] of items){const card=el('div','resource-card');if(!s)card.classList.add('is-unknown');card.append(el('span','resource-name',name),el('strong','resource-value',value),el('span','resource-note',s?note:(campaign&&campaign.kind==='pregame'?'Awaiting approved baseline':'No saved snapshot')));root.append(card);}
  }
  function economyTotals(s){if(!s)return null;if(s.owned_totals)return {population:s.owned_totals.population,...s.owned_totals.resources};if(s.settlements){const owned=s.settlements.filter(x=>x.owned);const totals={population:owned.reduce((a,x)=>a+(x.civilians||0),0)+(s.units||[]).filter(x=>x.owner==='player').reduce((a,x)=>a+(x.strength||0),0)+(s.fleets||[]).filter(x=>x.owner==='player').reduce((a,x)=>a+(x.crew||0),0)+(s.expeditions||[]).filter(x=>x.kind==='colonize').reduce((a,x)=>a+(x.settlers||0),0)};for(const k of ['food','ore','energy','materiel','data','metals','promethium','credits'])totals[k]=owned.reduce((a,x)=>a+(x.stocks?.[k]||0),0);for(const f of s.fleets||[])if(f.owner==='player'){totals.food+=f.food_reserve||0;totals.promethium+=f.promethium_reserve||0;}for(const u of s.units||[])if(u.owner==='player'){totals.food+=u.food_reserve||0;totals.food+=u.transit_food||0;}for(const sh of s.shipments||[])totals[sh.resource]=(totals[sh.resource]||0)+sh.quantity;for(const m of s.expeditions||[])if(m.kind==='colonize')totals.food+=m.food_cargo||0;return totals;}return {population:s.population,food:s.food,ore:s.ore,energy:s.energy};}
  function renderInspector(s,campaign) {
    updateMapSelectionHint();
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
  function terrainLabel(geo,terrain){const preset=geo?.surface?.preset;if(preset==='arid')return ({plains:'Dry plains',rock:'Rocklands'})[terrain]||terrainLabels[terrain]||terrain;if(preset==='barren')return terrain==='rock'?'Exposed rock':terrainLabels[terrain]||terrain;if(preset==='frozen')return ({plains:'Ice field',rock:'Frozen rock'})[terrain]||terrainLabels[terrain]||terrain;return terrainLabels[terrain]||terrain;}
  function provinceTerrain(geo,p){const counts={};for(const t of geo?.tiles||[])if(t.province_id===p.id)counts[t.terrain]=(counts[t.terrain]||0)+1;const terrain=Object.entries(counts).sort((a,b)=>b[1]-a[1])[0]?.[0];return terrain?terrainLabel(geo,terrain):'No land tiles';}
  function renderReport(s){const root=$('#turn-report');root.replaceChildren();text($('#report-turn'),s?`TURN ${s.turn}`:'—');const o=s?.latest_outcome||s?.outcomes?.at(-1);if(!o){root.append(el('div','empty-note',s?'No turn has been resolved yet.':'No recorded report.'));return;}const prod=o.production?Object.values(o.production).reduce((a,x)=>{for(const [k,v]of Object.entries(x))a[k]=(a[k]||0)+v;return a;},{}):{};const cons=o.consumption?Object.values(o.consumption).reduce((a,x)=>{for(const [k,v]of Object.entries(x))a[k]=(a[k]||0)+v;return a;},{}):{};const consumedFood=o.total_consumption?.food??cons.food??o.food_consumed;const populationLost=Array.isArray(o.deaths)?o.deaths.reduce((a,x)=>a+x.count,0):o.population_lost;for(const [k,v]of [['Food produced',prod.food??o.food_produced],['Food consumed',consumedFood],['Ore produced',prod.ore??o.ore_produced],['Energy produced',prod.energy??o.energy_produced],['Population lost',populationLost]]){const line=el('div','report-line');line.append(el('span','',k),el('b','',v==null?'Unknown':fmt(v)));root.append(line);}}
  function renderLog(s){const root=$('#command-log');root.replaceChildren();if(!s){root.append(el('div','empty-note','No events recorded.'));return;}if(s.narrative)root.append(el('div','',s.narrative));else root.append(el('div','empty-note',s.turn===0?'Initial demonstration state committed.':'No narrative supplied for this turn.'));}

  async function loadMap(){const campaignId=state.campaignId,s=liveState();if(!campaignId||!s){drawMap();return;}const request=++state.mapLoadSeq,epoch=state.contextEpoch,snapshotId=state.snapshot?.id,overlay=state.overlay,level=state.mapLevel;const parentId=state.mapNodeId,priorProvince=state.selectedProvince,priorEntity=state.selectedEntity;if(!s.nodes){state.mapLevel='planet';$('#map-level').value='planet';state.mapRecord={level:'planet',selected_planet:s.planet,geometry:{planet:s.planet,provinces:s.provinces,tiles:s.tiles},records:[]};drawMap();renderMapLegend();renderMapBreadcrumbs();renderMapHeading();renderInspector(s,state.campaign);return;}const historical=isHistorical()?`&snapshot_id=${encodeURIComponent(state.snapshot.id)}`:'';let query=`level=${encodeURIComponent(level)}${historical}`;if(level!=='galactic'&&parentId)query+=`&node_id=${encodeURIComponent(parentId)}`;try{const data=await api(`/api/player/campaigns/${encodeURIComponent(campaignId)}/map?${query}&overlay=${encodeURIComponent(overlay)}`);if(request!==state.mapLoadSeq||epoch!==state.contextEpoch||campaignId!==state.campaignId||snapshotId!==state.snapshot?.id||level!==state.mapLevel||parentId!==state.mapNodeId||overlay!==state.overlay)return;const enteringPlanet=level==='planet'&&(state.mapRecord?.level!=='planet'||state.mapRecord?.selected_planet?.id!==data.selected_planet?.id);state.mapRecord=data;if(enteringPlanet&&['planet-v5','planet-v6','planet-v7'].includes(data.geometry?.surface?.version)){const c=$('#planet-map'),g=data.geometry;state.zoom=2*minPlanetZoom(g,c.parentElement.clientWidth,c.parentElement.clientHeight);state.panX=state.panY=0;centerOnProvince(s.settlements?.find(item=>item.owned)?.province_id);}state.selectedProvince=priorProvince&&data.geometry?.provinces?.some(x=>x.id===priorProvince)?priorProvince:null;state.selectedEntity=priorEntity;drawMap();renderMapBreadcrumbs();renderMapHeading();renderMapLegend();renderInspector(s,state.campaign);}catch(error){if(epoch===state.contextEpoch&&campaignId===state.campaignId&&request===state.mapLoadSeq)notify(error.message,true);}}
  function updateMapSelectionHint(){
    const hint=$('.map-footer span');if(!hint)return;
    const province=state.selectedProvince&&state.mapRecord?.geometry?.provinces?.find(item=>item.id===state.selectedProvince);
    const selectedLabel=state.selectedEntity?recordTitle(state.selectedEntity):province?.name;
    const level=state.mapRecord?.level||state.mapLevel;
    const label=selectedLabel?String(selectedLabel):null;
    text(hint,label?`◉ Selected · ${label.length>32?`${label.slice(0,31)}…`:label}`:level==='planet'?'◉ Select a province to inspect':'◉ Select a recorded body to descend');
  }
  function renderMapHeading(){
    const styleControl=$('#map-style');styleControl.disabled=state.mapRecord?.level!=='planet'||!state.mapRecord?.geometry;styleControl.title=styleControl.disabled?'Surface style is available in Planet view':'Planet surface presentation';
    const record=state.mapRecord,hints=[...document.querySelectorAll('.map-footer span')];
    if(!record){text($('.section-title h1'),state.campaign?'No recorded geography':'Campaign geography unavailable');text($('.eyebrow'),'CAMPAIGN GEOGRAPHY');text($('#map-coordinates'),'CAMPAIGN GEOGRAPHY · NOT RECORDED');text($('#map-scale'),'—');if(hints.length){text(hints[0],'◉ No recorded map context');text(hints[1],'No geography available for this campaign');}return;}
    const level=record.level||'planet',subject=level==='galactic'?'The Reach':record.selected_planet?.name||record.parent?.name||'Map';text($('.section-title h1'),`${subject} · ${titleCase(level)}`);text($('.eyebrow'),`${titleCase(level).toUpperCase()} CARTOGRAPHY`);
    const surface=record.geometry?.surface,surfaceVersion=surface?.version;
    const planetLabel=['planet-v4','planet-v5','planet-v6','planet-v7'].includes(surfaceVersion)?`${surfaceVersion.toUpperCase()} · ${String(surface.preset).toUpperCase()}${surfaceVersion==='planet-v7'?`${surface.geology==='cratered'?' · CRATERED':''} · EAST–WEST WRAPPING`:surfaceVersion==='planet-v6'?' · EAST–WEST WRAPPING':''}`:['planet-v2','planet-v3'].includes(surfaceVersion)?`${surfaceVersion.toUpperCase()} SURFACE`:'PLANET-V1 · TERRAIN ONLY';
    text($('#map-coordinates'),level==='system'?'SYSTEM CHART · TOPOLOGICAL · NOT ORBITAL POSITIONS':level==='planet'?`PLANET CARTOGRAPHY · ${record.parent?.name||subject} · ${planetLabel}`:`${titleCase(level).toUpperCase()} CARTOGRAPHY · ${record.parent?.name||subject}`);
    const geometry=record.geometry?.planet;text($('#map-scale'),geometry?`${geometry.width} × ${geometry.height} GRID`:`${(record.nodes||[]).length} RECORDED`);if(hints.length){updateMapSelectionHint();text(hints[1],level==='planet'?'Drag to pan · wheel or buttons to zoom':'Click a known marker · drag to pan · wheel to zoom');}
  }
  function renderMapBreadcrumbs(){const root=$('#map-breadcrumbs');if(!root)return;root.replaceChildren();if(!state.mapRecord){root.textContent='No recorded map context';return;}const names=[['galactic','The Reach',null]];let nodeId=state.mapNodeId;const s=liveState();if(nodeId&&s){const chain=[];let node=s.nodes.find(n=>n.id===nodeId);while(node){chain.unshift(node);node=s.nodes.find(n=>n.id===node.parent_id);}for(const [index,n] of chain.entries()){const sameRoot=index===0&&n.name===names[0][1]&&(n.kind==='galaxy'||n.kind==='region');if(sameRoot||n.kind==='region'&&/reach/i.test(n.name))continue;const level=n.kind==='region'||n.kind==='galaxy'?'galactic':n.kind==='sector'?'sector':n.kind==='system'?'system':'planet';names.push([level,n.name,n.id]);}}
    for(const [index,item] of names.entries()){if(index)root.append(document.createTextNode(' › '));const button=el('button','link-button',item[1]);button.type='button';button.dataset.mapContext=item[2]||'';button.onclick=()=>{const level=item[0];state.selectedEntity=null;state.mapLevel=level;state.mapNodeId=item[2];$('#map-level').value=level;loadMap();};root.append(button);}}
  function setMapLevel(level){state.selectedEntity=null;state.mapLevel=level;$('#map-level').value=level;const s=liveState();let nodeId=null;if(level==='sector')nodeId=(s?.nodes||[]).find(n=>n.kind==='sector'&&n.knowledge!=='hidden')?.id||null;else if(level==='system')nodeId=(s?.nodes||[]).find(n=>n.kind==='system'&&n.knowledge==='surveyed')?.id||null;else if(level==='planet')nodeId=(s?.nodes||[]).find(n=>n.kind==='planet'&&n.knowledge==='surveyed')?.id||null;state.mapNodeId=nodeId;state.panX=state.panY=0;state.zoom=1;loadMap();}
  function minPlanetZoom(geometry,w,h){return Math.max(w/geometry.planet.width,h/geometry.planet.height)/Math.min(w/geometry.planet.width,h/geometry.planet.height);}
  function centerOnProvince(provinceId){const geometry=state.mapRecord?.geometry;if(!geometry||!provinceId)return;const anchor=window.HWMapRenderer.provinceLand(geometry).get(provinceId)?.anchor;if(!anchor)return;const canvas=$('#planet-map'),w=canvas.parentElement.clientWidth,h=canvas.parentElement.clientHeight,tile=Math.min(w/geometry.planet.width,h/geometry.planet.height)*state.zoom,safe=hierarchySafeRect(canvas.parentElement,w,h),cylinder=window.HWMapRenderer.wrapsX(geometry),anchorX=cylinder?window.HWMapRenderer.nearestX(anchor.x+.5,geometry.planet.width/2,geometry.planet.width):anchor.x+.5;state.panX=geometry.planet.width*tile/2-anchorX*tile+(safe.left+safe.right-w)/2;state.panY=geometry.planet.height*tile/2-(anchor.y+.5)*tile+(safe.top+safe.bottom-h)/2;}
  function zoomPercent(){const canvas=$('#planet-map'),geometry=state.mapRecord?.geometry,minimum=state.mapRecord?.level==='planet'&&geometry?.planet?minPlanetZoom(geometry,canvas.clientWidth,canvas.clientHeight):1;return `${Math.round(state.zoom/minimum*100)}%`;}
  function clampPlanetPan(geometry,w,h){const cols=geometry.planet.width,rows=geometry.planet.height;state.zoom=Math.max(minPlanetZoom(geometry,w,h),state.zoom);const tile=Math.min(w/cols,h/rows)*state.zoom,gridW=tile*cols,gridH=tile*rows,maxX=Math.max(0,(gridW-w)/2),maxY=Math.max(0,(gridH-h)/2);if(window.HWMapRenderer.wrapsX(geometry))state.panX=((state.panX+gridW/2)%gridW+gridW)%gridW-gridW/2;else state.panX=Math.max(-maxX,Math.min(maxX,state.panX));state.panY=Math.max(-maxY,Math.min(maxY,state.panY));}
  function drawMap(){const canvas=$('#planet-map'),ctx=canvas.getContext('2d'),frame=canvas.parentElement,s=liveState(),placeholder=$('#map-placeholder'),overviewButton=$('#map-overview-button');canvas.classList.toggle('is-targeting',Boolean(forceMap?.targeting()));const dpr=window.devicePixelRatio||1;const w=frame.clientWidth,h=frame.clientHeight;canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,w,h);placeholder.hidden=Boolean(s&&state.mapRecord);if(!s||!state.mapRecord){state.transform=null;overviewButton.hidden=true;renderForceMap();return;}
    const theme='light';
    if(state.mapRecord.level!=='planet'){text($('#zoom-reset'),zoomPercent());state.transform=window.HWMapRenderer.drawHierarchy(ctx,{w,h,record:state.mapRecord,safe:hierarchySafeRect(frame,w,h),zoom:state.zoom,panX:state.panX,panY:state.panY,theme:'dark',forceControlRect:hierarchyForceControlRect(frame)});overviewButton.hidden=true;renderForceMap();return;}
    const geometry=state.mapRecord.geometry;if(!geometry){placeholder.hidden=false;state.transform=null;overviewButton.hidden=true;renderForceMap();return;}
    const planetId=state.mapRecord?.selected_planet?.id||state.mapRecord?.parent?.id||geometry.planet.id;
    const safe=hierarchySafeRect(frame,w,h),overviewRect=positionOverview(frame,w,h,safe),labelObstacles=[overviewRect,hierarchyForceControlRect(frame)].filter(Boolean);clampPlanetPan(geometry,w,h);state.transform=window.HWMapRenderer.drawPlanet(ctx,{geometry,w,h,zoom:state.zoom,panX:state.panX,panY:state.panY,style:state.mapStyle,theme,selectedProvince:state.selectedProvince,overlay:state.overlay,compact:w<=780||h<=500,sites:s.settlements||[],planetId,safe,labelObstacles,paintOverlay:state.overlay!=='terrain'&&state.overlay!=='provinces'?(target,{tile,ox,oy})=>drawRecordedOverlay(target,geometry,geometry.tiles,ox,oy,tile,state.mapRecord.records||[],s):null});drawOverview(geometry,dpr);text($('#zoom-reset'),zoomPercent());
    renderForceMap();
  }
  function forceLabel(record) {
    return record?.name || record?.title || `ID …${String(record?.id || 'unknown').slice(-6)}`;
  }
  function renderForceMap() {
    if (!forceMap) return;
    const frame = $('.map-frame'), s = liveState(), record = state.mapRecord, transform = state.transform;
    const positions = {}, forces = [], routes = [];
    const width = frame.clientWidth, height = frame.clientHeight;
    if (s && record && transform) {
      if (record.level === 'planet' && transform.tile) {
        const geo = record.geometry;
        for (const province of geo?.provinces || []) {
          const anchor = window.HWMapRenderer.provinceLand(geo).get(province.id)?.anchor;
          if (anchor) {
            const cylinder=window.HWMapRenderer.wrapsX(geo),ref=(width/2-transform.ox)/transform.tile,worldX=cylinder?window.HWMapRenderer.nearestX(anchor.x+.5,ref,transform.cols):anchor.x+.5;
            positions[`province:${province.id}`] = {x:transform.ox+worldX*transform.tile,y:transform.oy+(anchor.y+.5)*transform.tile,worldX};
          }
        }
        for (const unit of s.units || []) {
          const origin = unit.location_id || unit.origin_province_id;
          if (!origin || unit.planet_id && geo?.provinces?.some(p => p.id === origin) === false) continue;
          const anchor = `province:${origin}`;
          if (!positions[anchor]) continue;
          forces.push({id:unit.id,label:forceLabel(unit),owner:unit.owner,fleet:false,anchor,record:unit,
            canMove:unit.owner==='player'&&!isHistorical()&&!unit.moving_until&&unit.strength>0&&unit.created_turn!==s.turn&&unit.acted_turn!==s.turn});
          if (unit.moving_until && unit.destination_province_id) routes.push({
            from:anchor,to:`province:${unit.destination_province_id}`,
            fromLabel:geo.provinces.find(p=>p.id===origin)?.name||'Recorded province',
            toLabel:geo.provinces.find(p=>p.id===unit.destination_province_id)?.name||'Recorded province',
            label:`Transit · dep ${unit.departure_turn??'—'} · arr ${unit.moving_until}`
          });
        }
      } else if (transform.hierarchy) {
        for (const point of transform.positions || []) positions[point.n.id] = {x:point.x,y:point.y};
      }
      if (record.level !== 'planet') for (const fleet of s.fleets || []) {
        const origin = fleet.system_id || fleet.location_id;
        if (!origin || !positions[origin]) continue;
        forces.push({id:fleet.id,label:forceLabel(fleet),owner:fleet.owner,fleet:true,
          transport:['transport','troop_transport'].includes(fleet.kind),anchor:origin,record:fleet,
          canMove:fleet.owner==='player'&&!isHistorical()&&!fleet.moving_until&&fleet.crew>0&&fleet.created_turn!==s.turn&&fleet.acted_turn!==s.turn});
        if (fleet.moving_until && fleet.destination_system_id) routes.push({
          from:origin,to:fleet.destination_system_id,
          fromLabel:s.nodes?.find(n=>n.id===origin)?.name||'Recorded system',
          toLabel:s.nodes?.find(n=>n.id===fleet.destination_system_id)?.name||'Recorded system',
          label:`Transit · dep ${fleet.departure_turn??'—'} · arr ${fleet.moving_until}`
        });
      }
      const orderText = $('#proposal-json')?.value || '';
      const validated = Boolean(state.previewText && state.previewText === orderText);
      let orderActions = [];
      try {
        const proposal = JSON.parse(orderText);
        orderActions = Array.isArray(proposal?.orders?.actions) ? proposal.orders.actions : [];
      } catch {}
      const addRequest = (action, preview) => {
        const style = preview ? {label:'PREVIEW',preview:true} : {label:'DRAFT',draft:true};
        if (action.type === 'deploy_unit') {
          const unit = (s.units || []).find(item => item.id === action.unit_id);
          const origin = unit && (unit.location_id || unit.origin_province_id);
          if (origin) routes.push({...style,from:`province:${origin}`,to:`province:${action.destination_province_id}`,
            fromLabel:geoName(record, origin),toLabel:geoName(record, action.destination_province_id)});
        } else if (action.type === 'fleet_move') {
          const fleet = (s.fleets || []).find(item => item.id === action.fleet_id);
          if (fleet) routes.push({...style,from:fleet.system_id,to:action.destination_system_id,
            fromLabel:s.nodes?.find(n=>n.id===fleet.system_id)?.name||'Recorded system',
            toLabel:s.nodes?.find(n=>n.id===action.destination_system_id)?.name||'Recorded system'});
        }
      };
      for (const action of movementRequests) addRequest(action, false);
      for (const action of orderActions.filter(item => item && typeof item === 'object' && ['deploy_unit','fleet_move'].includes(item.type))) addRequest(action, validated);
    }
    const count = (s?.units?.length || 0) + (s?.fleets?.length || 0);
    const emptyMessage = count
      ? record?.level === 'planet' ? 'No recorded ground forces appear at this planet.' : 'Select a sector to see recorded fleets, or a planet to see ground forces.'
      : 'No recorded forces in this campaign.';
    if(record?.level==='planet'&&window.HWMapRenderer.wrapsX(record.geometry)){
      const cols=transform.cols,worldW=cols*transform.tile;
      for(const route of routes){const from=positions[route.from],to=positions[route.to];if(!from||!to||!Number.isFinite(from.worldX)||!Number.isFinite(to.worldX))continue;
        const toWorld=window.HWMapRenderer.nearestX(to.worldX,from.worldX,cols),x1=transform.ox+from.worldX*transform.tile,x2=transform.ox+toWorld*transform.tile,y1=from.y,y2=to.y;
        route.segments=[];for(const shift of [-worldW,0,worldW]){const a=x1+shift,b=x2+shift;if(Math.max(a,b)>=0&&Math.min(a,b)<=width)route.segments.push({x1:a,y1,x2:b,y2});}
      }
    }
    forceMap.render({width,height,forces,routes,drafts:[],positions,obstacles:transform?.forceObstacles||[],emptyMessage,
      clipToViewport:record?.level==='planet'&&window.HWMapRenderer.wrapsX(record.geometry),
      onSelectForce:item=>{state.selectedEntity=item.record;renderInspector(liveState(),state.campaign);window.HWDesktop?.open('inspector');},
      onMove:item=>{movementIntent=item;window.HWDesktop?.open('orders');renderOrders();$('#orders-panel').dataset.ready='true';},
      onCancelTarget:()=>{movementIntent=null;window.HWDesktop?.open('orders');renderOrders();}
    });
  }
  function geoName(record, id) {
    return record?.geometry?.provinces?.find(province => province.id === id)?.name || 'Recorded province';
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
      const land=tiles.filter(t=>t.province_id===province.id&&t.terrain!=='ocean');
      if(!land.length)continue;
      const px=province.x+province.width/2,py=province.y+province.height/2,
        anchor=land.reduce((a,t)=>Math.hypot(t.x+.5-px,t.y+.5-py)<Math.hypot(a.x+.5-px,a.y+.5-py)?t:a,land[0]),
        cx=ox+(anchor.x+.5)*tile,cy=oy+(anchor.y+.5)*tile;
      if(state.overlay==='infrastructure'&&(hasFacilities||knownEmptyInfrastructure)){const count=hasFacilities?record.facilities.length:0;ctx.fillStyle='#343b3d';ctx.fillRect(cx-7,cy-7,14,14);ctx.fillStyle='#f7f8f4';ctx.fillRect(cx-4,cy-4,Math.max(3,Math.min(8,count*2)),8);if(tile>10){ctx.fillStyle='#fff';ctx.font='8px monospace';ctx.textAlign='center';ctx.fillText(String(count),cx,cy+13);}}
      if(state.overlay==='military'&&units.length){
        units.slice(0,5).forEach((unit,index)=>{
          const x=cx+(index-(Math.min(units.length,5)-1)/2)*18,y=cy;
          ctx.beginPath();
          if(unit.owner==='player')ctx.rect(x-6,y-6,12,12);
          else if(unit.owner==='foreign'){ctx.moveTo(x,y-8);ctx.lineTo(x+8,y);ctx.lineTo(x,y+8);ctx.lineTo(x-8,y);ctx.closePath();}
          else ctx.arc(x,y,6,0,Math.PI*2);
          ctx.fillStyle=unit.owner==='player'?'#0088ff':unit.owner==='foreign'?'#e2e5e5':'#b8c5c3';
          ctx.strokeStyle='#f4f6e8';ctx.lineWidth=3;ctx.stroke();ctx.fill();
        });
        if(units.length>5){ctx.font='700 11px monospace';ctx.textAlign='center';ctx.lineWidth=3;ctx.strokeStyle='#18323d';ctx.strokeText(`${units.length} recorded`,cx,cy+24);ctx.fillStyle='#f4f6e8';ctx.fillText(`${units.length} recorded`,cx,cy+24);}
      }
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
  function hierarchyForceControlRect(frame){
    const node=frame.querySelector('.force-map-controls');if(!node||!node.getClientRects().length)return null;
    const frameRect=frame.getBoundingClientRect(),rect=node.getBoundingClientRect();
    return{left:rect.left-frameRect.left,top:rect.top-frameRect.top,right:rect.right-frameRect.left,bottom:rect.bottom-frameRect.top};
  }
  function renderMapLegend(){
    const root=$('#map-legend');root.replaceChildren();if(!state.mapRecord)return;let entries;
    const unknown='repeating-linear-gradient(135deg,#343b3d 0 1.5px,#f1f2ee 1.5px 4px)';
    if(state.mapLevel!=='planet')entries=[['#626a6c',state.mapLevel==='galactic'?'Known sectors':state.mapLevel==='sector'?'Known systems':'Recorded bodies']];
    else if(state.overlay==='terrain'){
      const preset=state.mapRecord.geometry?.surface?.preset;
      entries=preset==='arid'?[['plains','Dry plains'],['rock','Rocklands']]:preset==='barren'?[['rock','Exposed rock']]:preset==='frozen'?[['plains','Ice field'],['rock','Frozen rock']]:[['ocean','Open water'],['coast','Coastal shelf'],['plains','Plains'],['rock','Rocklands'],['forest','Forest'],['marsh','Marsh']];
    }
    else if(state.overlay==='population')entries=[['#555d5f','Recorded residents'],['#e4e6e2','Recorded zero'],[unknown,'Unknown / unrecorded']];
    else if(state.overlay==='infrastructure')entries=[['#343b3d','Recorded facilities'],['#d7dad6','Owned site · none recorded'],[unknown,'Unknown / unrecorded']];
    else if(state.overlay==='military')entries=[['#0088ff','Owned forces'],['#e2e5e5','Observed foreign forces'],['#b8c5c3','Owner unknown'],[unknown,'No current observation']];
    else if(state.overlay==='politics')entries=[['#555d5f','Recorded unrest'],[unknown,'Unknown / unrecorded']];
    else entries=[['#91a39a','Recorded province areas'],['#a9c3c7','Open water']];
    const preset=state.mapRecord?.geometry?.surface?.preset;
    for(const [key,label]of entries){const item=el('span','legend-key');const sw=el('i','swatch');sw.style.background=window.HWMapRenderer.terrainColor(state.mapStyle,key,preset)||key;if(state.overlay==='military'){sw.style.outline='1px solid #f4f6e8';if(key==='#e2e5e5')sw.style.transform='rotate(45deg)';if(key==='#b8c5c3')sw.style.borderRadius='50%';}item.append(sw,document.createTextNode(label));root.append(item);}
  }
  function canvasPoint(event){const r=$('#planet-map').getBoundingClientRect();return{x:event.clientX-r.left,y:event.clientY-r.top};}
  function provinceLabelAt(point){
    return (state.transform?.provinceTargets||[]).find(target=>point.x>=target.left&&point.x<=target.right&&point.y>=target.top&&point.y<=target.bottom)||null;
  }
  function provinceTileAt(point){const target=provinceLabelAt(point);return target?state.mapRecord?.geometry?.tiles[target.anchor.y*state.transform.cols+target.anchor.x]||null:tileAt(point);}
  function tileAt(point){const t=state.transform;if(!t||t.hierarchy)return null;let x=Math.floor((point.x-t.ox)/t.tile);const y=Math.floor((point.y-t.oy)/t.tile),cylinder=window.HWMapRenderer.wrapsX(state.mapRecord?.geometry);if(cylinder)x=((x%t.cols)+t.cols)%t.cols;else if(x<0||x>=t.cols)return null;if(y<0||y>=t.rows)return null;return state.mapRecord?.geometry?.tiles[y*t.cols+x]||null;}

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
        const outcome=s.latest_outcome,production=outcome?.production?.[settlement.id],consumption=outcome?.consumption?.[settlement.id];
        const localDeaths=settlement.owned!==false&&Array.isArray(outcome?.deaths)?outcome.deaths.filter(x=>x.settlement_id===settlement.id):null;
        const deaths=localDeaths&&localDeaths.every(x=>Number.isFinite(x.count)&&x.count>=0)?localDeaths.reduce((sum,x)=>sum+x.count,0):null;
        const budget=s.latest_budget,unmet=settlement.owned===false?null:budget?.unmet_upkeep?.[settlement.id];
        const producedFood=Number.isFinite(production?.food)&&production.food>=0?production.food:null,consumedFood=Number.isFinite(consumption?.food)&&consumption.food>=0?consumption.food:null;
        const foodFlow=producedFood!==null&&consumedFood!==null?producedFood-consumedFood:null;
        const constraints=[];
        for(const [key,label,unit] of [['energy','Unmet energy upkeep','energy'],['credits','Unmet credit upkeep','credits'],['welfare','Unmet welfare','credits']]){
          if(Number.isFinite(unmet?.[key])&&unmet[key]>0)constraints.push(`${label}: ${fmt(unmet[key])} ${unit}`);
        }
        if(deaths>0)constraints.push(`Local deaths recorded: ${fmt(deaths)} people`);
        if(foodFlow!==null&&foodFlow<0)constraints.push(`Food flow: ${fmt(foodFlow)} units (production − consumption)`);
        if(constraints.length){const recorded=el('section','economy-recorded-condition');recorded.append(el('div','inspector-section','RECORDED CONSTRAINTS'));for(const constraint of constraints)recorded.append(el('div','recorded-constraint',constraint));group.append(recorded);}
        const turnDetails=el('details','record-identifiers economy-turn-details');turnDetails.append(el('summary','','Turn records & food flow'));
        if(settlement.owned===false)group.append(el('p','condition-limit','Foreign settlement budget and numerical baseline are unavailable.'));
        else if(!budget||!budget.unmet_upkeep)turnDetails.append(el('p','condition-limit','Local upkeep records are unavailable for this baseline.'));
        else if(!unmet||Object.keys(unmet).length===0)turnDetails.append(el('p','condition-limit','No unmet upkeep entries are recorded for this settlement.'));
        else for(const [key,value] of Object.entries(unmet))row(turnDetails,`Unmet ${titleCase(key)}`,fmt(value));
        row(turnDetails,'Local deaths recorded',deaths===null?'Unavailable':`${fmt(deaths)} people`);
        if(producedFood!==null||consumedFood!==null)turnDetails.append(resourceFlowChart(producedFood,consumedFood));
        else turnDetails.append(el('p','condition-limit','Local food production and consumption are unavailable.'));
        if(foodFlow!==null)turnDetails.append(el('div','food-flow-balance',`Food flow · ${foodFlow>0?'+':''}${fmt(foodFlow)} units · production − consumption`));
        turnDetails.append(el('p','condition-limit','Deaths count only this settlement; cause is unrecorded. Food flow is not a stock balance.'));
        group.append(turnDetails,el('p','condition-limit','Economic diagnosis and forecasts are unrecorded.'));
        const vitalGrid=el('dl','local-vital-grid');
        for(const [label,value] of [
          ['Local population',settlement.local_population],['Civilians',settlement.civilians],['Local crew',settlement.local_crew],
          ['Local soldiers',settlement.local_soldiers],['Housing',settlement.housing],['Unrest',settlement.unrest]
        ]){
          if(value===undefined)continue;
          const vital=el('div',`local-vital${label==='Local population'?' local-vital-primary':''}`);vital.append(el('dt','',label),el('dd','',value==null?'Unknown':fmt(value)));vitalGrid.append(vital);
        }
        group.append(vitalGrid);
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
    rows.forEach(([label,value,color],i)=>{const y=20+i*38;const name=document.createElementNS(svg.namespaceURI,'text');name.setAttribute('x','0');name.setAttribute('y',String(y+12));name.setAttribute('fill','var(--ink)');name.setAttribute('font-size','15');name.textContent=label;svg.append(name);const track=document.createElementNS(svg.namespaceURI,'rect');track.setAttribute('x','128');track.setAttribute('y',String(y));track.setAttribute('width','210');track.setAttribute('height','14');track.setAttribute('fill','var(--paper-deep)');svg.append(track);if(value!==null){const bar=document.createElementNS(svg.namespaceURI,'rect');bar.setAttribute('x','128');bar.setAttribute('y',String(y));bar.setAttribute('width',String(Math.max(value>0?1:0,210*value/max)));bar.setAttribute('height','14');bar.setAttribute('fill',color);svg.append(bar);}const valueText=document.createElementNS(svg.namespaceURI,'text');valueText.setAttribute('x','350');valueText.setAttribute('y',String(y+12));valueText.setAttribute('fill','var(--ink)');valueText.setAttribute('font-size','15');valueText.textContent=value===null?'Unknown':fmt(value);svg.append(valueText);});box.append(svg);return box;
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
    if(!valid.length)return null;
    const vals=valid.map(item=>item.metrics[metric]),peak=Math.max(1,...vals);
    const magnitude=10**Math.floor(Math.log10(peak/4));
    const tickStep=[1,2,5,10].find(step=>step*magnitude>=peak/4)*magnitude,max=tickStep*4;
    const graph=el('div','recorded-history-chart');
    const unit=historyMetricUnit(metric),first=valid[0],last=valid.at(-1),delta=last.metrics[metric]-first.metrics[metric];
    if(valid.length===1){graph.append(el('div','history-range-summary',`${titleCase(metric.replaceAll('_',' '))} · Turn ${first.turn}: ${fmt(first.metrics[metric])} ${unit}`),el('p','chart-note','One recorded value. A second record is needed to show change.'));return graph;}
    graph.append(el('div','history-range-summary',`${titleCase(metric.replaceAll('_',' '))} · ${unit} · Turn ${first.turn}: ${fmt(first.metrics[metric])} → Turn ${last.turn}: ${fmt(last.metrics[metric])} · Net change ${delta>0?'+':''}${fmt(delta)} ${unit}`));
    if(comparison){const a=items.find(x=>x.turn===comparison[0]),b=items.find(x=>x.turn===comparison[1]);if(a&&b&&a.turn!==b.turn&&Number.isFinite(a.metrics?.[metric])&&Number.isFinite(b.metrics?.[metric])){const change=b.metrics[metric]-a.metrics[metric];graph.append(el('div','history-comparison',`Turn ${a.turn} → Turn ${b.turn} · ${fmt(a.metrics[metric])} → ${fmt(b.metrics[metric])} ${unit} · Signed change ${change>0?'+':''}${fmt(change)} ${unit}`));}}
    const plot=el('div','history-plot-grid'),axis=el('div','history-value-axis');axis.style.minWidth=`${Math.max(4,...Array.from({length:5},(_,y)=>fmt(max-y*tickStep).length))}ch`;axis.setAttribute('aria-hidden','true');
    const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
    svg.setAttribute('viewBox','0 0 640 144');svg.setAttribute('preserveAspectRatio','none');svg.setAttribute('role','img');svg.setAttribute('aria-label',`Recorded ${titleCase(metric.replaceAll('_',' '))} history, turns ${valid[0].turn} to ${valid.at(-1).turn}, scale 0 to ${fmt(max)}`);svg.dataset.metric=metric;
    for(let y=0;y<=4;y++){
      const label=el('span','',fmt(max-y*tickStep));label.style.top=`${y*25}%`;axis.append(label);
      const line=document.createElementNS(svg.namespaceURI,'line');
      line.setAttribute('x1','0');line.setAttribute('x2','640');line.setAttribute('y1',String(y*36));line.setAttribute('y2',String(y*36));line.setAttribute('stroke','var(--line)');line.setAttribute('vector-effect','non-scaling-stroke');svg.append(line);
    }
    const color=metric==='food'?'var(--apple-system-mint-contrast)':metric==='energy'?'var(--apple-system-blue-contrast)':metric==='ore'?'var(--apple-system-indigo-contrast)':'var(--ink)';
    const points=valid.map((item,i)=>`${i*640/(valid.length-1)},${144-(item.metrics[metric]/max)*144}`).join(' ');
    const poly=document.createElementNS(svg.namespaceURI,'polyline');
    poly.setAttribute('points',points);poly.setAttribute('fill','none');poly.setAttribute('stroke',color);poly.setAttribute('stroke-width','2');poly.setAttribute('vector-effect','non-scaling-stroke');svg.append(poly);
    const turns=el('div','history-turn-axis');turns.append(el('span','',`Turn ${valid[0].turn}`),el('span','',`Turn ${valid.at(-1).turn}`));
    plot.append(axis,svg,turns);graph.append(plot);return graph;
  }
  function historyMetricUnit(metric){return ['population','military_personnel'].includes(metric)?'people':metric==='military'?'units and fleets':metric==='projects'||metric==='research'||metric==='territories'||metric==='facilities'?'records':metric.includes('revenue')||metric.includes('spending')||['treasury','credits'].includes(metric)?'credits':metric==='food_produced'||metric==='food_consumed'?'food units':metric==='energy_consumed'?'energy units':metric==='energy_produced'?'energy units':metric==='food'||metric==='ore'||metric==='energy'||metric==='metals'||metric==='materiel'||metric==='promethium'||metric==='data'?'stock units':'recorded count';}

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
  const reportAliases={industry:['economy','construction'],fleet:['military'],politics:['diplomacy','overview'],trade:['logistics','diplomacy'],factions:['diplomacy']};
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
    }else {
      const introductions={industry:'Settlement production, followed by recorded facilities and projects.',politics:'Contacted factions and treaties, followed by the related settlement and turn overview.',trade:'Shipments and depot facilities, followed by contacted factions and treaties.',research:'Completed technologies and recorded research projects.',exploration:'Recorded exploration missions and discoveries.',logistics:'Recorded shipments and depot facilities.'};
      if(introductions[view])panel.append(el('p','view-sub management-intro',introductions[view]));
      for(let i=0;i<records.length;i++){const data=records[i].records;if(sections[i]!==view)panel.append(el('div','inspector-section',titleCase(sections[i])));renderRecord(panel,data,view,sections[i]);}
    }
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
        const item=el('div','local-record-row');const heading=el('strong','',titleCase(facility.kind||'Facility'));const status=el('span',`local-record-status${facility.completed===true?' is-complete':facility.completed===false?' is-in-progress':''}`,facility.completed===true?'Complete':facility.completed===false?'In progress':'Status unknown');item.append(heading,status);
        const details=el('details','record-identifiers');details.append(el('summary','','Record IDs'));row(details,'Facility',facility.id);row(details,'Settlement',settlement.id);item.append(details);group.append(item);
      }
      const localProjects=projects.filter(x=>x.settlement_id===settlement.id);
      if(localProjects.length){group.append(el('div','inspector-section','PROJECTS'));for(const project of localProjects){const item=el('div','local-record-row');const heading=el('strong','',project.facility_kind?`${titleCase(project.facility_kind)} construction`:titleCase(project.kind||project.name||'Construction project'));item.append(heading);if(Number.isFinite(project.work_done)&&Number.isFinite(project.work_required)&&project.work_required>0&&project.work_done>=0&&project.work_done<=project.work_required){const progress=el('div','project-progress local-project-progress');const bar=document.createElement('progress');bar.max=project.work_required;bar.value=project.work_done;bar.setAttribute('aria-label',`Project work ${fmt(project.work_done)} of ${fmt(project.work_required)}`);progress.append(el('span','','WORK'),bar,el('strong','',`${fmt(project.work_done)} / ${fmt(project.work_required)}`));item.append(progress);}else item.append(el('div','view-sub local-project-progress-unknown','Work progress is not recorded.'));const details=el('details','record-identifiers');details.append(el('summary','','Record IDs'));row(details,'Project',project.id);row(details,'Settlement',settlement.id);item.append(details);group.append(item);}}
      panel.append(group);
    }
    if(!facilities.length&&!projects.length)panel.append(el('div','empty-note','No facilities or projects are recorded for the matching settlement IDs.'));
  }
  function safeValue(value){if(value===null||value===undefined)return 'Unknown';if(typeof value==='boolean')return value?'Yes':'No';if(typeof value==='object')return JSON.stringify(value);return String(value);}
  function settlementLabel(id){const s=liveState()?.settlements?.find(item=>item.id===id);return s?.name||resolveRecordReference(id);}
  function renderSettlementBreakdown(root,heading,records,units={}){
    if(!records||typeof records!=='object'||Array.isArray(records))return false;
    const group=el('section','report-group');group.append(el('h3','report-group-title',heading));let count=0;
    for(const [id,values] of Object.entries(records)){if(!values||typeof values!=='object'||Array.isArray(values))continue;const block=el('div','settlement-breakdown');block.append(el('h4','settlement-breakdown-title',settlementLabel(id)));const dl=el('dl','settlement-breakdown-facts');
      for(const [key,value] of Object.entries(values)){if(value===null||value===undefined||typeof value==='object')continue;dl.append(el('dt','',titleCase(key.replaceAll('_',' '))),el('dd','',`${safeValue(value)}${units[key]?' '+units[key]:''}`));count++;}
      if(dl.childElementCount){block.append(dl);group.append(block);}
    }
    if(count)root.append(group);return count>0;
  }
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
    if(!items.length){const empty={technologies:'No completed technologies are recorded.',missions:'No exploration missions are recorded.',discoveries:'No discoveries are recorded.',shipments:'No shipments are recorded.',depots:'No depot facilities are recorded.'};const message=section==='projects'?(view==='research'?'No research projects are recorded.':'No construction projects are recorded.'):empty[section]||'No records are available for this view.';root.append(el('div','empty-note',message));return;}
    const visible=['kind','type','role','assignment','owner','contacted','status','location_id','system_id','planet_id','settlement_id','strength','crew','readiness','capacity','food_reserve','promethium_reserve','work_done','work_required','completed','experience','population','turn'];
    const relation=/^(location|system|planet|settlement)_id$/;
    for(const item of items){
      if(!item||typeof item!=='object'){root.append(el('div','record-summary',safeValue(item)));continue;}
      const forces=['military','fleet'].includes(view)||['units','fleets'].includes(section);
      const card=el('article',`record-summary${forces?' force-record':''}`);
      const recordLabel=section==='projects'&&item.facility_kind?`${titleCase(item.facility_kind)} construction`:recordTitle(item);
      const heading=el('header','force-record-head');const title=el('h3','record-summary-title',recordLabel);if(forces){const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('class','command-icon');svg.setAttribute('viewBox','0 0 24 24');svg.setAttribute('aria-hidden','true');const path=document.createElementNS(svg.namespaceURI,'path');const fleetRecord=section==='fleets'||(section!=='units'&&['fleet','transport'].includes(item.kind));path.setAttribute('d',fleetRecord?'M2 15h20l-3 5H6zM5 12h14M8 9h8M11 3h2v9':'M12 3 20 7v5c0 5-4 8-8 10-4-2-8-5-8-10V7z');svg.append(path);title.replaceChildren(svg,document.createTextNode(` ${recordLabel}`));const ownerLabel=item.owner==='player'?'PLAYER':item.owner==='foreign'?'FOREIGN':item.owner!==undefined&&item.owner!==null?`OWNER ${safeValue(item.owner).toUpperCase()}`:'OWNER UNKNOWN';title.append(el('span',`force-owner-tag${item.owner==='player'?' is-player':item.owner==='foreign'?' is-foreign':''}`,ownerLabel));}heading.append(title);
      const locationKey=['location_id','system_id','planet_id','settlement_id'].find(key=>item[key]!==undefined&&item[key]!==null);
      if(forces){
        const identityParts=[item.status&&titleCase(safeValue(item.status)),locationKey&&resolveRecordReference(item[locationKey])];
        if(item.owner==='foreign'){
          if(Number.isFinite(item.observed_turn))identityParts.push(`Observed turn ${fmt(item.observed_turn)}`);
          if(item.confidence!==undefined&&item.confidence!==null)identityParts.push(`${titleCase(safeValue(item.confidence))} confidence`);
        }
        const identity=identityParts.filter(Boolean).join(' · ');if(identity)heading.append(el('span','force-identity',identity));
      }
      card.append(heading);
      const facts=el('dl','record-facts');let shown=0;
      const fleetRecord=forces&&(section==='fleets'||(section!=='units'&&['fleet','transport'].includes(item.kind)));
      const primaryKeys=forces?['strength','crew','readiness','food_reserve','promethium_reserve']:[];
      const fieldOrder=forces?[...primaryKeys,...visible.filter(key=>!primaryKeys.includes(key))]:visible;
      if(forces){
        for(const [key,label] of [['strength',fleetRecord?'Strength':'Ground strength'],['crew',fleetRecord?'Fleet crew':'Crew'],['readiness','Readiness']]){
          const fact=el('div',`record-fact force-primary fact-${key}`),value=item[key];
          const recorded=Number.isFinite(value)&&value>=0&&(key!=='readiness'||value<=100);
          fact.classList.toggle('is-unknown',!recorded);
          fact.append(el('dt','',label),el('dd','',recorded?`${safeValue(value)}${key==='readiness'?'%':''}`:'Unknown'));
          if(key==='readiness'&&Number.isFinite(value)&&value>=0&&value<=100){const gauge=document.createElement('progress');gauge.max=100;gauge.value=value;gauge.setAttribute('aria-label',`Readiness ${value}%`);fact.append(gauge);}
          facts.append(fact);
        }
        const supply=el('div','record-fact force-secondary fact-supplies');supply.append(el('dt','','Supplies'));
        const readings=el('dd');for(const [label,value] of [['Food',item.food_reserve],['Promethium',item.promethium_reserve]])readings.append(el('div','',`${label}: ${value===undefined||value===null?'Unknown':safeValue(value)}`));
        supply.append(readings);facts.append(supply);shown+=4;
      }
      for(const key of fieldOrder){if(!(key in item)||forces&&primaryKeys.includes(key)||key==='kind'&&recordTitle(item)===titleCase(item.kind)||forces&&(['owner','status'].includes(key)||key===locationKey))continue;
        if(item[key]===null||item[key]===undefined)continue;
        const value=relation.test(key)?resolveRecordReference(item[key]):key==='readiness'&&Number.isFinite(item[key])?`${safeValue(item[key])}%`:(['kind','type','role','owner','status','assignment'].includes(key)?titleCase(safeValue(item[key])):safeValue(item[key]));
        const fact=el('div',`record-fact fact-${key}`);fact.append(el('dt','',titleCase(key.replace(/_id$/,''))),el('dd','',value));if(key==='readiness'&&Number.isFinite(item.readiness)&&item.readiness>=0&&item.readiness<=100){const gauge=document.createElement('progress');gauge.max=100;gauge.value=item.readiness;gauge.setAttribute('aria-label',`Readiness ${item.readiness}%`);fact.append(gauge);}if(['strength','crew','readiness'].includes(key))fact.classList.add('force-primary');if(['food_reserve','promethium_reserve','capacity','location_id','system_id','planet_id','settlement_id'].includes(key))fact.classList.add('force-secondary');facts.append(fact);shown++;
      }
      if(section==='projects'){
        if(Number.isFinite(item.work_done)&&Number.isFinite(item.work_required)&&item.work_required>0&&item.work_done>=0&&item.work_done<=item.work_required){const progress=el('div','project-progress');const bar=document.createElement('progress');bar.max=item.work_required;bar.value=item.work_done;bar.setAttribute('aria-label',`Project work ${fmt(item.work_done)} of ${fmt(item.work_required)}`);progress.append(el('span','','WORK'),bar,el('strong','',`${fmt(item.work_done)} / ${fmt(item.work_required)}`));card.append(progress);}
        else card.append(el('div','view-sub project-progress-unknown','Work progress not recorded.'));
      }
      if(shown)card.append(facts);
      if(section==='factions'&&Array.isArray(item.treaties)){const treaties=el('div','faction-treaties');treaties.append(el('div','inspector-section','TREATIES'));if(item.treaties.length){for(const treaty of item.treaties){const facts=[titleCase(treaty.kind||'Treaty'),titleCase(treaty.status||'Status unknown')];if(treaty.proposed_turn!==undefined)facts.push(`Proposed turn ${safeValue(treaty.proposed_turn)}`);if(treaty.accepted_by_gm!==undefined)facts.push(`GM accepted ${safeValue(treaty.accepted_by_gm)}`);if(treaty.accepted_turn!==undefined)facts.push(`Accepted turn ${safeValue(treaty.accepted_turn)}`);treaties.append(el('p','view-sub',facts.join(' · ')));}}else treaties.append(el('p','view-sub','No treaties recorded.'));card.append(treaties);}
      if(item.id){const inspect=el('button','link-button entity-select','Inspect record');inspect.type='button';inspect.onclick=()=>selectEntity(item);card.append(inspect);}
      const details=el('details','record-identifiers');details.append(el('summary','','All recorded fields'));
      for(const [key,value] of Object.entries(item))row(details,titleCase(key),safeValue(value));
      card.append(details);root.append(card);
    }
  }
  function renderRecord(root,data,view,section=view){
    if(data===null||data===undefined){root.append(el('div','empty-note','No recorded values for this turn; unknown values are not zero.'));return;}
    if(Array.isArray(data)){renderRecordCards(root,data,view,section);return;}
    if(typeof data!=='object'){row(root,'Value',safeValue(data));return;}
    let entries=Object.entries(data);if(!entries.length){root.append(el('div','empty-note','No recorded values.'));return;}
    if(view==='fleet')entries.sort(([a],[b])=>(a==='fleets'?-1:0)-(b==='fleets'?-1:0));
    if(view==='industry'&&section==='economy')entries.sort(([a],[b])=>(a==='production'?-1:0)-(b==='production'?-1:0));
    for(const [key,value] of entries){if(Array.isArray(value)){if(titleCase(key)!==titleCase(view))root.append(el('div','inspector-section',titleCase(key)));renderRecordCards(root,value,view,key);}
      else if(value&&typeof value==='object'){
        if(section==='economy'&&key==='production'&&renderSettlementBreakdown(root,'PRODUCTION BY SETTLEMENT',value,{food:'units',ore:'units',energy:'units',metals:'units',promethium:'units',materiel:'units',data:'units'}))continue;
        if(section==='budget'&&key==='spending'&&renderSettlementBreakdown(root,'RECORDED SETTLEMENT SPENDING',value,{upkeep_energy:'energy',upkeep_credits:'credits',welfare:'credits'}))continue;
        if(section==='budget'&&key==='unmet_upkeep'&&Object.keys(value).length===0){root.append(el('div','empty-note','No unmet upkeep entries are recorded.'));continue;}
        const box=el('div','report-group');box.append(el('div','report-group-title',titleCase(key)));for(const [sub,val]of Object.entries(value)){if(Array.isArray(val)){box.append(el('div','inspector-section',titleCase(sub)));renderTable(box,val,true);}else row(box,titleCase(sub),safeValue(val));}
        if(key==='outcome'){const details=el('details','record-identifiers');details.append(el('summary','','Recorded turn details'),box);root.append(details);}else root.append(box);
      }
      else {const creditFields=['opening_credits','tax_revenue','trade_revenue','action_credit_spending','trade_spending','closing_credits'];const shown=section==='budget'&&creditFields.includes(key)&&Number.isFinite(value)?`${safeValue(value)} credits`:safeValue(value);row(root,titleCase(key),shown);}}
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
    const root=$('#orders-panel'),priorText=$('#proposal-json')?.value||'',priorOpen=$('#proposal-json')?.closest('details')?.open||false,priorToken=$('#gm-token')?.value;root.replaceChildren();
    if(!state.campaign||state.campaign.kind!=='demo'){root.append(el('div','note-box','This pre-game campaign has no numeric rules baseline. Decision packets and turn submission are disabled.'));return;}
    if(isHistorical()){root.append(el('div','note-box','Return to the live campaign revision before preparing an order packet.'));return;}
    const grid=el('div','orders-grid'),left=el('div');
    const status=el('div','order-status');status.id='order-status';status.setAttribute('role','status');
    status.textContent=state.previewText?'Preview validated · Review the backend response before commit.':'No proposal loaded · Export a packet or load an example.';left.append(status);
    const actions=el('div','orders-actions');const packet=el('button','button','Export decision packet');packet.onclick=exportPacket;const example=el('button','button','Load example proposal');example.onclick=loadExample;actions.append(packet,example);left.append(actions);
    const source=el('details','order-source');source.append(el('summary','','Token and proposal JSON'));
    const token=el('div','form-row'),tokenLabel=el('label','','GM token · kept in page memory');tokenLabel.htmlFor='gm-token';token.append(tokenLabel);
    const input=el('input');input.type='password';input.id='gm-token';input.autocomplete='off';input.value=priorToken??state.gmToken;input.placeholder='Set WOLD_GM_TOKEN on the server';input.oninput=()=>state.gmToken=input.value;token.append(input);source.append(token);
    const file=el('div','form-row'),fileLabel=el('label','','Import proposal file');fileLabel.htmlFor='proposal-file';file.append(fileLabel);
    const upload=el('input');upload.type='file';upload.id='proposal-file';upload.accept='application/json,.json';upload.onchange=async()=>{const fileRef=upload.files[0],epoch=state.contextEpoch,area=$('#proposal-json');if(!fileRef||!area)return;const value=await fileRef.text();if(epoch!==state.contextEpoch||!area.isConnected||area!==$('#proposal-json'))return;area.value=value;area.closest('details').open=true;invalidatePreview();};file.append(upload);source.append(file);
    const proposal=el('div','form-row'),proposalLabel=el('label','','Proposal JSON');proposalLabel.htmlFor='proposal-json';proposal.append(proposalLabel);
    const area=el('textarea');area.id='proposal-json';area.spellcheck=false;area.placeholder='Paste a proposal, or load an example.';area.value=priorText;area.oninput=invalidatePreview;proposal.append(area);source.open=priorOpen||Boolean(priorText);source.append(proposal);left.append(source);
    const buttons=el('div','orders-actions'),preview=el('button','button','Preview');preview.id='preview-order';preview.onclick=previewOrder;
    const commit=el('button','button','Commit validated turn');commit.id='commit-order';commit.disabled=!state.previewText||state.previewText!==area.value;commit.onclick=commitOrder;buttons.append(preview,commit);left.append(buttons);
    const right=el('div');const box=el('div','gm-explainer','Export the current packet, load or paste its returned JSON, then preview the backend calculation. Commit only after reviewing it. Editing the proposal invalidates its preview.');
    right.append(box,el('div','inspector-section','BACKEND RESPONSE'),Object.assign(el('pre','result-box'),{id:'order-result',textContent:'No request yet.'}));grid.append(left,right);root.append(grid);
    renderMovementOrders(root);
  }
  function renderMovementOrders(root) {
    const panel=el('section','movement-orders');
    panel.append(el('h3','','Recorded movement'));
    if(movementIntent) {
      panel.append(el('p','view-sub',`Choose a destination for ${movementIntent.label}. Click the map or use the destination list.`));
      const form=el('div','movement-form'),destinations=el('select'),s=liveState();
      destinations.setAttribute('aria-label',movementIntent.fleet?'Destination system':'Destination province');
      destinations.append(new Option('Choose destination…',''));
      if(movementIntent.fleet) {
        const edges=s?.links||[],id=movementIntent.record.system_id;
        const neighborIds=edges.filter(edge=>edge.a===id||edge.b===id).map(edge=>edge.a===id?edge.b:edge.a);
        for(const node of s?.nodes||[])if(node.kind==='system'&&node.knowledge!=='hidden'&&neighborIds.includes(node.id))destinations.append(new Option(node.name,node.id));
      } else {
        const provinces=state.mapRecord?.geometry?.provinces||[];
        const allProvinces=provinces.length?provinces:(s?.provinces||[]);
        for(const province of allProvinces)if(province.id!==movementIntent.record.location_id)destinations.append(new Option(province.name||`ID …${String(province.id).slice(-6)}`,province.id));
      }
      const sources=el('select');sources.setAttribute('aria-label','Supply source');
      sources.append(new Option(movementIntent.fleet?'No settlement source':'Choose owned depot source',movementIntent.fleet?'__none':''));
      const unit=movementIntent.record;
      for(const site of s?.settlements||[]) {
        if(!site.owned)continue;
        if(movementIntent.fleet) {
          const planetIds=(s.nodes||[]).filter(node=>node.kind==='planet'&&node.parent_id===unit.system_id).map(node=>node.id);
          if(!planetIds.includes(site.planet_id))continue;
        } else {
          if(site.planet_id!==unit.planet_id)continue;
          const depots=(s.facilities||[]).filter(f=>f.settlement_id===site.id&&f.kind==='depot'&&(f.active_turn||0)<=s.turn);
          if(!depots.length)continue;
        }
        sources.append(new Option(site.name,site.id));
      }
      form.append(destinations,sources);
      const target=el('button','button','Target on map');
      target.onclick=()=>{movementIntent.destinationSelect=destinations;movementIntent.sourceSelect=sources;forceMap?.beginTarget(movementIntent);window.HWDesktop?.returnMap();};
      const stage=el('button','button','Stage movement');
      stage.onclick=()=>{if(!destinations.value){notify('Choose a recorded destination.',true);return;}if(!movementIntent.fleet&&!sources.value){notify('Choose an owned settlement with a recorded active depot.',true);return;}stageMovement(movementIntent,destinations.value,sources.value==='__none'?null:(sources.value||null));};
      const cancel=el('button','button small','Cancel');
      cancel.onclick=()=>{movementIntent=null;forceMap?.cancelTarget();renderOrders();};
      form.append(target,stage,cancel);panel.append(form);
    }
    if(movementRequests.length) {
      panel.append(el('p','view-sub',`${movementRequests.length} movement request${movementRequests.length===1?'':'s'} staged in memory.`));
      const list=el('ul','movement-request-list'),s=liveState();
      for(const [index,item] of movementRequests.entries()) {
        const isFleet=item.type==='fleet_move',actorId=isFleet?item.fleet_id:item.unit_id;
        const actor=(isFleet?s?.fleets:s?.units)?.find(force=>force.id===actorId);
        const targetId=item.destination_system_id||item.destination_province_id;
        const target=isFleet?s?.nodes?.find(node=>node.id===targetId):state.mapRecord?.geometry?.provinces?.find(province=>province.id===targetId);
        const source=s?.settlements?.find(site=>site.id===item.source_id);
        const li=el('li',''),description=el('span','movement-request-label');
        description.textContent=`${forceLabel(actor||{id:actorId})} → ${target?.name||`Recorded destination · ID …${String(targetId).slice(-6)}`}${source?` · source ${source.name}`:''}`;
        description.title=`${isFleet?'Fleet':'Ground'} · force ${actorId} · destination ${targetId}${item.source_id?` · source ${item.source_id}`:''}`;
        const remove=el('button','button small','Remove');
        li.append(description,remove);remove.onclick=()=>{movementRequests.splice(index,1);renderMovementOrders(root);renderForceMap();};list.append(li);
      }
      panel.append(list);
      const exportButton=el('button','button','Export movement requests');
      exportButton.onclick=()=>{const blob=new Blob([JSON.stringify({requests:movementRequests},null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`${state.campaignId}-movement-requests.json`;a.click();URL.revokeObjectURL(a.href);};
      const build=el('button','button','Build proposal from GM packet');build.onclick=buildMovementProposal;panel.append(exportButton,build);
    }
    const existing=root.querySelector('.movement-orders');if(existing)existing.replaceWith(panel);else root.prepend(panel);
  }
  function stageMovement(item,destination,source){if(!item.fleet&&!source){notify('Choose an owned settlement source.',true);return;}const r=item.record,key=item.fleet?'fleet_id':'unit_id';if(movementRequests.some(a=>a[key]===r.id)){notify('This force already has a staged movement request.',true);return;}if(item.fleet)movementRequests.push({type:'fleet_move',fleet_id:r.id,destination_system_id:destination,source_id:source});else movementRequests.push({type:'deploy_unit',unit_id:r.id,destination_province_id:destination,source_id:source});movementIntent=null;forceMap?.cancelTarget();invalidatePreview();renderOrders();$('#orders-panel').dataset.ready='true';drawMap();}
  async function buildMovementProposal(){
    const campaignId=state.campaignId,epoch=state.contextEpoch,snapshotId=state.snapshot?.id,authToken=state.gmToken||state.accessToken,area=$('#proposal-json'),initialText=area?.value||'';
    let proposal;
    if(initialText.trim()){
      try{proposal=JSON.parse(initialText);}catch{notify('The existing proposal JSON is invalid; fix it before adding movements.',true);return;}
      if(!proposal||typeof proposal!=='object'||!proposal.orders||!Array.isArray(proposal.orders.actions)){notify('The existing proposal has no actions list; it was left unchanged.',true);return;}
    }else{
      try{
        const packet=await api(`/api/admin/campaigns/${encodeURIComponent(campaignId)}/packet`,{headers:authHeaders()});
        if(epoch!==state.contextEpoch||campaignId!==state.campaignId||snapshotId!==state.snapshot?.id||authToken!==(state.gmToken||state.accessToken)||area!==$('#proposal-json')||area?.value!==initialText)return;
        proposal=packet.example;
        if(!proposal||!proposal.orders||!Array.isArray(proposal.orders.actions)){notify('The GM packet example has no movement actions list.',true);return;}
        proposal.submission_id=`movement-${crypto.randomUUID()}`;
      }catch(error){if(epoch===state.contextEpoch&&campaignId===state.campaignId&&snapshotId===state.snapshot?.id)notify(`GM packet required to add base revision metadata: ${error.message}`,true);return;}
    }
    if(epoch!==state.contextEpoch||campaignId!==state.campaignId||snapshotId!==state.snapshot?.id||area!==$('#proposal-json')||area?.value!==initialText)return;
    if(proposal.orders.actions.some(action=>!action||typeof action!=='object'||Array.isArray(action))){notify('Existing proposal actions include a malformed entry; repair them before adding movement requests.',true);return;}
    const actors=new Set(proposal.orders.actions.map(action=>action.fleet_id||action.unit_id).filter(Boolean));
    if(movementRequests.some(action=>actors.has(action.fleet_id||action.unit_id))){notify('A staged force already has an action in this proposal.',true);return;}
    proposal.orders.actions.push(...movementRequests);area.value=JSON.stringify(proposal,null,2);area.closest('details').open=true;
    movementRequests.splice(0);invalidatePreview();renderMovementOrders($('#orders-panel'));renderForceMap();notify('Movement actions added. Preview the proposal with the GM token.');
  }
  async function exportPacket(){const campaignId=state.campaignId,epoch=state.contextEpoch;try{const packet=await api(`/api/admin/campaigns/${encodeURIComponent(campaignId)}/packet`,{headers:authHeaders()});if(epoch!==state.contextEpoch||campaignId!==state.campaignId)return;const blob=new Blob([JSON.stringify(packet,null,2)],{type:'application/json'});const link=document.createElement('a');link.href=URL.createObjectURL(blob);link.download=`${state.campaignId}-decision-packet-turn-${packet.turn}.json`;link.click();URL.revokeObjectURL(link.href);setOrderStatus(`Packet exported · turn ${packet.turn} · load or paste the returned proposal.`);text($('#order-result'),`Packet exported · turn ${packet.turn} · hash ${packet.base_hash}`);}catch(e){if(epoch===state.contextEpoch&&campaignId===state.campaignId)showError(e);}}
  async function loadExample(){const campaignId=state.campaignId,epoch=state.contextEpoch,snapshotId=state.snapshot?.id,area=$('#proposal-json'),initialText=area?.value||'',token=state.gmToken||state.accessToken;try{const packet=await api(`/api/admin/campaigns/${encodeURIComponent(campaignId)}/packet`,{headers:authHeaders()});if(epoch!==state.contextEpoch||campaignId!==state.campaignId||snapshotId!==state.snapshot?.id||token!==(state.gmToken||state.accessToken)||area!==$('#proposal-json')||area?.value!==initialText)return;const proposal=structuredClone(packet.example);proposal.submission_id=`example-${crypto.randomUUID()}`;area.value=JSON.stringify(proposal,null,2);area.closest('details').open=true;invalidatePreview();}catch(e){if(epoch===state.contextEpoch&&campaignId===state.campaignId)showError(e);}}
  function setOrderStatus(message){const status=$('#order-status');if(status)text(status,message);}
  function invalidatePreview(){state.previewText=null;state.previewProposal=null;window.HWDesktop?.setPreviewReady(false);const b=$('#commit-order');if(b)b.disabled=true;const result=$('#order-result');if(result&&state.view==='orders')text(result,'Proposal changed. Preview it again before committing.');if($('#proposal-json')?.value)setOrderStatus('Draft changed · Preview to validate before commit.');else setOrderStatus('No proposal loaded · Export a packet or load an example.');renderForceMap();}
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
  async function previewOrder(){const campaignId=state.campaignId,epoch=state.contextEpoch,snapshotId=state.snapshot?.id,area=$('#proposal-json'),requestText=area?.value;try{if(!area)throw new Error('Proposal field is unavailable.');const parsed=JSON.parse(requestText);const data=await api(`/api/admin/campaigns/${encodeURIComponent(campaignId)}/preview`,{method:'POST',headers:authHeaders(true),body:JSON.stringify(parsed)});if(epoch!==state.contextEpoch||campaignId!==state.campaignId||snapshotId!==state.snapshot?.id||area!==$('#proposal-json')||area.value!==requestText)return;state.previewText=requestText;state.previewProposal=parsed;$('#commit-order').disabled=false;window.HWDesktop?.setPreviewReady(true);setOrderStatus('Preview validated · Review the backend response before commit.');renderPreviewSummary(data);renderForceMap();}catch(e){if(epoch!==state.contextEpoch||campaignId!==state.campaignId||snapshotId!==state.snapshot?.id)return;if(area!==$('#proposal-json')||area?.value!==requestText)return;state.previewText=null;state.previewProposal=null;window.HWDesktop?.setPreviewReady(false);$('#commit-order').disabled=true;setOrderStatus('Preview failed · Correct the proposal and try again.');renderForceMap();showError(e);}}
  async function commitOrder(){const campaignId=state.campaignId,epoch=state.contextEpoch;const area=$('#proposal-json');if(!state.previewText||state.previewText!==area.value){invalidatePreview();return;}try{const data=await api(`/api/admin/campaigns/${encodeURIComponent(campaignId)}/commit`,{method:'POST',headers:authHeaders(true),body:JSON.stringify(state.previewProposal)});if(epoch!==state.contextEpoch||campaignId!==state.campaignId)return;state.previewText=null;window.HWDesktop?.setPreviewReady(false);$('#commit-order').disabled=true;text($('#order-result'),JSON.stringify(data,null,2));clearCampaignContext();state.campaignId=campaignId;await loadCampaign();notify(`Turn committed · archive ${data.archive_status||'pending'}`);}catch(e){if(epoch===state.contextEpoch&&campaignId===state.campaignId)showError(e);}}
  function showError(error){text($('#status-text'),error.message||String(error));notify(error.message||String(error),true);}

  function setView(view){window.HWDesktop?.open(view);}
  function startClock(){const update=()=>text($('#clock'),new Date().toLocaleTimeString('en-AU', {timeZone:'Australia/Melbourne',hour:'2-digit',minute:'2-digit',hour12:false}));update();setInterval(update,15000);}
  function initMap(){
    const canvas=$('#planet-map');
    forceMap=window.HWMilitaryMap?.setup(canvas.parentElement);
    canvas.addEventListener('pointerdown',e=>{if(e.button!==0)return;canvas.setPointerCapture(e.pointerId);state.drag={pointerId:e.pointerId,x:e.clientX,y:e.clientY,startX:state.panX,startY:state.panY,moved:false};canvas.classList.add('is-grabbing');window.HWDesktop?.setGesture(true);});
    const moveDrag=e=>{if(!state.drag||e.pointerId!==state.drag.pointerId)return;const dx=e.clientX-state.drag.x,dy=e.clientY-state.drag.y;if(Math.abs(dx)+Math.abs(dy)>3)state.drag.moved=true;state.panX=state.drag.startX+dx;state.panY=state.drag.startY+dy;drawMap();state.drag.startX=state.panX-dx;state.drag.startY=state.panY-dy;};
    canvas.addEventListener('pointermove',e=>{
      const point=canvasPoint(e);if(state.drag){moveDrag(e);return;}
      const tip=$('#map-tooltip');
      if(state.transform?.hierarchy){const hit=nearestMapNode(point);if(!hit){tip.hidden=true;return;}tip.hidden=false;text(tip,hit.uiOnly?`${hit.n.name} · unlocated · recorded destination`:`${hit.n.name} · ${titleCase(hit.n.knowledge)}${Math.hypot(hit.x-(hit.anchorX??hit.x),hit.y-(hit.anchorY??hit.y))>1?' · symbol offset; leader marks coordinate':''} · click to inspect`);tip.style.left=`${Math.min(point.x+12,canvas.clientWidth-230)}px`;tip.style.top=`${Math.min(point.y+12,canvas.clientHeight-35)}px`;return;}
      const tile=provinceTileAt(point);if(!tile){tip.hidden=true;return;}tip.hidden=false;const labelTarget=provinceLabelAt(point);const geometry=state.mapRecord?.geometry;const p=tile.province_id&&geometry?.provinces.find(x=>x.id===tile.province_id);text(tip,labelTarget?`${labelTarget.label} · ${p?.name||'Recorded province'} · province anchor`:`Hovered terrain: ${terrainLabel(geometry,tile.terrain)} · ${p?p.name:'Open water'} · ${tile.x}, ${tile.y}`);tip.style.left=`${Math.min(point.x+12,canvas.clientWidth-240)}px`;tip.style.top=`${Math.min(point.y+12,canvas.clientHeight-35)}px`;
    });
    canvas.addEventListener('pointerup',e=>{if(!state.drag)return;const drag=state.drag;state.drag=null;canvas.classList.remove('is-grabbing');window.HWDesktop?.setGesture(false);if(drag.moved)return;const point=canvasPoint(e);if(forceMap?.targeting()){const intent=movementIntent;if(intent?.fleet){const hit=nearestMapNode(point);if(hit?.n.kind==='system'){const dest=intent.destinationSelect;dest.value=hit.n.id;stageMovement(intent,hit.n.id,intent.sourceSelect.value==='__none'?null:intent.sourceSelect.value);}else notify('Select a recorded system marker.',true);}else{const tile=provinceTileAt(point);if(tile?.province_id&&intent?.destinationSelect){intent.destinationSelect.value=tile.province_id;stageMovement(intent,tile.province_id,intent.sourceSelect.value==='__none'?null:intent.sourceSelect.value);}else notify('Select a recorded province.',true);}forceMap?.completeTarget();return;}if(state.transform?.hierarchy){const hit=nearestMapNode(point);if(hit){const next={sector:'sector',system:'system',planet:'planet'}[hit.n.kind];if(next&&!hit.uiOnly){state.selectedEntity=null;state.mapLevel=next;state.mapNodeId=hit.n.id;$('#map-level').value=next;state.zoom=1;state.panX=state.panY=0;loadMap();}else{state.selectedEntity=hit.n;renderInspector(liveState(),state.campaign);window.HWDesktop?.positionInspector(e.clientX);window.HWDesktop?.open('inspector');}}return;}const tile=provinceTileAt(point);state.selectedEntity=null;state.selectedProvince=tile?.province_id||null;renderInspector(liveState(),state.campaign);if(tile?.province_id){window.HWDesktop?.positionInspector(e.clientX);window.HWDesktop?.open('inspector');}drawMap();});
    const cancel=()=>{state.drag=null;canvas.classList.remove('is-grabbing');window.HWDesktop?.setGesture(false);};canvas.addEventListener('pointercancel',cancel);window.addEventListener('pointermove',e=>{if(state.drag&&e.target!==canvas)moveDrag(e);});window.addEventListener('pointerup',e=>{if(state.drag&&e.target!==canvas)cancel();});canvas.addEventListener('lostpointercapture',()=>{if(state.drag)canvas.classList.add('is-grabbing');});canvas.addEventListener('pointerleave',()=>$('#map-tooltip').hidden=true);canvas.addEventListener('wheel',e=>{e.preventDefault();zoomMap(e.deltaY<0?1.15:1/1.15,canvasPoint(e));},{passive:false});let drawFrame=0;const observer=new ResizeObserver(()=>{if(drawFrame)return;drawFrame=requestAnimationFrame(()=>{drawFrame=0;drawMap();});});const observed=[canvas.parentElement,...document.querySelectorAll('.commandbar,#resource-shell,#view-title,#map-breadcrumbs,#live-banner,.map-caption,#map-legend,.map-footer')];for(const node of new Set(observed))if(node)observer.observe(node);const inspector=$('#command-inspector');if(inspector){observer.observe(inspector);new MutationObserver(()=>drawMap()).observe(inspector,{attributes:true,attributeFilter:['hidden','class']});}
  }
  function nearestMapNode(point){const{positions=[],hitTargets=positions,safeRect}=state.transform||{};if(safeRect&&(point.x<safeRect.left||point.x>safeRect.right||point.y<safeRect.top||point.y>safeRect.bottom))return null;for(const item of hitTargets)if(item.hitRect&&point.x>=item.hitRect.left&&point.x<=item.hitRect.right&&point.y>=item.hitRect.top&&point.y<=item.hitRect.bottom)return item;let found=null,distance=Infinity;for(const item of hitTargets.filter(item=>!item.uiOnly)){if(safeRect&&(item.x<safeRect.left||item.x>safeRect.right||item.y<safeRect.top||item.y>safeRect.bottom))continue;const d=Math.hypot(item.x-point.x,item.y-point.y);if(d<distance){found=item;distance=d;}}return distance<26?found:null;}
  function positionOverview(frame,w,h,safe){
    const button=$('#map-overview-button'),width=156,height=button.offsetHeight||108,margin=12;
    let left=Math.max(margin,w-width-(parseFloat(button.style.right)||margin)),top=Math.max(safe.top,safe.bottom-height-8);
    const inspector=$('#command-inspector');
    if(inspector&&!inspector.hidden){const r=inspector.getBoundingClientRect(),f=frame.getBoundingClientRect(),box={left:r.left-f.left,right:r.right-f.left,top:r.top-f.top,bottom:r.bottom-f.top};
      if(left<box.right&&left+width>box.left&&top<box.bottom&&top+height>box.top){
        if(box.left>width+margin*2)left=Math.min(left,box.left-width-margin);
        else if(w-box.right>width+margin*2)left=box.right+margin;
        else top=Math.max(safe.top,box.top-height-margin);
      }
    }
    button.style.right=`${w-left-width}px`;button.style.bottom=`${h-top-height}px`;
    return{left,right:left+width,top,bottom:top+height};
  }
  function drawOverview(geometry,dpr){const button=$('#map-overview-button'),overview=$('#map-overview'),wrap=window.HWMapRenderer.wrapsX(geometry),help=wrap?'East and west edges join. Split viewport boxes show one continuous view across that join. North and south remain bounded. Click the overview to navigate.':'Chart extent overview. Activate to center the map here';text(button.querySelector('span'),wrap?'EAST ↔ WEST JOIN':'CHART EXTENT');button.title=help;button.setAttribute('aria-label',help);button.hidden=!geometry||!state.transform;const w=Math.max(1,overview.clientWidth),h=Math.max(1,overview.clientHeight);overview.width=Math.round(w*dpr);overview.height=Math.round(h*dpr);const ctx=overview.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);state.overviewBounds=window.HWMapRenderer.drawOverview(ctx,{geometry,w,h,transform:state.transform,style:state.mapStyle});}
  function navigateFromOverview(event){const geometry=state.mapRecord?.geometry,bounds=state.overviewBounds;if(!geometry||!bounds||!state.transform)return;const r=$('#map-overview').getBoundingClientRect(),hasPointer=event.clientX>=r.left&&event.clientX<=r.right&&event.clientY>=r.top&&event.clientY<=r.bottom,x=hasPointer?Math.max(0,Math.min(bounds.cols,(event.clientX-r.left-bounds.left)/bounds.width*bounds.cols)):bounds.cols/2,y=hasPointer?Math.max(0,Math.min(bounds.rows,(event.clientY-r.top-bounds.top)/bounds.height*bounds.rows)):bounds.rows/2,t=state.transform,tile=t.tile,centerX=$('#planet-map').clientWidth/2,centerY=$('#planet-map').clientHeight/2,baseLeft=(centerX-t.gridW/2),baseTop=(centerY-t.gridH/2);const longitude=window.HWMapRenderer.wrapsX(geometry)?window.HWMapRenderer.nearestX(x,bounds.cols/2,bounds.cols):x;state.panX=centerX-(baseLeft+longitude*tile);state.panY=centerY-(baseTop+y*tile);drawMap();}
  function resetPaneLayout(){window.HWDesktop?.resetLayout();notify('Window positions and sizes reset.');}

  function zoomMap(mult,anchor=null){const canvas=$('#planet-map'),before=state.zoom,geometry=state.mapRecord?.geometry,minimum=state.mapRecord?.level==='planet'&&geometry?.planet?minPlanetZoom(geometry,canvas.clientWidth,canvas.clientHeight):1,after=Math.max(minimum,Math.min(minimum*5,before*mult));if(after===before)return;const safe=state.transform?.safeRect||{left:0,right:canvas.clientWidth,top:0,bottom:canvas.clientHeight},centerX=state.transform?.hierarchy?(safe.left+safe.right)/2:canvas.clientWidth/2,centerY=state.transform?.hierarchy?(safe.top+safe.bottom)/2:canvas.clientHeight/2,at=anchor||{x:(safe.left+safe.right)/2,y:(safe.top+safe.bottom)/2},ratio=after/before;state.panX=at.x-centerX-(at.x-centerX-state.panX)*ratio;state.panY=at.y-centerY-(at.y-centerY-state.panY)*ratio;state.zoom=after;text($('#zoom-reset'),zoomPercent());drawMap();}
  function recenterMap(){if(state.mapRecord?.level==='planet'){const province=state.selectedProvince||liveState()?.settlements?.find(item=>item.owned)?.province_id;if(province)centerOnProvince(province);else state.panX=state.panY=0;}else state.panX=state.panY=0;drawMap();}
  function installNavIcons(){const colors=['var(--apple-system-blue)','var(--apple-system-mint)','var(--apple-system-teal)','var(--apple-system-indigo)'];document.querySelectorAll('.nav-item').forEach((button,index)=>{const view=button.dataset.view;button.title=titleCase(view);button.setAttribute('aria-label',`Open ${titleCase(view)} report`);if(button.querySelector('.nav-icon'))return;const icon=el('span','nav-icon');icon.setAttribute('aria-hidden','true');const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 16 16');svg.setAttribute('aria-hidden','true');const base=colors[index%colors.length];const shapes=[[[2,2],[3,2],[2,3],[3,3]],[[1,1],[2,1],[3,1],[1,2],[3,2],[1,3],[2,3],[3,3]],[[1,3],[2,2],[3,1],[3,2],[3,3]],[[1,1],[2,1],[3,1],[1,2],[2,2],[3,2],[2,3],[2,4]]][index%4];for(const [x,y]of shapes){const rect=document.createElementNS(svg.namespaceURI,'rect');rect.setAttribute('x',String(x*2));rect.setAttribute('y',String(y*2));rect.setAttribute('width','2');rect.setAttribute('height','2');rect.setAttribute('fill',base);svg.append(rect);}const frame=document.createElementNS(svg.namespaceURI,'rect');frame.setAttribute('x','1');frame.setAttribute('y','1');frame.setAttribute('width','14');frame.setAttribute('height','14');frame.setAttribute('fill','none');frame.setAttribute('stroke','#283743');frame.setAttribute('stroke-width','1');svg.append(frame);icon.append(svg);button.insertBefore(icon,button.firstChild);});}
  function clearCampaignContext(){movementRequests.splice(0);movementIntent=null;forceMap?.cancelTarget();state.contextEpoch++;state.campaignLoadSeq++;state.campaignListSeq++;state.historyLoadSeq++;state.mapLoadSeq++;state.snapshotLoadSeq++;for(const [view,seq]of state.managementRequests)state.managementRequests.set(view,seq+1);state.campaign=null;state.snapshot=null;state.history=[];state.historyLoading=false;state.historyTotal=0;state.historyOffset=0;state.selectedProvince=null;state.selectedEntity=null;state.mapRecord=null;state.mapNodeId=null;state.mapLevel='galactic';state.panX=state.panY=0;state.zoom=1;state.previewText=null;state.previewProposal=null;state.managementContexts.clear();state.managementLoading.clear();state.economyLoading=null;state.historyMetric='population';state.historyCompare=null;for(const panel of state.managementPanels.values())panel.replaceChildren();for(const id of ['economy-panel','history-panel','orders-panel'])$( `#${id}`).replaceChildren();$('#orders-panel').dataset.ready='';$('#campaign-kind').textContent='NO CAMPAIGN';$('#turn-badge').textContent='TURN —';$('#historical-badge').hidden=true;render();}
  function createManagementWindow(view){let panel=managementPanel(view);const labels={industry:'Industry',fleet:'Fleet',politics:'Politics',trade:'Trade',factions:'Factions',budget:'Budget',logistics:'Logistics',construction:'Construction',research:'Research',military:'Military',diplomacy:'Diplomacy',intelligence:'Intelligence',exploration:'Exploration',colonies:'Colonies',characters:'Characters'};const i=[...document.querySelectorAll('.sidebar .nav-item')].find(button=>button.dataset.view===view);const index=i?[...document.querySelectorAll('.sidebar .nav-item')].indexOf(i):4;return window.HWDesktop.createWindow(view,labels[view]||titleCase(view),panel,{x:Math.max(12,90+(index%6)*30),y:Math.max(12,55+(index%5)*28),w:520,h:460});}
  function onWindowOpen(view){if(view==='campaign')updateCampaignSummary();state.view=view;window.HWDesktop?.setScope(selectedScope(view));if(view==='planet'){if(state.campaign&&liveState()&&!state.mapRecord)loadMap().catch(showError);}else if(view==='economy')renderEconomy().catch(showError);else if(view==='history'){if(!state.history.length&&!state.historyLoading)loadHistory(0).catch(showError);else renderHistory();}else if(view==='orders'){if(!$('#orders-panel').dataset.ready){renderOrders();$('#orders-panel').dataset.ready='true';}}else if(isManagementView(view))loadManagement(view).catch(showError);}
  function wire(){
    installNavIcons();$('#campaign-select').addEventListener('change',async e=>{const id=e.target.value||null;if(!id)return;clearCampaignContext();state.campaignId=id;state.view='planet';$('#map-level').value='galactic';render();window.HWDesktop.close('campaign');const epoch=state.contextEpoch;try{await loadCampaign();}catch(error){if(epoch===state.contextEpoch&&state.campaignId===id)showError(error);}});$('#refresh-button').onclick=()=>{if(state.accessStatus==='checking')return;return loadCampaigns(state.campaignId).catch(showError);};
    $('#overlay-select').onchange=e=>{state.overlay=e.target.value;loadMap();};$('#map-style').onchange=e=>{state.mapStyle=e.target.value;renderMapLegend();drawMap();};$('#map-level').onchange=e=>setMapLevel(e.target.value);$('#zoom-in').onclick=()=>zoomMap(1.2);$('#zoom-out').onclick=()=>zoomMap(1/1.2);$('#zoom-reset').onclick=()=>{const c=$('#planet-map'),g=state.mapRecord?.geometry;state.zoom=state.mapRecord?.level==='planet'&&g?.planet?minPlanetZoom(g,c.clientWidth,c.clientHeight):1;state.panX=state.panY=0;text($('#zoom-reset'),'100%');drawMap();};$('#map-recenter').onclick=recenterMap;$('#map-overview-button').onclick=navigateFromOverview;$('#reset-layout').onclick=resetPaneLayout;$('#login-button').onclick=login;$('#logout-button').onclick=logout;$('#status-text').textContent='Connecting';
    window.HWDesktop.init();window.HWDesktop.setOnOpen(onWindowOpen);window.HWDesktop.setOnFocus(view=>{state.view=view;});window.HWDesktop.setOnCreate(createManagementWindow);
  }
  async function login(){const token=$('#access-token').value.trim();if(!token){notify('Enter an access token.',true);return;}clearCampaignContext();state.campaignId=null;state.accessToken=token;state.gmToken=token;const epoch=state.contextEpoch;$('#logout-button').hidden=false;$('#login-button').hidden=true;text($('#status-text'),'Checking private access');state.accessStatus='checking';updateCampaignSummary();try{const loaded=await loadCampaigns();if(!loaded||epoch!==state.contextEpoch)return;text($('#status-text'),'Private access verified · choose a campaign');updateCampaignSummary();notify('Signed in for this page session.');}catch(error){if(epoch!==state.contextEpoch)return;state.accessToken='';state.gmToken='';$('#logout-button').hidden=true;$('#login-button').hidden=false;text($('#status-text'),'Sign in required');state.accessStatus='ready';updateCampaignSummary();notify(error.message,true);}}
  function logout(){clearCampaignContext();state.accessToken='';state.gmToken='';state.campaigns=[];state.campaignId=null;$('#campaign-select').replaceChildren(new Option('Select campaign…',''));$('#access-token').value='';$('#logout-button').hidden=true;$('#login-button').hidden=false;render();window.HWDesktop.open('campaign');text($('#status-text'),'Sign in required');state.accessStatus='ready';updateCampaignSummary();}
  async function boot(){wire();initMap();startClock();$('#campaign-select').append(new Option('Select campaign…',''));window.HWDesktop.open('campaign');try{const access=await api('/api/access');state.privateMode=access.login_required;state.accessStatus='ready';updateCampaignSummary();$('#access-box').hidden=!state.privateMode;if(state.privateMode){text($('#status-text'),'Sign in required');updateCampaignSummary();return;}if(!await loadCampaigns())return;text($('#status-text'),state.campaignId?'Connected to local campaign database':'Choose a campaign');updateCampaignSummary();}catch(e){state.accessStatus='unavailable';updateCampaignSummary();text($('#status-text'),`API unavailable · ${e.message}`);notify(`Backend unavailable: ${e.message}`,true);} }
  boot();
})();
