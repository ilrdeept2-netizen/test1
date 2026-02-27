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
import zlib
import struct
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
    ('invention-title', ['발명의 명칭', '명칭', '발명명칭']),
    ('technical-field', ['기술분야', '기술 분야', '관련기술분야']),
    ('background-art', ['발명의 배경이 되는 기술', '배경기술', '배경 기술', '종래기술', '발명의 배경']),
    ('technical-problem', ['해결하려는 과제', '해결하고자 하는 과제', '발명이 해결하려는 과제', '기술적 과제']),
    ('technical-solution', ['과제의 해결 수단', '해결수단', '과제 해결 수단']),
    ('advantageous-effects', ['발명의 효과', '효과']),
    ('description-of-drawings', ['도면의 간단한 설명', '도면 설명', '도면의 설명']),
    ('detailed-description', ['발명을 실시하기 위한 구체적인 내용', '실시예', '발명의 실시를 위한 구체적 내용',
                               '발명의 실시예', '구체적인 실시예', '발명의 상세한 설명']),
    ('reference-signs', ['부호의 설명', '도면 부호', '참조 부호']),
    ('claims', ['특허청구범위', '청구범위', '청구항', '특허 청구 범위']),
    ('abstract', ['요약서', '요약', '발명의 요약']),
    ('representative-drawing', ['대표도면', '대표 도면']),
])

# 공백 정규화 함수
def _normalize(text: str) -> str:
    return re.sub(r'\s+', '', text)


def detect_section(text):
    """텍스트에서 섹션 헤더를 감지하여 섹션 ID를 반환.

    매칭 우선순위:
    1. 정확 일치
    2. 공백 제거 후 일치
    3. 키워드 포함 (헤더가 키워드를 포함하거나 키워드가 헤더를 포함)
    """
    text = text.strip()
    match = re.match(r'[【\[](.*?)[】\]]', text)
    if not match:
        return None
    header = match.group(1).strip()

    # 청구항 N 패턴 (청구항 1, 청구항 2, ...)
    if re.match(r'청구항\s*\d+', header):
        return 'claim-item'

    header_norm = _normalize(header)

    # 1단계: 정확 일치
    for section_id, keywords in SECTION_DEFINITIONS.items():
        for keyword in keywords:
            if header == keyword:
                return section_id

    # 2단계: 공백 제거 후 일치
    for section_id, keywords in SECTION_DEFINITIONS.items():
        for keyword in keywords:
            if header_norm == _normalize(keyword):
                return section_id

    # 3단계: 키워드 포함 관계 (퍼지 매칭)
    for section_id, keywords in SECTION_DEFINITIONS.items():
        for keyword in keywords:
            kw_norm = _normalize(keyword)
            if kw_norm in header_norm or header_norm in kw_norm:
                # 너무 짧은 키워드는 오탐 가능성 배제 (2글자 이상)
                if len(kw_norm) >= 4:
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


