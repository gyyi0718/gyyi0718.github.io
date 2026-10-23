/* Nationwide place browsing. Saved coordinates are not current business verification. */
(() => {
  'use strict';
  const byId = id => document.getElementById(id);
  if (!byId('nationwide-map')) return;
  const ui = Object.fromEntries(['province','region','query','category','status','error','results','prev','next','page','reset','fit','download'].map(k => [k, byId('map-' + k)]));
  const provinces = ['서울','부산','대구','인천','광주','대전','울산','세종','경기','강원','충북','충남','전북','전남','경북','경남','제주'];
  const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const normalized = s => String(s).toLocaleLowerCase('ko').replace(/\s+/g, '');
  const number = n => n.toLocaleString('ko-KR');
  const searchURL = item => 'https://map.kakao.com/link/search/' + encodeURIComponent(item.name + ' ' + (item.address || item.regionName));
  let regions = [], all = [], filtered = [], page = 0, map, layer, ready = false;
  const pageSize = 20;

  function option(value, text) { const o = document.createElement('option'); o.value = value; o.textContent = text; return o; }
  function updateRegions() {
    const previous = ui.region.value;
    ui.region.replaceChildren(option('', '전체 지역'));
    regions.filter(r => !ui.province.value || r.province === ui.province.value).sort((a,b) => a.name.localeCompare(b.name,'ko')).forEach(r => ui.region.append(option(r.slug, r.province + ' · ' + r.name)));
    if ([...ui.region.options].some(o => o.value === previous)) ui.region.value = previous;
  }
  const placeProfiles = {"브이아이피참치|서울 중구 세종대로22길 16": "p08", "브라주카 그릴|서울 중구 무교로 19": "p05", "곰국시집|서울 중구 무교로 24": "p02", "삼우정|서울 중구 서소문로 134-12": "p10", "브이아이피참치|서울 중구 세종대로11길 42": "p07", "구이구이|서울 중구 을지로 6": "p03", "참숯골|서울 중구 무교로 16": "p13", "브이아이피참치|서울 중구 을지로 16": "p09", "우도일식|서울 중구 세종대로 124": "p12", "브이아이피참치|서울 중구 세종대로 135": "p06", "복성각|서울 중구 덕수궁길 7": "p04", "오리마당|서울 중구 세종대로 92": "p11", "곰국시집|서울 중구 명동10길 19-3": "p01"};
  function profileLink(item) { const id = item.record_status === "source_linked" && placeProfiles[item.name+"|"+item.address]; return id ? `<a href="/places/${id}.html">주소별 기록·비교 →</a>` : ""; }
  function stateLabel(item) { return item.record_status === 'source_linked' ? '지출 원문 연결' : '보관 장소 정보'; }
  function popup(item) {
    return '<div class="map-popup"><h4>' + esc(item.name) + '</h4><p>' + esc(item.address || '주소 정보 없음') + '</p><p>' + esc(item.province + ' · ' + item.regionName + ' 자료 / ' + item.category) + '</p><p>' + stateLabel(item) + ' · 위치·영업 재확인 필요</p><a href="' + esc(searchURL(item)) + '" target="_blank" rel="noopener noreferrer">카카오맵에서 확인 ↗</a>' + (item.sources ? '<p><a href="' + esc(item.sources[0].url) + '" target="_blank" rel="noopener noreferrer">서울시 지출 원문 ↗</a></p>' : '') + '</div>';
  }
  function mapGroups(items) {
    const groups = new Map();
    const cellSize = map.getZoom() >= 16 ? 28 : 48;
    items.filter(i => i.coordinates).forEach(item => {
      const p = map.project(item.coordinates, map.getZoom());
      const key = Math.floor(p.x / cellSize) + ':' + Math.floor(p.y / cellSize);
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(item);
    });
    return [...groups.values()];
  }
  function drawMap() {
    if (!map) return;
    layer.clearLayers();
    mapGroups(filtered).forEach(items => {
      const ll = items.length === 1 ? items[0].coordinates : [items.reduce((s,i)=>s+i.coordinates[0],0)/items.length,items.reduce((s,i)=>s+i.coordinates[1],0)/items.length];
      const size = items.length === 1 ? 19 : items.length < 10 ? 30 : 37;
      const marker = L.marker(ll, {icon:L.divIcon({className:'map-dot' + (items.length===1?' single':''), html:'<span>' + (items.length===1?'':number(items.length)) + '</span>',iconSize:[size,size],iconAnchor:[size/2,size/2]}),title:items.length===1?items[0].name:items.length+'개 장소 항목 확대',alt:items.length===1?items[0].name:items.length+'개 장소 항목'}).addTo(layer);
      if (items.length === 1) marker.bindPopup(popup(items[0]));
      else marker.on('click', () => {
        const bounds = L.latLngBounds(items.map(i=>i.coordinates));
        if (map.getZoom() >= 17 || bounds.getNorthEast().equals(bounds.getSouthWest())) {
          marker.bindPopup('<div class="map-popup"><h4>가까운 위치의 ' + items.length + '개 항목</h4><p>서로 다른 지역 자료의 같은 장소가 포함될 수 있습니다.</p><ol>' + items.map(i=>'<li><a target="_blank" rel="noopener noreferrer" href="'+esc(searchURL(i))+'">'+esc(i.name)+'</a><br>'+esc(i.regionName+' 자료 · '+i.address)+'</li>').join('')+'</ol></div>').openPopup();
        } else map.fitBounds(bounds,{padding:[35,35],maxZoom:Math.min(map.getZoom()+3,18)});
      });
    });
  }
  function fitResults() {
    if (!map) return;
    const coordinates = filtered.filter(i=>i.coordinates).map(i=>i.coordinates);
    if (coordinates.length) map.fitBounds(coordinates, {padding:[25,25],maxZoom:14});
    else if (ui.province.value === '서울') map.setView([37.5665,126.978],11);
    else map.setView([36,127.8],7);
  }
  function renderList() {
    const max = Math.max(1, Math.ceil(filtered.length/pageSize));
    page = Math.min(page,max-1);
    ui.results.innerHTML = filtered.length ? filtered.slice(page*pageSize,(page+1)*pageSize).map(item => '<section class="place-card"><span class="place-category">'+esc(item.province+' · '+item.regionName+' 자료 / '+item.category)+'</span><h4>'+esc(item.name)+'</h4><p>'+esc(item.address||'주소 정보 없음')+'</p><span class="place-state '+(item.sources?'source-linked':'')+'">'+stateLabel(item)+'</span><div class="place-actions">'+(item.coordinates?'<button type="button" data-place="'+esc(item.id)+'">지도에서 보기</button>':'<span>보관 좌표 없음</span>')+'<a target="_blank" rel="noopener noreferrer" href="'+esc(searchURL(item))+'">카카오맵 ↗</a>'+(item.sources?'<a target="_blank" rel="noopener noreferrer" href="'+esc(item.sources[0].url)+'">지출 원문 ↗</a>':'')+profileLink(item)+'</div></section>').join('') : '<p class="map-empty">조건에 맞는 장소가 없습니다. 검색어를 줄이거나 전국 전체 보기를 눌러 주세요.</p>';
    ui.page.textContent = (page+1)+' / '+max;
    ui.prev.disabled = !page;
    ui.next.disabled = page+1>=max;
    ui.download.disabled = !filtered.length;
    ui.results.querySelectorAll('[data-place]').forEach(button => button.addEventListener('click', () => {
      const item = filtered.find(i => i.id === button.dataset.place);
      if (!map || !item?.coordinates) return;
      map.setView(item.coordinates,17);
      L.popup().setLatLng(item.coordinates).setContent(popup(item)).openOn(map);
      if (window.innerWidth <= 650) byId('nationwide-map').scrollIntoView({block:'start',behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
    }));
  }
  function syncURL() {
    const url = new URL(location.href);
    for (const key of ['province','region','category']) ui[key].value ? url.searchParams.set(key,ui[key].value) : url.searchParams.delete(key);
    ui.query.value.trim() ? url.searchParams.set('q',ui.query.value.trim()) : url.searchParams.delete('q');
    history.replaceState(null,'',url.pathname+url.search+url.hash);
  }
  function refresh({fit=true}={}) {
    if (!ready) return;
    const q = normalized(ui.query.value);
    filtered = all.filter(i => (!ui.province.value || i.province===ui.province.value) && (!ui.region.value || i.regionSlug===ui.region.value) && (!ui.category.value || i.category===ui.category.value) && (!q || i.searchText.includes(q)));
    page=0;
    const mapped=filtered.filter(i=>i.coordinates).length;
    ui.status.textContent = new Set(filtered.map(i=>i.regionSlug)).size+'개 지역 자료 · '+number(filtered.length)+'개 항목 · 지도 좌표 '+number(mapped)+'개'+(mapped<filtered.length?' · 좌표 없는 '+number(filtered.length-mapped)+'개는 목록에서 확인':'');
    renderList();
    if(map) map.closePopup();
    if(fit) fitResults();
    drawMap();syncURL();
  }
  function restoreURL() {
    const params=new URLSearchParams(location.search);
    const rg=regions.find(r=>r.slug===params.get('region'));
    ui.province.value=rg?.province || (provinces.includes(params.get('province'))?params.get('province'):'');
    updateRegions();ui.region.value=rg?.slug||'';
    ui.query.value=params.get('q')||'';
    ui.category.value=[...ui.category.options].some(o=>o.value===params.get('category'))?params.get('category'):'';
    refresh();
  }
  async function init() {
    try {
      const response=await fetch('/data/nationwide-locations.json');
      if(!response.ok) throw new Error('HTTP '+response.status);
      const data=await response.json();regions=data.regions;
      all=regions.flatMap(r=>r.items.map(i=>({...i,province:r.province,regionName:r.name,regionSlug:r.slug,searchText:normalized([r.province,r.name,i.name,i.address,i.category].join(' '))}))).sort((a,b)=>a.name.localeCompare(b.name,'ko')||a.id.localeCompare(b.id));
      provinces.forEach(p=>ui.province.append(option(p,p)));
      [...new Set(all.map(i=>i.category))].sort((a,b)=>a.localeCompare(b,'ko')).forEach(c=>ui.category.append(option(c,c)));
      if (window.L) {
        map=L.map('nationwide-map',{scrollWheelZoom:false,minZoom:5,maxZoom:18}).setView([36,127.8],7);
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'}).on('tileerror',()=>{ui.error.hidden=false;ui.error.textContent='배경 지도 일부를 불러오지 못했습니다. 장소 목록과 카카오맵 링크는 계속 이용할 수 있습니다.';}).addTo(map);
        layer=L.layerGroup().addTo(map);
        L.control.scale({imperial:false}).addTo(map);
        map.on('zoomend',drawMap);
      } else {
        ui.fit.disabled=true;
        ui.error.hidden=false;ui.error.textContent='지도 화면을 불러오지 못했습니다. 아래 장소 목록과 외부 지도 링크를 이용해 주세요.';
      }
      ready=true;restoreURL();
    } catch(error) {
      ui.status.textContent='장소 자료를 불러오지 못했습니다. 페이지를 새로고침해 주세요.';
      ui.error.hidden=false;ui.error.innerHTML='<a href="/data/nationwide-locations.json">전체 장소 자료 직접 열기</a>';
      console.error('Nationwide map data:',error);
    }
  }
  ui.province.addEventListener('change',()=>{ui.region.value='';updateRegions();refresh();});
  ui.region.addEventListener('change',()=>{const r=regions.find(r=>r.slug===ui.region.value);if(r)ui.province.value=r.province;updateRegions();refresh();});
  ui.category.addEventListener('change',()=>refresh());
  let debounce;ui.query.addEventListener('input',()=>{clearTimeout(debounce);debounce=setTimeout(()=>refresh(),180);});
  ui.reset.addEventListener('click',()=>{clearTimeout(debounce);ui.province.value='';ui.region.value='';ui.query.value='';ui.category.value='';updateRegions();refresh();});
  ui.fit.addEventListener('click',fitResults);
  ui.prev.addEventListener('click',()=>{page--;renderList();document.querySelector('.map-results').scrollTop=0;});
  ui.next.addEventListener('click',()=>{page++;renderList();document.querySelector('.map-results').scrollTop=0;});
  ui.download.addEventListener('click',()=>{
    const cell=value=>'"'+String(value??'').replace(/^[=+@-]/,"'$&").replace(/"/g,'""')+'"';
    const rows=[['자료시도','자료지역','상호','보관주소','분류','위도','경도','확인상태','지출원문','외부지도검색'],...filtered.map(i=>[i.province,i.regionName,i.name,i.address,i.category,...(i.coordinates||['','']),stateLabel(i),i.sources?.[0]?.url||'',searchURL(i)])];
    const blob=new Blob(['\uFEFF'+rows.map(r=>r.map(cell).join(',')).join('\r\n')],{type:'text/csv;charset=utf-8'});
    const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='세금맛집_전국장소_검색결과.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
  window.addEventListener('popstate',()=>{if(ready)restoreURL();});
  init();
})();
