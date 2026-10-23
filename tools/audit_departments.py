"""Audit saved inputs without changing them; write a privacy-limited JSON receipt to stdout."""
from pathlib import Path
from collections import Counter,defaultdict
import json,hashlib,sys,datetime
ROOT=Path(__file__).resolve().parents[1]

def audit(raw_dir):
    source=ROOT/'data/seoul-2025-evidence.json';e=json.loads(source.read_text());rows=e['rows']
    desired={(r['source_id'],r['parsed_row']):r for r in rows};assert len(desired)==len(rows)
    manifest=json.loads((ROOT/'data/source-input-manifest.json').read_text());inputs=[];matched=set();raw_count=0;docs=set()
    for entry in manifest:
        path=Path(raw_dir)/entry['file'];digest=hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest==entry['sha256'],f'Input changed: {path.name}'
        inputs.append({'file':path.name,'sha256':digest,'bytes':path.stat().st_size})
        for line in path.open():
            obj=json.loads(line)
            if obj['doc']['org_id']!='seoul_city':continue
            docs.add(obj['doc']['id'])
            for r in obj['rows']:
                raw_count+=1;key=(obj['doc']['id'],r['row_no'])
                if key not in desired:continue
                assert key not in matched;matched.add(key);s=desired[key]
                for a,b in [('date','d'),('department','dept'),('amount','amount'),('source_merchant','place')]:assert s[a]==r.get(b),(key,a)
                assert obj['doc']['url']==s['source_url']
    assert len(matched)==2699 and len(docs)==2157 and raw_count==47231
    signatures=defaultdict(list)
    for r in rows:
        assert datetime.date.fromisoformat(r['date']).year==2025
        assert r['department'].strip() and r['road_address'] and r['amount']>0
        signatures[tuple(r[k] for k in ['date','department','source_merchant','road_address','amount'])].append(r)
    collisions=[v for v in signatures.values() if len(v)>1];assert len(collisions)==1
    checks=[{'source_id':'opengov:32773754','official_row':3,'date_time':'2025-01-17 12:55','merchant':'참숯골','department':'기획조정실 공기업담당관','amount':138000},
      {'source_id':'opengov:33017153','official_row':4,'date_time':'2025-02-04 12:14','merchant':'브라주카 그릴','department':'재난안전실 재난안전정책과','amount':95600},
      {'source_id':'opengov:34483996','official_row':72,'date_time':'2025-09-09 13:02','merchant':'브이아이피참치','department':'행정국 총무과','amount':140000},
      {'source_id':'opengov:34483996','official_row':74,'date_time':'2025-09-09 13:08','merchant':'브이아이피참치','department':'행정국 총무과','amount':140000},
      {'source_id':'opengov:34711308','official_row':19,'date_time':'2025-10-24 19:06','merchant':'복성각','department':'시민감사옴부즈만위원회','amount':1110000}]
    for x in checks:x['source_url']='https://opengov.seoul.go.kr/expense/'+x['source_id'].split(':')[1]
    return {'checked_on':'2026-10-23','scope':e['scope'],'input_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'raw_files':inputs,'raw_seoul_documents':len(docs),'raw_seoul_rows':raw_count,'matched_selected_rows':len(matched),'unique_document_row_keys':len(desired),'field_mismatches':0,'selected_first_date':min(r['date'] for r in rows),'selected_last_date':max(r['date'] for r in rows),'existing_selection_exclusions':e['filter_exclusions'],'same_date_department_place_address_amount_candidate_pairs':len(collisions),'candidate_decision':'Both rows retained: official source has separate serials and different times; does not prove two separate meals.','official_source_samples':checks,'official_check_method':'Manually inspected official public HTML tables on checked_on; not rerun by this offline audit script.','privacy':'No attendee names, recipient fields, or free-text purpose exported.','limitations':['Fixed selected sample, not all Seoul restaurants','Saved department labels are not unique organizational IDs','Current official source checked for samples only','Business identity and current operation unverified']}
if __name__=='__main__':print(json.dumps(audit(sys.argv[1]),ensure_ascii=False,indent=2))
