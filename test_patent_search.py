#!/usr/bin/env python3
"""
선행특허조사 앱 테스트 코드
===========================
"""

import os
import sys
import unittest
import tempfile

# 테스트 대상 모듈 임포트
from patent_search_app import (
    TextExtractor,
    KeywordExtractor,
    KIPRISSearcher,
    SimilarityAnalyzer,
    PatentSearchApp,
    PatentResult
)


class TestKeywordExtractor(unittest.TestCase):
    """키워드 추출기 테스트"""

    def test_extract_korean_keywords(self):
        """한글 키워드 추출 테스트"""
        text = "인공지능 기술을 활용한 자연어 처리 시스템입니다. 인공지능 모델을 사용합니다."
        keywords = KeywordExtractor.extract_keywords(text, top_n=5)

        self.assertIsInstance(keywords, list)
        self.assertTrue(len(keywords) > 0)

        # '인공지능'이 상위 키워드에 포함되어야 함
        keyword_words = [kw[0] for kw in keywords]
        self.assertIn('인공지능', keyword_words)

    def test_extract_english_keywords(self):
        """영어 키워드 추출 테스트"""
        text = "The artificial intelligence system uses machine learning for natural language processing."
        keywords = KeywordExtractor.extract_keywords(text, top_n=5)

        self.assertIsInstance(keywords, list)
        self.assertTrue(len(keywords) > 0)

    def test_extract_technical_terms(self):
        """기술 용어 추출 테스트"""
        text = "본 시스템은 AI, IoT, 5G 네트워크를 활용합니다. LSTM-2000 모델을 사용합니다."
        terms = KeywordExtractor.extract_technical_terms(text)

        self.assertIsInstance(terms, list)
        # 대문자 약어가 추출되어야 함
        self.assertTrue(any('AI' in term or 'IoT' in term or '5G' in term for term in terms))

    def test_stopwords_removal(self):
        """불용어 제거 테스트"""
        text = "본 발명은 상기 장치에 대한 것이다."
        keywords = KeywordExtractor.extract_keywords(text, top_n=10)

        keyword_words = [kw[0] for kw in keywords]
        # 불용어는 포함되지 않아야 함
        self.assertNotIn('본', keyword_words)
        self.assertNotIn('상기', keyword_words)


class TestKIPRISSearcher(unittest.TestCase):
    """KIPRIS 검색기 테스트"""

    def test_demo_mode_initialization(self):
        """데모 모드 초기화 테스트"""
        searcher = KIPRISSearcher()  # API 키 없이 초기화
        self.assertTrue(searcher.demo_mode)

    def test_demo_search(self):
        """데모 검색 테스트"""
        searcher = KIPRISSearcher()
        keywords = ['인공지능', '자연어', '처리']
        results = searcher.search_patents(keywords, max_results=5)

        self.assertIsInstance(results, list)
        self.assertTrue(len(results) > 0)

        # 결과가 PatentResult 객체인지 확인
        for result in results:
            self.assertIsInstance(result, PatentResult)
            self.assertTrue(hasattr(result, 'title'))
            self.assertTrue(hasattr(result, 'applicant'))
            self.assertTrue(hasattr(result, 'similarity_score'))


class TestSimilarityAnalyzer(unittest.TestCase):
    """유사도 분석기 테스트"""

    def test_tfidf_similarity(self):
        """TF-IDF 유사도 계산 테스트"""
        doc1 = "인공지능 기반 자연어 처리 시스템"
        doc2 = "자연어 처리를 위한 인공지능 모델"

        similarity = SimilarityAnalyzer.calculate_tfidf_similarity(doc1, doc2)

        self.assertIsInstance(similarity, float)
        self.assertGreaterEqual(similarity, 0.0)
        self.assertLessEqual(similarity, 1.0)

    def test_keyword_overlap(self):
        """키워드 중복도 테스트"""
        keywords = ['인공지능', '자연어', '처리']
        patent = PatentResult(
            title="인공지능 기반 시스템",
            applicant="테스트",
            application_number="10-2023-0000001",
            application_date="2023-01-01",
            abstract="이 시스템은 인공지능을 활용하여 자연어를 처리합니다.",
            ipc_code="G06F"
        )

        overlap = SimilarityAnalyzer.calculate_keyword_overlap(keywords, patent)

        self.assertIsInstance(overlap, float)
        self.assertGreater(overlap, 0.0)  # 겹치는 키워드가 있어야 함

    def test_patent_ranking(self):
        """특허 순위 정렬 테스트"""
        doc_text = "인공지능 자연어 처리 시스템"
        keywords = ['인공지능', '자연어', '처리']

        patents = [
            PatentResult(
                title="블록체인 시스템",
                applicant="회사A",
                application_number="10-2023-0000001",
                application_date="2023-01-01",
                abstract="블록체인 기반 데이터 보안",
                ipc_code="H04L"
            ),
            PatentResult(
                title="인공지능 자연어 분석",
                applicant="회사B",
                application_number="10-2023-0000002",
                application_date="2023-01-02",
                abstract="인공지능을 활용한 자연어 처리 방법",
                ipc_code="G06F"
            ),
        ]

        ranked = SimilarityAnalyzer.rank_patents(doc_text, keywords, patents)

        # 두 번째 특허가 더 높은 순위여야 함
        self.assertEqual(ranked[0].application_number, "10-2023-0000002")
        self.assertGreater(ranked[0].similarity_score, ranked[1].similarity_score)


