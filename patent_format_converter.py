#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
특허 문서 형식 변환기 (Patent Document Format Converter)
Word/HWP/HWPX → 한국특허청 HLT 형식 자동 변환

입력: .docx, .hwp, .hwpx
출력: .hlt (XML 기반 특허 명세서 포맷)
"""

import os
import sys
import re
import zlib
import struct
import zipfile
from pathlib import Path
from datetime import datetime
from lxml import etree
from typing import Dict, List, Optional, Tuple
from collections import OrderedDict

# 필수 라이브러리
try:
    from docx import Document
    import olefile
except ImportError as e:
    print(f"오류: 필수 라이브러리 누락 - {e}")
    print("필요한 패키지 설치: pip install python-docx olefile lxml")
    sys.exit(1)


# ============================================================
# 한국 특허명세서 섹션 정의
# ============================================================

# 섹션 순서 및 XML 태그 매핑 (한국특허청 기준)
SECTION_DEFINITIONS = OrderedDict([
    ('invention-title', {
        'xml_tag': 'invention-title',
        'korean_title': '발명의 명칭',
        'patterns': [
            r'발명의\s*명칭',
            r'발명\s*명칭',
        ],
        'is_title': True,
    }),
    ('technical-field', {
        'xml_tag': 'technical-field',
        'korean_title': '기술분야',
        'patterns': [
            r'기술\s*분야',
        ],
    }),
    ('background-art', {
        'xml_tag': 'background-art',
        'korean_title': '발명의 배경이 되는 기술',
        'patterns': [
            r'발명의\s*배경이?\s*되는\s*기술',
            r'배경\s*기술',
            r'종래\s*기술',
        ],
    }),
    ('prior-art-documents', {
        'xml_tag': 'prior-art-documents',
        'korean_title': '선행기술문헌',
        'patterns': [
            r'선행\s*기술\s*문헌',
            r'특허\s*문헌',
            r'비특허\s*문헌',
        ],
    }),
    ('disclosure', {
        'xml_tag': 'disclosure',
        'korean_title': '발명의 내용',
        'patterns': [
            r'발명의\s*내용',
        ],
    }),
    ('technical-problem', {
        'xml_tag': 'technical-problem',
        'korean_title': '해결하려는 과제',
        'patterns': [
            r'해결하려는\s*과제',
            r'해결하고자\s*하는\s*과제',
            r'발명이\s*이루고자\s*하는\s*기술적\s*과제',
            r'기술적\s*과제',
        ],
    }),
    ('technical-solution', {
        'xml_tag': 'technical-solution',
        'korean_title': '과제의 해결 수단',
        'patterns': [
            r'과제의?\s*해결\s*수단',
            r'기술적\s*해결\s*수단',
        ],
    }),
    ('advantageous-effects', {
        'xml_tag': 'advantageous-effects',
        'korean_title': '발명의 효과',
        'patterns': [
            r'발명의?\s*효과',
        ],
    }),
    ('description-of-drawings', {
        'xml_tag': 'description-of-drawings',
        'korean_title': '도면의 간단한 설명',
        'patterns': [
            r'도면의?\s*간단한?\s*설명',
        ],
    }),
    ('detailed-description', {
        'xml_tag': 'mode-for-invention',
        'korean_title': '발명을 실시하기 위한 구체적인 내용',
        'patterns': [
            r'발명을?\s*실시하기\s*위한\s*구체적인?\s*내용',
            r'발명의?\s*실시를?\s*위한\s*구체적인?\s*내용',
            r'실시\s*예',
            r'구체적인?\s*내용',
            r'상세한?\s*설명',
            r'발명의?\s*실시\s*형태',
        ],
    }),
    ('reference-signs', {
        'xml_tag': 'reference-signs',
        'korean_title': '부호의 설명',
        'patterns': [
            r'부호의?\s*설명',
            r'도면\s*부호의?\s*설명',
        ],
    }),
    ('claims', {
        'xml_tag': 'claims',
        'korean_title': '특허청구범위',
        'patterns': [
            r'특허\s*청구\s*범위',
            r'청구\s*범위',
            r'청구항',
        ],
    }),
    ('abstract', {
        'xml_tag': 'abstract',
        'korean_title': '요약서',
        'patterns': [
            r'요약서?',
            r'요\s*약\s*서',
        ],
    }),
    ('representative-drawing', {
        'xml_tag': 'representative-drawing',
        'korean_title': '대표도면',
        'patterns': [
            r'대표\s*도면',
        ],
    }),
])


def detect_section(text: str) -> Optional[str]:
    """텍스트에서 특허 명세서 섹션 헤더를 감지한다.

    【】, [], 또는 일반 텍스트에서 섹션 헤더 패턴을 찾는다.
    """
    text = text.strip()
    if not text:
        return None

    # 【 】 또는 [ ] 괄호 안의 텍스트를 추출
    bracket_matches = re.findall(r'[【\[](.*?)[】\]]', text)

    # 괄호 안 내용으로 먼저 매칭
    if bracket_matches:
        for match in bracket_matches:
            inner = match.strip()
            # 청구항 N 패턴 (개별 클레임 헤더)
            if re.match(r'청구항\s*\d+', inner):
                return 'claim-item'  # 개별 청구항 마커
            for section_id, defn in SECTION_DEFINITIONS.items():
                for pattern in defn['patterns']:
                    if re.match(pattern, inner) or re.search(pattern, inner):
                        return section_id
        return None

    # 괄호 없이 줄 시작이 섹션 헤더인 경우
    for section_id, defn in SECTION_DEFINITIONS.items():
        for pattern in defn['patterns']:
            if re.match(r'^' + pattern + r'\s*$', text) or re.match(r'^' + pattern + r'\s*[:：]', text):
                return section_id

    return None


def parse_claims(claim_texts: List[str]) -> List[Dict[str, str]]:
    """청구항 텍스트 리스트를 개별 청구항으로 파싱한다."""
    claims = []
    current_claim_num = 0
    current_claim_text = []

    for line in claim_texts:
        line = line.strip()
        if not line:
            continue

        # 【청구항 N】 패턴
        m = re.match(r'[【\[]?\s*청구항\s*(\d+)\s*[】\]]?\s*[:：]?\s*(.*)', line)
        if m:
            # 이전 청구항 저장
            if current_claim_num > 0 and current_claim_text:
                claims.append({
                    'num': current_claim_num,
                    'text': '\n'.join(current_claim_text).strip(),
                })
            current_claim_num = int(m.group(1))
            remainder = m.group(2).strip()
            current_claim_text = [remainder] if remainder else []
            continue

        # "1. " 또는 "1) " 패턴으로 시작하는 경우
        m = re.match(r'^(\d+)\s*[.)\]]\s*(.*)', line)
        if m:
            num = int(m.group(1))
            if num == current_claim_num + 1 or (current_claim_num == 0 and num == 1):
                if current_claim_num > 0 and current_claim_text:
                    claims.append({
                        'num': current_claim_num,
                        'text': '\n'.join(current_claim_text).strip(),
                    })
                current_claim_num = num
                current_claim_text = [m.group(2).strip()] if m.group(2).strip() else []
                continue

        # 현재 청구항에 라인 추가
        if current_claim_num > 0:
            current_claim_text.append(line)
        else:
            # 첫 청구항 시작 전의 텍스트 - 청구항 1로 간주
            current_claim_num = 1
            current_claim_text.append(line)

    # 마지막 청구항 저장
    if current_claim_num > 0 and current_claim_text:
        claims.append({
            'num': current_claim_num,
            'text': '\n'.join(current_claim_text).strip(),
        })

    return claims


# ============================================================
# 문서 리더 클래스
# ============================================================

class WordReader:
    """Word(.docx) 문서 파서"""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        try:
            self.document = Document(str(self.file_path))
        except Exception as e:
            raise ValueError(f"Word 문서를 열 수 없습니다: {e}")

    def extract_sections(self) -> OrderedDict:
        """문서에서 특허 명세서 섹션을 추출한다."""
        sections = OrderedDict()
        current_section = '_header'
        sections[current_section] = []

        for para in self.document.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            section_id = detect_section(text)
            if section_id == 'claim-item':
                # 【청구항 N】 -> claims 섹션에 "청구항 N:" 마커 삽입
                current_section = 'claims'
                if current_section not in sections:
                    sections[current_section] = []
                m = re.search(r'청구항\s*(\d+)', text)
                claim_num = m.group(1) if m else '1'
                remainder = re.sub(r'[【\[][^】\]]*[】\]]', '', text).strip()
                marker = f'청구항 {claim_num}:'
                if remainder:
                    marker += ' ' + remainder
                sections[current_section].append(marker)
            elif section_id:
                current_section = section_id
                if current_section not in sections:
                    sections[current_section] = []
                remainder = re.sub(r'[【\[][^】\]]*[】\]]', '', text).strip()
                if remainder:
                    sections[current_section].append(remainder)
            else:
                if current_section not in sections:
                    sections[current_section] = []
                sections[current_section].append(text)

        if '_header' in sections and not sections['_header']:
            del sections['_header']

        return sections


class HWPReader:
    """HWP5 바이너리(.hwp) 문서 파서"""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

    def extract_sections(self) -> OrderedDict:
        """HWP 문서에서 특허 명세서 섹션을 추출한다."""
        sections = OrderedDict()
        current_section = '_header'
        sections[current_section] = []

        try:
            ole = olefile.OleFileIO(str(self.file_path))
        except Exception as e:
            raise ValueError(f"HWP 파일을 열 수 없습니다 (OLE 형식이 아닌 경우 .hwpx 확장자를 확인하세요): {e}")

        try:
            # FileHeader에서 압축 여부 확인
            is_compressed = self._check_compressed(ole)

            # BodyText 스트림에서 텍스트 추출
            streams = ole.listdir()
            text_content = []

            for stream in sorted(streams, key=lambda s: '/'.join(s)):
                stream_name = '/'.join(stream)
                if 'BodyText' in stream_name or 'Section' in stream_name:
                    try:
                        raw = ole.openstream(stream).read()
                        if is_compressed:
                            try:
                                raw = zlib.decompress(raw, -15)
                            except zlib.error:
                                pass
                        text = self._extract_text_from_bodytext(raw)
                        if text:
                            text_content.append(text)
                    except Exception:
                        continue

            ole.close()

            full_text = '\n'.join(text_content)
            lines = full_text.split('\n')

            for line in lines:
                text = line.strip()
                if not text:
                    continue

                section_id = detect_section(text)
                if section_id == 'claim-item':
                    current_section = 'claims'
                    if current_section not in sections:
                        sections[current_section] = []
                    m = re.search(r'청구항\s*(\d+)', text)
                    claim_num = m.group(1) if m else '1'
                    remainder = re.sub(r'[【\[][^】\]]*[】\]]', '', text).strip()
                    marker = f'청구항 {claim_num}:'
                    if remainder:
                        marker += ' ' + remainder
                    sections[current_section].append(marker)
                elif section_id:
                    current_section = section_id
                    if current_section not in sections:
                        sections[current_section] = []
                    remainder = re.sub(r'[【\[][^】\]]*[】\]]', '', text).strip()
                    if remainder:
                        sections[current_section].append(remainder)
                else:
                    if current_section not in sections:
                        sections[current_section] = []
                    sections[current_section].append(text)

        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"HWP 파일 읽기 오류: {e}")

        if '_header' in sections and not sections['_header']:
            del sections['_header']

        return sections

    def _check_compressed(self, ole) -> bool:
        """FileHeader에서 압축 플래그를 확인한다."""
        try:
            header = ole.openstream('FileHeader').read()
            if len(header) >= 40:
                properties = struct.unpack_from('<I', header, 36)[0]
                return bool(properties & 0x01)
        except Exception:
            pass
        return True  # 기본적으로 압축된 것으로 가정

    def _extract_text_from_bodytext(self, data: bytes) -> str:
        """HWP5 BodyText 레코드에서 텍스트를 추출한다."""
        text_parts = []
        offset = 0

        while offset < len(data) - 4:
            try:
                # HWP5 레코드 헤더: tag(10bit) + level(10bit) + size(12bit)
                header = struct.unpack_from('<I', data, offset)[0]
                tag_id = header & 0x3FF
                size = (header >> 20) & 0xFFF

                if size == 0xFFF:
                    if offset + 8 <= len(data):
                        size = struct.unpack_from('<I', data, offset + 4)[0]
                        offset += 8
                    else:
                        break
                else:
                    offset += 4

                if offset + size > len(data):
                    break

                record_data = data[offset:offset + size]

                # HWPTAG_PARA_TEXT (tag_id == 67)
                if tag_id == 67 and size >= 2:
                    text = self._decode_para_text(record_data)
                    if text:
                        text_parts.append(text)

                offset += size

            except (struct.error, IndexError):
                break

        if not text_parts:
            # 레코드 파싱 실패 시 UTF-16LE 직접 디코딩 시도
            try:
                raw_text = data.decode('utf-16le', errors='ignore')
                cleaned = ''.join(
                    c for c in raw_text
                    if c.isprintable() or c in '\n\r\t'
                )
                if cleaned.strip():
                    text_parts.append(cleaned)
            except Exception:
                pass

        return '\n'.join(text_parts)

    def _decode_para_text(self, data: bytes) -> str:
        """HWPTAG_PARA_TEXT 레코드에서 텍스트를 디코딩한다."""
        chars = []
        i = 0
        while i < len(data) - 1:
            code = struct.unpack_from('<H', data, i)[0]
            i += 2

            if code == 0:
                break
            # HWP5 제어 문자 (확장 제어)
            elif code < 2:
                continue
            elif code in (2, 3, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23):
                # 확장 제어 문자 - 추가 데이터 건너뛰기
                i += 12 * 2
            elif code == 10:  # 줄바꿈
                chars.append('\n')
            elif code == 13:  # 단락 나눔
                chars.append('\n')
            elif code == 24:  # 하이픈
                chars.append('-')
            elif code == 30:  # 고정폭 빈칸
                chars.append(' ')
            elif code >= 32:
                chars.append(chr(code))

        return ''.join(chars).strip()


class HWPXReader:
    """HWPX(.hwpx) ZIP 기반 문서 파서"""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

    def extract_sections(self) -> OrderedDict:
        """HWPX 문서에서 특허 명세서 섹션을 추출한다."""
        sections = OrderedDict()
        current_section = '_header'
        sections[current_section] = []

        try:
            with zipfile.ZipFile(str(self.file_path), 'r') as zf:
                names = zf.namelist()
                # Contents/sectionN.xml 파일들에서 텍스트 추출
                section_files = sorted(
                    [n for n in names if re.match(r'Contents/section\d+\.xml', n, re.IGNORECASE)],
                )
                if not section_files:
                    # 다른 가능한 경로
                    section_files = sorted(
                        [n for n in names if 'section' in n.lower() and n.endswith('.xml')],
                    )

                text_lines = []
                for sf in section_files:
                    xml_data = zf.read(sf)
                    text = self._extract_text_from_xml(xml_data)
                    text_lines.extend(text)

        except zipfile.BadZipFile:
            raise ValueError("올바른 HWPX(ZIP) 형식이 아닙니다.")
        except Exception as e:
            raise ValueError(f"HWPX 파일 읽기 오류: {e}")

        for line in text_lines:
            text = line.strip()
            if not text:
                continue

            section_id = detect_section(text)
            if section_id == 'claim-item':
                current_section = 'claims'
                if current_section not in sections:
                    sections[current_section] = []
                m = re.search(r'청구항\s*(\d+)', text)
                claim_num = m.group(1) if m else '1'
                remainder = re.sub(r'[【\[][^】\]]*[】\]]', '', text).strip()
                marker = f'청구항 {claim_num}:'
                if remainder:
                    marker += ' ' + remainder
                sections[current_section].append(marker)
            elif section_id:
                current_section = section_id
                if current_section not in sections:
                    sections[current_section] = []
                remainder = re.sub(r'[【\[][^】\]]*[】\]]', '', text).strip()
                if remainder:
                    sections[current_section].append(remainder)
            else:
                if current_section not in sections:
                    sections[current_section] = []
                sections[current_section].append(text)

        if '_header' in sections and not sections['_header']:
            del sections['_header']

        return sections

    def _extract_text_from_xml(self, xml_data: bytes) -> List[str]:
        """HWPX section XML에서 텍스트를 추출한다."""
        lines = []
        try:
            root = etree.fromstring(xml_data)
            # OWPML 네임스페이스 처리
            nsmap = {}
            for prefix, uri in root.nsmap.items():
                if prefix:
                    nsmap[prefix] = uri

            # 모든 텍스트 노드 추출 (단락 단위)
            # hp: 네임스페이스의 t 태그 또는 일반 텍스트
            for elem in root.iter():
                tag = etree.QName(elem.tag).localname if isinstance(elem.tag, str) else ''
                if tag in ('t', 'T'):  # 텍스트 노드
                    if elem.text:
                        lines.append(elem.text)
                elif tag in ('p', 'P', 'run'):
                    # 단락 경계에서 줄바꿈
                    text = ''.join(elem.itertext()).strip()
                    if text and text not in lines:
                        lines.append(text)
        except etree.XMLSyntaxError:
            pass

        return lines


# ============================================================
# HLT XML 생성기
# ============================================================

class HLTGenerator:
    """KIPO 표준 HLT XML 생성기"""

    NSMAP = {None: "http://www.kipo.go.kr/kipo"}

    def generate(self, sections: OrderedDict, output_path: str) -> str:
        """섹션 데이터를 HLT XML 파일로 생성한다."""

        root = etree.Element("patent-document", nsmap=self.NSMAP)
        root.set("lang", "ko")
        root.set("doc-type", "specification")
        root.set("dtd-version", "v1.0")
        root.set("date-created", datetime.now().strftime('%Y%m%d'))

        comment = etree.Comment(
            f" Generated by Patent Format Converter on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} "
        )
        root.insert(0, comment)

        # description 엘리먼트
        description = etree.SubElement(root, "description")

        # 발명의 명칭
        title_elem = etree.SubElement(description, "invention-title")
        if 'invention-title' in sections and sections['invention-title']:
            title_elem.text = ' '.join(sections['invention-title'])
        else:
            title_elem.text = ""

        # 명세서 본문 섹션 순서
        body_sections = [
            ('technical-field', 'technical-field', '기술분야'),
            ('background-art', 'background-art', '발명의 배경이 되는 기술'),
            ('prior-art-documents', 'prior-art-documents', '선행기술문헌'),
            ('disclosure', 'disclosure', '발명의 내용'),
            ('technical-problem', 'technical-problem', '해결하려는 과제'),
            ('technical-solution', 'technical-solution', '과제의 해결 수단'),
            ('advantageous-effects', 'advantageous-effects', '발명의 효과'),
            ('description-of-drawings', 'description-of-drawings', '도면의 간단한 설명'),
            ('detailed-description', 'mode-for-invention', '발명을 실시하기 위한 구체적인 내용'),
            ('reference-signs', 'reference-signs', '부호의 설명'),
        ]

        for section_id, xml_tag, heading_text in body_sections:
            if section_id in sections and sections[section_id]:
                elem = etree.SubElement(description, xml_tag)
                heading = etree.SubElement(elem, "heading")
                heading.text = heading_text

                for para_text in sections[section_id]:
                    if para_text.strip():
                        p = etree.SubElement(elem, "p")
                        p.text = para_text

        # 청구범위
        if 'claims' in sections and sections['claims']:
            claims_elem = etree.SubElement(root, "claims")
            parsed_claims = parse_claims(sections['claims'])
            if parsed_claims:
                for claim_data in parsed_claims:
                    claim = etree.SubElement(claims_elem, "claim")
                    claim.set("id", f"CLM-{claim_data['num']:05d}")
                    claim.set("num", str(claim_data['num']))
                    claim_text = etree.SubElement(claim, "claim-text")
                    claim_text.text = claim_data['text']
            else:
                # 파싱 실패 시 전체 텍스트를 하나의 청구항으로
                claim = etree.SubElement(claims_elem, "claim")
                claim.set("id", "CLM-00001")
                claim.set("num", "1")
                claim_text = etree.SubElement(claim, "claim-text")
                claim_text.text = '\n'.join(sections['claims'])

        # 요약서
        if 'abstract' in sections and sections['abstract']:
            abstract_elem = etree.SubElement(root, "abstract")
            for para_text in sections['abstract']:
                if para_text.strip():
                    p = etree.SubElement(abstract_elem, "p")
                    p.text = para_text

        # 대표도면
        if 'representative-drawing' in sections and sections['representative-drawing']:
            repr_elem = etree.SubElement(root, "representative-drawing")
            for para_text in sections['representative-drawing']:
                if para_text.strip():
                    p = etree.SubElement(repr_elem, "p")
                    p.text = para_text

        # XML 파일 저장
        tree = etree.ElementTree(root)
        output_path = Path(output_path)

        with open(output_path, 'wb') as f:
            tree.write(
                f,
                pretty_print=True,
                xml_declaration=True,
                encoding='UTF-8',
                doctype='<!DOCTYPE patent-document SYSTEM "patent-document-v1-0.dtd">',
            )

        return str(output_path)


# ============================================================
# 메인 변환기 클래스
# ============================================================

class PatentFormatConverter:
    """특허 문서 형식 변환기 메인 클래스"""

    SUPPORTED_EXTENSIONS = {'.docx', '.hwp', '.hwpx'}

    def __init__(self, input_path: str, output_path: Optional[str] = None):
        self.input_path = Path(input_path)

        if not self.input_path.exists():
            raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {input_path}")

        if output_path:
            self.output_path = Path(output_path)
        else:
            self.output_path = self.input_path.with_suffix('.hlt')

        self.file_type = self.input_path.suffix.lower()
        if self.file_type not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"지원하지 않는 파일 형식: {self.file_type}\n"
                f"지원 형식: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}"
            )

    def extract_sections(self) -> OrderedDict:
        """문서에서 섹션을 추출한다 (변환 없이 미리보기용)."""
        return self._read_document()

    def convert(self) -> str:
        """파일 변환을 실행한다."""
        sections = self._read_document()

        generator = HLTGenerator()
        output_file = generator.generate(sections, str(self.output_path))

        return output_file

    def _read_document(self) -> OrderedDict:
        """파일 형식에 맞는 리더로 문서를 읽는다."""
        if self.file_type == '.docx':
            reader = WordReader(str(self.input_path))
            return reader.extract_sections()
        elif self.file_type == '.hwp':
            # HWP5인지 HWPX인지 자동 감지
            if self._is_zip_file():
                reader = HWPXReader(str(self.input_path))
            else:
                reader = HWPReader(str(self.input_path))
            return reader.extract_sections()
        elif self.file_type == '.hwpx':
            reader = HWPXReader(str(self.input_path))
            return reader.extract_sections()
        else:
            raise ValueError(f"지원하지 않는 파일 형식: {self.file_type}")

    def _is_zip_file(self) -> bool:
        """파일이 ZIP 형식(HWPX)인지 확인한다."""
        try:
            with open(self.input_path, 'rb') as f:
                magic = f.read(4)
                return magic[:2] == b'PK'
        except Exception:
            return False


def main():
    """CLI 메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Word/HWP → 한국특허청 HLT 형식 변환',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python patent_format_converter.py 명세서.docx
  python patent_format_converter.py 명세서.hwp -o output.hlt
  python patent_format_converter.py 명세서.hwpx --output 특허문서.hlt

지원 형식:
  - 입력: .docx, .hwp, .hwpx
  - 출력: .hlt (한국특허청 XML 형식)

문서 작성 가이드 (섹션 헤더):
  【발명의 명칭】
  【기술분야】
  【발명의 배경이 되는 기술】
  【해결하려는 과제】
  【과제의 해결 수단】
  【발명의 효과】
  【도면의 간단한 설명】
  【발명을 실시하기 위한 구체적인 내용】
  【부호의 설명】
  【특허청구범위】
  【요약서】
  【대표도면】
        """
    )

    parser.add_argument('input_file', help='변환할 파일 (Word/HWP)')
    parser.add_argument('-o', '--output', help='출력 HLT 파일 경로', default=None)

    args = parser.parse_args()

    try:
        converter = PatentFormatConverter(args.input_file, args.output)
        print(f"입력: {args.input_file}")
        print(f"출력: {converter.output_path}")
        print()

        sections = converter.extract_sections()
        print(f"감지된 섹션: {len(sections)}개")
        for sid, content in sections.items():
            print(f"  [{sid}] {len(content)}개 단락")

        print()
        output = converter.convert()
        print(f"변환 완료: {output}")
        return 0
    except Exception as e:
        print(f"오류: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
