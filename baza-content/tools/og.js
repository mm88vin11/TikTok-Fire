// Рисует обложки для соцсетей 1200x630 для каждой статьи: node tools/og.js <папка_сайта>
const {chromium}=require('playwright');const fs=require('fs'),path=require('path'),http=require('http');
const site=process.argv[2];const list=JSON.parse(fs.readFileSync(path.join(__dirname,'og-list.json'),'utf8'));
const out=path.join(site,'assets/blog/og');fs.mkdirSync(out,{recursive:true});
const srv=http.createServer((q,r)=>{const f=path.join(site,decodeURIComponent(q.url.split('?')[0]));if(!fs.existsSync(f)){r.writeHead(404);return r.end()}
r.writeHead(200,{'content-type':f.endsWith('.woff2')?'font/woff2':f.endsWith('.webp')?'image/webp':'text/html'});fs.createReadStream(f).pipe(r)}).listen(8767,async()=>{
const b=await chromium.launch();const p=await b.newPage({viewport:{width:1200,height:630}});
const esc=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;');
for(const a of list){const t=a.h1;const fs_=t.length>70?52:t.length>48?60:70;
const html=`<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:O;font-weight:600;src:url(/assets/fonts/onest-cyrillic-600-normal.woff2)}@font-face{font-family:O;font-weight:600;src:url(/assets/fonts/onest-latin-600-normal.woff2);unicode-range:U+0000-00FF}
@font-face{font-family:O;font-weight:400;src:url(/assets/fonts/onest-cyrillic-400-normal.woff2)}@font-face{font-family:O;font-weight:400;src:url(/assets/fonts/onest-latin-400-normal.woff2);unicode-range:U+0000-00FF}
*{margin:0;box-sizing:border-box}body{width:1200px;height:630px;font-family:O;background:radial-gradient(120% 140% at 100% 0%,#fff 0%,${a.tint} 60%);position:relative;overflow:hidden;color:#0B0B0D}
.l{position:absolute;left:64px;top:56px;width:640px;height:518px;display:flex;flex-direction:column}
.chip{align-self:flex-start;background:#fff;border-radius:99px;padding:10px 22px;font-size:24px;box-shadow:0 2px 12px rgba(0,0,0,.06)}
h1{margin-top:28px;font-weight:600;font-size:${fs_}px;line-height:1.05;letter-spacing:-.035em}
.f{margin-top:auto;display:flex;align-items:center;gap:16px;font-size:24px}.f img{width:60px;height:60px;border-radius:50%;background:#fff}.f b{font-weight:600}.f span{color:#6E6E78}
.o{position:absolute;right:40px;top:46%;transform:translateY(-50%) rotate(-4deg);width:390px;height:390px;object-fit:contain;filter:drop-shadow(0 30px 40px rgba(30,30,80,.2))}
.m{position:absolute;right:56px;bottom:44px;display:flex;align-items:center;gap:10px;font-weight:600;font-size:26px}.m img{width:44px}
</style></head><body><div class="l"><div class="chip">${esc(a.catname)}</div><h1>${esc(t)}</h1>
<div class="f"><img src="/assets/img/lg-badge.webp"><div><b>${a.lang=='ru'?'Владислав Мирошниченко':'Vladislav Miroshnichenko'}</b><br><span>${a.lang=='ru'?'основатель студии БАЗА':'founder of BAZA'}</span></div></div></div>
<img class="o" src="/assets/img/${a.hero}.webp"><div class="m"><img src="/assets/img/lg-mark.webp">bazadigital.ru</div></body></html>`;
fs.writeFileSync(path.join(site,'_og.html'),html);await p.goto('http://localhost:8767/_og.html');await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(60);
await p.screenshot({path:path.join(out,`${a.lang}-${a.slug}.jpg`),type:'jpeg',quality:86});}
fs.unlinkSync(path.join(site,'_og.html'));await b.close();srv.close();console.log('og',list.length);});
