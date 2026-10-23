"""Shared nationwide map markup; the saved place list is distinct from expense evidence."""
import json
from html import escape
from pathlib import Path

DATA = json.loads((Path(__file__).resolve().parents[1] / 'data/nationwide-locations.json').read_text())
PROVINCES = ['서울','부산','대구','인천','광주','대전','울산','세종','경기','강원','충북','충남','전북','전남','경북','경남','제주']
MAP_SCRIPTS = '<script defer src="/assets/vendor/leaflet/leaflet.js"></script><script defer src="/assets/nationwide-map.js?v=20261023b"></script>'

def map_content(include_directory=True):
    region_index = ''
    for province in PROVINCES:
        regions = sorted((r for r in DATA['regions'] if r['province']==province), key=lambda r:r['name'])
        links = ''.join(f'<a href="/map.html?region={escape(r["slug"])}">{escape(r["name"])} <span>{len(r["items"])}개 항목</span></a>' for r in regions)
        region_index += f'<details class="province-index"><summary>{province} <span>{len(regions)}개 자료</span></summary><div class="region-links">{links}</div></details>'
    content = '''<section id="nationwide-section" class="nationwide" aria-labelledby="map-heading">
<div class="map-section-head"><div><h2 id="map-heading">전국 장소 지도</h2><p>17개 시도 · 지역별 자료 229개 · 보관 장소 항목 2,189개</p></div><a href="#region-directory">전체 지역 목록 ↓</a></div>
<p class="map-intro">시도와 지역을 선택한 뒤 상호나 주소로 좁혀 보세요. 장소 목록에서 지도 위치와 외부 지도 검색을 열 수 있습니다. <b>보관 장소</b>는 위치 탐색용 정보이고, <b>원문 연결</b> 표시는 서울 선정 지출을 확인할 수 있는 항목입니다.</p>
<div class="map-filters">
<label>시도<select id="map-province"><option value="">전국 전체</option></select></label>
<label>지역별 자료<select id="map-region"><option value="">전체 지역</option></select></label>
<label class="map-query-label">상호·주소·지역 검색<input id="map-query" type="search" placeholder="예: 성남, 삼우정, 해운대" autocomplete="off"></label>
<label>보관 분류<select id="map-category"><option value="">전체 분류</option></select></label>
</div>
<div class="map-toolbar"><button id="map-reset" class="secondary" type="button">전국 전체 보기</button><button id="map-fit" class="secondary" type="button">검색 결과에 맞추기</button><button id="map-download" class="secondary" type="button">검색 결과 CSV</button><span class="map-legend"><i></i>보관 장소 · 숫자는 겹친 항목 수</span></div>
<p id="map-status" class="result-count" role="status">전국 장소 목록을 불러오는 중입니다.</p>
<p id="map-error" class="map-error" hidden></p>
<div class="map-layout"><div id="nationwide-map" role="region" aria-label="전국 장소 지도. 방향키로 이동하고 더하기와 빼기로 확대하거나 축소할 수 있습니다."></div><aside class="map-results" aria-label="검색 결과 목록"><div class="map-list-title"><h3>장소 목록</h3><span>상호 가나다순</span></div><div id="map-results"></div><div class="map-pager"><button id="map-prev" type="button" class="secondary" disabled>이전</button><span id="map-page"></span><button id="map-next" type="button" class="secondary" disabled>다음</button></div></aside></div>
<p class="map-caption">2025년 자료에서 보관한 장소 목록입니다. 지역은 <b>자료를 수집한 지자체 기준</b>이며 장소가 다른 지역에 있을 수 있습니다. 좌표가 없는 17개 항목도 목록과 카카오맵 검색으로 찾을 수 있습니다.</p>
<details class="map-scope"><summary>지도 자료의 범위와 확인 상태</summary><p>같은 장소가 여러 지역 자료에 들어갈 수 있어 2,189개 항목이 고유 식당 2,189곳을 뜻하지는 않습니다. 기존 목록의 상호·주소·좌표를 복원했으며, 전체 지역의 모든 식당을 수집한 목록은 아닙니다. 현재 위치·영업 여부는 외부 지도에서 다시 확인해 주세요.</p><p>서울시 본청 13개 상호·주소 항목은 원문 지출 기록을 연결했습니다. 다른 항목은 보관 장소 정보이며 원문 거래 행을 다시 연결하지 못한 방문 횟수·집행액·순위는 표시하지 않습니다. 좌표는 보관 당시 값으로, 원문 연결 여부와 별개입니다. <a href="/sources.html#nationwide-source">자료 출처와 복원 범위</a> · <a href="/data/nationwide-locations.json">장소 목록 JSON</a> · <a href="/privacy.html">지도 서비스 개인정보 안내</a></p></details>
<noscript><p>지도와 필터를 사용하려면 자바스크립트를 켜 주세요. <a href="/data/nationwide-locations.json">전체 장소 자료</a>는 직접 내려받을 수 있습니다.</p></noscript>
</section><section class="section" id="region-directory"><h2>전체 지역에서 찾기</h2><p>시도를 펼치고 지역을 고르면 해당 자료의 장소가 지도와 목록에 표시됩니다. 광역시·도 본청과 시·군·구 자료가 함께 포함되어 있습니다.</p><div class="province-grid">''' + region_index + '</div></section>'

    if not include_directory:
        content = content.split('<section class="section" id="region-directory">')[0]
        content = content.replace('href="#region-directory">전체 지역 목록 ↓', 'href="/map.html#region-directory">전체 지역 목록 →')
        content += '<p class="map-directory-link"><a href="/map.html#region-directory">17개 시도·229개 지역 목록에서 찾기 →</a></p>'
    return content
