import unittest,json,csv,sqlite3,hashlib,sys,subprocess
from pathlib import Path
from broad_seoul import address,extract,purpose_class
ROOT=Path(__file__).resolve().parents[1]
class BroadTests(unittest.TestCase):
 def test_purpose_semantics(self):
  from purpose_types import purpose_category
  examples={'공정경제과 직원 격려 오찬 비용 지급':'meal','출입기자단 소통간담회 간식 구매':'refreshment','식사 및 음료 구매':'mixed','오찬 후 커피 구매':'mixed','과일간식 공급업체 선정 관련 간담회':'uncertain','학교급식 지원사업 관련 간담회':'uncertain','사회복무요원 중식비 지원 관련 논의':'uncertain','어린이집 석식도우미 지원사업 관련 협의':'uncertain','간담회 참석자 식사 제공':'meal','직원 오찬 비용':'meal','유관기관 간담회':'uncertain'}
  for purpose,expected in examples.items():self.assertEqual(purpose_category(purpose)[0],expected,purpose)
 def test_boundaries(self):
  from place_boundaries import nonfood_purchase,location_boundary
  for text in ['부서 직원용 상비약 구매','내방객 접대를 위한 서울시 쇼핑백 구매','간담회 준비 문구 구매','다과 및 소모품 구매']:
   self.assertIsNotNone(nonfood_purchase(text),text)
  for text in ['의약품 구매 정책 관련 간담회','직원 간식 구매','식사 비용 지급']:
   self.assertIsNone(nonfood_purchase(text),text)
  for name,addr in [('NICE결제대행','온라인결제, 서울 마포구 마포대로 217'),('쿠팡이츠','서울 구로구 디지털로26길 72'),('가게','결제처 본사: 서울 강남구 테헤란로 1')]:
   self.assertIsNotNone(location_boundary(name,addr))
  self.assertIsNone(location_boundary('향림','서울 노원구 한글비석로 127'))
  data=json.loads((ROOT/'data/seoul-directory.json').read_text());ids={p['id'] for p in data['places']}
  self.assertTrue(ids.isdisjoint({'ce016c02bdd9','c0c1eb12c1af','d3e77c0bc17a'}));self.assertNotIn('구로구',{p['district'] for p in data['places']})
  self.assertTrue(all(p['location_evidence']=='named_address_no_intermediary_context' for p in data['places']))
 def test_platform_alias_and_purchase_object(self):
  from place_boundaries import platform_key,location_boundary,nonfood_purchase,PLATFORM_ALIASES
  from purpose_types import purpose_category
  for canonical,aliases in PLATFORM_ALIASES.items():
   for alias in aliases:
    for name in [alias,'주식회사 '+alias,'(주) '+alias,'㈜'+alias,alias.lower()]:
     self.assertEqual(platform_key(name),canonical,name)
     self.assertEqual(location_boundary(name,'서울 영등포구 영신로34길 30'),'platform_or_payment_counterparty')
  for name in ['SSG.COM','SSG COM','(주)에스에스지닷컴','주식회사 쓱닷컴']:self.assertEqual(platform_key(name),'SSGCOM')
  for purpose in ['공공도서관협의회 워크숍 참석 직원 격려 다과 구입','해외기관 서울야외도서관 견학 간담회 다과 구입','도서 관련 회의 다과 구입']:
   self.assertIsNone(nonfood_purchase(purpose));self.assertEqual(purpose_category(purpose)[0],'refreshment')
  for purpose in ['업무용 도서 구입','도서 및 다과 구입','도서관 도서 구입']:
   self.assertEqual(nonfood_purchase(purpose),'nonfood_flowers_books_gifts')
  ids={p['id'] for p in json.loads((ROOT/'data/seoul-directory.json').read_text())['places']}
  self.assertTrue(ids.isdisjoint({'35bcae10e8f9','1d8c286239bb'}))
 def test_address_regressions(self):
  self.assertEqual(address('서울 중구 서소문로 11길 14 1층'),('중구','서소문로11길 14'))
  self.assertEqual(address('서울 중구 서소문로11길14'),('중구','서소문로11길 14'))
  for value in ('서울 중구 서소문로 11길','서울 중구 서소문로11길','중구 서소문로11길 14','서울 강남구 (관내)','서울 중구 태평로 2가'):
   self.assertIsNone(address(value),value)
 def test_independent_sql_and_privacy(self):
  data=json.loads((ROOT/'data/seoul-directory.json').read_text())
  with (ROOT/'data/seoul-directory-records.csv').open() as f:rows=list(csv.DictReader(f))
  self.assertEqual(len(rows),27175);self.assertEqual(data['raw_rows'],len(rows)+sum(data['exclusions'].values()))
  db=sqlite3.connect(':memory:');db.execute('create table r(id,name,district,address,source,url,rownum,date,org,dept,amount integer,category,reason)')
  db.executemany('insert into r values(?,?,?,?,?,?,?,?,?,?,?,?,?)',[tuple(r.values()) for r in rows])
  self.assertEqual(db.execute('select count(*) from (select source,rownum from r group by source,rownum)').fetchone()[0],len(rows))
  self.assertEqual(db.execute('select count(distinct district) from r').fetchone()[0],23)
  expected={r[0]:r[1:] for r in db.execute('select id,count(*),count(distinct source),count(distinct substr(date,1,7)),min(date),max(date) from r group by id')}
  self.assertEqual(len(expected),1005)
  manifest=json.loads((ROOT/'data/publication-manifest.json').read_text())
  self.assertEqual((manifest['seoul_directory_groups'],manifest['seoul_directory_rows'],manifest['seoul_directory_districts']),(1005,27175,23))
  self.assertEqual({p.stem for p in (ROOT/'data/seoul-directory').glob('*.json')},set(expected))
  for p in data['places']:
   self.assertEqual(expected[p['id']],(p['records'],p['documents'],p['months'],p['first'],p['last']))
   self.assertGreaterEqual(p['documents'],5);self.assertGreaterEqual(p['months'],3)
   scopes=dict(db.execute('select substr(date,1,4)||"/"||org||"/"||category,count(*) from r where id=? group by 1',(p['id'],)))
   self.assertEqual(scopes,p['scopes'])
   records=json.loads((ROOT/f'data/seoul-directory/{p["id"]}.json').read_text())
   self.assertEqual(len(records),p['records'])
   for r in records:
    self.assertEqual(set(r),{'source_id','source_url','parsed_row','date','organization','department','amount','purpose_category','purpose_reason'})
    self.assertEqual(r['source_url'],'https://opengov.seoul.go.kr/expense/'+r['source_id'].split(':')[1])
  self.assertEqual(dict(db.execute('select category,count(*) from r group by category')),data['purpose_counts'])
  actual=dict(db.execute('select category,sum(amount) from r group by category'))
  self.assertEqual({k:actual.get(k,0) for k in data['purpose_amounts']},data['purpose_amounts'])
  db.close()
 def test_map_quarantine(self):
  backup=ROOT/'tools/archive/nationwide-locations-before-precision-audit.json'
  old=json.loads(backup.read_text() if backup.exists() else subprocess.check_output(['git','show','e98bacb37ceb143de0d2c1f6182403aeccf53ff7:data/nationwide-locations.json'],cwd=ROOT));new=json.loads((ROOT/'data/nationwide-locations.json').read_text())
  olditems={i['id']:i for r in old['regions'] for i in r['items']};newitems={i['id']:i for r in new['regions'] for i in r['items']}
  self.assertEqual(set(olditems)-set(newitems),{'anseong-4','boseong-10','yecheon-4'})
  changed=[k for k in newitems if newitems[k]!=olditems[k]];self.assertEqual(len(changed),9)
  for k in changed:self.assertIsNone(newitems[k]['coordinates']);self.assertEqual(newitems[k]['name'],olditems[k]['name'])
if __name__=='__main__':
 if len(sys.argv)>1:
  data,records=extract(sys.argv.pop());boundary=data.pop('boundary_rows');assert boundary==json.loads((ROOT/'data/seoul-place-boundary-audit.json').read_text())['rows'];decisions=data.pop('purpose_decisions');assert decisions==json.loads((ROOT/'tools/seoul-purpose-decisions.json').read_text());assert data==json.loads((ROOT/'data/seoul-directory.json').read_text())
  for pid,rs in records.items():assert rs==json.loads((ROOT/f'data/seoul-directory/{pid}.json').read_text())
  print('Raw reconstruction and every published record: PASS')
 unittest.main()
