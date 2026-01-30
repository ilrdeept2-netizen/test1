# -*- coding: utf-8 -*-
"""
OA(의견제출통지서) 대응 모듈
"""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
import json
from enum import Enum

from .prompts import PatentPrompts
from .ai_service import AIServiceManager, PATENT_SYSTEM_PROMPTS, AIResponse


class RejectionType(Enum):
    """거절이유 유형"""
    NOVELTY = "신규성"
    INVENTIVE_STEP = "진보성"
    ENABLEMENT = "기재불비"
    CLARITY = "명확성"
    SUPPORT = "서포트 요건"
    INDUSTRIAL_APPLICABILITY = "산업상 이용가능성"
    OTHER = "기타"


@dataclass
class CitedReference:
    """인용문헌 데이터 클래스"""
    reference_number: int  # 인용문헌 번호 (1, 2, 3...)
    publication_number: str = ""  # 공개번호/등록번호
    title: str = ""
    abstract: str = ""
    key_features: List[str] = field(default_factory=list)
    relevant_claims: List[int] = field(default_factory=list)


@dataclass
class RejectionReason:
    """거절이유 데이터 클래스"""
    rejection_type: RejectionType
    description: str
    affected_claims: List[int] = field(default_factory=list)
    cited_references: List[int] = field(default_factory=list)


@dataclass
class AmendedClaim:
    """보정된 청구항 데이터 클래스"""
    claim_number: int
    original_text: str
    amended_text: str
    amendment_basis: str = ""  # 보정 근거
    changes_description: str = ""  # 변경 사항 설명


@dataclass
class OAResponseDocument:
    """OA 대응 문서 데이터 클래스"""
    original_claims: List[str] = field(default_factory=list)
    cited_references: List[CitedReference] = field(default_factory=list)
    rejection_reasons: List[RejectionReason] = field(default_factory=list)
    amended_claims: List[AmendedClaim] = field(default_factory=list)
    opinion_statement: str = ""
    additional_arguments: List[str] = field(default_factory=list)


