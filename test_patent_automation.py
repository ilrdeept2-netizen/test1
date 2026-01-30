#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
특허 업무 자동화 시스템 테스트
"""

import sys
import os
import unittest

# 패키지 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestPrompts(unittest.TestCase):
    """프롬프트 모듈 테스트"""

    def test_prompts_import(self):
        """프롬프트 모듈 임포트 테스트"""
        from patent_automation.prompts import PatentPrompts
        self.assertIsNotNone(PatentPrompts)

    def test_get_all_categories(self):
        """카테고리 조회 테스트"""
        from patent_automation.prompts import PatentPrompts

        categories = PatentPrompts.get_all_categories()
        self.assertIsInstance(categories, dict)
        self.assertIn('specification', categories)
        self.assertIn('claims', categories)
        self.assertIn('oa_response', categories)

    def test_get_prompt(self):
        """프롬프트 조회 테스트"""
        from patent_automation.prompts import PatentPrompts

        prompt = PatentPrompts.get_prompt('SPECIFICATION_SECTIONS')
        self.assertIsInstance(prompt, str)
        self.assertIn('기술분야', prompt)

    def test_build_combined_prompt(self):
        """프롬프트 조합 테스트"""
        from patent_automation.prompts import PatentPrompts

        combined = PatentPrompts.build_combined_prompt(
            ['SPECIFICATION_SECTIONS', 'WRITING_STYLE_TRANSLATION_FRIENDLY'],
            "테스트 컨텍스트"
        )
        self.assertIn('컨텍스트', combined)
        self.assertIn('기술분야', combined)


class TestAIService(unittest.TestCase):
    """AI 서비스 모듈 테스트"""

    def test_ai_service_import(self):
        """AI 서비스 모듈 임포트 테스트"""
        from patent_automation.ai_service import (
            AIServiceManager,
            OpenAIService,
            AnthropicService,
            GoogleAIService
        )
        self.assertIsNotNone(AIServiceManager)
        self.assertIsNotNone(OpenAIService)
        self.assertIsNotNone(AnthropicService)
        self.assertIsNotNone(GoogleAIService)

    def test_ai_service_manager(self):
        """AI 서비스 매니저 테스트"""
        from patent_automation.ai_service import AIServiceManager

        manager = AIServiceManager()
        self.assertEqual(manager.default_provider, 'openai')

    def test_system_prompts(self):
        """시스템 프롬프트 테스트"""
        from patent_automation.ai_service import PATENT_SYSTEM_PROMPTS

        self.assertIn('default', PATENT_SYSTEM_PROMPTS)
        self.assertIn('specification', PATENT_SYSTEM_PROMPTS)
        self.assertIn('claims', PATENT_SYSTEM_PROMPTS)


class TestSpecificationWriter(unittest.TestCase):
    """명세서 작성 모듈 테스트"""

    def test_specification_writer_import(self):
        """명세서 작성 모듈 임포트 테스트"""
        from patent_automation.specification_writer import (
            SpecificationWriter,
            SpecificationSection,
            PatentSpecification
        )
        self.assertIsNotNone(SpecificationWriter)
        self.assertIsNotNone(SpecificationSection)
        self.assertIsNotNone(PatentSpecification)

    def test_specification_sections(self):
        """명세서 섹션 열거형 테스트"""
        from patent_automation.specification_writer import SpecificationSection

        self.assertEqual(SpecificationSection.TECHNICAL_FIELD.value, '기술분야')
        self.assertEqual(SpecificationSection.BACKGROUND.value, '발명의 배경이 되는 기술')
        self.assertEqual(SpecificationSection.EFFECT.value, '발명의 효과')

    def test_patent_specification(self):
        """특허 명세서 데이터 클래스 테스트"""
        from patent_automation.specification_writer import PatentSpecification

        spec = PatentSpecification()
        spec.title = "테스트 발명"
        spec.invention_name = "테스트 발명"

        self.assertEqual(spec.title, "테스트 발명")
        self.assertIsInstance(spec.to_dict(), dict)


class TestDrawingGenerator(unittest.TestCase):
    """도면 생성 모듈 테스트"""

    def test_drawing_generator_import(self):
        """도면 생성 모듈 임포트 테스트"""
        from patent_automation.drawing_generator import (
            DrawingGenerator,
            Drawing,
            SymbolSystem
        )
        self.assertIsNotNone(DrawingGenerator)
        self.assertIsNotNone(Drawing)
        self.assertIsNotNone(SymbolSystem)

    def test_symbol_system(self):
        """부호체계 테스트"""
        from patent_automation.drawing_generator import SymbolSystem

        symbols = SymbolSystem()
        symbols.add_symbol('100', '본체')
        symbols.add_symbol('110', '입력부', parent='100')

        self.assertEqual(symbols.get_symbol('100').name, '본체')
        self.assertEqual(symbols.get_symbol('110').parent_symbol, '100')

    def test_drawing(self):
        """도면 데이터 클래스 테스트"""
        from patent_automation.drawing_generator import Drawing

        drawing = Drawing(
            number=1,
            title='시스템 구성도',
            description='전체 시스템 구성을 나타내는 도면'
        )
        self.assertEqual(drawing.number, 1)
        self.assertEqual(drawing.title, '시스템 구성도')


class TestOAResponse(unittest.TestCase):
    """OA 대응 모듈 테스트"""

    def test_oa_response_import(self):
        """OA 대응 모듈 임포트 테스트"""
        from patent_automation.oa_response import (
            OAResponseHandler,
            RejectionType,
            CitedReference
        )
        self.assertIsNotNone(OAResponseHandler)
        self.assertIsNotNone(RejectionType)
        self.assertIsNotNone(CitedReference)

    def test_rejection_types(self):
        """거절이유 유형 테스트"""
        from patent_automation.oa_response import RejectionType

        self.assertEqual(RejectionType.NOVELTY.value, '신규성')
        self.assertEqual(RejectionType.INVENTIVE_STEP.value, '진보성')
        self.assertEqual(RejectionType.ENABLEMENT.value, '기재불비')

    def test_cited_reference(self):
        """인용문헌 데이터 클래스 테스트"""
        from patent_automation.oa_response import CitedReference

        ref = CitedReference(
            reference_number=1,
            publication_number='KR10-1234567',
            title='테스트 특허'
        )
        self.assertEqual(ref.reference_number, 1)
        self.assertEqual(ref.publication_number, 'KR10-1234567')


class TestClaimsWriter(unittest.TestCase):
    """청구항 작성 모듈 테스트"""

    def test_claims_writer_import(self):
        """청구항 작성 모듈 임포트 테스트"""
        from patent_automation.claims_writer import (
            ClaimsWriter,
            Claim,
            ClaimsSet
        )
        self.assertIsNotNone(ClaimsWriter)
        self.assertIsNotNone(Claim)
        self.assertIsNotNone(ClaimsSet)

    def test_claim(self):
        """청구항 데이터 클래스 테스트"""
        from patent_automation.claims_writer import Claim

        claim = Claim(
            number=1,
            text='테스트 청구항',
            is_independent=True
        )
        self.assertEqual(claim.number, 1)
        self.assertTrue(claim.is_independent)

    def test_claims_set(self):
        """청구항 세트 테스트"""
        from patent_automation.claims_writer import Claim, ClaimsSet

        claims_set = ClaimsSet()
        claims_set.claims.append(Claim(number=1, text='독립항', is_independent=True))
        claims_set.claims.append(Claim(number=2, text='종속항', is_independent=False, depends_on=1))

        independent = claims_set.get_independent_claims()
        dependent = claims_set.get_dependent_claims(1)

        self.assertEqual(len(independent), 1)
        self.assertEqual(len(dependent), 1)


class TestWebApp(unittest.TestCase):
    """웹 앱 테스트"""

    def test_create_app(self):
        """앱 생성 테스트"""
        from patent_automation.web_app import create_app

        app = create_app()
        self.assertIsNotNone(app)

    def test_app_routes(self):
        """앱 라우트 테스트"""
        from patent_automation.web_app import create_app

        app = create_app()
        client = app.test_client()

        # 메인 페이지
        response = client.get('/')
        self.assertEqual(response.status_code, 200)

        # 프롬프트 카테고리
        response = client.get('/api/prompts/categories')
        self.assertEqual(response.status_code, 200)

        # AI 제공자 목록
        response = client.get('/api/ai/providers')
        self.assertEqual(response.status_code, 200)


class TestPackageInit(unittest.TestCase):
    """패키지 초기화 테스트"""

    def test_package_import(self):
        """패키지 임포트 테스트"""
        import patent_automation
        self.assertIsNotNone(patent_automation)
        self.assertEqual(patent_automation.__version__, '1.0.0')

    def test_all_exports(self):
        """모든 내보내기 테스트"""
        from patent_automation import (
            PatentPrompts,
            AIServiceManager,
            SpecificationWriter,
            DrawingGenerator,
            OAResponseHandler,
            ClaimsWriter
        )

        self.assertIsNotNone(PatentPrompts)
        self.assertIsNotNone(AIServiceManager)
        self.assertIsNotNone(SpecificationWriter)
        self.assertIsNotNone(DrawingGenerator)
        self.assertIsNotNone(OAResponseHandler)
        self.assertIsNotNone(ClaimsWriter)


def run_tests():
    """테스트 실행"""
    print("=" * 60)
    print("     특허 업무 자동화 시스템 테스트")
    print("=" * 60)
    print()

    # 테스트 실행
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 테스트 클래스 추가
    suite.addTests(loader.loadTestsFromTestCase(TestPrompts))
    suite.addTests(loader.loadTestsFromTestCase(TestAIService))
    suite.addTests(loader.loadTestsFromTestCase(TestSpecificationWriter))
    suite.addTests(loader.loadTestsFromTestCase(TestDrawingGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestOAResponse))
    suite.addTests(loader.loadTestsFromTestCase(TestClaimsWriter))
    suite.addTests(loader.loadTestsFromTestCase(TestWebApp))
    suite.addTests(loader.loadTestsFromTestCase(TestPackageInit))

    # 테스트 결과
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 60)
    if result.wasSuccessful():
        print("✓ 모든 테스트 통과!")
    else:
        print(f"✗ 실패: {len(result.failures)}, 에러: {len(result.errors)}")
    print("=" * 60)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
