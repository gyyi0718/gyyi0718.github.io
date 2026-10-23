"""Fixed-address publication. Raw inputs remain read-only; no network required."""
import json,re,datetime,hashlib,csv,statistics
from collections import Counter,defaultdict
from pathlib import Path
from urllib.parse import quote
from rebuild_seoul import KNOWN,ROAD,MEAL,NONMEAL
ORG={'seoul_city':'서울시 본청','seoul_council':'서울시의회','seoul_office':'사업소','seoul_fire':'소방'}
ROOT=Path(__file__).resolve().parents[1]
def extract(raw):
 rows=[];seen=set();excluded=Counter();inputs=[];coverage=Counter()
 for path in sorted(Path(raw).glob('20??-??.jsonl')):
  inputs.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
  for line in path.open():
   obj=json.loads(line);doc=obj['doc'];org=doc['org_id']
   if org not in ORG:continue
   for r in obj['rows']:
    coverage[path.stem+' / '+org]+=1
    key=(doc['id'],r['row_no'])
    if key in seen:excluded['duplicate_document_row']+=1;continue
    seen.add(key)
    try:day=datetime.date.fromisoformat(r.get('d') or '')
    except ValueError:excluded['invalid_date']+=1;continue
    if not '2025-01-01'<=str(day)<='2026-08-31':excluded['outside_period']+=1;continue
    name=next((x for x in KNOWN if x in re.sub(r'\s+','',r.get('place') or '')),None)
    if not name:excluded['outside_names']+=1;continue
    merchant,allowed=KNOWN[name];m=ROAD.search(r.get('addr') or '');addr=' '.join(m.groups()) if m else ''
    if addr not in allowed:excluded['other_or_missing_address']+=1;continue
    purpose=r.get('purpose') or ''
    if not MEAL.search(purpose) or NONMEAL.search(purpose):excluded['purpose']+=1;continue
    amount=r.get('amount')
    if not isinstance(amount,(int,float)) or isinstance(amount,bool) or amount<=0 or not float(amount).is_integer():excluded['amount']+=1;continue
    assert doc['url']=='https://opengov.seoul.go.kr/expense/'+doc['id'].split(':')[1]
    rows.append(dict(source_id=doc['id'],parsed_row=r['row_no'],source_url=doc['url'],date=str(day),organization=org,department=r.get('dept') or '',merchant=merchant,address='서울 중구 '+addr,amount=int(amount)))
 rows.sort(key=lambda r:(r['date'],r['source_id'],r['parsed_row']))
 keys=sorted(set((r['merchant'],r['address']) for r in rows));ids={k:'p'+str(i+1).zfill(2) for i,k in enumerate(keys)}
 for r in rows:r['place_id']=ids[r['merchant'],r['address']]
 return {'scope':'기존 사전선정 9개 상호·13개 주소, 2025-01~2026-08 보관 문서의 식사 관련 행','inputs':inputs,'parsed_rows':sum(coverage.values()),'coverage':dict(coverage),'exclusions':dict(excluded),'rows':rows}
