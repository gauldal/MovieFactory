# MovieFactory – Design Questions

## Q1. FAST / FULL 분리 전략을 유지할 것인가?
- 결론: ❌ 유지하지 않음
- 이유:
  - 포스터 보유 영화 수가 약 2,000여 개
  - FAST / FULL 분리는 실익이 적고 구조 복잡도만 증가

---

## Q2. 전처리 CSV를 덮어쓸 것인가, 새로 만들 것인가?
- 결론: ✅ 새 파일 생성
- 파일명: `movie_clean_data_poster.csv`
- 이유:
  - 실험/복구 용이성
  - 빌더 재현성 확보

---

## Q3. 빌더가 검증까지 책임져야 하는가?
- 결론: 부분적으로 YES
- 검증은 “정합성 확인” 수준까지만
- 서비스 로직 검증은 런타임 책임

---

## Q4. 이미지 검색 세션은 언제 유지되는가?
- 결론:
  - 이미지 업로드 직후에만 유지
  - 텍스트 / 장르 / 홈 이동 시 즉시 해제

---

## Q5. 상세페이지 데이터는 검색 카드와 동일한가?
- 결론: ❌ 다름
- 카드용: 최소 필드
- 상세용: 전체 메타 정보 제공

# [QUESTIONS.md] 추가 (2026-02-09)

1) 이미지 검색 결과 컷 정책 최종 확정 필요
- MAX_RESULTS=600 / MIN_RESULTS=120이 현재 임시값.
- “의미 없는 이미지/노이즈 이미지” 기준을 clip_best(예: 0.55)로 유지할지, 혹은 추가 신호(예: prompt 점수 분포)로 강화할지?

2) 후보 풀 합집합 파라미터 튜닝 필요
- CLIP_RANK_POOL=600, SBERT_RANK_POOL=800이 현재값.
- 목표 UX: “배트맨 포스터 → 배트맨/어두운 범죄 액션이 상위권” + “엉뚱한 로맨스/코미디 상위 진입 최소화”
- 질문: pool 크기를 줄여 잡음을 줄일지(정밀도↑), 늘려 recall을 높일지(재현율↑) 기준 합의 필요.

3) 프롬프트 리스트 고도화
- 현재 pseudo_query는 top prompt 6개 중 score>0만 합쳐서 생성.
- 질문:
  - MovieFactory 장르 탭 용어(영문/한글/약어)와 동의어를 얼마나 확장할지?
  - “batman”처럼 특정 키워드를 계속 둘지(데이터셋/확장성 관점)?

4) 품질 평가 기준 정의
- 이미지 검색 품질을 어떤 방식으로 측정/검수할지:
  - 특정 대표 포스터(배트맨 등) Top-N 포함 여부
  - 장르/톤 일치율(정성)
  - 유사 포스터(색감/구도) vs 유사 서사(overview) 중 우선순위

[데이터 관련]
□ movie_clean_data_poster.csv 컬럼 확인했는가? (movie_id 사용)
□ Canonical CSV row 수 변동 없는가?
□ eval_reports는 git에 추적되지 않는가?

[평가 관련]
□ text_queries_intent.yaml 중복 타깃 없는가?
□ title anchor 전략 사용했는가?
□ baseline.json 최신 상태인가?

[CI 관련]
□ regression.yml이 check_regression.bat를 직접 실행하는가?
□ Windows runner 사용 중인가?
□ exit code가 정확히 전달되는가?

[Git 관련]
□ origin URL이 https://github.com/gauldal/MovieFactory.git 인가?
□ main 브랜치 강제 push 후 정상 동기화 되었는가?
□ GitHub Actions green 상태인가?

# Decision Log – 2026-02-12

---

## 1. 포트폴리오용인데 로딩/예외 처리 필요?

결론:
- 기본 기능이 우선
- 과도한 UX 연출은 불필요
- 안정성 > 연출

---

## 2. 모바일 트레일러 3개 vs 4개

문제:
- max_items 변경했는데 반영 안 됨

원인:
- movie_api.py가 아닌 main.py에서 실제 갯수 제어

결론:
- 모바일 4개
- 웹 3개 유지

---

## 3. Similar 개수 모바일에서 줄일 것인가?

문제:
- 모바일 2열 구조에서 홀수 노출 불균형

결론:
- 모바일 6개 (3x2 구성)
- 웹 14개 유지

---

## 4. Explain 기능 어디에 둘 것인가?

선택지:
- 검색 리스트
- 상세 페이지

결론:
- 상세 페이지에만 배치
- 리스트는 UI 복잡도 증가로 제외

---

## 5. 모바일 톤 블랙 vs 화이트

문제:
- 블랙톤 일부 적용으로 통일감 붕괴

결론:
- 웹/모바일 모두 화이트톤 유지

[QA CHECKLIST — MovieFactory v1.3]

A. HERO
□ Popular / Latest 토글 시 문구 정상 변경되는가?
□ Hero sort 버튼 active 상태 정상인가?
□ CLS (레이아웃 점프) 발생하지 않는가?

B. MOBILE
□ 장르 패널 열 때 배경 스크롤 고정되는가?
□ border 라인 제거 후 UI 깨짐 없는가?
□ 페이지네이션 중앙 정렬 유지되는가?

C. IMAGE SEARCH
□ 600개 과다 노출 문제 해결되었는가?
□ best_score ratio 적용 후 결과 수 안정적인가?
□ CLIP score 0.000 문제 해결되었는가?

D. DASHBOARD
□ Text 검색 시 TF-IDF / SBERT 동시 작동하는가?
□ Image 검색 시 CLIP만 작동하는가?
□ Engine Bar 길이 점수 비례하는가?
□ Overlap 항목 강조되는가?
□ Chart 영역 스크롤 영향 받지 않는가?

E. FOOTER
□ 한 줄로 출력되는가?
□ Sticky 유지되는가?
□ 가운데 문구 overflow 시 깨지지 않는가?

F. 반응형
□ 1024px 이하 grid 1열 전환되는가?
□ 모바일에서 dashboard input grid 깨지지 않는가?
