# 🏗️ MovieFactory Architecture

본 문서는 MovieFactory 프로젝트의 **시스템 구조와 설계 의도**를 설명한다.  
이 문서는 “무엇을 썼는가”가 아니라 **“왜 이렇게 나눴는가”**에 초점을 둔다.

---

## 1. 전체 구조 개요

MovieFactory는 **단일 실행 기준(project_root)** 을 중심으로  
모든 컴포넌트가 동일한 데이터와 캐시를 참조하도록 설계되었다.

실행 흐름은 아래와 같다.

    Builder 실행
        ↓
    project_root 생성
        ↓
    Engine Cache 생성 (.cache/)
        ↓
    Runtime Engine 조정
        ↓
    API (Flask)
        ↓
    Web UI / Analytics Dashboard

이 구조를 통해 환경·경로·실행 순서에 따른 불확실성을 제거한다.

---

## 2. 디렉토리 책임 분리

    movie_factory_project/
    ├─ moviefactory/
    │  ├─ app/
    │  ├─ engine/
    │  ├─ dashboard/
    │  └─ data/
    ├─ docs_public/
    └─ docker-compose.yml

각 디렉토리는 **하나의 책임만 가진다.**

---

### 2.1 app/ — Application Layer (Flask)

- Web UI 라우팅
- API Endpoint 제공
- 템플릿 렌더링

중요 원칙:
- app 레이어는 **엔진을 직접 호출하지 않는다**
- 모든 연산은 API 또는 Runtime Engine을 통해 위임된다

---

### 2.2 engine/ — Engine Layer (Search / Recommendation)

엔진 레이어는 **순수 계산 책임만 가진다.**

#### SBERT Engine
- 역할: 의미 기반 텍스트 유사도
- 입력: title + overview
- 출력: embedding → similarity
- 캐시: .cache/sbert_embeddings.pkl

#### TF-IDF Engine
- 역할: 키워드 기반 검색 보정
- 입력: 동일 텍스트
- 출력: sparse similarity
- 캐시: .cache/tfidf_matrix.pkl

#### Synthetic CF Engine
- 역할: 행동 신호 기반 유사도 시뮬레이션
- 입력: popularity, vote_average, vote_count
- 출력: movie × movie similarity
- 캐시: .cache/synthetic_cf.pkl

#### Hybrid Engine
- 역할: 개별 엔진 결과 결합
- 방식: weighted similarity sum
- 출력: 최종 movie × movie similarity
- 캐시: .cache/hybrid_similarity.pkl

엔진들은 **서로 직접 참조하지 않는다.**

---

### 2.3 runtime_engine.py — Coordinator

Runtime Engine은 다음 역할만 수행한다.

- 각 엔진의 run_xxx() 호출
- 캐시 존재 여부 확인
- 실행 순서 조정

즉, **연산은 하지 않고 조정만 한다.**

이로 인해:
- 엔진 교체
- 가중치 변경
- 캐시 전략 변경이 쉬워진다.

---

### 2.4 dashboard/ — Analytics Layer (Streamlit)

- 시각화 전용 레이어
- Flask API를 호출하여 지표 수집
- 추천 결과 및 유사도 분포 시각화

중요 원칙:
- 서비스 로직 없음
- 검색/추천 결과를 “보여주는 역할”만 수행

---

### 2.5 data/ — Dataset Layer

- 정제 완료된 단일 CSV 사용
- 모든 엔진은 동일한 데이터 기준으로 동작
- 데이터 중복 로드 없음

---

## 3. API 설계 원칙

- search_api.py : 모든 검색의 단일 진입점
- movie_api.py  : 단건 영화 조회
- dashboard_api.py : 지표 제공

API는:
- 상태를 저장하지 않는다
- 캐시를 생성하지 않는다
- Engine Layer 결과를 전달만 한다

---

## 4. 왜 이 구조인가

MovieFactory는 다음 문제를 피하기 위해 이 구조를 선택했다.

- 노트북 기반 실험 코드
- 엔진 간 강결합
- 실행 환경마다 달라지는 경로 문제
- 재현 불가능한 추천 결과

대신 선택한 것은:

- 단일 project_root
- 명시적 캐시
- 책임 분리
- 실행 가능한 서비스 구조

---

## 5. 요약

- Builder는 **재현을 보장**
- Runtime Engine은 **조정을 담당**
- Engine Layer는 **계산에 집중**
- App / Dashboard는 **표현에 집중**

이 구조는 v1 기준에서 **의도적으로 단순하지만**,  
v2 이후 확장을 고려한 **안정적인 기반**을 제공한다.
