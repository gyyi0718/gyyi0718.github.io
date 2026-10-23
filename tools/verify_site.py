#!/usr/bin/env python3
"""Verify publication boundaries, links and numeric identities without network access."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
from collections import defaultdict,Counter
import json,csv,statistics,re,xml.etree.ElementTree as ET,hashlib
ROOT=Path(__file__).resolve().parents[1]
class Page(HTMLParser):
 def __init__(self,text):self.links=[];self.ids=[];self.headings=[];self.meta=[];self.scripts=[];super().__init__();self.feed(text)
 def handle_starttag(self,t,attrs):
  a=dict(attrs)
  if a.get('id'):self.ids.append(a['id'])
  if t in ('a','link') and a.get('href'):self.links.append(a['href'])
  if t=='script':self.scripts.append(a.get('src',''))
  if t=='meta':self.meta.append(a)
  if t=='h1':self.headings.append(1)
def validate_rows(rows):
 keys=[(r['source_id'],r['parsed_row']) for r in rows];assert len(keys)==len(set(keys)),'duplicate row identity'
 for r in rows:
  assert re.fullmatch(r'2025-\d\d-\d\d',r['date']);assert r['amount']>0
  assert r['source_url']=='https://opengov.seoul.go.kr/expense/'+r['source_id'].split(':')[1]
def run():
 e=json.loads((ROOT/'data/seoul-2025-evidence.json').read_text());r=e['rows'];validate_rows(r)
 try:validate_rows(r+[r[0]])
 except AssertionError:pass
 else:raise AssertionError('duplicate-row regression failed')
 assert len(r)==2699 and sum(x['amount'] for x in r)==347526970
 assert statistics.median(x['amount'] for x in r)==105000
 groups=defaultdict(list)
 for x in r:groups[x['merchant'],x['road_address']].append(x)
 assert len(groups)==13 and len({k[0] for k in groups})==9
 csvrows=list(csv.DictReader((ROOT/'data/seoul-2025-selected-records.csv').open(encoding='utf-8-sig')))
 assert [{k:str(v) for k,v in x.items()} for x in r]==csvrows
 for x in csv.DictReader((ROOT/'data/seoul-groups.csv').open(encoding='utf-8-sig')):
  actual=groups[x['merchant'],x['address']];assert int(x['n'])==len(actual);assert int(x['amount'])==sum(t['amount'] for t in actual);assert int(x['median'])==statistics.median(t['amount'] for t in actual)
 for x in csv.DictReader((ROOT/'data/seoul-monthly.csv').open(encoding='utf-8-sig')):
  actual=[t for t in r if t['date'][:7]==x['month']];assert len(actual)==int(x['n']);assert sum(t['amount'] for t in actual)==int(x['amount']);assert len({t['source_id'] for t in actual})==int(x['documents'])
 j=json.loads((ROOT/'data/jeju-observation.json').read_text());assert (j['keys2021'],j['keys2025'],j['reobserved'])==(16109,12894,6582)
 assert (j['sensitivity']['broad2025'],j['sensitivity']['unclassified_keys2025'])==(19505,6703)
 assert j['excluded_rows']['missing_name_or_area']==38
 assert len(j['monthly'])==24 and len(j['dongs'])==43
 for field in ('keys2021','keys2025','reobserved','not_reobserved','only2025'):assert sum(x[field] for x in j['dongs'])==j[field]
 for y in ('2021','2025'):assert sum(j['month_histogram'][y].values())==j['keys'+y]
 assert j['month_histogram']['2021']['12']==9257 and j['month_histogram']['2025']['12']==9442
 assert all(x['rows']>=x['keys'] and x['extra_rows']==x['rows']-x['keys'] for x in j['monthly'])
 nationwide=json.loads((ROOT/'data/nationwide-locations.json').read_text());regions=nationwide['regions'];items=[i for r in regions for i in r['items']]
 assert len(regions)==229 and len({r['slug'] for r in regions})==229
 assert len({r['province'] for r in regions})==17 and len(items)==2189
 assert len({i['id'] for i in items})==2189
 assert sum(bool(i['coordinates']) for i in items)==2172
 assert sum(i['record_status']=='source_linked' for i in items)==13
 for i in items:
  assert not {'v','a','r','legacy_record_value','amount','rank','visits'}.intersection(i)
  if i['coordinates']:assert len(i['coordinates'])==2 and 32<i['coordinates'][0]<40 and 124<i['coordinates'][1]<133
  if i.get('sources'):assert all(x['url'].startswith('https://opengov.seoul.go.kr/expense/') for x in i['sources'])
 for name in ['index.html','map.html']:
  text=(ROOT/name).read_text()
  if name=='map.html':assert all('/map.html?region='+r['slug'] in text for r in regions)
  else:
   assert '/map.html#region-directory' in text
   assert 'id="region-directory"' not in text
   assert text.index('새 분석과 부서·월별 비교 도구')<text.index('id="nationwide-section"')
  assert 'nationwide-map.js' in text and 'map-region' in text
 files=list(ROOT.rglob('*.html'));assert len(files)==30;assert len(list((ROOT/'regions').glob('*.html')))==1
 forbidden=['data/catalogue.json','data/review-held.json','data/quality-status.json','data/segeummatjib-2025-top10.csv','data/segeummatjib-2025-regions.csv','tools/input','ga-events.js','maechul/og-map.png','maechul/og-survivors.png']
 for p in forbidden:assert not (ROOT/p).exists(),p
 parsed={p:Page(p.read_text()) for p in files}
 for p,d in parsed.items():
  assert len(d.headings)==1,(p,'h1');assert len(d.ids)==len(set(d.ids)),(p,'duplicate id')
  assert any(m.get('name')=='google-adsense-account' and m.get('content')=='ca-pub-3133301641364865' for m in d.meta)
  assert not d.scripts or d.scripts in (['/assets/explorer.js?v=20261023'],['/assets/departments.js'],['/assets/places.js'],['/assets/vendor/leaflet/leaflet.js','/assets/nationwide-map.js?v=20261023b']),(p,'unexpected external scripts')
  assert not any(m.get('name')=='robots' and 'noindex' in m.get('content','') for m in d.meta) or p.name=='404.html'
  for u in d.links+d.scripts:
   sp=urlsplit(u)
   if sp.scheme or sp.netloc:continue
   dest=ROOT/unquote(sp.path.lstrip('/')) if sp.path.startswith('/') else p.parent/unquote(sp.path) if sp.path else p
   if dest.is_dir():dest=dest/'index.html'
   assert dest.exists(),(p,u,'missing target')
   if sp.fragment and dest in parsed:assert unquote(sp.fragment) in parsed[dest].ids,(p,u,'missing fragment')
  assert not re.search('751,616|서울시청공무원.{0,5}맛집|adsbygoogle|gtag\\(',p.read_text()),p
 assert 'Disallow:' not in (ROOT/'robots.txt').read_text()
 assert (ROOT/'ads.txt').read_text().strip()=='google.com, pub-3133301641364865, DIRECT, f08c47fec0942fa0'
 assert '  - tools' in (ROOT/'_config.yml').read_text()
 urls=[x.text for x in ET.parse(ROOT/'sitemap.xml').findall('.//{*}loc')];assert len(urls)==len(set(urls))==29
 result={'status':'PASS','html_pages':30,'indexable_pages':29,'retired_region_files_absent':228,'nationwide_regions':229,'nationwide_entries':2189,'nationwide_coordinates':2172,'seoul_rows':2699,'seoul_groups':13,'jeju_dongs':43,'jeju_inputs':24,'checks':['source row identity and duplicate regression','Seoul CSV equality and derived aggregates','Jeju cohort/month/dong reconciliation','all internal resources and anchor targets','publication boundary and retired bulk endpoints absent','metadata sitemap robots ads ownership'],'file_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':run()
