(() => {
  'use strict';
  const root=typeof window==='undefined'?globalThis:window,MAX=24;
  function create(api,onUpdate=()=>{}){
    const cache=new Map(),controllers=new Set(),status=new Map();let context=null,request=0,running=false,queue=[];
    const current=token=>context&&token.request===request&&token.epoch===context.epoch&&token.campaignId===context.campaignId&&token.snapshotId===context.snapshotId&&token.systemId===context.systemId;
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
      for(let y=0;y<height;y++)for(let x=0;x<width;x++){
        const nx=(x+.5-width/2)/(width/2),ny=(height/2-y-.5)/(height/2),r2=nx*nx+ny*ny;if(r2>1)continue;
        const nz=Math.sqrt(1-r2),world=[0,1,2].map(i=>E[i]*nx+U[i]*ny+N[i]*nz),sampleLat=Math.asin(Math.max(-1,Math.min(1,world[1]))),sampleLon=Math.atan2(world[0],world[2]),sx=((sampleLon/(Math.PI*2)+.5)%1+1)%1*downsample.width,sy=(.5-sampleLat/Math.PI)*downsample.height,si=(Math.floor(sy)%downsample.height)*downsample.width+Math.floor(sx)%downsample.width,di=(y*width+x)*4,incidence=light?world[0]*light[0]+world[1]*light[1]+world[2]*light[2]:0,twilight=Math.max(0,Math.min(1,(incidence+.045)/.11)),diffuse=Math.pow(Math.max(0,incidence),.72)*twilight*twilight*(3-2*twilight),illumination=.045+.955*diffuse;
        image.data[di]=source.data[si*4]*illumination;image.data[di+1]=source.data[si*4+1]*illumination;image.data[di+2]=source.data[si*4+2]*illumination;image.data[di+3]=255;
      }
      ctx.putImageData(image,0,0);return out;
    }
    function setContext(next,record){
      systemRecord=record;request++;if(context&&(context.epoch!==next.epoch||context.campaignId!==next.campaignId||context.snapshotId!==next.snapshotId))cache.clear();
      context={...next,systemId:record?.parent?.id};queue=[];status.clear();for(const controller of controllers)controller.abort();controllers.clear();
      if(!context.systemId)return;
      for(const planet of (record?.nodes||[]).filter(item=>item.kind==='planet'&&item.knowledge==='surveyed').slice(0,MAX))if(planet.kind==='planet'&&planet.knowledge==='surveyed'){queue.push({id:planet.id,record:planet});status.set(planet.id,'loading');}
      drain();
    }
    async function drain(){
      if(running||!queue.length)return;running=true;const token={...context,request};
      try{while(queue.length&&current(token)){
        const {id}=queue.shift(),controller=new AbortController();controllers.add(controller);
        try{
          const map=await api(`/api/player/campaigns/${encodeURIComponent(token.campaignId)}/map?level=planet&node_id=${encodeURIComponent(id)}&snapshot_id=${encodeURIComponent(token.snapshotId||'')}&overlay=terrain`,{signal:controller.signal});
          if(!current(token))break;
          if(map.campaign_id!==token.campaignId||map.snapshot_id!==token.snapshotId||map.level!=='planet'||(map.selected_planet?.id||map.geometry?.planet?.id)!==id||map.selected_planet?.knowledge!=='surveyed')throw new Error('Preview map context did not match.');
          const geometry=map.geometry,ref=geometry?.detail_ref;
          if(ref?.version!=='planet-detail-v2'||!/^[0-9a-f]{64}$/.test(ref.sha256||'')||ref.width!==1024||ref.height!==640||!Number.isInteger(ref.byte_length)||ref.byte_length<1||ref.byte_length>8*1024*1024)throw new Error('Saved detail reference is unavailable.');
          const {orientation,light,illustrative=false}=orientationFor(systemRecord,id),key=`${token.epoch}:${token.campaignId}:${token.snapshotId}:${id}:${ref.sha256}:${orientation.latitude}:${orientation.longitude}`;
          if(cache.has(key)){status.set(id,'ready');if(current(token))onUpdate();continue;}
          const detailData=await api(`/api/player/campaigns/${encodeURIComponent(token.campaignId)}/detail?planet_id=${encodeURIComponent(id)}&snapshot_id=${encodeURIComponent(token.snapshotId||'')}`,{signal:controller.signal});
          if(!current(token))break;
          if((detailData.campaign_id!==undefined&&detailData.campaign_id!==token.campaignId)||detailData.planet_id!==id||detailData.snapshot_id!==token.snapshotId||detailData.detail_ref?.sha256!==ref.sha256||detailData.detail_ref?.version!==ref.version||detailData.detail_ref?.width!==ref.width||detailData.detail_ref?.height!==ref.height||detailData.detail_ref?.byte_length!==ref.byte_length||detailData.detail?.version!=='planet-detail-v2'||detailData.detail?.width!==ref.width||detailData.detail?.height!==ref.height)throw new Error('Saved detail did not match the selected snapshot.');
          const texture=root.HWMapRenderer.buildOrbitTexture({geometry,detail:detailData.detail,style:'orbital',overlay:'terrain'}),sprite=sphere(texture,orientation,light);
          cache.set(key,{id,sprite,sourceSha:ref.sha256,orientation,illustrative});status.set(id,'ready');while(cache.size>MAX)cache.delete(cache.keys().next().value);if(current(token))onUpdate();
        }catch(error){if(error?.name!=='AbortError'&&current(token)){status.set(id,'unavailable');onUpdate();}}finally{controllers.delete(controller);}
      }}finally{running=false;if(queue.length&&context)drain();}
    }
    let systemRecord=null;
    function get(id){if(!context)return null;for(const item of cache.values())if(item.id===id)return item;return null;}
    function stateFor(id){return status.get(id)||'unavailable';}
    function thumbnails(record){const result=new Map();if(!context||context.systemId!==record?.parent?.id)return result;for(const [key,item]of cache)if(key.startsWith(`${context.epoch}:${context.campaignId}:${context.snapshotId}:`))result.set(item.id,item.sprite);return result;}
    function suspend(){request++;queue=[];for(const controller of controllers)controller.abort();controllers.clear();}
    function clear(){suspend();context=null;systemRecord=null;cache.clear();status.clear();}
    return{setContext,thumbnails,get,stateFor,suspend,clear};
  }
  root.HWSystemPreviews={create};
})();
