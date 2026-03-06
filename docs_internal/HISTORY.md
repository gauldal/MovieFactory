# MovieFactory – Development History

이 문서는 MovieFactory 프로젝트의 주요 개발 단계를 기록한다.

---

# Phase 1 – 초기 설계

* 텍스트 검색 기반 영화 탐색 시스템 설계
* TF-IDF 검색 구현
* Flask 기반 웹 서비스 구조 구성

---

# Phase 2 – Hybrid Retrieval 도입

* SBERT semantic search 추가
* TF-IDF + SBERT Hybrid 구조 구성
* 검색 품질 개선

---

# Phase 3 – 이미지 검색 도입

* CLIP 기반 포스터 검색 추가
* 이미지 업로드 기반 영화 탐색 기능 구현

---

# Phase 4 – 데이터 구조 재설계

* 포스터 보유 영화만 포함하는 dataset 구성
* canonical dataset 도입

```
movie_clean_data_poster.csv
```

---

# Phase 5 – Runtime 안정화

주요 문제 해결

* TF-IDF matrix dimension mismatch
* SBERT embedding length mismatch
* 캐시 정합성 문제

RuntimeEngine 안정화 완료

---

# Phase 6 – UX 안정화

주요 개선

* 이미지 검색 세션 문제 해결
* 검색 타입 우선순위 정립
* 상세 페이지 데이터 구조 개선

---

# Phase 7 – Image Search v3

문제

CLIP 단독 검색 품질 문제

해결

```
CLIP + SBERT
RRF Fusion
```

후보 풀

```
CLIP pool
+
SBERT pool
```

결과

* 의미 기반 유사 영화 노출
* 특정 영화 고정 문제 해결

---

# Phase 8 – Evaluation System 구축

구성

```
text_queries_intent.yaml
run_text_eval
regression_check
baseline.json
```

CI

```
GitHub Actions regression.yml
```

---

# Phase 9 – Observability Dashboard

Streamlit 기반 운영 도구 구축

구성

```
Query Lab
Quality Monitor
```

기능

* 검색 실험 기록
* 성능 모니터링
* 결과 분석

---

# Phase 10 – Documentation 정리

프로젝트 문서 정리

```
README
Architecture
Builder Manual
Presentation
SPEC
QUESTIONS
HISTORY
TROUBLESHOOTING
```

MovieFactory 프로젝트 문서 구조 확정.
