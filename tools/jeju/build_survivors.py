# -*- coding: utf-8 -*-
"""제주 두 시점 재관측 — 동일 상호·행정동 키 비교. 영업 연속성이나 폐업을 추론하지 않는다."""
import csv, json, re, unicodedata, collections
from jeju_review import FOOD, allowed_store
from difflib import SequenceMatcher
DROP={'유흥시설','숙박','식품판매','식품'}
def year(y):
    agg=collections.defaultdict(float); meta={}
    for m in range(1,13):
        try: f=open(f'jeju/JT_SHP_SALES_VARTION_LIST_{y}{m:02d}.csv',encoding='utf-8-sig')
        except FileNotFoundError: raise RuntimeError(f'Missing required month {y}{m:02d}')
        for r in csv.DictReader(f):
            if r['MLSFC_NM'] in DROP or r['MLSFC_NM'] not in FOOD: continue
            try: v=float(r['ALL_SALES_PRICE_RATE'])
            except ValueError: continue
            k=(r['CMPNM_NM'].strip(), r['ADSTRD_NM'].strip())
            agg[k]+=v; meta[k]=(r['MLSFC_NM'], r['SIGNGU_NM'])
    return agg, meta
a21,_=year(2021); a25,m25=year(2025)
top21={k for k,_ in sorted(a21.items(),key=lambda x:-x[1])[:300]}
top25={k for k,_ in sorted(a25.items(),key=lambda x:-x[1])[:300]}
both=sorted(top21 & top25, key=lambda k:-a25[k])
stats={'metric': 'same_name_dong_reobservation', 'years': [2021, 2025], 'intermediate_years_checked': False, 'closure_verified': False, 'n21':len(a21),'n25':len(a25),
       'surv':{N: sum(1 for k,_ in sorted(a21.items(),key=lambda x:-x[1])[:N] if k in a25)/N*100
               for N in (50,100,300,1000)},
       'survall': sum(1 for k in a21 if k in a25)/len(a21)*100}

stores=[json.loads(l) for l in open('jeju_stores.jsonl',encoding='utf-8')]
def norm(s):
    s=unicodedata.normalize('NFKC',str(s or ''))
    s=re.sub(r'주식회사|㈜|\(주\)|유한회사|\(유\)','',s)
    return re.sub(r'[^0-9A-Za-z가-힣]','',s)
idx=collections.defaultdict(list)
for s in stores:
    if s.get('indsLclsNm')!='음식': continue
    s['_n']=norm(s.get('bizesNm'))+norm(s.get('brchNm')); s['_b']=norm(s.get('bizesNm'))
    idx[s.get('adongNm','')].append(s)
def find(nm,dong):
    t=norm(nm); best,bs=None,0.0
    for s in idx.get(dong,[]):
        for c in (s['_b'],s['_n']):
            if not c: continue
            r=SequenceMatcher(None,t,c).ratio()
            if r>bs: bs,best=r,s
    return (best,bs) if bs>=0.78 else (None,bs)

AIR=re.compile(r'공항')
out=[]
for k in both:
    nm,dong=k; st,sc=find(nm,dong)
    mls,sgg=m25.get(k,('',''))
    out.append({'nm':nm,'dong':dong,'sgg':sgg,'mls':mls,
                'v21':round(a21[k],2),'v25':round(a25[k],2),
                'growth':round((a25[k]/a21[k]-1)*100,1) if a21[k] else None,
                'air':1 if AIR.search(nm) else 0,
                'lat':st['lat'] if st and allowed_store(st) else None,'lon':st['lon'] if st and allowed_store(st) else None,
                'addr':(st.get('rdnmAdr') or st.get('lnoAdr')) if st else None,
                'inds':st.get('indsSclsNm') if st else None, 'display_exclusion': 'prohibited_classification' if st and not allowed_store(st) else None, 'match_score': round(sc, 3) if st else None})
geo=[x for x in out if x['lat']]
print(f"2021·2025 둘 다 상위300 = {len(out)}곳 | 좌표 확보 {len(geo)}곳 | 공항 {sum(x['air'] for x in out)}곳")
json.dump({'stats':stats,'items':out},open('jeju/survivors.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('동일 상호·행정동 재관측률:', {k:round(v,1) for k,v in stats['surv'].items()}, '| 전체', round(stats['survall'],1))
