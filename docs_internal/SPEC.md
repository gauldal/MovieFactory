# MovieFactory – System Specification

## 1. Purpose

MovieFactory는 단일 원본 데이터로부터 동일한 검색 서비스를 재현 가능한 구조로 구축하는 것을 목표로 한다.

본 프로젝트의 핵심 목표는 다음과 같다.

* 단일 원본 데이터 기반 검색 서비스 구축
* Hybrid Retrieval 구조 구현
* Builder 기반 재현 가능한 시스템 구성
* 검색 품질 실험 및 관찰 구조 구축

이 프로젝트는 단순한 검색 데모가 아니라 **설계 → 실행 → 검증 → 관찰이 가능한 시스템 구조**를 목표로 한다.

---

# 2. System Architecture

MovieFactory는 다음과 같은 레이어 구조로 구성된다.

```
Data Layer
Engine Layer
Service Layer
Evaluation Layer
Observability Layer
```

---

## 2.1 Data Layer

Raw Input

```
movies_metadata_20000.csv
```

Canonical Dataset

```
moviefactory/data/movie_clean_data_poster.csv
```

정책

* 포스터 존재 영화만 포함
* movie_id 기준 정렬
* 중복 제거
* 모든 엔진 / UI / 서비스는 이 CSV만 사용

이 파일은 **Single Source of Truth**이다.

---

## 2.2 Engine Layer

구성

* TF-IDF Engine
* SBERT Engine
* CLIP Engine
* Hybrid Engine
* Runtime Engine

원칙

* 엔진은 점수 계산만 수행
* 상태 저장 금지
* UI 로직 금지
* Flask 의존 금지

---

## 2.3 Image Search v3 Architecture

이미지 검색은 다음 구조로 동작한다.

```
Image Upload
→ CLIP Poster Similarity
→ Prompt 기반 pseudo_query 생성
→ SBERT semantic search
→ RRF Fusion
```

설정

```
CLIP_RANK_POOL = 600
SBERT_RANK_POOL = 800
RRF k = 40
w_clip = 1.0
w_sbert = 1.4
```

후보 풀

```
(CLIP top pool) ∪ (SBERT top pool)
```

컷 정책

* 점수 기반 ratio 컷 금지
* 순위 기반 컷 사용

---

## 2.4 Service Layer

서비스는 Flask 기반 웹 애플리케이션으로 구성된다.

구성

```
search_api
movie_api
dashboard_api
```

UI 구성

```
Home
Search Results
Movie Detail
Dashboard
```

역할

* 사용자 입력 처리
* 엔진 실행 트리거
* 결과 시각화

---

## 2.5 Evaluation Layer

검색 품질 평가를 위한 오프라인 평가 시스템을 포함한다.

구성

```
run_text_eval.py
regression_check.py
baseline.json
text_queries_intent.yaml
```

평가 지표

```
hit@1
hit@5
hit@10
mean_rank
```

정책

* baseline 대비 hit@k 감소 시 FAIL

---

## 2.6 Observability Layer

검색 품질 관찰을 위한 구조

구성

```
Query Lab
Quality Monitor
runs/*.json 기록
```

측정 지표

```
latency_ms
result_count
failure_tagging
engine_stats
```

MovieFactory의 UI는 단순 서비스 UI가 아니라 **검색 설계 관찰 도구**로 사용된다.

---

# 3. Builder Strategy

MovieFactory는 Level 1 Builder 전략을 채택한다.

목표

```
동일한 프로젝트 구조를 자동으로 재현
```

Builder 역할

* 프로젝트 구조 생성
* canonical dataset 준비
* 캐시 로드
* 실행 환경 구성

Builder는 **검색 로직을 생성하지 않는다.**

---

# 4. Core Principles

MovieFactory는 다음 원칙을 따른다.

1. Single Canonical Dataset
2. Engine Layer 책임 분리
3. Runtime 기반 검색 실행
4. Offline Evaluation 지원
5. Observability 구조 포함
6. Builder 기반 재현성 확보

---

# 5. Final Statement

MovieFactory는 단순한 검색 프로젝트가 아니라

```
검색 시스템 설계
+
검색 품질 검증
+
검색 실험 환경
```

을 하나의 구조 안에 구현한 프로젝트이다.
