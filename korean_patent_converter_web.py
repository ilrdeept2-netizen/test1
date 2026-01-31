#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
한국특허서식 변환기 웹 애플리케이션
Korean Patent Format Converter - Web Application

HWP, DOCX, PDF 파일을 한국특허청 HLT 형식으로 변환하는 웹 서비스
iLovePDF 스타일의 사용자 친화적 인터페이스 제공
"""

import os
import sys
import re
import uuid
import shutil
import tempfile
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
from lxml import etree

# 필수 라이브러리
try:
    from docx import Document
    import olefile
    from PyPDF2 import PdfReader
except ImportError as e:
    print(f"오류: 필수 라이브러리 누락 - {e}")
    print("필요한 패키지 설치: pip install python-docx PyPDF2 olefile lxml flask flask-cors")
    sys.exit(1)


# ============================================================================
# 특허 문서 처리 클래스들
# ============================================================================

class PatentSection:
    """특허 명세서 섹션 정의"""

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
        '특허문헌': 'prior-art-documents',
        '비특허문헌': 'prior-art-documents',
        '해결하려는과제': 'disclosure',
        '해결하려는 과제': 'disclosure',
        '과제': 'disclosure',
        '발명이해결하고자하는과제': 'disclosure',
        '발명이 해결하고자 하는 과제': 'disclosure',
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
        '특허청구범위': 'claims',
        '요약': 'abstract',
        '요약서': 'abstract',
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
        self.nsmap = {
            None: "http://www.kipo.go.kr/kipo",
        }

    def convert_to_hlt(self, sections: Dict[str, List[str]],
                      output_path: str,
                      metadata: Optional[Dict] = None) -> str:
        """섹션 데이터를 HLT XML로 변환"""

        root = etree.Element("patent-document", nsmap=self.nsmap)

        doc_info = etree.Comment(f" Generated by Korean Patent Converter Web on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ")
        root.insert(0, doc_info)

        description = etree.SubElement(root, "description")

        if 'invention-title' in sections and sections['invention-title']:
            title_elem = etree.SubElement(description, "invention-title")
            title_text = ' '.join(sections['invention-title'])
            title_elem.text = title_text
        else:
            title_elem = etree.SubElement(description, "invention-title")
            title_elem.text = "제목 없음"

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

                heading = etree.SubElement(section_elem, "heading")
                heading.text = self._get_section_title(section_key)

                for para_text in sections[section_key]:
                    if para_text.strip():
                        para = etree.SubElement(section_elem, "p")
                        para.text = para_text

        if 'claims' in sections and sections['claims']:
            claims_elem = etree.SubElement(root, "claims")

            claim_number = 1
            for claim_text in sections['claims']:
                if claim_text.strip():
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

        if 'abstract' in sections and sections['abstract']:
            abstract_elem = etree.SubElement(root, "abstract")
            for para_text in sections['abstract']:
                if para_text.strip():
                    para = etree.SubElement(abstract_elem, "p")
                    para.text = para_text

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


# ============================================================================
# Flask 웹 애플리케이션
# ============================================================================

app = Flask(__name__)
CORS(app)

# 설정
UPLOAD_FOLDER = tempfile.mkdtemp(prefix='patent_converter_')
ALLOWED_EXTENSIONS = {'hwp', 'docx', 'doc', 'pdf'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# 임시 파일 저장소
converted_files = {}


def allowed_file(filename):
    """허용된 파일 확장자 확인"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def cleanup_old_files():
    """오래된 임시 파일 정리 (1시간 이상 된 파일)"""
    while True:
        try:
            current_time = time.time()
            for file_id, file_info in list(converted_files.items()):
                if current_time - file_info.get('created', 0) > 3600:  # 1시간
                    try:
                        if os.path.exists(file_info.get('path', '')):
                            os.remove(file_info['path'])
                        del converted_files[file_id]
                    except:
                        pass
            time.sleep(300)  # 5분마다 정리
        except:
            pass


# 백그라운드 정리 스레드 시작
cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()


