# MovieFactory – Design Questions & Decisions

이 문서는 MovieFactory 개발 과정에서 발생한 주요 설계 질문과 그에 대한 최종 결정을 기록한다.

---

# Q1. FAST / FULL 실행 모드를 유지할 것인가?

초기 설계에서는 FAST / FULL 두 실행 모드를 사용하였다.

목적

* FAST : 빠른 개발 테스트
* FULL : 전체 데이터 실행

결론

```
FAST / FULL 구조 폐기
```

이유

* 포스터 기반 데이터셋이 약 2,000개 수준
* 성능 차이가 크지 않음
* 구조 복잡도 증가

---

# Q2. 전처리 CSV를 덮어쓸 것인가?

선택지

1. 원본 CSV 수정
2. 새로운 CSV 생성

결론

```
새로운 Canonical CSV 생성
```

파일

```
movie_clean_data_poster.csv
```

이유

* 실험 재현성
* 원본 데이터 보존

---

# Q3. Builder는 어디까지 책임져야 하는가?

결론

```
Builder는 환경 재현까지만 책임
```

Builder 책임

* 프로젝트 구조 생성
* 캐시 준비
* 실행 환경 설정

Builder 비책임

* 검색 품질 검증
* 서비스 로직 테스트

---

# Q4. 이미지 검색 세션 정책

문제

이미지 검색 후 텍스트 검색 시 이전 이미지가 계속 적용되는 문제

결론

```
이미지 검색은 단일 세션 이벤트
```

정책

* 텍스트 검색 시작 시 이미지 세션 종료
* 장르 탐색 시작 시 이미지 세션 종료

---

# Q5. 검색 카드와 상세 페이지 데이터 구조

문제

검색 카드용 데이터와 상세 페이지 데이터가 동일 구조일 경우 정보 부족

결론

```
card / detail 데이터 분리
```

카드

* 최소 정보

상세

* 전체 메타데이터

---

# Q6. Image Search v3 Fusion 전략

초기

```
CLIP 단독 검색
```

문제

* 특정 영화 고정 노출
* 의미적 유사성 부족

결론

```
CLIP + SBERT RRF Fusion
```

효과

* 의미적 유사성 강화
* CLIP outlier 완화

---

# Final Decision

MovieFactory는 다음 전략을 채택하였다.

```
Hybrid Retrieval
+
Poster Dataset
+
Offline Evaluation
+
Observability Dashboard
```
