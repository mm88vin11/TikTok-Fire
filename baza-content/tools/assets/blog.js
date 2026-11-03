/* Блог БАЗЫ: прогресс чтения, активный пункт оглавления, Яндекс Метрика после согласия на куки.
   Вставьте номер счётчика в METRIKA_ID (тот же, что в window.BAZA.metrika на сайте). */
(function(){var METRIKA_ID=null;
document.addEventListener("DOMContentLoaded",function(){
var bar=document.querySelector(".prog i"),art=document.querySelector(".prose");
var links=[].slice.call(document.querySelectorAll(".toc a"));
var heads=links.map(function(a){return document.getElementById(decodeURIComponent(a.getAttribute("href").slice(1)))});
function on(){if(bar&&art){var r=art.getBoundingClientRect(),h=r.height-innerHeight;bar.style.width=Math.min(100,Math.max(0,-r.top/(h>0?h:1)*100))+"%"}
var k=-1;heads.forEach(function(h,i){if(h&&h.getBoundingClientRect().top<140)k=i});links.forEach(function(a,i){a.classList.toggle("on",i===k)})}
addEventListener("scroll",on,{passive:true});on();});
try{if(!METRIKA_ID||localStorage.getItem("baza-consent")!=="all")return}catch(e){return}
(function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};m[i].l=1*new Date;k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)})(window,document,"script","https://mc.yandex.ru/metrika/tag.js","ym");
ym(METRIKA_ID,"init",{clickmap:true,trackLinks:true,accurateTrackBounce:true});})();
