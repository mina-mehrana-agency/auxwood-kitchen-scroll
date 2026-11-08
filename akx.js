/* Auxwood scroll kitchen. Loaded only when the visitor is about one screen away from the section. */
(function(){
var root=document.getElementById('akx-kitchen');if(!root||root.classList.contains('akx'))return;
var CSS='.akx{position:relative;background:#2a2a2a;direction:ltr}'
+'.akx-pin{position:sticky;top:0;height:100vh;height:100svh;overflow:hidden;display:flex;align-items:center;justify-content:center;contain:layout paint style}'
+'.akx-stage{position:relative;flex:none;aspect-ratio:2752/1536;width:max(100vw,179.17vh);width:max(100vw,179.17svh);background:#8f8f8d url(data:image/webp;base64,UklGRloAAABXRUJQVlA4IE4AAAAwBACdASogABIAPvFcm0akoqEYBgBLDwT0gAAoXOBNZxncezBzU4obbjAA/R0XZSLBHyOgrbF6Rhkh5sPL065nYmuvDypvLMtvVwAAAAA=) center/100% 100%}'
+'.akx-a{position:absolute;inset:0;opacity:0;background-size:100% 100%}'
+'.akx-raw{transition:opacity .25s linear}'
+'.akx-parts{position:absolute;inset:0}'
+'.akx-parts i,.akx-island,.akx-shadow{position:absolute;display:block;visibility:hidden;background-repeat:no-repeat}'
+'.akx-parts i{background-image:var(--akx-room)}'
+'.akx-island{left:32.85%;top:51.63%;width:37.57%;height:44.73%;background-size:100% 100%}'
+'.akx-shadow{left:18.17%;top:50.78%;width:63.59%;height:49.22%;background-size:100% 100%}'
+'.akx-parts b{position:absolute;display:block}'
+'.akx-parts u{position:absolute;display:block;visibility:hidden;background:rgba(0,0,0,.3);box-shadow:0 0 3.4em 1.6em rgba(0,0,0,.3)}'
+'.akx.is-live .akx-parts i,.akx.is-live .akx-island,.akx.is-live .akx-a{will-change:transform,opacity}'
+'.akx-hint{position:absolute;left:50%;bottom:22px;width:44px;height:44px;margin-left:-22px;border-radius:50%;background:rgba(30,30,30,.55);transition:opacity .2s linear;animation:akx-b 1.5s ease-in-out infinite;pointer-events:none}'
+'.akx-hint svg{display:block;width:100%;height:100%}'
+'.akx.is-past .akx-hint{opacity:0;animation:none}'
+'@keyframes akx-b{50%{transform:translateY(7px)}}'
+'@media (max-aspect-ratio:1/1){.akx-stage{width:calc(min(120vw,100vh)*1.7917);width:calc(min(120vw,100svh)*1.7917)}}'
+'.akx.is-static .akx-pin{position:relative;height:100%;display:block}'
+'.akx.is-static .akx-stage{width:100%}'
+'.akx.is-static .akx-a{opacity:1}'
+'.akx.is-static .akx-island,.akx.is-static .akx-shadow{visibility:visible}'
+'.akx.is-static .akx-hint{display:none}';
var st=document.createElement('style');st.textContent=CSS;document.head.appendChild(st);
root.classList.add('akx');
root.innerHTML='<div class="akx-pin"><div class="akx-stage"><div class="akx-a akx-raw"></div><div class="akx-parts"></div><div class="akx-a akx-room"></div><div class="akx-shadow"></div><div class="akx-island"></div></div><div class="akx-hint" aria-hidden="true"><svg viewBox="0 0 44 44"><path d="M14 19l8 8 8-8" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg></div></div>';
var W=2752,H=1536,base=root.getAttribute('data-base')||'',
pin=root.querySelector('.akx-pin'),stage=root.querySelector('.akx-stage'),
raw=root.querySelector('.akx-raw'),room=root.querySelector('.akx-room'),parts=root.querySelector('.akx-parts'),
island=root.querySelector('.akx-island'),shadow=root.querySelector('.akx-shadow');
/* Soft shadow behind each group: box in master pixels, scroll window. */
var S=[[525,195,925,1050,.2,.26],[965,815,1505,995,.34,.4],[1420,285,1795,985,.48,.53],[1010,255,1310,495,.56,.62],[1835,265,2200,1000,.65,.7]];
/* Each piece: outline in master pixels, start offset (share of stage width, height), start scale, scroll window,
   and optional patches [x0,y0,x1,y1,background] over pixels of neighbours that land later. */
var P=[
[[1400,275,1530,255,1680,225,1815,252,1815,1015,1680,1040,1525,1005,1527,766,1530,736,1400,743],.5,0,1,.4,.53,[[1744,225,1818,1040,'linear-gradient(#cfd4d6 4%,#d0d6d9 26%,#d6dadc 37%,#cbcdcf 52%,#c8cbcd 63%,#adb4b8 93%)'],[1398,484,1504,550,'linear-gradient(#a0b2b9,#a8b7be)']]],
[[1815,245,1985,205,2145,190,2218,176,2218,1080,1815,1017,1815,958,1748,937,1748,762,1815,768,1815,587,1748,590,1748,568,1815,565,1815,497,1748,501,1748,479,1815,472,1815,405,1748,412,1748,298,1815,283],.36,0,1,.58,.7],
[[498,756,572,760,945,746,947,1060,572,1170,498,1130],0,.72,1.12,.06,.2],
[[498,152,572,105,947,170,945,746,572,760,498,756],0,-.72,1,.12,.26],
[[943,799,1144,787,1144,1073,943,1110],0,.55,1.18,.22,.33],
[[1144,787,1403,773,1403,1027,1144,1073],0,.55,1.18,.25,.36],
[[1403,773,1529,766,1524,1005,1403,1027],0,.55,1.18,.28,.39],
[[943,772,1527,736,1530,767,943,801],0,-.36,1,.34,.44],
[[990,212,1040,209,1100,208,1160,210,1220,218,1270,228,1310,243,1326,258,1326,490,990,472],0,-.46,1,.48,.58],
[[947,464,1500,490,1500,540,1400,546,947,529],0,-.3,1,.52,.62]
],
Q=[],cur=0,raf=0,ready=false,lastRoom=-1,lastShadow=-1,past=false,pan=false,stageW=0,pinH=0,pinW=0,lastW=innerWidth;
function clamp(v){return v<0?0:v>1?1:v}
function size(){return innerWidth<800||stage.offsetWidth*Math.min(devicePixelRatio||1,2)<=1400?'s':'l'}
function fetchImg(name,done,failed){var i=new Image(),u=base+name+(name==='shadow'?'':'-'+size())+'.webp';i.fetchPriority='low';i.decoding='async';
  i.onerror=function(){if(failed)failed()};
  i.onload=function(){var ok=function(){done('url('+u+')')};if(i.decode)i.decode().then(ok,ok);else ok()};
  i.src=u}
/* If an image cannot be fetched, the section steps aside instead of showing a broken kitchen. */
function giveUp(){ready=false;removeEventListener('scroll',onScroll);root.style.display='none'}
function box(x0,y0,x1,y1){return 'left:'+(x0/W*100).toFixed(3)+'%;top:'+(y0/H*100).toFixed(3)+'%;width:'+((x1-x0)/W*100).toFixed(3)+'%;height:'+((y1-y0)/H*100).toFixed(3)+'%;'}
function build(){S.forEach(function(d){var e=document.createElement('u');e.style.cssText=box(d[0],d[1],d[2],d[3]);parts.appendChild(e);Q.push({el:e,tx:0,ty:0,s:1,a:d[4],b:d[5],t:-1,f:1})});
  P.forEach(function(d){var a=d[0],x0=W,x1=0,y0=H,y1=0,k,c=[];
    for(k=0;k<a.length;k+=2){x0=Math.min(x0,a[k]);x1=Math.max(x1,a[k]);y0=Math.min(y0,a[k+1]);y1=Math.max(y1,a[k+1])}
    for(k=0;k<a.length;k+=2)c.push(((a[k]-x0)/(x1-x0)*100).toFixed(2)+'% '+((a[k+1]-y0)/(y1-y0)*100).toFixed(2)+'%');
    var w=(x1-x0)/W,h=(y1-y0)/H,x=x0/W,y=y0/H,e=document.createElement('i');
    e.style.cssText=box(x0,y0,x1,y1)+'background-size:'+(100/w).toFixed(3)+'% '+(100/h).toFixed(3)+'%;background-position:'+(x/(1-w)*100).toFixed(3)+'% '+(y/(1-h)*100).toFixed(3)+'%;clip-path:polygon('+c.join(',')+')';
    (d[6]||[]).forEach(function(f){var b=document.createElement('b');b.style.cssText='left:'+((f[0]-x0)/(x1-x0)*100).toFixed(2)+'%;top:'+((f[1]-y0)/(y1-y0)*100).toFixed(2)+'%;width:'+((f[2]-f[0])/(x1-x0)*100).toFixed(2)+'%;height:'+((f[3]-f[1])/(y1-y0)*100).toFixed(2)+'%;background:'+f[4];e.appendChild(b)});
    parts.appendChild(e);Q.push({el:e,tx:d[1]/w*100,ty:d[2]/h*100,s:d[3],a:d[4],b:d[5],t:-1,f:6})});
  Q.push({el:island,tx:0,ty:134.14,s:1.28,a:.76,b:.92,t:-1,f:6})}
function measure(){stageW=stage.offsetWidth;pinW=pin.offsetWidth;pinH=pin.offsetHeight;pan=stageW>pinW*1.25;stage.style.fontSize=stageW/100+'px';if(!pan)stage.style.transform=''}
/* Phones see part of the kitchen at a time, so the camera follows the pieces. */
var F=[[0,.3],[.24,.3],[.34,.44],[.46,.55],[.58,.6],[.66,.72],[.74,.72],[.86,.516],[1,.516]];
function focus(p){for(var i=1;i<F.length;i++)if(p<=F[i][0]){var t=(p-F[i-1][0])/(F[i][0]-F[i-1][0]);t=t*t*(3-2*t);return F[i-1][1]+(F[i][1]-F[i-1][1])*t}return .516}
function draw(p){
  var was=past;past=p>.015;if(past!==was)root.classList.toggle('is-past',past);
  if(pan){var m=(stageW-pinW)/2,x=(.5-focus(p))*stageW;stage.style.transform='translate3d('+Math.max(-m,Math.min(m,x)).toFixed(1)+'px,0,0)'}
  if(!ready)return;
  for(var i=0;i<Q.length;i++){var q=Q[i],t=clamp((p-q.a)/(q.b-q.a));if(t===q.t)continue;q.t=t;var s=q.el.style;
    if(t===0){s.visibility='hidden';continue}
    var k=1-t;k=k*k*k;s.visibility='visible';s.opacity=Math.min(1,t*q.f);
    s.transform='translate3d('+(q.tx*k).toFixed(2)+'%,'+(q.ty*k).toFixed(2)+'%,0) scale('+(1+(q.s-1)*k).toFixed(4)+')'}
  var r=clamp((p-.68)/.1);if(r!==lastRoom){lastRoom=r;room.style.opacity=r;parts.style.visibility=r===1?'hidden':'visible'}
  var d=clamp((p-.84)/.08);if(d!==lastShadow){lastShadow=d;shadow.style.visibility=d?'visible':'hidden';shadow.style.opacity=d}}
function frame(){raf=0;var b=root.getBoundingClientRect(),g=clamp(-b.top/(b.height-pinH));cur+=(g-cur)*.16;if(Math.abs(g-cur)<.0004)cur=g;draw(cur);if(cur!==g)raf=requestAnimationFrame(frame)}
function onScroll(){if(!raf)raf=requestAnimationFrame(frame)}
function load(){fetchImg('raw',function(u){raw.style.backgroundImage=u;raw.style.opacity=1;
  fetchImg('room',function(v){root.style.setProperty('--akx-room',v);room.style.backgroundImage=v;
    fetchImg('island',function(w){island.style.backgroundImage=w;build();ready=true;draw(cur);fetchImg('shadow',function(x){shadow.style.backgroundImage=x})},giveUp)},giveUp)},giveUp)}
/* Reduced motion or data saver: only the finished kitchen, no scrolling effect. */
var c=navigator.connection;
if((window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches)||(c&&(c.saveData||/2g/.test(c.effectiveType||'')))){root.style.height='auto';root.style.aspectRatio='2752/1536';root.classList.add('is-static');
  fetchImg('room',function(v){room.style.backgroundImage=v;raw.style.display='none'},giveUp);
  fetchImg('island',function(w){island.style.backgroundImage=w});fetchImg('shadow',function(x){shadow.style.backgroundImage=x});
  return}
measure();
addEventListener('resize',function(){pinH=pin.offsetHeight;if(innerWidth===lastW)return;lastW=innerWidth;measure();Q.forEach(function(q){q.t=-1});lastRoom=-1;lastShadow=-1;onScroll()},{passive:true});
new IntersectionObserver(function(e){var live=e[0].isIntersecting;root.classList.toggle('is-live',live);
  if(live)addEventListener('scroll',onScroll,{passive:true});else removeEventListener('scroll',onScroll);
  onScroll()}).observe(root);
/* Never compete with the page's own images: wait for its load event, or 2.5 seconds at most. */
if(document.readyState==='complete')load();
else{var once=function(){if(once){once=null;load()}};addEventListener('load',function(){if(once)once()});setTimeout(function(){if(once)once()},2500)}
})();