def render(page,hero,sec,table,H):
 data=json.loads((ROOT/'data/place-records.json').read_text());rows=data['rows'];groups=defaultdict(list)
 for r in rows:groups[r['place_id']].append(r)
 def summary(rs):return [len(rs),len({r['date'][:7] for r in rs}),len({(r['organization'],r['department']) for r in rs}),rs[0]['date'],rs[-1]['date']]
 scope='<p class="note">기존 목록에서 미리 고른 9개 상호·13개 주소의 식사 관련 기록입니다. 서울 전체 식당 순위가 아닙니다. 2025년 1월~2026년 8월 보관 문서 중 수록된 행이며, 마지막 관측일은 현재 영업 확인일이 아닙니다. 기관별 수집량이 달라 건수를 수요 증감으로 해석할 수 없습니다.</p>'
 cards=[];options=[]
 for pid,rs in sorted(groups.items()):
  r=rs[0];name=r['merchant'];addr=r['address'];n,months,depts,first,last=summary(rs);label=name+' · '+addr
  options.append(f'<option value="{pid}">{H(label)}</option>')
  cards.append([f'<a href="/places/{pid}.html">{H(name)}</a>',H(addr),n,months,last])
  org=Counter(x['organization'] for x in rs);monthly=Counter(x['date'][:7] for x in rs)
  body=hero(H(label),'기록에 나온 주소를 기준으로 지점을 구분했습니다. 과거 공공 지출 근거를 먼저 살펴보고, 방문 전 현재 영업정보는 외부 지도에서 확인하세요.','PLACE RECORD', '자료 분석·편집: 세금맛집 | 2026-10-23')+scope
  body+=sec('이 주소에서 확인되는 기록',table(['기록 행','관측 월','기관·부서명 조합','첫 관측','최근 관측'],[[n,months,depts,first,last]])+f'<p>이 주소는 보관 범위 20개월 중 {months}개월에 나타납니다. 아래 월별 표에서 반복된 달을 확인할 수 있습니다. 한 행은 한 공개 집행 내역이며 방문 횟수와 일치한다고 단정하지 않습니다.</p>')
  body+=sec('어느 기관의 자료에 나타날까',table(['기관 범주','행 수'],[[ORG[o],org[o]] for o in ORG])+ '<p>기관 범주는 문서의 수집 분류입니다. 부서명은 기관 범주와 함께 구분하며 조직 개편 전후를 임의로 합치지 않습니다.</p>')
  body+=sec('월별 관측 달력',table(['월','기록 행'],[[f'{y}-{m:02}',monthly[f'{y}-{m:02}']] for y in (2025,2026) for m in range(1,13 if y==2025 else 9)])+'<p>0은 보관 자료에서 조건에 맞는 행을 찾지 못했다는 뜻입니다. 2026년 8월 등 수집량이 적은 달이 있어 부재·폐업·수요 감소로 해석하지 않습니다.</p>')
  # One latest example per institution, plus earliest: deliberate source selection, not recommendation.
  examples={ (rs[0]['source_id'],rs[0]['parsed_row']):rs[0] }
  for o in ORG:
   candidates=[x for x in rs if x['organization']==o]
   if candidates:examples[candidates[-1]['source_id'],candidates[-1]['parsed_row']]=candidates[-1]
  body+=sec('직접 대조할 원문 사례', '<p>첫 관측 행과 기관 범주별 최근 행을 골랐습니다. 원문 행 번호는 보관 파서의 식별자이며 웹 표의 표시 순번과 다를 수 있습니다.</p>'+table(['날짜','기관 / 부서','집행액','원문'],[[x['date'],H(ORG[x['organization']]+' / '+x['department']),f"{x['amount']:,}원",f'<a href="{x["source_url"]}">공개 문서 · 보관 행 {x["parsed_row"]}</a>'] for x in examples.values()]))
  siblings=[(p,v) for p,v in groups.items() if v[0]['merchant']==name and p!=pid]
  if siblings:body+=sec('같은 상호, 다른 주소','<ul>'+''.join(f'<li><a href="/places/{p}.html">{H(v[0]["address"])}</a></li>' for p,v in siblings)+'</ul><p>상호가 같아도 주소가 다르면 별도 장소로 집계합니다. 동일 사업자나 지점 관계까지 확인한 것은 아닙니다.</p>')
  with (ROOT/f'data/place-{pid}.csv').open('w') as f:
   writer=csv.DictWriter(f,fieldnames=list(rs[0]),lineterminator='\n');writer.writeheader();writer.writerows(rs)
  body+=sec('최근 기록 20행',f'<p>날짜 역순으로 최대 20행을 보여 줍니다. <a href="/data/place-{pid}.csv">이 주소의 전체 {n}행 CSV</a>에서 원하는 기간과 부서를 직접 찾을 수 있습니다.</p>'+table(['날짜','기관 / 부서','집행액','원문'],[[x['date'],H(ORG[x['organization']]+' / '+x['department']),f"{x['amount']:,}원",f'<a href="{x["source_url"]}">문서 / 보관 행 {x["parsed_row"]}</a>'] for x in reversed(rs[-20:])]))
  body+=sec('다음 단계',f'<div class="actions"><a class="button" href="/places/?left={pid}#compare">다른 주소와 비교</a><a class="button secondary" href="https://map.naver.com/p/search/{quote(label)}">현재 지도 검색</a></div><p>외부 지도는 검색 결과입니다. 영업시간·메뉴·가격·현재 상호는 해당 서비스에서 별도로 확인하세요.</p><p><a href="/data/place-records.csv">전체 원문 연결 CSV</a> · <a href="/places/#method">선정·제외 기준</a> · <a href="/map.html">전국 보관 지도</a></p>')
  page('places/'+pid+'.html',label+' 기록',f'{first}~{last}, {months}개월의 원문 연결 기록과 기관별 분포, 같은 상호의 주소를 비교합니다.',body)
 body=hero('주소를 구분하고, 기록으로 비교하세요','13개 주소의 과거 지출 기록을 모았습니다. 기관과 기간을 같은 조건으로 맞춰 비교하고, 각 주소의 관측 달력과 공개 문서로 이동할 수 있습니다.','PLACE GUIDE','자료 분석·편집: 세금맛집 | 2026-10-23')+scope
 body+=sec('어떤 주소부터 볼까요',table(['장소 상세','기록 주소','행 수','관측 월','최근 관측'],cards)+'<p>상호·주소 순으로 표시합니다. 건수순 추천이나 맛 순위가 아닙니다. 브이아이피참치는 네 주소, 곰국시집은 두 주소로 나눴습니다.</p>')
 body+='<section class="section" id="compare"><h2>같은 조건으로 두 주소 비교</h2><p>같은 기간·기관으로 맞춰도 사전선정 표본과 수집 누락의 한계는 남습니다. 총액은 메뉴 가격이나 인당 식비가 아닙니다.</p><div class="grid"><label>첫 주소<select id="place-left">'+''.join(options)+'</select></label><label>둘째 주소<select id="place-right">'+''.join(options)+'</select></label><label>기간<select id="place-year"><option value="">전체 보관 기간</option><option value="2025">2025년</option><option value="2026">2026년 1~8월</option></select></label><label>기관<select id="place-org"><option value="">전체 범주</option>'+''.join(f'<option value="{o}">{v}</option>' for o,v in ORG.items())+'</select></label></div><p id="place-status" role="status">비교 도구를 불러오는 중입니다. 위 표와 장소 상세는 JavaScript 없이도 이용할 수 있습니다.</p><div id="place-comparison"></div><noscript><p>JavaScript가 꺼져 있습니다. 위 장소 상세의 기관 표와 관측 달력을 나란히 확인하거나 CSV를 내려받으세요.</p></noscript></section>'
 # Explain an observed scope difference using two distinct addresses, calculated from current rows.
 pair=[groups['p06'],groups['p08']]
 body+=sec('본청만 보면 같은 172행, 다른 기관을 더하면?', '<p><a href="/places/p06.html">브이아이피참치 세종대로 135</a>와 <a href="/places/p08.html">세종대로22길 16</a>은 2025~2026 보관 기간의 본청 기록만 보면 각각 172행입니다. 의회·사업소·소방 범주까지 더하면 주소별 기록의 구성이 달라집니다.</p>'+table(['주소','본청','그 밖의 기관 범주','전체'],[[H(v[0]['address']),sum(x['organization']=='seoul_city' for x in v),sum(x['organization']!='seoul_city' for x in v),len(v)] for v in pair])+'<p>장소를 비교할 때는 총건수보다 먼저 어느 기관의 자료인지 맞춰야 합니다. 위 비교 도구에서 두 주소와 본청을 선택한 뒤 전체 범주로 바꾸면 차이를 직접 확인할 수 있습니다. 다른 기관의 기록이 많다고 더 좋은 식당이거나 실제 방문이 더 많다는 뜻은 아닙니다.</p>')
 body+=sec('기록의 범위를 넓혀 얻은 것',f'<p>기존 서울시 본청 2025년 2,699행에서 같은 주소 조건을 유지한 채 보관 기간과 기관 범주를 넓혀 {len(rows):,}행을 연결했습니다. 신규 식당의 발견이 아니라 이미 선정한 주소의 시간·기관 맥락을 보강한 자료입니다.</p>'+table(['범주','2025년','2026년 1~8월'],[[ORG[o],sum(x['organization']==o and x['date'].startswith('2025') for x in rows),sum(x['organization']==o and x['date'].startswith('2026') for x in rows)] for o in ORG]))
 body+='<section class="section" id="method"><h2>출처·재계산·제외 기준</h2><p>서울 정보소통광장 업무추진비 보관 JSONL 20개에서 날짜 범위, 사전선정 상호와 도로명·번지 조합, 식사·오찬·만찬·간담 등 목적 표현, 양의 정수 금액을 확인했습니다. 다과·상품권·화환·경조·물품·선물·격려금 표현은 제외했습니다. 문서 ID와 행 번호의 중복은 제거하고, 금액·날짜가 같아도 별도 원문 행이면 유지합니다. 목적 키워드는 식당 여부의 완전한 증명이 아니며 수기 오기와 파싱 오류가 남을 수 있습니다.</p><p>선정 주소 밖의 동명 업소, 주소 누락·다른 번지, 잘못된 날짜와 금액은 포함하지 않습니다. 원문 전체의 수집 완전성을 입증하지 않으며 모든 행을 새로 온라인 대조한 자료도 아닙니다. 참석자와 목적 자유문은 공개하지 않습니다.</p><p><a href="/data/place-audit.json">공식 원문 표본 대조 기록</a> · <a href="/data/place-records.csv">공개 행 CSV</a> · <a href="/data/place-records.json">입력 해시·수집량·제외 집계 및 공개 행 JSON</a> · <a href="/regions/seoul_city.html">기존 2025 본청 상세 검색</a> · <a href="/contact.html">오류 제보</a></p></section>'
 page('places/index.html','주소별 기록과 비교','13개 주소의 기간·기관·관측 달력·원문 사례를 확인하고 두 장소를 같은 조건으로 비교합니다.',body,True,script='<script src="/assets/places.js" defer></script>')
if __name__=='__main__':
 import sys
 data=extract(sys.argv[1]);out=ROOT/'data/place-records.json';out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 with (ROOT/'data/place-records.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(data['rows'][0]),lineterminator='\n');w.writeheader();w.writerows(data['rows'])
 print(json.dumps({'rows':len(data['rows']),'parsed':data['parsed_rows'],'exclusions':data['exclusions'],'organizations':dict(Counter(r['organization'] for r in data['rows']))},ensure_ascii=False))
