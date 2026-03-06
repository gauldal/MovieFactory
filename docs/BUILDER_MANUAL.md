# Builder Manual

MovieFactory Builder는 프로젝트의 모든 산출물을
**단일 원본 데이터로부터 재현 가능하게 생성하는 파이프라인**입니다.

Builder는 데이터 정제, 임베딩 생성, 캐시 생성까지 수행하여
검색 시스템 실행에 필요한 모든 리소스를 준비합니다.

---

# 1. 목적

Builder의 목적은 다음과 같습니다.

* 검색 시스템의 **재현성 보장**
* 단일 기준 데이터셋 생성
* 검색 엔진 캐시 사전 생성
* Runtime 성능 최적화

즉 Builder는

```
데이터 준비 → 검색 환경 구축 → 실험 가능 상태 생성
```

까지 담당합니다.

---

# 2. 입력 데이터

Builder는 다음 원본 데이터를 사용합니다.

```
movies_metadata_20000.csv
```

이 데이터는 영화 메타데이터를 포함하며 다음 정보를 포함합니다.

* 영화 제목
* 장르
* 설명
* 평점
* 투표 수
* 포스터 정보

---

# 3. 출력 산출물

Builder 실행 후 다음 산출물이 생성됩니다.

```
movie_clean_data_poster.csv
TF-IDF cache
SBERT embeddings
CLIP embeddings
Engine runtime cache
```

각 산출물의 역할

### Canonical Dataset

```
movie_clean_data_poster.csv
```

검색 시스템의 기준 데이터셋입니다.

조건

* 포스터 존재 영화만 포함
* 정제된 텍스트 사용

---

### TF-IDF Cache

키워드 검색을 위한 벡터화 결과를 저장합니다.

---

### SBERT Embeddings

영화 설명 텍스트를 임베딩 벡터로 변환한 결과입니다.

---

### CLIP Embeddings

영화 포스터 이미지 기반 검색을 위한 벡터입니다.

---

### Runtime Engine Cache

Runtime 검색 속도를 높이기 위한 사전 계산 결과입니다.

---

# 4. 실행 흐름

Builder는 다음 순서로 실행됩니다.

```
1. 원본 데이터 로드
2. 데이터 전처리
3. 포스터 존재 영화 필터링
4. 텍스트 정제
5. SBERT 임베딩 생성
6. CLIP 임베딩 생성
7. TF-IDF 캐시 생성
8. Runtime 캐시 생성
9. 검증 후 종료
```

---

# 5. 실패 조건

Builder는 다음 상황에서 실행을 중단합니다.

* Canonical Dataset 생성 실패
* 캐시 생성 누락
* 임베딩 차원 불일치
* 필수 데이터 누락

이러한 검증을 통해 Runtime 오류를 방지합니다.

---

# 6. 재현성 보장 조건

MovieFactory는 다음 조건을 통해 재현성을 보장합니다.

* 동일 입력 데이터 → 동일 결과
* 랜덤 시드 고정
* Canonical Dataset 기준 실행
* 캐시 overwrite 시 전체 재생성

이 구조를 통해

```
Builder 실행 → 동일 검색 환경 재구성
```

이 가능합니다.
