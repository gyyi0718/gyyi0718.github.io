"""Low-volume official HTML checks; does not write raw HTML or attendee fields."""
import json,subprocess,re,hashlib
from pathlib import Path
from html.parser import HTMLParser
from broad_seoul import address
ROOT=Path(__file__).resolve().parents[1]
class Rows(HTMLParser):
 def __init__(self,s):super().__init__();self.rows=[];self.row=[];self.cell=None;self.feed(s)
 def handle_starttag(self,t,a):
  if t=='tr':self.row=[]
  if t in ('td','th'):self.cell=''
 def handle_data(self,s):
  if self.cell is not None:self.cell+=s
 def handle_endtag(self,t):
  if t in ('td','th') and self.cell is not None:self.row.append(' '.join(self.cell.split()));self.cell=None
  if t=='tr' and self.row:self.rows.append(self.row)
def audit():
 data=json.loads((ROOT/'data/seoul-directory.json').read_text());allrows=[]
 for p in data['places']:
  for r in json.loads((ROOT/f'data/seoul-directory/{p["id"]}.json').read_text()):allrows.append(dict(place=p,**r))
 samples=[]
 for org in ('seoul_city','seoul_council','seoul_office','seoul_fire'):
  for year in ('2025','2026'):
   samples.append(('기관×연도 최대금액',max((r for r in allrows if r['organization']==org and r['date'].startswith(year)),key=lambda r:r['amount'])))
 for district in ('은평구','성동구','서대문구'):
  samples.append(('중심지역 밖 주소',min((r for r in allrows if r['place']['district']==district),key=lambda r:r['date'])))
 output=[]
 for stratum,r in samples:
  p=r['place'];item={k:r[k] for k in ('source_url','date','organization','parsed_row','amount')};item.update(stratum=stratum,name=p['name'],address=p['address'])
  try:
   result=subprocess.run(['curl','-fLsS','--max-time','25',r['source_url']],capture_output=True,check=True)
   parsed=Rows(result.stdout.decode());matches=[]
   for row in parsed.rows:
    if len(row)<6:continue
    if r['date'] not in row[2] or re.sub(r'[^\d]','',row[5])!=str(r['amount']):continue
    actual=address(row[3]);expected=address(p['address'])
    if actual!=expected:continue
    if re.sub(r'\s','',p['name']).upper() not in re.sub(r'\s','',row[3]).upper():continue
    if re.sub(r'\s','',row[1])!=re.sub(r'\s','',r['department']):continue
    matches.append(row)
   item['status']='matched' if matches else 'needs_review';item['matched_rows']=len(matches);item['html_sha256']=hashlib.sha256(result.stdout).hexdigest()
  except Exception as e:item['status']='unavailable';item['error']=type(e).__name__
  output.append(item);print(json.dumps(item,ensure_ascii=False),flush=True)
 receipt={'date':'2026-10-23','scope':'4 institutions x 2 years maximum-amount rows plus 3 districts outside Jung/Jongno; merchant,date,department,address,amount checked in official HTML','samples':output,'limitation':'Purposive stratified checks, not random accuracy estimate or validation of every row; merchant identity and current operation not certified.'}
 (ROOT/'data/seoul-directory-source-audit.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':audit()
