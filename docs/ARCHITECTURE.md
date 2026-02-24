# Architecture

## 1. 전체 구조

Raw Data
↓
Builder
↓
Canonical Dataset (movie_clean_data_poster.csv)
↓
Engine Cache Layer
↓
Runtime Engine
↓
Web / Mobile App

---

## 2. 계층별 역할

### Data Layer
- 단일 기준 데이터 로드
- 포스터 존재 영화만 서비스 대상

### Builder Layer
- 데이터 정제
- 임베딩 생성
- 캐시 생성
- 재현 가능한 산출물 생성

### Engine Layer
- TF-IDF 점수 계산
- SBERT 점수 계산
- CLIP 점수 계산
- Hybrid 가중 결합

### Runtime Layer
- 후보군 생성
- 정렬 전략 적용
- Ranker ON/OFF 분기

### Experiment Layer
- Offline Proxy Metric 계산
- A/B 비교
- Δ 계산

### App Layer
- Dashboard
- Engine 비교 UI
- Recommendation Analysis

---

## 3. A/B 실험 구조

Ranker OFF:
- TF-IDF only

Ranker ON:
- hybrid_rerank()

비교 지표:
- 5 Proxy Metrics

---

## 4. 설계 원칙

- 단일 기준 데이터
- 캐시 기반 속도 보장
- Runtime은 캐시만 사용
- Builder 실패 시 전체 중단
- 평가와 UI 분리