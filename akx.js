/* Auxwood 3D kitchen: rendered pieces land in the raw room as the visitor scrolls.
   Loaded only when the visitor is about one screen away from the section. Built by tools/build.py. */
(function(){
var root=document.getElementById('akx-kitchen');if(!root||root.classList.contains('akx'))return;
var D={"W":1920,"H":1072,"A":[2600,1201],"S":["base","coffee","fridge","island","left","upper"],"P":[{"id":"tall1","x":103,"y":278,"w":192,"h":525,"ax":4,"ay":4},{"id":"tall2","x":233,"y":279,"w":181,"h":524,"ax":200,"ay":4},{"id":"oven","x":360,"y":279,"w":170,"h":524,"ax":385,"ay":4},{"id":"base1","x":490,"y":603,"w":159,"h":199,"ax":1975,"ay":533},{"id":"base2","x":618,"y":603,"w":119,"h":199,"ax":2138,"ay":533},{"id":"base3","x":713,"y":603,"w":199,"h":200,"ax":1178,"ay":533},{"id":"base4","x":907,"y":603,"w":119,"h":200,"ax":1381,"ay":533},{"id":"base5","x":1018,"y":603,"w":115,"h":200,"ax":1504,"ay":533},{"id":"worktop","x":488,"y":523,"w":646,"h":98,"ax":1514,"ay":1023},{"id":"splash","x":527,"y":477,"w":591,"h":120,"ax":1530,"ay":820},{"id":"up1","x":508,"y":285,"w":219,"h":197,"ax":190,"ay":820},{"id":"up2","x":918,"y":285,"w":207,"h":197,"ax":413,"ay":820},{"id":"hood","x":722,"y":193,"w":190,"h":278,"ax":598,"ay":533},{"id":"fridge","x":1116,"y":279,"w":210,"h":524,"ax":559,"ay":4},{"id":"topl","x":103,"y":183,"w":427,"h":112,"ax":2125,"ay":820},{"id":"topu1","x":508,"y":193,"w":219,"h":102,"ax":590,"ay":1023},{"id":"topu2","x":918,"y":193,"w":207,"h":102,"ax":813,"ay":1023},{"id":"topf","x":1116,"y":183,"w":208,"h":112,"ax":4,"ay":1023},{"id":"topc","x":1292,"y":195,"w":486,"h":100,"ax":1024,"ay":1023},{"id":"cpanel","x":1292,"y":288,"w":466,"h":311,"ax":773,"ay":4},{"id":"cbase1","x":1292,"y":603,"w":161,"h":199,"ax":2261,"ay":533},{"id":"cbase2","x":1410,"y":603,"w":162,"h":200,"ax":1623,"ay":533},{"id":"cbase3","x":1517,"y":603,"w":182,"h":200,"ax":1789,"ay":533},{"id":"cbase4","x":1636,"y":603,"w":182,"h":199,"ax":4,"ay":820},{"id":"cworktop","x":1292,"y":595,"w":528,"h":27,"ax":862,"ay":1139},{"id":"espresso","x":1366,"y":500,"w":370,"h":111,"ax":216,"ay":1023},{"id":"shelf1","x":1325,"y":459,"w":425,"h":67,"ax":2164,"ay":1023},{"id":"shelf2","x":1325,"y":392,"w":425,"h":57,"ax":433,"ay":1139},{"id":"shelf3","x":1325,"y":316,"w":425,"h":58,"ax":4,"ay":1139},{"id":"island","x":521,"y":647,"w":881,"h":305,"ax":1243,"ay":4},{"id":"islandtop","x":509,"y":509,"w":902,"h":183,"ax":624,"ay":820},{"id":"stool1","x":592,"y":754,"w":127,"h":267,"ax":792,"ay":533},{"id":"stool2","x":900,"y":754,"w":120,"h":267,"ax":923,"ay":533},{"id":"stool3","x":1202,"y":754,"w":127,"h":267,"ax":1047,"ay":533},{"id":"pendants","x":665,"y":120,"w":590,"h":283,"ax":4,"ay":533}]},base=root.getAttribute('data-base')||'';
var CSS='.akx{position:relative;background:#f3f0ea;direction:ltr;color:#23262b}'
+'.akx-pin{position:sticky;top:0;height:100vh;height:100svh;overflow:hidden;display:flex;align-items:center;justify-content:center;padding:12px;box-sizing:border-box}'
+'.akx-box{display:flex;flex-direction:column;width:min(100%,calc((100vh - 90px)*1.7917 + 28px));width:min(100%,calc((100svh - 90px)*1.7917 + 28px));box-sizing:border-box;padding:14px 14px 10px;background:#fff;border-radius:26px;box-shadow:0 1px 2px rgba(11,21,38,.05),0 40px 80px -40px rgba(11,21,38,.25)}'
+'.akx-frame{position:relative;width:100%;aspect-ratio:2752/1536;overflow:hidden;border-radius:15px;background:#b9b5ad url(data:image/webp;base64,UklGRloAAABXRUJQVlA4IE4AAADwAwCdASogABIAPv1ipEcloqGYBABbD8T0gAAeCN0MrkiKG0tk7Z6AAPpKo3CQssLqUE7zSoekSU5+c8gtjl5wWmOkYTp3m7AaxAAAAAA=) center/100% 100%;contain:layout paint style}'
+'.akx-stage{position:absolute;inset:0}'
+'.akx-a{position:absolute;inset:0;opacity:0;background-size:100% 100%}'
+'.akx-raw{transition:opacity .25s linear}'
+'.akx-parts{position:absolute;inset:0}'
+'.akx-parts i,.akx-parts u{position:absolute;display:block;visibility:hidden;background-repeat:no-repeat}'
+'.akx-parts i{background-image:var(--akx-parts)}'
+'.akx-parts u{inset:0;background-image:var(--akx-shadows);background-size:100% '+(D.S.length*100)+'%}'
+'.akx.is-live .akx-a{will-change:opacity}'
+'.akx-e{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:9px 4px 0;direction:rtl}'
+'.akx-c{margin:0;font-size:15px;line-height:1.5;opacity:.75}'
+'.akx-g{display:flex;gap:6px;margin:0;padding:0;list-style:none}'
+'.akx-g li{width:22px;height:2px;border-radius:2px;background:rgba(35,38,43,.14);transition:background-color .4s ease}'
+'.akx-g li.on{background:rgba(35,38,43,.8)}'
+'@media (max-aspect-ratio:1/1){.akx-box{width:100%;padding:10px 10px 8px;border-radius:22px}.akx-frame{aspect-ratio:auto;height:min(104vw,calc(100vh - 110px));height:min(104vw,calc(100svh - 110px))}.akx-stage{inset:0 auto 0 50%;width:calc(min(104vw,100vh - 110px)*1.7917);width:calc(min(104vw,100svh - 110px)*1.7917);margin-left:calc(min(104vw,100vh - 110px)*-.8958);margin-left:calc(min(104vw,100svh - 110px)*-.8958)}}'
+'.akx.is-static .akx-pin{position:relative;height:auto}';
var st=document.createElement('style');st.textContent=CSS;document.head.appendChild(st);
root.classList.add('akx');
var CAP=['ساختمان خام','نصب کابینت‌ها','کافی‌بار','جزیره و سینک','آشپزخانهٔ کامل'],seg='';
CAP.forEach(function(){seg+='<li></li>'});
root.innerHTML='<div class="akx-pin"><div class="akx-box"><div class="akx-frame"><div class="akx-stage"><div class="akx-a akx-raw"></div><div class="akx-parts"></div><div class="akx-a akx-room"></div></div></div><div class="akx-e"><p class="akx-c"></p><ol class="akx-g">'+seg+'</ol></div></div></div>';
var $=function(s){return root.querySelector(s)};
var pin=$('.akx-pin'),frameEl=$('.akx-frame'),stage=$('.akx-stage'),raw=$('.akx-raw'),room=$('.akx-room'),parts=$('.akx-parts'),cap=$('.akx-c'),segs=[].slice.call(root.querySelectorAll('.akx-g li'));
/* How each piece arrives: start offset (share of the stage width, height), start scale, scroll window, fade speed. */
var M={tall1:[-.34,0,1,.04,.1],tall2:[-.34,0,1,.06,.12],oven:[-.3,0,1,.08,.14],
base1:[0,.62,1.1,.12,.18],base2:[0,.62,1.1,.135,.195],base3:[0,.62,1.1,.15,.21],base4:[0,.62,1.1,.165,.225],base5:[0,.62,1.1,.18,.24],
worktop:[0,-.3,1,.2,.25],splash:[0,0,1,.24,.27,1.2],fridge:[.4,0,1,.26,.32],
up1:[0,-.6,1,.31,.37],up2:[0,-.6,1,.33,.39],hood:[0,-.7,1,.35,.41],
topl:[0,-.45,1,.39,.44],topu1:[0,-.45,1,.41,.46],topu2:[0,-.45,1,.42,.47],topf:[0,-.45,1,.43,.48],
cpanel:[.35,0,1,.47,.52],cbase1:[0,.6,1.1,.5,.55],cbase2:[0,.6,1.1,.512,.562],cbase3:[0,.6,1.1,.524,.574],cbase4:[0,.6,1.1,.536,.586],
cworktop:[0,-.3,1,.55,.59],topc:[0,-.45,1,.57,.61],shelf1:[.4,0,1,.6,.65],shelf2:[.4,0,1,.62,.67],shelf3:[.4,0,1,.64,.69],espresso:[0,.2,1.15,.65,.69],
island:[0,.72,1.22,.68,.75],islandtop:[0,-.4,1,.73,.77],stool1:[0,.35,1.08,.76,.79],stool2:[0,.35,1.08,.772,.802],stool3:[0,.35,1.08,.784,.814],
pendants:[0,-.45,1,.79,.83],tree:[-.3,.1,1.05,.81,.85]};
/* Paint order: faces a piece hides from the camera lean towards the centre of the picture and towards
   the horizon, so whatever sits closer to them goes on top and covers them, as it does in the real room. */
var Z=['splash','topl','topc','topf','topu1','topu2','cpanel','shelf3','shelf2','shelf1','cbase4','cbase3','cbase2','cbase1','cworktop','fridge','tall1','tall2','oven','up1','up2','base1','base2','base3','base5','base4','worktop','espresso','hood','island','islandtop','stool1','stool2','stool3','pendants'];
/* When each group's shadow settles on the raw room. */
var SW={left:[.1,.14],base:[.2,.25],fridge:[.3,.33],upper:[.37,.48],coffee:[.64,.7],island:[.75,.79]};
var Q=[],cur=0,raf=0,ready=false,lastRoom=-1,stageNo=-1,pan=false,stageW=0,pinH=0,frameW=0,lastW=innerWidth;
function clamp(v){return v<0?0:v>1?1:v}
function size(){return innerWidth<800||stage.offsetWidth*Math.min(devicePixelRatio||1,2)<=1100?'s':'l'}
function fetchImg(name,sized,done,failed){var i=new Image(),u=base+name+(sized?'-'+size():'')+'.webp';i.fetchPriority='low';i.decoding='async';
  i.onerror=function(){if(failed)failed()};
  i.onload=function(){var ok=function(){done('url('+u+')')};if(i.decode)i.decode().then(ok,ok);else ok()};
  i.src=u}
/* If an image cannot be fetched, the section steps aside instead of showing a broken kitchen. */
function giveUp(){ready=false;removeEventListener('scroll',onScroll);root.style.display='none'}
function build(){var W=D.W,H=D.H,AW=D.A[0],AH=D.A[1];
  D.S.forEach(function(g,i){var e=document.createElement('u'),w=SW[g];e.style.backgroundPosition='0 '+(D.S.length>1?(i/(D.S.length-1)*100).toFixed(3):0)+'%';parts.appendChild(e);Q.push({el:e,tx:0,ty:0,s:1,a:w[0],b:w[1],t:-1,f:1,wc:0})});
  D.P.slice().sort(function(a,b){return Z.indexOf(a.id)-Z.indexOf(b.id)}).forEach(function(p){var m=M[p.id];if(!m)return;var e=document.createElement('i'),w=p.w/W,h=p.h/H;
    e.style.cssText='left:'+(p.x/W*100).toFixed(3)+'%;top:'+(p.y/H*100).toFixed(3)+'%;width:'+(w*100).toFixed(3)+'%;height:'+(h*100).toFixed(3)+'%;background-size:'+(AW/p.w*100).toFixed(3)+'% '+(AH/p.h*100).toFixed(3)+'%;background-position:'+(p.ax/(AW-p.w)*100).toFixed(3)+'% '+(p.ay/(AH-p.h)*100).toFixed(3)+'%';
    parts.appendChild(e);Q.push({el:e,tx:m[0]/w*100,ty:m[1]/h*100,s:m[2],a:m[3],b:m[4],t:-1,f:m[5]||6,wc:0})})}
function measure(){stageW=stage.offsetWidth;frameW=frameEl.offsetWidth;pinH=pin.offsetHeight;pan=stageW>frameW*1.15;if(!pan)stage.style.transform=''}
/* Phones see part of the kitchen at a time, so the camera follows the pieces. */
var F=[[0,.42],[.04,.12],[.12,.2],[.2,.37],[.26,.45],[.3,.6],[.36,.33],[.42,.4],[.48,.62],[.54,.76],[.66,.76],[.72,.5],[1,.5]];
function focus(p){for(var i=1;i<F.length;i++)if(p<=F[i][0]){var t=(p-F[i-1][0])/(F[i][0]-F[i-1][0]);t=t*t*(3-2*t);return F[i-1][1]+(F[i][1]-F[i-1][1])*t}return .5}
function setStage(n){if(n===stageNo)return;stageNo=n;cap.textContent=CAP[n];segs.forEach(function(s,i){s.classList.toggle('on',i<=n)})}
function draw(p){
  setStage(p<.04?0:p<.47?1:p<.68?2:p<.84?3:4);
  if(pan){var m=(stageW-frameW)/2,x=(.5-focus(p))*stageW;stage.style.transform='translate3d('+Math.max(-m,Math.min(m,x)).toFixed(1)+'px,0,0)'}
  if(!ready)return;
  var r=clamp((p-.84)/.09);
  for(var i=0;i<Q.length;i++){var q=Q[i],t=clamp((p-q.a)/(q.b-q.a));if(t===q.t)continue;q.t=t;var s=q.el.style,moving=t>0&&t<1;
    if(moving!==q.wc){q.wc=moving;s.willChange=moving?'transform,opacity':'auto'}
    if(t===0){s.visibility='hidden';continue}
    var k=1-t;k=k*k*k;s.visibility='visible';s.opacity=Math.min(1,t*q.f);
    s.transform=t===1?'none':'translate3d('+(q.tx*k).toFixed(2)+'%,'+(q.ty*k).toFixed(2)+'%,0) scale('+(1+(q.s-1)*k).toFixed(4)+')'}
  if(r!==lastRoom){lastRoom=r;room.style.opacity=r;var hide=r===1?'hidden':'visible';parts.style.visibility=hide;raw.style.visibility=hide}}
function frame(){raf=0;var b=root.getBoundingClientRect(),g=clamp(-b.top/(b.height-pinH));cur+=(g-cur)*.16;if(Math.abs(g-cur)<.0004)cur=g;draw(cur);if(cur!==g)raf=requestAnimationFrame(frame)}
function onScroll(){if(!raf)raf=requestAnimationFrame(frame)}
function load(){fetchImg('raw',true,function(u){raw.style.backgroundImage=u;raw.style.opacity=1;
  fetchImg('parts',true,function(v){root.style.setProperty('--akx-parts',v);
    fetchImg('room',true,function(w){room.style.backgroundImage=w;build();ready=true;draw(cur);
      fetchImg('shadows',false,function(x){root.style.setProperty('--akx-shadows',x)})},giveUp)},giveUp)},giveUp)}
/* Reduced motion or data saver: only the finished kitchen, no scrolling effect. */
var c=navigator.connection;
if((window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches)||(c&&(c.saveData||/2g/.test(c.effectiveType||'')))){root.style.height='auto';root.classList.add('is-static');setStage(4);
  fetchImg('room',true,function(w){room.style.backgroundImage=w;room.style.opacity=1},giveUp);return}
measure();setStage(0);
addEventListener('resize',function(){pinH=pin.offsetHeight;if(innerWidth===lastW)return;lastW=innerWidth;measure();onScroll()},{passive:true});
new IntersectionObserver(function(e){var live=e[0].isIntersecting;root.classList.toggle('is-live',live);
  if(live)addEventListener('scroll',onScroll,{passive:true});else removeEventListener('scroll',onScroll);
  onScroll()}).observe(root);
/* Never compete with the page's own images: wait for its load event, or 2.5 seconds at most. */
if(document.readyState==='complete')load();
else{var once=function(){if(once){once=null;load()}};addEventListener('load',function(){if(once)once()});setTimeout(function(){if(once)once()},2500)}
})();
