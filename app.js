const $=s=>document.querySelector(s);
let state={scope:"global",period:"24h",data:null};
const fa=n=>new Intl.NumberFormat("en-US").format(Number(n||0));
function dateLabel(s){if(!s)return"نامشخص";return new Date(s).toLocaleString("fa-IR",{dateStyle:"medium",timeStyle:"short"});}
function render(){
 const d=state.data;if(!d){$("#status").textContent="داده‌ای دریافت نشد. پس از اجرای اولین GitHub Action، صفحه را تازه‌سازی کن.";return;}
 const rows=(((d.rankings||{})[state.scope]||{})[state.period]||[]);
 $("#status").textContent=rows.length?`${rows.length} پروژه · مرتب‌شده بر اساس رشد ستاره‌ها`:"برای این بازه هنوز داده کافی ثبت نشده است.";
 $("#projects").innerHTML=rows.slice(0,20).map((p,i)=>`<article class="project ${p.repeated?"duplicate":""}">
 <div class="project-top"><span class="rank">${i+1}</span><div class="project-main"><div class="repo-name"><a href="${p.html_url}" target="_blank" rel="noopener">${esc(p.full_name)}</a></div><div class="owner">${esc(p.language||"Open Source")} · ${fa(p.stars)} ستاره کل</div></div><div class="growth">+${fa(p.growth)} ★</div></div>
 <p class="description">${esc(p.description_fa||p.description||"توضیحی برای این مخزن ثبت نشده است.")}</p>
 <div class="tags">${p.repeated?'<span class="tag red">تکراری در گزارش‌های قبلی</span>': '<span class="tag">تازه در فهرست</span>'}<span class="tag">${esc(p.language||"نامشخص")}</span>${(p.topics||[]).slice(0,2).map(t=>`<span class="tag">${esc(t)}</span>`).join("")}</div>
 <div class="project-foot"><span>آخرین به‌روزرسانی: ${dateLabel(p.updated_at)}</span><a href="${p.html_url}" target="_blank" rel="noopener">مشاهده در GitHub ↗</a></div></article>`).join("")||'<div class="empty">هنوز Snapshot کافی برای این رتبه‌بندی وجود ندارد.</div>';
 $("#tracked").textContent=fa(d.tracked_count);$("#new-count").textContent=fa(d.new_count);$("#history-days").textContent=fa((d.history||[]).length);$("#updated").textContent="آخرین برداشت: "+dateLabel(d.generated_at);
 renderHistory(d.history||[]);
}
function renderHistory(h){const el=$("#history-chart");if(h.length<2){el.innerHTML="<p>برای نمودار روند، حداقل دو برداشت روزانه لازم است. این بخش با اجرای زمان‌بندی‌شده تکمیل می‌شود.</p>";return;}
 const a=h.slice(-14),max=Math.max(1,...a.map(x=>x.tracked_count||0));el.innerHTML='<div class="chart-bars">'+a.map(x=>`<div class="bar" style="height:${Math.max(5,(x.tracked_count/max)*90)}%"><span>${new Date(x.date).toLocaleDateString("fa-IR",{day:"numeric",month:"numeric"})}</span></div>`).join("")+'</div>';}
function esc(s){return String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
document.querySelectorAll("[data-scope]").forEach(b=>b.addEventListener("click",()=>{document.querySelectorAll("[data-scope]").forEach(x=>x.classList.toggle("active",x===b));state.scope=b.dataset.scope;render();}));
document.querySelectorAll("[data-period]").forEach(b=>b.addEventListener("click",()=>{document.querySelectorAll("[data-period]").forEach(x=>x.classList.toggle("active",x===b));state.period=b.dataset.period;render();}));
async function load(){ $("#status").textContent="در حال دریافت آخرین گزارش…";try{const r=await fetch("data/latest.json?ts="+Date.now(),{cache:"no-store"});if(!r.ok)throw Error("missing");state.data=await r.json();render();}catch(e){$("#status").innerHTML="هنوز گزارشی منتشر نشده است. فایل <b>data/latest.json</b> پس از اجرای اولین گردش‌کار ساخته می‌شود.";}}
$("#refresh").addEventListener("click",load);load();
if("serviceWorker"in navigator)window.addEventListener("load",()=>navigator.serviceWorker.register("./sw.js").catch(()=>{}));
