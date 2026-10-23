import unittest,json,csv,sqlite3,datetime,sys
from pathlib import Path
from place_records import extract
ROOT=Path(__file__).resolve().parents[1]
class PlaceTests(unittest.TestCase):
 def test_integrity_and_original_sample(self):
  d=json.loads((ROOT/'data/place-records.json').read_text());r=d['rows']
  self.assertEqual(len(r),4478);self.assertEqual(len({(x['source_id'],x['parsed_row']) for x in r}),4478)
  self.assertEqual(sum(d['exclusions'].values())+len(r),d['parsed_rows'])
  self.assertEqual(len(d['inputs']),20)
  self.assertEqual(len({x['place_id'] for x in r}),13)
  for pid in ('p06','p08'):self.assertEqual(sum(x['place_id']==pid and x['organization']=='seoul_city' for x in r),172)
  for pid in {x['place_id'] for x in r}:
   with (ROOT/f'data/place-{pid}.csv').open() as f:self.assertEqual(len(list(csv.DictReader(f))),sum(x['place_id']==pid for x in r))
  allowed={'source_id','parsed_row','source_url','date','organization','department','merchant','address','amount','place_id'}
  for x in r:
   self.assertEqual(set(x),allowed);datetime.date.fromisoformat(x['date']);self.assertGreater(x['amount'],0)
  old=json.loads((ROOT/'data/seoul-2025-evidence.json').read_text())['rows']
  original={(x['source_id'],x['parsed_row']):(x['date'],x['department'],x['merchant'],x['road_address'],x['amount'],x['source_url']) for x in old}
  current={(x['source_id'],x['parsed_row']):(x['date'],x['department'],x['merchant'],x['address'],x['amount'],x['source_url']) for x in r if x['organization']=='seoul_city' and x['date'].startswith('2025')}
  self.assertEqual(original,current)
  with (ROOT/'data/place-records.csv').open() as f:csvrows=list(csv.DictReader(f))
  self.assertEqual(csvrows,[{k:str(v) for k,v in x.items()} for x in r])
 def test_filter_markup(self):
  text=(ROOT/"places/index.html").read_text()
  self.assertIn('<option value="2025">2025년</option>',text)
  self.assertNotIn("</option value",text)
 def test_sql_reconciliation(self):
  r=json.loads((ROOT/'data/place-records.json').read_text())['rows'];db=sqlite3.connect(':memory:');db.execute('create table records(place,date,org,dept,amount)')
  db.executemany('insert into records values(?,?,?,?,?)',[(x['place_id'],x['date'],x['organization'],x['department'],x['amount']) for x in r])
  for pid,n,months,last in db.execute('select place,count(*),count(distinct substr(date,1,7)),max(date) from records group by place'):
   text=(ROOT/f'places/{pid}.html').read_text()
   self.assertIn(f'<td>{n}</td><td>{months}</td>',text);self.assertIn(last,text)
  self.assertEqual(dict(db.execute('select org,count(*) from records group by org')),{'seoul_city':3907,'seoul_council':330,'seoul_office':229,'seoul_fire':12})
if __name__=='__main__':
 if len(sys.argv)>1:
  raw=sys.argv.pop();assert extract(raw)==json.loads((ROOT/'data/place-records.json').read_text());print('Raw deterministic reconstruction: PASS')
 unittest.main()
