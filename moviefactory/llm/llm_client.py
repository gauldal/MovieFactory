# moviefactory/llm/llm_client.py
"""
MovieFactory v1.4
LLM Client Wrapper

본 파일은 외부 LLM 호출을 단일 인터페이스로 캡슐화한다.

설계 원칙
- 추천 로직과 완전 분리
- Explanation Engine에서만 사용
- LLM 교체(OpenAI / Local / Mock) 가능하도록 추상화
- 실패 시 시스템 중단 방지
"""

import os
import time
from typing import Optional


class LLMClient:
    """
    LLM 호출 전용 클라이언트 래퍼
    """

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        timeout: int = 20,
    ):
        self.provider = provider
        self.model = model
        self.timeout = timeout

        # 환경 변수 기반 키 관리
        self.api_key = os.getenv("OPENAI_API_KEY")

        if self.provider == "openai" and not self.api_key:
            raise RuntimeError(
                "OPENAI_API_KEY 환경 변수가 설정되지 않았습니다."
            )

    def generate_explanation(self, prompt: str) -> str:
        """
        프롬프트를 받아 자연어 설명을 생성한다.

        실패 시 예외를 던지지 않고 안전한 기본 메시지를 반환한다.
        """
        try:
            if self.provider == "openai":
                return self._call_openai(prompt)

            # 향후 로컬 LLM / 다른 Provider 확장 지점
            return self._fallback_response()

        except Exception as e:
            return self._safe_fallback(str(e))

    # ─────────────────────────────────────
    # Provider Implementations
    # ─────────────────────────────────────

    def _call_openai(self, prompt: str) -> str:
        """
        OpenAI API 호출 (Chat Completion 기반)
        """
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)

        start_time = time.time()

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful recommendation explanation assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
            max_tokens=200,
        )

        elapsed = time.time() - start_time
        if elapsed > self.timeout:
            raise TimeoutError("LLM 응답 시간이 제한을 초과했습니다.")

        return response.choices[0].message.content.strip()

    # ─────────────────────────────────────
    # Fallback Handling
    # ─────────────────────────────────────

    def _fallback_response(self) -> str:
        """
        Provider 미지원 시 기본 응답
        """
        return (
            "This movie was included in the recommendations"
            "because it closely matches your search intent and thematic interests."
        )

    def _safe_fallback(self, error_message: Optional[str] = None) -> str:
        """
        LLM 실패 시 시스템 안정성을 위한 안전한 기본 설명
        """
        return (
            "This movie was recommended due to its relevant themes and"
            "genre characteristics that align with your search intent."
        )


__all__ = ["LLMClient"]
