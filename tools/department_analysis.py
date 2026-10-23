"""Department distribution for the fixed, source-linked Seoul sample. No network calls."""
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlencode
import csv, hashlib, json

DATE = '2026-10-23'

def explore(merchant, address, department=''):
    return '/regions/seoul_city.html?' + urlencode({'merchant': merchant, 'address': address, 'department': department})

def calculate(rows):
    groups = defaultdict(list)
    identities = set()
    for row in rows:
        key = (row['source_id'], row['parsed_row'])
        if key in identities:
            raise ValueError('Duplicate document/row identity')
        identities.add(key)
        if not row['department'].strip():
            raise ValueError('Missing department label')
        groups[row['merchant'], row['road_address']].append(row)
    result = []
    for (merchant, address), selected in sorted(groups.items()):
        departments = defaultdict(list)
        for row in selected:
            departments[row['department']].append(row)
        labels = []
        for department, records in sorted(departments.items(), key=lambda x: (-len(x[1]), x[0])):
            months = Counter(r['date'][5:7] for r in records)
            labels.append({'department': department, 'records': len(records),
                'months': [months[f'{m:02}'] for m in range(1, 13)],
                'active_months': len(months), 'first_date': min(r['date'] for r in records),
                'last_date': max(r['date'] for r in records),
                'explorer_url': explore(merchant, address, department)})
        collapsed = Counter()
        for row in selected:
            collapsed[row['department'].split()[-1]] += 1
        result.append({'id': f'place-{len(result)+1}', 'merchant': merchant, 'address': address,
            'records': len(selected), 'department_labels': len(labels),
            'top1_records': labels[0]['records'], 'top5_records': sum(x['records'] for x in labels[:5]),
            'top5_share': round(sum(x['records'] for x in labels[:5])/len(selected)*100, 1),
            'single_record_labels': sum(x['records']==1 for x in labels),
            'repeat_thresholds': {str(m):sum(x['active_months']>=m for x in labels) for m in (3,6,9)},
            'last_token_labels':len(collapsed),
            'last_token_top5_share':round(sum(v for _,v in collapsed.most_common(5))/len(selected)*100,1),
            'explorer_url': explore(merchant,address), 'departments':labels})
    return {'date':DATE, 'scope':'2025 서울 본청의 지정 9개 상호·13개 주소 조합 선정 기록',
        'records':len(rows), 'department_labels':len({r['department'] for r in rows}),
        'places':result, 'note':'부서는 저장된 명칭 문자열 단위이며 조직 개편·별칭을 통합한 실제 조직 수가 아님. 기록 수는 방문자 수·식사 횟수가 아님.'}

