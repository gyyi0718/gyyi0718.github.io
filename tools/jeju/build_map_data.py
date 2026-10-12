# -*- coding: utf-8 -*-
"""동별 공개지표 합계 상위 후보 산출. 원화 매출 순위와 배수를 주장하지 않는다."""
import csv, glob, json, collections, os

WINDOW = [f"2025{m:02d}" for m in range(1, 13)]   # 공통 비교기간 12개월
FOOD = {'한식','카페','술집','간식','양식','치킨','분식','중식','일식',
        '패스트푸드','아시아음식','뷔페','샤브샤브','퓨전요리','도시락','제과제빵','미분류'}
DROP = {'유흥시설','숙박','식품판매','식품'}

agg = collections.defaultdict(lambda: {'rate': 0.0, 'months': set(), 'row_count': 0, 'mls': '', 'scl': '', 'sgg': ''})
for ym in WINDOW:
    path = f'jeju/JT_SHP_SALES_VARTION_LIST_{ym}.csv'
    if not os.path.exists(path):
        raise RuntimeError(f'Missing required month {ym}')
    for r in csv.DictReader(open(path, encoding='utf-8-sig')):
        if r['MLSFC_NM'] in DROP or r['MLSFC_NM'] not in FOOD:
            continue
        try:
            v = float(r['ALL_SALES_PRICE_RATE'])
        except ValueError:
            continue
        k = (r['CMPNM_NM'].strip(), r['ADSTRD_NM'].strip())
        a = agg[k]
        a['rate'] += v; a['months'].add(ym); a['row_count'] += 1
        a['mls'] = r['MLSFC_NM']; a['scl'] = r['SCLAS_NM']; a['sgg'] = r['SIGNGU_NM']

print(f'집계 점포 {len(agg):,}개 / 동 {len(set(k[1] for k in agg))}개')

# 동별 상위
by_dong = collections.defaultdict(list)
for (nm, dong), a in agg.items():
    by_dong[dong].append({'nm': nm, 'dong': dong, **a, 'months': len(a['months'])})
out = {}
for dong, lst in by_dong.items():
    lst.sort(key=lambda x: -x['rate'])
    out[dong] = lst[:5]          # 1위 + 예비 4곳(매칭 실패 대비)

json.dump(out, open('jeju/map_top_by_dong.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
cov = collections.Counter(x[0]['months'] for x in out.values())
print('동별 1위의 관측 월수 분포:', dict(sorted(cov.items())))
print('저장: jeju/map_top_by_dong.json')
