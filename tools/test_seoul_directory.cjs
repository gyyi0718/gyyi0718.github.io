const fs=require('fs'),vm=require('vm'),assert=require('assert');
const data=JSON.parse(fs.readFileSync('data/seoul-directory.json','utf8')),source=fs.readFileSync('assets/seoul-directory.js','utf8');
function element(values=['']){return {value:'',options:values.map(value=>({value})),listeners:{},addEventListener(t,fn){this.listeners[t]=fn},querySelectorAll(selector){const attr=selector.slice(1,-1),key=attr==='data-record'?'record':'compare';return [...(this.innerHTML||'').matchAll(new RegExp(attr+'="([^"]+)"','g'))].map(m=>{const b=element();b.dataset={[key]:m[1]};(this.buttons??={})[key+':'+m[1]]=b;return b;});},scrollIntoView(){},focus(){}};}
async function environment(search='',failure=''){
 const e={};for(const id of ['b-query','b-district','b-year','b-org','b-purpose','b-status','b-results','b-detail','b-prev','b-next','b-page','b-reset','b-download','b-clear-selection','record-detail'])e[id]=element();
 e['b-district'].options=['',...new Set(data.places.map(p=>p.district))].map(value=>({value}));e['b-year'].options=['','2025','2026'].map(value=>({value}));e['b-org'].options=['','seoul_city','seoul_council','seoul_office','seoul_fire'].map(value=>({value}));
 e['b-purpose'].options=['','meal','uncertain','refreshment','mixed'].map(value=>({value}));
 const loc={search,pathname:'/seoul/'},events={},downloads=[];const context={document:{getElementById:id=>e[id],createElement:()=>({click(){}})},location:loc,window:{addEventListener(t,f){events[t]=f}},history:{pushState(a,b,url){loc.search=url.includes('?')?'?'+url.split('?')[1]:'';}},URLSearchParams,Blob,URL:{createObjectURL(b){downloads.push(b);return 'blob:test'},revokeObjectURL(){}},setTimeout:f=>f(),console,fetch:async url=>{if(failure==='all'||failure==='detail'&&url!='/data/seoul-directory.json')throw Error('offline');return {ok:true,json:async()=>url==='/data/seoul-directory.json'?data:stored.get(url.split('/').pop().replace('.json',''))};}};
 await vm.runInNewContext(source,context);return {e,loc,events,downloads};
}
const stored=new Map(data.places.map(p=>[p.id,JSON.parse(fs.readFileSync('data/seoul-directory/'+p.id+'.json','utf8'))]));
const settle=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
 const {e,loc,events}=await environment();let cases=0;
 for(const district of ['',...new Set(data.places.map(p=>p.district))])for(const year of ['','2025','2026'])for(const org of ['','seoul_city','seoul_council','seoul_office','seoul_fire'])for(const purpose of ['','meal','uncertain','refreshment','mixed']){
  e['b-purpose'].value=purpose;e['b-district'].value=district;e['b-year'].value=year;e['b-org'].value=org;e['b-year'].listeners.change();await settle();
  let n=0,groups=0;
  for(const p of data.places){if(district&&p.district!==district)continue;const rs=stored.get(p.id).filter(r=>(!year||r.date.startsWith(year))&&(!org||r.organization===org)&&(!purpose||r.purpose_category===purpose));if(rs.length){groups++;n+=rs.length;}}
  assert(e['b-status'].textContent.includes(`${groups}개 상호·주소 묶음 · 선택 범위 ${n.toLocaleString('ko-KR')}행`));cases++;
 }
 e['b-query'].value='없는장소zzzz';e['b-query'].listeners.input();await settle();assert(e['b-results'].innerHTML.includes('조건에 맞는 후보가 없습니다'));
 e['b-reset'].listeners.click();await settle();assert.equal(e['b-query'].value,'');
 loc.search='?district=중구&year=2025';events.popstate();await settle();assert.equal(e['b-year'].value,'2025');assert.equal(e['b-district'].value,'중구');
 const journey=await environment();const a=data.places.find(p=>p.name==='삼우정'),b=data.places.find(p=>p.name==='복성각');assert(a&&b);
 journey.e['b-query'].value=a.name;journey.e['b-query'].listeners.input();await settle();await journey.e['b-results'].buttons['record:'+a.id].listeners.click();
 journey.e['b-query'].value=b.name;journey.e['b-query'].listeners.input();await settle();await journey.e['b-results'].buttons['compare:'+b.id].listeners.click();
 assert(journey.loc.search.includes('place='+a.id));assert(journey.loc.search.includes('compare='+b.id));assert(journey.e['b-detail'].innerHTML.includes('같은 기간·기관·목적으로 비교'));
 journey.e['b-district'].value='중구';journey.e['b-district'].listeners.change();await settle();assert(journey.loc.search.includes(a.id));
 const shared=await environment(journey.loc.search);assert(shared.e['b-detail'].innerHTML.includes('같은 기간·기관·목적으로 비교'));
 journey.e['b-detail'].listeners.click({target:{id:'b-clear-selection'}});await settle();assert(!journey.loc.search.includes('place='));
 const first=data.places[0];const broken=await environment('?place='+first.id,'detail');assert(broken.e['b-detail'].innerHTML.includes('상세 데이터를 불러오지 못했습니다'));
 const offline=await environment('','all');assert(offline.e['b-status'].textContent.includes('검색 자료를 불러오지 못했습니다'));
 const invalid=await environment('?place=unknown');assert(invalid.e['b-detail'].textContent.includes('식별자를 찾지 못했습니다'));
 let exportCases=0,exportRows=0;const exportEnv=await environment();
 for(const p of data.places)for(const year of ['','2025','2026'])for(const org of ['','seoul_city','seoul_council','seoul_office','seoul_fire'])for(const purpose of ['','meal','uncertain','refreshment','mixed']){
  const expected=stored.get(p.id).filter(r=>(!year||r.date.startsWith(year))&&(!org||r.organization===org)&&(!purpose||r.purpose_category===purpose));
  if(!expected.length)continue;
  const test=exportEnv;test.loc.search='?place='+p.id+'&year='+year+'&org='+org+'&purpose='+purpose;test.events.popstate();await settle();test.downloads.length=0;test.e['b-download'].listeners.click();
  const actual=await test.downloads[0].text();const fields=['name','address','date','organization','department','amount','source_url','source_id','parsed_row','purpose_category','purpose_reason'];const quote=v=> '"'+String(v??'').replaceAll('"','""')+'"';
  const csv=fields.join(',')+'\n'+expected.map(r=>fields.map(k=>quote(k==='name'?p.name:k==='address'?p.address:r[k])).join(',')).join('\n')+'\n';
  assert.equal(actual.replace(/^\uFEFF/,''),csv);exportCases++;exportRows+=expected.length;
 }
 console.log(JSON.stringify({exportCases,exportRows,status:'PASS',scopeCases:cases,checks:['independent per-record filtered counts','zero results','reset','popstate','index failure','detail failure','unknown shared id']}));
})();
