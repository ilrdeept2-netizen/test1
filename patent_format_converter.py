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


class PatentSection:
    """특허 명세서 섹션 정의"""

    # 특허 명세서 표준 섹션 (한국 특허청 기준)
    SECTIONS = {
        '발명의명칭': 'invention-title',
        '발명의 명칭': 'invention-title',
        '발명명칭': 'invention-title',
        '기술분야': 'technical-field',
        '발명의배경이되는기술': 'background-art',
        '발명의 배경이 되는 기술': 'background-art',
        '배경기술': 'background-art',
        '선행기술문헌': 'prior-art-documents',
        '선행기술': 'prior-art-documents',
        '해결하려는과제': 'disclosure',
        '해결하려는 과제': 'disclosure',
        '과제': 'disclosure',
        '과제의해결수단': 'means-for-solving',
        '과제의 해결 수단': 'means-for-solving',
        '해결수단': 'means-for-solving',
        '발명의효과': 'effects',
        '발명의 효과': 'effects',
        '효과': 'effects',
        '도면의간단한설명': 'brief-description-of-drawings',
        '도면의 간단한 설명': 'brief-description-of-drawings',
        '도면의설명': 'brief-description-of-drawings',
        '도면설명': 'brief-description-of-drawings',
        '발명을실시하기위한구체적인내용': 'detailed-description',
        '발명을 실시하기 위한 구체적인 내용': 'detailed-description',
        '실시예': 'detailed-description',
        '구체적인내용': 'detailed-description',
        '상세한설명': 'detailed-description',
        '청구범위': 'claims',
        '청구항': 'claims',
        '요약': 'abstract',
    }


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

        # 모든 페이지에서 텍스트 추출
        full_text = ""
        for page in self.pdf.pages:
            try:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            except:
                continue

        # 줄 단위로 처리
        lines = full_text.split('\n')

        for line in lines:
            text = line.strip()
            if not text:
                continue

            # 섹션 헤더 감지
            section_key = self._detect_section(text)
            if section_key:
                current_section = section_key
                sections[current_section] = []
            else:
                if current_section not in sections:
                    sections[current_section] = []
                sections[current_section].append(text)

        return sections

    def _detect_section(self, text: str) -> Optional[str]:
        """섹션 헤더 감지"""
        # 【 】 또는 [ ] 안의 텍스트 추출
        matches = re.findall(r'[【\[]([^】\]]+)[】\]]', text)
        if matches:
            section_text = matches[0].strip()
            section_key = section_text.replace(' ', '')
            if section_key in PatentSection.SECTIONS:
                return PatentSection.SECTIONS[section_key]

        # 일반 헤더 형식 감지
        for key, value in PatentSection.SECTIONS.items():
            if text.startswith(key) or key in text:
                return value

        return None


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

    def extract_text_with_structure(self) -> Dict[str, List[str]]:
        """구조를 유지하며 텍스트 추출"""
        sections = {}
        current_section = 'header'
        sections[current_section] = []

        for para in self.document.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            # 섹션 헤더 감지
            section_key = self._detect_section(text)
            if section_key:
                current_section = section_key
                sections[current_section] = []
            else:
                if current_section not in sections:
                    sections[current_section] = []
                sections[current_section].append(text)

        return sections

    def _detect_section(self, text: str) -> Optional[str]:
        """섹션 헤더 감지"""
        matches = re.findall(r'[【\[]([^】\]]+)[】\]]', text)
        if matches:
            section_text = matches[0].strip()
            section_key = section_text.replace(' ', '')
            if section_key in PatentSection.SECTIONS:
                return PatentSection.SECTIONS[section_key]

        for key, value in PatentSection.SECTIONS.items():
            if text.startswith(key):
                return value

        return None


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

                section_key = self._detect_section(text)
                if section_key:
                    current_section = section_key
                    sections[current_section] = []
                else:
                    if current_section not in sections:
                        sections[current_section] = []
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

    def _detect_section(self, text: str) -> Optional[str]:
        """섹션 헤더 감지"""
        matches = re.findall(r'[【\[]([^】\]]+)[】\]]', text)
        if matches:
            section_text = matches[0].strip()
            section_key = section_text.replace(' ', '')
            if section_key in PatentSection.SECTIONS:
                return PatentSection.SECTIONS[section_key]

        for key, value in PatentSection.SECTIONS.items():
            if key in text or text.startswith(key):
                return value

        return None


