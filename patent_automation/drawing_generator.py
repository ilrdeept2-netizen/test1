# -*- coding: utf-8 -*-
"""
특허 도면 생성 및 관리 모듈
"""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
import json
import re

from .prompts import PatentPrompts
from .ai_service import AIServiceManager, PATENT_SYSTEM_PROMPTS, AIResponse


@dataclass
class DrawingElement:
    """도면 요소 데이터 클래스"""
    symbol: str  # 부호 (예: 100, S101)
    name: str    # 명칭 (예: 본체, 입력 단계)
    description: str = ""
    parent_symbol: str = ""


@dataclass
class Drawing:
    """도면 데이터 클래스"""
    number: int  # 도면 번호
    title: str   # 도면 제목
    description: str = ""  # 도면 설명
    html_code: str = ""    # HTML 코드
    elements: List[DrawingElement] = field(default_factory=list)
    drawing_type: str = "block"  # block, flow, structure, circuit 등


@dataclass
class SymbolSystem:
    """부호체계 데이터 클래스"""
    symbols: Dict[str, DrawingElement] = field(default_factory=dict)

    def add_symbol(self, symbol: str, name: str, description: str = "", parent: str = ""):
        """부호 추가"""
        self.symbols[symbol] = DrawingElement(
            symbol=symbol,
            name=name,
            description=description,
            parent_symbol=parent
        )

    def get_symbol(self, symbol: str) -> Optional[DrawingElement]:
        """부호 조회"""
        return self.symbols.get(symbol)

    def to_formatted_text(self) -> str:
        """포맷된 텍스트로 변환"""
        lines = ["【부호의 설명】"]
        for symbol, element in sorted(self.symbols.items(), key=lambda x: x[0]):
            lines.append(f"{symbol}: {element.name}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {k: {"name": v.name, "description": v.description, "parent": v.parent_symbol}
                for k, v in self.symbols.items()}


