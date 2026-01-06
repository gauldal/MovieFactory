# 🛠️ MovieFactory Builder Manual

본 문서는 MovieFactory 프로젝트를 **누구나 동일한 결과로 재현**하기 위한  
Builder의 역할과 실행 절차를 설명한다.

Builder는 “편의 스크립트”가 아니라  
**프로젝트 전체를 다시 만들어내는 단일 진입점(Single Entry Point)** 이다.

---

## 1. Builder의 책임 범위

`zip_builder_final.py`는 다음을 보장한다.

1. project_root 디렉토리 생성
2. 코드 구조 배치
3. 데이터 파일 복사
4. 엔진 캐시 생성 트리거
5. 즉시 실행 가능한 상태 보장

Builder 실행 이후에는  
**추가 수동 설정 없이 Web UI와 Dashboard를 바로 실행**할 수 있어야 한다.

---

## 2. Builder 실행 전 준비 사항

- Python 3.9+
- Docker / Docker Compose
- (선택) GPU 환경 시 CUDA 지원

권장 실행 위치:

    movie_factory/
    └─ zip_builder_final.py

---

## 3. 기본 실행 방법

    python zip_builder_final.py

Builder 실행이 완료되면  
아래와 같은 산출물이 생성된다.

    movie_factory_project/
    ├─ moviefactory/
    ├─ docs_public/
    ├─ docker-compose.yml
    ├─ Dockerfile.*
    └─ requirements*.txt

---

## 4. Builder 내부 실행 흐름

Builder는 다음 순서로 동작한다.

    1. project_root 생성
    2. 디렉토리 구조 구성
    3. 소스 코드 배치
    4. 데이터 복사
    5. Engine ensure 단계 호출
       - run_sbert()
       - run_tfidf()
       - run_cf()
       - run_hybrid()
    6. 실행 가능 상태 검증

이 과정에서 Builder는  
**엔진 내부 로직을 직접 다루지 않는다.**

---

## 5. FAST / FULL 모드 개념

Builder는 두 가지 실행 모드를 가진다.

### FAST 모드
- 목적: 구조 및 실행 경로 검증
- 특징:
  - 최소 데이터 사용
  - 빠른 캐시 생성
- 권장 용도:
  - 초기 구조 확인
  - CI / 테스트 환경

### FULL 모드
- 목적: 전체 데이터 기반 실행
- 특징:
  - 전체 캐시 생성
  - 실제 서비스 수준 결과
- 권장 용도:
  - 최종 검증
  - 발표 / 데모

v1 기준에서는 **FAST 모드로 구조 검증을 우선 권장**한다.

---

## 6. Builder 실패 시 체크리스트

### 캐시 관련
- `.cache/` 디렉토리가 비어 있음
  → Engine ensure 단계 실패

### 검색 속도가 느림
- 캐시 미생성 또는 삭제됨
  → Builder 재실행 필요

### Dashboard가 실행되지 않음
- Streamlit 컨테이너 상태 확인
- docker-compose 로그 확인

---

## 7. Builder 설계 철학

Builder는 다음 원칙을 따른다.

- 환경 의존성 최소화
- 명시적 산출물 생성
- 실행 결과의 결정성 보장

즉,  
**“한 번 실행하면, 누가 실행해도 같은 결과”**를 목표로 한다.

---

## 8. 요약

- Builder는 프로젝트의 시작점이다
- 모든 실행 경로는 Builder를 기준으로 한다
- 수동 설정이 개입되면 설계 의도에서 벗어난다

MovieFactory의 재현성은  
**Builder 설계에서 시작된다.**
