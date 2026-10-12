# -*- coding: utf-8 -*-
import json
from jeju_review import SOURCE_URL, page_shell, PROHIBITED
D=json.load(open('jeju/survivors.json',encoding='utf-8'))
S=D['stats']; items=[x for x in D['items'] if x['lat'] and x['lon'] and not PROHIBITED.search(x.get('inds') or '')]
main=[x for x in items if not x['air']]; air=[x for x in items if x['air']]
MX=max(x['v25'] for x in main)
P50 = S['surv'].get('50', S['surv'].get(50))
REOBS = f"원자료 업종 필터를 통과한 상호·행정동 키를 비교했습니다. 2021년 공개지표 합계 상위 50개의 {P50:.0f}%, 2021년 관측 키 {S['n21']:,}개 중 약 {S['survall']:.0f}%가 2025년 자료에서도 관측됐습니다. 상위 50개 재관측률은 2025년 순위와 무관하게 자료에 존재하는 비율입니다. 표와 지도는 별도로 두 해 모두 공개지표 합계 상위 300개에 포함되고 음식 업종의 장소 후보로 연결된 목록입니다. 유흥·숙박·판매 업종으로 연결된 항목은 표시에서 제외했습니다. 2022~2024년 연속 영업, 현재 영업, 실제 매출 순위, 폐업을 확인한 결과는 아닙니다."
html='''<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>2021·2025 두 시점의 제주 식당</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Apple SD Gothic Neo','Malgun Gothic',sans-serif;background:#fafbfa;color:#222;line-height:1.6}
.wrap{max-width:1100px;margin:0 auto;padding:0 16px 60px}
header{background:#fff;border-bottom:1px solid #eee;padding:26px 16px}
header .in{max-width:1100px;margin:0 auto}
h1{font-size:26px;color:#C2410C;letter-spacing:-.4px}
header p{color:#777;font-size:14px;margin-top:7px}
.kpi{display:flex;gap:12px;flex-wrap:wrap;margin:22px 0 6px}
.k{flex:1;min-width:150px;background:#fff;border:1px solid #eee;border-radius:14px;padding:16px 18px}
.k .n{font-size:27px;font-weight:800;color:#C2410C;letter-spacing:-1px}
.k .l{font-size:12.5px;color:#888;margin-top:3px}
h2{font-size:19px;margin:32px 0 10px}
h2 small{font-size:13px;color:#999;font-weight:400;margin-left:7px}
#map{height:440px;border-radius:14px;border:1px solid #eee;overflow:hidden}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid #eee;border-radius:14px;overflow:hidden;font-size:14px}
th,td{padding:10px 12px;text-align:left;border-bottom:1px solid #f4f4f4}
th{background:#fafafa;font-size:12.5px;color:#777;font-weight:600}
td.n{text-align:right;font-variant-numeric:tabular-nums}
tr:last-child td{border-bottom:none}
.up{color:#C2410C;font-weight:700}.dn{color:#0369A1}
.pill{display:inline-block;background:#FFF7ED;color:#C2410C;font-size:11px;border-radius:9px;padding:1px 7px;margin-left:5px}
.note{background:#fff;border:1px solid #eee;border-radius:14px;padding:16px 18px;font-size:13px;color:#666;margin-top:14px}
.note b{color:#444}
footer{font-size:11.5px;color:#999;line-height:1.8;margin-top:26px}
.scroll{overflow-x:auto}
@media(max-width:760px){h1{font-size:21px}#map{height:340px}}
</style></head><body>
<header><div class="in"><h1>2021·2025 두 시점의 제주 식당</h1>
<p>2021년과 2025년, 두 해 모두 공개지표 합계 상위 300개에 포함된 음식점 후보</p></div></header>
<div class="wrap">
<div class="kpi">
  <div class="k"><div class="n">''' + f"{S['surv'][str(50)] if str(50) in S['surv'] else S['surv'][50]:.0f}%" + '''</div><div class="l">2021년 지표 상위 50개의 2025년 재관측률</div></div>
  <div class="k"><div class="n">''' + f"{S['survall']:.0f}%" + '''</div><div class="l">2021년 관측 상호·행정동의 2025년 재관측률</div></div>
  <div class="k"><div class="n">''' + str(len(main)) + '''곳</div><div class="l">두 해 모두 지표 상위 300개 · 좌표 연결 목록</div></div>
</div>
<div class="note">''' + REOBS + '''</div>
<h2>지도<small>원 크기는 2025년 공개지표 합계</small></h2>
<div id="map"></div>
<h2>두 해 모두 지표 상위 300개<small>2025년 공개지표 합계 순</small></h2>
<div class="scroll"><table><thead><tr><th>#</th><th>식당</th><th>지역</th><th>업종</th><th class="n">2021</th><th class="n">2025</th><th class="n">지표합계 변화</th></tr></thead><tbody>
'''
for i,x in enumerate(main,1):
    g=x['growth']; cls='up' if (g or 0)>=0 else 'dn'
    html+=f"<tr><td>{i}</td><td><b>{x['nm']}</b></td><td>{x['sgg']} {x['dong']}</td><td>{x['inds'] or x['mls']}</td><td class='n'>{x['v21']}</td><td class='n'>{x['v25']}</td><td class='n {cls}'>{'+' if (g or 0)>=0 else ''}{g}%</td></tr>\n"
