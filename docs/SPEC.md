# MovieFactory SPEC

## 1. 목적 (Purpose)

MovieFactory는  
**단일 원본 데이터로부터 어느 환경에서든 동일한 산출물을 생성하고,  
웹/모바일 환경에서 정상적으로 동작하는 영화 검색 서비스를 재현 가능하게 만드는 것**을 목표로 한다.

본 프로젝트는 실험용 코드나 중간 산출물이 아닌,  
**완성된 서비스 형태를 기준으로 동결(frozen)된 산출물**을 생성하는 데 목적이 있다.

---

## 2. 프로젝트 범위 (Scope)

MovieFactory는 다음 기능을 포함한다.

- Flask 기반 웹/모바일 영화 검색 서비스
- 텍스트 기반 검색 (TF-IDF / SBERT)
- 이미지(포스터) 기반 검색 (CLIP)
- 장르 기반 탐색
- 하이브리드 검색 결과 통합
- 단일 기준 데이터셋과 캐시를 사용한 안정적인 런타임

본 SPEC은 **최종 서비스 기준**만을 다루며,  
과거 실험/트러블/질문 기록은 본 명세의 범위에 포함하지 않는다.

---

## 3. 입력 데이터 (Single Raw Input)

### 3.1 Raw Input

- 입력 파일: `movies_metadata_20000.csv`
- 출처: TMDB 기반 영화 메타데이터
- 역할: **유일한 원본 데이터**

빌더는 오직 이 원본 파일 하나만을 입력으로 사용한다.

---

## 4. 전처리 및 기준 데이터 (Canonical Dataset)

### 4.1 유일 기준 데이터 (Single Source of Truth)

- 파일명: `movie_clean_data_poster.csv`
- 위치: `moviefactory/data/movie_clean_data_poster.csv`

본 파일은 **서비스, 엔진, 검색, UI, 캐시 생성의 유일한 기준 데이터**이다.

### 4.2 생성 원칙

`movie_clean_data_poster.csv`는 다음 조건을 만족하는 영화만 포함한다.

- 유효한 포스터 정보가 존재하는 영화
- CLIP 포스터 임베딩 생성에 성공한 영화 집합
- 중복 제거된 `movie_id` 기준 정렬된 데이터

이 데이터셋은 약 2,000여 개 영화로 구성되며,  
**서비스에 실제로 노출 가능한 영화만 포함**한다.

### 4.3 컬럼 구성

기준 데이터는 아래 컬럼을 포함한다.

- movie_id
- title
- original_title
- overview
- tagline
- genres
- tmdb_poster_url
- poster_path
- popularity
- vote_average
- vote_count
- release_date
- runtime

본 컬럼 구성은 영화 리스트, 상세 페이지, 검색, 장르 탐색에 충분하다.

---

## 5. 캐시 및 엔진 데이터 (Caches & Engines)

### 5.1 캐시 기준

모든 캐시는 `movie_clean_data_poster.csv`를 기준으로 생성된다.

- TF-IDF 캐시
- SBERT 임베딩
- CLIP 이미지 임베딩
- (선택) CF 추천 캐시

### 5.2 일관성 원칙

- 모든 캐시는 동일한 `movie_id` 집합과 순서를 공유해야 한다.
- 캐시 간 길이 또는 정렬 불일치는 허용하지 않는다.
- 캐시가 존재하지 않는 엔진은 자동으로 비활성화되며, 서비스는 중단되지 않는다.

---

## 6. 런타임 엔진 (Runtime Engine)

### 6.1 역할 분리

- RuntimeEngine:  
  - 기준 CSV 로딩
  - 검색 결과 후보 생성
  - 최종 정렬 및 필터링
- HybridEngine:  
  - 엔진별 점수 정규화
  - 가중치 기반 점수 결합
- 개별 엔진(TFIDF, SBERT, CLIP, CF):  
  - 점수 계산만 수행
  - 순위/페이지/출력 책임 없음

### 6.2 반환 계약

- 검색 엔진의 최종 반환값은 **영화 dict 리스트(List[Dict])**이다.
- 페이지네이션, 슬라이싱은 App 레이어에서 처리한다.

