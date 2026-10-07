#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""손으로 쓰지 않은 지역 페이지를 색인에서 제외한다.

템플릿으로 생성된 페이지는 noindex, follow 로 둔다.
- noindex : 검색 색인에 올리지 않는다(대량 생성 페이지로 보이지 않게)
- follow  : 링크는 따라가게 두어 지도·리포트 등 본문 페이지로 크롤러가 흐르게 한다
사이트에서 링크는 그대로 살아 있으므로 사람은 평소대로 볼 수 있다.
"""
import os, re, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = '<meta name="robots" content="noindex, follow">'
NOTE = ('<p class="body" style="font-size:13.5px;color:#888;border-top:1px solid #eee;padding-top:14px;margin-top:18px">'
        '이 페이지는 공개된 집행내역을 집계해 자동으로 만든 <b>데이터 표</b>입니다. '
        '지역을 직접 분석해 쓴 글은 <a href="../index.html" style="color:#0B9D58">메인 지도</a>에서 '
        '따로 모아 두었고, 집계 결과 전체는 <a href="../sources.html" style="color:#0B9D58">CSV</a>로 공개합니다.</p>')

added, skipped = 0, 0
for p in sorted(glob.glob(os.path.join(ROOT, 'regions', '*.html'))):
    h = open(p, encoding='utf-8').read()
    if '<!-- hand-written -->' in h:
        # 손으로 쓴 페이지에 noindex 가 잘못 들어가 있으면 걷어낸다
        if TAG in h:
            open(p, 'w', encoding='utf-8').write(h.replace(TAG + '\n', '').replace(TAG, ''))
        skipped += 1
        continue
    if TAG in h:
        skipped += 1
        continue
    h = h.replace('<meta name="viewport"', TAG + '\n<meta name="viewport"', 1)
    anchor = '<div class="card"><h2>이 순위는 이렇게 만들었습니다</h2>'
    if anchor in h and '자동으로 만든 <b>데이터 표</b>' not in h:
        h = h.replace(anchor, anchor + '\n' + NOTE, 1)
    open(p, 'w', encoding='utf-8').write(h)
    added += 1

print(f'noindex 적용 {added}곳 · 손글/기적용 제외 {skipped}곳')
