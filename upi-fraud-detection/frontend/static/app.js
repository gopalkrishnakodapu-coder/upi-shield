const $=s=>document.querySelector(s);
async function api(path, options){const r=await fetch(path,options); if(!r.ok) throw new Error(await r.text()); return r.json();}
function card(label,value){return `<div class="card"><span>${label}</span><b>${value}</b></div>`}
async function init(){
  try{
    const s=await api('/api/stats'); $('#apiStatus').textContent='API online';
    $('#stats').innerHTML=card('Transactions',s.transactions.toLocaleString())+
      card('Dataset fraud-risk rate',(s.fraud_risk_rate*100).toFixed(1)+'%')+
      card('Average amount','₹'+s.average_amount.toLocaleString())+
      card('Median fraud amount','₹'+s.median_fraud_amount.toLocaleString());
    $('#category').innerHTML=s.categories.map(x=>`<option>${x}</option>`).join('');
    $('#state').innerHTML=s.states.map(x=>`<option>${x}</option>`).join('');
    loadModels(); loadTransactions();
  }catch(e){$('#apiStatus').textContent='API error'; console.error(e)}
}
async function loadModels(){
 const rows=await api('/api/models');
 $('#modelTable').innerHTML=`<div class="table-wrap"><table class="table"><thead><tr><th>Model</th><th>Accuracy</th><th>Precision</th><th>Recall</th><th>F1</th><th>ROC-AUC</th></tr></thead><tbody>${
 rows.map(r=>`<tr><td><b>${r.model}</b></td><td>${(r.accuracy*100).toFixed(1)}%</td><td>${(r.precision*100).toFixed(1)}%</td><td>${(r.recall*100).toFixed(1)}%</td><td class="metric-good">${(r.f1*100).toFixed(1)}%</td><td>${(r.roc_auc*100).toFixed(1)}%</td></tr>`).join('')
 }</tbody></table></div>`;
}
async function loadTransactions(){
 const fraud=$('#fraudOnly').checked; const rows=await api('/api/transactions?limit=50&fraud_only='+fraud);
 if(!rows.length){$('#dataTable').innerHTML='<p>No transactions found.</p>';return}
 const cols=['trans_hour','trans_day','trans_month','category','age','trans_amount','state','fraud_risk'];
 $('#dataTable').innerHTML=`<table class="table"><thead><tr>${cols.map(c=>`<th>${c}</th>`).join('')}</tr></thead><tbody>${
 rows.map(r=>`<tr>${cols.map(c=>`<td>${c==='trans_amount'?'₹'+Number(r[c]).toFixed(2):r[c]}</td>`).join('')}</tr>`).join('')
 }</tbody></table>`;
}
$('#fraudOnly').addEventListener('change',loadTransactions);
document.querySelectorAll('.tab').forEach(b=>b.addEventListener('click',()=>{
 document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));b.classList.add('active');
 document.querySelectorAll('.panel').forEach(x=>x.classList.remove('active'));$('#'+b.dataset.tab).classList.add('active');
}));
$('#predictForm').addEventListener('submit',async e=>{
 e.preventDefault(); const payload={
  trans_hour:+$('#hour').value,trans_day:+$('#day').value,trans_month:+$('#month').value,
  category:+$('#category').value,age:+$('#age').value,trans_amount:+$('#amount').value,state:+$('#state').value};
 const box=$('#result'); box.classList.remove('hidden'); box.innerHTML='<p>Assessing transaction…</p>';
 try{const r=await api('/api/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  const cls=r.risk_level.toLowerCase(); box.innerHTML=`<div class="risk ${cls}">${r.risk_level} RISK</div>
   <div class="score">${r.risk_score}%</div><div class="meter"><i style="width:${r.risk_score}%"></i></div>
   <p><b>Random Forest:</b> ${(r.random_forest.probability*100).toFixed(2)}% fraud probability</p>
   <p><b>Logistic Regression:</b> ${(r.logistic_regression.probability*100).toFixed(2)}% fraud probability</p>
   <p>${r.recommendation}</p>`;
 }catch(err){box.innerHTML='<p class="high">Prediction failed. Check the backend.</p>'}
});
init();
