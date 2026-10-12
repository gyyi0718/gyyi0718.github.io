#!/usr/bin/env python3
"""2026-10-12 correction build. Keep legacy inputs immutable; publish scoped evidence.

python3 tools/rebuild_reviewed.py [--refresh-seoul /path/to/opengov]
No publishing, crawling or source mutations are performed by this command.
"""
from pathlib import Path
from collections import Counter, defaultdict
import argparse, csv, datetime, hashlib, html, json, re

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
INPUT = ROOT / 'tools/input'
DATE = '2026-10-12'
H = html.escape
BAD_CATEGORY = re.compile(r'카페|커피|제과|베이커리|디저트|찻집|호텔|신라스테이|하얏트|판매|정육점|식품|과일|채소|떡,|컴퓨터|인테리어|기업|S-OIL|빌딩|쉼터|서비스|아파트|교회|주차장|보관|저수지|안경|광장|수목원|이발소|전망대|슈퍼|공원|전시관|터미널|농업|유흥|자연드림|복호두|아임일리터')
BAD_NAME = re.compile(r'카페|까페|커피|정미소|여객선|터미널|주유소|공원|카페프렌즈', re.I)
MEAL = re.compile(r'식사|오찬|만찬|중식|석식|조식|간담|급식|회식')
NONMEAL = re.compile(r'다과|상품권|화환|경조|물품|선물|격려금')
ROAD = re.compile(r'([가-힣A-Za-z0-9·]+(?:대로|번길|길|로))\s*(\d+(?:-\d+)?)')
KNOWN = {
    '삼우정': ('삼우정', {'서소문로 134-12'}),
    '우도일식': ('우도일식', {'세종대로 124'}),
    '브이아이피참치': ('브이아이피참치', {'세종대로11길 42', '세종대로22길 16', '을지로 16', '세종대로 135'}),
    '오리마당': ('오리마당', {'세종대로 92'}),
    '구이구이': ('구이구이', {'을지로 6'}),
    '참숯골': ('참숯골', {'무교로 16'}),
    '곰국시집': ('곰국시집', {'무교로 24', '명동10길 19-3'}),
    '복성각': ('복성각', {'덕수궁길 7'}),
    '브라주카': ('브라주카 그릴', {'무교로 19'}),
}

