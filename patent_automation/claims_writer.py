# -*- coding: utf-8 -*-
"""
특허 청구항 작성 모듈
"""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
import json
import re

from .prompts import PatentPrompts
from .ai_service import AIServiceManager, PATENT_SYSTEM_PROMPTS, AIResponse


@dataclass
class Claim:
    """청구항 데이터 클래스"""
    number: int
    text: str
    is_independent: bool = True
    depends_on: Optional[int] = None
    features: List[str] = field(default_factory=list)
    version: int = 1


@dataclass
class ClaimsSet:
    """청구항 세트 데이터 클래스"""
    claims: List[Claim] = field(default_factory=list)

    def get_independent_claims(self) -> List[Claim]:
        """독립항 목록 반환"""
        return [c for c in self.claims if c.is_independent]

    def get_dependent_claims(self, independent_claim_number: int) -> List[Claim]:
        """특정 독립항의 종속항 목록 반환"""
        return [c for c in self.claims if c.depends_on == independent_claim_number]

    def to_formatted_text(self) -> str:
        """포맷된 텍스트로 변환"""
        output = ["【청구범위】"]
        for claim in sorted(self.claims, key=lambda x: x.number):
            output.append(f"\n【청구항 {claim.number}】")
            output.append(claim.text)
        return "\n".join(output)


