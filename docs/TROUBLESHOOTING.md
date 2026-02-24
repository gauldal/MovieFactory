2026/02/09
# MovieFactory – Troubleshooting

## 문제 1. TF-IDF matmul dimension mismatch
- 원인:
  - CSV와 캐시 기준 불일치
- 해결:
  - poster 기준 CSV로 통일
  - npz + vectorizer 쌍만 사용

---

## 문제 2. SBERT IndexError
- 원인:
  - embeddings 길이와 movie_ids 길이 불일치
- 해결:
  - 엔진 초기화 시 min 길이로 강제 슬라이싱

---

## 문제 3. 이미지 검색 화면 고정
- 원인:
  - session에 image_search_path가 계속 유지됨
- 해결:
  - genre / text 진입 시 세션 강제 해제
  - reset 옵션 추가

---

## 문제 4. 포스터가 안 보임
- 원인:
  - tmdb_poster_url 비어 있음
- 해결:
  - poster_path 기반 URL 자동 생성

---

## 문제 5. 상세페이지 메타정보 누락
- 원인:
  - 검색 카드용 dict를 상세에도 사용
- 해결:
  - card / detail 분리
  - 상세 전용 row_to_detail 도입

# [TROUBLESHOOTING.md] 추가 (2026-02-09)

## 증상: 이미지 검색 결과가 “똑같이” 나오거나 품질이 변하지 않음
- 원인 후보:
  - 수정한 runtime_engine.py가 실제 실행 경로의 파일이 아닐 수 있음
  - 이미지 분기 로직이 CLIP 단독으로 남아있을 수 있음
- 확인:
  - 콘솔에 [IMG-HYBRID] 또는 [IMG-RRF] 로그가 찍히는지 확인

## 증상: 결과가 2234개 전부 나옴
- 원인:
  - “대상 전체 비교”와 “결과 전체 노출”을 혼동한 상태
- 해결:
  - 결과 컷 정책 적용 (MAX_RESULTS, MIN_RESULTS)
  - RRF 사용 시 점수 기반 컷(best*ratio) 금지 → 순위 기반 컷 사용

## 증상: 결과가 2개 등으로 너무 적게 나옴
- 원인:
  - RRF 점수 scale이 작아 best*ratio 컷을 적용하면 대부분 제거됨
- 해결:
  - RRF는 순위 기반 컷으로 변경
  - 약한 입력 판정은 clip_best(원점수)로 처리

## 증상: 특정 movie_id(예: 155)가 아예 결과에서 사라짐 (rank=None)
- 원인:
  - CLIP_RANK_POOL 제한으로 후보 풀에 포함되지 않음
    - 예: CLIP rank=1213인데 pool=600이면 제외
- 해결:
  - RRF 대상 pool을 (CLIP 상위 pool) ∪ (SBERT 상위 pool) 합집합으로 구성
  - 검수 중에는 필요 시 pool_ids.add(155) 같은 임시 안전장치로 확인 가능(검수 후 제거)

## 권장 디버그 로그(필수)
- pseudo_query / candidates / sbert_scores / clip_best / kept
- TARGET movie_id 랭크 및 TOP20 출력
  - 예: [IMG-RRF][TARGET] movie_id=155 rank=2

[문제] KeyError: 'id'
원인: CSV 컬럼이 id가 아니라 movie_id
해결: 컬럼명 확인 후 movie_id 사용

[문제] Intent 쿼리 장황하게 작성 시 전부 0점
원인: Anchor 정보 부족 + 데이터셋 title 미일치
해결: title anchor 전략 도입

[문제] hit@5/10 0.9로 회귀 발생
원인: 일부 쿼리 target 미포함
해결: 정확한 title 포함하여 재작성

[문제] GitHub 로그인 2FA 막힘
원인: Authenticator 미등록
해결: github-recovery-codes.txt 사용 복구

[문제] eval_reports git rm 실패
원인: 추적된 적 없음
해결: git ls-files로 확인 후 무시

[문제] CI와 로컬 결과 불일치 우려
해결: regression.yml에서 check_regression.bat 직접 호출

