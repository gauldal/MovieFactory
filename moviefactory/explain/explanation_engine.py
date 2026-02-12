# moviefactory/engine/explanation_engine.py
"""
MovieFactory v1.4
ExplanationEngine
- 추천 결과에 대한 사후 설명 전용
- score / rank / weight 접근 금지
- LLM 미설정 환경에서도 서버 기동 가능
- 실행 환경에 따라 LLM / Mock 자동 선택
"""

from pathlib import Path
from typing import Optional

from moviefactory.contracts.explanation_contract import ExplanationInput
from moviefactory.llm.llm_client import LLMClient


class ExplanationEngine:
    def __init__(
        self,
        prompt_path: Optional[Path] = None,
        llm_client=None,
    ):
        # ================================
        # Prompt Template Load
        # ================================
        if prompt_path is None:
            self.prompt_path = (
                Path(__file__).resolve()
                .parent.parent
                / "llm"
                / "prompts"
                / "recommendation_explain_prompt.txt"
            )
        else:
            self.prompt_path = prompt_path

        if not self.prompt_path.exists():
            raise FileNotFoundError(
                f"Explanation prompt not found: {self.prompt_path}"
            )

        self.prompt_template = self.prompt_path.read_text(encoding="utf-8")

        # ================================
        # LLM Client Initialization
        # ================================
        if llm_client is not None:
            self.llm_client = llm_client
        else:
            self.llm_client = self._init_llm_client()

    def _init_llm_client(self):

        # 실행 환경에 따라 LLM / Mock 자동 선택
        # - OPENAI_API_KEY 설정됨 -> LLMClient
        # - 미설정 / 오류 발생 → MockLLMClient

        try:
            return LLMClient()
        except RuntimeError:
            from moviefactory.llm.mock_llm import MockLLMClient

            return MockLLMClient()

    # ================================
    # Public API
    # ================================
    def explain_recommendation(
        self,
        explanation_input: ExplanationInput,
    ) -> str:
        prompt = self._build_prompt(explanation_input)
        return self.llm_client.generate_explanation(prompt)

    # ================================
    # Prompt Builder
    # ================================
    def _build_prompt(
        self,
        explanation_input: ExplanationInput,
    ) -> str:
        return self.prompt_template.format(
            query=explanation_input.query,
            title=explanation_input.title,
            genres=", ".join(explanation_input.genres),
            year=explanation_input.year or "알 수 없음",
            semantic_hint=self._semantic_hint(explanation_input),
            keyword_hint=self._keyword_hint(explanation_input),
            overall_hint=self._overall_hint(explanation_input),
        )

    # ================================
    # Hint Generators
    # ================================
    def _semantic_hint(self, explanation_input: ExplanationInput) -> str:
        return "검색 의도와 주제적으로 밀접한 연관성이 있습니다."

    def _keyword_hint(self, explanation_input: ExplanationInput) -> str:
        return "줄거리와 핵심 키워드가 사용자 관심사와 잘 부합합니다."

    def _overall_hint(self, explanation_input: ExplanationInput) -> str:
        return "여러 기준을 종합적으로 고려했을 때 적합하다고 판단되었습니다."


__all__ = ["ExplanationEngine"]