---

## 7. 서비스 구조 (Service Structure)

### 7.1 App

- Flask 기반
- 웹/모바일 템플릿 분리
- 모든 화면은 `movie_clean_data_poster.csv` 기준으로 동작

### 7.2 UI 원칙

- 포스터 없는 영화는 서비스에 노출하지 않는다.
- 웹/모바일 UI는 동결 대상이며, 빌더는 UI를 변경하지 않는다.

---

## 8. 빌더의 책임 (Builder Responsibility)

최종 빌더는 다음을 책임진다.

- 원본 데이터(`movies_metadata_20000.csv`) 기반 전처리
- `movie_clean_data_poster.csv` 생성
- 캐시 및 산출물 생성
- 필수 산출물이 누락된 경우 빌더 실행 실패로 처리
- 코드 트리 구성
- 서비스 기동에 필요한 모든 산출물 제공

빌더는 수작업 개입 없이 동일한 결과를 생성해야 한다.

---

## 9. 비목표 (Out of Scope)

다음은 본 SPEC의 범위에 포함하지 않는다.

- 사용자 계정 기반 추천 시스템
- 실시간 로그 수집/분석
- 외부 API 의존 서비스
- 학습 파이프라인 자동화

---

## 10. 명세의 상태 (Status)

본 문서는 MovieFactory 프로젝트의 **동결 명세(Frozen Specification)** 이며,  
본 문서를 기준으로 프로젝트는 완성 상태로 관리된다.
-
# MovieFactory – Specification (SPEC)

## 1. 프로젝트 개요
MovieFactory는 영화 메타데이터를 기반으로  
텍스트 / 장르 / 이미지(포스터) 검색을 통합 제공하는 하이브리드 영화 탐색 서비스다.

본 프로젝트의 핵심 목표는:
- 단일 원본 데이터로부터
- 완전 자동화된 빌더를 통해
- 어디서든 동일한 산출물과 서비스 상태를 재현하는 것이다.

---

## 2. Canonical Data 정책
- 유일한 원본 데이터: `movies_metadata_20000.csv`
- 런타임에서 사용하는 유일한 전처리 데이터:
  - `movie_clean_data_poster.csv`
- 모든 캐시, 엔진, 서비스는 **poster 기준 CSV**만 참조한다.

---

## 3. 데이터 기준
- 포스터가 존재하는 영화만 서비스 대상
- `poster_path`만 존재하는 경우:
  - `tmdb_poster_url`을 자동 생성하여 사용
- 포스터 없는 영화는 런타임에서 제외

---

## 4. 검색 유형
### 4.1 텍스트 검색
- TF-IDF + SBERT 하이브리드
- Hybrid Re-rank 적용
- title / overview 기준 필터링

### 4.2 장르 검색
- DB 필터 기반 검색
- 장르 alias 지원 (예: SF → Science Fiction)

### 4.3 이미지 검색
- CLIP 엔진 단독 사용
- 업로드된 이미지 기반 유사 포스터 검색

---

## 5. 런타임 엔진 계약
- 모든 검색 결과는 `List[Dict]` 형태로 반환
- tuple / pandas 객체 반환 금지
- 검색 실패 시 빈 리스트 반환
- 서버 500 오류를 유발하는 예외는 엔진 내부에서 차단

---

## 6. 서비스 구성
- Web 페이지 (Desktop)
- Mobile 페이지
- API (search / movie / explain / dashboard)

---

## 7. 캐시 구조
.cache/full_working/
- tfidf/
- sbert/
- clip/
- metadata.json

---

## 8. 빌더 책임
- 원본 CSV 기반 전처리 수행
- `movie_clean_data_poster.csv` 생성
- 모든 캐시 및 코드 트리 자동 생성
- 필수 산출물 누락 시 빌더 실패 처리
- 수작업 개입 없이 동일 결과 보장

# [SPEC.md] 추가/갱신 (2026-02-09)

