# 🎬 MovieFactory
  
**Search Quality Improvement Platform**
  
Hybrid Movie Search & Search Experiment System  
Hybrid Retrieval Engine  
Query Lab  
Quality Monitor  
  
CX Tech / Search Systems Portfolio Project
  
<p align="center">
  <img src="docs/images/demo.gif" width="900">
</p>
  
MovieFactory는 **검색 품질 개선(Search Quality Improvement)**을 목표로 설계된 Hybrid Movie Search Experiment Platform입니다.
  
이 프로젝트에서는 다음 기능을 하나의 구조로 통합했습니다.
- 서로 다른 검색 모델을 결합하여 검색 품질 개선  
- 검색 결과 랭킹을 분석하는 Search Quality Analysis 환경 구축  
- 검색 알고리즘 실험(Query Lab)  
- 검색 품질 모니터링(Search Ops Dashboard)  
  
검색 기능 구현을 넘어 **검색 품질 분석, 실험, 운영까지 포함한 Search Quality Lifecycle 시스템**을 설계했습니다.

이 프로젝트는 다음 질문에서 시작되었습니다.
> 서로 다른 검색 모델을 결합하면 실제 검색 품질이 좋아질까?  
> 그리고 검색 품질 변화를 어떻게 분석하고 검증할 수 있을까?  
  
MovieFactory는 이 질문을 탐구하기 위해 만들어진 **검색 품질 실험 시스템**입니다.
  
---
  
# 🚀 What This Project Demonstrates
MovieFactory는 다음 문제를 해결하기 위한 프로젝트입니다.
- 검색 결과 품질 개선 (Search Quality Improvement)  
- 검색 결과 분석 (Search Result Analysis)  
- 검색 알고리즘 실험 (Search Experimentation)  
- 검색 시스템 운영 모니터링 (Search Operations Monitoring)  
  
검색 시스템을 단순 기능이 아닌 검색 품질을 분석하고 실험할 수 있는 **Search Experiment Platform**을 구축했습니다.

