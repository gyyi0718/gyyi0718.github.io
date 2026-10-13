# 제주 두 시점·동별 후보 재생성

원본 CSV와 jeju_stores.jsonl을 보유한 작업 폴더에서 아래 스크립트를 순서대로 실행합니다. 스크립트와 jeju_review.py를 같은 폴더에 둡니다. 입력 파일 해시와 재집계 통계는 data/jeju-review.json에 있습니다.

1. python3 build_survivors.py
2. python3 build_survivors_html.py
3. python3 build_map_data.py
4. python3 match_map.py
5. python3 build_map_html.py

출력 jeju/survivors.html → 사이트 maechul/index.html, jeju/maechul_map.html → 사이트 maechul/map.html. 사이트 tools/verify_pages.py로 검사 후 배포합니다. 입력은 2021·2025년 각 12개월이며 결측 파일은 오류로 중단합니다.

필터: 원자료 음식 중분류 목록, 유흥시설·숙박·식품판매·식품 제외. 화면은 상가정보 음식 대분류 중 유흥·숙박·판매 세부분류 제외. 재관측률은 원자료 필터 이후 동일 상호·행정동 키 분모이며 지도 후보 분모와 다릅니다.

2026-10-12 수정: 실제 매출·연속 영업·폐업 주장 철회. 지도는 상위 5개 중 좌표 연결된 후보이며 13개는 후순위. 같은 상호·행정동 여러 행은 합산하되 관측 개월은 고유 월수. 지도 장소 매칭은 상호 유사도 추정이며 사업자번호 검증이 아닙니다. 파일의 FOOD 필터 변경 시 모든 지표와 문구를 재생성합니다.

2026-10-13 지도 수정: CARTO의 API KEY REQUIRED 오류를 확인하여 공식 https://tile.openstreetmap.org/{z}/{x}/{y}.png 로 변경했습니다. OpenStreetMap 저작권 링크를 지도에 표시하고 브라우저 기본 Referer와 HTTP 캐시를 유지합니다. 대량 수집·오프라인 다운로드·배경 prefetch 기능은 없습니다. 정책: https://operations.osmfoundation.org/policies/tiles/