## Image Search v3 (CLIP→Prompt→SBERT→RRF) 설계 확정
- 목적: 이미지(포스터) 기반 검색에서 “분위기/의미” 유사도를 우선 반영하고, CLIP outlier(특정 포스터가 항상 1등) 문제를 완화한다.
- 파이프라인:
  1) CLIP(이미지↔포스터) 전체 비교로 movie_id→score 생성 (대상: 2234)
  2) CLIP(image↔text prompt)로 prompt 점수 계산 → 상위 prompt로 pseudo_query 생성
  3) SBERT(pseudo_query↔overview)로 의미 점수 생성
  4) RRF(Reciprocal Rank Fusion)로 CLIP rank + SBERT rank 결합해 최종 순위 산출
- RRF 튜닝 파라미터(현재 검증값):
  - k=40
  - w_clip=1.0
  - w_sbert=1.4

## 후보 풀(POOL) 정책
- 문제: CLIP rank 상위 N개만 풀로 쓰면, CLIP에서 중위권인 영화(예: movie_id=155)가 후보에서 제외되어 최종 결과에서 사라질 수 있음.
- 해결: RRF 대상 pool은 **(CLIP 상위 pool) ∪ (SBERT 상위 pool)** 합집합으로 구성한다.
  - CLIP_RANK_POOL: 600 (튜닝 범위 600~1200)
  - SBERT_RANK_POOL: 800 (튜닝 범위 600~1200)

## 결과 컷 정책(UX)
- 대상 비교는 전체(2234) 가능하나, 결과 UI는 “유사한 것”만 노출해야 함.
- RRF 점수는 scale이 작고 절대값 의미가 약하므로, best*ratio 같은 “점수 기반 컷”은 금지.
- 컷은 “순위 기반”으로 수행:
  - MAX_RESULTS=600 (UI 페이징은 여기서 21개씩)
  - MIN_RESULTS=120 (입력이 약한 경우 축소)
  - clip_best(원점수) 기준으로 약한 쿼리 판정:
    - clip_best < 0.55 → MIN_RESULTS까지만 반환

프로젝트명: MovieFactory
목표: 하이브리드 영화 검색 엔진의 정량 평가 및 회귀 방지 자동화

[엔진 구성]
- SBERT + TF-IDF 하이브리드 검색
- Canonical CSV: moviefactory/data/movie_clean_data_poster.csv
- 평가 쿼리: moviefactory/eval/text_queries_intent.yaml

[평가 지표]
- hit@1
- hit@5
- hit@10
- mean_rank (정답 존재 시 평균 순위)

[평가 실행 명령]
python -m moviefactory.eval.run_text_eval moviefactory/eval/text_queries_intent.yaml

[회귀 체크 명령]
python -m moviefactory.eval.regression_check moviefactory/eval/text_queries_intent.yaml

[원클릭 실행]
check_regression.bat

[Baseline 정책]
- baseline.json과 비교
- hit@k 감소 시 FAIL
- mean_rank 증가 시 FAIL

[현재 안정 상태]
hit@1  = 1.000
hit@5  = 1.000
hit@10 = 1.000
mean_rank = 1.00

# MovieFactory – Mobile & Detail Enhancement Spec
Date: 2026-02-12

---

## 1. 이미지 검색 시스템 안정화

### 목표
- CLIP 기반 이미지 검색 정확도 향상
- RRF(Reciprocal Rank Fusion) 결합 안정화
- 디버그 로그 제거 후 클린 모드 전환

### 구현 내용
- CLIP + SBERT RRF 결합 구조 유지
- CLIP pool = 600
- SBERT pool = 800
- RRF weight:
  - w_clip = 1.0
  - w_sbert = 1.4
- 디버그 로그 전면 제거 (운영 모드)

---

## 2. 모바일 상세 페이지 개선

### 트레일러 개수
- 모바일: 4개
- 웹: 3개

### Similar Movies 개수
- 모바일: 6개 (2행 구성)
- 웹: 14개 유지

### 분기 기준
- is_mobile_request() 기반 템플릿 분기

---

## 3. Explain 기능 (추천 이유 표시)

### 위치
- movie_detail_mobile.html
- movie_detail.html

### 동작 방식
- 버튼 클릭 → /api/explain/<movie_id> 호출
- JS(explain.js)로 결과 비동기 표시
- aria-live 적용 (접근성 대응)

---

