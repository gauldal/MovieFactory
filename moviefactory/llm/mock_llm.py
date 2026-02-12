# moviefactory/llm/mock_llm.py
"""
MovieFactory v1.4
Mock / Fallback LLM Module

본 파일은 LLM 미연결 상황에서도
시스템 전체가 안정적으로 동작하도록 하기 위한
Mock 및 Fallback 전용 모듈이다.

사용 목적
- 개발 환경에서 API Key 없이 실행
- 네트워크 장애 / LLM 실패 대비
- 발표, 데모, 테스트 시 안정성 확보

설계 원칙
- 실제 LLM 호출 없음
- 항상 동일하거나 규칙 기반의 설명 반환
- Explanation Engine / LLMClient 어디서든 대체 가능
"""

from typing import Optional


class MockLLMClient:
    """
    LLMClient 대체용 Mock 클래스
    """

    def __init__(self):
        self.provider = "mock"
        self.model = "mock-static"

    def generate_explanation(self, prompt: str) -> str:
        """
        프롬프트를 받아 고정된 설명을 반환한다.

        프롬프트 내용은 사용하지 않으며,
        설명 품질이 아닌 '흐름 검증'이 목적이다.
        """
        return (
            "이 영화는 사용자의 검색 의도와 주제적으로 잘 맞는 요소를 가지고 있으며, "
            "장르와 이야기 전개 측면에서도 유사한 특징을 보여 추천되었습니다."
        )


class FallbackLLMClient:
    """
    예외 상황 전용 Fallback 설명 생성기

    LLM 호출 중 예외가 발생했을 때
    시스템이 중단되지 않도록 안전한 설명을 제공한다.
    """

    def __init__(self, reason: Optional[str] = None):
        self.reason = reason

    def generate_explanation(self, prompt: str) -> str:
        """
        항상 안전한 기본 설명을 반환한다.
        """
        return (
            "이 추천은 사용자의 관심 주제와 영화의 주요 특징을 종합적으로 고려하여 "
            "선택된 결과입니다."
        )


__all__ = [
    "MockLLMClient",
    "FallbackLLMClient",
]
