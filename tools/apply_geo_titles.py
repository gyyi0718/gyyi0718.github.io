#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""지역 페이지 제목을 사람들이 실제로 검색하는 말("공무원 맛집")로 맞춘다.

- <title>, og:title : "2025 {지역} 업무추진비 맛집 TOP10" → "2025 {지역} 공무원 맛집 TOP10 (업무추진비 기준)"
- <h1>              : "2025 {지역} 공무원 맛집 TOP10"
- 첫 카드에 질문에 바로 답하는 한 문장을 넣는다 (AI 검색이 문단 단위로 인용하므로)
여러 번 돌려도 같은 결과가 나온다. noindex 여부는 건드리지 않는다.
"""
import os, re, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLD = re.compile(r'2025 (.+?) 업무추진비 맛집 TOP10')
META = re.compile(r'<p class="meta">공개된 업무추진비 결제 ([\d,]+)건 전수 집계 · 1위 (.+?) \((\d+)회\)</p>')
changed = 0
for p in sorted(glob.glob(os.path.join(ROOT, 'regions', '*.html'))):
    h0 = h = open(p, encoding='utf-8').read()
    m = re.search(r'<h1>2025 (.+?) (?:업무추진비|공무원) 맛집 TOP10', h)
    if not m:
        print('건너뜀(형식 다름):', os.path.basename(p)); continue
    region = m.group(1)
    h = re.sub(r'(<title>|og:title" content=")2025 (.+?) 업무추진비 맛집 TOP10',
               r'\g<1>2025 \2 공무원 맛집 TOP10 (업무추진비 기준)', h)
    h = h.replace(f'<h1>2025 {region} 업무추진비 맛집 TOP10', f'<h1>2025 {region} 공무원 맛집 TOP10')
    mm = META.search(h)
    if mm and 'class="body lead"' not in h:
        n, top, cnt = mm.groups()
        lead = (f'<p class="body lead">{region} 공무원들이 2025년 업무추진비로 가장 많이 결제한 식당은 '
                f'<b>{top}</b>({cnt}회)입니다. 공개된 결제 {n}건을 전부 세어 만든 순위입니다.</p>')
        h = h.replace(mm.group(0), mm.group(0) + '\n' + lead, 1)
    if h != h0:
        open(p, 'w', encoding='utf-8').write(h); changed += 1
print(f'수정 {changed}곳')
