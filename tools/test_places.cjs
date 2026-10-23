const fs=require('fs'),vm=require('vm'),assert=require('assert');
const data=JSON.parse(fs.readFileSync('data/place-records.json','utf8'));
const rows=data.rows;
const ids=[...new Set(rows.map(r=>r.place_id))].sort();
const element=values=>({value:values[0],options:values.map(value=>({value})),selectedOptions:[{textContent:'테스트'}],listeners:{},addEventListener(t,f){this.listeners[t]=f},set selectedIndex(i){this.value=this.options[i].value}});
const els={'place-left':element(ids),'place-right':element(ids),'place-year':element(['','2025','2026']),'place-org':element(['','seoul_city','seoul_council','seoul_office','seoul_fire']),'place-purpose':element(['','meal','uncertain','refreshment','mixed']),'place-status':{},'place-comparison':{}};
const context={document:{getElementById:id=>els[id]},fetch:async()=>({ok:true,json:async()=>data}),URLSearchParams,location:{search:''},history:{replaceState(){}},console};
(async()=>{
 await vm.runInNewContext(fs.readFileSync('assets/places.js','utf8'),context);
 let cases=0;
 for(const id of ids)for(const year of ['','2025','2026'])for(const org of ['','seoul_city','seoul_council','seoul_office','seoul_fire'])for(const purpose of ['','meal','uncertain','refreshment','mixed']){
  els['place-purpose'].value=purpose;els['place-left'].value=id;els['place-year'].value=year;els['place-org'].value=org;els['place-left'].listeners.change();
  const selected=rows.filter(r=>r.place_id===id&&(!year||r.date.startsWith(year))&&(!org||r.organization===org)&&(!purpose||r.purpose_category===purpose));
  assert(els['place-status'].textContent.includes(selected.length.toLocaleString()+'행 /'));
  if(selected.length){const total=selected.reduce((s,r)=>s+r.amount,0);assert(els['place-comparison'].innerHTML.includes(total.toLocaleString('ko-KR')));}else assert(els['place-comparison'].innerHTML.includes('해당 기록 없음'));
  cases++;
 }
 els['place-right'].value=els['place-left'].value;els['place-left'].listeners.change();assert(els['place-status'].textContent.includes('같은 주소'));
 context.fetch=async()=>{throw Error('offline')};await vm.runInNewContext(fs.readFileSync('assets/places.js','utf8'),context);assert(els['place-status'].textContent.includes('불러오지 못했습니다'));
 console.log(JSON.stringify({status:'PASS',filterCases:cases,checks:['counts and amounts','empty states','same address','fetch failure']}));
})();
