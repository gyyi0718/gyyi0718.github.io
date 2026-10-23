'use strict';
(async()=>{
 const ids=['place-left','place-right','place-year','place-org'];
 const controls=ids.map(x=>document.getElementById(x));
 const status=document.getElementById('place-status'),output=document.getElementById('place-comparison');
 const esc=x=>String(x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 try {
  const response=await fetch('/data/place-records.json');if(!response.ok)throw Error(response.status);
  const {rows}=await response.json();const params=new URLSearchParams(location.search);
  controls[1].selectedIndex=1;
  for(let i=0;i<4;i++){const value=params.get(['left','right','year','org'][i]);if(value!==null&&[...controls[i].options].some(o=>o.value===value))controls[i].value=value;}
  function render(){
   const [left,right,year,org]=controls.map(x=>x.value);
   const values=[left,right].map(id=>{
    const all=rows.filter(r=>r.place_id===id),rs=all.filter(r=>(!year||r.date.startsWith(year))&&(!org||r.organization===org));
    const amounts=rs.map(r=>r.amount).sort((a,b)=>a-b),mid=Math.floor(amounts.length/2);
    return {id,label:all[0].merchant+' · '+all[0].address,n:rs.length,months:new Set(rs.map(r=>r.date.slice(0,7))).size,depts:new Set(rs.map(r=>r.organization+' / '+r.department)).size,total:amounts.reduce((a,b)=>a+b,0),median:rs.length?(amounts.length%2?amounts[mid]:(amounts[mid-1]+amounts[mid])/2):null,last:rs.length?rs[rs.length-1].date:'해당 기록 없음',source:rs.length?rs[rs.length-1].source_url:null};
   });
   const lines=[['기록 행','n'],['관측 월','months'],['기관·부서명 조합','depts'],['집행액 합계 (원)','total'],['한 행 금액 중앙값 (원)','median'],['최근 관측','last']];
   output.innerHTML='<div class="table-wrap"><table><thead><tr><th scope="col">항목</th>'+values.map(v=>`<th scope="col"><a href="/places/${v.id}.html">${esc(v.label)}</a></th>`).join('')+'</tr></thead><tbody>'+lines.map(([label,key])=>'<tr><th scope="row">'+label+'</th>'+values.map(v=>'<td>'+(v.n===0?'해당 기록 없음':typeof v[key]==='number'?v[key].toLocaleString('ko-KR'):esc(v[key]))+'</td>').join('')+'</tr>').join('')+'<tr><th scope="row">최근 원문</th>'+values.map(v=>'<td>'+(v.source?`<a href="${esc(v.source)}">공개 집행 문서</a>`:'해당 기록 없음')+'</td>').join('')+'</tr></tbody></table></div>';
   status.textContent=(left===right?'같은 주소를 선택했습니다. 다른 주소를 고르면 비교할 수 있습니다. ':'')+`선택 범위: ${year||'2025~2026 보관 기간'} · ${controls[3].selectedOptions[0].textContent}. ${values[0].n.toLocaleString()}행 / ${values[1].n.toLocaleString()}행. 0건은 영업 여부를 뜻하지 않습니다.`;
   const q=new URLSearchParams({left,right,year,org});history.replaceState(null,'','?'+q+'#compare');
  }
  controls.forEach(c=>c.addEventListener('change',render));render();
 }catch(error){status.textContent='비교 자료를 불러오지 못했습니다. 위 장소별 상세 표와 CSV를 이용하거나 새로고침하세요.';controls.forEach(c=>c.disabled=true);}
})();
