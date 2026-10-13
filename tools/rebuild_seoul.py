#!/usr/bin/env python3
"""Rebuild the fixed Seoul sample from saved source JSONL; does not restore retired regions."""
import re,json,datetime,argparse
from pathlib import Path
from collections import Counter
DATE='2026-10-13'
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

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('input_dir',type=Path);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();DATA=a.output_dir;DATA.mkdir(parents=True,exist_ok=True);refresh_seoul(a.input_dir)
