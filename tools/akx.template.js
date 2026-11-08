/* Auxwood kitchen drawing. Loaded only when the visitor is about one screen away from the section. Built by tools/build-scene.js. */
(function(){
var root=document.getElementById('akx-kitchen');if(!root||root.classList.contains('akx'))return;
var D=__SCENE__;
var CSS='.akx{position:relative;background:#f3f0ea;direction:ltr;color:#23262b}'
+'.akx-pin{position:sticky;top:0;height:100vh;height:100svh;overflow:hidden;display:flex;align-items:center;justify-content:center;padding:12px;box-sizing:border-box}'
+'.akx-box{display:flex;flex-direction:column;width:min(100%,1560px);max-height:100%;box-sizing:border-box;padding:26px 30px 18px;background:#fff;border-radius:28px;box-shadow:0 1px 2px rgba(11,21,38,.05),0 40px 80px -40px rgba(11,21,38,.25)}'
+'.akx-frame{position:relative;align-self:center;width:min(100%,calc((100vh - 190px)*1.672));width:min(100%,calc((100svh - 190px)*1.672));aspect-ratio:1020/610;overflow:hidden;background:#fff;contain:layout paint style}'
+'.akx-stage{position:absolute;inset:0}'
+'.akx-s{position:absolute;display:block;left:0;top:0;width:100%;height:100%;visibility:hidden}'
+'.akx.is-live .akx-m{will-change:transform,opacity}'
+'.akx-rv{position:absolute;top:0;left:-8%;width:108%;height:100%;overflow:hidden;visibility:hidden;-webkit-mask-image:linear-gradient(to right,transparent,#000 7%);mask-image:linear-gradient(to right,transparent,#000 7%)}'
+'.akx-ri{position:absolute;top:0;left:7.4074%;width:92.5926%;height:100%}'
+'.akx-rv .akx-f{visibility:inherit}'
+'.akx.is-live .akx-rv,.akx.is-live .akx-ri,.akx.is-live .akx-f{will-change:transform,opacity}'
+'.akx-t{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;margin-top:12px;padding-top:10px;border-top:1px solid rgba(35,38,43,.16);opacity:0;direction:rtl;line-height:1.5}'
+'.akx-t b{display:block;font-size:12px;font-weight:700;letter-spacing:0}'
+'.akx-t i{display:block;font-style:normal;font-size:12px;opacity:.7}'
+'.akx-t small{display:block;font-size:11px;opacity:.55}'
+'.akx-t strong{display:block;font-size:16px;font-weight:400;direction:ltr;text-align:left}'
+'.akx-bar{display:block;width:96px;height:3px;margin-top:6px;border:.6px solid rgba(35,38,43,.8);background:repeating-linear-gradient(to left,rgba(35,38,43,.85) 0 16px,transparent 16px 32px)}'
+'.akx-e{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-top:10px;direction:rtl}'
+'.akx-c{margin:0;font-size:15px;line-height:1.5;opacity:.75}'
+'.akx-g{display:flex;gap:6px;margin:0;padding:0;list-style:none}'
+'.akx-g li{width:22px;height:2px;border-radius:2px;background:rgba(35,38,43,.14);transition:background-color .4s ease}'
+'.akx-g li.on{background:rgba(35,38,43,.8)}'
+'@media (max-aspect-ratio:1/1){.akx-box{padding:14px 14px 12px;border-radius:22px}.akx-frame{width:100%;height:min(104vw,calc(100vh - 210px));height:min(104vw,calc(100svh - 210px));aspect-ratio:auto}.akx-stage{inset:0 auto 0 50%;width:calc(min(104vw,100vh - 210px)*1.672);width:calc(min(104vw,100svh - 210px)*1.672);margin-left:calc(min(104vw,100vh - 210px)*-.836);margin-left:calc(min(104vw,100svh - 210px)*-.836)}}'
+'.akx.is-static .akx-pin{position:relative;height:auto}';
var st=document.createElement('style');st.textContent=CSS;document.head.appendChild(st);
root.classList.add('akx');
var VW=D.V[0],VH=D.V[1],NS='xmlns="http://www.w3.org/2000/svg"',INK=D.INK;
function vb(b){return 'viewBox="'+b.join(' ')+'" preserveAspectRatio="none" aria-hidden="true"'}
function svg(cls,b,inner){return '<svg '+NS+' class="akx-s '+cls+'" '+vb(b)+'>'+inner+'</svg>'}
function stroke(d,w,op,extra){return '<path d="'+d+'" fill="none" stroke="'+INK+'" stroke-width="'+w+'" stroke-opacity="'+op+'" stroke-linecap="round" stroke-linejoin="round"'+(extra||'')+'/>'}
var DASH=' pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="1" class="akx-d"';
/* Line version of a piece: white paper fill and ink. */
function lineMarkup(f){return f.map(function(x){return x[1]?'<path d="'+x[0]+'" fill="#fff"/>':stroke(x[0],x[2],x[3])}).join('')}
/* Finished version: colour wash and ink. */
function washMarkup(f){return f.map(function(x){return x[1]?'<path d="'+x[0]+'" fill="'+x[1]+'"'+(x[2]?' opacity="'+x[2]+'"':'')+'/>':stroke(x[0],x[2],x[3])}).join('')}
var full=[0,0,VW,VH],h='';
/* Pencil. */
h+=svg('akx-pencil',full,D.P.map(function(d){return stroke(d,1,.45,DASH)}).join('')+'<circle cx="510" cy="235" r="3.5" fill="none" stroke="'+INK+'" stroke-opacity=".45" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="1" class="akx-d"/>'
  +'<g class="akx-notes" fill="'+INK+'" fill-opacity=".6" font-size="14" text-anchor="middle" direction="rtl" style="font-family:inherit">'+D.N.map(function(n){return '<text x="'+n.x+'" y="'+n.y+'">'+n.t+'</text>'}).join('')+'</g>');
/* Raw room. */
h+=svg('akx-shell',full,D.S.map(function(d,i){return stroke(d,1.45,.92,DASH)}).join(''));
h+=svg('akx-marks akx-m',full,D.K.map(function(k){return stroke(k[0],k[1],k[2])}).join(''));
/* Pieces. */
D.Q.forEach(function(q){var b=q.b;h+='<svg '+NS+' class="akx-s akx-m akx-p" data-id="'+q.id+'" '+vb(b)+' style="left:'+(b[0]/VW*100).toFixed(3)+'%;top:'+(b[1]/VH*100).toFixed(3)+'%;width:'+(b[2]/VW*100).toFixed(3)+'%;height:'+(b[3]/VH*100).toFixed(3)+'%">'+lineMarkup(q.f)+'</svg>'});
/* Finished drawing, wiped in from the right. */
var fin=washMarkup(D.A);D.Q.forEach(function(q){fin+=washMarkup(q.f)});fin+=washMarkup(D.Z);
/* What stands in front of the people and the light is painted again on top of them. */
var front='';D.Q.forEach(function(q){if(q.id==='island'||q.id==='stools'||q.id==='pendants')front+=washMarkup(q.f)});front+=washMarkup(D.Z);
var L=D.L,lit='<defs><linearGradient id="akx-sun" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#FFF1CF" stop-opacity=".95"/><stop offset="1" stop-color="#FFF1CF" stop-opacity=".15"/></linearGradient><linearGradient id="akx-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#D9E7F1"/><stop offset="1" stop-color="#F4EEDF"/></linearGradient><radialGradient id="akx-glow"><stop offset="0" stop-color="#FFE3A0" stop-opacity=".9"/><stop offset="1" stop-color="#FFE3A0" stop-opacity="0"/></radialGradient></defs>'
+'<path d="'+L.sky+'" fill="url(#akx-sky)"/><path d="'+L.out+'" fill="#A9BA98" opacity=".8"/>'
+L.sun.map(function(d){return '<path d="'+d+'" fill="url(#akx-sun)"/>'}).join('')
+L.glow.map(function(g){return '<circle cx="'+g[0]+'" cy="'+g[1]+'" r="46" fill="url(#akx-glow)"/>'}).join('')
+'<path d="'+L.cones+'" fill="none" stroke="#B9AF87" stroke-width="1.1" stroke-dasharray="1.5 4.5"/>';
h+='<div class="akx-rv"><div class="akx-ri"><svg '+NS+' class="akx-s akx-f" '+vb(full)+'>'+fin+'</svg><svg '+NS+' class="akx-s akx-light akx-f" '+vb(full)+'>'+lit+'</svg><svg '+NS+' class="akx-s akx-people akx-f" '+vb(full)+'><path d="'+D.U+'" fill="#4A5463" fill-opacity=".72"/>'+front+'</svg></div></div>';
/* Sheet frame and dimension line. */
h+=svg('akx-sheet',full,stroke('M.6 .6H1019.4V609.4H.6Z',1,.85,DASH)+stroke('M'+D.D.x0+' '+D.D.y+'H'+D.D.x1+'M'+D.D.x0+' '+(D.D.y-5)+'V'+(D.D.y+5)+'M'+D.D.x1+' '+(D.D.y-5)+'V'+(D.D.y+5),.8,.6,DASH));
var CAP=['طرح اولیه','ساختمان خام','نصب کابینت‌ها','نقشهٔ نهایی','جنس و رنگ','نور و زندگی'],seg='';
CAP.forEach(function(){seg+='<li></li>'});
root.innerHTML='<div class="akx-pin"><div class="akx-box"><div class="akx-frame"><div class="akx-stage">'+h+'</div></div>'
+'<div class="akx-t"><div><b>آکس چوب</b><i>کابینت منحنی، مدرن و کلاسیک</i><span class="akx-bar"></span></div><div><small>کد پروژه</small><strong>AUX501</strong></div></div>'
+'<div class="akx-e"><p class="akx-c"></p><ol class="akx-g">'+seg+'</ol></div></div></div>';
var $=function(s){return root.querySelector(s)},$$=function(s){return [].slice.call(root.querySelectorAll(s))};
var pin=$('.akx-pin'),frameEl=$('.akx-frame'),stage=$('.akx-stage'),pencil=$('.akx-pencil'),notes=$('.akx-notes'),shell=$('.akx-shell'),marks=$('.akx-marks'),sheet=$('.akx-sheet'),rv=$('.akx-rv'),ri=$('.akx-ri'),light=$('.akx-light'),people=$('.akx-people'),title=$('.akx-t'),cap=$('.akx-c'),segs=$$('.akx-g li');
function clamp(v){return v<0?0:v>1?1:v}
function win(p,a,b){return clamp((p-a)/(b-a))}
/* Everything that draws itself: [element, start, end]. */
var DR=[];
$$('.akx-pencil .akx-d').forEach(function(e,i,all){var a=.005+i/all.length*.08;DR.push({el:e,a:a,b:a+.035,t:-1})});
$$('.akx-shell .akx-d').forEach(function(e,i,all){var a=.1+i/all.length*.055;DR.push({el:e,a:a,b:a+.03,t:-1})});
$$('.akx-sheet .akx-d').forEach(function(e,i){var a=.665+i*.02;DR.push({el:e,a:a,b:a+.035,t:-1})});
/* Everything that arrives: moved by the compositor only. */
var MV=$$('.akx-p').map(function(e,i){var q=D.Q[i],b=q.b,m=q.m;return{el:e,tx:m[0]/(b[2]/VW)*100,ty:m[1]/(b[3]/VH)*100,s:m[2],a:m[3],b:m[4],t:-1}});
var cur=0,raf=0,stageW=0,pinH=0,frameW=0,pan=false,lastW=innerWidth,stageNo=-1,lastRv=-1,lastLight=-1,lastPencil=-1,lastMarks=-1,lastTitle=-1,lastNotes=-1;
function measure(){stageW=stage.offsetWidth;frameW=frameEl.offsetWidth;pinH=pin.offsetHeight;pan=stageW>frameW*1.15;if(!pan)stage.style.transform=''}
/* Phones see part of the drawing at a time, so the camera follows the pieces. */
var FC=[[0,.5],[.19,.5],[.24,.31],[.31,.31],[.37,.5],[.46,.5],[.5,.62],[.55,.8],[.585,.8],[.63,.5],[1,.5]];
function focus(p){for(var i=1;i<FC.length;i++)if(p<=FC[i][0]){var t=(p-FC[i-1][0])/(FC[i][0]-FC[i-1][0]);t=t*t*(3-2*t);return FC[i-1][1]+(FC[i][1]-FC[i-1][1])*t}return .5}
function setStage(n){if(n===stageNo)return;stageNo=n;cap.textContent=CAP[n];segs.forEach(function(s,i){s.classList.toggle('on',i<=n)})}
function vis(e,on){e.style.visibility=on?'visible':'hidden'}
function draw(p){
  if(pan){var m=(stageW-frameW)/2,x=(.5-focus(p))*stageW;stage.style.transform='translate3d('+Math.max(-m,Math.min(m,x)).toFixed(1)+'px,0,0)'}
  setStage(p<.1?0:p<.2?1:p<.665?2:p<.71?3:p<.84?4:5);
  var i,q,t,s,k;
  for(i=0;i<DR.length;i++){q=DR[i];t=win(p,q.a,q.b);if(t===q.t)continue;q.t=t;q.el.setAttribute('stroke-dashoffset',(1-t).toFixed(3))}
  for(i=0;i<MV.length;i++){q=MV[i];t=win(p,q.a,q.b);if(t===q.t)continue;q.t=t;s=q.el.style;
    if(t===0){s.visibility='hidden';continue}
    k=1-t;k=k*k*k;s.visibility='visible';s.opacity=Math.min(1,t*6);
    s.transform=t===1?'none':'translate3d('+(q.tx*k).toFixed(2)+'%,'+(q.ty*k).toFixed(2)+'%,0) scale('+(1+(q.s-1)*k).toFixed(4)+')'}
  /* Pencil steps back as the ink arrives. */
  var o=p<.1?1:p<.2?1-(p-.1)/.1*.7:.3-win(p,.2,.6)*.18;if(o!==lastPencil){lastPencil=o;pencil.style.opacity=o.toFixed(3)}
  var ns=win(p,.05,.09)*(1-win(p,.2,.25));if(ns!==lastNotes){lastNotes=ns;notes.style.opacity=ns.toFixed(3)}
  var mk=win(p,.14,.2);if(mk!==lastMarks){lastMarks=mk;marks.style.opacity=mk.toFixed(3);vis(marks,mk>0)}
  var ti=win(p,.67,.71);if(ti!==lastTitle){lastTitle=ti;title.style.opacity=ti.toFixed(3)}
  /* Colour wipes in from the right; once it covers everything the line layers rest. */
  var w=win(p,.71,.83);if(w!==lastRv){lastRv=w;vis(rv,w>0);if(w>0){w=w*w*(3-2*w);var d=(1-w)*1.08;rv.style.transform='translate3d('+(d*100/1.08).toFixed(2)+'%,0,0)';ri.style.transform='translate3d('+(-d*100).toFixed(2)+'%,0,0)'}
    var done=lastRv===1;[pencil,shell].forEach(function(e){vis(e,!done)});if(done)marks.style.visibility='hidden';MV.forEach(function(m){if(done)m.el.style.visibility='hidden';else m.t=-1})}
  var l=win(p,.84,.95);if(l!==lastLight){lastLight=l;vis(light,l>0);vis(people,l>0);light.style.opacity=l.toFixed(3);people.style.opacity=win(l,.4,1).toFixed(3)}
}
/* The timeline starts as the section enters the screen, so the raw room is already drawn when it pins. */
function frame(){raf=0;var b=root.getBoundingClientRect(),en=pinH*.85,g=clamp((en-b.top)/(b.height-pinH+en));cur+=(g-cur)*.16;if(Math.abs(g-cur)<.0004)cur=g;draw(cur);if(cur!==g)raf=requestAnimationFrame(frame)}
function onScroll(){if(!raf)raf=requestAnimationFrame(frame)}
vis(pencil,1);vis(shell,1);vis(sheet,1);
/* Reduced motion or data saver: only the finished sheet, no scrolling effect. */
var c=navigator.connection;
if((window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches)||(c&&(c.saveData||/2g/.test(c.effectiveType||'')))){root.style.height='auto';root.classList.add('is-static');measure();draw(1);return}
measure();draw(0);
addEventListener('resize',function(){pinH=pin.offsetHeight;if(innerWidth===lastW)return;lastW=innerWidth;measure();onScroll()},{passive:true});
new IntersectionObserver(function(e){var live=e[0].isIntersecting;root.classList.toggle('is-live',live);
  if(live)addEventListener('scroll',onScroll,{passive:true});else removeEventListener('scroll',onScroll);
  onScroll()}).observe(root);
})();
