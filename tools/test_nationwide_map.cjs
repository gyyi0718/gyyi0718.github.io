// Exercise the shipped controller against the full saved dataset without a browser.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname,'..');
const data = JSON.parse(fs.readFileSync(path.join(root,'data/nationwide-locations.json')));
class Element {
  constructor(){this.value='';this.textContent='';this.innerHTML='';this.hidden=true;this.disabled=false;this.options=[];this.events={};}
  append(o){this.options.push(o);}
  replaceChildren(...o){this.options=o;this.value='';}
  addEventListener(e,fn){this.events[e]=fn;}
  querySelectorAll(){return [];}
  click(){this.events.click?.();}
}
async function environment({leaflet=true,failFetch=false,search=''}={}) {
  const ids=Object.fromEntries(['nationwide-map',...['province','region','query','category','status','error','results','prev','next','page','reset','fit','download'].map(x=>'map-'+x)].map(x=>[x,new Element()]));
  for(const key of ['province','region','category'])ids['map-'+key].options=[{value:''}];
  let blob, layers=[], map;
  const fakeLayer={clearLayers(){layers=[];},addTo(){return this;}};
  const chain={on(){return this;},addTo(){return this;}};
  const L={
    map(){map={zoom:7,setView(ll,z){this.zoom=z;return this;},getZoom(){return this.zoom;},project(ll){return{x:ll[0]*800,y:ll[1]*800};},fitBounds(){return this;},on(){return this;},closePopup(){}};return map;},
    tileLayer(){return chain;},layerGroup(){return fakeLayer;},control:{scale(){return chain;}},divIcon(x){return x;},
    marker(ll,opts){const m={ll,opts,addTo(){layers.push(this);return this;},bindPopup(content){this.content=content;return this;},on(){return this;}};return m;},
  };
  const context={document:{getElementById:id=>ids[id],createElement:()=>new Element(),querySelector:()=>({scrollTop:0})},console:{...console,error:failFetch?()=>{}:console.error},URL:class extends URL {static createObjectURL(b){blob=b;return 'blob:test';}static revokeObjectURL(){}},URLSearchParams,Blob,Map,Set,location:{href:'http://localhost/map.html'+search,search},history:{replaceState(...args){context.lastURL=args[2];}},setTimeout:fn=>{queueMicrotask(fn);return 1;},clearTimeout(){},fetch:async()=>{if(failFetch)throw new Error('test unavailable');return {ok:true,json:async()=>data};},window:{L:leaflet?L:undefined,addEventListener(){},innerWidth:1200,matchMedia:()=>({matches:false})}};
  context.L=L;
  vm.runInNewContext(fs.readFileSync(path.join(root,'assets/nationwide-map.js'),'utf8'),context);
  await new Promise(r=>setImmediate(r));
  return{ids,context,layers:()=>layers,blob:()=>blob};
}
(async()=>{
  const env=await environment(),e=env.ids;
  assert.match(e['map-status'].textContent,/229개 지역 자료 · 2,186개 항목 · 지도 좌표 2,160개/);
  assert.equal(e['map-region'].options.length,230);
  // Every region remains reachable, including zero-coordinate Seoul evidence.
  for(const r of data.regions){
    e['map-region'].value=r.slug;e['map-region'].events.change();
    assert.equal(e['map-province'].value,r.province);
    assert.match(e['map-status'].textContent,new RegExp('1개 지역 자료 · '+r.items.length+'개 항목'));
    for(const item of r.items) assert.ok(e['map-results'].innerHTML.includes(item.name.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;')),item.name);
  }
  e['map-reset'].click();e['map-next'].click();assert.equal(e['map-page'].textContent,'2 / 110');
  e['map-prev'].click();assert.equal(e['map-page'].textContent,'1 / 110');
  e['map-query'].value='삼우정';e['map-query'].events.input();await new Promise(r=>setImmediate(r));
  const expected=data.regions.flatMap(r=>r.items).filter(i=>[i.name,i.address,i.category].join(' ').includes('삼우정'));
  assert.match(e['map-status'].textContent,new RegExp(expected.length+'개 항목'));
  e['map-download'].click();const csv=await env.blob().text();assert.equal(csv.trim().split('\r\n').length,expected.length+1);assert.ok(csv.includes('삼우정'));assert.ok(!csv.includes('방문 횟수'));
  e['map-query'].value='없는장소_xyz_987654321';e['map-query'].events.input();await new Promise(r=>setImmediate(r));
  assert.match(e['map-status'].textContent,/0개 항목/);assert.ok(e['map-results'].innerHTML.includes('조건에 맞는 장소가 없습니다'));assert.ok(e['map-download'].disabled);
  e['map-reset'].click();assert.match(e['map-status'].textContent,/2,186개 항목/);
  const deep=await environment({search:'?region=sn2025'});assert.equal(deep.ids['map-province'].value,'경기');assert.match(deep.ids['map-status'].textContent,/9개 항목/);
  const absent=await environment({leaflet:false});assert.match(absent.ids['map-status'].textContent,/2,186개 항목/);assert.equal(absent.ids['map-error'].hidden,false);
  const failed=await environment({failFetch:true});assert.match(failed.ids['map-status'].textContent,/불러오지 못했습니다/);assert.match(failed.ids['map-error'].innerHTML,/nationwide-locations.json/);
  console.log(JSON.stringify({status:'PASS',all_region_filters:229,checks:['full map population','every region reachable including missing coordinates','pagination','search','filtered CSV row count','empty result feedback','reset','region deep link','Leaflet failure list fallback','data fetch failure feedback']},null,2));
})().catch(error=>{console.error(error);process.exitCode=1;});
