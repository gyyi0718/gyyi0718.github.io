# -*- coding: utf-8 -*-
import json
from jeju_review import SOURCE_URL, page_shell, PROHIBITED
P = json.load(open('jeju/map_points.json', encoding='utf-8'))
pts = sorted(((d,v) for d,v in P.items() if not PROHIBITED.search(v.get('inds') or '')), key=lambda kv: -kv[1]['rate'])
data = [{'dong': d, 'nm': v['nm'], 'inds': v['inds'], 'addr': v['addr'],
         'lat': v['lat'], 'lon': v['lon'], 'rate': round(v['rate'], 2),
         'sgg': v['sgg'], 'mon': v['months'], 'candidate_position':v.get('demoted', 0)+1} for d, v in pts]
mx = max(x['rate'] for x in data)
html = '''<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>매출맛집 — 제주 동별 공개지표 상위 후보</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Apple SD Gothic Neo','Malgun Gothic',sans-serif;background:#fafbfa;color:#222}
header{position:sticky;top:0;z-index:1100;background:#fff;border-bottom:1px solid #eee;padding:11px 16px;display:flex;gap:12px;align-items:baseline;flex-wrap:wrap}
header h1{font-size:18px;color:#C2410C}
header .sub{font-size:12.5px;color:#888}
#wrap{display:flex;height:calc(100vh - 49px)}
#map{flex:1;min-width:0}
#side{width:290px;flex-shrink:0;overflow-y:auto;border-left:1px solid #eee;background:#fff}
#side .it{padding:10px 13px;border-bottom:1px solid #f3f3f3;cursor:pointer}
#side .it:hover{background:#fff7ed}
#side .d{font-size:11.5px;color:#C2410C;font-weight:700}
#side .n{font-size:14px;font-weight:700;margin-top:1px}
#side .m{font-size:11.5px;color:#888;margin-top:2px}
.bar{height:3px;background:#FDBA74;border-radius:2px;margin-top:5px}
.pop b{font-size:14.5px}
.pop .g{color:#666;font-size:12.5px;line-height:1.6}
footer{padding:13px 16px;font-size:11.5px;color:#999;line-height:1.75;background:#fff;border-top:1px solid #eee}
@media(max-width:760px){#wrap{flex-direction:column;height:auto}#map{height:58vh}#side{width:100%;border-left:none;border-top:1px solid #eee;max-height:42vh}}
</style></head><body>
<header><h1>🍊 매출맛집</h1><span class="sub">제주 동·읍·면별 공개지표 상위 후보 — 2025년 12개월</span></header>
<div id="wrap"><div id="map"></div><div id="side"></div></div>
<footer>
자료: <a href="''' + SOURCE_URL + '''">제주관광공사 · 관광 소비행태 데이터 카드사 음식 급상승 데이터</a> (신한카드 자료).<br>
계산: 2025년 12개 월별 CSV의 ALL_SALES_PRICE_RATE를 상호·행정동별로 합산했습니다. 공개지표 합계는 제공기관의 공식 연간 매출액이 아니며, 실제 매출 순위나 점포 간 매출 배수로 해석하지 않습니다.<br>
같은 상호·행정동에 여러 원문 행이 있으면 함께 더하므로 동일 상호의 지점이 섞일 수 있습니다. 관측 개월은 월별 고유 개수입니다. 동별 지표 합계 상위 5개에서 음식 업종 장소 후보가 연결되는 첫 항목을 표시합니다. 따라서 동별 1위 목록이 아닙니다. 후보 순번은 제외·매칭 전 상위 5개 안의 위치입니다. 동일 행정동과 상호 유사도로 연결했으며 사업자 식별·현장 검증은 하지 않았습니다.<br>
원자료의 유흥시설·숙박·식품판매·식품과 상가정보의 유흥·숙박·판매 업종을 제외했습니다. 음식 업종에는 카페·제과도 포함합니다. 상호·주소와 현재 영업 상태를 방문 전에 확인하세요.<br>
정정일 2026-10-12 · <a href="../corrections.html">정정 이력</a> · <a href="../privacy.html">개인정보처리방침</a>
</footer>
<script>
const D=''' + json.dumps(data, ensure_ascii=False) + ''';
const MX=''' + str(mx) + ''';
const map=L.map('map').setView([33.38,126.55],10);
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
 {attribution:'&copy; OpenStreetMap &copy; CARTO',maxZoom:19}).addTo(map);
const mk=[];
D.forEach((p,i)=>{
  const r=6+14*Math.sqrt(p.rate/MX);
  const m=L.circleMarker([p.lat,p.lon],{radius:r,color:'#fff',weight:1.5,
    fillColor:i<3?'#C2410C':(i<10?'#EA580C':'#FB923C'),fillOpacity:.85}).addTo(map);
  m.bindPopup(`<div class="pop"><b>${p.nm}</b><br><span class="g">${p.sgg} ${p.dong} · ${p.inds}<br>${p.addr}<br>공개지표 합계 ${p.rate} · 후보 ${p.candidate_position}번 · 관측 ${p.mon}개월</span></div>`);
  mk.push(m);
});
const side=document.getElementById('side');
side.innerHTML=D.map((p,i)=>`<div class="it" data-i="${i}">
  <div class="d">${p.sgg} ${p.dong}</div><div class="n">${p.nm}</div>
  <div class="m">${p.inds} · 공개지표 합계 ${p.rate} · 후보 ${p.candidate_position}번</div>
  <div class="bar" style="width:${Math.max(4,100*p.rate/MX)}%"></div></div>`).join('');
side.addEventListener('click',e=>{const it=e.target.closest('.it');if(!it)return;
  const i=+it.dataset.i;map.setView([D[i].lat,D[i].lon],15);mk[i].openPopup();});
</script></body></html>'''
html = page_shell(html, 'map.html')
open('jeju/maechul_map.html', 'w', encoding='utf-8').write(html)
print('생성: jeju/maechul_map.html', len(html), 'bytes /', len(data), '개 지점')
