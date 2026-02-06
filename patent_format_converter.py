#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
특허 문서 형식 변환기 (Patent Document Format Converter)
Word/HWP/PDF → 한국특허청 HLT 형식 자동 변환

입력: .docx, .hwp, .pdf
출력: .hlt (XML 기반 특허 명세서 포맷)
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime
from collections import OrderedDict
from lxml import etree
from typing import Dict, List, Optional

# 필수 라이브러리
try:
    from docx import Document
    import olefile
    from PyPDF2 import PdfReader
except ImportError as e:
    print(f"오류: 필수 라이브러리 누락 - {e}")
    print("필요한 패키지 설치: pip install python-docx PyPDF2 olefile lxml")
    sys.exit(1)


# =====================================================================
# 섹션 정의 및 유틸리티 함수
# =====================================================================

SECTION_DEFINITIONS = OrderedDict([
    ('invention-title', ['발명의 명칭']),
    ('technical-field', ['기술분야']),
    ('background-art', ['발명의 배경이 되는 기술', '배경기술']),
    ('technical-problem', ['해결하려는 과제', '해결하고자 하는 과제']),
    ('technical-solution', ['과제의 해결 수단']),
    ('advantageous-effects', ['발명의 효과']),
    ('description-of-drawings', ['도면의 간단한 설명']),
    ('detailed-description', ['발명을 실시하기 위한 구체적인 내용', '실시예']),
    ('reference-signs', ['부호의 설명']),
    ('claims', ['특허청구범위', '청구범위']),
    ('abstract', ['요약서', '요약']),
    ('representative-drawing', ['대표도면']),
])


def detect_section(text):
    """텍스트에서 섹션 헤더를 감지하여 섹션 ID를 반환"""
    text = text.strip()
    match = re.match(r'[【\[](.*?)[】\]]', text)
    if not match:
        return None
    header = match.group(1).strip()

    # 청구항 N 패턴
    if re.match(r'청구항\s*\d+', header):
        return 'claim-item'

    # 섹션 정의에서 매칭
    for section_id, keywords in SECTION_DEFINITIONS.items():
        for keyword in keywords:
            if header == keyword:
                return section_id

    return None


def parse_claims(lines):
    """청구항 텍스트 라인들을 파싱하여 구조화된 리스트로 반환"""
    claims = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # "청구항 N:" 형식
        m = re.match(r'청구항\s*(\d+)\s*[:：]\s*(.*)', line)
        if m:
            claims.append({'num': int(m.group(1)), 'text': m.group(2).strip()})
            continue

        # "N." 형식
        m = re.match(r'(\d+)\.\s+(.*)', line)
        if m:
            claims.append({'num': int(m.group(1)), 'text': m.group(2).strip()})
            continue

        # 번호 없는 경우: 이전 청구항에 추가 또는 새 청구항 생성
        if claims:
            claims[-1]['text'] += ' ' + line
        else:
            claims.append({'num': len(claims) + 1, 'text': line})

    return claims


# =====================================================================
# 문서 읽기 클래스
# =====================================================================

class WordReader:
    """Word 문서 읽기 클래스"""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        try:
            self.document = Document(str(self.file_path))
        except Exception as e:
            raise ValueError(f"Word 문서를 열 수 없습니다: {e}")

    def get_paragraphs(self):
        """문서의 모든 비어있지 않은 단락 텍스트를 반환"""
        return [p.text for p in self.document.paragraphs if p.text.strip()]

    def extract_text_with_structure(self) -> Dict[str, List[str]]:
        """구조를 유지하며 텍스트 추출"""
        sections = {}
        current_section = 'header'
        sections[current_section] = []

        for para in self.document.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            section_key = detect_section(text)
            if section_key and section_key != 'claim-item':
                current_section = section_key
                sections[current_section] = []
            elif section_key == 'claim-item':
                # 청구항 아이템은 claims 섹션에 포함
                if 'claims' not in sections:
                    sections['claims'] = []
                current_section = 'claims'
            else:
                sections.setdefault(current_section, [])
                sections[current_section].append(text)

        return sections