def export(data, output_dir):
    output_dir = Path(output_dir)
    (output_dir/'seoul-departments.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    summaries=[]; detail=[]
    for p in data['places']:
        summaries.append({k:p[k] for k in ['merchant','address','records','department_labels','top1_records','top5_records','top5_share','single_record_labels','last_token_labels','last_token_top5_share'] } | {'labels_6_months':p['repeat_thresholds']['6']})
        for d in p['departments']:
            detail.append({'merchant':p['merchant'],'address':p['address'],'department':d['department'],'records':d['records'],'active_months':d['active_months'],**{f'month_{i+1:02}':v for i,v in enumerate(d['months'])},'first_date':d['first_date'],'last_date':d['last_date'],'explorer_url':d['explorer_url']})
    for filename, rows in [('seoul-department-summary.csv',summaries),('seoul-department-months.csv',detail)]:
        with (output_dir/filename).open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");writer.writeheader();writer.writerows(rows)

def render(rows, data_dir, hero, sec, note, table, related, H, N):
    data=calculate(rows);export(data,data_dir)
    a=next(p for p in data['places'] if p['merchant']=='참숯골')
    b=next(p for p in data['places'] if p['merchant']=='브라주카 그릴')
    result=hero('231건과 225건.<br>비슷한 건수, 다른 부서 분포.','같은 장소의 기록이 여러 부서명에 고르게 퍼져 있는지, 일부 부서명에 집중되어 있는지 비교했습니다. 총건수 뒤에 가려진 반복 패턴을 직접 확인해 보세요.','SEOUL · 부서 분포 분석',meta='분석·원문 표본 대조: 세금맛집 | 2026-10-23')
    result+=note('<b>이 글의 분모</b> · 2025년 서울시 본청 자료에서 미리 선정한 9개 상호·13개 주소 조합, 2,699행만 분석합니다. 서울 전체 식당이나 각 부서의 전체 지출을 대표하지 않습니다. 여기서 “부서명”은 저장된 명칭 문자열로, 실제 조직 수나 방문자 수와 다릅니다.')
    result+='<nav class="toc" aria-label="이 분석 바로가기"><a href="#department-explorer">부서·월별 비교 도구</a><a href="#all-places">13개 장소 전체 표</a><a href="#audit-method">검증·재계산 방법</a></nav>'
    result+=sec('건수가 비슷해도 기록이 쌓이는 방식은 다릅니다',f'<p>무교로 16의 참숯골은 {a["records"]}행, 무교로 19의 브라주카 그릴은 {b["records"]}행입니다. 6행 차이만 보면 비슷한 자료처럼 보이지만, 각 장소에서 가장 많은 부서명 5개를 합하면 각각 <b>{a["top5_records"]}행({a["top5_share"]}%)</b>과 <b>{b["top5_records"]}행({b["top5_share"]}%)</b>입니다. 기록의 집중 정도는 다릅니다.</p><p>이 비교는 어느 식당이 더 좋은지 대신, <b>한 장소의 집계가 소수 부서명의 반복 기록에 얼마나 영향을 받는지</b>를 보여줍니다. 식당 이용 기록을 읽을 때 총건수와 함께 살펴볼 두 번째 축입니다.</p>')
    result+='<div class="grid">'
    for p in (a,b):
        result+=f'<section class="card"><h3>{H(p["merchant"])}</h3><p class="small">{H(p["address"])}</p><p><strong>{p["top5_records"]} / {p["records"]}행 · {p["top5_share"]}%</strong><br>가장 많은 부서명 5개의 비중</p><div class="share-track" role="img" aria-label="상위 5개 부서명 {p["top5_share"]}퍼센트, 나머지 {100-p["top5_share"]:.1f}퍼센트"><span style="width:{p["top5_share"]}%"></span></div><p class="small">진한 색: 상위 5개 · 옅은 색: 나머지</p>'+table(['저장 부서명','기록 수'],[[H(d['department']),d['records']] for d in p['departments'][:5]])+f'<a href="{H(p["explorer_url"])}">이 장소의 지출 원문 찾기 →</a></section>'
    result+='</div>'
    result+=sec('넓게 등장하는 것과 여러 달 반복되는 것도 다릅니다',f'<p>참숯골에서는 {a["department_labels"]}개 부서명, 브라주카 그릴에서는 {b["department_labels"]}개 부서명이 나타납니다. 반면 <b>서로 다른 6개월 이상 기록이 있는 부서명</b>은 {a["repeat_thresholds"]["6"]}개와 {b["repeat_thresholds"]["6"]}개입니다. 더 많은 부서명이 보인다는 사실과 여러 달 반복된다는 사실을 같은 의미로 읽으면 안 됩니다.</p><p>6개월은 이 글에서 정한 비교 기준입니다. 연속 6개월을 뜻하지 않으며, 직원 개인의 재방문이나 단골 여부도 알 수 없습니다. 특정 문턱에만 기대지 않도록 3개월·9개월 기준도 함께 계산했습니다.</p>'+table(['기록이 있는 서로 다른 달','참숯골: 부서명 수','브라주카 그릴: 부서명 수'],[[f'{m}개월 이상',a['repeat_thresholds'][str(m)],b['repeat_thresholds'][str(m)]] for m in (3,6,9)])+'<p>3개월 기준에서는 참숯골 21개, 브라주카 그릴 28개로 순서가 반대입니다. 짧은 기간에 여러 번 나타나는 분포와 더 많은 달에 걸쳐 나타나는 분포는 다릅니다. 따라서 하나의 문턱을 골라 어느 장소가 더 널리 이용된다고 단정할 수 없습니다.</p><p>기획조정실 공기업담당관의 참숯골 기록은 31행이 11개월에 걸쳐 나타납니다. 날짜별 원문을 열어 분포를 확인할 수 있지만, 이 결과만으로 업무상 선택 이유나 식사 만족도는 설명할 수 없습니다.</p>')
    options=''.join(f'<option value="{p["id"]}"'+(' selected' if p['merchant']=='참숯골' else '')+f'>{H(p["merchant"])} · {H(p["address"])}</option>' for p in data['places'])
    result+=f'''<section class="section" id="department-explorer"><h2>장소별로 부서와 기록 월을 직접 비교하세요</h2><p>장소를 고르면 모든 부서명의 월별 기록을 볼 수 있습니다. 부서명을 누르면 해당 장소·부서 조건이 적용된 서울 탐색기로 이동합니다. 숫자는 각 월의 선정 거래 행 수입니다.</p><label for="distribution-place">분석할 상호 · 주소</label><select id="distribution-place">{options}</select><p id="distribution-status" role="status">아래 정적 전체 집계표와 CSV로도 결과를 확인할 수 있습니다.</p><div class="table-wrap"><table><thead><tr><th scope="col">저장 부서명</th><th scope="col">기록</th><th scope="col">기록 월 수</th>'''+''.join(f'<th scope="col">{m}월</th>' for m in range(1,13))+'''</tr></thead><tbody id="distribution-rows"></tbody></table></div><noscript><p>자바스크립트가 꺼져 있습니다. 아래 전체 요약표와 부서·월별 CSV를 이용해 주세요.</p></noscript></section>'''
    result+='<div id="all-places"></div>'
    result+=sec('13개 상호·주소 조합을 같은 기준으로 계산했습니다',table(['상호·주소','기록 수','부서명 수','상위 5개 비중','6개월 이상 부서명 수'],[[f'<a href="{H(p["explorer_url"])}">{H(p["merchant"])}</a><br>{H(p["address"])}',p['records'],p['department_labels'],f'{p["top5_share"]}%',p['repeat_thresholds']['6']] for p in data['places']])+'<p>상호·주소 가나다순이며 추천 순위가 아닙니다. 명동10길 19-3의 곰국시집은 8행·3개 부서명뿐이라 상위 5개 비중이 자동으로 100%가 됩니다. 이런 작은 표본을 기록이 수백 건인 장소와 같은 강도로 해석하면 안 됩니다.</p>')
    result+=sec('부서 이름을 합치는 규칙을 바꿔도 차이가 남을까요?',table(['장소','저장 명칭 그대로: 부서명 수 / 상위 5개 비중','마지막 어절만: 명칭 수 / 상위 5개 비중'],[[p['merchant'],f'{p["department_labels"]} / {p["top5_share"]}%',f'{p["last_token_labels"]} / {p["last_token_top5_share"]}%'] for p in (a,b)])+'<p>예를 들어 상위 조직명이 달라도 마지막 부서명이 같으면 합치는 민감도 계산입니다. 브라주카 그릴의 상위 5개 비중은 15.6%에서 16.9%로 바뀌지만 두 장소 간 차이는 남습니다. 다만 마지막 어절이 같다고 같은 조직이라고 확정할 수 없으므로 본문 기본 집계에는 적용하지 않았습니다. 조직 개편 전후의 실제 부서를 통합하려면 별도의 조직 이력이 필요합니다.</p>')
    result+='<div id="audit-method"></div>'
    result+=sec('중복 의심과 이상치는 이렇게 대조했습니다', '<p>선정 2,699행 모두를 기존 월별 JSONL의 문서 ID·파싱 행 번호로 다시 연결했고, 날짜·부서명·상호·금액이 일치했습니다. 문서 ID와 파싱 행 번호가 같은 중복은 없습니다.</p><p>날짜·부서·상호·주소·금액이 모두 같은 후보는 1쌍 있었습니다. <a href="https://opengov.seoul.go.kr/expense/34483996">9월 총무과 공개 문서</a>의 연번 72·74는 같은 날 140,000원씩이지만 사용시간이 13:02와 13:08로 다릅니다. 공식 표에 별도 행으로 있으므로 둘 다 보존했습니다. 별개의 실제 식사 두 번이라고 확정한 것은 아닙니다.</p><p>최대 금액 1,110,000원도 <a href="https://opengov.seoul.go.kr/expense/34711308">10월 시민감사옴부즈만위원회 문서</a> 연번 19에서 10월 24일 복성각 기록과 일치했습니다. 이 글은 금액 가중치를 쓰지 않고 한 행을 한 건으로 세므로 큰 금액이 부서 비중을 더 크게 만들지 않습니다.</p>'+table(['대표 대조 사례','공식 원문','확인한 값'],[['참숯골 · 공기업담당관','<a href="https://opengov.seoul.go.kr/expense/32773754">문서 32773754 · 연번 3</a>','2025-01-17 12:55 · 무교로 16 · 138,000원'],['브라주카 그릴 · 재난안전정책과','<a href="https://opengov.seoul.go.kr/expense/33017153">문서 33017153 · 연번 4</a>','2025-02-04 12:14 · 무교로 19 · 95,600원']])+'<p>공식 화면의 연번은 원문 대조 시 확인한 값입니다. 저장 파싱 행과 항상 같다고 가정하지 않습니다. 전체 원문의 현재 내용까지 전수 대조한 것은 아닙니다.</p>')
    result+=sec('재계산 방법과 제외 기준','<ol><li>입력은 기존 서울 선정 기록 2,699행입니다. 원자료 47,231행에서 2025년 밖 9행, 지정 상호 밖 43,796행, 주소 불일치·누락 322행, 식사 관련 목적 조건 밖 405행을 제외한 표본입니다. <a href="/method.html">선정 규칙</a>을 먼저 확인하세요.</li><li>상호와 도로명 주소 조합으로 나눈 뒤 저장 부서명 문자열별 행 수를 셉니다. 상위 5개 비중은 가장 큰 5개 행 수 합 ÷ 해당 장소 전체 행 수 × 100입니다. 동률이어도 선택되는 합계는 같습니다.</li><li>부서명별 집행일에서 월을 추출해 서로 다른 달 수를 셉니다. 한 달에 여러 행이 있어도 기록 월 수는 1입니다. 부서·월별 행 수를 다시 합하면 장소 합계와 일치해야 합니다.</li><li>한 장소에 이름이 같은 사업체가 공존하거나 시점에 따라 운영 주체가 달라지는 경우는 식별하지 못합니다. 제외된 행과 미수집 문서가 있어 이 결과를 서울 전체 빈도나 점유율로 확장할 수 없습니다.</li></ol><p>참석자 이름·인원별 신상·사용목적 자유문장은 새 공개 데이터에 포함하지 않았습니다. 공개 집계는 상호·주소·부서명·기록 수·월별 분포와 기존 탐색기 연결만 담습니다.</p><div class="actions"><a class="button secondary" href="/data/seoul-department-summary.csv">13개 장소 집계 CSV</a><a class="button secondary" href="/data/seoul-department-months.csv">부서·월별 891개 조합 CSV</a><a class="button secondary" href="/data/seoul-departments.json">전체 집계 JSON</a></div><p><a href="/data/seoul-2025-selected-records.csv">입력 거래행 CSV</a> · <a href="/data/seoul-department-audit.json">입력 해시와 대조 기록</a></p>')
    result+=sec('이 분석으로 판단할 수 있는 것','<p>비슷한 건수의 두 장소라도 기록이 퍼진 부서명의 폭과 반복된 달 수는 다를 수 있습니다. 한 줄짜리 “이용 건수”를 볼 때 <b>어떤 부서명에서, 몇 달에 걸쳐 나온 기록인지</b>를 함께 확인하는 데 이 표를 활용하세요.</p><p>많은 부서명이 등장한다고 맛이나 서비스가 검증되는 것은 아닙니다. 기록이 집중되었다고 부적절한 지출이라는 뜻도 아닙니다. 장소 선택 이유·행사 성격·참석자 수 같은 추가 맥락 없이 추천이나 예산 낭비 판단으로 연결하지 않습니다.</p>')
    result+=related([('/regions/seoul_city.html','서울 기록을 직접 검색하고 공개 문서 확인'),('/report-2025.html','같은 상호를 주소별로 나누는 이유'),('/map.html?region=seoul_city','전국 지도에서 서울 선정 장소 찾기')])
    return result
