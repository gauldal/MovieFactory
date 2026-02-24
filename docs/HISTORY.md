2026/02/09

MovieFactory – Development History

Phase 1. 초기 설계

* FAST / FULL 분리 구조 도입
* 텍스트 기반 검색 중심 설계

Phase 2. 하이브리드 엔진 도입

* TF-IDF + SBERT 결합
* Hybrid Re-rank 구조 구현

Phase 3. 이미지 검색 추가

* CLIP 기반 포스터 검색 도입
* 포스터 보유 영화 기준 재설계

Phase 4. 구조 단순화

* FAST / FULL 폐기
* poster 기준 단일 CSV 정책 확정

Phase 5. 런타임 안정화

* 캐시 길이 불일치 문제 해결
* 엔진 내부 예외 방어 로직 추가

Phase 6. UX 안정화

* 이미지 검색 세션 고정 문제 해결
* 장르 / 텍스트 우선순위 정립

Phase 7. 최종 정리 단계

* runtime\_engine 최종본 확정
* 문서 구조 전면 재작성

\# \[HISTORY.md] 추가 (2026-02-09)



\## 이미지 검색 품질 개선 작업 (Image Search v3)

\- 현상:

  - CLIP 단독 기반 이미지 검색에서 특정 영화(예: Don Juan DeMarco)가 반복적으로 상위권에 고정되고,

    업로드한 포스터(다크나이트)가 상위에 노출되지 않거나 매우 낮은 순위로 나오는 문제가 발생.

  - 디버그 결과: movie\_id=155(The Dark Knight)가 CLIP 전체 2234 기준 약 1213위로 확인됨.



\- 조치/개선:

  1) CLIP 결과 + SBERT 의미 결과를 “가중합” 대신 “RRF(순위 결합)”으로 변경

     - 목적: CLIP outlier의 상위 고정을 완화하고 SBERT의 의미 신호를 상위에 반영.

  2) RRF는 점수 절대값이 작아 “best\*ratio” 컷을 적용하면 결과가 과도하게 줄어드는 문제 확인

     - 해결: RRF 결과 컷은 “순위 기반”으로 전환 (MAX\_RESULTS/ MIN\_RESULTS)

  3) CLIP 상위 pool만 사용할 경우(예: 600) CLIP 중위권 영화(155)가 후보에서 제외되어 사라지는 문제 확인

     - 해결: RRF 대상 풀을 (CLIP 상위 pool) ∪ (SBERT 상위 pool) 합집합으로 구성



\- 결과(검증 로그):

  - pseudo\_query: "batman vigilante superhero dark city crime"

  - clip\_best=0.9731, kept=600

  - movie\_id=155 최종 fused rank=2로 상위권 복귀



1\. SBERT/TF-IDF 하이브리드 검색 엔진 구성

2\. text\_queries.yaml → text\_queries\_intent.yaml 확장

3\. run\_text\_eval.py 10줄 보강

4\. 회귀 체크 모듈 regression\_check.py 구현

5\. baseline.json 생성

6\. check\_regression.bat 원클릭 자동화

7\. GitHub 레포 강제 초기화 및 새 구조로 푸시

8\. GitHub Actions regression.yml 추가

9\. CI를 check\_regression.bat 기반으로 통일

10\. intent 쿼리 안정형 재작성 (title anchor 전략 도입)

11\. hit@1/5/10 = 1.000 안정화

12\. regression PASS 확인



\# Development History – 2026-02-12



---



\## 1. CLIP 정확도 이슈 발견

\- target\_id 순위 불안정

\- metadata / embedding mismatch 점검

\- metadata.json 중복 없음 확인

\- clip\_engine.py 재정비



---



\## 2. RRF 디버깅

\- clip\_rank 확인

\- sbert\_rank 확인

\- fused rank 로그 추가

\- TARGET movie rank 출력



---



\## 3. 디버그 로그 제거

\- 운영 모드 전환

\- print 제거

\- DEBUG 블록 삭제



---



\## 4. 모바일 상세 개선

\- Explain 버튼 추가

\- explain.js 연결

\- aria 접근성 적용



---



\## 5. 트레일러 개수 수정 실패 원인 분석

\- movie\_api.py 수정했으나 반영 안 됨

\- 실제 라우트는 main.py에서 제어 확인

\- 중복 trailer 호출 발견

\- main.py 정리



---



\## 6. 모바일 레이아웃 이슈

\- 햄버거 버튼 미작동

\- grid 1열 출력 문제

\- mobile.css 재정비



---



\## 7. 최종 상태

\- 이미지 검색 3회 정상 동작

\- 고해상도 이미지 처리 안정

\- 모바일 2열 정상

\- Trailer 4 / Similar 6 적용 완료

\- Explain 기능 정상 작동

[CHANGE HISTORY — v1.1 → v1.3]

v1.1
- 기본 Hybrid Engine 구성
- TF-IDF / SBERT / CLIP 통합

v1.2
- Dashboard 추가
- Engine Comparison 병렬 UI 구성
- Dataset Overview 카드 도입

v1.2.5
- Image Search 과다 노출 문제 발견 (600개)
- best_score * ratio 임시 패치

v1.3
- anchor 기준 컷 안정화
- CLIP score 정규화 적용
- Engine bar 시각화 도입
- overlap highlight 적용
- Search Controls 50:50 grid 정리
- Release Year chart 고정 높이 설정
- Mobile 장르 패널 구조 안정화
- border 제거 후 scroll 고정 문제 해결
- Hero 문구 sort 기반 분기 적용
- Footer 2줄 → 1줄 통합
- footer-dashboard 제거 (mf-bottom-bar 통합)

[1단계]
- Port scan timeout 문제 발생
- gunicorn bind 설정 수정
- 0.0.0.0:$PORT 적용

[2단계]
- ModuleNotFoundError: clip 발생
- openai clip 제거
- open_clip_torch 전환

[3단계]
- CLIP import 시 서버 부팅 실패
- Lazy Loading 구조로 변경
- CLIPEngine 내부에서 torch/open_clip import

[4단계]
- CLIPScorer 초기화 시 encoder 생성 제거
- score() 호출 시에만 encoder 생성

[5단계]
- runtime_engine.py 내 image search RRF 개선
- SBERT 제한 풀 적용
- dynamic anchor threshold 추가

[6단계]
- requirements.txt에 open_clip_torch 추가
- GitHub push
- Render Auto Deploy 시작

[현재 상태]
- Render Free 환경 빌드 대기 중
- Deploying 단계에서 dependency 설치 대기