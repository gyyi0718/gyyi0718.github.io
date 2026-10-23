"""Evidence boundaries before address normalization; not business licensing."""
import re
NONFOOD={
 'medicine':r'상비약(?:품)?|의약품|구급약|마스크|소독제|백신',
 'stationery_packaging':r'쇼핑백|종이가방|포장지|문구|사무용품|복사용지|복사지|인쇄물|토너|잉크|볼펜|봉투|포장재',
 'equipment_supplies':r'청소용품|세제|휴지|화장지|건전지|종이컵|생활용품|수건|위생용품|소모품|비품|노트북|모니터|사무기기|소프트웨어|장비|부품|제설제|보안기기|속기기계',
 'flowers_books_gifts':r'꽃다발|화분|도서(?!관)|전자책|전차책|기념품|축하품|격려품|승차권',
}
PLATFORM=re.compile(r'쿠팡|우아한형제들|배달의민족|배민|요기요|G마켓|지마켓|옥션|11번가|SSG\.?COM|네이버페이|카카오페이|결제대행|페이먼츠|PAYMENTS|코페이|다우데이타|헥토',re.I)
PLATFORM_ALIASES={
 'SSGCOM':('에스에스지닷컴','쓱닷컴','SSGCOM'),
 'COUPANG':('쿠팡','COUPANG'),
 'WOOWABROTHERS':('우아한형제들','WOOWABROTHERS'),
 'GMARKET':('지마켓','G마켓','GMARKET'),
 'AUCTION':('옥션','AUCTION'),
 '11ST':('11번가','십일번가','11ST'),
 'YOGIYO':('요기요','YOGIYO'),
 'NAVERPAY':('네이버페이','NAVERPAY'),
 'KAKAOPAY':('카카오페이','KAKAOPAY'),
}
def platform_key(text):
 text=re.sub(r'주식회사|유한회사|㈜|\(주\)|\(유\)','',text,flags=re.I)
 text=re.sub(r'[\s.·_\-]+','',text).upper()
 for canonical,aliases in PLATFORM_ALIASES.items():
  if any(alias.upper() in text for alias in aliases):return canonical
 return None
NONFOOD_VENDOR=re.compile(r'약국|문구|쇼핑백|오피스디포|철물|인쇄|서점|다이소')
def nonfood_purchase(purpose):
 t=re.sub(r'\s+','',purpose)
 for category,words in NONFOOD.items():
  # Discussion of procurement is not itself a purchase.
  for match in re.finditer(r'(?:'+words+r')(.{0,16})(?:구매|구입|제작)(?:비용|비|대금|지출|결의|\(|$)',t):
   if category=='flowers_books_gifts' and re.search(r'관련|협의|워크숍|견학|행사|참석|회의',match.group(1)):continue
   return 'nonfood_'+category
 return None
def location_boundary(name,raw_address):
 n=re.sub(r'\s+','',name);a=re.sub(r'\s+','',raw_address)
 if platform_key(n) or PLATFORM.search(n):return 'platform_or_payment_counterparty'
 if re.search(r'온라인|인터넷|통신판매|웹사이트',a):return 'online_address_context'
 if re.search(r'본사|결제처|사업자등록주소|대표주소|소재지불명|관내일대',a):return 'headquarters_or_representative_address'
 if platform_key(a) or PLATFORM.search(a):return 'platform_in_address_context'
 if NONFOOD_VENDOR.search(n):return 'nonfood_vendor_unverified'
 return None
