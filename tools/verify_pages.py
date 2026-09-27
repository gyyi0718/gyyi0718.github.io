#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""세금맛집 전수 검산 — 229개 지역 페이지의 숫자가 공개 CSV와 일치하는지 대조한다.

사용법:  python3 tools/verify_pages.py
대조 항목(페이지당 5개): 집계 건수 · 등장한 식당 수 · TOP10 비중 · 1위 식당명 · 1위 결제 횟수
불일치가 있으면 목록을 출력하고 exit code 1 로 끝난다.
"""
import csv, glob, os, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

def locate(name):
    """저장소 안, 스크립트 옆, 현재 폴더 어디에 두어도 찾아낸다."""
    for d in (os.path.join(ROOT, 'data'), HERE, os.getcwd(), ROOT):
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    sys.exit(f'{name} 을 찾을 수 없습니다. 내려받은 CSV를 이 스크립트와 같은 폴더에 두고 다시 실행해 주세요.')

TOP  = locate('segeummatjib-2025-top10.csv')
REGS = locate('segeummatjib-2025-regions.csv')

def num(x):
    try: return int(x)
    except (TypeError, ValueError): return None

def load():
    top = collections.defaultdict(list)
    for r in csv.DictReader(open(TOP, encoding='utf-8-sig')):
        top[r['지역코드']].append(r)
    regs = {r['지역코드']: r for r in csv.DictReader(open(REGS, encoding='utf-8-sig'))}
    return top, regs

def main():
    top, regs = load()
    bad, checked = [], 0
    pages = sorted(glob.glob(os.path.join(ROOT, 'regions', '*.html'))) \
            or sorted(glob.glob(os.path.join(os.getcwd(), 'regions', '*.html')))
    if not pages:
        sys.exit('regions/*.html 을 찾을 수 없습니다. 저장소 루트에서 실행해 주세요.')
    for path in pages:
        slug = os.path.basename(path)[:-5]
        if slug not in regs:
            bad.append((slug, 'CSV에 지역 없음', '')); continue
        html = open(path, encoding='utf-8').read()
        m, items = regs[slug], top[slug]
        rec, posts = num(m['집계건수']), num(m['등장식당수'])
        if rec is None:
            bad.append((slug, '집계건수 비숫자', m['집계건수'])); continue

        if f'{rec:,}건' not in html:
            bad.append((slug, '집계 건수', f'{rec:,}'))
        if posts is not None and f'{posts:,}곳' not in html:
            bad.append((slug, '등장한 식당 수', f'{posts:,}'))

        visits = sum(int(i['결제횟수']) for i in items)
        share = round(visits / rec * 100, 1)
        if f'{share}%' not in html:
            bad.append((slug, 'TOP10 비중', f'{share}%'))

        first = items[0]
        if first['식당명'] not in html:
            bad.append((slug, '1위 식당명', first['식당명']))
        if f"<b>{int(first['결제횟수'])}회</b>" not in html:
            bad.append((slug, '1위 결제 횟수', first['결제횟수']))
        checked += 1

    print(f'검증 {checked}개 · 불일치 {len(bad)}건')
    if bad:
        for slug, what, val in bad:
            print(f'  {slug:20} {what:16} CSV={val}')
        return 1
    print('모든 페이지의 숫자가 공개 CSV와 일치합니다.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