@app.route('/')
def index():
    """메인 페이지"""
    return render_template('patent_converter.html')


@app.route('/api/convert', methods=['POST'])
def convert_file():
    """파일 변환 API"""
    try:
        # 파일 확인
        if 'file' not in request.files:
            return jsonify({'error': '파일이 업로드되지 않았습니다.'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': '지원하지 않는 파일 형식입니다. HWP, DOCX, PDF 파일만 가능합니다.'}), 400

        # 파일 저장
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_{filename}")
        file.save(input_path)

        try:
            # 파일 확장자에 따라 리더 선택
            ext = os.path.splitext(filename)[1].lower()

            if ext == '.docx':
                reader = WordReader(input_path)
            elif ext == '.hwp':
                reader = HWPReader(input_path)
            elif ext == '.pdf':
                reader = PDFReader(input_path)
            elif ext == '.doc':
                return jsonify({'error': '구형 .doc 형식은 먼저 .docx로 변환해주세요.'}), 400
            else:
                return jsonify({'error': f'지원하지 않는 파일 형식: {ext}'}), 400

            # 텍스트 추출
            sections = reader.extract_text_with_structure()

            # HLT 변환
            output_filename = os.path.splitext(filename)[0] + '.hlt'
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_{output_filename}")

            converter = HLTConverter()
            converter.convert_to_hlt(sections, output_path)

            # 원본 파일 삭제
            if os.path.exists(input_path):
                os.remove(input_path)

            # 변환된 파일 정보 저장
            converted_files[file_id] = {
                'path': output_path,
                'filename': output_filename,
                'created': time.time()
            }

            return jsonify({
                'success': True,
                'message': '변환 완료',
                'download_url': f'/api/download/{file_id}',
                'filename': output_filename
            })

        except Exception as e:
            # 오류 시 임시 파일 정리
            if os.path.exists(input_path):
                os.remove(input_path)
            raise e

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<file_id>')
def download_file(file_id):
    """변환된 파일 다운로드"""
    try:
        if file_id not in converted_files:
            return jsonify({'error': '파일을 찾을 수 없습니다. 다시 변환해주세요.'}), 404

        file_info = converted_files[file_id]
        file_path = file_info['path']
        filename = file_info['filename']

        if not os.path.exists(file_path):
            return jsonify({'error': '파일이 만료되었습니다. 다시 변환해주세요.'}), 404

        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/xml'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health_check():
    """헬스 체크"""
    return jsonify({'status': 'healthy', 'service': 'Korean Patent Converter'})


def main():
    """메인 함수"""
    import argparse

    # 환경변수에서 PORT 읽기 (클라우드 배포용)
    default_port = int(os.environ.get('PORT', 5000))

    parser = argparse.ArgumentParser(description='한국특허서식 변환기 웹 서버')
    parser.add_argument('-p', '--port', type=int, default=default_port, help='포트 번호 (기본값: 5000)')
    parser.add_argument('-H', '--host', default='0.0.0.0', help='호스트 (기본값: 0.0.0.0)')
    parser.add_argument('-d', '--debug', action='store_true', help='디버그 모드')

    args = parser.parse_args()

    print()
    print("=" * 60)
    print("  한국특허서식 변환기 웹 서버")
    print("  Korean Patent Format Converter - Web Server")
    print("=" * 60)
    print()
    print(f"  서버 주소: http://localhost:{args.port}")
    print()
    print("  지원 형식:")
    print("    - 입력: HWP, DOCX, PDF")
    print("    - 출력: HLT (한국특허청 XML 형식)")
    print()
    print("  종료하려면 Ctrl+C를 누르세요.")
    print()
    print("=" * 60)
    print()

    try:
        app.run(host=args.host, port=args.port, debug=args.debug)
    finally:
        # 종료 시 임시 폴더 정리
        try:
            shutil.rmtree(UPLOAD_FOLDER, ignore_errors=True)
        except:
            pass


if __name__ == '__main__':
    main()
