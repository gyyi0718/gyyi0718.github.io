"""Shared display eligibility and source definition for the reviewed Jeju pages."""
import re
SOURCE_URL = "https://www.bigdata-culture.kr/bigdata/user/data_market/detail.do?id=f0306b70-597a-11ec-8ee4-95f65f846b27"
FOOD = {"한식", "카페", "술집", "간식", "양식", "치킨", "분식", "중식", "일식", "패스트푸드", "아시아음식", "뷔페", "샤브샤브", "퓨전요리", "도시락", "제과제빵", "미분류"}
PROHIBITED = re.compile(r"유흥|숙박|판매|여관|호텔|모텔")
def allowed_store(store):
    return store.get("indsLclsNm") == "음식" and not PROHIBITED.search(store.get("indsSclsNm") or "")
def page_shell(text, filename):
    text = text.replace("</head>", '<meta name="google-adsense-account" content="ca-pub-3133301641364865"><link rel="canonical" href="https://gyyi0718.github.io/maechul/' + filename + '"></head>', 1)
    nav = '<nav style="padding:12px 16px;background:white;display:flex;gap:16px;flex-wrap:wrap"><a href="../index.html">세금맛집</a><a href="index.html">제주 두 시점</a><a href="map.html">제주 후보 지도</a><a href="../sources.html">출처</a><a href="../corrections.html">정정</a><a href="../contact.html">문의</a></nav>'
    return text.replace("<body>", "<body>" + nav, 1)