def validate_claims(claims: List[Dict]) -> List[str]:
    """청구항 목록의 오류를 검사하여 경고 메시지 리스트로 반환.

    검사 항목:
    - 청구항 번호 순서 연속성 (1, 2, 3, ...)
    - 중복 번호
    - 종속항 참조 번호 존재 여부 (제N항에 있어서 → N이 있어야 함)
    - 독립항 존재 여부 (종속항만 있는 경우)
    """
    warnings = []
    if not claims:
        return ['청구항이 없습니다.']

    nums = [c['num'] for c in claims]
    num_set = set(nums)

    # 중복 번호 검사
    seen = set()
    for n in nums:
        if n in seen:
            warnings.append(f'청구항 {n}: 번호 중복')
        seen.add(n)

    # 순서 연속성 검사 (1부터 시작, 빈 번호 없어야 함)
    expected = list(range(1, len(num_set) + 1))
    sorted_nums = sorted(num_set)
    if sorted_nums != expected:
        missing = [n for n in expected if n not in num_set]
        if missing:
            warnings.append(f'청구항 번호 누락: {missing}')
        extra = [n for n in sorted_nums if n not in expected]
        if extra:
            warnings.append(f'청구항 번호 불연속: {extra}')

    # 종속항 참조 검사 (제N항에 있어서)
    dep_pattern = re.compile(r'제\s*(\d+)\s*항에\s*(?:있어서|의해서|의해)')
    independent_nums = set()

    for claim in claims:
        text = claim['text']
        deps = dep_pattern.findall(text)
        if not deps:
            independent_nums.add(claim['num'])
        else:
            for dep_str in deps:
                dep_num = int(dep_str)
                if dep_num not in num_set:
                    warnings.append(
                        f'청구항 {claim["num"]}: 존재하지 않는 제{dep_num}항 참조'
                    )
                if dep_num >= claim['num']:
                    warnings.append(
                        f'청구항 {claim["num"]}: 자신보다 나중 번호(제{dep_num}항) 참조'
                    )

    if not independent_nums:
        warnings.append('독립항이 없습니다. 청구항 1은 독립항이어야 합니다.')

    return warnings


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
    """HWP 문서 읽기 클래스 (HWP5 형식 지원)"""

    # HWP5 레코드 태그 ID
    HWPTAG_PARA_TEXT = 67

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        self._compressed = True  # 기본값: 압축됨

    def extract_text_with_structure(self) -> Dict[str, List[str]]:
        """구조를 유지하며 텍스트 추출"""
        sections = {}
        current_section = 'header'
        sections[current_section] = []

        try:
            full_text = self._extract_hwp5_text()
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

    def _extract_hwp5_text(self) -> str:
        """HWP5 OLE 스트림에서 텍스트 추출 (zlib 압축 해제 + 레코드 파싱)"""
        text_parts = []

        ole = olefile.OleFileIO(str(self.file_path))
        try:
            # FileHeader에서 압축 여부 확인
            if ole.exists('FileHeader'):
                header_data = ole.openstream('FileHeader').read()
                if len(header_data) >= 36:
                    flags = struct.unpack_from('<I', header_data, 32)[0]
                    self._compressed = bool(flags & 0x1)

            # BodyText/Section0, Section1, ... 순서대로 읽기
            section_idx = 0
            while True:
                stream_path = f'BodyText/Section{section_idx}'
                if not ole.exists(stream_path):
                    break

                data = ole.openstream(stream_path).read()

                # zlib 압축 해제 (raw deflate)
                if self._compressed:
                    try:
                        data = zlib.decompress(data, -15)
                    except zlib.error:
                        pass  # 압축되지 않은 경우 그대로 사용

                section_text = self._parse_hwp5_records(data)
                if section_text:
                    text_parts.append(section_text)

                section_idx += 1
        finally:
            ole.close()

        return '\n'.join(text_parts)

    def _parse_hwp5_records(self, data: bytes) -> str:
        """HWP5 레코드 바이너리에서 텍스트(HWPTAG_PARA_TEXT) 추출"""
        text_parts = []
        offset = 0
        data_len = len(data)

        while offset + 4 <= data_len:
            header = struct.unpack_from('<I', data, offset)[0]
            tag_id = header & 0x3FF
            size = (header >> 20) & 0xFFF
            offset += 4

            # 확장 크기 (size == 0xFFF 이면 다음 4바이트가 실제 크기)
            if size == 0xFFF:
                if offset + 4 > data_len:
                    break
                size = struct.unpack_from('<I', data, offset)[0]
                offset += 4

            if offset + size > data_len:
                break

            if tag_id == self.HWPTAG_PARA_TEXT and size > 0:
                raw = data[offset:offset + size]
                try:
                    text = raw.decode('utf-16le')
                    # 제어 문자 제거 (chr(0)~chr(31) 중 \n, \t 제외)
                    text = ''.join(
                        c for c in text
                        if c >= ' ' or c in '\n\t'
                    )
                    if text.strip():
                        text_parts.append(text.strip())
                except UnicodeDecodeError:
                    pass

            offset += size

        return '\n'.join(text_parts)


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
        sections = self.get_sections()

        generator = HLTGenerator()
        generator.generate(sections, str(self.output_path))

        return str(self.output_path)

    def get_sections(self) -> OrderedDict:
        """파일 형식에 따라 섹션 추출 (모든 형식 지원)"""
        if self.file_type == '.docx':
            return self.extract_sections()
        else:
            raw = self._read_document()
            return self._normalize_sections(raw)

    def _normalize_sections(self, raw: Dict[str, List[str]]) -> OrderedDict:
        """_read_document() 결과를 SECTION_DEFINITIONS 순서로 정렬된 OrderedDict로 변환"""
        result = OrderedDict()
        for section_id in SECTION_DEFINITIONS:
            if section_id in raw and raw[section_id]:
                result[section_id] = raw[section_id]
        # 정의에 없는 섹션도 포함
        for k, v in raw.items():
            if k not in result and v:
                result[k] = v
        return result

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
