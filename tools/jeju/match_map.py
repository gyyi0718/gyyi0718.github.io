# -*- coding: utf-8 -*-
"""동별 상위 후보를 소상공인 상가정보와 매칭해 좌표를 붙이고 업종을 검증한다.
상가정보에서 '음식'으로 확인된 곳만 남긴다 → 리조트·법인·판매점이 걸러진다."""
import json, re, unicodedata, collections
from difflib import SequenceMatcher
from jeju_review import allowed_store

stores = [json.loads(l) for l in open('jeju_stores.jsonl', encoding='utf-8')]

def norm(s):
    s = unicodedata.normalize('NFKC', str(s or ''))
    s = re.sub(r'주식회사|㈜|\(주\)|유한회사|\(유\)|\(주식회사\)', '', s)
    return re.sub(r'[^0-9A-Za-z가-힣]', '', s)

def base(s):
    return re.sub(r'(본점|점|지점|직영점)$', '', s)

idx = collections.defaultdict(list)
for st in stores:
    idx[st.get('adongNm', '')].append((norm(st.get('bizesNm')) + norm(st.get('brchNm')),
                                       norm(st.get('bizesNm')), st))

def find(name, dong):
    tgt = norm(name); tgtb = base(tgt)
    best, bs = None, 0.0
    for full, only, st in idx.get(dong, []):
        for c in (full, only):
            if not c:
                continue
            r = SequenceMatcher(None, tgt, c).ratio()
            rb = SequenceMatcher(None, tgtb, base(c)).ratio()
            sc = max(r, rb) + (0.15 if tgtb and tgtb in c else 0)
            if sc > bs:
                bs, best = sc, st
    return best, bs

top = json.load(open('jeju/map_top_by_dong.json', encoding='utf-8'))
picked, dropped = {}, []
for dong, cands in top.items():
    if not dong.strip():
        continue
    for c in cands:                       # 1위부터, 음식으로 확인될 때까지 내려감
        st, sc = find(c['nm'], dong)
        if st and sc >= 0.75 and allowed_store(st):
            picked[dong] = {**c, 'lat': st['lat'], 'lon': st['lon'],
                            'addr': st.get('rdnmAdr') or st.get('lnoAdr'),
                            'inds': st.get('indsSclsNm'), 'matched': st.get('bizesNm'),
                            'score': round(sc, 2), 'demoted': cands.index(c)}
            break
    else:
        dropped.append(dong)

json.dump(picked, open('jeju/map_points.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print(f'매칭 성공 {len(picked)}개 동 / 실패 {len(dropped)}개 {dropped}')
print(f"1위 그대로 채택 {sum(1 for v in picked.values() if v['demoted']==0)}개, "
      f"아래 순위로 내려간 동 {sum(1 for v in picked.values() if v['demoted']>0)}개")
