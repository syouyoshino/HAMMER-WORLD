(() => {
  'use strict';

  const CAMERA_KEYS=['panX','panY','zoom','orbitActive'];
  function capture(state){
    return {campaignId:state.campaignId,snapshotId:state.snapshot?.id||null,contextEpoch:state.contextEpoch,
      mapLevel:state.mapLevel,mapNodeId:state.mapNodeId,selectedProvince:state.selectedProvince,
      selectedEntity:state.selectedEntity,selectedFeatureId:state.selectedFeatureId,
      selectedFeaturePlanetId:state.selectedFeaturePlanetId,selectedFeatureReturnProvince:state.selectedFeatureReturnProvince,
      selectedComposition:state.selectedComposition?{...state.selectedComposition}:null,
      overlay:state.overlay,mapStyle:state.mapStyle,showFeatureNames:state.showFeatureNames,
      featureListOpen:state.featureListOpen,featureListQuery:state.featureListQuery,
      orbitView:{...state.orbitView},systemView:state.systemView?{...state.systemView}:undefined,detailAsset:state.detailAsset,detailKey:state.detailKey,
      detailStatus:state.detailStatus,mapRecord:state.mapRecord,orbitTexture:state.orbitTexture,
      orbitTextureKey:state.orbitTextureKey,orbitInitialKey:state.orbitInitialKey,
      entryFocusMarker:state.entryFocusMarker?{...state.entryFocusMarker}:null,
      camera:Object.fromEntries(CAMERA_KEYS.map(key=>[key,state[key]]))};
  }
  function matches(ticket,state){return Boolean(ticket&&ticket.contextEpoch===state.contextEpoch&&
    ticket.campaignId===state.campaignId&&ticket.snapshotId===(state.snapshot?.id||null));}
  function restore(ticket,state){
    if(!matches(ticket,state))return false;
    state.mapLevel=ticket.mapLevel;state.mapNodeId=ticket.mapNodeId;
    state.selectedProvince=ticket.selectedProvince;state.selectedEntity=ticket.selectedEntity;
    state.selectedFeatureId=ticket.selectedFeatureId;state.selectedFeaturePlanetId=ticket.selectedFeaturePlanetId;
    state.selectedFeatureReturnProvince=ticket.selectedFeatureReturnProvince;
    state.selectedComposition=ticket.selectedComposition?{...ticket.selectedComposition}:null;
    state.overlay=ticket.overlay;state.mapStyle=ticket.mapStyle;state.showFeatureNames=ticket.showFeatureNames;
    state.featureListOpen=ticket.featureListOpen;state.featureListQuery=ticket.featureListQuery;
    state.orbitView={...ticket.orbitView};if(ticket.systemView)state.systemView={...ticket.systemView};Object.assign(state,ticket.camera);
    state.detailAsset=ticket.detailAsset;state.detailKey=ticket.detailKey;state.detailStatus=ticket.detailStatus;
    state.orbitTexture=ticket.orbitTexture;state.orbitTextureKey=ticket.orbitTextureKey;state.orbitInitialKey=ticket.orbitInitialKey;state.entryFocusMarker=ticket.entryFocusMarker?{...ticket.entryFocusMarker}:null;
    return true;
  }
  function element(tag,className,text){const node=document.createElement(tag);if(className)node.className=className;if(text!==undefined)node.textContent=String(text);return node;}
  function row(root,label,value){const line=element('div','inspector-row');line.append(element('span','',label),element('b','',value));root.append(line);}
  function renderFocus(root,node,record,onBack,nodes,onSelect,mapped=false){
    root.replaceChildren();root.hidden=false;root.dataset.bodyFocus='true';
    const kind=node.kind,detected=node.knowledge!=='surveyed';
    root.className='body-focus-view'+(mapped?' body-focus-mapped':'');root.dataset.bodyId=node.id;root.dataset.bodyKind=kind;root.dataset.bodyKnowledge=node.knowledge;root.setAttribute('role','region');root.setAttribute('aria-label',`${node.name||kind} focused record`);
    const stage=element('div','body-focus-stage');stage.setAttribute('aria-hidden','true');
    stage.append(element('div',`body-focus-illustration body-focus-${kind}`),element('span','body-focus-caption',kind==='star'?'ILLUSTRATIVE STELLAR DISC · NOT TO SCALE':'SCHEMATIC SILHOUETTE · SURFACE UNKNOWN'));
    const reading=element('div','body-focus-reading');
    const heading=element('h2','inspector-planet',node.name||`Unknown ${kind}`);heading.tabIndex=-1;
    reading.append(heading,element('div','inspector-sub',`${(node.knowledge||'unknown').toUpperCase()} RECORD · ${kind.toUpperCase()} FOCUS`));
    if(kind==='star'){
      row(reading,'Stellar class',node.stellar_class||'Unknown');
      row(reading,'Physical radius',node.radius_m!=null?`${node.radius_m} m`:record?.radius_km!=null?`${record.radius_km} km`:'Unknown');
      row(reading,'Saved position',Array.isArray(record?.position)?`${record.position.join(', ')} micro-AU`:'Unknown');
      row(reading,'Motion',record?'Frozen at epoch 0':'Unknown · astronomy not recorded');
      reading.append(element('div','note-box','Illustrative star glow. No stellar activity, flare, or event data is recorded.'));
    }else{
      row(reading,'Physical radius',node.radius_m!=null?`${node.radius_m} m`:record?.radius_km!=null?`${record.radius_km} km`:'Unknown');
      row(reading,'Surface',mapped?'Recorded planetary survey':'Unknown · no detailed surface recorded');
      row(reading,'Saved position',Array.isArray(record?.position)?`${record.position.join(', ')} micro-AU`:'Unknown');
      reading.append(element('div','note-box',mapped?'The recorded planetary map remains available.':'Neutral silhouette only. No terrain, craters, or coordinates are inferred.'));
    }
    const back=element('button','button small','Back to origin map');back.type='button';back.id='body-focus-back';back.addEventListener('click',onBack);reading.append(back);
    renderKnownBodies(reading,nodes,onSelect,node.id);root.append(stage,reading);
  }
  function renderKnownBodies(root,nodes,onSelect,selectedId=null){
    const known=(nodes||[]).filter(node=>node&&['star','planet','moon'].includes(node.kind)&&node.knowledge!=='hidden');
    if(!known.length)return;
    const section=element('nav','known-bodies');section.id='known-bodies-list';section.setAttribute('aria-label','Known bodies in this system');
    section.append(element('div','inspector-section','KNOWN BODIES · THIS SYSTEM'));
    const list=element('div','known-bodies-rows');
    const ordered=[...known.filter(n=>n.kind==='star')];
    for(const planet of known.filter(n=>n.kind==='planet')){ordered.push(planet,...known.filter(n=>n.kind==='moon'&&n.parent_id===planet.id));}
    for(const moon of known.filter(n=>n.kind==='moon'&&!ordered.includes(n)))ordered.push(moon);
    for(const node of ordered){
      const button=element('button','known-body-row'+(node.kind==='moon'?' known-body-moon':''));button.type='button';button.dataset.bodyId=node.id;if(node.id===selectedId)button.setAttribute('aria-current','true');
      button.append(element('span','known-body-name',node.name||`Unknown ${node.kind}`),element('span','known-body-meta',`${(node.knowledge||'unknown').toUpperCase()} · ${node.kind.toUpperCase()}`));
      button.title=node.kind==='planet'&&node.knowledge==='surveyed'?'Open recorded planet map':`Focus ${node.name||node.kind}`;button.addEventListener('click',()=>onSelect(node));list.append(button);
    }
    section.append(list);root.append(section);
  }
  document.addEventListener('visibilitychange',()=>document.documentElement.classList.toggle('body-focus-paused',document.hidden));
  window.HWBodyFocus={capture,matches,restore,renderFocus,renderKnownBodies};
})();
