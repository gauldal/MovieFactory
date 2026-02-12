# Architecture

## 전체 구조

MovieFactory는 다음과 같은 계층 구조를 가진다.

Raw Data
↓
Builder
↓
Canonical Dataset (poster)
↓
Cache Engines
↓
Runtime Engine
↓
App (Web / Mobile)

---

## 계층별 역할

### Data Layer
- 기준 데이터 로딩
- 영화 메타 정보 제공

### Engine Layer
- TF-IDF / SBERT / CLIP 점수 계산
- 하이브리드 점수 결합

### Runtime Layer
- 검색 후보 생성
- 최종 정렬 및 필터링

### App Layer
- 페이지네이션
- 웹 / 모바일 렌더링
- 사용자 요청 처리

---

## 설계 원칙

- 단일 기준 데이터 사용
- 엔진과 UI 책임 분리
- 캐시 기반 성능 최적화
- 실패 시 안전한 fallback
