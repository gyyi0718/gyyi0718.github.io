"""Read-only raw join and limited online source verification; no raw purposes exported."""
import csv,json,re,hashlib,subprocess,sys,datetime
from pathlib import Path
from audit_broad_sources import Rows
ROOT=Path(__file__).resolve().parents[1]
def run(raw):
 records=list(csv.DictReader((ROOT/'data/seoul-directory-records.csv').open(encoding='utf-8-sig')))
 selected={(r['source_id'],int(r['parsed_row'])):r for r in records if r['date'].startswith('2025-') and r['purpose_category']=='meal'}
 joined={}; originals={}
 for f in sorted(Path(raw).glob('20??-??.jsonl')):
  for line in f.open():
   obj=json.loads(line)
   for r in obj['rows']:
    key=(obj['doc']['id'],r['row_no'])
    if key not in selected:continue
    assert key not in joined
    pub=selected[key];assert pub['date']==r['d'] and int(pub['amount'])==r['amount']
    stamp=r.get('dt') or '';dt=datetime.datetime.strptime(stamp,'%Y-%m-%d %H:%M');assert dt.date().isoformat()==pub['date']
    joined[key]={**{k:pub[k] for k in ('place_id','name','district','address','source_id','source_url','parsed_row','date','organization','amount')},'recorded_time':dt.strftime('%H:%M'),'hour':dt.hour};originals[key]=r
 assert joined.keys()==selected.keys()
 rows=sorted(joined.values(),key=lambda r:(r['date'],r['source_id'],int(r['parsed_row'])))
 with (ROOT/'data/editorial-times.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 # Predetermined strata include every institution with a meal row, unusual hours,
 # morning/noon/evening ranges, and noncentral candidate cases. No random accuracy claim.
 targets={}
 for org in sorted({r['organization'] for r in rows}):
  rs=[r for r in rows if r['organization']==org];targets[('기관 '+org)]=rs[0]
 for h in (10,11,12,15,19,22):
  rs=[r for r in rows if r['hour']==h]
  if rs:targets['시각 '+str(h)]=rs[0]
 for name in ('서민갈비살','지호한방삼계탕','화평동왕냉면','한촌설렁탕'):
  targets[name]=next(r for r in rows if r['name']==name)
 audit=[];cache={}
 for label,r in targets.items():
  original=originals[(r['source_id'],int(r['parsed_row']))];url=r['source_url']
  if url not in cache:cache[url]=subprocess.run(['curl','-fLsS','--max-time','25',url],check=True,capture_output=True).stdout
  body=cache[url];compact=lambda s:re.sub(r'\s','',s or '')
  match=[x for x in Rows(body.decode()).rows if len(x)>=6 and r['date'] in x[2] and r['recorded_time'] in x[2] and compact(original['place']) in compact(x[3]) and compact(original['addr']) in compact(x[3]) and compact(original['purpose'])==compact(x[4]) and compact(original['dept'])==compact(x[1]) and re.sub(r'\D','',x[5])==str(r['amount'])]
  audit.append(dict(stratum=label,**r,status='matched' if match else 'needs_review',html_sha256=hashlib.sha256(body).hexdigest()))
  print(label,audit[-1]['status'],flush=True)
 receipt=dict(checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Purposive source checks of date/time, raw merchant/address, department, purpose and amount; no attendee text retained',samples=audit,raw_join_rows=len(rows),limitation='Not all rows checked online; time denotes the published execution timestamp, not opening hours or a confirmed visit.')
 (ROOT/'data/editorial-source-audit.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
 assert all(x['status']=='matched' for x in audit)
if __name__=='__main__':run(sys.argv[1])
