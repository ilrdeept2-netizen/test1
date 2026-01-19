#!/usr/bin/env python3
"""
특허 문서 형식 변환기 (Patent Document Format Converter)
Word/HWP 파일을 한국특허청 HLT 형식으로 변환

Converts Word/HWP files to Korean Patent Office HLT format
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime
from lxml import etree
from typing import Dict, List, Optional

try:
    from docx import Document
    from docx.text.paragraph import Paragraph
    from docx.oxml.text.paragraph import CT_P
    from docx.oxml.table import CT_Tbl
    from docx.table import Table, _Cell
    import olefile
except ImportError as e:
    print(f"오류: 필수 라이브러리 누락 - {e}")
    print("필요한 패키지 설치: pip install -r requirements.txt")
    sys.exit(1)


class PatentSection:
    """특허 명세서 섹션 정의"""

    # 특허 명세서 표준 섹션 (한국 특허청 기준)
    SECTIONS = {
        '발명의명칭': 'invention-title',
        '발명의 명칭': 'invention-title',
        '기술분야': 'technical-field',
        '발명의배경이되는기술': 'background-art',
        '발명의 배경이 되는 기술': 'background-art',
        '배경기술': 'background-art',
        '선행기술문헌': 'prior-art-documents',
        '선행기술': 'prior-art-documents',
        '해결하려는과제': 'disclosure',
        '해결하려는 과제': 'disclosure',
        '과제의해결수단': 'means-for-solving',
        '과제의 해결 수단': 'means-for-solving',
        '해결수단': 'means-for-solving',
        '발명의효과': 'effects',
        '발명의 효과': 'effects',
        '도면의간단한설명': 'brief-description-of-drawings',
        '도면의 간단한 설명': 'brief-description-of-drawings',
        '도면의설명': 'brief-description-of-drawings',
        '발명을실시하기위한구체적인내용': 'detailed-description',
        '발명을 실시하기 위한 구체적인 내용': 'detailed-description',
        '실시예': 'detailed-description',
        '구체적인내용': 'detailed-description',
        '청구범위': 'claims',
        '청구항': 'claims',
        '요약': 'abstract',
    }


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
        # 【 】 또는 [ ] 안의 텍스트 추출
        matches = re.findall(r'[【\[]([^】\]]+)[】\]]', text)
        if matches:
            section_text = matches[0].strip()
            # 공백 제거하여 비교
            section_key = section_text.replace(' ', '')
            if section_key in PatentSection.SECTIONS:
                return PatentSection.SECTIONS[section_key]

        # 일반 헤더 형식 감지 (1., 가., 등)
        for key, value in PatentSection.SECTIONS.items():
            if key in text or text.startswith(key):
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
            # HWP 파일은 OLE 컨테이너
            ole = olefile.OleFileIO(str(self.file_path))

            # HWP 파일 구조에서 텍스트 추출
            # BodyText 스트림에서 텍스트 추출 시도
            streams = ole.listdir()
            text_content = []

            for stream in streams:
                stream_name = '/'.join(stream)
                if 'BodyText' in stream_name or 'Section' in stream_name:
                    try:
                        data = ole.openstream(stream).read()
                        # HWP 텍스트 디코딩 (간단한 방법)
                        # 실제로는 더 복잡한 파싱이 필요할 수 있음
                        text = self._extract_text_from_stream(data)
                        if text:
                            text_content.append(text)
                    except:
                        continue

            ole.close()

            # 추출된 텍스트를 섹션별로 분류
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
            print("기본 텍스트 추출을 시도합니다...")
            sections['header'] = [f"HWP 파일: {self.file_path.name}"]

        return sections

    def _extract_text_from_stream(self, data: bytes) -> str:
        """HWP 스트림에서 텍스트 추출"""
        # 간단한 텍스트 추출 (UTF-16LE 디코딩 시도)
        try:
            text = data.decode('utf-16le', errors='ignore')
            # 제어 문자 제거
            text = ''.join(char for char in text if char.isprintable() or char in '\n\r\t')
            return text
        except:
            try:
                text = data.decode('utf-8', errors='ignore')
                return text
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
        self.nsmap = {
            None: "http://www.kipo.go.kr/kipo2",
            'xsi': "http://www.w3.org/2001/XMLSchema-instance"
        }

    def convert_to_hlt(self, sections: Dict[str, List[str]],
                      output_path: str,
                      metadata: Optional[Dict] = None) -> str:
        """섹션 데이터를 HLT XML로 변환"""

        # 루트 엘리먼트 생성
        root = etree.Element("patent-document", nsmap=self.nsmap)
        root.set("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation",
                "http://www.kipo.go.kr/kipo2 patent-document-v1.dtd")

        # 메타데이터 추가
        if metadata:
            self._add_metadata(root, metadata)
        else:
            self._add_default_metadata(root)

        # 명세서 본문
        spec = etree.SubElement(root, "description")

        # 발명의 명칭
        if 'invention-title' in sections:
            title_elem = etree.SubElement(spec, "invention-title")
            title_elem.text = ' '.join(sections['invention-title'])

        # 각 섹션 추가
        section_order = [
            'technical-field',
            'background-art',
            'prior-art-documents',
            'disclosure',
            'means-for-solving',
            'effects',
            'brief-description-of-drawings',
            'detailed-description'
        ]

        for section_key in section_order:
            if section_key in sections and sections[section_key]:
                section_elem = etree.SubElement(spec, section_key)

                # 각 문단을 <p> 태그로 추가
                for para_text in sections[section_key]:
                    if para_text.strip():
                        para = etree.SubElement(section_elem, "p")
                        para.text = para_text

        # 청구범위
        if 'claims' in sections and sections['claims']:
            claims_elem = etree.SubElement(root, "claims")

            for i, claim_text in enumerate(sections['claims'], 1):
                if claim_text.strip():
                    claim = etree.SubElement(claims_elem, "claim")
                    claim.set("num", str(i))
                    claim_p = etree.SubElement(claim, "claim-text")
                    claim_p.text = claim_text

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
                      encoding='UTF-8')

        return str(output_path)

    def _add_default_metadata(self, root):
        """기본 메타데이터 추가"""
        # 간단한 메타데이터
        comment = etree.Comment(f"Generated by Patent Format Converter on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        root.insert(0, comment)

    def _add_metadata(self, root, metadata: Dict):
        """메타데이터 추가"""
        meta = etree.SubElement(root, "metadata")
        for key, value in metadata.items():
            elem = etree.SubElement(meta, key)
            elem.text = str(value)


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
        if self.file_type not in ['.docx', '.doc', '.hwp']:
            raise ValueError(f"지원하지 않는 파일 형식: {self.file_type}")

    def convert(self) -> str:
        """파일 변환 실행"""
        print(f"입력 파일: {self.input_path}")
        print(f"출력 파일: {self.output_path}")
        print(f"파일 형식: {self.file_type}")

        # 문서 읽기
        print("\n문서 읽기 중...")
        sections = self._read_document()

        print(f"발견된 섹션: {list(sections.keys())}")

        # HLT로 변환
        print("\nHLT 형식으로 변환 중...")
        converter = HLTConverter()
        output_file = converter.convert_to_hlt(sections, str(self.output_path))

        print(f"\n✓ 변환 완료!")
        print(f"출력 파일: {output_file}")
        print(f"\n생성된 HLT 파일을 한국특허문서작성기(K-Editor)에서 열어 확인하세요.")

        return output_file

    def _read_document(self) -> Dict[str, List[str]]:
        """문서 형식에 따라 읽기"""
        if self.file_type == '.docx':
            reader = WordReader(str(self.input_path))
            return reader.extract_text_with_structure()
        elif self.file_type == '.hwp':
            reader = HWPReader(str(self.input_path))
            return reader.extract_text_with_structure()
        elif self.file_type == '.doc':
            # .doc 형식은 .docx로 먼저 변환 필요
            raise NotImplementedError("구형 .doc 형식은 먼저 .docx로 변환해주세요.")
        else:
            raise ValueError(f"지원하지 않는 파일 형식: {self.file_type}")


def main():
    """CLI 메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Word/HWP 파일을 한국특허청 HLT 형식으로 변환',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python patent_format_converter.py 명세서.docx
  python patent_format_converter.py 명세서.hwp -o output.hlt
  python patent_format_converter.py 특허문서.docx --output 특허문서.hlt

지원 형식:
  - 입력: .docx, .hwp
  - 출력: .hlt (한국특허청 XML 형식)

주의사항:
  - 문서는 표준 특허 명세서 구조를 따라야 합니다
  - 섹션 헤더는 【】 또는 [] 안에 표기해주세요
  - 예: 【발명의 명칭】, 【기술분야】, 【청구범위】 등
        """
    )

    parser.add_argument(
        'input_file',
        help='변환할 Word 또는 HWP 파일'
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
        print(f"\n오류 발생: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
