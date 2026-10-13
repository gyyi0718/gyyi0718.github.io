#!/usr/bin/env python3
"""Output consistency + independent semantic checks; not a nationwide source audit."""
import csv, json, re, sys, html
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1]
def check_evidence(ev, cat):
 rows=ev['rows']; keys=[(x['source_id'],x['parsed_row']) for x in rows]
 assert len(keys)==len(set(keys)), 'duplicate source document/row'
 groups=defaultdict(list)
 for x in rows:
  assert x['date'].startswith('2025-') and x['amount']>0
  assert x['source_url']=='https://opengov.seoul.go.kr/expense/'+x['source_id'].split(':')[-1]
  groups[(x['merchant'],x['road_address'])].append(x)
 seoul=next(x for x in cat if x['slug']=='seoul_city')
 assert len(rows)==ev['selected_records']==seoul['selected_transaction_count']
 assert len(groups)==seoul['selected_merchant_address_count']==len(seoul['items'])
 assert sum(i['v'] for i in seoul['items'])==len(rows)
 for i in seoul['items']:
  group=groups[(i['n'],i['ad'])]
  assert len(group)==i['v']
  assert sum(x['amount'] for x in group)==i['a']
  assert len({x['department'] for x in group if x['department']})==i['d']
 n=len(rows);u=len(groups);top=sorted((len(x) for x in groups.values()),reverse=True)[:10]
 assert u<=n-(sum(top)-len(top)) and n<=u*max(top)
def check_jeju():
 meta=json.loads((ROOT/'data/jeju-review.json').read_text())
 for filename,key in [('maechul/index.html','M'),('maechul/map.html','D')]:
  page=(ROOT/filename).read_text()
  data=json.loads(re.search(r'const '+key+r'=(\[.*?\]);',page,re.S)[1])
  assert all(32<float(x['lat'])<35 and 125<float(x['lon'])<128 for x in data),'Jeju coordinate bounds'
  assert all(not re.search(r'유흥|숙박|판매',x.get('inds') or '') for x in data),'prohibited Jeju category'
  assert len(data)==len({(x['nm'],x['dong']) for x in data}),'duplicate Jeju display key'
  assert meta['source_url'] in page,'missing Jeju primary source'
  assert not re.search(r'카드매출이 가장 큰|점포 간 순서와 배수는 비교|동별 매출 1위',page),'unsupported Jeju sales claim'
  if key=='D':
   assert len(data)==meta['map_points']
   assert all(1<=x['mon']<=12 for x in data),'row count confused with month count'
   assert all(1<=x['candidate_position']<=5 for x in data)
   assert sum(x['candidate_position']>1 for x in data)==meta['map_later_candidates']
  else:
   assert len(data)==meta['displayed_nonairport']
   assert f"{meta['stats']['surv']['50']:.0f}%" in page,'stale reobservation rate'
 return True

def main():
 check_jeju()
 cat=json.loads((ROOT/'data/catalogue.json').read_text())
 held=json.loads((ROOT/'data/review-held.json').read_text())
 ev=json.loads((ROOT/'data/seoul-2025-evidence.json').read_text())
 check_evidence(ev,cat)
 mutant={**ev,'rows':ev['rows']+[ev['rows'][0]]}
 try:check_evidence(mutant,cat)
 except AssertionError:pass
 else:raise AssertionError('duplicate-row regression failed')
 csvrows=list(csv.DictReader((ROOT/'data/segeummatjib-2025-top10.csv').open(encoding='utf-8-sig')))
 regrows=list(csv.DictReader((ROOT/'data/segeummatjib-2025-regions.csv').open(encoding='utf-8-sig')))
 assert len(cat)==len(regrows)==229
 assert len(csvrows)==sum(len(r['items']) for r in cat)
 keyed={(r['지역코드'],int(r['기존번호_표시순서'])):r for r in csvrows}
 all_items={(r['slug'],i['n'],i['ad']) for r in cat for i in r['items']}
 for h in held:assert (h['slug'],h['n'],h['ad']) not in all_items,'held item remains in catalogue'
 for r in cat:
  assert r['unique_restaurant_count'] is None and r['restaurant_transaction_count'] is None
  assert r['display_record_sum']==sum(i['v'] for i in r['items'])
  s=(ROOT/'regions'/f'{r["slug"]}.html').read_text()
  assert 'adsbygoogle.js' not in s and 'google-adsense-account' in s
  for i in r['items']:
   assert i['v']>0 and i['a']>0 and i['a']/i['v']<=1000000
   assert i['c'] not in ('여객선터미널','공원','정육점','컴퓨터주변기기','카페','농업')
   cr=keyed[(r['slug'],i['r'])]
   assert cr['식당명']==i['n'] and int(cr['결제횟수'])==i['v'] and int(cr['집행액(원)'])==i['a']
   assert html.escape(i['n']) in s and f'<b>{i["v"]}회</b>' in s
   if r['slug']!='seoul_city':assert i['d'] is None
 home=(ROOT/'index.html').read_text()
 mapdata=json.loads(re.search(r'const REGIONS_2025=(\[.*?\]);',home,re.S)[1])
 assert [(r['slug'],r['items']) for r in cat]==[(r['slug'],r['items']) for r in mapdata]
 for p in list((ROOT/'regions').glob('*.html'))+list(ROOT.glob('*.html'))+list((ROOT/'maechul').glob('*.html')):
  s=p.read_text()
  assert 'adsbygoogle.js' not in s,str(p)+' has ad serving script'
  if 'L.tileLayer(' in s:
   assert 'https://tile.openstreetmap.org/{z}/{x}/{y}.png' in s,'unexpected tile service'
   assert 'https://www.openstreetmap.org/copyright' in s,'missing map attribution'
   assert 'cartocdn.com' not in s,'key-required CARTO tile regression'
  assert not re.search(r'5년 내내|30%는 문을 닫|시청 거의 모든 부서|세금으로 검증된',s),str(p)+' unsupported claim'
  for ref in re.findall(r'href="([^"]+)"',s):
   if ref.startswith(('https:','http:','mailto:','javascript:','#','data:')) or '${' in ref:continue
   target=(ROOT/ref.lstrip('/')) if ref.startswith('/') else (p.parent/ref.split('#')[0].split('?')[0])
   assert target.exists(),f'missing local link {p}: {ref}'
 print(f'PASS: {len(cat)} regions; {len(csvrows)} candidate rows; {len(held)} held; {len(ev["rows"])} selected source rows.')
 print('Checked outputs, source-row uniqueness, grouped amounts/departments, population bounds, hold exclusion, links, claims. Nationwide original records not re-audited.')
if __name__=='__main__':
 try:main()
 except (AssertionError,KeyError,ValueError) as e:print('FAIL:',str(e));sys.exit(1)
