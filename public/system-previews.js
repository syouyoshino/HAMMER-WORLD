(() => {
  'use strict';
  const root=typeof window==='undefined'?globalThis:window,MAX_SPRITES=24,MAX_RAW=2,MAX_BYTES=16*1024*1024;
  function create(api,onUpdate=()=>{}){
    const sprites=new Map(),raw=new Map(),status=new Map(),jobs=new Map();let context=null,request=0,active=null,queue=[],systemRecord=null;
    const current=token=>context&&token.request===request&&token.epoch===context.epoch&&token.campaignId===context.campaignId&&token.snapshotId===context.snapshotId&&token.systemId===context.systemId;
    const keyFor=(id,sha,style,token=context)=>`${token.epoch}:${token.campaignId}:${token.snapshotId}:${id}:${sha}:${style}`;
    function orientationFor(record,id){
      const model=root.HWSystemView?.model(record),planet=model?.located?.find(item=>item.n.id===id),star=model?.located?.find(item=>item.n.kind==='star');
      if(!planet||!star){const fallback=[-.42,.5,.76],length=Math.hypot(...fallback);return{orientation:{latitude:0,longitude:0},light:fallback.map(value=>value/length),illustrative:true};}
      const v=star.normalized.map((value,index)=>value-planet.normalized[index]),length=Math.hypot(...v);if(!length)return{orientation:{latitude:0,longitude:0},light:null};
      const light=v.map(value=>value/length),solarLongitude=Math.atan2(light[0],light[2]),east=[Math.cos(solarLongitude),0,-Math.sin(solarLongitude)],normal=light.map((value,index)=>value*Math.cos(.6)+east[index]*Math.sin(.6));
      return{orientation:{latitude:Math.asin(Math.max(-1,Math.min(1,normal[1]))),longitude:Math.atan2(normal[0],normal[2])},light};
    }
    function sphere(texture,orientation,light){
      const downsample=document.createElement('canvas');downsample.width=256;downsample.height=128;const dctx=downsample.getContext('2d');dctx.drawImage(texture,0,0,downsample.width,downsample.height);
      const source=dctx.getImageData(0,0,downsample.width,downsample.height),width=128,height=128,out=document.createElement('canvas');out.width=width;out.height=height;
      const ctx=out.getContext('2d'),image=ctx.createImageData(width,height),lat=orientation.latitude,lon=orientation.longitude,sp=Math.sin(lat),cp=Math.cos(lat),sl=Math.sin(lon),cl=Math.cos(lon),N=[cp*sl,sp,cp*cl],E=[cl,0,-sl],U=[-sp*sl,cp,-sp*cl];
      for(let y=0;y<height;y++)for(let x=0;x<width;x++){const nx=(x+.5-width/2)/(width/2),ny=(height/2-y-.5)/(height/2),r2=nx*nx+ny*ny;if(r2>1)continue;const nz=Math.sqrt(1-r2),world=[0,1,2].map(i=>E[i]*nx+U[i]*ny+N[i]*nz),sampleLat=Math.asin(Math.max(-1,Math.min(1,world[1]))),sampleLon=Math.atan2(world[0],world[2]),sx=((sampleLon/(Math.PI*2)+.5)%1+1)%1*downsample.width,sy=(.5-sampleLat/Math.PI)*downsample.height,si=(Math.floor(sy)%downsample.height)*downsample.width+Math.floor(sx)%downsample.width,di=(y*width+x)*4,incidence=light?world[0]*light[0]+world[1]*light[1]+world[2]*light[2]:0,twilight=Math.max(0,Math.min(1,(incidence+.045)/.11)),diffuse=Math.pow(Math.max(0,incidence),.72)*twilight*twilight*(3-2*twilight),illumination=.045+.955*diffuse;image.data[di]=source.data[si*4]*illumination;image.data[di+1]=source.data[si*4+1]*illumination;image.data[di+2]=source.data[si*4+2]*illumination;image.data[di+3]=255;}
      ctx.putImageData(image,0,0);return out;
    }
    function retain(key,value){raw.delete(key);raw.set(key,value);let bytes=[...raw.values()].reduce((sum,item)=>sum+item.bytes,0);while(raw.size>MAX_RAW||bytes>MAX_BYTES){const oldest=raw.keys().next().value,item=raw.get(oldest);raw.delete(oldest);bytes-=item.bytes;}}
    const member=id=>context&&(systemRecord?.nodes||[]).find(node=>node.id===id&&node.kind==='planet'&&node.knowledge==='surveyed'&&node.parent_id===context.systemId);
    const jobKey=(id,style)=>`${id}:${style}`;
    function cancelJobs(error){
      for(const job of jobs.values()){job.controller?.abort();job.reject(error);if(status.get(job.id)==='loading')status.set(job.id,'unavailable');}
      jobs.clear();queue=[];active=null;
    }
    function enqueue(id,style,priority=false){
      const key=jobKey(id,style);let job=jobs.get(key);
      if(!job){let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no;});promise.catch(()=>{});job={id,style,promise,resolve,reject,token:{...context,request}};jobs.set(key,job);queue.push(job);}
      if(priority){const at=queue.indexOf(job);if(at>=0){queue.splice(at,1);queue.unshift(job);}}
      status.set(id,'loading');drain();return job.promise;
    }
    function setContext(next,record){
      request++;cancelJobs(new Error('Preview context changed.'));
      if(!context||context.epoch!==next.epoch||context.campaignId!==next.campaignId||context.snapshotId!==next.snapshotId){sprites.clear();raw.clear();}
      context={...next,systemId:record?.parent?.id};systemRecord=record;status.clear();if(!context.systemId)return;
      for(const planet of (record?.nodes||[]).filter(node=>member(node.id)).slice(0,MAX_SPRITES)){
        const style=context.style||'orbital';
        if(get(planet.id,style)){status.set(planet.id,'ready');continue;}
        enqueue(planet.id,style);
      }
    }
    function ensurePlanet(id,style='orbital'){
      if(!member(id))return Promise.reject(new Error('Planet is not a surveyed member of the current system.'));
      const asset=getPlanet(id,style);if(asset)return Promise.resolve(asset);
      return enqueue(id,style,true);
    }
    async function build(id,style,token,controller){
      const map=await api(`/api/player/campaigns/${encodeURIComponent(token.campaignId)}/map?level=planet&node_id=${encodeURIComponent(id)}&snapshot_id=${encodeURIComponent(token.snapshotId||'')}&overlay=terrain`,{signal:controller.signal});if(!current(token))return;
      if(map.campaign_id!==token.campaignId||map.snapshot_id!==token.snapshotId||map.level!=='planet'||map.selected_planet?.id!==id||map.selected_planet?.knowledge!=='surveyed'||map.selected_planet?.parent_id!==token.systemId||(map.parent&&(map.parent.id!==id||map.parent.parent_id!==token.systemId)))throw new Error('Preview map context did not match.');
      const geometry=map.geometry,ref=geometry?.detail_ref;if(ref?.version!=='planet-detail-v2'||!/^[0-9a-f]{64}$/.test(ref.sha256||'')||ref.width!==1024||ref.height!==640||!Number.isInteger(ref.byte_length)||ref.byte_length<1||ref.byte_length>8*1024*1024)throw new Error('Saved detail reference is unavailable.');
      const {orientation,light,illustrative=false}=orientationFor(systemRecord,id),key=keyFor(id,ref.sha256,style,token);
      let asset=raw.get(key);if(!asset){const detailData=await api(`/api/player/campaigns/${encodeURIComponent(token.campaignId)}/detail?planet_id=${encodeURIComponent(id)}&snapshot_id=${encodeURIComponent(token.snapshotId||'')}`,{signal:controller.signal});if(!current(token))return;
        if((detailData.campaign_id!==undefined&&detailData.campaign_id!==token.campaignId)||detailData.planet_id!==id||detailData.snapshot_id!==token.snapshotId||detailData.detail_ref?.sha256!==ref.sha256||detailData.detail_ref?.version!==ref.version||detailData.detail_ref?.width!==ref.width||detailData.detail_ref?.height!==ref.height||detailData.detail_ref?.byte_length!==ref.byte_length||detailData.detail?.version!=='planet-detail-v2'||detailData.detail?.width!==ref.width||detailData.detail?.height!==ref.height)throw new Error('Saved detail did not match the selected snapshot.');
        asset={id,geometry,detail:detailData.detail,sourceSha:ref.sha256,ref,bytes:ref.byte_length,style,orientation,light,illustrative};
      }
      if(!current(token))throw new Error('Preview context changed.');
      const texture=root.HWMapRenderer.buildOrbitTexture({geometry:asset.geometry,detail:asset.detail,style,overlay:'terrain'}),sprite=sphere(texture,orientation,light);
      if(!current(token))throw new Error('Preview context changed.');
      retain(key,asset);
      const item={id,sprite,sourceSha:ref.sha256,orientation,light,illustrative,style};
      sprites.delete(key);sprites.set(key,item);while(sprites.size>MAX_SPRITES)sprites.delete(sprites.keys().next().value);
      return asset;
    }
    function drain(){
      if(active||!queue.length||!context)return;
      const job=queue.shift();if(!current(job.token)){job.reject(new Error('Preview context changed.'));return drain();}
      active=job;job.controller=new AbortController();
      build(job.id,job.style,job.token,job.controller).then(asset=>{
        if(current(job.token)&&jobs.get(jobKey(job.id,job.style))===job){status.set(job.id,'ready');job.resolve(asset);onUpdate();}
      }).catch(error=>{
        job.reject(error);if(current(job.token)){status.set(job.id,'unavailable');onUpdate();}
      }).finally(()=>{
        if(jobs.get(jobKey(job.id,job.style))===job)jobs.delete(jobKey(job.id,job.style));
        if(active===job){active=null;drain();}
      });
    }
    function get(id,style=null){
      if(!member(id))return null;
      for(const item of sprites.values())if(item.id===id&&(!style||item.style===style))return item;
      return null;
    }
    function getPlanet(id,style='orbital',expectedSha=null){
      if(!member(id))return null;
      for(const [key,asset] of raw)if(asset.id===id&&asset.style===style&&(expectedSha===null||asset.sourceSha===expectedSha)){
        raw.delete(key);raw.set(key,asset);return asset;
      }
      return null;
    }
    function stateFor(id){return status.get(id)||'unavailable';}
    function thumbnails(record){const result=new Map();if(!context||context.systemId!==record?.parent?.id)return result;for(const item of sprites.values())if(member(item.id))result.set(item.id,item.sprite);return result;}
    function suspend(){request++;cancelJobs(new Error('Preview requests suspended.'));}
    function clear(){suspend();context=null;systemRecord=null;sprites.clear();raw.clear();status.clear();}
    return{setContext,thumbnails,get,getPlanet,stateFor,ensurePlanet,suspend,clear};
  }
  root.HWSystemPreviews={create};
})();
