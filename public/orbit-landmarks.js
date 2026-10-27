(() => {
  'use strict';
  const overlaps=(a,b,gap=5)=>a.left<b.right+gap&&a.right>b.left-gap&&a.top<b.bottom+gap&&a.bottom>b.top-gap;

  // Fine-grid anchors use tile-index coordinates: add half a tile for the center.
  const validAnchor=(anchor,planet)=>anchor&&Number.isFinite(anchor.x)&&Number.isFinite(anchor.y)&&planet?.width>0&&planet?.height>0&&anchor.x+.5>=0&&anchor.x+.5<planet.width&&anchor.y+.5>=0&&anchor.y+.5<planet.height;

  function groupsFor(settlements,planetId,provinceLand,selectedProvince,planet){
    const groups=new Map();
    for(const site of settlements||[]){
      if(site.planet_id!==planetId||!site.province_id)continue;
      const land=provinceLand.get(site.province_id),anchor=land?.anchor;
      if(!validAnchor(anchor,planet))continue;
      let group=groups.get(site.province_id);
      if(!group){group={provinceId:site.province_id,anchor,settlements:[],owned:false};groups.set(site.province_id,group);}
      group.settlements.push(site);group.owned=group.owned||site.owned===true;
    }
    return [...groups.values()].map(group=>{
      group.settlements.sort((a,b)=>String(a.id).localeCompare(String(b.id)));
      group.priority=group.provinceId===selectedProvince?0:group.owned?1:2;
      group.label=group.settlements.length===1?group.settlements[0].name||group.settlements[0].id:`${group.settlements[0].name||group.settlements[0].id} +${group.settlements.length-1}`;
      group.title=`${group.settlements.map(site=>site.name||site.id).join(', ')} · recorded province anchor`;
      return group;
    }).sort((a,b)=>a.priority-b.priority||String(a.provinceId).localeCompare(String(b.provinceId)));
  }

  function layout(groups,{planet,view,rect,safeRect,obstacles=[],screenPoint,measure=label=>({width:Math.max(76,Math.min(180,label.length*6.4+16)),height:24}),horizonMargin=.035,limit=12}){
    const placed=[],projected=[],d=view.distance??2.45,threshold=1/d+horizonMargin;
    for(const group of groups){
      if(!validAnchor(group.anchor,planet))continue;
      const {x,y}=group.anchor,latitude=Math.PI*(.5-(y+.5)/planet.height),longitude=(x+.5)/planet.width*Math.PI*2-Math.PI;
      const point=screenPoint(latitude,longitude,view,rect);
      if(!point||!Number.isFinite(point.x)||!Number.isFinite(point.y)||!Number.isFinite(point.depth)||point.depth<=threshold)continue;
      const markerRect={left:point.x-7,top:point.y-7,right:point.x+7,bottom:point.y+7};
      if(markerRect.left<safeRect.left||markerRect.top<safeRect.top||markerRect.right>safeRect.right||markerRect.bottom>safeRect.bottom||obstacles.some(box=>overlaps(box,markerRect,0)))continue;
      projected.push({...group,point,latitude,longitude,markerRect});
    }
    for(const item of projected){
      if(placed.length>=limit)break;
      const {point}=item;
      if(placed.some(other=>overlaps(item.markerRect,other.markerRect,2)))continue;
      const size=measure(item.label),candidates=[[13,-size.height-8],[13,8],[-size.width-13,-size.height-8],[-size.width-13,8],[-size.width/2,-size.height-16],[-size.width/2,16]];
      let labelRect=null;
      for(const [dx,dy] of candidates){
        const candidate={left:point.x+dx,top:point.y+dy,right:point.x+dx+size.width,bottom:point.y+dy+size.height};
        if(candidate.left<safeRect.left||candidate.top<safeRect.top||candidate.right>safeRect.right||candidate.bottom>safeRect.bottom)continue;
        // Reserve every eligible anchor before placing labels, including later priorities.
        if(obstacles.some(box=>overlaps(candidate,box,7))||projected.some(other=>overlaps(candidate,other.markerRect,2))||placed.some(other=>overlaps(candidate,other.labelRect,5)))continue;
        labelRect=candidate;break;
      }
      if(!labelRect)continue;
      const leader={x1:point.x,y1:point.y,x2:Math.max(labelRect.left,Math.min(labelRect.right,point.x)),y2:Math.max(labelRect.top,Math.min(labelRect.bottom,point.y))};
      placed.push({...item,labelRect,leader,markerOffset:{x:point.x-labelRect.left,y:point.y-labelRect.top}});
    }
    return placed;
  }

  window.HWOrbitLandmarks={groupsFor,layout};
})();