# 📑 목차
* [Demo](#-demo)
* [프로젝트 설계 목표](#-프로젝트-설계-목표)
* [Problem](#-problem)
* [Solution](#-solution)
* [Search Quality Improvement](#-search-quality-improvement)
* [Technical Highlights](#-technical-highlights)
* [Key Features](#-key-features)
* [System Architecture](#-system-architecture)
* [Architecture Key Ideas](#-architecture-key-ideas)
* [Mobile UI](#-mobile-ui)
* [Application Screens](#-application-screens)
* [Search Experiment Tools](#-search-experiment-tools)
* [검색 실험 환경](#-검색-실험-환경)
* [Search Evaluation Result](#-search-evaluation-result)
* [Evaluation & Regression](#-evaluation--regression)
* [기술 스택](#-기술-스택)
* [Project Timeline](#-project-timeline)
* [What I Learned](#-what-i-learned)
* [Troubleshooting](#-troubleshooting)
* [Installation](#-installation)
* [Run Application](#-run-application)
* [프로젝트 구조](#-프로젝트-구조)
* [프로젝트 핵심 포인트](#-프로젝트-핵심-포인트)
* [Project Status](#-project-status)

---

# 🎬 Demo

### Web Demo
<p align="center">
  <img src="docs/images/demo.gif" width="900">
</p>

### Mobile Demo
<p align="center">
  <img src="docs/images/mobile_demo.gif" width="420">
</p>

MovieFactory는 다음 흐름으로 동작합니다.  
1️⃣ Text Search  
2️⃣ Image Search  
3️⃣ Query Lab 분석  
4️⃣ Hybrid Ranking Explain  
5️⃣ Search Ops Monitoring  
MovieFactory는 **검색 → 분석 → 실험 → 운영** 흐름을 제공하는 **Search Experiment Platform**입니다.

---

# 🎯 프로젝트 설계 목표
검색 시스템은 단순히 결과를 반환하는 기능을 넘어 다음 문제를 해결해야 합니다.

- 서로 다른 검색 모델을 결합하는 **Hybrid Retrieval**
- 검색 결과 품질을 분석하는 **Search Result Explainability**  
- 검색 모델 성능을 비교할 수 있는 **Experiment Environment**
- 실제 서비스 품질을 관리하는 **Search Operations Monitoring**
  
MovieFactory는 이러한 문제를 해결하기 위해  
**검색 시스템 + 실험 환경 + 운영 모니터링**을 하나의 구조로 설계했습니다.

---

# 🔎 Problem
영화 검색 시스템은 보통 하나의 검색 방식에 의존합니다.
예를 들어
  
- 키워드 검색 → 의미 기반 유사도 부족
- 의미 검색 → 정확한 키워드 매칭 부족
- 이미지 검색 → 서사적 연관성 부족
  
또한 검색 시스템에서는 다음 질문에 답하기 어렵습니다.
- 왜 특정 영화가 상위에 랭크되었을까?
- Search Quality를 바꾸면 결과는 어떻게 달라질까?
  
MovieFactory는 이러한 문제를 해결하기 위해  
- **Hybrid Search Architecture**  
- **Search Result Explainability**  
- **Search Experiment Environment**  
- **Search Operations Monitoring**
  
를 하나의 시스템으로 통합했습니다.

---

# 💡 Solution
MovieFactory는 검색 품질 개선을 위한 **Search Quality Improvement Platform**입니다.  
핵심 접근 방식은 다음과 같습니다.
  
### Hybrid Retrieval
TF-IDF, SBERT, CLIP 등 서로 다른 검색 엔진을 결합하여 검색 품질을 개선합니다.  
### Ranking Fusion
Reciprocal Rank Fusion(RRF)을 사용하여 서로 다른 검색 결과를 안정적으로 통합합니다.  
### Search Experiment Environment
Query Lab을 통해 검색 결과의 랭킹 과정을 분석하고 검색 모델 실험을 수행할 수 있습니다.  
### Search Operations Monitoring
Streamlit 기반 Quality Monitor Dashboard를 통해 검색 실험 결과와 운영 지표를 모니터링합니다.  

---

# 🚀 Search Quality Improvement
초기 이미지 검색은 **CLIP 단독 검색 구조**였습니다.
  
문제
- 유사 결과 반복 노출
- 검색 다양성 부족
  
개선 구조
```
CLIP Retrieval
+ SBERT Retrieval
→ Reciprocal Rank Fusion (RRF)
```
  
개선 효과
- 검색 결과 다양성 향상
- 의미 기반 유사 영화 탐색 가능
- 이미지 + 텍스트 결합 검색 구현
  
---
  
# 🔬 Technical Highlights

MovieFactory는 다음과 같은 검색 시스템 구조를 구현합니다.

**Hybrid Retrieval Pipeline**
TF-IDF, SBERT, CLIP 검색 결과를 결합  
**Reciprocal Rank Fusion (RRF)**
서로 다른 검색 엔진 결과를 안정적으로 통합  
**Candidate Pool Strategy**
CLIP / SBERT 후보 풀을 합집합으로 구성  
**Ranking Explainability**
Query Lab을 통한 랭킹 분석  
**Regression Guard**
검색 품질 회귀 자동 감지  

---
  
# ✨ Key Features
### Hybrid Retrieval Engine
여러 검색 엔진을 결합하여 검색 품질을 향상시킵니다.
지원 엔진  
- **TF-IDF** : 키워드 기반 검색
- **SBERT** : 의미 기반 임베딩 검색
- **CLIP** : 이미지 기반 유사 콘텐츠 검색
  
### Hybrid Ranking Fusion
여러 검색 결과를 결합하여 최종 랭킹을 생성합니다.
사용 방식
- Score Fusion
- Reciprocal Rank Fusion (RRF)
  
### Query Lab (Search Quality Analysis Tool)
검색 결과가 **왜 해당 순서로 랭킹되었는지 분석**할 수 있는 실험 환경입니다.
지원 기능
- Engine Retrieval 분석
- Candidate Pool 분석
- Hybrid Fusion 분석
- Engine Contribution 분석
- Ablation 실험  
  
### Quality Monitor (Ops Dashboard)
검색 실험 결과와 운영 데이터를 모니터링합니다.
지원 기능
- 검색 품질 트렌드 분석
- latency 모니터링
- 실험 run 기록
- KPI 분석  
  
### Reproducible Builder
프로젝트를 **한 번의 실행으로 재구성**할 수 있습니다.
```
python builder.py
```
Builder는 다음을 자동 구성합니다.
- 프로젝트 구조
- 데이터셋
- 캐시 환경
- 실행 스크립트
  
---
  
# 🧠 System Architecture
### Search Pipeline Summary
Text Query / Image Input  
TF-IDF / SBERT / CLIP Retrieval  
Candidate Pool Union  
Hybrid Ranking Fusion  
Final Search Results

<p align="center">
  <img src="docs/images/architecture.png" width="900">
</p>

MovieFactory는 **TF-IDF, SBERT, CLIP을 결합한 Hybrid Retrieval Engine**을 기반으로 검색 결과를 생성합니다.  
텍스트 검색에서는 TF-IDF와 SBERT 기반 검색 결과를 **Score Fusion 방식**으로 결합합니다.  
이미지 검색에서는 다음과 같은 파이프라인을 사용합니다.  
```
CLIP Embedding
→ Pseudo Query Generation
→ SBERT Semantic Retrieval
→ Candidate Pool Union
→ Reciprocal Rank Fusion (RRF)
→ Top-N Results
```
이 구조를 통해  
- 키워드 검색
- 의미 기반 검색
- 이미지 기반 검색
  
을 하나의 **통합 검색 파이프라인**으로 구성했습니다.  
또한 Query Lab과 Ops Dashboard를 통해 검색 품질을 **실험하고 모니터링할 수 있는 구조**를 구현했습니다.
  
---
  
# 🧠 Architecture Key Ideas
MovieFactory 검색 시스템 설계의 핵심 아이디어입니다.
  
### Hybrid Retrieval  
서로 다른 검색 모델을 결합하여 검색 품질을 향상  
TF-IDF / SBERT / CLIP

### Candidate Pool Strategy  
여러 검색 엔진 결과를 합집합으로 구성하여
검색 결과의 **다양성과 탐색 범위**를 확장

### Reciprocal Rank Fusion  
서로 다른 검색 결과를 안정적으로 통합

### Ranking Explainability  
Query Lab을 통해 검색 결과 생성 과정을 분석

### Search Experiment Platform  
검색 알고리즘 실험 환경 구축  

---
  
# 📱 Mobile UI
<p align="center">
  <img src="docs/images/mobile_demo.gif" width="420">
</p>

MovieFactory는 모바일 환경에서도 사용할 수 있도록 UI를 구성했습니다.  
모바일 주요 기능  
- 장르 기반 영화 탐색
- 텍스트 검색
- 포스터 기반 이미지 검색
- 영화 상세 페이지 탐색
  
---
  
# 🖥 Application Screens
## Home
<p align="center">
  <img src="docs/images/home.png" width="900">
</p>

- 최신 영화 목록
- 장르 기반 탐색
- 검색 진입 화면
  
---
  
## Text Search
<p align="center">
  <img src="docs/images/text.png" width="900">
</p>

텍스트 검색은 **TF-IDF + SBERT Hybrid Retrieval** 기반으로 동작합니다.
  
---
  
## Image Search
<p align="center">
  <img src="docs/images/image_search.png" width="900">
</p>
영화 포스터 이미지를 업로드하면 CLIP 기반 이미지 임베딩을 생성합니다.  
  
이 임베딩을 기반으로 **pseudo query**를 생성하고 SBERT 의미 검색을 수행하여 의미적으로 유사한 영화 후보를 찾습니다.  
최종적으로 CLIP 검색 결과와 SBERT 검색 결과를 **Reciprocal Rank Fusion (RRF)** 방식으로 결합하여 최종 랭킹을 생성합니다.  
  
---
  
# 🔬 Search Experiment Tools
## Query Lab (Search Quality Analysis Tool)
<p align="center">
  <img src="docs/images/query_lab.png" width="900">
</p>
검색 결과를 분석하는 실험 환경입니다.
  
---
  
## Quality Monitor (Search Ops Dashboard)
<p align="center">
  <img src="docs/images/quality_monitor.png" width="900">
</p>
검색 품질과 실험 결과를 모니터링합니다.
  
---
  
# 🧪 검색 실험 환경
MovieFactory는 검색 품질 개선을 위한 실험 환경을 제공합니다.
지원 기능
- query 기반 랭킹 분석
- 엔진별 성능 비교
- Ablation 실험
- latency 측정
- 실험 run 기록  
  
실험 결과는 **Quality Monitor Dashboard**에서 확인할 수 있습니다.
  
---
  
# 📊 Search Evaluation Result
검색 품질을 검증하기 위해 **Intent Query 기반 평가**를 수행했습니다.
평가 지표
- **Hit@1** : 정답 영화가 1위로 검색되는 비율
- **Hit@5** : 정답 영화가 상위 5위 안에 포함되는 비율
- **Hit@10** : 정답 영화가 상위 10위 안에 포함되는 비율
- **Mean Rank** : 정답 영화 평균 순위
예시 결과
```
Hit@1     : 0.90 → 1.00
Hit@5     : 1.00
Hit@10    : 1.00
Mean Rank : 1.30 → 1.00
```
Hybrid Retrieval 적용 이후 **검색 정확도와 랭킹 안정성이 개선**되었습니다.
  
---
  
# 🧪 Evaluation & Regression
검색 품질 회귀(regression)를 방지하기 위해 자동 평가 구조를 포함합니다.
```
python -m moviefactory.eval.run_text_eval
```
```
python -m moviefactory.eval.regression_check moviefactory/eval/text_queries_intent.yaml
```
CI에서도 동일 커맨드를 실행하여
**로컬 환경과 CI 환경 간 평가 결과 일관성**을 검증합니다.
  
---
  
# 🧱 기술 스택
Backend
- Python
- Flask
  
Retrieval
- TF-IDF
- SBERT
- CLIP
  
ML / Embedding
- SentenceTransformers
- OpenCLIP
  
Dashboard
- Streamlit
  
Data Processing
- Pandas
- NumPy
  
---
  
# 📅 Project Timeline
  
**2025.11 — 프로젝트 시작**  
- 영화 검색 실습 프로젝트 기반 개발 시작  
- TF-IDF 기반 텍스트 검색 구현  
  
**2025.12 — Hybrid Retrieval 확장**  
- SBERT 기반 의미 검색 추가  
- TF-IDF + SBERT Hybrid Retrieval 구현  
  
**2026.01 — Image Search 기능 확장**  
- CLIP 기반 이미지 임베딩 검색 구현  
- RRF 기반 Hybrid Ranking 적용  
  
**2026.02 — 검색 실험 플랫폼 구축**  
- Query Lab Dashboard 구현  
- Quality Monitor Dashboard 구현  
  
---
  
# 📚 What I Learned
MovieFactory 프로젝트를 통해 다음 경험을 얻었습니다.
- Hybrid Retrieval System 설계
- Search Ranking Explainability 분석
- Search Experiment Framework 구축
- Search Operations Monitoring 경험
  
---
  
# 🧯 Troubleshooting
### TF-IDF Dimension Mismatch
CSV 데이터와 TF-IDF 캐시 기준 불일치 문제  
해결 - canonical CSV 기준 유지

### Image Search Result Bias
CLIP 단독 검색 구조 문제  
해결 - CLIP + SBERT + RRF

### Image Session Persistence
이미지 검색 이후 텍스트 검색 시 세션 유지 문제  
해결 - image session reset
  
전체 문제 기록은 **docs/TROUBLESHOOTING.md** 문서를 참고하세요.  
  
---
  
# ⚙️ Installation
```
pip install -r requirements.txt
```
  
---
  
# 🚀 Run Application
```
python -m moviefactory.app.main
```
  
---
  
# 📂 프로젝트 구조
```
moviefactory/
app/
engine/
streamlit/
eval/
builder/
data/
```
  
---
  
# 📊 프로젝트 핵심 포인트
MovieFactory는 단순 영화 검색 서비스가 아니라  
**검색 품질을 분석하고 개선하기 위한 Search Experiment Platform**입니다.
이 프로젝트에서 구현한 핵심 시스템은 다음과 같습니다.

### Hybrid Retrieval System
TF-IDF, SBERT, CLIP 기반 검색 엔진을 결합하여  
텍스트 검색, 의미 검색, 이미지 검색을 하나의 통합 검색 시스템으로 구성했습니다.  
### Search Result Analysis
Query Lab을 통해 검색 결과의 랭킹 과정을 분석하고  
검색 엔진별 기여도와 후보 풀 구조를 확인할 수 있습니다.  
### Search Experiment Environment
검색 알고리즘 변경에 따른 랭킹 변화를 분석할 수 있도록  
검색 실험 환경과 평가 파이프라인을 구축했습니다.  
### Search Operations Monitoring
Quality Monitor Dashboard를 통해  
검색 실험 결과와 운영 지표를 모니터링할 수 있습니다.
  
---
  
# 🚧 Project Status
MovieFactory는 개인 연구 및 포트폴리오 목적으로 개발된 프로젝트입니다.
<p align="center">
  <a href="docs/MovieFactory_Search_Quality_Platform_Portfolio.pdf">
    📄 View Portfolio Presentation (PDF)
  </a>
</p>
  
---
  
# 👤 Author
진달래  
CX Tech
서비스 운영 개선
Experiment / Analysis Platform  
  
GitHub  
https://github.com/gauldal  
Email  
[gauldaldal@gmail.com](mailto:gauldaldal@gmail.com)
