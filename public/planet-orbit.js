(() => {
  "use strict";
  const TAU = Math.PI * 2, MAX_SIDE = 2048, MAX_PIXELS = 2_097_152;
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  const wrapLon = value => ((value + Math.PI) % TAU + TAU) % TAU - Math.PI;

  function basis(latitude, longitude) {
    const p = clamp(latitude, -Math.PI / 2, Math.PI / 2), l = wrapLon(longitude), sp = Math.sin(p), cp = Math.cos(p), sl = Math.sin(l), cl = Math.cos(l);
    return { N:[cp*sl,sp,cp*cl], E:[cl,0,-sl], U:[-sp*sl,cp,-sp*cl] };
  }
  function unit(latitude, longitude) {
    const p=clamp(latitude,-Math.PI/2,Math.PI/2),l=wrapLon(longitude),c=Math.cos(p);
    return [c*Math.sin(l),Math.sin(p),c*Math.cos(l)];
  }
  function dot(a,b) { return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]; }
  function screenPoint(latitude, longitude, view, rect) {
    const b=basis(view.latitude,view.longitude), d=unit(latitude,longitude), z=dot(d,b.N), D=view.distance??2.45;
    if(D*z<=1)return null;
    const scale=Math.min(rect.width,rect.height)*.36, den=D-z;
    return {x:rect.left+rect.width/2+scale*D*dot(d,b.E)/den,
      y:rect.top+rect.height/2-scale*D*dot(d,b.U)/den, depth:z};
  }
  function inversePoint(x,y,view,rect) {
    const scale=Math.min(rect.width,rect.height)*.36, nx=(x-rect.left-rect.width/2)/scale, ny=-(y-rect.top-rect.height/2)/scale, D=view.distance??2.45;
    // Perspective segment from (0,0,D) to the image plane at z=0.
    const a=nx*nx+ny*ny+D*D, bq=-2*D*D, c=D*D-1, disc=bq*bq-4*a*c;
    if(disc<0)return null;
    const t=(-bq-Math.sqrt(disc))/(2*a), hit=[nx*t,ny*t,D*(1-t)];
    if(hit[2]<=0)return null;
    const frame=basis(view.latitude,view.longitude), world=[0,1,2].map(i=>frame.E[i]*hit[0]+frame.U[i]*hit[1]+frame.N[i]*hit[2]);
    return {latitude:Math.asin(clamp(world[1],-1,1)),longitude:wrapLon(Math.atan2(world[0],world[2]))};
  }
  function focusFlatCamera(width,height,cols,rows,focusX,focusY,distance=2.45) {
    const tile=Math.min(width,height)*.36*distance*Math.PI/((distance-1)*rows);
    return {tile,panX:width/2-(width-cols*tile)/2-focusX*tile,
      panY:height/2-(height-rows*tile)/2-focusY*tile};
  }
  function distanceForTile(rect,rows,tile) {
    const scale=Math.max(.001,tile)*rows,denom=scale-Math.min(rect.width,rect.height)*.36*Math.PI;
    return clamp(denom>0?scale/denom:4.2,1.018,4.2);
  }
  function powerOfTwoSize(width,height) {
    const scale=Math.min(1,MAX_SIDE/width,MAX_SIDE/height,Math.sqrt(MAX_PIXELS/(width*height)));
    const pow=v=>2**Math.floor(Math.log2(Math.max(1,v*scale)));
    return {width:pow(width),height:pow(height)};
  }
  // Average the saved upload rows in linear light, weighted by recorded alpha.
  function rowMeans(pixels,width,height){
    const means=new Uint8ClampedArray(height*4),linear=Array.from({length:256},(_,i)=>(i/255)**2.2);
    for(let y=0;y<height;y++){
      let r=0,g=0,b=0,alpha=0;
      for(let x=0;x<width;x++){const i=(y*width+x)*4,a=pixels[i+3]/255;alpha+=a;r+=linear[pixels[i]]*a;g+=linear[pixels[i+1]]*a;b+=linear[pixels[i+2]]*a;}
      const j=y*4;means[j]=alpha?255*(r/alpha)**(1/2.2):0;means[j+1]=alpha?255*(g/alpha)**(1/2.2):0;means[j+2]=alpha?255*(b/alpha)**(1/2.2):0;means[j+3]=255*alpha/width;
    }
    return means;
  }
  function create(canvas) {
    const gl=canvas?.getContext?.("webgl",{alpha:true,antialias:true,premultipliedAlpha:true,preserveDrawingBuffer:false});
    if(!gl)return null;
    const vs=`attribute vec2 p; varying vec2 v; void main(){v=p*.5+.5;gl_Position=vec4(p,0.,1.);}`;
    const gradientSampling=gl.getExtension("OES_standard_derivatives")&&gl.getExtension("EXT_shader_texture_lod");
    const fs=`${gradientSampling?"#extension GL_OES_standard_derivatives : enable\n#extension GL_EXT_shader_texture_lod : enable\n":""}#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif
varying vec2 v;
uniform sampler2D tex,poleMean;
uniform vec3 N,E,U;
uniform vec2 viewSize,textureSize;
uniform float D,pixelAngle;
vec4 linearPremul(vec4 c){return vec4(pow(c.rgb,vec3(2.2))*c.a,c.a);}
void main(){
 vec2 q=(v-.5)*viewSize*2.777777777777778;
 vec3 ro=vec3(0.,0.,D),rd=normalize(vec3(q,-D));
 float b=dot(ro,rd),h=b*b-(dot(ro,ro)-1.);if(h<0.)discard;
 float t=-b-sqrt(h);if(t<=0.)discard;
 vec3 hit=ro+rd*t,w=normalize(E*hit.x+U*hit.y+N*hit.z);
 float radial=length(w.xz),theta=atan(radial,abs(w.y));
 float lat=asin(clamp(w.y,-1.,1.)),lon=radial<.000001?0.:atan(w.x,w.z);
 vec2 uv=vec2(lon/6.28318530718+.5,.5+lat/3.14159265359);
 float angular=${gradientSampling?".5*(length(dFdx(w))+length(dFdy(w)))":"pixelAngle/max(.12,abs(dot(normalize(hit),-rd)))"};
 float footprint=max(angular,3.14159265359/textureSize.y*.5);
 float meanWeight=1.-smoothstep(footprint,2.*footprint,theta);
 float longitudeSpan=min(.5,angular/max(radial,.000001)/6.28318530718);
 ${gradientSampling?"vec2 dx=vec2(0.,dFdx(uv.y)),dy=vec2(0.,dFdy(uv.y));":""}
 vec4 sum=vec4(0.);
 for(int i=0;i<8;i++){
  vec2 at=vec2(fract(uv.x+(float(i)-3.5)*longitudeSpan/4.),uv.y);
  sum+=linearPremul(${gradientSampling?"texture2DGradEXT(tex,at,dx,dy)":"texture2D(tex,at)"});
 }
 sum/=8.;
 vec4 mean=linearPremul(texture2D(poleMean,vec2(.5,uv.y)));
 // The unique endpoint row mean also defines the exact mathematical pole.
 if(radial<.000001)meanWeight=1.;
 vec4 filtered=mix(sum,mean,meanWeight);
 vec4 color=vec4(pow(filtered.rgb/max(filtered.a,.000001),vec3(1./2.2)),filtered.a);
 vec3 normal=normalize(hit);
 float incidence=dot(normal,normalize(vec3(-.42,.5,.76)));
 float diffuse=pow(max(0.,incidence),.72)*smoothstep(-.10,.12,incidence);
 float light=.30+.70*diffuse;
 float limb=smoothstep(-.2,.3,normal.z);
 gl_FragColor=vec4(color.rgb*light,color.a*limb);
}`;
    const shader=(type,src)=>{const s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;};
    try {
      const program=gl.createProgram();gl.attachShader(program,shader(gl.VERTEX_SHADER,vs));gl.attachShader(program,shader(gl.FRAGMENT_SHADER,fs));gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error("Orbit shader link failed");
      const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]),gl.STATIC_DRAW);
      const texture=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,texture);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR_MIPMAP_LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.REPEAT);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
      const poleMean=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,poleMean);for(const axis of [gl.TEXTURE_WRAP_S,gl.TEXTURE_WRAP_T])gl.texParameteri(gl.TEXTURE_2D,axis,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
      const loc=name=>gl.getUniformLocation(program,name),lostState={value:false};
      canvas.addEventListener?.("webglcontextlost",event=>{event.preventDefault();lostState.value=true;});canvas.addEventListener?.("webglcontextrestored",()=>{lostState.value=true;});
      return {canvas,gl,program,buffer,texture,poleMean,locations:{p:gl.getAttribLocation(program,"p"),N:loc("N"),E:loc("E"),U:loc("U"),viewSize:loc("viewSize"),D:loc("D"),tex:loc("tex"),poleMean:loc("poleMean"),textureSize:loc("textureSize"),pixelAngle:loc("pixelAngle")}, uploaded:null, lostState,
        render(source,revision,width,height,view,rect={left:0,top:0,width,height}){if(this.lostState.value||gl.isContextLost()||!source)return false;const dims=powerOfTwoSize(source.width,source.height);if(this.uploaded!==revision){let image=source;if(dims.width!==source.width||dims.height!==source.height){const tmp=document.createElement("canvas");tmp.width=dims.width;tmp.height=dims.height;tmp.getContext("2d").drawImage(source,0,0,dims.width,dims.height);image=tmp;}
            gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,texture);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,true);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,image);gl.generateMipmap(gl.TEXTURE_2D);
            const meanCanvas=document.createElement("canvas");meanCanvas.width=1;meanCanvas.height=dims.height;const meanContext=meanCanvas.getContext("2d"),data=meanContext.createImageData(1,dims.height);data.data.set(rowMeans(image.getContext("2d").getImageData(0,0,dims.width,dims.height).data,dims.width,dims.height));meanContext.putImageData(data,0,0);gl.bindTexture(gl.TEXTURE_2D,poleMean);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,meanCanvas);this.uploaded=revision;}
          const dpr=Math.min(2,window.devicePixelRatio||1),targetW=Math.max(1,Math.round(width*dpr)),targetH=Math.max(1,Math.round(height*dpr));if(canvas.width!==targetW||canvas.height!==targetH){canvas.width=targetW;canvas.height=targetH;}if(this.lostState.value){this.lostState.value=false;this.uploaded=null;return false;}gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT);gl.viewport(Math.round(rect.left*dpr),Math.round((height-rect.top-rect.height)*dpr),Math.round(rect.width*dpr),Math.round(rect.height*dpr));gl.useProgram(program);gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.enableVertexAttribArray(this.locations.p);gl.vertexAttribPointer(this.locations.p,2,gl.FLOAT,false,0,0);const f=basis(view.latitude,view.longitude),short=Math.max(1,Math.min(rect.width,rect.height));
          gl.uniform3fv(this.locations.N,f.N);gl.uniform3fv(this.locations.E,f.E);gl.uniform3fv(this.locations.U,f.U);gl.uniform2f(this.locations.viewSize,rect.width/short,rect.height/short);gl.uniform1f(this.locations.D,view.distance??2.45);gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,texture);gl.uniform1i(this.locations.tex,0);gl.activeTexture(gl.TEXTURE1);gl.bindTexture(gl.TEXTURE_2D,poleMean);gl.uniform1i(this.locations.poleMean,1);gl.uniform2f(this.locations.textureSize,dims.width,dims.height);gl.uniform1f(this.locations.pixelAngle,Math.max(.000001,(view.distance-1)/(short*.36*view.distance*dpr)));gl.drawArrays(gl.TRIANGLES,0,6);return !gl.isContextLost();}};
    } catch { return null; }
  }
  window.HWPlanetOrbit={basis,unit,screenPoint,inversePoint,focusFlatCamera,distanceForTile,powerOfTwoSize,rowMeans,create};
})();
