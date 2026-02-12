2026/02/09

MovieFactory – Development History

Phase 1. 초기 설계

* FAST / FULL 분리 구조 도입
* 텍스트 기반 검색 중심 설계

Phase 2. 하이브리드 엔진 도입

* TF-IDF + SBERT 결합
* Hybrid Re-rank 구조 구현

Phase 3. 이미지 검색 추가

* CLIP 기반 포스터 검색 도입
* 포스터 보유 영화 기준 재설계

Phase 4. 구조 단순화

* FAST / FULL 폐기
* poster 기준 단일 CSV 정책 확정

Phase 5. 런타임 안정화

* 캐시 길이 불일치 문제 해결
* 엔진 내부 예외 방어 로직 추가

Phase 6. UX 안정화

* 이미지 검색 세션 고정 문제 해결
* 장르 / 텍스트 우선순위 정립

Phase 7. 최종 정리 단계

* runtime\_engine 최종본 확정
* 문서 구조 전면 재작성

\# \[HISTORY.md] 추가 (2026-02-09)



\## 이미지 검색 품질 개선 작업 (Image Search v3)

\- 현상:

&nbsp; - CLIP 단독 기반 이미지 검색에서 특정 영화(예: Don Juan DeMarco)가 반복적으로 상위권에 고정되고,

&nbsp;   업로드한 포스터(다크나이트)가 상위에 노출되지 않거나 매우 낮은 순위로 나오는 문제가 발생.

&nbsp; - 디버그 결과: movie\_id=155(The Dark Knight)가 CLIP 전체 2234 기준 약 1213위로 확인됨.



\- 조치/개선:

&nbsp; 1) CLIP 결과 + SBERT 의미 결과를 “가중합” 대신 “RRF(순위 결합)”으로 변경

&nbsp;    - 목적: CLIP outlier의 상위 고정을 완화하고 SBERT의 의미 신호를 상위에 반영.

&nbsp; 2) RRF는 점수 절대값이 작아 “best\*ratio” 컷을 적용하면 결과가 과도하게 줄어드는 문제 확인

&nbsp;    - 해결: RRF 결과 컷은 “순위 기반”으로 전환 (MAX\_RESULTS/ MIN\_RESULTS)

&nbsp; 3) CLIP 상위 pool만 사용할 경우(예: 600) CLIP 중위권 영화(155)가 후보에서 제외되어 사라지는 문제 확인

&nbsp;    - 해결: RRF 대상 풀을 (CLIP 상위 pool) ∪ (SBERT 상위 pool) 합집합으로 구성



\- 결과(검증 로그):

&nbsp; - pseudo\_query: "batman vigilante superhero dark city crime"

&nbsp; - clip\_best=0.9731, kept=600

&nbsp; - movie\_id=155 최종 fused rank=2로 상위권 복귀



