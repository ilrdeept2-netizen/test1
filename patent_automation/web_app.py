# -*- coding: utf-8 -*-
"""
특허 업무 자동화 웹 애플리케이션
Flask 기반 웹 인터페이스
"""

import os
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, send_file
from werkzeug.utils import secure_filename
import tempfile

from .prompts import PatentPrompts
from .ai_service import AIServiceManager, PATENT_SYSTEM_PROMPTS
from .specification_writer import SpecificationWriter, SpecificationSection
from .drawing_generator import DrawingGenerator
from .oa_response import OAResponseHandler
from .claims_writer import ClaimsWriter


def create_app(config=None):
    """Flask 앱 생성"""
    app = Flask(__name__,
                template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                static_folder=os.path.join(os.path.dirname(__file__), 'static'))

    app.secret_key = os.environ.get('SECRET_KEY', 'patent-automation-secret-key-' + str(uuid.uuid4()))

    # 설정
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
    app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

    if config:
        app.config.update(config)

    # AI 서비스 매니저 초기화
    ai_manager = AIServiceManager()

    # 프로젝트 저장소 (세션 기반)
    projects = {}

    def get_project(project_id):
        """프로젝트 가져오기 또는 생성"""
        if project_id not in projects:
            projects[project_id] = {
                'id': project_id,
                'created_at': datetime.now().isoformat(),
                'specification_writer': SpecificationWriter(ai_manager),
                'drawing_generator': DrawingGenerator(ai_manager),
                'oa_handler': OAResponseHandler(ai_manager),
                'claims_writer': ClaimsWriter(ai_manager),
                'context': {},
                'history': []
            }
        return projects[project_id]

    # ============================================
    # 라우트 정의
    # ============================================

    @app.route('/')
    def index():
        """메인 페이지"""
        return render_template('index.html')

    @app.route('/api/project/create', methods=['POST'])
    def create_project():
        """새 프로젝트 생성"""
        project_id = str(uuid.uuid4())[:8]
        project = get_project(project_id)
        return jsonify({
            'success': True,
            'project_id': project_id,
            'message': '프로젝트가 생성되었습니다.'
        })

    @app.route('/api/prompts/categories', methods=['GET'])
    def get_prompt_categories():
        """프롬프트 카테고리 목록"""
        categories = PatentPrompts.get_all_categories()
        return jsonify({
            'success': True,
            'categories': categories
        })

    @app.route('/api/prompts/<category>', methods=['GET'])
    def get_category_prompts(category):
        """카테고리별 프롬프트"""
        prompts = PatentPrompts.get_category_prompts(category)
        return jsonify({
            'success': True,
            'category': category,
            'prompts': prompts
        })

    # ============================================
    # 명세서 작성 API
    # ============================================

    @app.route('/api/specification/write-section', methods=['POST'])
    def write_specification_section():
        """명세서 섹션 작성"""
        data = request.json
        project_id = data.get('project_id', 'default')
        section_name = data.get('section')
        context = data.get('context', '')
        provider = data.get('provider', 'openai')
        additional_prompt = data.get('additional_prompt', '')

        project = get_project(project_id)
        writer = project['specification_writer']

        try:
            section = SpecificationSection[section_name]
            response = writer.write_section(section, context, provider, additional_prompt)

            return jsonify({
                'success': True,
                'section': section_name,
                'content': response.content,
                'tokens_used': response.tokens_used
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

    @app.route('/api/specification/write-all', methods=['POST'])
    def write_all_sections():
        """모든 명세서 섹션 작성"""
        data = request.json
        project_id = data.get('project_id', 'default')
        context = data.get('context', '')
        provider = data.get('provider', 'openai')

        project = get_project(project_id)
        writer = project['specification_writer']

        try:
            results = writer.write_all_sections(context, provider)

            return jsonify({
                'success': True,
                'sections': {k: {'content': v.content, 'tokens': v.tokens_used}
                            for k, v in results.items()}
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

    @app.route('/api/specification/review', methods=['POST'])
    def review_specification():
        """명세서 검토 및 보완"""
        data = request.json
        project_id = data.get('project_id', 'default')
        section_name = data.get('section')
        provider = data.get('provider', 'openai')

        project = get_project(project_id)
        writer = project['specification_writer']

        try:
            section = SpecificationSection[section_name]
            response = writer.review_section(section, provider)

            return jsonify({
                'success': True,
                'review': response.content
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

    @app.route('/api/specification/export', methods=['GET'])
    def export_specification():
        """명세서 내보내기"""
        project_id = request.args.get('project_id', 'default')
        format_type = request.args.get('format', 'text')

        project = get_project(project_id)
        writer = project['specification_writer']

        if format_type == 'json':
            content = writer.export_to_json()
            return jsonify(json.loads(content))
        else:
            content = writer.export_to_text()
            return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}

    # ============================================
    # 도면 API
    # ============================================

    @app.route('/api/drawing/plan', methods=['POST'])
    def plan_drawings():
        """도면 계획 수립"""
        data = request.json
        project_id = data.get('project_id', 'default')
        context = data.get('context', '')
        provider = data.get('provider', 'openai')

        project = get_project(project_id)
        generator = project['drawing_generator']

        try:
            response = generator.plan_drawings(context, provider)

            return jsonify({
                'success': True,
                'plan': response.content
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

    @app.route('/api/drawing/generate', methods=['POST'])
    def generate_drawing():
        """도면 HTML 생성"""
        data = request.json
        project_id = data.get('project_id', 'default')
        drawing_number = data.get('number', 1)
        drawing_info = data.get('info', {})
        context = data.get('context', '')
        provider = data.get('provider', 'openai')

        project = get_project(project_id)
        generator = project['drawing_generator']

        try:
            response = generator.generate_drawing_html(
                drawing_number, drawing_info, context, provider
            )

            return jsonify({
                'success': True,
                'html': response.content
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

    @app.route('/api/drawing/symbols', methods=['POST'])
    def generate_symbol_system():
        """부호체계 생성"""
        data = request.json
        project_id = data.get('project_id', 'default')
        drawings_info = data.get('drawings', [])
        context = data.get('context', '')
        provider = data.get('provider', 'openai')

        project = get_project(project_id)
        generator = project['drawing_generator']

        try:
            response = generator.generate_symbol_system(drawings_info, context, provider)
            symbol_system = generator.get_symbol_system()

            return jsonify({
                'success': True,
                'content': response.content,
                'symbols': symbol_system.to_dict()
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

    # ============================================
    # OA 대응 API
    # ============================================

    @app.route('/api/oa/analyze', methods=['POST'])
    def analyze_rejection():
        """거절이유 분석"""
        data = request.json
        project_id = data.get('project_id', 'default')
        rejection_notice = data.get('rejection_notice', '')
        specification = data.get('specification', '')
        cited_docs = data.get('cited_docs', [])
        provider = data.get('provider', 'openai')

        project = get_project(project_id)
        handler = project['oa_handler']

        try:
            response = handler.analyze_rejection(
                rejection_notice, specification, cited_docs, provider
            )

            return jsonify({
                'success': True,
                'analysis': response.content
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

    @app.route('/api/oa/amend-claim', methods=['POST'])
    def amend_claim():
        """청구항 보정"""
        data = request.json
        project_id = data.get('project_id', 'default')
        claim_number = data.get('claim_number', 1)
        specification = data.get('specification', '')
        rejection_notice = data.get('rejection_notice', '')
        cited_docs = data.get('cited_docs', [])
        provider = data.get('provider', 'openai')

        project = get_project(project_id)
        handler = project['oa_handler']

        try:
            response = handler.draft_amended_claim(
                claim_number, specification, rejection_notice, cited_docs, provider
            )

            return jsonify({
                'success': True,
                'amended_claim': response.content
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

    @app.route('/api/oa/opinion', methods=['POST'])
    def draft_opinion():
        """의견서 작성"""
        data = request.json
        project_id = data.get('project_id', 'default')
        amended_claims = data.get('amended_claims', [])
        specification = data.get('specification', '')
        rejection_notice = data.get('rejection_notice', '')
        cited_docs = data.get('cited_docs', [])
        provider = data.get('provider', 'openai')

        project = get_project(project_id)
        handler = project['oa_handler']

        try:
            response = handler.draft_opinion_statement(
                amended_claims, specification, rejection_notice, cited_docs, provider
            )

            return jsonify({
                'success': True,
                'opinion': response.content
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

    @app.route('/api/oa/compare-claims', methods=['POST'])
    def compare_claims():
        """청구항 비교"""
        data = request.json
        project_id = data.get('project_id', 'default')
        original = data.get('original', '')
        amended = data.get('amended', '')
        provider = data.get('provider', 'openai')

        project = get_project(project_id)
        handler = project['oa_handler']

        try:
            response = handler.compare_claims(original, amended, provider)

            return jsonify({
                'success': True,
                'comparison': response.content
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

    # ============================================
    # 청구항 API
    # ============================================

    @app.route('/api/claims/write', methods=['POST'])
    def write_claims():
        """청구항 작성"""
        data = request.json
        project_id = data.get('project_id', 'default')
        specification = data.get('specification', '')
        symbol_system = data.get('symbol_system', {})
        provider = data.get('provider', 'openai')

        project = get_project(project_id)
        writer = project['claims_writer']

        try:
            response = writer.write_all_claims(specification, symbol_system, provider)

            return jsonify({
                'success': True,
                'claims': response.content,
                'parsed_claims': writer.export_to_json()
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

    @app.route('/api/claims/review', methods=['POST'])
    def review_claims():
        """청구항 검토"""
        data = request.json
        project_id = data.get('project_id', 'default')
        specification = data.get('specification', '')
        provider = data.get('provider', 'openai')

        project = get_project(project_id)
        writer = project['claims_writer']

        try:
            response = writer.review_claims(specification, provider)

            return jsonify({
                'success': True,
                'review': response.content
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

    @app.route('/api/claims/export', methods=['GET'])
    def export_claims():
        """청구항 내보내기"""
        project_id = request.args.get('project_id', 'default')
        format_type = request.args.get('format', 'text')

        project = get_project(project_id)
        writer = project['claims_writer']

        if format_type == 'json':
            content = writer.export_to_json()
            return jsonify(json.loads(content))
        else:
            content = writer.export_to_text()
            return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}

    # ============================================
    # 통합 워크플로우 API
    # ============================================

    @app.route('/api/workflow/full-specification', methods=['POST'])
    def full_specification_workflow():
        """전체 명세서 작성 워크플로우"""
        data = request.json
        project_id = data.get('project_id', 'default')
        invention_info = data.get('invention_info', {})
        inventor_draft = data.get('inventor_draft', '')
        provider = data.get('provider', 'openai')

        project = get_project(project_id)
        spec_writer = project['specification_writer']
        drawing_gen = project['drawing_generator']
        claims_writer = project['claims_writer']

        results = {
            'project_id': project_id,
            'steps': []
        }

        try:
            # 1. 발명 정보 설정
            spec_writer.set_invention_info(
                invention_info.get('title', ''),
                invention_info.get('name', '')
            )
            results['steps'].append({'step': '발명 정보 설정', 'status': 'completed'})

            # 2. 도면 계획
            context = inventor_draft or json.dumps(invention_info, ensure_ascii=False)
            drawing_plan = drawing_gen.plan_drawings(context, provider)
            results['steps'].append({
                'step': '도면 계획',
                'status': 'completed',
                'content': drawing_plan.content
            })

            # 3. 부호체계 생성
            symbol_response = drawing_gen.generate_symbol_system([], context, provider)
            spec_writer.set_symbol_system(drawing_gen.get_symbol_system().to_dict())
            results['steps'].append({
                'step': '부호체계 생성',
                'status': 'completed',
                'content': symbol_response.content
            })

            # 4. 명세서 전체 섹션 작성
            spec_results = spec_writer.write_all_sections(context, provider)
            results['steps'].append({
                'step': '명세서 작성',
                'status': 'completed',
                'sections': list(spec_results.keys())
            })

            # 5. 청구항 작성
            specification_text = spec_writer.export_to_text()
            claims_response = claims_writer.write_all_claims(
                specification_text,
                drawing_gen.get_symbol_system().to_dict(),
                provider
            )
            results['steps'].append({
                'step': '청구항 작성',
                'status': 'completed',
                'content': claims_response.content
            })

            # 6. 최종 명세서
            results['specification'] = spec_writer.export_to_text()
            results['claims'] = claims_writer.export_to_text()
            results['symbol_system'] = drawing_gen.get_symbol_system().to_formatted_text()

            return jsonify({
                'success': True,
                'results': results
            })

        except Exception as e:
            results['error'] = str(e)
            return jsonify({
                'success': False,
                'results': results
            }), 400

    @app.route('/api/workflow/oa-response', methods=['POST'])
    def oa_response_workflow():
        """OA 대응 워크플로우"""
        data = request.json
        project_id = data.get('project_id', 'default')
        specification = data.get('specification', '')
        original_claims = data.get('original_claims', [])
        rejection_notice = data.get('rejection_notice', '')
        cited_docs = data.get('cited_docs', [])
        provider = data.get('provider', 'openai')

        project = get_project(project_id)
        handler = project['oa_handler']

        results = {
            'project_id': project_id,
            'steps': []
        }

        try:
            # 1. 원청구항 설정
            handler.set_original_claims(original_claims)
            results['steps'].append({'step': '원청구항 설정', 'status': 'completed'})

            # 2. 거절이유 분석
            analysis = handler.analyze_rejection(
                rejection_notice, specification, cited_docs, provider
            )
            results['steps'].append({
                'step': '거절이유 분석',
                'status': 'completed',
                'content': analysis.content
            })

            # 3. 청구항 1항 보정
            amended_claim_1 = handler.draft_amended_claim(
                1, specification, rejection_notice, cited_docs, provider
            )
            results['steps'].append({
                'step': '청구항 1항 보정',
                'status': 'completed',
                'content': amended_claim_1.content
            })

            # 4. 의견서 작성
            opinion = handler.draft_opinion_statement(
                [amended_claim_1.content], specification, rejection_notice, cited_docs, provider
            )
            results['steps'].append({
                'step': '의견서 작성',
                'status': 'completed',
                'content': opinion.content
            })

            # 5. 청구항 비교
            if original_claims:
                comparison = handler.compare_claims(
                    original_claims[0], amended_claim_1.content, provider
                )
                results['steps'].append({
                    'step': '청구항 비교',
                    'status': 'completed',
                    'content': comparison.content
                })

            # 6. 최종 결과
            results['amendment'] = handler.export_amendment()
            results['opinion'] = handler.export_opinion()

            return jsonify({
                'success': True,
                'results': results
            })

        except Exception as e:
            results['error'] = str(e)
            return jsonify({
                'success': False,
                'results': results
            }), 400

    # ============================================
    # AI 설정 API
    # ============================================

    @app.route('/api/ai/providers', methods=['GET'])
    def get_ai_providers():
        """사용 가능한 AI 제공자 목록"""
        return jsonify({
            'success': True,
            'providers': [
                {'id': 'openai', 'name': 'OpenAI GPT-4', 'models': ['gpt-4o', 'gpt-4-turbo']},
                {'id': 'anthropic', 'name': 'Anthropic Claude', 'models': ['claude-sonnet-4-20250514', 'claude-3-opus-20240229']},
                {'id': 'google', 'name': 'Google Gemini', 'models': ['gemini-2.0-flash', 'gemini-pro']}
            ]
        })

    @app.route('/api/ai/configure', methods=['POST'])
    def configure_ai():
        """AI 서비스 설정"""
        data = request.json
        provider = data.get('provider')
        api_key = data.get('api_key')
        model = data.get('model')

        try:
            ai_manager.register_service(provider, api_key, model)
            return jsonify({
                'success': True,
                'message': f'{provider} 서비스가 설정되었습니다.'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

    return app


# 개발 서버 실행용
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