class HLTConverter:
    """HLT 형식 변환기"""

    def __init__(self):
        # 한국특허청 HLT XML 네임스페이스
        self.nsmap = {
            None: "http://www.kipo.go.kr/kipo",
        }

    def convert_to_hlt(self, sections: Dict[str, List[str]],
                      output_path: str,
                      metadata: Optional[Dict] = None) -> str:
        """섹션 데이터를 HLT XML로 변환"""

        # 루트 엘리먼트 생성 (한국특허청 표준 형식)
        root = etree.Element("patent-document", nsmap=self.nsmap)

        # 문서 정보
        doc_info = etree.Comment(f" Generated by Patent Format Converter on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ")
        root.insert(0, doc_info)

        # 명세서 본문
        description = etree.SubElement(root, "description")

        # 발명의 명칭 (필수)
        if 'invention-title' in sections and sections['invention-title']:
            title_elem = etree.SubElement(description, "invention-title")
            title_text = ' '.join(sections['invention-title'])
            title_elem.text = title_text
        else:
            # 기본 제목
            title_elem = etree.SubElement(description, "invention-title")
            title_elem.text = "제목 없음"

        # 명세서 섹션 순서 (한국특허청 기준)
        section_order = [
            ('technical-field', 'technical-field'),
            ('background-art', 'background-art'),
            ('prior-art-documents', 'prior-art-documents'),
            ('disclosure', 'disclosure'),
            ('means-for-solving', 'solution'),
            ('effects', 'advantageous-effects'),
            ('brief-description-of-drawings', 'description-of-drawings'),
            ('detailed-description', 'mode-for-invention'),
        ]

        for section_key, xml_tag in section_order:
            if section_key in sections and sections[section_key]:
                section_elem = etree.SubElement(description, xml_tag)

                # 섹션 제목
                heading = etree.SubElement(section_elem, "heading")
                heading.text = self._get_section_title(section_key)

                # 내용
                for para_text in sections[section_key]:
                    if para_text.strip():
                        para = etree.SubElement(section_elem, "p")
                        para.text = para_text

        # 청구범위
        if 'claims' in sections and sections['claims']:
            claims_elem = etree.SubElement(root, "claims")

            claim_number = 1
            for claim_text in sections['claims']:
                if claim_text.strip():
                    # 청구항 번호 추출 시도
                    match = re.match(r'청구항\s*(\d+)', claim_text)
                    if match:
                        claim_number = int(match.group(1))
                        claim_text = re.sub(r'청구항\s*\d+\s*[:：]?\s*', '', claim_text)

                    claim = etree.SubElement(claims_elem, "claim")
                    claim.set("id", f"CLM-{claim_number:05d}")
                    claim.set("num", str(claim_number))

                    claim_text_elem = etree.SubElement(claim, "claim-text")
                    claim_text_elem.text = claim_text.strip()

                    claim_number += 1

        # 요약
        if 'abstract' in sections and sections['abstract']:
            abstract_elem = etree.SubElement(root, "abstract")
            for para_text in sections['abstract']:
                if para_text.strip():
                    para = etree.SubElement(abstract_elem, "p")
                    para.text = para_text

        # XML 파일 저장
        tree = etree.ElementTree(root)
        output_path = Path(output_path)

        with open(output_path, 'wb') as f:
            tree.write(f,
                      pretty_print=True,
                      xml_declaration=True,
                      encoding='UTF-8',
                      doctype='<!DOCTYPE patent-document SYSTEM "patent-document-v1-0.dtd">')

        return str(output_path)

    def _get_section_title(self, section_key: str) -> str:
        """섹션 키에 해당하는 한글 제목 반환"""
        titles = {
            'technical-field': '기술분야',
            'background-art': '발명의 배경이 되는 기술',
            'prior-art-documents': '선행기술문헌',
            'disclosure': '발명의 내용',
            'means-for-solving': '과제의 해결 수단',
            'effects': '발명의 효과',
            'brief-description-of-drawings': '도면의 간단한 설명',
            'detailed-description': '발명을 실시하기 위한 구체적인 내용',
        }
        return titles.get(section_key, section_key)


