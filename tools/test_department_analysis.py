"""Independent SQLite aggregate checks plus identity/threshold regression cases."""
import csv,json,sqlite3,unittest,hashlib
from pathlib import Path
from department_analysis import calculate
ROOT=Path(__file__).resolve().parents[1]
class DistributionTest(unittest.TestCase):
 def test_published_aggregates(self):
  rows=json.loads((ROOT/'data/seoul-2025-evidence.json').read_text())['rows'];actual=json.loads((ROOT/'data/seoul-departments.json').read_text());self.assertEqual(actual,calculate(rows))
  db=sqlite3.connect(':memory:');db.execute('CREATE TABLE r(merchant,address,dept,day)');db.executemany('INSERT INTO r VALUES(?,?,?,?)',[(r['merchant'],r['road_address'],r['department'],r['date']) for r in rows])
  with (ROOT/'data/seoul-department-months.csv').open(encoding='utf-8-sig') as f:details=list(csv.DictReader(f))
  self.assertEqual(len(details),891);self.assertEqual(sum(int(x['records']) for x in details),2699)
  for p in actual['places']:
   expected=db.execute('SELECT dept,COUNT(*),COUNT(DISTINCT substr(day,1,7)) FROM r WHERE merchant=? AND address=? GROUP BY dept ORDER BY COUNT(*) DESC,dept',(p['merchant'],p['address'])).fetchall()
   self.assertEqual(p['records'],sum(x[1] for x in expected));self.assertEqual(p['department_labels'],len(expected))
   self.assertEqual(p['top5_records'],sum(x[1] for x in expected[:5]));self.assertEqual(p['repeat_thresholds']['6'],sum(x[2]>=6 for x in expected))
   for d in p['departments']:
    months=[db.execute('SELECT COUNT(*) FROM r WHERE merchant=? AND address=? AND dept=? AND substr(day,6,2)=?',(p['merchant'],p['address'],d['department'],f'{m:02}')).fetchone()[0] for m in range(1,13)]
    self.assertEqual(d['months'],months)
    out=next(x for x in details if (x['merchant'],x['address'],x['department'])==(p['merchant'],p['address'],d['department']))
    self.assertEqual(int(out['records']),sum(months));self.assertEqual([int(out[f'month_{m:02}']) for m in range(1,13)],months)
  byname={p['merchant']:p for p in actual['places']}
  self.assertEqual((byname['참숯골']['top5_records'],byname['브라주카 그릴']['top5_records']),(91,35))
  self.assertEqual((byname['참숯골']['repeat_thresholds']['6'],byname['브라주카 그릴']['repeat_thresholds']['6']),(7,2))
  audit=json.loads((ROOT/'data/seoul-department-audit.json').read_text());self.assertEqual(audit['input_sha256'],hashlib.sha256((ROOT/'data/seoul-2025-evidence.json').read_bytes()).hexdigest())
  for p in actual['places']:
   self.assertFalse({'purpose','people','recipient','attendee'} & set(p))
 def test_identity_and_month_boundaries(self):
  def row(i,month,dept='A'):return {'source_id':'test:1','parsed_row':i,'department':dept,'merchant':'X','road_address':'Y','date':f'2025-{month:02}-01'}
  rows=[row(1,1),row(2,1),row(3,2),row(4,3),row(5,4),row(6,5)]
  p=calculate(rows)['places'][0];self.assertEqual(p['repeat_thresholds']['6'],0);self.assertEqual(p['departments'][0]['active_months'],5)
  rows.append(row(7,6));self.assertEqual(calculate(rows)['places'][0]['repeat_thresholds']['6'],1)
  with self.assertRaises(ValueError):calculate(rows+[rows[0]])
  self.assertEqual(calculate([row(1,1),row(2,1)])['records'],2)
if __name__=='__main__':unittest.main()
