import json,re,collections,datetime,sys,hashlib
from pathlib import Path
from place_boundaries import location_boundary
from purpose_types import purpose_class,purpose_category,PURPOSE_LABELS
DIST='종로구 중구 용산구 성동구 광진구 동대문구 중랑구 성북구 강북구 도봉구 노원구 은평구 서대문구 마포구 양천구 강서구 구로구 금천구 영등포구 동작구 관악구 서초구 강남구 송파구 강동구'.split()
BAD=re.compile(r'청사|구내|간담회장|회의실|상황실|편의점|마트|카페|까페|커피|스타벅스|제과|과자|베이커리|베이글|파리바게|뚜레쥬|출장|호텔|HOTEL|회관|백화점|온라인|배달|정보통신|코페이|키오스크|다우데이타|헥토|후생|복지위원회|행복플러스|에스씨케이|한국야쿠르트|과일|후르츠|곤트란|코코호도|크로와상|탐앤탐스|투썸|팀홀튼|파리크라상|파스쿠찌|폴바셋|풀바셋|할리스|가배도|펠트|콜렉티보|노티드|TWG|Tea|외\s*\d|등\s*\d|\d{3}[- ]\d{3,4}',re.I)
def address(a):
 if not re.search(r'서울(?:특별시|시)?\s',a):return None
 d=next((d for d in DIST if re.search(r'(?:\s|^)'+d+r'(?:\s|$)',a)),None)
 if not d:return None
 a=re.sub(r'(?<=[로길])\s+(?=\d+[가-힣]*길)','',a)
 m=re.search(r'([가-힣A-Za-z0-9·]+(?:대로|번길|길|로))\s*(\d+(?:-\d+)?)(?![\d가-힣])',a)
 if not m:return None
 if re.search(r'(?:태평로|신문로) [12]$', ' '.join(m.groups())):return None
 return d,' '.join(m.groups())

