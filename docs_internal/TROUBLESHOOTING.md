# MovieFactory – Troubleshooting Guide

이 문서는 개발 과정에서 발생한 주요 문제와 해결 방법을 기록한다.

---

# Issue 1 – TF-IDF dimension mismatch

증상

```
matmul dimension mismatch
```

원인

* CSV와 TF-IDF 캐시 기준 불일치

해결

* poster 기반 canonical CSV 사용
* vectorizer / matrix 쌍 유지

---

# Issue 2 – SBERT IndexError

증상

```
IndexError
```

원인

* embeddings 길이와 movie_ids 길이 불일치

해결

```
min length 기준 슬라이싱
```

---

# Issue 3 – 이미지 검색 결과 고정

증상

* 동일 결과 반복 노출

원인

* CLIP 단독 검색 구조

해결

```
CLIP + SBERT RRF Fusion
```

---

# Issue 4 – 이미지 검색 세션 유지 문제

증상

텍스트 검색 시 이전 이미지가 계속 적용

원인

session 상태 유지

해결

```
텍스트 / 장르 검색 시
image session reset
```

---

# Issue 5 – 포스터 미표시

원인

```
tmdb_poster_url 없음
```

해결

```
poster_path 기반 URL 생성
```

---

# Issue 6 – 상세 페이지 정보 부족

원인

검색 카드 데이터 재사용

해결

```
row_to_detail 구조 분리
```

---

# Debug Recommendation

이미지 검색 디버그 시 다음 로그 확인

```
pseudo_query
clip_best
candidate_pool
fused_rank
target_movie_rank
```

예시 로그

```
[IMG-RRF] movie_id=155 rank=2
```

이를 통해 검색 품질을 확인할 수 있다.
