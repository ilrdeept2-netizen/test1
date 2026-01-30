# -*- coding: utf-8 -*-
"""
AI 서비스 모듈 - OpenAI, Anthropic, Google AI API 연동
"""

import os
import json
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Generator
from dataclasses import dataclass

@dataclass
class AIResponse:
    """AI 응답 데이터 클래스"""
    content: str
    model: str
    tokens_used: int = 0
    finish_reason: str = ""
    raw_response: Any = None


class AIServiceBase(ABC):
    """AI 서비스 기본 클래스"""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> AIResponse:
        """텍스트 생성"""
        pass

    @abstractmethod
    def generate_stream(self, prompt: str, system_prompt: str = "", **kwargs) -> Generator[str, None, None]:
        """스트리밍 텍스트 생성"""
        pass


class OpenAIService(AIServiceBase):
    """OpenAI API 서비스"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = None

    def _get_client(self):
        if self.client is None:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("openai 패키지를 설치해주세요: pip install openai")
        return self.client

    def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> AIResponse:
        client = self._get_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=kwargs.get("model", self.model),
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 4096)
        )

        return AIResponse(
            content=response.choices[0].message.content,
            model=response.model,
            tokens_used=response.usage.total_tokens if response.usage else 0,
            finish_reason=response.choices[0].finish_reason,
            raw_response=response
        )

    def generate_stream(self, prompt: str, system_prompt: str = "", **kwargs) -> Generator[str, None, None]:
        client = self._get_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        stream = client.chat.completions.create(
            model=kwargs.get("model", self.model),
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 4096),
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class AnthropicService(AIServiceBase):
    """Anthropic Claude API 서비스"""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self.client = None

    def _get_client(self):
        if self.client is None:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("anthropic 패키지를 설치해주세요: pip install anthropic")
        return self.client

    def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> AIResponse:
        client = self._get_client()

        response = client.messages.create(
            model=kwargs.get("model", self.model),
            max_tokens=kwargs.get("max_tokens", 4096),
            system=system_prompt if system_prompt else "당신은 20년 경력의 베테랑 변리사입니다.",
            messages=[{"role": "user", "content": prompt}]
        )

        return AIResponse(
            content=response.content[0].text,
            model=response.model,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens if response.usage else 0,
            finish_reason=response.stop_reason,
            raw_response=response
        )

    def generate_stream(self, prompt: str, system_prompt: str = "", **kwargs) -> Generator[str, None, None]:
        client = self._get_client()

        with client.messages.stream(
            model=kwargs.get("model", self.model),
            max_tokens=kwargs.get("max_tokens", 4096),
            system=system_prompt if system_prompt else "당신은 20년 경력의 베테랑 변리사입니다.",
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            for text in stream.text_stream:
                yield text


class GoogleAIService(AIServiceBase):
    """Google Gemini API 서비스"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model = model
        self.client = None

    def _get_client(self):
        if self.client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai
            except ImportError:
                raise ImportError("google-generativeai 패키지를 설치해주세요: pip install google-generativeai")
        return self.client

    def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> AIResponse:
        client = self._get_client()

        model = client.GenerativeModel(kwargs.get("model", self.model))

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        response = model.generate_content(full_prompt)

        return AIResponse(
            content=response.text,
            model=self.model,
            tokens_used=0,
            finish_reason="stop",
            raw_response=response
        )

    def generate_stream(self, prompt: str, system_prompt: str = "", **kwargs) -> Generator[str, None, None]:
        client = self._get_client()

        model = client.GenerativeModel(kwargs.get("model", self.model))

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        response = model.generate_content(full_prompt, stream=True)

        for chunk in response:
            if chunk.text:
                yield chunk.text


class AIServiceManager:
    """AI 서비스 관리자 - 여러 AI 서비스를 통합 관리"""

    PROVIDERS = {
        "openai": OpenAIService,
        "anthropic": AnthropicService,
        "google": GoogleAIService
    }

    def __init__(self, default_provider: str = "openai"):
        self.services: Dict[str, AIServiceBase] = {}
        self.default_provider = default_provider

    def register_service(self, provider: str, api_key: Optional[str] = None, model: Optional[str] = None):
        """AI 서비스 등록"""
        if provider not in self.PROVIDERS:
            raise ValueError(f"지원하지 않는 제공자: {provider}. 지원: {list(self.PROVIDERS.keys())}")

        service_class = self.PROVIDERS[provider]
        kwargs = {}
        if api_key:
            kwargs["api_key"] = api_key
        if model:
            kwargs["model"] = model

        self.services[provider] = service_class(**kwargs)

    def get_service(self, provider: Optional[str] = None) -> AIServiceBase:
        """AI 서비스 가져오기"""
        provider = provider or self.default_provider

        if provider not in self.services:
            # 자동 등록 시도
            self.register_service(provider)

        return self.services[provider]

    def generate(self, prompt: str, provider: Optional[str] = None, **kwargs) -> AIResponse:
        """텍스트 생성"""
        service = self.get_service(provider)
        return service.generate(prompt, **kwargs)

    def generate_stream(self, prompt: str, provider: Optional[str] = None, **kwargs) -> Generator[str, None, None]:
        """스트리밍 텍스트 생성"""
        service = self.get_service(provider)
        return service.generate_stream(prompt, **kwargs)


# 특허 업무 특화 시스템 프롬프트
PATENT_SYSTEM_PROMPTS = {
    "default": """당신은 20년 경력의 베테랑 변리사입니다.
특허 명세서 작성에 전문성을 가지고 있으며, 다음 원칙을 따릅니다:
1. 번역 친화적 간결체로 작성
2. 접속사 삭제, 지시어 최소화, 단문 위주, 능동태 지향
3. 구체적이고 기술적인 묘사
4. 권리범위 확보를 위한 전략적 서술""",

    "specification": """당신은 특허 명세서 작성 전문가입니다.
【기술분야】, 【발명의 배경이 되는 기술】, 【해결하고자 하는 과제】, 【발명의 효과】, 【도면의 간단한 설명】 항목을 작성합니다.
배경기술은 최소한도로, 효과는 상세하게 작성하는 것이 원칙입니다.""",

    "claims": """당신은 특허 청구항 작성 전문가입니다.
독립항은 넓은 권리범위를, 종속항은 구체적 특징을 포함하도록 작성합니다.
청구항 간의 논리적 연결과 기재불비 방지에 주의합니다.""",

    "oa_response": """당신은 특허 심사 대응 전문가입니다.
심사관의 거절이유를 분석하고, 진보성을 인정받기 위한 보정서와 의견서를 작성합니다.
인용발명과의 차별점을 명확히 하고, 객관적 증거를 제시합니다.""",

    "drawing": """당신은 특허 도면 작성 전문가입니다.
도면 구성, 부호체계 정리, HTML 기반 도면 코드 생성을 담당합니다.
모든 구성요소에 부호를 부여하고, 명확한 선과 배치로 특허 도면 스타일을 유지합니다."""
}
