#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""손으로 쓴 30곳 원고를 지역 페이지에 반영한다.

- title / og:title / description / h1 을 원고의 것으로 교체
- '데이터로 읽는 X 밥상' 카드 본문을 원고 본문으로 교체
- 손으로 쓴 페이지임을 표시하는 마커를 남겨 noindex 대상에서 제외한다
"""
import sys, os, re, html as H
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'prose'))
import batch1, batch2, batch3, batch4, batch5

P = {}
for b in (batch1, batch2, batch3, batch4, batch5):
    P.update(b.P)

MARK = '<!-- hand-written -->'
done, skip = 0, []

for slug, v in P.items():
    path = os.path.join(ROOT, 'regions', f'{slug}.html')
    if not os.path.exists(path):
        skip.append((slug, '파일 없음')); continue
    h = open(path, encoding='utf-8').read()
    if MARK in h:
        skip.append((slug, '이미 반영')); continue
    o = h
    t, d, h1 = H.escape(v['title']), H.escape(v['desc'].strip()), H.escape(v['h1'])

    h = re.sub(r'<title>.*?</title>', f'<title>{t}</title>', h, count=1, flags=re.S)
    h = re.sub(r'(<meta name="description" content=")[^"]*(")', lambda m: m.group(1)+d+m.group(2), h, count=1)
    h = re.sub(r'(<meta property="og:title" content=")[^"]*(")', lambda m: m.group(1)+t+m.group(2), h, count=1)
    h = re.sub(r'(<meta property="og:description" content=")[^"]*(")', lambda m: m.group(1)+d+m.group(2), h, count=1)
    h = re.sub(r'<h1>.*?</h1>', f'<h1>{h1}</h1>', h, count=1, flags=re.S)

    # 분석 카드 본문 교체
    m = re.search(r'(<div class="card"><h2>데이터로 읽는 .*?</h2>)(.*?)(</div>)', h, re.S)
    if not m:
        skip.append((slug, '분석 카드 못 찾음')); continue
    body = v['body'].strip() + '\n'
    h = h[:m.start(1)] + f'<div class="card"><h2>{h1.replace("2025 ","").replace(" 업무추진비 맛집 TOP10","")} 데이터 읽기</h2>\n' + body + m.group(3) + h[m.end(3):]

    h = h.replace('<!DOCTYPE html>', MARK + '\n<!DOCTYPE html>', 1)
    if h != o:
        open(path, 'w', encoding='utf-8').write(h); done += 1

print(f'반영 {done}곳 / 건너뜀 {len(skip)}')
for s, why in skip: print(f'  {s:16} {why}')
