# Architecture

MovieFactory는 **Hybrid Retrieval 기반 영화 검색 시스템**이며,
데이터 생성부터 검색 실행까지 다음과 같은 계층 구조로 구성됩니다.

---

# 1. 전체 시스템 흐름

```
Raw Data
   ↓
Builder
   ↓
Canonical Dataset
(movie_clean_data_poster.csv)
   ↓
Engine Cache Layer
   ↓
Runtime Engine
   ↓
Web / Mobile App
```

각 계층은 **데이터 재현성, 검색 속도, 실험 가능성**을 고려하여 설계되었습니다.

---

# 2. 계층별 역할

## Data Layer

서비스의 기준이 되는 **단일 Canonical Dataset**을 관리합니다.

역할

* 원본 데이터 로드
* 데이터 정제 기준 관리
* 포스터 존재 영화만 서비스 대상 유지

결과

```
movie_clean_data_poster.csv
```

이 파일이 **검색 시스템의 단일 기준 데이터셋**이 됩니다.

---

## Builder Layer

Builder는 프로젝트의 모든 산출물을 생성하는 **재현성 중심 파이프라인**입니다.

주요 기능

* 데이터 정제
* 임베딩 생성
* 검색 캐시 생성
* Canonical Dataset 생성

생성 산출물

* Canonical Dataset
* TF-IDF Cache
* SBERT Embeddings
* CLIP Embeddings
* Runtime Engine Cache

Builder 실행 후 **Runtime에서는 추가 계산 없이 캐시만 사용합니다.**

---

## Engine Layer

Hybrid Retrieval을 수행하는 검색 엔진 계층입니다.

지원 엔진

* TF-IDF (Keyword Retrieval)
* SBERT (Semantic Retrieval)
* CLIP (Image Retrieval)

각 엔진은 독립적으로 점수를 계산하며 이후 Hybrid Fusion 단계에서 결합됩니다.

---

## Runtime Layer

실제 검색 요청을 처리하는 계층입니다.

Runtime에서는 다음 작업이 수행됩니다.

* 후보군 생성
* 엔진 점수 계산
* Fusion 전략 적용
* 결과 정렬

Runtime 설계 원칙

* **캐시 기반 검색**
* **Builder에서 생성된 데이터만 사용**
* **Runtime에서는 임베딩 생성 없음**

---

## Experiment Layer

검색 품질 개선을 위한 실험 환경입니다.

지원 기능

* Offline Proxy Metric 계산
* A/B 실험 비교
* Hybrid vs Single Engine 비교
* Δ 변화 분석

이 실험 환경은 **Query Lab**에서 활용됩니다.

---

## App Layer

사용자 인터페이스 및 분석 도구를 제공합니다.

구성

* Movie Search Web UI
* Query Lab (검색 분석 도구)
* Ops Dashboard (운영 모니터링)

---

# 3. A/B 실험 구조

Hybrid Ranker의 성능을 평가하기 위해 Runtime 레벨에서 분기합니다.

### Ranker OFF

```
TF-IDF Only
```

### Ranker ON

```
Hybrid Rerank
(TF-IDF + SBERT)
```

두 결과를 비교하여 검색 품질 변화를 분석합니다.

---

# 4. 설계 원칙

MovieFactory는 다음 설계 원칙을 기반으로 구축되었습니다.

* **단일 Canonical Dataset 사용**
* **Builder 중심 재현 가능한 데이터 생성**
* **Runtime은 캐시 기반 실행**
* **검색 실험 구조 내장**
* **실험과 UI 분리**

이 구조를 통해

```
데이터 생성 → 검색 실행 → 실험 분석 → 운영 모니터링
```

까지 하나의 시스템 안에서 수행할 수 있습니다.
