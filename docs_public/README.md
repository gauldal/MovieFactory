# 🎬 MovieFactory

MovieFactory는 **텍스트 · 이미지 · 행동 기반 신호를 결합한  
엔드투엔드 영화 검색·추천 시스템**입니다.

이 프로젝트의 목표는 단순히 “추천 정확도”를 높이는 것이 아니라,  
**ML / DL 기반 추천 시스템을 실제 서비스 구조로  
재현 가능하게 설계하고 실행하는 것**입니다.

---

## 📎 Note

MovieFactory는  
추천 정확도 경쟁이나 최신 모델 벤치마크를 목표로 하지 않습니다.  
**재현 가능한 추천 시스템 구조 설계**에 초점을 둔 프로젝트입니다.

---

## ✨ 핵심 특징

### 🔍 4가지 독립 검색 엔진
- **SBERT**: 의미 기반 텍스트 검색 (Semantic Search)
- **TF-IDF**: 키워드 중심 텍스트 검색
- **CLIP**: 이미지 기반 영화 검색
- **Synthetic CF**: 행동 지표(popularity 등)를 활용한 유사도 계산

### 🔗 4가지 하이브리드 검색 방식
- SBERT + TF-IDF + CF 결합 Hybrid Ranking
- 단건 영화 기반 유사 영화 추천
- 텍스트 검색 → Hybrid 재정렬
- 이미지 검색 → Hybrid 결합

### 단일 Builder 실행으로 전체 구조 재현
- 데이터
- 엔진 캐시
- API
- Web UI
- Streamlit Dashboard

---

## 🧠 설계 철학

- **성능보다 구조**
- **모델보다 파이프라인**
- **실험보다 재현성**

MovieFactory v1은 일부러 다음을 포함하지 않습니다.
- LLM / RAG
- Online Learning
- 실사용 로그 기반 개인화

이유는 명확합니다.  
**복잡한 기능보다, 끝까지 실행 가능한 구조를 먼저 완성하는 것이 목적**이기 때문입니다.

---

## 🚀 빠른 시작

    python zip_builder_final.py
    cd movie_factory_project
    docker-compose up

- Web UI (Flask): http://localhost:5000  
- Analytics Dashboard (Streamlit): http://localhost:8501  

---

## 📁 프로젝트 구조 요약

    movie_factory_project/
    ├─ moviefactory/
    │  ├─ app/        # Flask Web UI & API
    │  ├─ engine/     # Search / Recommendation Engines
    │  ├─ dashboard/  # Streamlit Analytics
    │  └─ data/       # Clean Movie Dataset
    ├─ docs_public/   # GitHub Documentation
    └─ docker-compose.yml

---

## 📌 문서 안내

- **ARCHITECTURE.md**  
  전체 시스템 구조와 엔진 책임 설명

- **BUILDER_MANUAL.md**  
  Builder 실행 방식과 재현 절차

- **PRESENTATION.md**  
  프로젝트 의도 및 발표·면접용 설명

---

## 📈 확장 방향 (v2+)

- 사용자 행동 로그 기반 CF
- LLM 기반 추천 설명 레이어
- A/B Test 기반 랭킹 비교
- Online Feature Store 연계

---

MovieFactory는  
**“돌아가는 추천 시스템을 처음부터 끝까지 설계·구현할 수 있는가”**에 대한  
하나의 완성된 답변입니다.

---

## 🏷️ Build Metadata

This release was built with **v1.1-final (FAST)** — see `BUILD_INFO.json`.

---

## ⚠️ 실행 환경 안내

- 본 프로젝트는 **Docker 기반 실행**을 전제로 설계되었습니다.
- Windows / macOS / Linux 환경에서 동일하게 실행 가능합니다.
- GPU 가속은 선택 사항이며, 기본 실행은 CPU 기준입니다.

---

## 🐳 Dockerfile 정책 요약

- `Dockerfile.flask` : CPU 기반 Flask Web / API (기본)
- `Dockerfile.streamlit` : Streamlit Dashboard
- `Dockerfile.gpu` : GPU 가속 환경 (선택)

---

## 📄 License

This project is released under the **MIT License**.