class PDFReader:
    """PDF 문서 읽기 클래스"""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        try:
            self.pdf = PdfReader(str(self.file_path))
        except Exception as e:
            raise ValueError(f"PDF 문서를 열 수 없습니다: {e}")

    def extract_text_with_structure(self) -> Dict[str, List[str]]:
        """구조를 유지하며 텍스트 추출"""
        sections = {}
        current_section = 'header'
        sections[current_section] = []

        full_text = ""
        for page in self.pdf.pages:
            try:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            except:
                continue

        lines = full_text.split('\n')

        for line in lines:
            text = line.strip()
            if not text:
                continue

            section_key = detect_section(text)
            if section_key and section_key != 'claim-item':
                current_section = section_key
                sections[current_section] = []
            else:
                sections.setdefault(current_section, [])
                sections[current_section].append(text)

        return sections


class HWPReader:
    """HWP 문서 읽기 클래스"""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

    def extract_text_with_structure(self) -> Dict[str, List[str]]:
        """구조를 유지하며 텍스트 추출"""
        sections = {}
        current_section = 'header'
        sections[current_section] = []

        try:
            ole = olefile.OleFileIO(str(self.file_path))
            streams = ole.listdir()
            text_content = []

            for stream in streams:
                stream_name = '/'.join(stream)
                if 'BodyText' in stream_name or 'Section' in stream_name:
                    try:
                        data = ole.openstream(stream).read()
                        text = self._extract_text_from_stream(data)
                        if text:
                            text_content.append(text)
                    except:
                        continue

            ole.close()

            full_text = '\n'.join(text_content)
            lines = full_text.split('\n')

            for line in lines:
                text = line.strip()
                if not text:
                    continue

                section_key = detect_section(text)
                if section_key and section_key != 'claim-item':
                    current_section = section_key
                    sections[current_section] = []
                else:
                    sections.setdefault(current_section, [])
                    sections[current_section].append(text)

        except Exception as e:
            print(f"경고: HWP 파일 읽기 오류 - {e}")
            sections['header'] = [f"HWP 파일: {self.file_path.name}"]

        return sections

    def _extract_text_from_stream(self, data: bytes) -> str:
        """HWP 스트림에서 텍스트 추출"""
        try:
            text = data.decode('utf-16le', errors='ignore')
            text = ''.join(char for char in text if char.isprintable() or char in '\n\r\t')
            return text
        except:
            try:
                return data.decode('utf-8', errors='ignore')
            except:
                return ""


# =====================================================================
# HLT 생성기
# =====================================================================

class HLTGenerator:
    """HLT (XML) 형식 생성기"""

    NSMAP = {None: 'http://www.kipo.go.kr/kipo'}

    def generate(self, sections, output_path):
        """섹션 딕셔너리를 기반으로 HLT XML 파일 생성"""
        root = etree.Element('patent-document', nsmap=self.NSMAP)

        for section_id, content_lines in sections.items():
            if section_id == 'invention-title':
                elem = etree.SubElement(root, 'invention-title')
                elem.text = '\n'.join(content_lines)

            elif section_id == 'claims':
                claims_elem = etree.SubElement(root, 'claims')
                parsed = parse_claims(content_lines)
                for claim in parsed:
                    claim_elem = etree.SubElement(claims_elem, 'claim')
                    claim_elem.set('num', str(claim['num']))
                    p = etree.SubElement(claim_elem, 'p')
                    p.text = claim['text']

            elif section_id == 'abstract':
                abstract_elem = etree.SubElement(root, 'abstract')
                for line in content_lines:
                    p = etree.SubElement(abstract_elem, 'p')
                    p.text = line

            else:
                section_elem = etree.SubElement(root, section_id)
                for line in content_lines:
                    p = etree.SubElement(section_elem, 'p')
                    p.text = line

        tree = etree.ElementTree(root)
        tree.write(output_path, xml_declaration=True, encoding='UTF-8',
                   pretty_print=True)
        return output_path


