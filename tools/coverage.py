import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def render(page,hero,sec,table,H):
 data=json.loads((ROOT/'data/nationwide-locations.json').read_text());rows=[]
 for r in sorted(data['regions'],key=lambda r:(r['province'],r['name'])):
  n=len(r['items']);linked=sum(i['record_status']=='source_linked' for i in r['items'])
  rows.append([H(r['province']+' · '+r['name']),n,linked,'미확인', '선정 기록 연결' if linked else '보관 목록만 제공'])
 body=hero('어느 지역에서 무엇을 확인할 수 있나요','전국 보관 목록과 지출 원문 연결 범위를 구분합니다. 장소가 목록에 있다는 사실은 현재 영업 확인이나 지출 기록 검증을 뜻하지 않습니다.','COVERAGE')
 body+=sec('전국 보관 지도', '<p>현재 공개 목록은 2,186항목이며 원문 연결 표시는 그중 13항목입니다. 분모는 지역 자료별 항목 수이고 고유 식당 수가 아닙니다. 같은 장소가 여러 자료에 들어갈 수 있습니다. 현재 영업 확인은 전 항목 미실시입니다.</p><p>지명 분류 3항목을 격리하고, 상세 주소가 없는 9항목의 대표 좌표 표시를 해제했습니다. 지도 좌표는 2,160항목에 남아 있으며 이는 현재 위치를 모두 확인했다는 뜻이 아닙니다. <a href="/data/location-precision-audit.json">정밀도 감사 내역</a> · <a href="/map.html">보관 지도</a></p>')
 body+=sec('수집 지자체별 제공 범위',table(['보관 수집지역','공개 항목','원문 연결 항목','현재 영업','제공 수준'],rows)+'<p>이 표의 지역은 자료를 수집한 지자체 기준입니다. 식당 소재지 기준과 다를 수 있으므로 원문 연결 항목을 지역 전체 식당의 검증률로 해석하지 않습니다.</p>')
 broad=json.loads((ROOT/'data/seoul-directory.json').read_text());districts={}
 for p in broad['places']:
  if p['district'] not in districts:districts[p['district']]=[0,0]
  districts[p['district']][0]+=1;districts[p['district']][1]+=p['records']
 body+=sec('서울 확장 기록: 장소 소재지 기준',f'<p>전국 보관 목록과 별도로 서울 공개 지출 원본에서 주소·반복 문서 기준을 적용해 {len(broad["places"]):,}개 표기·주소 묶음, {broad["selected_rows"]:,}행을 추출했습니다. 전체 지출 기록에는 용도 미확정과 간식·음료·혼합이 포함되며 식사 확정 통계가 아닙니다. 기존 13개 원문 연결 항목과 겹치므로 서로 더해 고유 장소 수를 만들 수 없습니다. 상호 표기 차이도 남아 있습니다. <a href="/seoul/">서울 장소 찾기</a>에서 지역·기관·기간을 선택하세요.</p>'+table(['장소 소재 구','표기·주소 묶음','공개 행','현재 영업'],[[H(d),v[0],v[1],'미확인'] for d,v in sorted(districts.items())]))
 body+=sec('지출 기록을 찾으려면','<p><a href="/places/">기존 13주소 상세·비교</a>와 <a href="/regions/seoul_city.html">2025년 본청 선정 기록 검색</a>에서 범위에 맞는 원문을 확인할 수 있습니다. 다른 지역의 보관 장소는 현재 지출 통계 검색 자료가 아닙니다. <a href="/sources.html">출처·방법</a>에 각 자료의 기간과 선정 기준을 공개합니다.</p>')
 page('coverage.html','지역별 자료 확인 범위','보관 수집지역별 목록 수, 원문 연결 범위와 현재 영업 미확인 상태를 공개합니다.',body,True)
