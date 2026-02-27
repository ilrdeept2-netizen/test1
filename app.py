#!/usr/bin/env python3
"""
특허 문서 변환기 웹 인터페이스
Patent Document Converter Web Interface
"""

import os
import sys
from pathlib import Path
from flask import Flask, render_template, request, send_file, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
import tempfile
import traceback

# 변환기 임포트
try:
    from patent_format_converter import PatentFormatConverter, parse_claims, validate_claims
except ImportError:
    print("오류: patent_format_converter.py를 찾을 수 없습니다.")
    sys.exit(1)

app = Flask(__name__)
app.secret_key = 'patent-converter-secret-key-2026'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB 제한

# 업로드 허용 파일 형식
ALLOWED_EXTENSIONS = {'docx', 'hwp', 'pdf'}

# 임시 디렉토리
TEMP_DIR = Path(tempfile.gettempdir()) / 'patent_converter'
TEMP_DIR.mkdir(exist_ok=True)


def allowed_file(filename):
    """허용된 파일 형식 확인"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')


@app.route('/convert', methods=['POST'])
def convert():
    """파일 변환 처리"""
    try:
        # 파일 확인
        if 'file' not in request.files:
            return jsonify({'error': '파일이 선택되지 않았습니다'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': '파일이 선택되지 않았습니다'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': f'지원하지 않는 파일 형식입니다. (.docx, .hwp, .pdf만 가능)'}), 400

        # 안전한 파일명
        filename = secure_filename(file.filename)

        # 임시 파일로 저장
        input_path = TEMP_DIR / filename
        file.save(str(input_path))

        # 출력 파일 경로
        output_filename = input_path.stem + '.hlt'
        output_path = TEMP_DIR / output_filename

        # 변환 실행
        print(f"변환 시작: {input_path} -> {output_path}")
        converter = PatentFormatConverter(str(input_path), str(output_path))
        result_path = converter.convert()

        # 변환된 파일 전송
        return send_file(
            result_path,
            as_attachment=True,
            download_name=output_filename,
            mimetype='application/xml'
        )

    except Exception as e:
        error_msg = f"변환 중 오류 발생: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        return jsonify({'error': error_msg}), 500

    finally:
        # 임시 파일 정리
        try:
            if 'input_path' in dir() and input_path.exists():
                input_path.unlink()
        except Exception:
            pass


@app.route('/preview', methods=['POST'])
def preview():
    """변환 전 섹션 미리보기 (JSON 반환)"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '파일이 선택되지 않았습니다'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': '파일이 선택되지 않았습니다'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': '지원하지 않는 파일 형식입니다. (.docx, .hwp, .pdf만 가능)'}), 400

        filename = secure_filename(file.filename)
        input_path = TEMP_DIR / filename
        file.save(str(input_path))

        try:
            converter = PatentFormatConverter(str(input_path), str(input_path.with_suffix('.hlt')))
            sections = converter.get_sections()

            # 섹션 레이블 매핑 (영문 ID → 한국어 이름)
            SECTION_LABELS = {
                'invention-title': '발명의 명칭',
                'technical-field': '기술분야',
                'background-art': '발명의 배경이 되는 기술',
                'technical-problem': '해결하려는 과제',
                'technical-solution': '과제의 해결 수단',
                'advantageous-effects': '발명의 효과',
                'description-of-drawings': '도면의 간단한 설명',
                'detailed-description': '발명을 실시하기 위한 구체적인 내용',
                'reference-signs': '부호의 설명',
                'claims': '특허청구범위',
                'abstract': '요약',
                'representative-drawing': '대표도면',
            }

            preview_data = []
            for section_id, lines in sections.items():
                label = SECTION_LABELS.get(section_id, section_id)
                preview_data.append({
                    'id': section_id,
                    'label': label,
                    'lines': lines[:5],       # 미리보기는 최대 5줄
                    'total_lines': len(lines),
                })

            # 누락된 필수 섹션 경고
            required = ['invention-title', 'technical-field', 'claims', 'abstract']
            missing = [SECTION_LABELS.get(s, s) for s in required if s not in sections]

            # 청구항 검증
            claim_warnings = []
            if 'claims' in sections:
                parsed = parse_claims(sections['claims'])
                claim_warnings = validate_claims(parsed)

            return jsonify({
                'sections': preview_data,
                'section_count': len(sections),
                'missing_required': missing,
                'claim_warnings': claim_warnings,
                'filename': filename,
            })
        finally:
            if input_path.exists():
                input_path.unlink()

    except Exception as e:
        return jsonify({'error': f'미리보기 오류: {str(e)}'}), 500


@app.route('/api/status')
def status():
    """API 상태 확인"""
    return jsonify({
        'status': 'running',
        'version': '1.1.0',
        'supported_formats': list(ALLOWED_EXTENSIONS)
    })


@app.route('/health')
def health():
    """헬스 체크"""
    return 'OK', 200


if __name__ == '__main__':
    print("=" * 60)
    print("특허 문서 형식 변환기 웹 서버")
    print("Patent Document Format Converter Web Server")
    print("=" * 60)
    print()
    print("서버 주소: http://localhost:5000")
    print("지원 형식: .docx, .hwp -> .hlt")
    print()
    print("서버를 중지하려면 Ctrl+C를 누르세요")
    print("=" * 60)

    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
