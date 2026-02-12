2026/02/09
# MovieFactory – Troubleshooting

## 문제 1. TF-IDF matmul dimension mismatch
- 원인:
  - CSV와 캐시 기준 불일치
- 해결:
  - poster 기준 CSV로 통일
  - npz + vectorizer 쌍만 사용

---

## 문제 2. SBERT IndexError
- 원인:
  - embeddings 길이와 movie_ids 길이 불일치
- 해결:
  - 엔진 초기화 시 min 길이로 강제 슬라이싱

---

## 문제 3. 이미지 검색 화면 고정
- 원인:
  - session에 image_search_path가 계속 유지됨
- 해결:
  - genre / text 진입 시 세션 강제 해제
  - reset 옵션 추가

---

## 문제 4. 포스터가 안 보임
- 원인:
  - tmdb_poster_url 비어 있음
- 해결:
  - poster_path 기반 URL 자동 생성

---

## 문제 5. 상세페이지 메타정보 누락
- 원인:
  - 검색 카드용 dict를 상세에도 사용
- 해결:
  - card / detail 분리
  - 상세 전용 row_to_detail 도입

# [TROUBLESHOOTING.md] 추가 (2026-02-09)

## 증상: 이미지 검색 결과가 “똑같이” 나오거나 품질이 변하지 않음
- 원인 후보:
  - 수정한 runtime_engine.py가 실제 실행 경로의 파일이 아닐 수 있음
  - 이미지 분기 로직이 CLIP 단독으로 남아있을 수 있음
- 확인:
  - 콘솔에 [IMG-HYBRID] 또는 [IMG-RRF] 로그가 찍히는지 확인

## 증상: 결과가 2234개 전부 나옴
- 원인:
  - “대상 전체 비교”와 “결과 전체 노출”을 혼동한 상태
- 해결:
  - 결과 컷 정책 적용 (MAX_RESULTS, MIN_RESULTS)
  - RRF 사용 시 점수 기반 컷(best*ratio) 금지 → 순위 기반 컷 사용

## 증상: 결과가 2개 등으로 너무 적게 나옴
- 원인:
  - RRF 점수 scale이 작아 best*ratio 컷을 적용하면 대부분 제거됨
- 해결:
  - RRF는 순위 기반 컷으로 변경
  - 약한 입력 판정은 clip_best(원점수)로 처리

## 증상: 특정 movie_id(예: 155)가 아예 결과에서 사라짐 (rank=None)
- 원인:
  - CLIP_RANK_POOL 제한으로 후보 풀에 포함되지 않음
    - 예: CLIP rank=1213인데 pool=600이면 제외
- 해결:
  - RRF 대상 pool을 (CLIP 상위 pool) ∪ (SBERT 상위 pool) 합집합으로 구성
  - 검수 중에는 필요 시 pool_ids.add(155) 같은 임시 안전장치로 확인 가능(검수 후 제거)

## 권장 디버그 로그(필수)
- pseudo_query / candidates / sbert_scores / clip_best / kept
- TARGET movie_id 랭크 및 TOP20 출력
  - 예: [IMG-RRF][TARGET] movie_id=155 rank=2
