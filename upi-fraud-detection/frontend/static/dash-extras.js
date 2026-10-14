/* Dashboard extras: screenshot scanner + admin profile popups */
(function(){
const $=s=>document.querySelector(s);
const esc=t=>String(t).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const inr=n=>'₹'+Number(n).toLocaleString('en-IN',{maximumFractionDigits:2});
let lastFocus=null;
function open(id){lastFocus=document.activeElement;$(id).classList.remove('hidden');const f=$(id).querySelector('button,input');if(f)f.focus()}
function close(m){m.classList.add('hidden');if(lastFocus)lastFocus.focus()}
document.querySelectorAll('.modal').forEach(m=>{
  m.addEventListener('click',e=>{if(e.target===m||e.target.hasAttribute('data-close'))close(m)})});
document.addEventListener('keydown',e=>{if(e.key==='Escape')document.querySelectorAll('.modal:not(.hidden)').forEach(close)});

/* ---------- Admin profile ---------- */
$('#adminBtn').addEventListener('click',async()=>{open('#adminModal');
  try{const r=await fetch('/api/admin/profile');if(!r.ok)throw 0;const a=await r.json();const st=a.stats;
    const ini=(a.name||'A').trim().split(/\s+/).map(w=>w[0]).join('').slice(0,2).toUpperCase();
    const up=a.uptime_minutes>=60?Math.floor(a.uptime_minutes/60)+' h '+a.uptime_minutes%60+' min':a.uptime_minutes+' min';
    $('#adminBody').innerHTML=`<div class="who"><div class="avatar">${esc(ini)}</div><div><b>${esc(a.name)}</b><span class="muted">${esc(a.role)}</span></div></div>
     <dl class="kv"><dt>Email</dt><dd>${esc(a.email)}</dd><dt>Phone</dt><dd>${esc(a.phone)}</dd><dt>Organization</dt><dd>${esc(a.organization)}</dd><dt>Access</dt><dd>${esc(a.access)}</dd><dt>Server uptime</dt><dd>${up}</dd><dt>Version</dt><dd>${esc(a.version)}</dd></dl>
     <div class="mini"><div><b>${st.wallet_users}</b><span>Wallet users</span></div><div><b>${st.payments}</b><span>Payments</span></div><div><b>${st.flagged_payments}</b><span>Flagged</span></div>
     <div><b>${st.blocked_payments}</b><span>Blocked</span></div><div><b>${st.reported_ids}</b><span>Reported IDs</span></div><div><b>2</b><span>ML models</span></div></div>`
  }catch{$('#adminBody').innerHTML='<p class="high">Could not load profile. Check the backend.</p>'}});

/* ---------- Screenshot scanner (OCR in the browser) ---------- */
let worker=null,libP=null;
function loadLib(){return libP||(libP=new Promise((res,rej)=>{if(window.Tesseract)return res();const s=document.createElement('script');s.src='/ocr/tesseract.min.js';s.onload=res;s.onerror=()=>rej(new Error('Reader failed to load'));document.head.appendChild(s)}))}
async function getWorker(){if(worker)return worker;await loadLib();
  worker=await Tesseract.createWorker('eng',1,{workerPath:'/ocr/worker.min.js',corePath:'/ocr/tesseract-core-simd-lstm.wasm.js',langPath:'/ocr/',gzip:true,
   logger:m=>{if(m.status==='recognizing text')$('#scanBar i').style.width=Math.round(m.progress*100)+'%'}});
  await worker.setParameters({tessedit_pageseg_mode:'11',preserve_interword_spaces:'1'});return worker}
function parseShot(raw){const t=raw.replace(/[ \t]*@[ \t]*/g,'@');const o={amt:'',upi:'',ref:'',date:'',status:''};
 const ups=[...t.matchAll(/[a-z0-9][a-z0-9._\-]{1,}@[a-z][a-z0-9.\-]{1,}/gi)].map(m=>m[0].toLowerCase().replace(/[.\-]+$/,''));
 o.upi=ups[0]||'';
 let m=t.match(/(?:₹|Rs\.?|INR|[%¥Z€])\s?([\d,]{1,9}(?:\.\d{1,2})?)\b/);
 if(!m)m=t.match(/(?:paid|sent|received|amount|debited|credited)[^\d\n]{0,25}([\d,]{1,9}(?:\.\d{1,2})?)/i);
 if(!m)m=t.match(/^[ \t]*[₹%¥Z]?[ \t]*(\d{1,3}(?:,\d{2,3})+(?:\.\d{1,2})?|\d{1,7}(?:\.\d{1,2})?)[ \t]*$/m);
 if(m)o.amt=m[1].replace(/,/g,'');
 m=t.match(/(?:UPI\s*(?:Ref(?:erence)?\.?|Transaction)?\s*(?:ID|No\.?|Number)?|UTR|Ref(?:erence)?\.?\s*(?:ID|No\.?|Number)?|Txn\s*ID|Transaction\s*ID)\s*[:#\-]?\s*([A-Z0-9]{6,})/i)||t.match(/\b(\d{12})\b/);
 if(m)o.ref=m[1];
 m=t.match(/\b\d{1,2}\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?,?\s*\d{2,4}(?:[,\s]+\d{1,2}:\d{2}(?::\d{2})?\s?(?:[ap]\.?m\.?)?)?/i)||t.match(/\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}(?:[,\s]+\d{1,2}:\d{2}(?::\d{2})?\s?(?:[ap]m)?)?/i);
 if(m)o.date=m[0].trim();
 m=t.match(/\b(failed|failure|declined|pending|processing|cancelled|reversed)\b/i)||t.match(/\b(success(?:ful(?:ly)?)?|completed)\b/i);
 if(m)o.status=m[1].toLowerCase();
 return o}
$('#scanBtn').addEventListener('click',()=>open('#scanModal'));
$('#shotFile').addEventListener('change',async e=>{const f=e.target.files[0];if(!f)return;
 $('#scanOut').classList.add('hidden');$('#scanVerdict').classList.add('hidden');
 $('#scanBar').classList.remove('hidden');$('#scanBar i').style.width='0';$('#scanProg').textContent='Reading screenshot… the first scan loads the reader (about 7 MB).';
 try{const w=await getWorker();const raw=(await w.recognize(f)).data.text||'';$('#scanRaw').textContent=raw.trim()||'(nothing readable)';
  const o=parseShot(raw);$('#sf-amt').value=o.amt;$('#sf-upi').value=o.upi;$('#sf-ref').value=o.ref;$('#sf-date').value=o.date;$('#sf-status').value=o.status;
  const n=Object.values(o).filter(Boolean).length;
  $('#scanProg').textContent=n?`Read ${n} of 5 details. Fix anything that looks wrong.`:'Could not read any payment details. Try a clearer, uncropped screenshot.';
  $('#scanBar').classList.add('hidden');$('#scanOut').classList.remove('hidden');if(n>=2)verdict()}
 catch(err){$('#scanProg').textContent='Could not read the image: '+err.message;$('#scanBar').classList.add('hidden')}
 e.target.value=''});
$('#scanCheck').addEventListener('click',verdict);
async function verdict(){const upi=$('#sf-upi').value.trim().toLowerCase(),amt=+$('#sf-amt').value,ref=$('#sf-ref').value.trim(),st=$('#sf-status').value.trim().toLowerCase();
 const F=[];let lvl='Low';const bump=l=>{if(l==='High'||(l==='Medium'&&lvl==='Low'))lvl=l};
 if(!upi){F.push(['warn','No UPI ID found. Check the payee name and ID yourself.']);bump('Medium')}
 else{try{const r=await fetch('/api/scan/payee?upi_id='+encodeURIComponent(upi));if(!r.ok)throw new Error('lookup failed');const p=await r.json();
   if(!p.exists){F.push(['warn',`${upi} is not registered in this system, so it cannot be verified here.`]);bump('Medium')}
   else if(p.risk_level==='High'){F.push(['bad',`${p.name} (${upi}) is high risk: ${p.reasons.join('; ')||'reported by users'}.`]);bump('High')}
   else if(p.risk_level==='Medium'){F.push(['warn',`${p.name} (${upi}) is medium risk: ${p.reasons.join('; ')}.`]);bump('Medium')}
   else F.push(['ok',`${p.name} (${upi}) has no fraud reports.`])}catch(e){F.push(['warn','Payee check failed: '+e.message])}}
 if(/fail|declin|pending|process|cancel|revers/.test(st)){F.push(['bad',`The screenshot says "${st}". Do not release goods or services until the money is confirmed in the bank app.`]);bump('High')}
 else if(!st){F.push(['warn','No payment status found in the screenshot.']);bump('Medium')}
 else F.push(['ok',`Status shown: ${st}.`]);
 if(!ref){F.push(['warn','No transaction reference found. Genuine UPI receipts always show one.']);bump('Medium')}
 else if(!/^\d{12}$/.test(ref)){F.push(['warn',`Reference "${ref}" is not a 12-digit UPI reference. Edited screenshots often get this wrong (or the text was misread).`]);bump('Medium')}
 if(!amt)F.push(['warn','No amount found.']);else if(amt>2000){F.push(['warn',`High amount (${inr(amt)}). Double-check before acting.`]);bump('Medium')}
 const el=$('#scanVerdict');el.classList.remove('hidden');
 el.innerHTML=`<div class="lvl ${lvl.toLowerCase()}">${lvl} risk</div>`+F.map(f=>`<div class="flag ${f[0]}">${esc(f[1])}</div>`).join('')+
  '<p class="muted">A screenshot can be edited or faked. Always confirm the credit in the bank or UPI app, never rely on the screenshot alone.</p>'}
})();
