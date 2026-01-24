"""
문서 처리 에이전트

다양한 문서 형식을 변환하고 처리합니다.
"""

import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from pathlib import Path

from .base_agent import BaseAgent, AgentResult, AgentStatus


@dataclass
class DocumentInfo:
    """문서 정보"""
    file_path: str
    file_type: str
    size: int
    content: str
    metadata: Dict[str, Any]


class DocumentProcessorAgent(BaseAgent):
    """
    문서 처리 에이전트

    Word, HWP, PDF 등 다양한 형식의 문서를
    특허청 표준 형식(HLT)으로 변환합니다.
    """

    # 지원하는 파일 형식
    SUPPORTED_FORMATS = {
        "input": [".docx", ".doc", ".hwp", ".pdf", ".txt", ".pptx", ".xlsx"],
        "output": [".hlt", ".xml", ".json", ".txt"]
    }

    # 특허 명세서 표준 섹션
    PATENT_SECTIONS = [
        "발명의 명칭",
        "기술분야",
        "발명의 배경이 되는 기술",
        "발명의 내용",
        "해결하려는 과제",
        "과제의 해결 수단",
        "발명의 효과",
        "도면의 간단한 설명",
        "발명을 실시하기 위한 구체적인 내용",
        "부호의 설명",
        "청구범위",
        "요약서",
        "대표도",
        "도면"
    ]

    def __init__(self, **kwargs):
        super().__init__(
            name="document_processor",
            model="claude-sonnet-4-20250514",
            system_prompt="""당신은 문서 처리 전문가입니다.
Word, HWP, PDF 등 다양한 형식의 문서를
특허청 표준 형식(HLT)으로 변환합니다.

지원 형식:
- 입력: .docx, .hwp, .pdf, .txt
- 출력: .hlt, .xml, .json

한국 특허 명세서 표준 섹션:
1. 발명의 명칭
2. 기술분야
3. 발명의 배경이 되는 기술
4. 발명의 내용
5. 도면의 간단한 설명
6. 발명을 실시하기 위한 구체적인 내용
7. 청구범위
8. 요약서""",
            tools=["read", "write", "bash"],
            **kwargs
        )

    async def process(self, input_data: Any) -> AgentResult:
        """
        문서를 처리합니다.

        Args:
            input_data: 파일 경로 또는 문서 내용

        Returns:
            AgentResult: 처리 결과
        """
        self.status = AgentStatus.RUNNING

        try:
            if isinstance(input_data, dict):
                file_path = input_data.get("file", "")
                output_format = input_data.get("format", "json")
            elif isinstance(input_data, str):
                if os.path.exists(input_data):
                    file_path = input_data
                    output_format = "json"
                else:
                    # 직접 내용이 전달된 경우
                    parsed = await self._parse_content(input_data)
                    self.status = AgentStatus.COMPLETED
                    return AgentResult(success=True, data=parsed)
            else:
                raise ValueError("지원하지 않는 입력 형식입니다.")

            # 파일 형식 확인
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in self.SUPPORTED_FORMATS["input"]:
                raise ValueError(f"지원하지 않는 파일 형식: {file_ext}")

            # 문서 파싱
            content = await self._read_document(file_path, file_ext)

            # 구조화된 데이터 추출
            parsed = await self._parse_content(content)

            self.status = AgentStatus.COMPLETED
            return AgentResult(
                success=True,
                data=parsed,
                metadata={
                    "source_file": file_path,
                    "file_type": file_ext,
                    "output_format": output_format
                }
            )

        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"문서 처리 오류: {e}")
            return AgentResult(success=False, data=None, error=str(e))

    async def _read_document(self, file_path: str, file_ext: str) -> str:
        """문서 파일을 읽습니다."""
        if file_ext == ".txt":
            return await self.execute_tool("read", file_path=file_path)

        elif file_ext == ".docx":
            # python-docx 사용
            try:
                from docx import Document
                doc = Document(file_path)
                return "\n".join([para.text for para in doc.paragraphs])
            except ImportError:
                # python-docx가 없으면 bash로 처리
                cmd = f"python3 -c \"from docx import Document; doc = Document('{file_path}'); print('\\n'.join([p.text for p in doc.paragraphs]))\""
                return await self.execute_tool("bash", command=cmd)

        elif file_ext == ".pdf":
            # PyPDF2 사용
            try:
                cmd = f"python3 -c \"import PyPDF2; f = open('{file_path}', 'rb'); r = PyPDF2.PdfReader(f); print('\\n'.join([p.extract_text() for p in r.pages]))\""
                return await self.execute_tool("bash", command=cmd)
            except:
                return f"PDF 파일을 읽을 수 없습니다: {file_path}"

        elif file_ext == ".hwp":
            # olefile 사용 (기본 텍스트 추출)
            try:
                cmd = f"python3 -c \"import olefile; ole = olefile.OleFileIO('{file_path}'); print(ole.exists('BodyText/Section0'))\""
                return await self.execute_tool("bash", command=cmd)
            except:
                return f"HWP 파일을 읽을 수 없습니다: {file_path}"

        else:
            return await self.execute_tool("read", file_path=file_path)

    async def _parse_content(self, content: str) -> Dict[str, Any]:
        """문서 내용을 구조화합니다."""
        # AI를 사용하여 섹션 분류
        parse_prompt = f"""
다음 문서 내용을 한국 특허 명세서 표준 형식으로 구조화하세요.

문서 내용:
{content[:8000]}

표준 섹션:
1. 발명의 명칭
2. 기술분야
3. 발명의 배경이 되는 기술
4. 발명의 내용 (해결하려는 과제, 과제의 해결 수단, 발명의 효과)
5. 도면의 간단한 설명
6. 발명을 실시하기 위한 구체적인 내용
7. 청구범위
8. 요약서

JSON 형식으로 각 섹션의 내용을 추출하세요.
"""

        response = ""
        async for chunk in self.query(parse_prompt):
            response += chunk

        # 기본 구조 생성
        parsed = {
            "title": self._extract_section(content, "발명의 명칭"),
            "technical_field": self._extract_section(content, "기술분야"),
            "background": self._extract_section(content, "발명의 배경"),
            "content": {
                "problem": self._extract_section(content, "해결하려는 과제"),
                "solution": self._extract_section(content, "과제의 해결 수단"),
                "effect": self._extract_section(content, "발명의 효과")
            },
            "drawings": self._extract_section(content, "도면"),
            "detailed_description": self._extract_section(content, "구체적인 내용"),
            "claims": self._extract_claims(content),
            "abstract": self._extract_section(content, "요약서"),
            "raw_content": content[:5000],
            "ai_structured": response
        }

        return parsed

    def _extract_section(self, content: str, section_name: str) -> str:
        """특정 섹션을 추출합니다."""
        patterns = [
            rf"{section_name}[:\s]*(.+?)(?=\n[가-힣]+분야|\n청구|\n요약|$)",
            rf"【{section_name}】(.+?)(?=【|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()[:2000]

        return ""

    def _extract_claims(self, content: str) -> List[str]:
        """청구항을 추출합니다."""
        claims = []
        pattern = r"청구항\s*(\d+)[.:\s]*(.+?)(?=청구항\s*\d+|$)"
        matches = re.findall(pattern, content, re.DOTALL)

        for num, text in matches:
            claims.append({
                "number": int(num),
                "text": text.strip()[:1000]
            })

        return claims

    async def convert_to_hlt(self, parsed_data: Dict[str, Any]) -> str:
        """구조화된 데이터를 HLT 형식으로 변환합니다."""
        hlt_template = """<?xml version="1.0" encoding="UTF-8"?>
<patent-specification>
    <title>{title}</title>
    <technical-field>{technical_field}</technical-field>
    <background>{background}</background>
    <invention-content>
        <problem>{problem}</problem>
        <solution>{solution}</solution>
        <effect>{effect}</effect>
    </invention-content>
    <drawings>{drawings}</drawings>
    <detailed-description>{detailed_description}</detailed-description>
    <claims>{claims}</claims>
    <abstract>{abstract}</abstract>
</patent-specification>"""

        claims_xml = ""
        for claim in parsed_data.get("claims", []):
            claims_xml += f"\n        <claim number=\"{claim['number']}\">{claim['text']}</claim>"

        hlt_content = hlt_template.format(
            title=parsed_data.get("title", ""),
            technical_field=parsed_data.get("technical_field", ""),
            background=parsed_data.get("background", ""),
            problem=parsed_data.get("content", {}).get("problem", ""),
            solution=parsed_data.get("content", {}).get("solution", ""),
            effect=parsed_data.get("content", {}).get("effect", ""),
            drawings=parsed_data.get("drawings", ""),
            detailed_description=parsed_data.get("detailed_description", ""),
            claims=claims_xml,
            abstract=parsed_data.get("abstract", "")
        )

        return hlt_content

    async def batch_convert(
        self,
        files: List[str],
        output_format: str = "hlt"
    ) -> AgentResult:
        """여러 문서를 일괄 변환합니다."""
        self.status = AgentStatus.RUNNING
        results = []

        try:
            for file_path in files:
                result = await self.process({"file": file_path, "format": output_format})
                results.append({
                    "file": file_path,
                    "success": result.success,
                    "data": result.data,
                    "error": result.error
                })

            self.status = AgentStatus.COMPLETED
            return AgentResult(
                success=all(r["success"] for r in results),
                data=results,
                metadata={"total": len(files), "format": output_format}
            )

        except Exception as e:
            self.status = AgentStatus.ERROR
            return AgentResult(success=False, data=results, error=str(e))