class DrawingGenerator:
    """특허 도면 생성 및 관리 클래스"""

    def __init__(self, ai_manager: Optional[AIServiceManager] = None):
        self.ai_manager = ai_manager or AIServiceManager()
        self.drawings: List[Drawing] = []
        self.symbol_system = SymbolSystem()

    def _generate_html_template(self, drawing_type: str) -> str:
        """도면 타입별 HTML 템플릿 생성"""

        templates = {
            "block": """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        .drawing-container {{
            width: 800px;
            height: 600px;
            border: 2px solid #000;
            position: relative;
            background: #fff;
            font-family: 'Malgun Gothic', sans-serif;
        }}
        .block {{
            border: 2px solid #000;
            background: #fff;
            position: absolute;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 10px;
            box-sizing: border-box;
        }}
        .block-label {{
            font-size: 14px;
            font-weight: bold;
        }}
        .block-number {{
            position: absolute;
            top: -20px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 12px;
        }}
        .arrow {{
            position: absolute;
            background: #000;
        }}
        .arrow-horizontal {{
            height: 2px;
        }}
        .arrow-vertical {{
            width: 2px;
        }}
        .arrow-head {{
            width: 0;
            height: 0;
            border-style: solid;
            position: absolute;
        }}
    </style>
</head>
<body>
    <div class="drawing-container">
        <!-- 도면 요소들이 여기에 배치됩니다 -->
        {elements}
    </div>
</body>
</html>""",

            "flow": """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        .flowchart-container {{
            width: 600px;
            padding: 20px;
            font-family: 'Malgun Gothic', sans-serif;
        }}
        .step {{
            border: 2px solid #000;
            padding: 15px 30px;
            margin: 10px auto;
            text-align: center;
            background: #fff;
            max-width: 400px;
        }}
        .step-rectangle {{
            border-radius: 0;
        }}
        .step-rounded {{
            border-radius: 20px;
        }}
        .step-diamond {{
            transform: rotate(45deg);
            width: 100px;
            height: 100px;
            margin: 30px auto;
        }}
        .step-diamond .step-content {{
            transform: rotate(-45deg);
        }}
        .connector {{
            width: 2px;
            height: 30px;
            background: #000;
            margin: 0 auto;
            position: relative;
        }}
        .connector::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            border-left: 6px solid transparent;
            border-right: 6px solid transparent;
            border-top: 10px solid #000;
        }}
        .step-number {{
            font-size: 12px;
            margin-bottom: 5px;
        }}
        .step-text {{
            font-size: 14px;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="flowchart-container">
        {elements}
    </div>
</body>
</html>""",

            "structure": """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        .structure-container {{
            width: 800px;
            height: 600px;
            border: 2px solid #000;
            position: relative;
            background: #fff;
            font-family: 'Malgun Gothic', sans-serif;
        }}
        .component {{
            border: 2px solid #000;
            position: absolute;
            background: #fff;
        }}
        .component-label {{
            position: absolute;
            font-size: 12px;
            white-space: nowrap;
        }}
        .leader-line {{
            position: absolute;
            background: #000;
            height: 1px;
        }}
        .dimension-line {{
            position: absolute;
            border-top: 1px solid #000;
        }}
        .dimension-text {{
            position: absolute;
            font-size: 10px;
            background: #fff;
            padding: 0 5px;
        }}
    </style>
</head>
<body>
    <div class="structure-container">
        {elements}
    </div>
</body>
</html>"""
        }

        return templates.get(drawing_type, templates["block"])

    def plan_drawings(self, invention_context: str, provider: str = None) -> AIResponse:
        """발명 내용에 기반한 도면 계획 수립"""
        prompt = f"""
{PatentPrompts.DRAWING_PLAN}

발명 내용:
{invention_context}

요청사항:
1. 본 발명 기술에 대해 핵심을 포함한 전체 도면을 5~6장 이내로 구성해주세요.
2. 각 도면의 목적과 포함될 내용을 설명해주세요.
3. 도면 간의 연관관계를 설명해주세요.

출력 형식:
도 1: [제목] - [설명]
도 2: [제목] - [설명]
...
"""

        response = self.ai_manager.generate(
            prompt,
            provider=provider,
            system_prompt=PATENT_SYSTEM_PROMPTS["drawing"],
            max_tokens=2048
        )

        return response

    def generate_drawing_html(self, drawing_number: int, drawing_info: Dict,
                             invention_context: str, provider: str = None) -> AIResponse:
        """개별 도면 HTML 코드 생성"""
        prompt = f"""
다음 도면을 HTML 코드로 생성해주세요.

도면 번호: 도 {drawing_number}
도면 제목: {drawing_info.get('title', '')}
도면 설명: {drawing_info.get('description', '')}
도면 타입: {drawing_info.get('type', 'block')}

발명 내용:
{invention_context}

요구사항:
1. 특허 도면 스타일로 무채색 라인드로잉으로 작성
2. 모든 구성요소에 부호 번호 표시
3. 선을 명확히 하고 깔끔하게 배치
4. 텍스트는 박스 중앙에 배치
5. 완전한 HTML 파일 형태로 제공

HTML 코드만 출력해주세요.
"""

        response = self.ai_manager.generate(
            prompt,
            provider=provider,
            system_prompt=PATENT_SYSTEM_PROMPTS["drawing"],
            max_tokens=4096
        )

        return response

    def generate_symbol_system(self, drawings_info: List[Dict],
                               invention_context: str, provider: str = None) -> AIResponse:
        """부호체계 생성"""
        drawings_desc = "\n".join([f"도 {d.get('number', i+1)}: {d.get('title', '')} - {d.get('description', '')}"
                                   for i, d in enumerate(drawings_info)])

        prompt = f"""
{PatentPrompts.DRAWING_SYMBOL_SYSTEM}

도면 정보:
{drawings_desc}

발명 내용:
{invention_context}

요청사항:
1. 모든 도면의 구성요소에 부호 부여
2. 구성요소 명칭에 '/' 나 '및' 사용 금지
3. 'XXX 부' 형태 지양, 단계는 'SXX' 형식으로 부여
4. 영문 없이 한글로 명칭 작성
5. 도면에 표시되는 모든 요소에 부호 부여

출력 형식:
100: 본체
110: 입력부
111: 제1 입력 요소
...
S101: 입력 단계
S102: 처리 단계
...
"""

        response = self.ai_manager.generate(
            prompt,
            provider=provider,
            system_prompt=PATENT_SYSTEM_PROMPTS["drawing"],
            max_tokens=2048
        )

        # 응답에서 부호체계 파싱
        self._parse_symbol_system(response.content)

        return response

    def _parse_symbol_system(self, content: str):
        """부호체계 텍스트 파싱"""
        lines = content.strip().split('\n')
        for line in lines:
            # "100: 본체" 형식 파싱
            match = re.match(r'^\s*([A-Za-z]?\d+)\s*[:：]\s*(.+)$', line)
            if match:
                symbol = match.group(1)
                name = match.group(2).strip()
                self.symbol_system.add_symbol(symbol, name)

    def remove_numbers_from_html(self, html_code: str) -> str:
        """HTML 도면에서 번호 제거"""
        # SXXX 패턴 제거
        html_code = re.sub(r'S\d{2,3}\s*', '', html_code)
        # 숫자만 있는 라벨 제거
        html_code = re.sub(r'>\s*\d+\s*<', '><', html_code)
        return html_code

    def add_drawing(self, number: int, title: str, description: str = "",
                   html_code: str = "", drawing_type: str = "block"):
        """도면 추가"""
        drawing = Drawing(
            number=number,
            title=title,
            description=description,
            html_code=html_code,
            drawing_type=drawing_type
        )
        self.drawings.append(drawing)
        return drawing

    def update_drawing_html(self, number: int, html_code: str):
        """도면 HTML 업데이트"""
        for drawing in self.drawings:
            if drawing.number == number:
                drawing.html_code = html_code
                return True
        return False

    def review_drawing(self, drawing_number: int, inventor_drawing: str = "",
                      provider: str = None) -> AIResponse:
        """도면 검토"""
        drawing = next((d for d in self.drawings if d.number == drawing_number), None)

        prompt = f"""
{PatentPrompts.DRAWING_REVIEW}

도면 번호: 도 {drawing_number}
{"현재 도면 제목: " + drawing.title if drawing else ""}
{"현재 도면 설명: " + drawing.description if drawing else ""}

{"발명자 제공 도면 정보:" if inventor_drawing else ""}
{inventor_drawing}

검토 요청:
1. 도면이 본 발명기술을 잘 반영하고 있는지 검토
2. 부호나 번호가 빠진 구성요소 확인
3. 수정 또는 추가 필요 사항 제안
"""

        response = self.ai_manager.generate(
            prompt,
            provider=provider,
            system_prompt=PATENT_SYSTEM_PROMPTS["drawing"],
            max_tokens=2048
        )

        return response

    def get_drawing_descriptions(self) -> str:
        """도면의 간단한 설명 생성"""
        descriptions = ["【도면의 간단한 설명】"]
        for drawing in sorted(self.drawings, key=lambda x: x.number):
            descriptions.append(f"도 {drawing.number}은 {drawing.description}")
        return "\n".join(descriptions)

    def export_all_html(self, output_dir: str = "."):
        """모든 도면 HTML 파일 내보내기"""
        import os
        exported_files = []

        for drawing in self.drawings:
            if drawing.html_code:
                filename = f"figure_{drawing.number}.html"
                filepath = os.path.join(output_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(drawing.html_code)
                exported_files.append(filepath)

        return exported_files

    def get_symbol_system(self) -> SymbolSystem:
        """부호체계 반환"""
        return self.symbol_system

    def get_drawings(self) -> List[Drawing]:
        """모든 도면 반환"""
        return self.drawings