class TestTextExtractor(unittest.TestCase):
    """텍스트 추출기 테스트"""

    def test_txt_extraction(self):
        """텍스트 파일 추출 테스트"""
        # 임시 텍스트 파일 생성
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("테스트 문서입니다. 인공지능 특허 관련 내용.")
            tmp_path = f.name

        try:
            text = TextExtractor.extract(tmp_path)
            self.assertIn("인공지능", text)
            self.assertIn("특허", text)
        finally:
            os.remove(tmp_path)

    def test_unsupported_format(self):
        """지원하지 않는 형식 테스트"""
        with self.assertRaises(ValueError):
            TextExtractor.extract("test.unknown")


class TestPatentSearchApp(unittest.TestCase):
    """메인 앱 테스트"""

    def test_app_initialization(self):
        """앱 초기화 테스트"""
        app = PatentSearchApp()
        self.assertIsNotNone(app.text_extractor)
        self.assertIsNotNone(app.keyword_extractor)
        self.assertIsNotNone(app.searcher)
        self.assertIsNotNone(app.analyzer)

    def test_analyze_txt_document(self):
        """텍스트 문서 분석 테스트"""
        # 임시 텍스트 파일 생성
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("""
            본 발명은 인공지능 기반 자연어 처리 시스템에 관한 것이다.
            딥러닝 기술을 활용하여 텍스트를 분석하고 분류하는 방법을 제공한다.
            특히 트랜스포머 아키텍처를 사용하여 높은 정확도를 달성한다.
            """)
            tmp_path = f.name

        try:
            app = PatentSearchApp()
            result = app.analyze_document(tmp_path)

            self.assertIsNone(result['error'])
            self.assertTrue(len(result['keywords']) > 0)
            self.assertTrue(len(result['patents']) > 0)
            self.assertIn('딥러닝', result['extracted_text'])
        finally:
            os.remove(tmp_path)

    def test_format_results(self):
        """결과 포맷팅 테스트"""
        app = PatentSearchApp()

        result = {
            'file_name': 'test.txt',
            'keywords': [('인공지능', 5), ('딥러닝', 3)],
            'technical_terms': ['AI', 'NLP'],
            'patents': [
                PatentResult(
                    title="테스트 특허",
                    applicant="테스트 회사",
                    application_number="10-2023-0000001",
                    application_date="2023-01-01",
                    abstract="테스트 요약",
                    ipc_code="G06F",
                    similarity_score=0.85,
                    kipris_url="http://test.com"
                )
            ]
        }

        formatted = app.format_results(result)

        self.assertIn("선행특허조사 결과 보고서", formatted)
        self.assertIn("인공지능", formatted)
        self.assertIn("테스트 특허", formatted)


class TestIntegration(unittest.TestCase):
    """통합 테스트"""

    def test_full_workflow(self):
        """전체 워크플로우 테스트"""
        # 1. 샘플 문서 생성
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("""
            발명의 명칭: 인공지능 기반 문서 분류 시스템

            기술 분야:
            본 발명은 인공지능(AI)과 자연어처리(NLP) 기술을 활용한
            문서 자동 분류 시스템에 관한 것이다.

            배경 기술:
            기존의 문서 분류 시스템은 규칙 기반으로 작동하여 새로운 유형의
            문서를 처리하는 데 한계가 있었다.

            발명의 내용:
            본 발명은 딥러닝 기반의 BERT 모델을 활용하여 문서의 의미를
            파악하고 자동으로 분류하는 시스템을 제공한다.
            """)
            tmp_path = f.name

        try:
            # 2. 앱 실행
            app = PatentSearchApp()
            result = app.analyze_document(tmp_path)

            # 3. 결과 검증
            self.assertIsNone(result['error'])

            # 키워드 추출 확인
            keywords = [kw[0] for kw in result['keywords']]
            self.assertTrue(any('문서' in kw or '분류' in kw for kw in keywords))

            # 특허 검색 결과 확인
            self.assertTrue(len(result['patents']) > 0)

            # 4. 보고서 생성 확인
            report = app.format_results(result)
            self.assertIn("선행특허조사", report)

        finally:
            os.remove(tmp_path)


def run_tests():
    """테스트 실행"""
    print("=" * 60)
    print("🧪 선행특허조사 앱 테스트")
    print("=" * 60)
    print()

    # 테스트 스위트 생성
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 테스트 클래스 추가
    suite.addTests(loader.loadTestsFromTestCase(TestKeywordExtractor))
    suite.addTests(loader.loadTestsFromTestCase(TestKIPRISSearcher))
    suite.addTests(loader.loadTestsFromTestCase(TestSimilarityAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestTextExtractor))
    suite.addTests(loader.loadTestsFromTestCase(TestPatentSearchApp))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 60)
    if result.wasSuccessful():
        print("✅ 모든 테스트 통과!")
    else:
        print(f"❌ 실패: {len(result.failures)}개, 오류: {len(result.errors)}개")
    print("=" * 60)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
