"""Read-only targeted official checks for the final two review findings."""
import json,re,sys,subprocess,hashlib,collections,datetime
from pathlib import Path
from audit_broad_sources import Rows
from broad_seoul import address,BAD,EXTRA,HOLD
from purpose_types import purpose_category
from place_boundaries import nonfood_purchase,location_boundary
ROOT=Path(__file__).resolve().parents[1]
def compact(x):return re.sub(r'\s','',x or '')
def name(x):return re.sub(r'^(?:주식회사|㈜|\(주\)|주\))','',compact(x)).strip(' ()').upper()
def run(raw):
 targets={('opengov:35679981',1),('opengov:35787107',18),('opengov:36240386',10)};samples=[];groups=collections.defaultdict(list)
 data=json.loads((ROOT/'data/seoul-directory.json').read_text());public={(r['source_id'],r['parsed_row']) for p in data['places'] for r in json.loads((ROOT/f'data/seoul-directory/{p["id"]}.json').read_text())}
 for file in sorted(Path(raw).glob('20??-??.jsonl')):
  for line in file.open():
   o=json.loads(line);doc=o['doc']
   for r in o['rows']:
    key=(doc['id'],r['row_no'])
    if key in targets:samples.append((doc,r))
    n=name(r.get('place'));a=address(r.get('addr') or '');category,reason=purpose_category(r.get('purpose') or '')
    if n not in ('오설록김포공항점','교동한과') or not a:continue
    if not '2025-01-01'<=(r.get('d') or '')<='2026-08-31':continue
    if reason=='non_meal_purchase' or reason.startswith('nonfood_') or location_boundary(r.get('place') or '',r.get('addr') or '') or BAD.search(n) or EXTRA.search(n) or n in HOLD:continue
    amount=r.get('amount')
    if not isinstance(amount,(int,float)) or isinstance(amount,bool) or not 0<amount<=3000000 or amount!=int(amount):continue
    groups[(n,*a)].append((doc['id'],r['d'][:7]))
 results=[]
 for doc,r in samples:
  body=subprocess.run(['curl','-fLsS','--max-time','25',doc['url']],capture_output=True,check=True).stdout
  matched=[row for row in Rows(body.decode()).rows if len(row)>=6 and r['d'] in row[2] and compact(r.get('dept'))==compact(row[1]) and compact(r.get('place')) in compact(row[3]) and compact(r.get('addr')) in compact(row[3]) and compact(r['purpose'])==compact(row[4]) and re.sub(r'[^\d]','',row[5])==str(r['amount'])]
  a=address(r.get('addr') or '');rs=groups.get((name(r.get('place')),*a),[]) if a else [];category,reason=purpose_category(r['purpose'])
  results.append({'source_url':doc['url'],'parsed_row':r['row_no'],'name':name(r.get('place')),'date':r['d'],'amount':r['amount'],'purpose_category':category,'nonfood_reason':nonfood_purchase(r['purpose']),'location_reason':location_boundary(r.get('place') or '',r.get('addr') or ''),'published':(doc['id'],r['row_no']) in public,'eligible_group_documents':len({x[0] for x in rs}),'eligible_group_months':len({x[1] for x in rs}),'status':'matched' if matched else 'needs_review','html_sha256':hashlib.sha256(body).hexdigest()})
 print(json.dumps({'samples':results,'platform_reference':'https://company.ssg.com/','limitation':'Three targeted online rows; whole current dataset reconstructed separately; no current-business certification.'},ensure_ascii=False,indent=2))
if __name__=='__main__':run(sys.argv[1])