class PatentFormatConverter:
    """특허 문서 형식 변환기 메인 클래스"""

    def __init__(self, input_path: str, output_path: Optional[str] = None):
        self.input_path = Path(input_path)

        if not self.input_path.exists():
            raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {input_path}")

        # 출력 경로 설정
        if output_path:
            self.output_path = Path(output_path)
        else:
            self.output_path = self.input_path.with_suffix('.hlt')

        # 파일 확장자 확인
        self.file_type = self.input_path.suffix.lower()
        if self.file_type not in ['.docx', '.doc', '.hwp', '.pdf']:
            raise ValueError(f"지원하지 않는 파일 형식: {self.file_type}\n지원 형식: .docx, .hwp, .pdf")

    def convert(self) -> str:
        """파일 변환 실행"""
        print(f"=" * 70)
        print(f"특허 문서 변환기 - Patent Format Converter")
        print(f"=" * 70)
        print()
        print(f"입력 파일: {self.input_path.name}")
        print(f"파일 형식: {self.file_type}")
        print(f"출력 파일: {self.output_path.name}")
        print()

        # 문서 읽기
        print("📖 문서 읽는 중...")
        sections = self._read_document()

        # 발견된 섹션 출력
        print(f"✓ 발견된 섹션: {len(sections)}개")
        for section_name in sections.keys():
            content_count = len(sections[section_name])
            print(f"  - {section_name}: {content_count}개 항목")
        print()

        # HLT로 변환
        print("🔄 HLT 형식으로 변환 중...")
        converter = HLTConverter()
        output_file = converter.convert_to_hlt(sections, str(self.output_path))

        print()
        print(f"=" * 70)
        print(f"✓ 변환 완료!")
        print(f"=" * 70)
        print()
        print(f"출력 파일: {output_file}")
        print()
        print("다음 단계:")
        print("  1. 생성된 HLT 파일을 K-Editor에서 열기")
        print("  2. 내용 확인 및 수정")
        print("  3. XML 변환 (HLZ 파일 생성)")
        print("  4. 특허청 전자출원")
        print()

        return output_file

    def _read_document(self) -> Dict[str, List[str]]:
        """문서 형식에 따라 읽기"""
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

문서 작성 가이드:
  다음과 같은 섹션 헤더를 사용하세요:
  【발명의 명칭】
  【기술분야】
  【발명의 배경이 되는 기술】
  【해결하려는 과제】
  【과제의 해결 수단】
  【발명의 효과】
  【도면의 간단한 설명】
  【발명을 실시하기 위한 구체적인 내용】
  【청구범위】
  【요약】
        """
    )

    parser.add_argument(
        'input_file',
        help='변환할 파일 (Word/HWP/PDF)'
    )

    parser.add_argument(
        '-o', '--output',
        help='출력 HLT 파일 경로 (기본값: 입력파일명.hlt)',
        default=None
    )

    args = parser.parse_args()

    try:
        converter = PatentFormatConverter(args.input_file, args.output)
        converter.convert()
        return 0
    except Exception as e:
        print()
        print(f"❌ 오류 발생: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
