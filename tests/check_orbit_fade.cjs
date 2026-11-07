// Run the app's real opacity scheduler with publication delays and stale callbacks.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const app=fs.readFileSync('public/app.js','utf8');
const helpers=app.slice(app.indexOf('  function paintOrbit('),app.indexOf('  function orbitFocus('));
const release=app.slice(app.indexOf('  function releaseOrbitComposite('),app.indexOf('  function measureOrbitPresentation('));
function fixture(from='surface'){
 const callbacks=new Map(),canceled=[],backdrops=[],group={style:{},prepend(node){this.backdrop=node;}},frame={clientWidth:1440,clientHeight:1000};
 let clock=0,nextId=0,paints=0,draws=0;
 const canvas={width:648,height:450,style:{}},native={canvas,epoch:1,campaignId:'demo',snapshotId:'saved',style:'orbital',overlay:'terrain',w:1440,h:1000,dpr:1,rect:{left:0,top:240,width:1440,height:660}};
 const state={contextEpoch:1,campaignId:'demo',snapshot:{id:'saved'},mapRecord:{geometry:{}},mapLoadSeq:2,mapInputSeq:4,mapStyle:'orbital',overlay:'terrain',orbitActive:from==='surface',orbitView:{latitude:.2,longitude:1,distance:2.45},zoom:1,panX:0,panY:0,orbitCanvas:canvas,orbitFade:{from,phase:'prepare',duration:420,raf:null}};
 const box={state,window:{devicePixelRatio:1,HWOrbitBackground:{draw(){paints++;}}},performance:{now:()=>clock},$:()=>({parentElement:frame}),clearOrbitLandmarks(){},drawMap(){draws++;},requestAnimationFrame(fn){callbacks.set(++nextId,fn);return nextId;},cancelAnimationFrame(id){canceled.push(id);callbacks.delete(id);},document:{createElement(){const node={width:0,height:0,remove(){this.removed=true;},getContext:()=>({setTransform(){}})};backdrops.push(node);return node;}}};
 vm.createContext(box);vm.runInContext(`let orbitComposite=null,orbitPresentationLayer=globalThis.group,nativeOrbitFrame=globalThis.native;${release}${helpers};globalThis.api={present:presentOrbitFade,cancel:cancelOrbitFade,valid:orbitFadeValid};`,Object.assign(box,{group,native}));
 const start=()=>{assert.equal(box.api.present(1440,1000,native.rect,null),true);return state.orbitFade;};
 const run=(id,time=clock)=>{const callback=callbacks.get(id);assert(callback,'Publication and motion RAFs must be owned');callbacks.delete(id);clock=time;callback(time);};
 return{box,state,group,canvas,frame,callbacks,canceled,backdrops,start,run,paints:()=>paints,draws:()=>draws};
}
for(const from of ['surface','orbit']){
 const f=fixture(from),fade=f.start(),epsilon=1/255;
 assert.equal(f.canvas.style.opacity,'1','Native globe retains full opacity inside the group');
 const first=Number(f.group.style.opacity);assert(Math.abs(first-(from==='surface'?epsilon:1-epsilon))<1e-8);
 f.run(fade.raf,300);f.run(fade.raf,700);
 assert.equal(Number(f.group.style.opacity),first,'GPU publication cannot spend the fade clock');
 const samples=[];
 for(let time=716;time<1120;time+=16){f.run(fade.raf,time);samples.push(Number(f.group.style.opacity));assert.equal(f.paints(),1,'No backdrop raster work during opacity ticks');assert.equal(f.draws(),0,'No map redraw during opacity ticks');}
 assert(samples.length>=20);assert(Math.abs(samples[0]-first)<.01,'Motion accelerates gently after publication');
 for(let i=1;i<samples.length;i++)assert(from==='surface'?samples[i]>=samples[i-1]:samples[i]<=samples[i-1]);
 f.run(fade.raf,1120);assert.equal(f.state.orbitFade,null);assert.equal(f.draws(),1,'Completion performs one atomic final draw');
 assert.equal(f.group.style.opacity,'1');assert.equal(f.backdrops[0].width,1);assert.equal(f.backdrops[0].height,1);assert(f.backdrops[0].removed);
}
for(const stage of [0,1,2]){
 const f=fixture(),old=f.start();for(let i=0;i<stage;i++)f.run(old.raf);
 const stale=f.callbacks.get(old.raf);f.box.api.cancel();assert(f.canceled.includes(old.raf));
 f.state.orbitFade={from:'orbit',phase:'prepare',duration:420,raf:null};f.state.orbitActive=false;const replacement=f.start(),opacity=f.group.style.opacity,handle=replacement.raf;
 stale(16);assert.equal(f.state.orbitFade,replacement);assert.equal(replacement.raf,handle);assert.equal(f.group.style.opacity,opacity);assert(!f.backdrops[1].removed,'Stale callbacks cannot free the new presentation');
}
for(const mutate of [f=>f.state.contextEpoch++,f=>f.state.campaignId='other',f=>f.state.snapshot={id:'later'},f=>f.state.mapRecord={},f=>f.state.mapLoadSeq++,f=>f.state.mapInputSeq++,f=>f.state.mapStyle='survey',f=>f.state.overlay='provinces',f=>f.state.orbitView.longitude+=.1,f=>f.state.orbitView.distance+=.1,f=>f.state.zoom++,f=>f.state.panX++,f=>f.state.orbitActive=false,f=>f.frame.clientWidth--,f=>f.frame.clientHeight--,f=>f.box.window.devicePixelRatio=2,f=>f.canvas.width--,f=>f.state.orbitUnavailable=true]){
 const f=fixture(),fade=f.start();mutate(f);f.run(fade.raf);assert.equal(f.state.orbitFade,null);assert.equal(f.draws(),1);assert.equal(f.group.style.opacity,'1');assert(f.backdrops[0].removed);
}
console.log('Actual fade publication clock, opacity-only ticks, atomic completion, resource cleanup and stale/context/camera/viewport callback guards passed');
