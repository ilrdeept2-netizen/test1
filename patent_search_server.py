"""
선행특허조사 웹 서버 (Flask + HTML 기반)
==========================================
모바일 친화적인 반응형 웹 앱
"""

import os
import json
import tempfile
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

from patent_search_app import (
    PatentSearchApp,
    TextExtractor,
    KeywordExtractor,
    PatentResult
)

app = Flask(__name__)
CORS(app)

# 설정
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 최대 50MB
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

ALLOWED_EXTENSIONS = {'docx', 'doc', 'pdf', 'pptx', 'ppt', 'xlsx', 'xls', 'txt', 'hwp'}


def allowed_file(filename):
    """허용된 파일 형식인지 확인"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """메인 페이지"""
    return render_template('patent_search.html')


@app.route('/api/analyze', methods=['POST'])
def analyze_document():
    """문서 분석 API"""
    try:
        # 파일 확인
        if 'file' not in request.files:
            return jsonify({'error': '파일이 업로드되지 않았습니다.'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': f'지원하지 않는 파일 형식입니다. 지원 형식: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

        # 파일 저장
        filename = secure_filename(file.filename)
        # 한글 파일명 처리
        if not filename or filename == '':
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'txt'
            filename = f'uploaded_file.{ext}'

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            # API 키 (선택사항)
            api_key = request.form.get('api_key', '')

            # 분석 수행
            search_app = PatentSearchApp(kipris_api_key=api_key if api_key else None)
            result = search_app.analyze_document(filepath)

            if result['error']:
                return jsonify({'error': result['error']}), 500

            # 결과 변환
            response_data = {
                'success': True,
                'file_name': file.filename,
                'keywords': result['keywords'][:20],
                'technical_terms': result['technical_terms'][:15],
                'patents': [
                    {
                        'title': p.title,
                        'applicant': p.applicant,
                        'application_number': p.application_number,
                        'application_date': p.application_date,
                        'abstract': p.abstract,
                        'ipc_code': p.ipc_code,
                        'similarity_score': round(p.similarity_score * 100, 1),
                        'kipris_url': p.kipris_url
                    }
                    for p in result['patents']
                ],
                'text_preview': result['extracted_text'][:1000] + '...' if len(result['extracted_text']) > 1000 else result['extracted_text']
            }

            return jsonify(response_data)

        finally:
            # 임시 파일 삭제
            if os.path.exists(filepath):
                os.remove(filepath)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/<format_type>', methods=['POST'])
def export_results(format_type):
    """결과 내보내기 API"""
    try:
        data = request.get_json()

        if format_type == 'txt':
            content = generate_text_report(data)
            return jsonify({'content': content, 'filename': f"{data.get('file_name', 'report')}_특허조사결과.txt"})

        elif format_type == 'json':
            content = json.dumps(data, ensure_ascii=False, indent=2)
            return jsonify({'content': content, 'filename': f"{data.get('file_name', 'report')}_특허조사결과.json"})

        elif format_type == 'csv':
            content = generate_csv_report(data)
            return jsonify({'content': content, 'filename': f"{data.get('file_name', 'report')}_특허조사결과.csv"})

        else:
            return jsonify({'error': '지원하지 않는 형식입니다.'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def generate_text_report(data):
    """텍스트 보고서 생성"""
    lines = []
    lines.append("=" * 60)
    lines.append("📋 선행특허조사 결과 보고서")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"📁 분석 파일: {data.get('file_name', 'N/A')}")
    lines.append("")

    lines.append("🔑 주요 키워드:")
    for i, kw in enumerate(data.get('keywords', [])[:15], 1):
        keyword, count = kw if isinstance(kw, (list, tuple)) else (kw, 0)
        lines.append(f"   {i:2d}. {keyword} ({count}회)")
    lines.append("")

    tech_terms = data.get('technical_terms', [])
    if tech_terms:
        lines.append("🔧 기술 용어:")
        lines.append(f"   {', '.join(tech_terms[:15])}")
        lines.append("")

    lines.append("📜 관련 특허 목록:")
    lines.append("-" * 60)

    for i, p in enumerate(data.get('patents', []), 1):
        lines.append(f"\n{i}. {p.get('title', 'N/A')}")
        lines.append(f"   출원인: {p.get('applicant', 'N/A')}")
        lines.append(f"   출원번호: {p.get('application_number', 'N/A')}")
        lines.append(f"   출원일: {p.get('application_date', 'N/A')}")
        lines.append(f"   IPC: {p.get('ipc_code', 'N/A')}")
        lines.append(f"   유사도: {p.get('similarity_score', 0)}%")
        abstract = p.get('abstract', '')
        lines.append(f"   요약: {abstract[:150]}...")
        lines.append(f"   링크: {p.get('kipris_url', 'N/A')}")

    lines.append("")
    lines.append("=" * 60)

    return '\n'.join(lines)


def generate_csv_report(data):
    """CSV 보고서 생성"""
    lines = ["순위,제목,출원인,출원번호,출원일,IPC,유사도,링크"]

    for i, p in enumerate(data.get('patents', []), 1):
        title = p.get('title', '').replace('"', '""')
        applicant = p.get('applicant', '').replace('"', '""')
        line = f'{i},"{title}","{applicant}",{p.get("application_number", "")},{p.get("application_date", "")},{p.get("ipc_code", "")},{p.get("similarity_score", 0)}%,{p.get("kipris_url", "")}'
        lines.append(line)

    return '\n'.join(lines)


if __name__ == '__main__':
    print("=" * 50)
    print("🔍 선행특허조사 웹 서버")
    print("=" * 50)
    print()
    print("📌 웹 브라우저에서 아래 주소로 접속하세요:")
    print("   http://localhost:5000")
    print()
    print("📌 모바일에서 접속하려면:")
    print("   같은 네트워크의 IP 주소를 사용하세요")
    print("   예: http://192.168.x.x:5000")
    print()
    print("📌 종료하려면 Ctrl+C를 누르세요.")
    print("=" * 50)

    app.run(host='0.0.0.0', port=5000, debug=True)