## 4. 모바일 UI 통일

### 톤
- 모바일 화이트톤 유지 (웹과 통일)
- 블랙톤 제거

### 구조
- 모바일 2열 카드 레이아웃
- Similar 3x2 유지
- Trailer 2x2 구성

---

## 5. 정리 사항

- 중복 트레일러 호출 제거
- 디버그 print 제거
- 운영용 안정 코드 확정

[PROJECT] MovieFactory v1.3 — UI & Dashboard Stabilization Spec

1. HOME / SEARCH HERO
- Popular / Latest 토글 시 Hero 문구 동적 변경
- sort 파라미터 기반 텍스트 조건 분기
- Eyebrow / Title / Description 구조 고정
- CSS 단일 소스 유지 (mf-hero-* 계열)

2. MOBILE UI
- 햄버거 장르 패널:
  - overlay 고정 (scroll 영향 제거)
  - header 위 레이어 정리
  - 불필요 border 제거
- 페이지네이션 중앙 정렬
- 장르 패널 라인 제거 (clean UI 유지)

3. IMAGE SEARCH LOGIC
- best_score * ratio 방식 적용
- anchor 기준 컷 도입
- 결과 수 과다 노출(600개) → 안정화
- CLIP score 정규화 적용 (0~1)

4. ENGINE COMPARISON (Dashboard)
- TF-IDF / SBERT / CLIP 병렬 비교
- Top 5 노출
- 점수 기반 bar 시각화
- ratio 기반 score-high / mid / low 클래스 적용
- overlap highlight 적용

5. DASHBOARD LAYOUT
- Dataset Overview 카드형 구조
- Search Controls 50:50 grid
- Engine Grid 3-column 고정
- Release Year Chart 고정 height
- Recommendation Analysis 2-column grid

6. FOOTER 통합
- mf-bottom-bar에 footer 문구 통합
- 기존 footer-dashboard 숨김
- 한 줄 구조:
  [ARRAY] — [브랜드 문구] — [Top / Dashboard]
- sticky bottom 유지

7. CSS 정책
- SINGLE SOURCE OF TRUTH 유지
- dashboard 영역은 mf-dashboard-* prefix만 사용
- global grid geometry 절대 수정 금지
- :root 변수 오염 금지

[프로젝트명]
MovieFactory – Hybrid Search + CLIP Image Search 기반 영화 검색 시스템

[배포 환경]
- Platform: Render (Free Plan)
- Runtime: Python 3
- WSGI: gunicorn
- Entry: moviefactory.app.main:app
- Port Binding: 0.0.0.0:$PORT

[핵심 아키텍처]

1. RuntimeEngine
   - 전체 검색/추천 통합 엔진
   - CSV 기반 메타데이터 로딩
   - Poster 없는 영화 제외 정책 적용
   - 장르 캐시 (_genres_cache) 사전 생성

2. Text Search (Hybrid)
   - TF-IDF + SBERT hybrid_rerank
   - Title Boost 안전장치 포함
   - gibberish 필터링 적용
   - score threshold 0.12 컷 정책

3. Image Search
   - CLIP 기반 cosine similarity
   - Prompt 기반 pseudo_query 생성
   - SBERT 제한 풀(pool) 내 결합
   - RRF 기반 fusion
   - 동적 anchor threshold 컷 정책

4. CLIP 구조 개선
   - open_clip_torch 사용
   - Lazy Loading 구조 적용
     - CLIPScorer 생성 시 모델 로딩 안 함
     - score() 호출 시 encoder 생성
   - DISABLE_CLIP 환경변수 지원

5. Dashboard Engine Comparison
   - TF-IDF similarity
   - SBERT similarity
   - CLIP similarity (원본 cosine score)

[데이터]
- canonical CSV:
  - movie_clean_data_poster.csv 우선
  - fallback: movie_clean_data.csv
- clip_embeddings.npz 사용 (우선)
- metadata.json 기반 movie_id 매핑

[배포 명령]
gunicorn moviefactory.app.main:app --bind 0.0.0.0:$PORT

[의존성]
- torch
- open_clip_torch
- sentence-transformers
- scikit-learn
- pandas
- numpy
- pillow