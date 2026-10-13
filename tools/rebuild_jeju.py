#!/usr/bin/env python3
"""Recompute observation data from the 24 named source CSVs; no geolocation or sales inference."""
from pathlib import Path
from collections import defaultdict,Counter
import csv,json,hashlib,argparse,io
FOOD={'한식','카페','술집','간식','양식','치킨','분식','중식','일식','패스트푸드','아시아음식','뷔페','샤브샤브','퓨전요리','도시락','제과제빵'}
def compute(base):
 years={};broad={};unknown={};categories={};inputs=[];monthly=[];excluded=Counter()
 for y in (2021,2025):
  keys=defaultdict(set);bs=set();us=set();cats=Counter()
  for m in range(1,13):
   p=base/f'JT_SHP_SALES_VARTION_LIST_{y}{m:02}.csv';raw=p.read_bytes();inputs.append(dict(file=p.name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()));ms=set();n=0
   for r in csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))):
    assert r['ANALS_YM']==f'{y}{m:02}',f'Unexpected period in {p.name}'
    c=r['MLSFC_NM'];cats[c]+=1;k=tuple(r[x].strip() for x in ('CMPNM_NM','SIGNGU_NM','ADSTRD_NM'))
    if not all(k):excluded['missing_name_or_area']+=1;continue
    if c in FOOD|{'미분류'}:bs.add(k)
    if c=='미분류':us.add(k)
    if c not in FOOD:excluded[c]+=1;continue
    n+=1;keys[k].add(m);ms.add(k)
   monthly.append(dict(year=y,month=m,rows=n,keys=len(ms),extra_rows=n-len(ms)))
  years[y]=keys;broad[y]=bs;unknown[y]=us;categories[str(y)]=dict(cats)
 a,b=years[2021],years[2025];dongs=[]
 for s,d in sorted({(k[1],k[2]) for k in set(a)|set(b)}):
  ak={k for k in a if k[1:]==(s,d)};bk={k for k in b if k[1:]==(s,d)}
  dongs.append(dict(city=s,dong=d,keys2021=len(ak),keys2025=len(bk),reobserved=len(ak&bk),not_reobserved=len(ak-bk),only2025=len(bk-ak),all12_2021=sum(len(a[k])==12 for k in ak),all12_2025=sum(len(b[k])==12 for k in bk)))
 return dict(years=[2021,2025],key_fields=['CMPNM_NM','SIGNGU_NM','ADSTRD_NM'],included_categories=sorted(FOOD),excluded_rows=dict(excluded),keys2021=len(a),keys2025=len(b),reobserved=len(set(a)&set(b)),not_reobserved=len(set(a)-set(b)),only2025=len(set(b)-set(a)),monthly=monthly,dongs=dongs,month_histogram={str(y):dict(Counter(len(v) for v in years[y].values())) for y in years},inputs=inputs,source_url='https://www.bigdata-culture.kr/bigdata/user/data_market/detail.do?id=f0306b70-597a-11ec-8ee4-95f65f846b27',category_counts=categories,sensitivity=dict(broad2021=len(broad[2021]),broad2025=len(broad[2025]),broad_reobserved=len(broad[2021]&broad[2025]),unclassified_keys2021=len(unknown[2021]),unclassified_keys2025=len(unknown[2025])))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('input_dir',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.write_text(json.dumps(compute(a.input_dir),ensure_ascii=False,indent=2)+'\n');print(a.output)
