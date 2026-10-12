# 검토 데이터 재생성 (2026-10-12)

실행: `python3 tools/rebuild_reviewed.py` 이후 `python3 tools/verify_pages.py`.
서울 원문 재집계: `python3 tools/rebuild_reviewed.py --refresh-seoul /Users/ygy/work/segeum/data/opengov`.
기존 입력은 tools/input/ 에 보존하고 크롤러 접근 제외하며 HTML 템플릿은 .txt로 보관합니다.

서울은 2025년 서울시 본청 수집문서에서 지정 9개 상호·13개 주소의 식사 목적 기록을 선정한 분석입니다. 전체 서울 식당 순위가 아닙니다. parsed_row는 보관 파서 행 번호이며 공식 웹페이지 연번과 다릅니다. 원문 날짜·상호·금액으로 행을 찾습니다. source-input-manifest.json은 읽은 12개 파일의 해시입니다.

## 전국 후속 재집계 입력 계약

필수 필드: source_id, source_url(공식 상세문서 또는 첨부파일), source_sha256, parsed_row, date, merchant_raw, address_raw, amount, department_raw, purpose_raw, classification(meal/nonmeal/review_hold와 근거), collection_scope(기관·부서·월별 수집 범위와 누락).
사업체 키는 상호·도로명·건물번호로 만들며 지점명을 임의 삭제하지 않습니다. 원문파일을 보존한 뒤 중복·합계행·금액·분류·주소를 검증하고 서로 다른 지표 source_document_count / parsed_row_count / restaurant_transaction_count / unique_restaurant_count / distinct_department_count 를 각각 계산합니다. 근거를 확보하지 못한 값은 null입니다.

기존 apply_* 및 gen_post* 도구는 의미가 혼재된 통계를 복원할 수 있어 중단 안내를 반환합니다. 기존 지역 top10.json은 원본 보존용이며 검증 완료 자료가 아닙니다.

검사 범위: HTML/CSV/map 일치, 보류제외, 서울 원문행 중복(의도적 중복 삽입 검사 포함), 주소별 합계·부서명수, 알려진 선정모집단 논리식, 로컬 링크. 전국 원문 검증이나 광고 승인 보장이 아닙니다. 이 명령은 배포하지 않습니다.

자료 페이지 광고송출코드는 현재 검토상태에 맞춰 제거했습니다. ads.txt와 계정메타는 유지합니다. 향후 내용과 근거를 확인한 페이지는 광고 여부를 따로 판단할 수 있습니다. noindex는 광고 심사 면제가 아닙니다.

제주 페이지는 tools/jeju/README.md의 원자료 재생성 절차를 따릅니다. tools/rebuild_reviewed.py는 제주 페이지를 덮어쓰지 않습니다. 제주 검사는 업종제외, 위경도, 후보 순번, 고유 관측월 범위, 재관측률과 공식 출처 링크까지 포함합니다.
