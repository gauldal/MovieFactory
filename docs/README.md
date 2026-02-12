# 🎬 MovieFactory

> 단일 기준 데이터셋 기반, 재현 가능한 하이브리드 영화 검색 엔진

MovieFactory는 텍스트·이미지 임베딩을 결합한 하이브리드 검색 시스템이다.  
모든 검색 결과는 **단일 기준 데이터셋 + 캐시 구조**를 기반으로 생성되며,  
CLI·웹·CI 환경에서 동일한 평가 결과를 보장한다.

---

# 1. 프로젝트 목표

- 🎯 재현 가능한 검색 엔진 구축
- 🎯 단일 기준 데이터 기반 구조 설계
- 🎯 회귀 테스트 자동화 (Regression Check)
- 🎯 CI 환경에서 동일한 평가 결과 보장
- 🎯 실험 코드와 프로덕션 코드 분리

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

# 3. 기준 데이터

본 프로젝트는 아래 파일을 **유일한 기준 데이터**로 사용한다.

```
moviefactory/data/movie_clean_data_poster.csv
```

조건:
- 포스터 존재
- 이미지 임베딩 생성 성공
- 텍스트 정제 완료

---

# 4. 검색 구조

### 🔹 Text
- TF-IDF
- SBERT

### 🔹 Image
- CLIP

### 🔹 Hybrid
가중치 기반 점수 결합 방식

```
score = w1*sbert + w2*tfidf + w3*clip + w4*cf
```

---

# 5. 평가 시스템 (Evaluation)

## 기본 평가 실행

```
python -m moviefactory.eval.run_text_eval
```

## 특정 YAML 실행

```
python -m moviefactory.eval.run_text_eval moviefactory/eval/text_queries_intent.yaml
```

---

# 6. 회귀 테스트 (Regression Check)

### 🔹 최초 기준 업데이트

```
python -m moviefactory.eval.regression_check moviefactory/eval/text_queries_intent.yaml --update-baseline
```

### 🔹 일반 회귀 검사

```
python -m moviefactory.eval.regression_check moviefactory/eval/text_queries_intent.yaml
```

또는

```
check_regression.bat
```

성공 시:

```
✅ PASS (no regression)
```

---

# 7. CI 자동 실행

GitHub Actions에서:

- main push 시 자동 실행
- 회귀 발생 시 실패 처리

Workflow 위치:

```
.github/workflows/regression.yml
```

---

# 8. 개발 철학

- 단일 소스 데이터
- 캐시 기반 재현성
- 평가 우선 설계
- CLI와 CI 동일 동작
- 결과 수치 기반 개선

---

# 9. 현재 기준 성능 (Intent Eval)

| Metric   | Score |
|----------|-------|
| hit@1    | 0.900 |
| hit@5    | 1.000 |
| hit@10   | 1.000 |
| mean_rank| 1.30  |

---

# 10. 라이선스

Private Project