# Troubleshooting Log – 2026-02-12

---

## 문제 1: 트레일러 개수 변경이 반영되지 않음

### 증상
- max_items=4 설정했는데 3개만 표시

### 원인
- main.py에서 3으로 고정되어 있었음
- movie_api.py는 실제 라우트가 아님

### 해결
- main.py 수정
- 중복 호출 제거

---

## 문제 2: Similar 개수 변경 불가

### 증상
- limit=6으로 변경해도 14개 유지

### 원인
- mobile 분기 없이 고정값 사용

### 해결
- is_mobile_request() 기반 분기 추가

---

## 문제 3: 모바일 블랙톤 혼입

### 증상
- 일부 섹션 블랙톤 적용
- 텍스트 안 보임

### 원인
- mobile.css 일부 덮어쓰기
- base 스타일 상속 충돌

### 해결
- 모바일 화이트톤 재설계
- 불필요 dark 스타일 제거

---

## 문제 4: 햄버거 버튼 미작동

### 원인
- mobile.js 이벤트 누락
- CSS z-index 충돌

### 해결
- JS 이벤트 재연결
- overlay/panel 구조 재정렬

---

## 문제 5: 이미지 리사이징 안 됨

### 원인
- CSS max-width 미적용

### 해결
- md-poster max-width 100% 적용

---

## 문제 6: Explain API 동작 오류

### 원인
- bp 정의 누락
- Blueprint 등록 순서 문제

### 해결
- explain_bp를 main.py에서 등록
- bp 정의 위치 정정

[TROUBLESHOOTING GUIDE — MovieFactory]

1. 이미지 검색 결과 600개 노출
원인:
- threshold 미설정
- best_score 기준 없이 raw similarity 필터링

해결:
- best_score * ratio 방식 도입
- anchor 기준 컷 적용

---

2. CLIP score 0.000 출력
원인:
- 정규화 미적용
- float formatting 오류

해결:
- score normalization
- 소수점 formatting 통일

---

3. 모바일 장르 패널 스크롤 따라 내려감
원인:
- position fixed 누락
- overlay z-index 문제

해결:
- overlay fixed
- panel z-index 4500 유지

---

4. border 제거 후 상단 고정 깨짐
원인:
- layout 의존 border 구조

해결:
- 구조 재정렬 (header 위 배치)

---

5. Engine bar 색상 적용 안 됨
원인:
- score-high / mid / low 클래스 미적용
- JS ratio 계산 누락

해결:
- maxScore 기준 ratio 계산 추가
- mf-engine-bar-fill 클래스 적용

---

6. Footer 2줄 출력
원인:
- mf-bottom-bar와 footer-dashboard 분리 구조

해결:
- bottom-bar 내부에 footer 문구 통합
- footer-dashboard display:none

[문제 1] Port scan timeout
원인:
- gunicorn이 $PORT에 bind되지 않음
해결:
- --bind 0.0.0.0:$PORT 명시

--------------------------------------------------

[문제 2] ModuleNotFoundError: clip
원인:
- openai clip 패키지 미설치
해결:
- open_clip_torch 전환
- requirements.txt 추가

--------------------------------------------------

[문제 3] 서버 부팅 중 CLIP 모델 로딩으로 실패
원인:
- __init__ 시점에 heavy import 발생
해결:
- Lazy loading 구조 도입
- encoder는 score() 호출 시 생성

--------------------------------------------------

[문제 4] Render Free에서 빌드 지연
원인:
- Free 플랜 빌드 큐 대기
- torch 설치 시간 소요
대응:
- 대기 (10~20분 정상 범위)
- 불필요한 재배포 금지

--------------------------------------------------

[문제 5] Deploy 로그가 즉시 안 보임
원인:
- 로그 시간 필터
- Live tail 미사용
대응:
- Last hour → Last day 변경
- Live tail ON
- F5 새로고침

--------------------------------------------------

[문제 6] CLIP 비활성화 테스트 필요 시
해결:
- Render 환경변수 DISABLE_CLIP=1 설정
- 서버 안정성 확인 후 재활성화