class OAResponseHandler:
    """OA 대응 처리 클래스"""

    def __init__(self, ai_manager: Optional[AIServiceManager] = None):
        self.ai_manager = ai_manager or AIServiceManager()
        self.oa_document = OAResponseDocument()

    def set_original_claims(self, claims: List[str]):
        """원 청구항 설정"""
        self.oa_document.original_claims = claims

    def add_cited_reference(self, reference: CitedReference):
        """인용문헌 추가"""
        self.oa_document.cited_references.append(reference)

    def add_rejection_reason(self, reason: RejectionReason):
        """거절이유 추가"""
        self.oa_document.rejection_reasons.append(reason)

    def analyze_rejection(self, rejection_notice: str, specification: str,
                         cited_docs: List[str], provider: str = None) -> AIResponse:
        """거절이유 분석"""
        cited_docs_text = "\n\n---\n\n".join([f"[인용문헌 {i+1}]\n{doc}"
                                              for i, doc in enumerate(cited_docs)])

        prompt = f"""
첨부된 것은 본 발명의 출원명세서와, 그에 대한 특허청의 의견제출통지서 및 인용문헌들입니다.

[출원명세서]
{specification}

[의견제출통지서]
{rejection_notice}

[인용문헌들]
{cited_docs_text}

먼저 심사관의 거절이유에 대한 정당성을 검토해주세요.

분석 요청:
1. 거절이유의 유형 파악 (신규성, 진보성, 기재불비 등)
2. 각 거절이유가 어떤 청구항에 해당하는지 정리
3. 인용문헌별 핵심 특징 파악
4. 거절이유의 정당성 평가
5. 극복 가능성 및 전략 제안
"""

        response = self.ai_manager.generate(
            prompt,
            provider=provider,
            system_prompt=PATENT_SYSTEM_PROMPTS["oa_response"],
            max_tokens=4096
        )

        return response

    def draft_amended_claim(self, claim_number: int, specification: str,
                           rejection_notice: str, cited_docs: List[str],
                           provider: str = None) -> AIResponse:
        """보정 청구항 작성"""
        original_claim = ""
        if claim_number <= len(self.oa_document.original_claims):
            original_claim = self.oa_document.original_claims[claim_number - 1]

        cited_docs_text = "\n\n---\n\n".join([f"[인용문헌 {i+1}]\n{doc}"
                                              for i, doc in enumerate(cited_docs)])

        prompt = f"""
심사관 거절이유를 극복하며, 인용발명들로부터 진보성을 인정받아 등록되는 것을 목적으로, 보정된 청구항 {claim_number}항을 작성해주세요.

[원 청구항 {claim_number}항]
{original_claim}

[출원명세서]
{specification}

[의견제출통지서]
{rejection_notice}

[인용문헌들]
{cited_docs_text}

작성 지침:
1. 인용발명들과 차별화되는 구성요소 추가
2. 권리범위를 필요 이상으로 좁히지 않도록 주의
3. 명세서에 기재된 내용 범위 내에서 보정
4. 명확하고 간결한 표현 사용
"""

        response = self.ai_manager.generate(
            prompt,
            provider=provider,
            system_prompt=PATENT_SYSTEM_PROMPTS["oa_response"],
            max_tokens=2048
        )

        return response

    def draft_opinion_statement(self, amended_claims: List[str], specification: str,
                               rejection_notice: str, cited_docs: List[str],
                               provider: str = None) -> AIResponse:
        """의견서 작성"""
        amended_claims_text = "\n\n".join([f"[보정 청구항 {i+1}항]\n{claim}"
                                           for i, claim in enumerate(amended_claims)])
        cited_docs_text = "\n\n---\n\n".join([f"[인용문헌 {i+1}]\n{doc}"
                                              for i, doc in enumerate(cited_docs)])

        prompt = f"""
보정된 청구항에 따른 의견서를 작성해주세요. 보정 근거와 이유를 최대한 상세하고 정확하게 작성해주세요.

[보정된 청구항]
{amended_claims_text}

[출원명세서]
{specification}

[의견제출통지서]
{rejection_notice}

[인용문헌들]
{cited_docs_text}

작성 지침:
1. 인용발명들로부터 진보성을 인정받아야 하므로, 인용발명들과 본 발명을 적절하게 최대한 인용
2. 객관적 증거 제시
3. 보정 근거 명확히 기재 (명세서 단락 번호 인용)
4. 본 발명과 인용발명의 구체적 차이점 설명
5. 본 발명의 기술적 효과 강조

의견서 구성:
1. 보정의 취지
2. 보정의 근거
3. 거절이유에 대한 의견
   - 인용발명 1과의 대비
   - 인용발명 2와의 대비 (있는 경우)
   - 진보성 인정 주장
4. 결론
"""

        response = self.ai_manager.generate(
            prompt,
            provider=provider,
            system_prompt=PATENT_SYSTEM_PROMPTS["oa_response"],
            max_tokens=4096
        )

        self.oa_document.opinion_statement = response.content
        return response

    def draft_additional_argument(self, current_opinion: str, specification: str,
                                  cited_docs: List[str], provider: str = None) -> AIResponse:
        """추가 주장 작성"""
        cited_docs_text = "\n\n---\n\n".join([f"[인용문헌 {i+1}]\n{doc}"
                                              for i, doc in enumerate(cited_docs)])

        prompt = f"""
{PatentPrompts.OA_ADDITIONAL_ARGUMENT}

[현재 의견서]
{current_opinion}

[출원명세서]
{specification}

[인용문헌들]
{cited_docs_text}

심사관을 더 확실하게 설득하기 위해 의견서 주장 부분을 뒷받침할 추가 단락을 작성해주세요.
본 발명출원명세서와 인용문헌 특허명세서를 상호 비교하면서 명확한 보정 근거를 제시해주세요.
삽입될 위치를 정확히 알려주세요.
"""

        response = self.ai_manager.generate(
            prompt,
            provider=provider,
            system_prompt=PATENT_SYSTEM_PROMPTS["oa_response"],
            max_tokens=2048
        )

        self.oa_document.additional_arguments.append(response.content)
        return response

    def compare_claims(self, original_claim: str, amended_claim: str,
                      provider: str = None) -> AIResponse:
        """청구항 비교"""
        prompt = f"""
{PatentPrompts.OA_CLAIM_COMPARISON}

[원 청구항]
{original_claim}

[보정 청구항]
{amended_claim}

달라진 부분을 명확히 표시해주세요.
- 추가된 부분: **볼드체**로 표시
- 삭제된 부분: ~~취소선~~으로 표시
- 수정된 부분: 원문과 수정문 병기
"""

        response = self.ai_manager.generate(
            prompt,
            provider=provider,
            system_prompt=PATENT_SYSTEM_PROMPTS["oa_response"],
            max_tokens=2048
        )

        return response

    def amend_dependent_claims(self, amended_claim_1: str, original_claims: List[str],
                               provider: str = None) -> AIResponse:
        """종속항 보정"""
        original_claims_text = "\n\n".join([f"[원 청구항 {i+1}항]\n{claim}"
                                            for i, claim in enumerate(original_claims)])

        prompt = f"""
보정된 청구항 1항에 따라 종속항들을 보정해주세요.

[보정된 청구항 1항]
{amended_claim_1}

[원 청구항들]
{original_claims_text}

보정 지침:
1. 종속항이 1항에 그 내용이 병합되어 삭제되더라도 다른 종속항 번호를 순차로 정리하지 말고 그냥 둔 상태로 작성
2. 1항 보정에 따라 필요한 최소한의 수정만 진행
3. 각 종속항의 특징은 유지
"""

        response = self.ai_manager.generate(
            prompt,
            provider=provider,
            system_prompt=PATENT_SYSTEM_PROMPTS["oa_response"],
            max_tokens=4096
        )

        return response

    def export_amendment(self) -> str:
        """보정서 형식으로 내보내기"""
        output = ["【보정서】\n"]

        output.append("【보정 청구범위】")
        for amended in self.oa_document.amended_claims:
            output.append(f"\n【청구항 {amended.claim_number}】")
            output.append(amended.amended_text)

        return "\n".join(output)

    def export_opinion(self) -> str:
        """의견서 형식으로 내보내기"""
        output = ["【의견서】\n"]
        output.append(self.oa_document.opinion_statement)

        if self.oa_document.additional_arguments:
            output.append("\n【추가 주장】")
            for i, arg in enumerate(self.oa_document.additional_arguments, 1):
                output.append(f"\n[추가 주장 {i}]")
                output.append(arg)

        return "\n".join(output)

    def get_oa_document(self) -> OAResponseDocument:
        """OA 대응 문서 반환"""
        return self.oa_document
