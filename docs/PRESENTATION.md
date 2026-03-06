# MovieFactory – Presentation

이 문서는 MovieFactory 프로젝트의 **설계 의도와 실험 결과**를 설명하기 위한 발표 자료입니다.

---

# 1. 문제 정의

검색 시스템에서 Hybrid Ranker는 실제로 추천 품질을 개선하는가?

검색 시스템은 보통 직관적으로 개선되지만
정량적으로 검증된 구조는 부족한 경우가 많습니다.

MovieFactory는 다음 질문을 중심으로 설계되었습니다.

```
Hybrid Retrieval은 실제로 추천 품질을 개선하는가?
```

---

# 2. 설계 접근

이 문제를 해결하기 위해 다음 구조를 설계했습니다.

* 단일 Canonical Dataset 구성
* 캐시 기반 검색 시스템 설계
* Runtime 레벨 실험 분기
* Offline Proxy Metric 기반 평가

이 구조를 통해 검색 품질 변화를 정량적으로 측정할 수 있습니다.

---

# 3. 시스템 구조

전체 시스템 구조

```
Builder
   ↓
Canonical Dataset
   ↓
Cache Engines
(TF-IDF / SBERT / CLIP)
   ↓
Runtime Engine
   ↓
Application Layer
```

실험은 Runtime 단계에서 분기됩니다.

---

# 4. A/B 실험 설계

Hybrid Ranker의 성능을 평가하기 위해 다음 비교 실험을 수행했습니다.

### OFF

```
TF-IDF only
```

### ON

```
Hybrid Rerank
(TF-IDF + SBERT)
```

실험 설정

```
120 Session Simulation
Top-K = 20
```

---

# 5. 평가 지표

검색 품질을 평가하기 위해 다음 Proxy Metric을 사용했습니다.

* Genre Coherence@K
* Intra-list Diversity@K
* Popularity(log1p)@K
* VoteCount(log1p)@K
* Weighted Rating@K

이 지표들은 추천 품질의 여러 측면을 반영합니다.

---

# 6. 결과 분석

Hybrid Ranker 적용 결과

증가

* Popularity
* VoteCount
* Weighted Rating

감소

* Genre Coherence

이는 Hybrid Ranker가

```
대중성 높은 콘텐츠 추천
```

에는 강점을 가지지만

```
장르 응집도
```

에서는 일부 trade-off가 있음을 의미합니다.

---

# 7. 결론

Hybrid Ranker는 정량적으로 추천 품질을 개선했습니다.

MovieFactory는 단순 검색 구현이 아니라

```
설계 → 실험 → 검증 → 회귀 보호
```

까지 포함한 **구조 중심 검색 시스템 프로젝트**입니다.
