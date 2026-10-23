'use strict';
(async()=>{
 const $=id=>document.getElementById(id),esc=x=>String(x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const controls=['b-query','b-district','b-year','b-org','b-purpose'].map($),status=$('b-status'),results=$('b-results'),detail=$('b-detail');
 const purposeLabels={meal:'원문에 식사 명시',uncertain:'용도 미확정',refreshment:'간식·음료 명시',mixed:'식사·간식 혼합 명시'};
 const orgs={seoul_city:'서울시 본청',seoul_council:'서울시의회',seoul_office:'사업소',seoul_fire:'소방'};
 let data,selected='',compare='',page=0,stamp=0,currentRows=[],currentPlace=null;const cache=new Map();
 const num=n=>n.toLocaleString('ko-KR');
 function scopeCount(p){return Object.entries(p.scopes).filter(([k])=>(!controls[2].value||k.startsWith(controls[2].value+'/'))&&(!controls[3].value||k.split('/')[1]===controls[3].value)&&(!controls[4].value||k.split('/')[2]===controls[4].value)).reduce((a,[k,n])=>a+n,0);}
 function readURL(){const q=new URLSearchParams(location.search);['q','district','year','org','purpose'].forEach((k,i)=>{const v=q.get(k)||'';controls[i].value=i===0||[...controls[i].options].some(o=>o.value===v)?v:'';});selected=q.get('place')||'';compare=q.get('compare')||'';page=Math.max(0,Number(q.get('page'))||0);}
 function writeURL(){const q=new URLSearchParams();['q','district','year','org','purpose'].forEach((k,i)=>{if(controls[i].value)q.set(k,controls[i].value);});if(selected)q.set('place',selected);if(compare)q.set('compare',compare);if(page)q.set('page',page);const next=location.pathname+(q.size?'?'+q:'');if(next!==location.pathname+location.search)history.pushState(null,'',next);}
 function rowsTable(rows){return '<div class="table-wrap"><table><thead><tr><th>날짜</th><th>기관·부서</th><th>목적 확인 수준</th><th>집행액</th><th>원문</th></tr></thead><tbody>'+rows.map(r=>`<tr><td>${r.date}</td><td>${esc(orgs[r.organization]+' / '+r.department)}</td><td>${esc(purposeLabels[r.purpose_category])}</td><td>${num(r.amount)}원</td><td><a href="${esc(r.source_url)}">문서 · 보관 행 ${r.parsed_row}</a></td></tr>`).join('')+'</tbody></table></div>';}
 async function showDetail(){
  const token=++stamp;currentRows=[];currentPlace=null;
  if(!selected){detail.textContent='후보의 ‘기록 보기’를 선택하세요.';return;}
  const p=data.places.find(p=>p.id===selected);if(!p){detail.textContent='이 공유 주소의 장소 식별자를 찾지 못했습니다. 검색 조건을 초기화해 다시 선택하세요.';return;}
  detail.textContent='선택한 장소의 원문 연결 기록을 불러오는 중입니다.';
  try{
   if(!cache.has(p.id)){const response=await fetch('/data/seoul-directory/'+p.id+'.json');if(!response.ok)throw Error(response.status);cache.set(p.id,await response.json());}
   if(token!==stamp)return;
   const rs=cache.get(p.id).filter(r=>(!controls[2].value||r.date.startsWith(controls[2].value))&&(!controls[3].value||r.organization===controls[3].value)&&(!controls[4].value||r.purpose_category===controls[4].value));currentRows=rs;currentPlace=p;
   const months=new Map();for(const r of rs)months.set(r.date.slice(0,7),(months.get(r.date.slice(0,7))||0)+1);
   const others=data.places.filter(x=>x.address===p.address&&x.id!==p.id);
   detail.innerHTML=`<button type="button" id="b-clear-selection">선택·비교 해제</button><p>검색어·지역은 후보 목록에만 적용됩니다. 선택한 장소는 유지되며 기간·기관·목적 조건은 두 장소에 함께 적용됩니다. 업종·현재 영업 미확인 후보입니다.</p><h3>${esc(p.name)}</h3><p>${esc(p.address)}</p><p><b>${num(rs.length)}행</b> · ${new Set(rs.map(r=>r.source_id)).size}개 문서 · ${months.size}개 관측 월 · ${rs.length?rs[0].date+' ~ '+rs[rs.length-1].date:'선택 범위에 해당 기록 없음'}</p><p>${p.location_evidence==='named_address_no_intermediary_context'?`<a href="https://map.naver.com/p/search/${encodeURIComponent(p.name+' '+p.address)}">기록 주소 지도 검색</a>`:'방문 장소 주소 근거가 부족해 지도 연결을 보류했습니다.'} · 현재 영업·메뉴·가격은 외부 서비스에서 별도로 확인하세요.</p>`;
   if(compare){
    const other=data.places.find(x=>x.id===compare);
    if(other){
     if(!cache.has(other.id)){const response=await fetch('/data/seoul-directory/'+other.id+'.json');if(!response.ok)throw Error(response.status);cache.set(other.id,await response.json());}
     if(token!==stamp)return;
     const right=cache.get(other.id).filter(r=>(!controls[2].value||r.date.startsWith(controls[2].value))&&(!controls[3].value||r.organization===controls[3].value)&&(!controls[4].value||r.purpose_category===controls[4].value));
     const metrics=arr=>{const amounts=arr.map(r=>r.amount).sort((a,b)=>a-b),m=Math.floor(amounts.length/2);return [arr.length,new Set(arr.map(r=>r.source_id)).size,new Set(arr.map(r=>r.date.slice(0,7))).size,arr.reduce((s,r)=>s+r.amount,0),arr.length?(amounts.length%2?amounts[m]:(amounts[m-1]+amounts[m])/2):null];};
     const leftM=metrics(rs),rightM=metrics(right);detail.innerHTML+='<h4>같은 기간·기관·목적으로 비교</h4><p>표의 건수·금액은 선택한 목적 범주의 지출 행입니다. 전체 조건에는 용도 미확정과 간식·음료도 포함됩니다. 메뉴 가격·인당 가격이 아니며 수집 범위가 완전하지 않습니다.</p><div class="table-wrap"><table><thead><tr><th>항목</th><th>'+esc(p.name+' / '+p.address)+'</th><th>'+esc(other.name+' / '+other.address)+'</th></tr></thead><tbody>'+['기록 행','공개 문서','관측 월','집행액 합계 (원)','행 금액 중앙값 (원)'].map((label,i)=>'<tr><th>'+label+'</th><td>'+(leftM[i]===null?'해당 없음':num(leftM[i]))+'</td><td>'+(rightM[i]===null?'해당 없음':num(rightM[i]))+'</td></tr>').join('')+'</tbody></table></div>';
    }else detail.innerHTML+='<p>비교 대상 식별자를 찾지 못했습니다.</p>';
   }
   if(!rs.length){detail.innerHTML+='<p class="note">다른 기관이나 기간을 선택하세요. 0건은 폐업이나 방문 부재의 증거가 아닙니다.</p>';return;}
   detail.innerHTML+='<h4>관측 달력</h4><div class="month-chips">'+[2025,2026].flatMap(y=>Array.from({length:y===2025?12:8},(_,i)=>`${y}-${String(i+1).padStart(2,'0')}`)).filter(m=>!controls[2].value||m.startsWith(controls[2].value)).map(m=>`<span>${m} <b>${months.get(m)||0}행</b></span>`).join('')+'</div><p>0은 보관자료에서 해당 조건의 행이 없다는 뜻입니다. 각 달의 수집량이 같지 않습니다.</p>';
   detail.innerHTML+=`<button type="button" id="b-download">선택 범위 ${num(rs.length)}행 CSV</button><h4>최근 30행 · 최신순</h4>`+rowsTable([...rs].reverse().slice(0,30));
   if(others.length)detail.innerHTML+='<details><summary>같은 주소에 기록된 다른 상호 표기 '+others.length+'개</summary><p>동일 업소의 별칭일 수도, 같은 건물의 다른 업소일 수도 있습니다. 합산하지 않았습니다.</p><ul>'+others.map(x=>`<li><a href="/seoul/?place=${x.id}">${esc(x.name)}</a> · ${x.records}행(전체 범위)</li>`).join('')+'</ul></details>';
   $('b-download').addEventListener('click',download);
  }catch(e){if(token===stamp)detail.innerHTML='<p role="alert">상세 데이터를 불러오지 못했습니다. 아래 지역별 정적 원문 목록 또는 <a href="/data/seoul-directory-records.csv">전체 CSV</a>를 이용하세요.</p>';}
 }
 detail.addEventListener('click',event=>{if(event.target.id==='b-clear-selection'){selected='';compare='';writeURL();showDetail();}});
 function download(){
  const fields=['name','address','date','organization','department','amount','source_url','source_id','parsed_row','purpose_category','purpose_reason'];const cell=v=>'"'+String(v??'').replaceAll('"','""')+'"';
  const text='\uFEFF'+fields.join(',')+'\n'+currentRows.map(r=>fields.map(k=>cell(k==='name'?currentPlace.name:k==='address'?currentPlace.address:r[k])).join(',')).join('\n')+'\n';
  const url=URL.createObjectURL(new Blob([text],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='seoul-'+selected+'.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 }
 async function render(push=false){
  const q=controls[0].value.replace(/\s/g,'').toUpperCase(),d=controls[1].value;
  const ps=data.places.filter(p=>(!d||p.district===d)&&(!q||(p.name+p.address).replace(/\s/g,'').toUpperCase().includes(q))&&scopeCount(p)>0);
  page=Math.min(page,Math.max(0,Math.ceil(ps.length/20)-1));if(push)writeURL();
  status.textContent=`${ps.length}개 상호·주소 묶음 · 선택 범위 ${num(ps.reduce((n,p)=>n+scopeCount(p),0))}행 (${purposeLabels[controls[4].value]||'전체 지출 기록'}). 상호순으로 표시합니다. 현재 영업 확인 목록이 아닙니다.`;
  results.innerHTML=ps.length?'<div class="grid">'+ps.slice(page*20,page*20+20).map(p=>`<section class="card"><h3>${esc(p.name)}</h3><p>${esc(p.address)}</p><p>${num(scopeCount(p))}행 · 전체 범위 최근 기록 ${p.last}</p><button type="button" data-record="${p.id}">기록 보기 · ${esc(p.name)}</button><button type="button" data-compare="${p.id}">비교에 추가 · ${esc(p.name)}</button></section>`).join('')+'</div>':'<p class="note">조건에 맞는 후보가 없습니다. 검색어를 줄이거나 기관·기간·지역 조건을 초기화하세요.</p>';
  $('b-page').textContent=`${page+1} / ${Math.max(1,Math.ceil(ps.length/20))}`;$('b-prev').disabled=page===0;$('b-next').disabled=(page+1)*20>=ps.length;
  results.querySelectorAll('[data-record]').forEach(button=>button.addEventListener('click',async()=>{selected=button.dataset.record;writeURL();await showDetail();$('record-detail').scrollIntoView({block:'start'});$('record-detail').focus({preventScroll:true});}));
  results.querySelectorAll('[data-compare]').forEach(button=>button.addEventListener('click',async()=>{if(!selected)selected=button.dataset.compare;else compare=button.dataset.compare===selected?'':button.dataset.compare;writeURL();await showDetail();$('record-detail').scrollIntoView({block:'start'});}));
  await showDetail();
 }
 try{
  const response=await fetch('/data/seoul-directory.json');if(!response.ok)throw Error(response.status);data=await response.json();readURL();
  controls.forEach((c,i)=>c.addEventListener('change',()=>{page=0;render(true);}));
  $('b-query').addEventListener('input',()=>{page=0;render(true);});
  $('b-prev').addEventListener('click',()=>{page--;render(true);});$('b-next').addEventListener('click',()=>{page++;render(true);});
  $('b-reset').addEventListener('click',()=>{controls.forEach(c=>c.value='');selected='';compare='';page=0;render(true);});
  window.addEventListener('popstate',()=>{readURL();render(false);});await render();
 }catch(e){status.textContent='검색 자료를 불러오지 못했습니다. 아래 지역별 정적 목록과 CSV를 이용하세요.';controls.forEach(c=>c.disabled=true);$('b-prev').disabled=true;$('b-next').disabled=true;}
})();
