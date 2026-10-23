"""python3 editorial-calculations.py seoul-directory-records.csv editorial-times.csv
Print reproducible 2025 institution geography and explicit-meal time aggregates.
Only Python standard library. Place keys are published spelling/address groups.
"""
import csv,json,sys,collections,itertools

def calculate(records,times):
 rows=[r for r in records if r['date'].startswith('2025-')]
 orgs=sorted({r['organization'] for r in rows}); summaries=[]; districts=[];monthly=[]
 sets={o:{r['place_id'] for r in rows if r['organization']==o} for o in orgs}
 for o in orgs:
  rs=[r for r in rows if r['organization']==o]; shares=[]
  for m in range(1,13):
   mm=[r for r in rs if r['date'][5:7]==f'{m:02}'];central=sum(r['district'] in ('중구','종로구') for r in mm)
   shares.append(central/len(mm));monthly.append(dict(organization=o,month=f'2025-{m:02}',rows=len(mm),central_rows=central,central_share=central/len(mm)))
  central=sum(r['district'] in ('중구','종로구') for r in rs)
  summaries.append(dict(organization=o,rows=len(rs),places=len(sets[o]),districts=len({r['district'] for r in rs}),documents=len({r['source_id'] for r in rs}),central_rows=central,central_share=central/len(rs),equal_month_share=sum(shares)/12,meal_rows=sum(r['purpose_category']=='meal' for r in rs),not_in_city=len(sets[o]-sets['seoul_city'])))
  for d in sorted({r['district'] for r in rows}):
   sub=[r for r in rs if r['district']==d];districts.append(dict(organization=o,district=d,rows=len(sub),places=len({r['place_id'] for r in sub}),share=len(sub)/len(rs)))
 groups=collections.defaultdict(list)
 for r in rows:groups[r['place_id']].append(r)
 strict={p for p,rr in groups.items() if len({r['source_id'] for r in rr})>=5 and len({r['date'][:7] for r in rr})>=3}
 for item in summaries:
  rr=[r for r in rows if r['place_id'] in strict and r['organization']==item['organization']]
  item['strict_2025_rows']=len(rr);item['strict_2025_places']=len({r['place_id'] for r in rr});item['strict_2025_central_share']=sum(r['district'] in ('중구','종로구') for r in rr)/len(rr)
 office_extra=[]
 for pid in sorted(sets['seoul_office']-sets['seoul_city']):
  rr=sorted([r for r in rows if r['place_id']==pid and r['organization']=='seoul_office'],key=lambda r:(r['date'],r['source_id'],int(r['parsed_row'])))
  office_extra.append(dict(place_id=pid,name=rr[0]['name'],address=rr[0]['address'],district=rr[0]['district'],rows=len(rr),documents=len({r['source_id'] for r in rr}),meal_rows=sum(r['purpose_category']=='meal' for r in rr),source_url=rr[0]['source_url']))
 overlaps=[dict(a=a,b=b,intersection=len(sets[a]&sets[b]),union=len(sets[a]|sets[b]),only_a=len(sets[a]-sets[b]),only_b=len(sets[b]-sets[a])) for a,b in itertools.combinations(orgs,2)]
 byid=collections.defaultdict(list)
 for r in times:byid[r['place_id']].append(r)
 time_places=[]
 for pid,rs in sorted(byid.items()):
  if len({r['source_id'] for r in rs})<3:continue
  time_places.append(dict(place_id=pid,name=rs[0]['name'],address=rs[0]['address'],district=rs[0]['district'],rows=len(rs),documents=len({r['source_id'] for r in rs}),midday=sum(11<=int(r['hour'])<15 for r in rs),evening=sum(17<=int(r['hour'])<22 for r in rs),other=sum(not (11<=int(r['hour'])<15 or 17<=int(r['hour'])<22) for r in rs)))
 return dict(period=['2025-01-01','2025-12-31'],rows=len(rows),places=len({r['place_id'] for r in rows}),organizations=summaries,districts=districts,monthly=monthly,overlap=overlaps,office_extra=office_extra,purpose_counts=dict(collections.Counter(r['purpose_category'] for r in rows)),time_rows=len(times),hours=[dict(hour=h,rows=sum(int(r['hour'])==h for r in times)) for h in range(24)],time_places=time_places)
if __name__=='__main__':
 with open(sys.argv[1],encoding='utf-8-sig') as f:records=list(csv.DictReader(f))
 with open(sys.argv[2],encoding='utf-8-sig') as f:times=list(csv.DictReader(f))
 print(json.dumps(calculate(records,times),ensure_ascii=False,indent=2))
