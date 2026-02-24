# 🎬 MovieFactory

> Reproducible Hybrid Movie Search Engine with Offline A/B Experiment Framework

MovieFactory는 단일 기준 데이터 기반으로 설계된  
텍스트·이미지 하이브리드 검색 시스템이며,  
재현 가능한 평가 및 Offline A/B 실험 구조를 포함한다.

---

# 1. 프로젝트 목표

- 🎯 단일 기준 데이터 기반 검색 엔진 설계
- 🎯 Hybrid Ranker 품질을 정량적으로 검증
- 🎯 CLI / Web / CI 동일 결과 보장
- 🎯 회귀 테스트 자동화
- 🎯 실험 코드와 서비스 코드 분리

---

# 2. 시스템 구조

```
movie_factory_project/
│
├─ moviefactory/
│   ├─ engine/           # 검색 엔진 코어
│   ├─ app/              # Flask 웹 서버
│   ├─ eval/             # 평가 및 회귀 테스트
│   ├─ data/             # 기준 데이터셋
│   └─ .cache/           # 임베딩 캐시
│
├─ check_regression.bat  # 원클릭 회귀 체크
└─ .github/workflows/    # CI 자동 실행
```

---

# 3. 검색 엔진 구성

### Text
- TF-IDF
- SBERT

### Image
- CLIP

### Hybrid Score
score = w1sbert + w2tfidf + w3clip + w4cf


---

# 4. Offline A/B Experiment

Hybrid Ranker가 실제 추천 품질을 개선하는지 검증하기 위해  
Offline Proxy Metric 기반 실험을 설계하였다.

## A/B 설정

| Mode | Description |
|------|-------------|
| OFF  | TF-IDF only |
| ON   | Hybrid Rerank |

- n_sessions = 120
- top_k = 20
- candidate_k = 700

## Proxy Metrics

1. Genre Coherence@K
2. Intra-list Genre Diversity@K
3. Popularity(log1p)@K
4. VoteCount(log1p)@K
5. Weighted Rating@K

## 결과 요약

- Δ avg: +0.42
- Popularity ↑
- VoteCount ↑
- Coherence ↓ (trade-off)

---

# 5. Evaluation & Regression

### 기본 평가

```
python -m moviefactory.eval.run_text_eval

```

### 회귀 검사

```
python -m moviefactory.eval.regression_check moviefactory/eval/text_queries_intent.yaml

```

CI에서도 동일 커맨드 실행.

---

# 6. 설계 원칙

- 단일 기준 데이터
- 캐시 기반 재현성
- Runtime은 캐시만 사용
- 평가 수치 기반 개선
- 실험과 서비스 구조 분리

---

# 7. 현재 기준 성능 (Intent Eval)

| Metric    | Score |
|-----------|-------|
| hit@1     | 0.900 |
| hit@5     | 1.000 |
| hit@10    | 1.000 |
| mean_rank | 1.30  |

---

# 8. 프로젝트 의의

MovieFactory는 단순 검색 구현이 아니라,

- 재현 가능한 검색 시스템 설계
- Offline 실험 구조 설계
- 회귀 테스트 자동화
- Hybrid 품질 검증 체계

를 포함한 구조 중심 프로젝트이다.