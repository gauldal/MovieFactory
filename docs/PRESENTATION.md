# MovieFactory – Presentation

---

## 1. 문제 정의

Hybrid Ranker는 실제로 추천 품질을 개선하는가?

검색 시스템은 보통 직관적으로 개선하지만,
정량적 검증 구조는 부족하다.

---

## 2. 설계 접근

- 단일 기준 데이터셋 구성
- 캐시 기반 검색 구조 설계
- Runtime에서 실험 분기 가능하도록 설계
- Offline Proxy Metric 기반 A/B 실험 설계

---

## 3. 시스템 구조

Builder → Canonical Dataset → Cache Engines → Runtime → App

실험은 Runtime 레벨에서 분기.

---

## 4. A/B 실험 설계

OFF:
TF-IDF only

ON:
Hybrid Rerank

120 Session Simulation

Top-K = 20

---

## 5. 평가 지표

- Genre Coherence@K
- Intra-list Diversity@K
- Popularity(log1p)@K
- VoteCount(log1p)@K
- Weighted Rating@K

---

## 6. 결과 분석

Hybrid는:

- Popularity 증가
- VoteCount 증가
- Weighted Rating 증가

Trade-off:

- Genre Coherence 감소

즉,
상업적 추천 품질은 개선되었으나,
장르 응집도는 일부 감소.

---

## 7. 결론

Hybrid Ranker는
정량적으로 추천 품질을 개선한다.

본 프로젝트는 단순 구현이 아니라,
설계 → 실험 → 검증 → 회귀 보호까지 포함한
구조 중심 시스템이다.