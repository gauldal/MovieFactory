# Builder Manual

## 목적

MovieFactory의 모든 산출물을
단일 원본 데이터로부터 재현 가능하게 생성한다.

---

## 입력

- movies_metadata_20000.csv

---

## 출력

- movie_clean_data_poster.csv
- TF-IDF cache
- SBERT embeddings
- CLIP embeddings
- Engine runtime cache

---

## 실행 흐름

1. 원본 로드
2. 전처리
3. 포스터 필터링
4. 텍스트 정제
5. 임베딩 생성
6. 캐시 저장
7. 검증 후 종료

---

## 실패 조건

- 기준 데이터 미생성
- 캐시 누락
- 임베딩 차원 불일치

---

## 재현성 보장 조건

- 동일 입력 → 동일 결과
- 랜덤 시드 고정
- 캐시 overwrite 시 전체 재생성