# Reviewed ambiguous billing labels / non-meal venues are held, not silently renamed.
HOLD=set("골든컴퍼니파트너스주식회사 디에스디엘주식회사 롯데쇼핑㈜ 루미호스피탈리티K-FOOD 르메르디앙목시지점 마루 마쉐리 성원푸드몰 스케줄코퍼레이션 스타필드애비뉴그랑서울 시안컴퍼니 식사 씨제이푸드빌 아이 아이와푸즈코리아 엔엠에프 엠즈씨드 오씨아이드림주식회사 정신 제스트에프앤씨 제이유엔유통 제이큐코리아 티시스신문로지점 한진흥업㈜ 한화푸드테크 해피푸드코리아 효창에프씨".split())
EXTRA=re.compile(r'매점|전통차|전통찻|와플|던킨|루소랩|매머드|배스킨|백미당|블랑제리|비터버터|빠우|엘리스파이|파란만잔')
ORG={'seoul_city':'서울시 본청','seoul_council':'서울시의회','seoul_office':'사업소','seoul_fire':'소방'}
ROOT=Path(__file__).resolve().parents[1]
def extract(raw):
 groups=collections.defaultdict(list);rej=collections.Counter();seen=set();inputs=[];coverage=collections.Counter();raw_count=0;decisions=[];boundary_rows=[]
 for p in sorted(Path(raw).glob('20??-??.jsonl')):
  inputs.append({'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
  for line in p.open():
   o=json.loads(line);doc=o['doc']
   for r in o['rows']:
    raw_count+=1;coverage[p.stem+'/'+doc['org_id']]+=1
    key=(doc['id'],r['row_no'])
    if key in seen:rej['duplicate_document_row']+=1;continue
    seen.add(key)
    if doc['org_id'] not in ORG:rej['other_institution']+=1;continue
    try:day=datetime.date.fromisoformat(r.get('d') or '')
    except ValueError:rej['invalid_date']+=1;continue
    if not '2025-01-01'<=str(day)<='2026-08-31':rej['outside_period']+=1;continue
    purpose=r.get('purpose') or ''
    category,classification=purpose_category(purpose)
    decisions.append({'source_id':doc['id'],'parsed_row':r['row_no'],'category':category,'reason':classification})
    boundary=classification if classification.startswith('nonfood_') else location_boundary(r.get('place') or '',r.get('addr') or '')
    if boundary:
     rej[boundary]+=1;boundary_rows.append({'source_id':doc['id'],'source_url':doc['url'],'parsed_row':r['row_no'],'reason':boundary,'amount':r.get('amount')});continue
    if classification=='non_meal_purchase':
     rej[classification]+=1
     continue
    a=address(r.get('addr') or '')
    if not a:rej['address_not_explicit_or_complete']+=1;continue
    n=re.sub(r'\s+','',r.get('place') or '')
    n=re.sub(r'^(?:주식회사|㈜|\(주\)|주\))','',n).strip(' ()').upper()
    if not 2<=len(n)<=45 or BAD.search(n) or EXTRA.search(n) or n in HOLD or re.search(r'[/;@]|[가-힣]외$|등$|^\d+점$',n):rej['non_meal_or_ambiguous_name']+=1;continue
    if (n,a[1]) in {('적당','을지로 29'),('라운드앤드','정동길 35')}:
     rej['venue_type_uncertain']+=1;decisions.append({'source_id':doc['id'],'parsed_row':r['row_no'],'reason':'venue_type_uncertain'});continue
    amount=r.get('amount')
    if isinstance(amount,bool) or not isinstance(amount,(int,float)) or not 0<amount<=3000000 or int(amount)!=amount:rej['invalid_or_review_amount']+=1;continue
    assert doc['url']=='https://opengov.seoul.go.kr/expense/'+doc['id'].split(':')[1]
    groups[(n,*a)].append({'source_id':doc['id'],'source_url':doc['url'],'parsed_row':r['row_no'],'date':str(day),'organization':doc['org_id'],'department':r.get('dept') or '', 'amount':int(amount),'purpose_category':category,'purpose_reason':classification})
 selected=[];records={}
 for key,rows in sorted(groups.items()):
  docs=len({r['source_id'] for r in rows});months=len({r['date'][:7] for r in rows})
  if docs<5 or months<3:rej['below_repeat_threshold']+=len(rows);continue
  pid=hashlib.sha256('|'.join(key).encode()).hexdigest()[:12]
  assert pid not in records
  rows.sort(key=lambda r:(r['date'],r['source_id'],r['parsed_row']));records[pid]=rows
  selected.append({'id':pid,'name':key[0],'district':key[1],'address':'서울 '+key[1]+' '+key[2],'records':len(rows),'purpose_counts':dict(collections.Counter(r['purpose_category'] for r in rows)),'venue_type':'unverified','location_evidence':'named_address_no_intermediary_context','documents':docs,'months':months,'first':rows[0]['date'],'last':rows[-1]['date'],'scopes':dict(collections.Counter(r['date'][:4]+'/'+r['organization']+'/'+r['purpose_category'] for r in rows)),'organizations':dict(collections.Counter(r['organization'] for r in rows)),'source_url':rows[-1]['source_url']})
 return {'schema':4,'boundary_rows':boundary_rows,'purpose_rule':'All included spending rows classified as meal, uncertain, refreshment or mixed; purposes are not business-category certification','purpose_counts':dict(collections.Counter(r['purpose_category'] for rs in records.values() for r in rs)),'purpose_amounts':{k:sum(r['amount'] for rs in records.values() for r in rs if r['purpose_category']==k) for k in PURPOSE_LABELS},'purpose_decisions':decisions,'updated':'2026-10-23','period':['2025-01-01','2026-08-31'],'raw_rows':raw_count,'exclusions':dict(rej),'input_files':inputs,'coverage':dict(coverage),'selected_rows':sum(map(len,records.values())),'places':selected},records

def write(raw):
 import csv
 data,records=extract(raw);folder=ROOT/'data/seoul-directory';folder.mkdir(exist_ok=True)
 (ROOT/'data/seoul-place-boundary-audit.json').write_text(json.dumps({'scope':'Excluded before address normalization; not current business classification','rows':data.pop('boundary_rows')},ensure_ascii=False,separators=(',',':'))+'\n')
 (ROOT/'tools/seoul-purpose-decisions.json').write_text(json.dumps(data.pop('purpose_decisions'),ensure_ascii=False,separators=(',',':'))+'\n')
 (ROOT/'data/seoul-directory.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
 for stale in folder.glob('*.json'):
  if stale.stem not in records:stale.unlink() # regenerated public shards only; raw files remain untouched
 fields=['place_id','name','district','address','source_id','source_url','parsed_row','date','organization','department','amount','purpose_category','purpose_reason']
 with (ROOT/'data/seoul-directory-records.csv').open('w') as f:
  writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');writer.writeheader()
  for p in data['places']:
   rs=records[p['id']];(folder/(p['id']+'.json')).write_text(json.dumps(rs,ensure_ascii=False,separators=(',',':'))+'\n')
   for r in rs:writer.writerow(dict(place_id=p['id'],name=p['name'],district=p['district'],address=p['address'],**r))
 print(json.dumps({'groups':len(data['places']),'rows':data['selected_rows'],'districts':len(set(p['district'] for p in data['places'])),'exclusions':data['exclusions']},ensure_ascii=False))

def render(page,hero,sec,table,H):
 from urllib.parse import quote
 data=json.loads((ROOT/'data/seoul-directory.json').read_text());places=data['places'];by=collections.defaultdict(list)
 for p in places:by[p['district']].append(p)
 scope='<p class="note">서울 공개 지출 보관자료에서 상호 사전선정 없이 추출한 원문 지출 장소 후보입니다. 기본 건수·금액은 식사 명시·용도 미확정·간식/음료·혼합을 합한 전체 포함 행입니다. 업종을 확인한 식당 목록은 아닙니다. 상호 표기와 주소가 같은 묶음이며 고유 사업체 수·맛 순위가 아닙니다. 현재 영업은 확인하지 않았습니다. 전국 지도는 별도의 보관 목록입니다.</p>'
 body=hero('지역에서 후보를 찾고, 이용 근거를 확인하세요','원문에 흩어진 지출 장소 후보를 주소·기간·기관으로 찾습니다. 후보를 선택하면 월별 기록과 공개 문서, 같은 주소의 다른 상호 표기까지 확인할 수 있습니다.','SEOUL RECORD FINDER','자료 분석·편집: 세금맛집 | 2026-10-23')+scope
 body+=f'<p><b>{len(places):,}개 상호·주소 묶음 · {len(by)}개 구 · {data["selected_rows"]:,}행</b> / 2025년 1월~2026년 8월 보관자료</p>'
 body+='<section class="section" id="finder"><h2>장소 후보 찾기</h2><div class="grid"><label for="b-query">상호·도로명 검색</label><input id="b-query" type="search" placeholder="예: 칼국수, 성수, 서소문로"><label for="b-district">장소 소재 구</label><select id="b-district"><option value="">전체 구</option>'+''.join(f'<option>{d}</option>' for d in DIST if d in by)+'</select><label for="b-year">기록 기간</label><select id="b-year"><option value="">전체 보관 기간</option><option value="2025">2025년</option><option value="2026">2026년 1~8월</option></select><label for="b-org">문서 기관 범주</label><select id="b-org"><option value="">전체 기관</option>'+''.join(f'<option value="{k}">{v}</option>' for k,v in ORG.items())+'</select><label for="b-purpose">목적 확인 수준</label><select id="b-purpose"><option value="">전체 지출 기록</option><option value="meal">원문에 식사 명시</option><option value="uncertain">용도 미확정</option><option value="refreshment">간식·음료 명시</option><option value="mixed">식사·간식 혼합 명시</option></select></div><p id="b-status" role="status">탐색 자료를 불러오는 중입니다. 아래 지역별 원문 목록은 JavaScript 없이도 읽을 수 있습니다.</p><div id="b-results"></div><div class="actions"><button id="b-prev" type="button">이전 후보</button><span id="b-page"></span><button id="b-next" type="button">다음 후보</button><button id="b-reset" type="button">조건 초기화</button></div></section><section class="section" id="record-detail" tabindex="-1"><h2>선택한 장소의 기록</h2><div id="b-detail">후보의 ‘기록 보기’를 선택하세요. 다른 후보를 ‘비교에 추가’하면 같은 기간·기관으로 나란히 볼 수 있습니다.</div></section>'
 body+=sec('목적 확인 수준별 포함 행',table(['분류','행 수','집행액 합계 (원)'],[[PURPOSE_LABELS[k],data['purpose_counts'].get(k,0),data['purpose_amounts'].get(k,0)] for k in PURPOSE_LABELS])+'<p>네 분류는 서로 겹치지 않으며 합계가 전체 포함 행입니다. 원문에 식사 명시는 문구에 근거한 분류이고 업종 인증이 아닙니다. 간담회만 적힌 행은 용도 미확정으로 남깁니다. 식사와 음료가 함께 적힌 혼합 구매는 혼합 명시 분류로 보내며 전체 금액을 식사에 합산하지 않습니다. 위 필터는 두 비교 장소와 CSV에도 같은 기준으로 적용합니다.</p>')
 central=sum(len(by[d]) for d in ('중구','종로구'));share=round(central/len(places)*100,1)
 body+=sec('서울 전체 식당 분포와 다른 이유',f'<p>이 자료의 {share}%({central:,}/{len(places):,}묶음)는 중구·종로구 주소입니다. 식당이 그곳에만 있어서가 아니라, 서울시 기관이 공개한 지출 자료와 주소·반복 기록 조건을 통과한 범위이기 때문입니다. 내 동네가 적게 나오면 아래 지역 표를 확인하고 전국 보관 지도로 탐색 범위를 넓힐 수 있습니다.</p><p>같은 건물에 여러 업소가 있거나 같은 업소의 이름이 다르게 적힐 수 있습니다. 주소만 같다는 이유로 합산하지 않았습니다. 후보 상세에서 같은 주소의 다른 표기를 함께 보여 주므로, 원문을 확인해 지점을 구분하세요.</p>')
 summary=[]
 for d in DIST:
  ps=by[d];n=sum(p['records'] for p in ps)
  summary.append([H(d),len(ps),n,'<a href="#area-'+str(DIST.index(d))+'">원문 목록</a>' if ps else '기준을 충족한 기록 없음'])
 body+=sec('지역별 기록 범위',table(['장소 소재 구','상호·주소 묶음','원문 연결 행','탐색'],summary)+'<p>0은 식당이 없다는 뜻이 아닙니다. 원문에 서울·구·도로명·건물번호가 모두 있어야 하며, 최소 5개 문서·3개 월에서 나타난 묶음만 제공합니다. 단발성 후보와 주소 불명확 기록은 공개하지 않습니다.</p>')
 for d in DIST:
  ps=by[d]
  if not ps:continue
  orgs=collections.Counter()
  for p in ps:orgs.update(p['organizations'])
  body+=f'<section class="section" id="area-{DIST.index(d)}"><h2>{d}의 원문 연결 후보</h2><p>{len(ps)}개 표기·주소 묶음에서 {sum(p["records"] for p in ps):,}행을 확인했습니다. 문서 범주별 행: '+H(' · '.join(ORG[o]+' '+str(orgs[o]) for o in ORG))+'. 구청의 지출만을 뜻하지 않으며 장소 소재지 기준입니다.</p><details><summary>'+d+' 전체 후보와 원문 펼치기</summary>'+table(['상호 표기','기록 주소','행 / 문서 / 월','최근 기록','근거'],[[f'<a href="/seoul/?place={p["id"]}#record-detail">{H(p["name"])}</a>',H(p['address']),f'{p["records"]} / {p["documents"]} / {p["months"]}',p['last'],f'<a href="{p["source_url"]}">최근 공개 문서</a>'] for p in ps])+'</details></section>'
 labels={'nonfood_medicine':'의약품·위생용품 명시 구매','nonfood_stationery_packaging':'문구·포장재 명시 구매','nonfood_equipment_supplies':'장비·소모품 명시 구매','nonfood_flowers_books_gifts':'꽃·도서·기념품 명시 구매','platform_or_payment_counterparty':'플랫폼·결제대행 거래처','online_address_context':'원주소 온라인 거래 표시','headquarters_or_representative_address':'본사·결제처·대표주소 표시','platform_in_address_context':'원주소 플랫폼 표시','nonfood_vendor_unverified':'비식품 거래처로 장소 보류','meal_policy_topic_uncertain':'급식 정책·지원 등 회의 주제로 판단 보류','refreshment_or_mixed_purchase':'간식·음료 등 또는 혼합 구매','non_meal_purchase':'비식사 구매 표현','meeting_only_uncertain':'간담 표현만으로 식사 판단 불가','no_explicit_meal_word':'명시적 식사 표현 없음','venue_type_uncertain':'업종 검토 보류','outside_period':'기간 밖 날짜','purpose_not_meal':'식사 목적 조건 불충족','address_not_explicit_or_complete':'서울·구·도로명·건물번호 미확인','non_meal_or_ambiguous_name':'비식사·시설·결제 명칭 또는 모호한 상호','below_repeat_threshold':'5문서·3개월 미만','invalid_or_review_amount':'금액 검토 필요','duplicate_document_row':'동일 문서·행 중복','invalid_date':'잘못된 날짜'}
 body+='<section class="section" id="method"><h2>포함·분류·제외 기준</h2><p>주소 정규화 전에 온라인·결제대행·플랫폼·본사주소 맥락을 검사합니다. 해당 거래처와 의약품·문구·포장재·장비 등 명시적 비식품 구매는 장소 후보와 지역 집계에서 제외합니다. 모든 구매나 간담회를 제외하지 않습니다. <a href="/data/seoul-place-boundary-audit.json">제외 행의 문서·이유 기록</a>으로 지출 근거를 보존합니다. 남은 주소도 실제 방문을 입증하지 않으며 포장·배달 여부가 포함될 수 있습니다.</p><p>2025-01~2026-08 보관 원본 124,203행에 날짜·주소·상호·양의 정수 금액(300만원 이하) 조건을 적용합니다. 상품권·화환·경조·물품·선물·격려금 등 비대상 구매는 제외합니다. 간담회, 간식·음료 행은 삭제하지 않고 목적 확인 수준으로 구분합니다.</p><p>식사·오찬 등 지출/행사 표현이 명시된 행은 식사 명시, 간담회나 급식 정책 등 회의 주제만 적힌 행은 용도 미확정, 간식·음료 명시와 식사·간식 혼합 명시는 각각 별도 분류입니다. 업종·현재 영업은 미확인입니다. 카페·시설·결제대행 등 명칭과 검토에서 카페라는 제보를 받은 두 주소(적당·라운드앤드, 2026-10-23 검토; 업종 출처 재확인 전 보류)는 별도 보류하며, 이것이 모든 카페를 판별했다는 뜻은 아닙니다.</p><p>상호 표기와 명시적 서울 구·도로명·건물번호를 묶고, 전체 포함 행에서 5개 문서·3개 월 이상인 후보를 제공합니다. 목적 필터 후에는 5문서 미만이 될 수 있습니다. 표기 별칭을 합치지 않습니다. 참석자와 목적 자유문은 공개하지 않고 행별 분류와 이유 코드만 제공합니다.</p>' +table(['단계별 제외 사유','행 수'],[[labels.get(k,k),v] for k,v in data['exclusions'].items()])+f'<p>입력 {data["raw_rows"]:,} = 공개 {data["selected_rows"]:,} + 제외 {sum(data["exclusions"].values()):,}행. 사유는 순서대로 적용되어 중복 계산하지 않습니다.</p><p><a href="/data/seoul-directory-semantic-audit.json">목적 유형·기관·연도·주소별 원문 대조</a> (현행 분류) · <a href="/data/seoul-directory-source-audit.json">이전 금액·주소 표본 대조</a> (식사 분류 정확도 검증 아님) · <a href="/data/seoul-directory-records.csv">전체 공개 행 CSV</a> · <a href="/data/seoul-directory.json">집계·입력 해시·수집량 JSON</a> · <a href="/coverage.html">전국 자료 범위</a> · <a href="/sources.html">출처·검증 안내</a></p></section>'
 page('seoul/index.html','서울 지출 장소 후보 찾기','상호를 미리 고르지 않고 공개 지출에서 추출한 장소 후보를 지역·기관·기간으로 찾고 원문을 확인합니다.',body,True,script='<script src="/assets/seoul-directory.js" defer></script>')
if __name__=='__main__':write(sys.argv[1])