def write_json(p, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

def refresh_seoul(raw):
    documents, rows, seen = {}, [], set()
    rejected = Counter()
    raw_rows = 0
    for p in sorted(Path(raw).glob('2025-*.jsonl')):
        for line in p.open():
            obj = json.loads(line); doc = obj['doc']
            if doc['org_id'] != 'seoul_city': continue
            documents[doc['id']] = {k: doc[k] for k in ('id', 'title', 'url')}
            for r in obj['rows']:
                raw_rows += 1
                try:
                    day = datetime.date.fromisoformat(r.get('d') or '')
                except ValueError:
                    rejected['invalid_date'] += 1; continue
                if day.year != 2025:
                    rejected['outside_2025'] += 1; continue
                key = (doc['id'], r['row_no'])
                if key in seen:
                    rejected['duplicate_document_row'] += 1; continue
                seen.add(key)
                merchant = re.sub(r'\s+', '', r.get('place') or '')
                matched = next((x for x in KNOWN if x in merchant), None)
                if not matched:
                    rejected['outside_selected_names'] += 1; continue
                name, allowed = KNOWN[matched]
                roadmatch = ROAD.search(r.get('addr') or '')
                address = ' '.join(roadmatch.groups()) if roadmatch else None
                if address not in allowed:
                    rejected['missing_or_other_address'] += 1; continue
                purpose = r.get('purpose') or ''
                if not MEAL.search(purpose) or NONMEAL.search(purpose):
                    rejected['purpose_not_meal_scope'] += 1; continue
                if not isinstance(r.get('amount'), (int, float)) or r['amount'] <= 0:
                    rejected['nonpositive_amount'] += 1; continue
                # Public export omits free text purpose/recipient information.
                rows.append({'source_id': doc['id'], 'source_url': doc['url'], 'source_title': doc['title'],
                    'parsed_row': r['row_no'], 'date': str(day), 'department': r.get('dept') or '',
                    'merchant': name, 'source_merchant': r.get('place') or '', 'road_address': '서울 중구 ' + address,
                    'amount': r['amount']})
    rows.sort(key=lambda r: (r['date'], r['source_id'], r['parsed_row']))
    result = {'scope': '2025 서울시 본청 기존 수집 JSONL 중 지정 9개 상호·13개 주소 조합의 식사 관련 기록',
        'source_documents': len(documents), 'parsed_rows': raw_rows, 'valid_unique_2025_rows': len(seen),
        'filter_exclusions': dict(rejected), 'selected_records': len(rows), 'rows': rows,
        'documents': list(documents.values()), 'refreshed': DATE,
        'limitation': '원문 전체의 수집 완전성과 현재 영업 상태를 입증하지 않음. 9개 상호는 기존 목록의 식당 업종 중 선정한 분석 표본이며 전체 서울 식당 순위가 아님.'}
    write_json(DATA / 'seoul-2025-evidence.json', result)

def seoul_groups(evidence):
    groups = defaultdict(list)
    for row in evidence['rows']:
        groups[(row['merchant'], row['road_address'])].append(row)
    out = []
    for (name, addr), rows in groups.items():
        out.append({'n': name, 'ad': addr, 'v': len(rows), 'a': sum(r['amount'] for r in rows),
            'd': len({r['department'] for r in rows if r['department']}), 'c': '식사 관련 기록', 'll': None,
            'evidence': rows[:3], 'status': 'parsed_rows_reaggregated'})
    out.sort(key=lambda x: (-x['v'], x['ad'], x['n']))
    for rank, row in enumerate(out, 1): row['r'] = rank
    return out

def build_catalogue():
    original = json.loads((INPUT/'catalogue-before-20261012.json').read_text())
    out, held, anomalies = [], [], []
    evidence = json.loads((DATA/'seoul-2025-evidence.json').read_text())
    for old in original:
        row = {k: v for k, v in old.items() if k not in ('tp', 'tr', 'items', 'note')}
        items = old['items']; n, u = old['tr'], old['tp']
        inconsistent = isinstance(u, int) and isinstance(n, int) and bool(items) and (u > n - (sum(i['v'] for i in items) - len(items)) or n > u * max(i['v'] for i in items))
        if inconsistent: anomalies.append(old['slug'])
        row.update(legacy_record_value=n, legacy_total_posts=u, legacy_note=old['note'],
            restaurant_transaction_count=None, unique_restaurant_count=None,
            source_document_count=None, parsed_row_count=None,
            status='legacy_aggregate_unverified', note='기존 집계 후보입니다. 원문 거래행을 다시 연결하지 못한 수치는 확정 통계로 해석하지 마세요.',
            scope='기존 상위 후보 중 업종·금액 이상 항목 제외; 전체 지역 순위가 아님', items=[])
        for item in items:
            reason = None
            if BAD_CATEGORY.search(item['c']) or BAD_NAME.search(item['n']): reason='비식당·카페 업종 또는 상호/장소 오매칭 가능성'
            if item['v'] <= 0 or item['a'] <= 0: reason='결제 횟수 또는 금액 오류'
            elif item['a'] / item['v'] > 1000000: reason='회당 100만 원 초과: 식사 외 지출·금액 오기 여부 확인 필요'
            if reason:
                held.append({'slug': old['slug'], 'city': old['city'], **item, 'reason': reason}); continue
            fixed = {**item, 'd': None, 'legacy_source_key_count': item.get('d'), 'status':'legacy_aggregate_unverified'}
            # Keep original numbers as display IDs; removing a row never fabricates a replacement rank.
            row['items'].append(fixed)
        if row['slug'] == 'seoul_city':
            row['items'] = seoul_groups(evidence)
            row['status'] = 'selected_parsed_rows_reaggregated'
            row['source_document_count'] = evidence['source_documents']
            row['parsed_row_count'] = evidence['parsed_rows']
            row['selected_transaction_count'] = evidence['selected_records']
            row['selected_merchant_address_count'] = len(row['items'])
            row['note'] = '기존 수집 원문에서 지정 9개 상호·주소별 식사 관련 기록을 다시 집계했습니다. 전체 서울 식당 순위가 아닙니다.'
            row['scope'] = evidence['scope']
        row['display_item_count'] = len(row['items'])
        row['display_record_sum'] = sum(x['v'] for x in row['items'])
        out.append(row)
    write_json(DATA/'catalogue.json', out)
    write_json(DATA/'review-held.json', held)
    write_json(DATA/'quality-status.json', {'date': DATE, 'regions':len(out), 'legacy_definition_conflicts': anomalies,
        'held_items':len(held), 'held_regions':len({x['slug'] for x in held}),
        'verification_levels':{'legacy_aggregate_unverified':228, 'selected_parsed_rows_reaggregated':1},
        'policy':'Unknown source population totals are null. Selected-key counts are not unique restaurant counts. No ads on reference or review pages.'})
    return out, held, evidence, anomalies

def page(title, body, path, noindex=False):
    template=(INPUT/'page-template.txt').read_text()
    head=template[template.index('<!DOCTYPE'):template.index('</head>')]
    head=re.sub(r'<title>.*?</title>', '<title>'+H(title)+' — 세금맛집</title>', head, flags=re.S)
    head=re.sub(r'<meta (?:name="description"|property="og:[^"]+")[^>]*>', '', head)
    head=re.sub(r'<script[^>]*adsbygoogle[^>]*></script>', '', head)
    head += '<meta name="google-adsense-account" content="ca-pub-3133301641364865">'
    if noindex: head+='<meta name="robots" content="noindex,follow">'
    head+='<link rel="canonical" href="https://gyyi0718.github.io/'+path+'">'
    head+='<style>table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:10px 7px;border-bottom:1px solid #eee;text-align:left;overflow-wrap:anywhere}.scroll{overflow-x:auto}.status{background:#fff6db;padding:15px;border-radius:10px;line-height:1.8}a{color:#08763f}p{line-height:1.9;margin:12px 0}li{line-height:1.8;margin-left:20px}header nav{float:none;display:flex;flex-wrap:wrap;gap:12px;padding:6px 0}header nav a{margin:0}details{margin:12px 0}summary{cursor:pointer;color:#08763f}</style>'
    prefix='../' if '/' in path else ''
    nav=''.join(f'<a href="{prefix}{url}">{label}</a>' for url,label in [('index.html','지도·지역'),('regions/seoul_city.html','서울 원문 분석'),('report-2025.html','자료 현황'),('method.html','집계 기준'),('sources.html','출처'),('corrections.html','정정'),('about.html','소개'),('contact.html','문의')])
    text=head+'</head><body><header><a class="logo" href="'+prefix+'index.html">🍚 세금맛집</a><nav>'+nav+'</nav></header><main class="wrap">'+body+'</main><footer>세금맛집 · 공개 업무추진비 기록을 읽는 개인 데이터 프로젝트<br>'+nav+'</footer></body></html>'
    (ROOT/path).write_text(text)

def card(title, text): return '<section class="card"><h2>'+title+'</h2>'+text+'</section>'

def write_csv(path, fields, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader(); w.writerows(rows)

def render(catalogue, held, evidence, anomalies):
    source_html=(ROOT/'sources.html').read_text()
    # These are navigation links, never represented as proof for a particular value.
    homes={}
    for slug, url in re.findall(r'<tr[^>]*>.*?regions/([^".]+)\.html.*?<a href="(https?://[^"]+)"', source_html, re.S): homes[slug]=url
    byslug={r['slug']:r for r in catalogue}
    for r in catalogue:
        exact=r['slug']=='seoul_city'; city=H(r['city']); slug=r['slug']; items=r['items']
        title='서울시청 업무추진비: 9개 상호를 주소별로 다시 세어 보기' if exact else f'2025 {r["city"]} 식당 후보 자료'
        b='<section class="card"><h1>'+title+'</h1><p class="meta">자료 연도 2025 · 정정·검토일 '+DATE+'</p><p>'+H(r['note'])+'</p>'
        if exact:
            b+='<p><b>같은 이름이라고 같은 식당으로 합치면 안 됩니다.</b> 기존 서울 페이지는 브이아이피참치를 한 주소에 합쳤지만, 보관한 원문에는 세종대로11길 42·세종대로22길 16·을지로 16·세종대로 135가 따로 등장합니다. 이번 표는 상호와 도로명·건물번호가 같은 행끼리만 셉니다. 현재 영업장 확인이나 사업자 단위 식별을 대신하지 않습니다.</p>'
            b+=f'<div class="stats"><div class="stat">확인 가능한 수집문서<br><b>{evidence["source_documents"]:,}개</b></div><div class="stat">파싱된 원문행<br><b>{evidence["parsed_rows"]:,}행</b></div><div class="stat">선정 조건에 맞는 기록<br><b>{evidence["selected_records"]:,}건</b></div><div class="stat">상호·주소 조합<br><b>{len(items)}개</b></div></div><p>전체 서울시 결제 건수와 고유 식당 수는 제시하지 않습니다. 9개 상호는 기존 식당 후보에서 골랐으며, 이 밖의 식당보다 결제가 많다는 뜻이 아닙니다.</p>'
        else:
            b+=f'<p class="status">확인 상태: <b>원문 연결 재검토 중</b>. 기존 목록에서 음식점 업종으로 분류된 {len(items)}개 후보를 남겼습니다. 아래 번호는 기존 자료 번호이며, 보류 항목 뒤의 순위를 당겨 새 순위를 만들지 않았습니다. 결제 횟수·금액은 기존 집계값이고 이번에 원문 전체를 재검증한 값이 아닙니다.</p>'
        b+='</section>'
        if exact:
            b+=card('이번 분석의 재현 범위', f'<p>서울 정보소통광장에서 수집해 보관한 2025년 파일 12개의 서울시 본청 문서를 사용했습니다. {evidence["valid_unique_2025_rows"]:,}개 유효한 2025년 문서·행 번호를 확인한 뒤, 지정 9개 상호와 주소가 일치하고 목적에 식사·오찬·만찬·중식·석식·조식·간담·급식·회식 표현이 있는 양수 금액 행을 선택했습니다. 다과·상품권·물품·선물 등은 제외했습니다.</p><p>상호가 같아도 주소가 없거나 다른 경우 합치지 않았습니다. 부서 수는 문서 개수가 아닌 원문 부서명 문자열의 고유 개수입니다. 부서 개편·표기 차이는 남을 수 있습니다. 게시판에 공개된 모든 문서를 빠짐없이 모았는지는 확인하지 못했습니다.</p><p><a href="../data/seoul-2025-selected-records.csv">선정 기록 전체 CSV</a> · <a href="../data/seoul-2025-documents.csv">수집문서별 원문 링크</a> · <a href="../data/seoul-2025-evidence.json">재계산용 JSON</a></p>')
        else:
            b+=card('이 지역 자료를 읽는 방법',f'<p>아래 {len(items)}개 후보의 기존 결제 횟수 합은 <b>{r["display_record_sum"]:,}건</b>입니다. 이것은 현재 표시한 후보 목록 안의 합계이며 지역 전체 결제 수가 아닙니다. 회당 금액은 각 행의 집행액을 횟수로 나눈 값이며 인당 식비·메뉴 가격·맛 평가가 아닙니다.</p><p>기존 지역 메모: {H(r["legacy_note"])}. 이 메모의 전수·부서 범위 표현도 원문을 다시 확인하기 전에는 검증된 수집 범위로 사용하지 않습니다. 전체 고유 식당 수와 전체 식당 결제 수는 알 수 없어 공란으로 정정했습니다.</p>')
        table='<div class="scroll"><table><thead><tr><th>'+('표시 순서' if exact else '기존 번호')+'</th><th>상호·주소</th><th>기록 횟수</th><th>금액·회당</th></tr></thead><tbody>'
        for i in items:
            table+=f'<tr data-item="{i["r"]}"><td>{i["r"]}</td><td><b>{H(i["n"])}</b><br>{H(i["c"])}<br>{H(i["ad"])}<br><a target="_blank" rel="noopener" href="https://map.kakao.com/link/search/{H(i["n"]+" "+i["ad"],quote=True)}">지도에서 현재 장소 확인</a></td><td><b>{i["v"]}회</b>'+ (f'<br>부서명 {i["d"]}개' if exact else '')+f'</td><td>{i["a"]:,}원<br>회당 {round(i["a"]/i["v"]):,}원</td></tr>'
        table+='</tbody></table></div><p>주소·업종은 현재 영업 확인을 뜻하지 않습니다. 방문 전 지도에서 상호·주소를 다시 확인하세요.</p>'
        b+=card('상호·주소별 재집계' if exact else '기존 집계의 식당 후보', table)
        if exact:
            samples=''
            for i in items[:6]:
                samples+='<h3>'+H(i['n'])+' · '+H(i['ad'])+'</h3><ul>'
                for e in i['evidence']:
                    samples+=f'<li>{e["date"]} · {e["amount"]:,}원 · {H(e["department"])} — <a href="{e["source_url"]}" target="_blank" rel="noopener">원문 {e["source_id"].split(":")[-1]}의 파싱 행 {e["parsed_row"]}</a></li>'
                samples+='</ul>'
            b+=card('숫자에서 원문까지 따라가기', '<p>아래 링크는 기관 첫 화면이 아니라 집계에 사용한 상세 문서입니다. 행 번호는 저장한 표 파서 기준이며 원문 화면의 번호와 다를 수 있습니다. 목적 문구·인원 같은 추가 정보는 원문에서 직접 확인할 수 있습니다.</p>'+samples)
            b+=card('이전 분석에서 바뀐 결론', '<p>기존 49,425를 결제 건수와 식당 수에 동시에 사용한 것은 오류였습니다. 또한 지도 주소를 한 곳으로 붙이는 과정에서 지점이 섞였고, 오리마당·복성각의 표시 주소와 원문 주소도 달랐습니다. 이를 단순히 숫자 하나 교체하는 대신, 선정 상호와 원문 주소 조합을 공개하는 방식으로 바꿨습니다.</p><p>따라서 기존의 “열 곳이 모두 중구”, “거의 모든 부서”, “접대가 많다”, “도보 10분”이라는 해석은 철회했습니다. 참석자·목적의 추가 검증 없이 결제 빈도를 맛이나 이용자의 선호로 확대 해석하지 않습니다.</p>')
        rh=[i for i in held if i['slug']==slug]
        if rh:
            b+=card('이번에 보류한 항목', '<p>보류는 해당 업체가 실제 음식점이 아니라는 단정이 아닙니다. 기존 지도 연결과 식당 분류를 증명하지 못해 추천·지도·합계에서 제외한 것입니다.</p><ul>'+''.join('<li>'+H(i['n'])+' · 기존 '+H(i['c'])+' · '+H(i['reason'])+'</li>' for i in rh)+'</ul>')
        b+=card('정정 내역과 다른 지역', '<p><a href="../corrections.html">2026-10-12 정정 이력</a> · <a href="../sources.html">데이터 정의·내려받기</a> · <a href="../index.html">전체 지역 목록</a></p>')
        page(title,b,'regions/'+slug+'.html',noindex=not exact)
    render_aux(catalogue, held, evidence, anomalies)
    render_map(catalogue)

def render_aux(catalogue, held, ev, anomalies):
    nitems=sum(len(r['items']) for r in catalogue)
    glossary='<table><tr><th>지표</th><th>정의·공개 상태</th></tr><tr><td>source_document_count</td><td>서로 다른 공식문서 ID 개수. 서울 표본만 원문 목록과 연결.</td></tr><tr><td>parsed_row_count</td><td>보관 파일에서 읽은 행 개수. 식당 결제 수가 아님.</td></tr><tr><td>selected_transaction_count</td><td>명시한 상호·주소·목적 필터를 통과한 문서·행 개수.</td></tr><tr><td>selected_merchant_address_count</td><td>선정 기록의 상호·주소 키 수. 사업체 수나 고유 식당 수가 아님.</td></tr><tr><td>restaurant_transaction_count / unique_restaurant_count</td><td>동일 모집단의 식당 결제 수 / 고유 식당 수. 검증하지 못해 null.</td></tr><tr><td>legacy_record_value / legacy_total_posts</td><td>이전 파일 값. 의미가 혼재되어 현재 통계에 쓰지 않음.</td></tr><tr><td>기존 번호</td><td>예전 목록의 위치. 보류 후 빈 번호를 유지하며 새로운 순위가 아님.</td></tr></table>'
    b=card('공개자료를 어떻게 읽을 수 있나', '<p>세금맛집은 지방자치단체 업무추진비의 상호·결제 기록을 찾아볼 수 있도록 정리하는 개인 프로젝트입니다. 현재 사이트는 원문으로 다시 계산한 서울 사례와, 원문 연결을 추가 점검하는 228개 지역의 기존 후보 자료를 구분합니다. 맛·위생·가격·현재 영업을 평가하는 서비스는 아닙니다.</p><p>운영·정정 책임은 세금맛집 운영자에게 있으며 <a href="contact.html">문의</a>로 오류 제보를 받습니다. 원문과 계산 결과를 함께 확인한 뒤 정정 날짜·변경 이유를 남깁니다. 자동 수집·처리 도구를 사용하며, 통계 검산이 원문 전체 검증을 대신하지 않습니다.</p><p>2026-10-12 현재 자료 페이지의 광고 송출 코드는 제거했습니다. ads.txt와 계정 메타 태그는 사이트 소유권 확인용으로 유지합니다. 광고 승인 여부가 자료 정확성을 보증하지 않습니다.</p>')
    page('세금맛집 소개',b,'about.html')
    b=card('서로 다른 지표를 구분합니다',glossary)+card('원문 재집계와 기존 자료',f'<p>서울 표본은 {ev["source_documents"]:,}개 수집문서의 {ev["parsed_rows"]:,}행을 읽고, 2025년의 유효한 문서·행 ID를 중복 제거한 뒤 선정 조건을 적용했습니다. 원문과 연결한 전체 선정 기록을 CSV로 공개합니다. 전체 서울시 식당 모집단을 복원한 결과는 아닙니다.</p><p>그 밖의 지역은 기존 집계 JSON이 남아 있지만, 원문 거래행과 연결할 수 있는 입력 파일을 이번 환경에서 찾지 못했습니다. 따라서 기존 건수는 재검증되지 않은 값으로 표시합니다. 기존 생성기의 total_posts에는 게시물·월별 묶음·행 수가 혼재했고, depts에는 실제 부서가 아닌 문서 키 개수가 들어갈 수 있었습니다.</p>')+card('업소 필터와 결론의 범위',f'<p>기존 목록에서 비식당·카페 분류, 상호 오매칭 의심, 비양수 금액, 회당 100만 원 초과 항목 {len(held)}개를 보류했습니다. 대체 순위를 추정하지 않았습니다. 보류 목록은 별도 파일로 공개합니다. 통과한 후보도 원문 검증이 끝난 것은 아닙니다.</p><p>과거 정규화가 지점명을 지우거나 같은 지도 ID의 기록을 합쳤기 때문에 다른 지점이 합쳐졌을 수 있습니다. 새 서울 표본은 도로명과 건물번호까지 맞는 행만 묶고, 다른 주소는 분리합니다. 같은 주소의 동명 업소·상호변경까지 해결하는 사업체 식별자는 없다는 한계가 남습니다.</p><p>회당 금액은 합계액÷횟수입니다. 인당 가격이나 메뉴 가격이 아닙니다. 참석자·목적을 확인하지 않은 “접대가 많다”, “거의 모든 부서가 간다”, “문을 닫았다” 같은 주장은 하지 않습니다.</p>')+card('검사는 세 가지입니다','<ol><li>출력 일치: 페이지·지도·CSV가 같은 검토 데이터를 사용하는지 확인합니다.</li><li>의미 검산: 알려진 모집단에서 중복 키, 합계, 범위·분모·비식당 분류를 검사합니다. 모르는 값은 0 대신 null로 둡니다.</li><li>원문 추적: 서울 선정 행마다 상세 문서 URL·행 번호를 제공합니다. 자동 검사 통과를 전국 원문 검증 완료로 부르지 않습니다.</li></ol><p><code>python3 tools/verify_pages.py</code>로 검사할 수 있습니다. noindex는 검색 색인 설정이며 광고 심사 제외 기능으로 취급하지 않습니다.</p>')
    page('집계 기준과 검증 범위',b,'method.html')
    links='<ul><li><a href="data/catalogue.json">검토 데이터 JSON</a></li><li><a href="data/segeummatjib-2025-regions.csv">지역별 검증 상태 CSV</a></li><li><a href="data/segeummatjib-2025-top10.csv">기존 번호를 보존한 후보 CSV</a> (파일명 호환용 top10이며 전국 순위가 아님)</li><li><a href="data/seoul-2025-selected-records.csv">서울 선정 기록 전체 CSV</a></li><li><a href="data/seoul-2025-documents.csv">서울 수집 상세문서 목록 CSV</a></li><li><a href="data/review-held.json">보류 항목·이유 JSON</a></li><li><a href="data/quality-status.json">검증 상태 JSON</a></li></ul>'
    b=card('출처와 재현 자료',f'<p>공식 홈페이지 링크가 있다고 개별 수치가 검증되는 것은 아닙니다. 서울 표본은 상세문서·행 번호까지 연결했으며 다른 지역은 이전 집계값의 출처 연결이 아직 확보되지 않았습니다. 지역마다 이 상태를 동일하게 표시합니다.</p>{links}')+card('필드 정의',glossary)+card('지역별 상태','<table><tr><th>지역</th><th>현재 확인 상태</th><th>표시 후보</th></tr>'+''.join(f'<tr><td><a href="regions/{r["slug"]}.html">{H(r["city"])}</a></td><td>{"선정 원문행 재집계" if r["slug"]=="seoul_city" else "기존 집계 · 원문 연결 보류"}</td><td>{len(r["items"])}개</td></tr>' for r in catalogue)+'</table>')
    page('출처·데이터 내려받기',b,'sources.html')
    b=card('2025년 자료 현황',f'<p>현재 {len(catalogue)}개 지역 자료를 제공합니다. 서로 다른 수집 범위와 미검증 분모를 합쳐 “전국 751,616건”이라고 제시하던 통계와 지역 간 식당 순위는 철회했습니다. 아래는 데이터의 검토 상태이며 전국 외식 시장 통계가 아닙니다.</p><ul><li>서울: 공식 수집문서 {ev["source_documents"]:,}개에서 지정 상호·주소의 {ev["selected_records"]:,}개 기록 재집계</li><li>그 밖의 228개 지역: 기존 집계 후보, 원문 연결 보류</li><li>기존 목록에서 비식당·오매칭·이상금액 등 {len(held)}개 보류</li><li>전체 식당 수와 전체 식당 결제 수: 미확인</li></ul>')+card('상호를 합치는 방식이 결론을 바꿉니다','<p>서울의 브이아이피참치는 기존 한 줄에서 여러 주소를 함께 세었을 가능성이 있습니다. 재집계에서는 세종대로11길·세종대로22길·을지로·세종대로를 분리했습니다. “같은 상호가 여러 번 나온다”와 “한 식당에 결제가 집중된다”는 서로 다른 주장입니다.</p><p>이 차이를 직접 확인할 수 있도록 <a href="regions/seoul_city.html">서울 원문 분석</a>에 주소별 기록, 필터와 원문 표본을 공개했습니다. 다른 지역의 순위 비교는 원문 연결과 동일 모집단을 확보한 다음 진행합니다.</p>')+card('데이터 내려받기',links)
    page('2025 자료 검토 현황',b,'report-2025.html')
    b=card('2026-10-12 정정',f'<p>이번 정정은 애드센스 승인 여부와 관계없이 유지하는 데이터 품질 수정입니다.</p><ol><li>229개 지역의 total_posts를 고유 식당 수로 해석한 표시를 철회했습니다. 종전 지표를 같은 모집단으로 읽으면 모순인 지역은 {len(anomalies)}개입니다. 다른 지역도 논리식 통과만으로 고유 식당 수가 증명되지는 않습니다.</li><li>문서 키 수를 부서 수로 해석한 표시를 철회했습니다. 서울만 실제 원문 부서명으로 다시 계산했습니다.</li><li>비식당·카페·장소 오매칭 의심·고액 이상 항목 {len(held)}개를 보류해 지도·후보표·요약에서 제외했습니다. 원본은 보존하고 대체 순위를 만들어 넣지 않았습니다.</li><li>서울에서 상호·주소별 원문 재집계를 제공하고 전체 서울 순위로 표현하지 않습니다.</li><li>전국 비교, 지역 전체 대비 점유율, 접대·인원·부서 이용에 대한 입증되지 않은 설명을 삭제했습니다.</li><li>제주 매출 분석의 연속 영업·폐업 해석을 두 시점 재관측으로 수정했습니다. 원자료 업종 필터를 일관 적용해 상위 50개 재관측률을 68%로 재계산했으며 일반 유흥 주점은 표시에서 제외했습니다. 동별 지도는 상위 5개 중 연결된 후보이며 1위 목록이 아닙니다. 중복 행 수를 개월 수로 세던 값은 고유 월수로 수정했습니다.</li><li>자료·검토 페이지에서 광고 송출 코드를 제거하고 소유권 확인 정보를 유지했습니다.</li></ol><p><a href="data/quality-status.json">지역별 검사 상태</a> · <a href="data/review-held.json">보류 항목 전체</a></p>')+card('아직 확인하지 못한 것','<p>전국 원문 거래행 복원, 원문 수집 완전성, 현재 영업 상태, 지도 장소의 전수 대조는 끝나지 않았습니다. 서울도 선정 표본에 대한 재집계이며 전체 식당 모집단 검증이 아닙니다. 이 한계는 검색 색인 설정이나 광고 승인 결과로 대체되지 않습니다.</p>')
    page('정정 이력',b,'corrections.html')
    regs=[]; top=[]
    for r in catalogue:
        regs.append({'지역코드':r['slug'],'지역':r['city'],'확인상태':r['status'],'표시후보수':len(r['items']),'표시기록합':r['display_record_sum'],'전체식당결제수':'','고유식당수':'','범위':r['scope'],'이전집계값_미검증':r['legacy_record_value'],'이전total_posts_의미미확인':r['legacy_total_posts']})
        for i in r['items']:
            top.append({'지역코드':r['slug'],'지역':r['city'],'기존번호_표시순서':i['r'],'식당명':i['n'],'업종':i['c'],'결제횟수':i['v'],'집행액(원)':i['a'],'회당평균(원)':round(i['a']/i['v']),'원문부서명수':i['d'] if i['d'] is not None else '', '주소':i['ad'],'확인상태':i['status']})
    write_csv(DATA/'segeummatjib-2025-regions.csv',list(regs[0]),regs)
    write_csv(DATA/'segeummatjib-2025-top10.csv',list(top[0]),top)
    write_csv(DATA/'seoul-2025-selected-records.csv',list(ev['rows'][0]),ev['rows'])
    write_csv(DATA/'seoul-2025-documents.csv',['id','title','url'],ev['documents'])
    urls=['','about.html','contact.html','privacy.html','method.html','sources.html','report-2025.html','corrections.html','regions/seoul_city.html','maechul/']
    (ROOT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>https://gyyi0718.github.io/{u}</loc><lastmod>{DATE}</lastmod></url>' for u in urls)+'</urlset>')

def render_map(catalogue):
    s=(INPUT/'map-template.txt').read_text()
    s=re.sub(r'<script[^>]*adsbygoogle[^>]*></script>', '', s)
    s=s.replace('</head>','<meta name="google-adsense-account" content="ca-pub-3133301641364865"><link rel="canonical" href="https://gyyi0718.github.io/"></head>')
    s=re.sub(r'<title>.*?</title>', '<title>세금맛집 — 공개 업무추진비 식당 후보·원문 분석</title>', s)
    s=re.sub(r'<meta name="description"[^>]*>', '<meta name="description" content="공개 업무추진비의 식당 후보와 원문을 연결합니다. 서울 주소별 재집계와 지역별 자료 확인 상태를 제공합니다.">',s)
    intro='<section id="intro"><h1>기록에서 찾는 식당, 원문에서 확인하는 숫자</h1><p>2025년 공개 업무추진비를 식당 후보별로 읽어봅니다. <b>서울은 선정한 9개 상호를 원문 주소별로 재집계</b>했고, 다른 지역은 기존 집계의 확인 상태를 함께 보여드립니다. 지도 번호는 기존 자료 번호이며 맛 순위나 전국 순위가 아닙니다.</p><p><a href="regions/seoul_city.html">서울 원문 분석 읽기</a> · <a href="corrections.html">10월 12일 정정 이력</a> · <a href="sources.html">자료 내려받기</a></p><p class="cav">원문이 다시 연결되지 않은 지역의 건수·금액은 기존 집계값입니다. 비식당·오매칭·이상금액 항목은 보류했습니다. 전체 식당 수와 전국 합계는 제시하지 않습니다.</p></section>'
    s=re.sub(r'<section id="intro">.*?</section>', lambda m:intro,s,flags=re.S)
    listing='<section id="allregions"><h2>지역별 후보와 확인 상태</h2>'
    for sido in dict.fromkeys(r['sido'] for r in catalogue):
        listing+='<section class="sidoblk"><h3>'+H(sido)+'</h3><ul>'
        for r in catalogue:
            if r['sido']!=sido:continue
            listing+=f'<li><a href="regions/{r["slug"]}.html">{H(r["city"])}</a><span>'+('선정 원문행 재집계' if r['slug']=='seoul_city' else '기존 후보 · 원문 연결 보류')+f' · {len(r["items"])}개</span></li>'
        listing+='</ul></section>'
    listing+='</section>'
    start=s.index('<section id="allregions">'); end=s.index('<style>',start)
    s=s[:start]+listing+'\n'+s[end:]
    maps=[]
    for r in catalogue:
        maps.append({**r,'tr':r['display_record_sum'],'tp':None})
    s=re.sub(r'const REGIONS_2025=\[.*?\];',lambda m:'const REGIONS_2025='+json.dumps(maps,ensure_ascii=False,separators=(',',':'))+';',s,flags=re.S)
    s=s.replace('${e.r}위 ${e.n}','번호 ${e.r} · ${e.n}').replace('📋 TOP10 게시글','📋 자료·확인 상태')
    s=s.replace('2025 ${rg.city} 맛집 TOP10','2025 ${rg.city} 식당 후보 자료')
    s=s.replace('공무원들이 ${t1.v}번 간 ${t1.n} — 업무추진비 ${fmt(rg.tr)}건 집계','표시한 ${rg.items.length}개 항목 · 기록 합 ${fmt(rg.tr)}건 (지역 전체 통계 아님)')
    s=s.replace('1위 ${t1.n} (${t1.v}회)<br>집계 ${fmt(r.tr)}건','${r.items.length}개 후보<br>${r.slug===\'seoul_city\'?\'선정 원문 재집계\':\'원문 연결 보류\'}')
    s=s.replace('광고가 아니라 <b>세금으로 실제 결제된 기록</b>으로 만든 순위입니다.','현재 페이지의 숫자는 지역별 확인 상태와 함께 읽어 주세요.')
    s=s.replace('${rg.city} 상세 분석 페이지','${rg.city} 자료와 확인 상태').replace('연간 <b>${e.v}회</b> 결제','기록 <b>${e.v}회</b>')
    s=s.replace('전국 지자체 2025년 업무추진비 공개자료 전수 집계','2025년 업무추진비 기존 집계 후보와 서울 선정 원문 분석')
    s=s.replace('2025 전국 밥상 리포트','2025 자료 검토 현황').replace('5년을 버틴 제주 식당','2021·2025 두 시점 제주 식당').replace('5년 내내','두 해 모두')
    s=s.replace('기본지도 (호스팅하면 카카오맵으로 전환)','기본지도').replace('연말에 한 상 차려서 올릴게요. 지금은 2025년 결산을 구경해 주세요.','검토가 끝난 자료부터 반영합니다. 지금은 2025년 자료를 확인해 주세요.')
    s=s.replace('지자체들이 업무추진비를 매월 공개하는 대로 모아서,','현재 게시 자료의 정확성을 먼저 점검하고,')
    s=s.replace('>1위 ', '>번호 1 ').replace('>2~3위', '>번호 2~3').replace('>4~10위', '>번호 4~10').replace('멀리서는 1~3위만', '멀리서는 번호 1~3만').replace('📊 전국 리포트','📊 자료 현황')
    s=s.replace('개 부서 이용','개 원문 부서명')
    s=s.replace('</header>', '</header><aside style="padding:12px 18px;background:#fff6db;font-size:14px;line-height:1.7">지역별 원문 확인 상태를 먼저 읽어 주세요. <a href="regions/seoul_city.html">서울 주소별 재집계</a> · <a href="corrections.html">정정 이력</a><br>서울 재집계 항목은 주소를 다시 확인하는 동안 지도 좌표 대신 상세 목록에서 제공합니다.</aside>',1)
    (ROOT/'index.html').write_text(s)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--refresh-seoul');args=ap.parse_args()
    if args.refresh_seoul: refresh_seoul(args.refresh_seoul)
    result=build_catalogue();render(*result)
    print(json.dumps({'regions':len(result[0]),'held':len(result[1]),'seoul_selected_records':result[2]['selected_records'],'legacy_conflicts':len(result[3])},ensure_ascii=False))