# =====================================================================
# 메인 변환기
# =====================================================================

class PatentFormatConverter:
    """특허 문서 형식 변환기 메인 클래스"""

    def __init__(self, input_path: str, output_path: Optional[str] = None):
        self.input_path = Path(input_path)

        if not self.input_path.exists():
            raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {input_path}")

        if output_path:
            self.output_path = Path(output_path)
        else:
            self.output_path = self.input_path.with_suffix('.hlt')

        self.file_type = self.input_path.suffix.lower()
        if self.file_type not in ['.docx', '.doc', '.hwp', '.pdf']:
            raise ValueError(f"지원하지 않는 파일 형식: {self.file_type}\n지원 형식: .docx, .hwp, .pdf")

    def extract_sections(self) -> OrderedDict:
        """문서에서 섹션을 추출하여 OrderedDict로 반환"""
        reader = self._create_reader()
        paragraphs = [p.text for p in reader.document.paragraphs if p.text.strip()]

        sections = OrderedDict()
        current_section = None
        pending_claim_num = None

        for text in paragraphs:
            section_type = detect_section(text)

            if section_type == 'claim-item':
                # 청구항 아이템은 claims 섹션에 포함
                current_section = 'claims'
                sections.setdefault('claims', [])
                m = re.match(r'[【\[]청구항\s*(\d+)[】\]]', text.strip())
                if m:
                    pending_claim_num = m.group(1)
                continue

            elif section_type is not None:
                current_section = section_type
                pending_claim_num = None
                if current_section not in sections:
                    sections[current_section] = []
                continue

            if current_section and current_section in sections:
                if pending_claim_num:
                    text = f'청구항 {pending_claim_num}: {text}'
                    pending_claim_num = None
                sections[current_section].append(text)

        return sections

    def convert(self) -> str:
        """파일 변환 실행"""
        sections = self.extract_sections()

        generator = HLTGenerator()
        generator.generate(sections, str(self.output_path))

        return str(self.output_path)

    def _create_reader(self):
        """파일 형식에 따른 리더 생성"""
        if self.file_type == '.docx':
            return WordReader(str(self.input_path))
        elif self.file_type == '.doc':
            raise NotImplementedError("구형 .doc 형식은 먼저 .docx로 변환해주세요.")
        else:
            raise ValueError(f"extract_sections은 .docx 파일만 지원합니다: {self.file_type}")

    def _read_document(self) -> Dict[str, List[str]]:
        """문서 형식에 따라 읽기 (HWP, PDF 포함)"""
        if self.file_type == '.docx':
            reader = WordReader(str(self.input_path))
            return reader.extract_text_with_structure()
        elif self.file_type == '.hwp':
            reader = HWPReader(str(self.input_path))
            return reader.extract_text_with_structure()
        elif self.file_type == '.pdf':
            reader = PDFReader(str(self.input_path))
            return reader.extract_text_with_structure()
        elif self.file_type == '.doc':
            raise NotImplementedError("구형 .doc 형식은 먼저 .docx로 변환해주세요.")
        else:
            raise ValueError(f"지원하지 않는 파일 형식: {self.file_type}")


def main():
    """CLI 메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Word/HWP/PDF → 한국특허청 HLT 형식 변환',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python patent_format_converter.py 명세서.docx
  python patent_format_converter.py 명세서.hwp -o output.hlt
  python patent_format_converter.py 명세서.pdf --output 특허문서.hlt

지원 형식:
  - 입력: .docx, .hwp, .pdf
  - 출력: .hlt (한국특허청 XML 형식)
        """
    )

    parser.add_argument('input_file', help='변환할 파일 (Word/HWP/PDF)')
    parser.add_argument('-o', '--output', help='출력 HLT 파일 경로', default=None)

    args = parser.parse_args()

    try:
        converter = PatentFormatConverter(args.input_file, args.output)
        output = converter.convert()
        print(f"변환 완료: {output}")
        return 0
    except Exception as e:
        print(f"오류 발생: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
