"""Independent SQLite aggregate checks; optional raw timestamp/identity reconciliation."""
import unittest,sqlite3,csv,json,sys,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data'
RAW=Path(sys.argv.pop()) if len(sys.argv)>1 and not sys.argv[-1].startswith('-') else None
class EditorialTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.m=json.loads((DATA/'editorial-2025.json').read_text());cls.db=sqlite3.connect(':memory:')
  for table,file in [('r','seoul-directory-records.csv'),('t','editorial-times.csv')]:
   with (DATA/file).open(encoding='utf-8-sig') as f:
    reader=csv.DictReader(f);keys=reader.fieldnames;rows=list(reader)
   cls.db.execute('create table '+table+' ('+','.join(keys)+')');cls.db.executemany('insert into '+table+' values ('+','.join('?' for _ in keys)+')',[[r[k] for k in keys] for r in rows])
  cls.db.execute("create view y as select * from r where date between '2025-01-01' and '2025-12-31'")
 @classmethod
 def tearDownClass(cls):cls.db.close()
 def q(self,s,args=()):return self.db.execute(s,args).fetchall()
 def test_geography(self):
  self.assertEqual(self.q('select count(*),count(distinct place_id) from y')[0],(17117,969))
  for r in self.m['organizations']:
   o=r['organization'];actual=self.q('select count(*),count(distinct place_id),count(distinct source_id),count(distinct district),count(distinct substr(date,1,7)) from y where organization=?',(o,))[0]
   self.assertEqual(actual,(r['rows'],r['places'],r['documents'],r['districts'],12))
   self.assertAlmostEqual(self.q("select avg(case when district in ('중구','종로구') then 1.0 else 0 end) from y where organization=?",(o,))[0][0],r['central_share'])
   strict=self.q("select count(*),count(distinct place_id),avg(case when district in ('중구','종로구') then 1.0 else 0 end) from y where organization=? and place_id in (select place_id from y group by place_id having count(distinct source_id)>=5 and count(distinct substr(date,1,7))>=3)",(o,))[0]
   self.assertEqual(strict[:2],(r['strict_2025_rows'],r['strict_2025_places']));self.assertAlmostEqual(strict[2],r['strict_2025_central_share'])
   months=[x['central_share'] for x in self.m['monthly'] if x['organization']==o];self.assertAlmostEqual(sum(months)/12,r['equal_month_share'])
  for r in self.m['monthly']:
   actual=self.q("select count(*),sum(district in ('중구','종로구')) from y where organization=? and substr(date,1,7)=?",(r['organization'],r['month']))[0];self.assertEqual(actual,(r['rows'],r['central_rows']))
  for r in self.m['districts']:
   self.assertEqual(self.q('select count(*),count(distinct place_id) from y where organization=? and district=?',(r['organization'],r['district']))[0],(r['rows'],r['places']))
  extra={r['place_id'] for r in self.m['office_extra']};actual={x[0] for x in self.q("select distinct place_id from y where organization='seoul_office' except select distinct place_id from y where organization='seoul_city'")}
  self.assertEqual(extra,actual);self.assertEqual(len(extra),84)
  for r in self.m['office_extra']:
   self.assertEqual(self.q("select count(*),count(distinct source_id),sum(purpose_category='meal') from y where organization='seoul_office' and place_id=?",(r['place_id'],))[0],(r['rows'],r['documents'],r['meal_rows']))
  for r in self.m['overlap']:
   a={x[0] for x in self.q('select distinct place_id from y where organization=?',(r['a'],))};b={x[0] for x in self.q('select distinct place_id from y where organization=?',(r['b'],))}
   self.assertEqual((len(a&b),len(a|b),len(a-b),len(b-a)),(r['intersection'],r['union'],r['only_a'],r['only_b']))
 def test_times(self):
  self.assertEqual(self.q('select count(*) from t')[0][0],468)
  self.assertEqual(self.q("select count(*) from t join y using(source_id,parsed_row) where y.purpose_category='meal' and t.date=y.date and t.amount=y.amount and t.place_id=y.place_id")[0][0],468)
  self.assertEqual(self.q('select count(*) from (select source_id,parsed_row from t group by source_id,parsed_row)')[0][0],468)
  for r in self.m['hours']:self.assertEqual(self.q('select count(*) from t where cast(hour as integer)=?',(r['hour'],))[0][0],r['rows'])
  ids={x[0] for x in self.q('select place_id from t group by place_id having count(distinct source_id)>=3')};self.assertEqual(ids,{r['place_id'] for r in self.m['time_places']});self.assertEqual(len(ids),44)
  for r in self.m['time_places']:
   actual=self.q('select count(*),count(distinct source_id),sum(cast(hour as integer) between 11 and 14),sum(cast(hour as integer) between 17 and 21) from t where place_id=?',(r['place_id'],))[0]
   self.assertEqual(actual,(r['rows'],r['documents'],r['midday'],r['evening']));self.assertEqual(r['rows'],r['midday']+r['evening']+r['other'])
 def test_rendered_time_details(self):
  from html.parser import HTMLParser
  class DetailRows(HTMLParser):
   def __init__(self):super().__init__();self.rows=[];self.ids=[];self.current=None;self.cell=None;self.links=[]
   def handle_starttag(self,tag,attrs):
    a=dict(attrs)
    if tag=='details' and a.get('id','').startswith('time-'):self.ids.append(a['id'])
    if tag=='tr' and 'data-time-source' in a:self.current={'key':(a['data-time-source'],a['data-time-row']),'place':a['data-time-place'],'cells':[],'url':None}
    if self.current is not None and tag=='td':self.cell=''
    if self.current is not None and tag=='a':self.current['url']=a.get('href')
    if tag=='a' and a.get('href','').startswith('#time-'):self.links.append(a['href'][1:])
   def handle_data(self,text):
    if self.cell is not None:self.cell+=text
   def handle_endtag(self,tag):
    if tag=='td' and self.cell is not None:self.current['cells'].append(self.cell);self.cell=None
    if tag=='tr' and self.current is not None:self.rows.append(self.current);self.current=None
  parsed=DetailRows();parsed.feed((ROOT/'analysis/recorded-times.html').read_text())
  ids={r['place_id'] for r in self.m['time_places']};self.assertEqual(set(parsed.ids),{'time-'+i for i in ids});self.assertEqual(set(parsed.links),set(parsed.ids));self.assertEqual(len(parsed.ids),44)
  expected={}
  for row in self.q('select source_id,parsed_row,place_id,date,recorded_time,hour,organization,amount,source_url from t'):
   source,num,pid,date,time,hour,org,amount,url=row
   if pid not in ids:continue
   band='11~14시' if 11<=int(hour)<15 else '17~21시' if 17<=int(hour)<22 else '그 밖'
   expected[source,num]=(pid,[date,time,band,{'seoul_city':'서울시 본청','seoul_council':'서울시의회','seoul_office':'사업소','seoul_fire':'소방'}[org],f'{int(amount):,}원','공식 문서 · 파싱 행 '+num],url)
  self.assertEqual(len(parsed.rows),len(expected));self.assertEqual({r['key']:(r['place'],r['cells'],r['url']) for r in parsed.rows},expected)
  seomin=[r for r in parsed.rows if r['place']=='3ce71df6c523'];self.assertEqual(len(seomin),7);self.assertEqual(sum(r['cells'][2]=='17~21시' for r in seomin),6)
 def test_exports_and_sources(self):
  for key in ('organizations','districts','monthly','overlap','time_places','hours','office_extra'):
   with (DATA/f'editorial-{key}.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
   self.assertEqual(rows,[{k:str(v) for k,v in r.items()} for r in self.m[key]])
  self.assertEqual((DATA/'editorial-calculations.py').read_bytes(),(ROOT/'tools/editorial_metrics.py').read_bytes())
  audit=json.loads((DATA/'editorial-source-audit.json').read_text());self.assertEqual(len(audit['samples']),14);self.assertTrue(all(r['status']=='matched' for r in audit['samples']))
  for f in DATA.glob('editorial-*'):
   text=f.read_text(encoding='utf-8-sig');self.assertNotIn('/Users/',text)
   self.assertFalse(re.search(r'"(?:people|purpose|attendees)"\s*:',text))
 def test_raw_time_join(self):
  if RAW is None:self.skipTest('raw directory not supplied')
  expected={(x[0],int(x[1])):x[2:] for x in self.q('select source_id,parsed_row,date,recorded_time,amount from t')};seen=set()
  for f in RAW.glob('20??-??.jsonl'):
   for line in f.read_text().splitlines():
    obj=json.loads(line)
    for r in obj['rows']:
     k=(obj['doc']['id'],r['row_no'])
     if k not in expected:continue
     self.assertNotIn(k,seen);seen.add(k);d,t,amount=expected[k];self.assertEqual(r['dt'],d+' '+t);self.assertEqual(r['d'],d);self.assertEqual(r['amount'],int(amount))
  self.assertEqual(seen,set(expected))
if __name__=='__main__':unittest.main()
