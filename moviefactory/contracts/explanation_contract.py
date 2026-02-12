# moviefactory/contracts/explanation_contract.py
"""
MovieFactory v1.4
LLM 추천 설명 입력 계약 (Explanation Contract)

본 파일은 v1.4 설명 계층에서 사용하는
'설명 입력 데이터의 표준 스키마'만을 정의한다.

⚠️ 주의
- 추천 로직, 점수 계산, 랭킹 변경 없음
- 데이터 구조 정의 전용
- v1.3 추천 결과를 그대로 설명 계층에 전달하기 위한 계약
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ExplanationInput:
    """
    LLM 설명 API에 전달되는 단일 추천 아이템 기준 입력 계약

    이 객체는 '왜 이 영화가 추천되었는가'를
    자연어로 설명하기 위한 최소 정보만 포함한다.
    """

    # 사용자 입력
    query: str

    # 추천된 영화 기본 정보
    movie_id: int
    title: str
    genres: List[str]
    year: Optional[int]

    # 엔진 기여 정보 (정규화된 비율)
    engine_contribution: Dict[str, float]
    # 예시: {"tfidf": 0.58, "sbert": 0.42}

    # 유사도/신호 정보 (설명 참고용)
    similarity_signals: Dict[str, float]
    # 예시: {"sbert_similarity": 0.82, "tfidf_similarity": 0.64}

    # 랭커 점수 (직접 노출 금지, 내부 참고용)
    ranker_score: Optional[float] = None


__all__ = ["ExplanationInput"]