class ClaimsWriter:
    """청구항 작성 클래스"""

    def __init__(self, ai_manager: Optional[AIServiceManager] = None):
        self.ai_manager = ai_manager or AIServiceManager()
        self.claims_set = ClaimsSet()
        self.invention_features: List[str] = []

    def set_invention_features(self, features: List[str]):
        """발명 특징 설정"""
        self.invention_features = features

    def analyze_invention_features(self, specification: str, provider: str = None) -> AIResponse:
        """명세서에서 발명 특징 추출"""
        prompt = f"""
다음 특허 명세서에서 본 발명의 핵심 특징들을 추출해주세요.

[명세서]
{specification}

추출 지침:
1. 기술적 특징을 구체적으로 나열
2. 각 특징이 청구항에 포함될 수 있는 형태로 정리
3. 핵심 특징과 부가 특징 구분
4. 특징별 기술적 효과 연결

출력 형식:
[핵심 특징 1]: 설명 - 효과
[핵심 특징 2]: 설명 - 효과
...
[부가 특징 1]: 설명 - 효과
...
"""

        response = self.ai_manager.generate(
            prompt,
            provider=provider,
            system_prompt=PATENT_SYSTEM_PROMPTS["claims"],
            max_tokens=2048
        )

        return response

    def write_independent_claim(self, specification: str, symbol_system: Dict[str, str] = None,
                                provider: str = None) -> AIResponse:
        """독립항(청구항 1항) 작성"""
        symbol_info = ""
        if symbol_system:
            symbol_info = "\n[부호체계]\n" + "\n".join([f"{k}: {v}" for k, v in symbol_system.items()])

        prompt = f"""
{PatentPrompts.CLAIMS_WRITING}

[명세서]
{specification}

{symbol_info}

독립항(청구항 1항) 작성 지침:
1. 상당히 넓은 권리범위를 가지도록 작성
2. 필수 구성요소만 포함
3. 명확하고 간결한 표현
4. 기재불비 방지를 위해 명세서 용어와 일치

청구항 1항만 작성해주세요.
"""

        response = self.ai_manager.generate(
            prompt,
            provider=provider,
            system_prompt=PATENT_SYSTEM_PROMPTS["claims"],
            max_tokens=1024
        )

        # 청구항 파싱 및 저장
        claim_text = self._extract_claim_text(response.content)
        if claim_text:
            self.claims_set.claims.append(Claim(
                number=1,
                text=claim_text,
                is_independent=True
            ))

        return response

    def write_dependent_claims(self, specification: str, independent_claim: str,
                               features_count: int = 5, provider: str = None) -> AIResponse:
        """종속항 작성"""
        features_info = ""
        if self.invention_features:
            features_info = "\n[발명 특징]\n" + "\n".join([f"- {f}" for f in self.invention_features])

        prompt = f"""
{PatentPrompts.CLAIMS_WRITING}

[명세서]
{specification}

[청구항 1항 (독립항)]
{independent_claim}

{features_info}

종속항 작성 지침:
1. 청구항 1항에 대한 종속항으로 작성
2. 각 종속항은 본 발명기술의 특징 1개를 구체적으로 포함
3. 약 {features_count}개의 종속항 작성
4. 각 종속항은 "제1항에 있어서," 로 시작

청구항 2항부터 작성해주세요.
"""

        response = self.ai_manager.generate(
            prompt,
            provider=provider,
            system_prompt=PATENT_SYSTEM_PROMPTS["claims"],
            max_tokens=2048
        )

        # 종속항 파싱 및 저장
        self._parse_dependent_claims(response.content)

        return response

    def write_all_claims(self, specification: str, symbol_system: Dict[str, str] = None,
                        provider: str = None) -> AIResponse:
        """전체 청구항 작성"""
        symbol_info = ""
        if symbol_system:
            symbol_info = "\n[부호체계]\n" + "\n".join([f"{k}: {v}" for k, v in symbol_system.items()])

        prompt = f"""
{PatentPrompts.CLAIMS_WRITING}

[명세서]
{specification}

{symbol_info}

작성 지침:
1. 독립항은 1항만으로, 상당히 넓은 권리범위를 가지도록 작성
2. 나머지는 1항의 종속항으로 작성
3. 각 종속항은 본 발명기술의 특징 1개를 구체적으로 포함
4. 명세서에 기재된 모든 중요 특징이 청구항에 반영되도록 작성

전체 청구항을 작성해주세요.
"""

        response = self.ai_manager.generate(
            prompt,
            provider=provider,
            system_prompt=PATENT_SYSTEM_PROMPTS["claims"],
            max_tokens=4096
        )

        # 청구항 파싱
        self._parse_all_claims(response.content)

        return response

    def review_claims(self, specification: str, provider: str = None) -> AIResponse:
        """청구항 검토"""
        current_claims = self.claims_set.to_formatted_text()

        prompt = f"""
{PatentPrompts.CLAIMS_REVIEW}

[현재 청구항]
{current_claims}

[명세서]
{specification}

검토 지침:
1. 빠진 본 발명기술의 특징이 있는지 확인
2. 각 청구항의 명확성 검토
3. 청구항 간 종속관계 적절성 검토
4. 권리범위 적절성 검토

검토 결과와 함께 추가할 종속항이 있으면 작성해주세요.
"""

        response = self.ai_manager.generate(
            prompt,
            provider=provider,
            system_prompt=PATENT_SYSTEM_PROMPTS["claims"],
            max_tokens=2048
        )

        return response

    def align_with_specification(self, specification: str, provider: str = None) -> AIResponse:
        """청구항과 명세서 정합성 확인"""
        current_claims = self.claims_set.to_formatted_text()

        prompt = f"""
{PatentPrompts.CLAIMS_SPECIFICATION_ALIGNMENT}

[확정 청구항]
{current_claims}

[명세서]
{specification}

검토 요청:
1. 청구항 내용 중 상세한 설명에 추가하거나 보완할 내용 확인
2. 청구항에 기재된 구성요소가 명세서에 충분히 설명되어 있는지 확인
3. 필요한 보완 단락 작성
"""

        response = self.ai_manager.generate(
            prompt,
            provider=provider,
            system_prompt=PATENT_SYSTEM_PROMPTS["claims"],
            max_tokens=2048
        )

        return response

    def _extract_claim_text(self, content: str) -> str:
        """응답에서 청구항 텍스트 추출"""
        # 【청구항 X】 패턴 이후 텍스트 추출
        match = re.search(r'【청구항\s*\d+】\s*\n?([\s\S]*?)(?=【|$)', content)
        if match:
            return match.group(1).strip()

        # 번호 없이 청구항 내용만 있는 경우
        lines = content.strip().split('\n')
        claim_lines = []
        in_claim = False

        for line in lines:
            if '청구항' in line and '【' in line:
                in_claim = True
                continue
            if in_claim and line.strip():
                if line.startswith('【'):
                    break
                claim_lines.append(line)

        if claim_lines:
            return '\n'.join(claim_lines)

        return content.strip()

    def _parse_dependent_claims(self, content: str):
        """종속항 파싱"""
        # 【청구항 X】 패턴으로 분리
        pattern = r'【청구항\s*(\d+)】\s*\n?([\s\S]*?)(?=【청구항|$)'
        matches = re.findall(pattern, content)

        for match in matches:
            claim_number = int(match[0])
            claim_text = match[1].strip()

            if claim_number > 1:  # 종속항만
                depends_on = 1  # 기본적으로 1항에 종속

                # "제X항에 있어서" 패턴에서 종속 관계 파악
                dep_match = re.search(r'제(\d+)항에\s*있어서', claim_text)
                if dep_match:
                    depends_on = int(dep_match.group(1))

                self.claims_set.claims.append(Claim(
                    number=claim_number,
                    text=claim_text,
                    is_independent=False,
                    depends_on=depends_on
                ))

    def _parse_all_claims(self, content: str):
        """전체 청구항 파싱"""
        self.claims_set.claims = []

        # 【청구항 X】 패턴으로 분리
        pattern = r'【청구항\s*(\d+)】\s*\n?([\s\S]*?)(?=【청구항|$)'
        matches = re.findall(pattern, content)

        for match in matches:
            claim_number = int(match[0])
            claim_text = match[1].strip()

            is_independent = claim_number == 1
            depends_on = None

            if not is_independent:
                dep_match = re.search(r'제(\d+)항에\s*있어서', claim_text)
                if dep_match:
                    depends_on = int(dep_match.group(1))
                else:
                    depends_on = 1

            self.claims_set.claims.append(Claim(
                number=claim_number,
                text=claim_text,
                is_independent=is_independent,
                depends_on=depends_on
            ))

    def add_claim(self, text: str, is_independent: bool = False, depends_on: int = 1):
        """청구항 수동 추가"""
        next_number = max([c.number for c in self.claims_set.claims], default=0) + 1

        self.claims_set.claims.append(Claim(
            number=next_number,
            text=text,
            is_independent=is_independent,
            depends_on=None if is_independent else depends_on
        ))

    def update_claim(self, claim_number: int, new_text: str):
        """청구항 업데이트"""
        for claim in self.claims_set.claims:
            if claim.number == claim_number:
                claim.text = new_text
                claim.version += 1
                return True
        return False

    def delete_claim(self, claim_number: int) -> bool:
        """청구항 삭제 (번호는 유지)"""
        self.claims_set.claims = [c for c in self.claims_set.claims
                                   if c.number != claim_number]
        return True

    def get_claims(self) -> ClaimsSet:
        """청구항 세트 반환"""
        return self.claims_set

    def export_to_text(self) -> str:
        """텍스트로 내보내기"""
        return self.claims_set.to_formatted_text()

    def export_to_json(self) -> str:
        """JSON으로 내보내기"""
        return json.dumps({
            "claims": [
                {
                    "number": c.number,
                    "text": c.text,
                    "is_independent": c.is_independent,
                    "depends_on": c.depends_on,
                    "version": c.version
                }
                for c in self.claims_set.claims
            ]
        }, ensure_ascii=False, indent=2)