html+='''</tbody></table></div>
<h2>공항 매장<small>따로 뒀습니다</small></h2>
<div class="note">상호명에 “공항”이 포함된 항목은 별도 표에 두었습니다. 실제 공항 입점 여부와 현재 영업 상태를 현장 확인한 분류는 아닙니다.</div>
<div class="scroll"><table><thead><tr><th>#</th><th>매장</th><th class="n">2021</th><th class="n">2025</th><th class="n">지표합계 변화</th></tr></thead><tbody>
'''
for i,x in enumerate(air,1):
    g=x['growth']; cls='up' if (g or 0)>=0 else 'dn'
    html+=f"<tr><td>{i}</td><td><b>{x['nm']}</b></td><td class='n'>{x['v21']}</td><td class='n'>{x['v25']}</td><td class='n {cls}'>{'+' if (g or 0)>=0 else ''}{g}%</td></tr>\n"
html+='''</tbody></table></div>
<footer>
자료: <a href="''' + SOURCE_URL + '''">제주관광공사 · 관광 소비행태 데이터 카드사 음식 급상승 데이터</a> (문화빅데이터플랫폼, 신한카드 자료) 및 소상공인시장진흥공단 상가정보.<br>
계산: 2021년과 2025년의 각 12개월 CSV에서 ALL_SALES_PRICE_RATE를 상호명·행정동명별로 더했습니다. 동일 상호·행정동 안의 여러 원문 행을 함께 더하므로 지점이 섞일 수 있습니다. “공개지표 합계”는 이 사이트의 계산값이며 제공기관의 공식 연간 매출 지표가 아닙니다. 원자료 설명은 매출 비율 정보를 제공한다고 안내합니다. 분모와 표본이 같다는 근거를 확보하지 못했으므로 실제 매출 순위·매출 배수·매출 증가율로 해석하지 않습니다. 표의 변화율은 지표 합계의 산술 변화입니다.<br>
원자료의 음식 관련 중분류만 집계하고 유흥시설·숙박·식품판매·식품 분류는 제외했습니다. 상가정보의 음식 대분류 안에 있는 일반 유흥 주점도 지도·표에서 추가 제외했습니다. 원자료 분류와 상가정보 분류가 다를 수 있어 재관측률의 분모와 지도 목록은 구분합니다.<br>
위치는 같은 행정동 안의 상호 유사도로 연결한 후보이며, 사업자번호로 확인한 동일 업체가 아닙니다. 방문 전 상호·주소·영업 여부를 확인하세요. 상호 변경·이전·표기 변경·카드 표본 변화는 미관측 원인이 될 수 있으며 폐업으로 간주하지 않습니다.<br>
정정일 2026-10-12 · <a href="../corrections.html">정정 이력</a> · <a href="../privacy.html">개인정보처리방침</a>
</footer>
</div>
<script>
const M=''' + json.dumps(main,ensure_ascii=False) + ''';
const MX=''' + str(MX) + ''';
const map=L.map('map').setView([33.38,126.55],10);
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',{attribution:'&copy; OpenStreetMap &copy; CARTO',maxZoom:19}).addTo(map);
M.forEach((p,i)=>{
  const r=6+13*Math.sqrt(p.v25/MX);
  L.circleMarker([p.lat,p.lon],{radius:r,color:'#fff',weight:1.5,
    fillColor:i<3?'#9A3412':(i<10?'#C2410C':'#FB923C'),fillOpacity:.85}).addTo(map)
   .bindPopup(`<b>${p.nm}</b><br><span style="color:#666;font-size:12.5px">${p.sgg} ${p.dong} · ${p.inds||p.mls}<br>${p.addr||''}<br>2021 ${p.v21} → 2025 ${p.v25} (${p.growth>=0?'+':''}${p.growth}%)</span>`);
});
</script></body></html>'''
html = page_shell(html, '')
open('jeju/survivors.html','w',encoding='utf-8').write(html)
print(f'생성: jeju/survivors.html | 본목록 {len(main)}곳 / 공항 {len(air)}곳')
