#!/usr/bin/env python3
"""
특허 문서 변환기 웹 인터페이스
Patent Document Converter Web Interface

API:
  GET  /             - 메인 페이지
  POST /api/analyze  - 파일 업로드 후 섹션 분석 (JSON 응답)
  POST /api/convert  - 편집된 섹션 데이터를 HLT XML로 변환 (파일 다운로드)
  POST /convert      - (레거시) 파일 업로드 후 바로 HLT 다운로드
"""

import os
import sys
import json
import tempfile
import traceback
from pathlib import Path
from collections import OrderedDict

from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename

from patent_format_converter import PatentFormatConverter, HLTGenerator

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

ALLOWED_EXTENSIONS = {'docx', 'hwp', 'hwpx'}
TEMP_DIR = Path(tempfile.gettempdir()) / 'patent_converter'
TEMP_DIR.mkdir(exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """파일을 업로드받아 섹션을 분석하고 JSON으로 반환한다."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '파일이 선택되지 않았습니다'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '파일이 선택되지 않았습니다'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': '지원하지 않는 파일 형식입니다. (.docx, .hwp, .hwpx만 가능)'}), 400

        filename = secure_filename(file.filename)
        if not filename:
            filename = 'uploaded_file' + os.path.splitext(file.filename)[1]

        input_path = TEMP_DIR / filename
        file.save(str(input_path))

        try:
            converter = PatentFormatConverter(str(input_path))
            sections = converter.extract_sections()

            # OrderedDict -> regular dict for JSON serialization
            sections_dict = {}
            for key, value in sections.items():
                sections_dict[key] = value

            return jsonify({
                'filename': file.filename,
                'sections': sections_dict,
            })
        finally:
            # 임시 입력 파일 정리
            try:
                input_path.unlink(missing_ok=True)
            except Exception:
                pass

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'분석 중 오류 발생: {str(e)}'}), 500


@app.route('/api/convert', methods=['POST'])
def api_convert():
    """편집된 섹션 데이터를 받아 HLT XML 파일을 생성하여 반환한다."""
    try:
        data = request.get_json()
        if not data or 'sections' not in data:
            return jsonify({'error': '섹션 데이터가 없습니다'}), 400

        sections = OrderedDict(data['sections'])
        original_filename = data.get('filename', 'patent.hlt')
        base_name = os.path.splitext(original_filename)[0]
        output_filename = base_name + '.hlt'

        output_path = TEMP_DIR / output_filename

        generator = HLTGenerator()
        generator.generate(sections, str(output_path))

        return send_file(
            str(output_path),
            as_attachment=True,
            download_name=output_filename,
            mimetype='application/xml',
        )

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'변환 중 오류 발생: {str(e)}'}), 500


@app.route('/convert', methods=['POST'])
def convert_legacy():
    """레거시 엔드포인트: 파일 업로드 후 바로 HLT 다운로드."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '파일이 선택되지 않았습니다'}), 400

        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({'error': '지원하지 않는 파일 형식입니다.'}), 400

        filename = secure_filename(file.filename)
        if not filename:
            filename = 'uploaded_file' + os.path.splitext(file.filename)[1]

        input_path = TEMP_DIR / filename
        file.save(str(input_path))

        output_filename = input_path.stem + '.hlt'
        output_path = TEMP_DIR / output_filename

        try:
            converter = PatentFormatConverter(str(input_path), str(output_path))
            converter.convert()

            return send_file(
                str(output_path),
                as_attachment=True,
                download_name=output_filename,
                mimetype='application/xml',
            )
        finally:
            try:
                input_path.unlink(missing_ok=True)
            except Exception:
                pass

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'변환 중 오류 발생: {str(e)}'}), 500


@app.route('/api/status')
def status():
    return jsonify({
        'status': 'running',
        'version': '2.0.0',
        'supported_formats': list(ALLOWED_EXTENSIONS),
    })


@app.route('/health')
def health():
    return 'OK', 200


if __name__ == '__main__':
    print("=" * 60)
    print("특허 명세서 변환기 웹 서버 v2.0")
    print("Patent Specification Converter Web Server")
    print("=" * 60)
    print()
    print("  http://localhost:5000")
    print()
    print("지원 형식: .docx, .hwp, .hwpx -> .hlt")
    print("Ctrl+C 로 종료")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5000, debug=True)
