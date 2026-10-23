"""Purpose-stratified source checks, independent of the address normalizer.
No attendee fields or raw purpose free text are published.
"""
import json,re,subprocess,hashlib,collections
from pathlib import Path
from audit_broad_sources import Rows
from purpose_types import purpose_class,purpose_category
from place_boundaries import nonfood_purchase,location_boundary
from broad_seoul import address
ROOT=Path(__file__).resolve().parents[1]
def compact(s):return re.sub(r'\s','',s)
def run(raw):
 public={(r['source_id'],r['parsed_row']) for p in json.loads((ROOT/'data/seoul-directory.json').read_text())['places'] for r in json.loads((ROOT/f'data/seoul-directory/{p["id"]}.json').read_text())}
 pool=[]
 for path in sorted(Path(raw).glob('20??-??.jsonl')):
  for line in path.open():
   obj=json.loads(line)
   for r in obj['rows']:
    purpose=r.get('purpose') or '';key=(obj['doc']['id'],r['row_no'])
    pool.append((obj['doc'],r,purpose_class(purpose),key in public))
 samples={}
 for doc,r,reason,included in pool:
  boundary=nonfood_purchase(r.get('purpose') or '') or location_boundary(r.get('place') or '',r.get('addr') or '')
  if boundary:samples.setdefault(('place_boundary',boundary),(doc,r,reason,included))
  if (doc['id'],r['row_no']) in {('opengov:35398221',15),('opengov:36272394',2),('opengov:34067534',9)}:samples[('reported_boundary',doc['id'],r['row_no'])]=(doc,r,reason,included)
  if included:
   samples.setdefault(('published_purpose',purpose_category(r.get('purpose') or '')[0]),(doc,r,reason,included))
   samples.setdefault(('published_org_year',doc['org_id'],r['d'][:4]),(doc,r,reason,included))
   district=next((d for d in ('성동구','성북구','강북구') if d in (r.get('addr') or '')),None)
   if district:samples.setdefault(('published_district',district),(doc,r,reason,included))
  if reason in ('refreshment_purchase','mixed_meal_refreshment'):
   token=next((x for x in ('간식','음료','커피','다과') if x in (r.get('purpose') or '')),None)
   if token:samples.setdefault(('held_purchase',token),(doc,r,reason,included))
  if reason=='policy_topic_uncertain':samples.setdefault(('held_policy_topic',),(doc,r,reason,included))
  if reason=='meeting_only_uncertain':samples.setdefault(('held_meeting',doc['org_id']),(doc,r,reason,included))
  if '과일간식' in (r.get('purpose') or '') and '공급업체' in (r.get('purpose') or ''):samples.setdefault(('snack_as_meeting_topic',),(doc,r,reason,included))
  if (r.get('place') or '').replace(' ','') in ('적당','라운드앤드'):samples.setdefault(('held_cafe_report',r['place']),(doc,r,reason,included))
  if (doc['id'],r['row_no'])==('opengov:36707683',22):samples[('reported_snack',)]=(doc,r,reason,included)
 for org in ('seoul_city','seoul_council','seoul_office','seoul_fire'):
  for year in ('2025','2026'):
   cell=[x for x in pool if x[3] and x[0]['org_id']==org and x[1]['d'].startswith(year)]
   if cell:samples[('seeded_sample',org,year)]=min(cell,key=lambda x:hashlib.sha256(('purpose-review-20261023/'+x[0]['id']+'/'+str(x[1]['row_no'])).encode()).hexdigest())
 cache={};out=[]
 for strata,(doc,r,reason,included) in samples.items():
  item={'stratum':list(strata),'source_url':doc['url'],'parsed_row':r['row_no'],'date':r.get('d'),'organization':doc['org_id'],'name':r.get('place'),'address_summary':address(r.get('addr') or ''),'amount':r.get('amount'),'place_boundary':nonfood_purchase(r.get('purpose') or '') or location_boundary(r.get('place') or '',r.get('addr') or ''),'purpose_class':reason,'purpose_category':purpose_category(r.get('purpose') or '')[0],'address_check':bool(r.get('addr')),'published':included,'purpose_terms':re.findall(r'식사|오찬|만찬|중식|석식|조식|급식|회식|간담|간식|음료|커피|다과|구매|구입',r.get('purpose') or '')}
  try:
   if doc['url'] not in cache:cache[doc['url']]=subprocess.run(['curl','-fLsS','--max-time','20',doc['url']],capture_output=True,check=True).stdout
   body=cache[doc['url']];rows=Rows(body.decode()).rows
   matches=[row for row in rows if len(row)>=6 and str(r.get('d')) in row[2] and re.sub(r'[^\d]','',row[5])==str(r.get('amount')) and compact(r.get('dept') or '')==compact(row[1]) and compact(r.get('addr') or '') in compact(row[3]) and compact(r.get('place') or '') in compact(row[3]) and compact(r.get('purpose') or '')==compact(row[4])]
   item.update(status='matched' if matches else 'needs_review',html_sha256=hashlib.sha256(body).hexdigest(),matched_rows=len(matches))
  except Exception as e:item.update(status='unavailable',error=type(e).__name__)
  out.append(item);print(json.dumps(item,ensure_ascii=False),flush=True)
 receipt={'date':'2026-10-23','scope':'Published purpose categories, institution/year cells, noncentral districts, snack/beverage/coffee/refreshment and meeting-only purposes, reported snack, cafe-reported names, snack-policy topic and deterministic hash-seeded sample per institution/year. Direct raw address substring and exact purpose/dept text compared with official HTML; no shared address parser.','samples':out,'limitations':'Purposive sample, not statistical accuracy estimate. Explicit meal words do not certify business category or current operation. Free-text purposes and attendee fields omitted from published receipt.'}
 (ROOT/'data/seoul-directory-semantic-audit.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 import sys
 run(sys.argv[1])
