"""
선행특허조사 앱 (Prior Art Patent Search Application)
=====================================
다양한 형식의 문서를 업로드하면 관련 특허를 검색해주는 앱

지원 파일 형식: Word(.docx), 한글(.hwp), PDF, PowerPoint(.pptx), Excel(.xlsx), 텍스트(.txt)
"""

import os
import re
import json
import time
import tempfile
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import Counter
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

# 텍스트 추출 라이브러리
try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from pptx import Presentation
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False

try:
    import openpyxl
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from pyhwpx import Hwp
    HWP_AVAILABLE = True
except ImportError:
    HWP_AVAILABLE = False


@dataclass
class PatentResult:
    """특허 검색 결과를 담는 데이터 클래스"""
    title: str
    applicant: str
    application_number: str
    application_date: str
    abstract: str
    ipc_code: str
    similarity_score: float = 0.0
    kipris_url: str = ""


class TextExtractor:
    """다양한 파일 형식에서 텍스트를 추출하는 클래스"""

    @staticmethod
    def extract_from_docx(file_path: str) -> str:
        """Word 문서에서 텍스트 추출"""
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx 라이브러리가 필요합니다. pip install python-docx")

        doc = DocxDocument(file_path)
        text_parts = []

        for paragraph in doc.paragraphs:
            text_parts.append(paragraph.text)

        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text_parts.append(cell.text)

        return '\n'.join(text_parts)

    @staticmethod
    def extract_from_pdf(file_path: str) -> str:
        """PDF에서 텍스트 추출"""
        if not PDF_AVAILABLE:
            raise ImportError("PyPDF2 라이브러리가 필요합니다. pip install PyPDF2")

        text_parts = []
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text_parts.append(page.extract_text() or '')

        return '\n'.join(text_parts)

    @staticmethod
    def extract_from_pptx(file_path: str) -> str:
        """PowerPoint에서 텍스트 추출"""
        if not PPTX_AVAILABLE:
            raise ImportError("python-pptx 라이브러리가 필요합니다. pip install python-pptx")

        prs = Presentation(file_path)
        text_parts = []

        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text_parts.append(shape.text)
                if shape.has_table:
                    for row in shape.table.rows:
                        for cell in row.cells:
                            text_parts.append(cell.text)

        return '\n'.join(text_parts)

    @staticmethod
    def extract_from_excel(file_path: str) -> str:
        """Excel에서 텍스트 추출"""
        if not EXCEL_AVAILABLE:
            raise ImportError("openpyxl 라이브러리가 필요합니다. pip install openpyxl")

        wb = openpyxl.load_workbook(file_path, data_only=True)
        text_parts = []

        for sheet in wb.worksheets:
            for row in sheet.iter_rows():
                for cell in row:
                    if cell.value:
                        text_parts.append(str(cell.value))

        return '\n'.join(text_parts)

    @staticmethod
    def extract_from_txt(file_path: str) -> str:
        """텍스트 파일에서 텍스트 추출"""
        encodings = ['utf-8', 'cp949', 'euc-kr', 'utf-16']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue

        raise ValueError(f"파일 인코딩을 감지할 수 없습니다: {file_path}")

    @staticmethod
    def extract_from_hwp(file_path: str) -> str:
        """한글(HWP) 파일에서 텍스트 추출"""
        if not HWP_AVAILABLE:
            # 대체 방법: olefile 사용
            try:
                import olefile
                import zlib

                ole = olefile.OleFileIO(file_path)

                # HWP 파일의 본문 스트림 읽기
                if ole.exists('BodyText/Section0'):
                    encoded_text = ole.openstream('BodyText/Section0').read()
                    try:
                        # 압축 해제 시도
                        decoded_text = zlib.decompress(encoded_text, -15)
                        # 간단한 텍스트 추출 (완벽하지 않음)
                        text = decoded_text.decode('utf-16-le', errors='ignore')
                        # 제어 문자 제거
                        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
                        return text
                    except:
                        pass

                ole.close()
                return "[HWP 파일 텍스트 추출 실패 - pyhwpx 라이브러리 설치 필요]"

            except ImportError:
                return "[HWP 지원을 위해 olefile 또는 pyhwpx 라이브러리가 필요합니다]"

        hwp = Hwp()
        hwp.open(file_path)
        text = hwp.get_text()
        hwp.close()
        return text

    @classmethod
    def extract(cls, file_path: str) -> str:
        """파일 확장자에 따라 적절한 추출 방법 선택"""
        ext = os.path.splitext(file_path)[1].lower()

        extractors = {
            '.docx': cls.extract_from_docx,
            '.doc': cls.extract_from_docx,  # .doc는 제한적 지원
            '.pdf': cls.extract_from_pdf,
            '.pptx': cls.extract_from_pptx,
            '.ppt': cls.extract_from_pptx,  # .ppt는 제한적 지원
            '.xlsx': cls.extract_from_excel,
            '.xls': cls.extract_from_excel,  # .xls는 제한적 지원
            '.txt': cls.extract_from_txt,
            '.hwp': cls.extract_from_hwp,
        }

        if ext not in extractors:
            raise ValueError(f"지원하지 않는 파일 형식입니다: {ext}")

        return extractors[ext](file_path)


class KeywordExtractor:
    """텍스트에서 핵심 키워드를 추출하는 클래스"""

    # 한국어 불용어 목록
    KOREAN_STOPWORDS = {
        '있다', '하다', '되다', '이다', '것', '수', '등', '및', '또한', '그', '이', '저',
        '무엇', '어떤', '모든', '각', '더', '매우', '너무', '아주', '정말', '진짜',
        '위해', '통해', '따라', '대해', '관한', '의한', '로서', '에서', '으로', '에게',
        '본', '상기', '해당', '이러한', '그러한', '어떠한', '다른', '같은', '동일한',
        '발명', '기술', '방법', '장치', '시스템', '구성', '실시', '예', '도면', '참조',
        '포함', '구비', '형성', '제공', '설치', '연결', '배치', '위치', '상태', '과정',
    }

    # 영어 불용어 목록
    ENGLISH_STOPWORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
        'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been', 'be',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
        'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'it', 'its',
        'which', 'who', 'whom', 'what', 'when', 'where', 'why', 'how', 'all', 'each',
        'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'not',
    }

    @classmethod
    def extract_keywords(cls, text: str, top_n: int = 20) -> List[Tuple[str, int]]:
        """텍스트에서 핵심 키워드 추출"""
        # 텍스트 정규화
        text = text.lower()

        # 한글 단어 추출 (2글자 이상)
        korean_words = re.findall(r'[가-힣]{2,}', text)

        # 영어 단어 추출 (3글자 이상)
        english_words = re.findall(r'[a-z]{3,}', text)

        # 불용어 제거
        korean_words = [w for w in korean_words if w not in cls.KOREAN_STOPWORDS]
        english_words = [w for w in english_words if w not in cls.ENGLISH_STOPWORDS]

        # 단어 빈도 계산
        word_counts = Counter(korean_words + english_words)

        # 상위 N개 키워드 반환
        return word_counts.most_common(top_n)

    @classmethod
    def extract_technical_terms(cls, text: str) -> List[str]:
        """기술 용어 추출 (복합어, 영어 약어 등)"""
        terms = []

        # 영어 약어 (대문자 2-6글자)
        abbreviations = re.findall(r'\b[A-Z]{2,6}\b', text)
        terms.extend(abbreviations)

        # 복합 기술 용어 (영어-숫자 조합)
        tech_patterns = re.findall(r'\b[A-Za-z]+[-_]?\d+[A-Za-z]*\b', text)
        terms.extend(tech_patterns)

        # 한글-영어 복합어
        mixed_terms = re.findall(r'[가-힣]+\s*\([A-Za-z]+\)', text)
        terms.extend(mixed_terms)

        return list(set(terms))


class KIPRISSearcher:
    """KIPRIS (한국특허정보원) API를 사용한 특허 검색"""

    BASE_URL = "http://plus.kipris.or.kr/openapi/rest"

    def __init__(self, api_key: str = None):
        """
        KIPRIS API 초기화

        API 키는 KIPRIS Plus (http://plus.kipris.or.kr)에서 발급받을 수 있습니다.
        API 키가 없으면 데모 모드로 작동합니다.
        """
        self.api_key = api_key or os.environ.get('KIPRIS_API_KEY', '')
        self.demo_mode = not bool(self.api_key)

        if self.demo_mode:
            print("⚠️ KIPRIS API 키가 설정되지 않았습니다. 데모 모드로 작동합니다.")
            print("   실제 특허 검색을 위해서는 KIPRIS Plus에서 API 키를 발급받으세요.")

    def search_patents(self, keywords: List[str], max_results: int = 20) -> List[PatentResult]:
        """키워드로 특허 검색"""
        if self.demo_mode:
            return self._demo_search(keywords, max_results)

        return self._real_search(keywords, max_results)

    def _real_search(self, keywords: List[str], max_results: int) -> List[PatentResult]:
        """실제 KIPRIS API를 사용한 검색"""
        results = []
        query = ' '.join(keywords[:5])  # 상위 5개 키워드 사용

        # URL 인코딩
        encoded_query = urllib.parse.quote(query)

        # API 엔드포인트
        url = f"{self.BASE_URL}/patUtiModInfoSearchSevice/freeSearchInfo"
        params = {
            'word': query,
            'patent': 'true',
            'utility': 'true',
            'numOfRows': str(max_results),
            'pageNo': '1',
            'accessKey': self.api_key
        }

        query_string = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_string}"

        try:
            with urllib.request.urlopen(full_url, timeout=30) as response:
                xml_data = response.read().decode('utf-8')
                results = self._parse_kipris_response(xml_data)
        except Exception as e:
            print(f"KIPRIS API 호출 오류: {e}")
            # 오류 시 데모 데이터 반환
            results = self._demo_search(keywords, max_results)

        return results

    def _parse_kipris_response(self, xml_data: str) -> List[PatentResult]:
        """KIPRIS XML 응답 파싱"""
        results = []

        try:
            root = ET.fromstring(xml_data)
            items = root.findall('.//item')

            for item in items:
                title = item.findtext('inventionTitle', '')
                applicant = item.findtext('applicantName', '')
                app_num = item.findtext('applicationNumber', '')
                app_date = item.findtext('applicationDate', '')
                abstract = item.findtext('astrtCont', '')
                ipc = item.findtext('ipcNumber', '')

                result = PatentResult(
                    title=title,
                    applicant=applicant,
                    application_number=app_num,
                    application_date=app_date,
                    abstract=abstract,
                    ipc_code=ipc,
                    kipris_url=f"http://kpat.kipris.or.kr/kpat/biblioa.do?method=biblioFrame&applno={app_num}"
                )
                results.append(result)

        except ET.ParseError as e:
            print(f"XML 파싱 오류: {e}")

        return results

    def _demo_search(self, keywords: List[str], max_results: int) -> List[PatentResult]:
        """데모 모드 - 샘플 특허 데이터 반환"""
        demo_patents = [
            PatentResult(
                title="인공지능 기반 자연어 처리 시스템 및 방법",
                applicant="삼성전자(주)",
                application_number="10-2023-0012345",
                application_date="2023-01-15",
                abstract="본 발명은 딥러닝 기술을 활용하여 자연어를 처리하고 분석하는 시스템에 관한 것으로, 특히 트랜스포머 아키텍처를 기반으로 한 언어 모델을 이용하여 텍스트의 의미를 파악하고 분류하는 방법을 제공한다.",
                ipc_code="G06F 40/30",
                similarity_score=0.85,
                kipris_url="http://kpat.kipris.or.kr/kpat/biblioa.do?method=biblioFrame&applno=1020230012345"
            ),
            PatentResult(
                title="블록체인 기반 데이터 보안 시스템",
                applicant="(주)카카오",
                application_number="10-2023-0023456",
                application_date="2023-02-20",
                abstract="본 발명은 블록체인 기술을 활용하여 데이터의 무결성과 보안성을 보장하는 시스템에 관한 것으로, 분산 원장 기술을 통해 데이터 위변조를 방지하고 투명한 거래 기록을 유지한다.",
                ipc_code="H04L 9/32",
                similarity_score=0.72,
                kipris_url="http://kpat.kipris.or.kr/kpat/biblioa.do?method=biblioFrame&applno=1020230023456"
            ),
            PatentResult(
                title="IoT 센서 네트워크를 위한 저전력 통신 프로토콜",
                applicant="LG전자(주)",
                application_number="10-2023-0034567",
                application_date="2023-03-10",
                abstract="본 발명은 사물인터넷 환경에서 센서 노드 간의 효율적인 데이터 전송을 위한 저전력 통신 프로토콜에 관한 것으로, 배터리 수명을 연장하면서도 안정적인 데이터 전송을 보장한다.",
                ipc_code="H04W 84/18",
                similarity_score=0.68,
                kipris_url="http://kpat.kipris.or.kr/kpat/biblioa.do?method=biblioFrame&applno=1020230034567"
            ),
            PatentResult(
                title="자율주행 차량의 장애물 인식 장치 및 방법",
                applicant="현대자동차(주)",
                application_number="10-2023-0045678",
                application_date="2023-04-05",
                abstract="본 발명은 라이다와 카메라 센서를 융합하여 자율주행 차량 주변의 장애물을 정확하게 인식하고 분류하는 장치 및 방법에 관한 것이다.",
                ipc_code="G06V 20/56",
                similarity_score=0.65,
                kipris_url="http://kpat.kipris.or.kr/kpat/biblioa.do?method=biblioFrame&applno=1020230045678"
            ),
            PatentResult(
                title="클라우드 컴퓨팅 환경에서의 리소스 최적화 시스템",
                applicant="네이버(주)",
                application_number="10-2023-0056789",
                application_date="2023-05-12",
                abstract="본 발명은 클라우드 환경에서 컴퓨팅 리소스를 동적으로 할당하고 최적화하는 시스템에 관한 것으로, 머신러닝 기반 예측 모델을 사용하여 워크로드를 분석하고 효율적으로 자원을 배분한다.",
                ipc_code="G06F 9/50",
                similarity_score=0.62,
                kipris_url="http://kpat.kipris.or.kr/kpat/biblioa.do?method=biblioFrame&applno=1020230056789"
            ),
        ]

        # 키워드와 관련된 특허 시뮬레이션
        keyword_str = ' '.join(keywords).lower()

        # 키워드 기반 유사도 조정
        for patent in demo_patents:
            score = 0.5  # 기본 점수
            title_lower = patent.title.lower()
            abstract_lower = patent.abstract.lower()

            for keyword in keywords:
                kw = keyword.lower()
                if kw in title_lower:
                    score += 0.1
                if kw in abstract_lower:
                    score += 0.05

            patent.similarity_score = min(score, 0.95)

        # 유사도 순으로 정렬
        demo_patents.sort(key=lambda x: x.similarity_score, reverse=True)

        return demo_patents[:max_results]


class SimilarityAnalyzer:
    """문서와 특허 간의 유사도를 분석하는 클래스"""

    @staticmethod
    def calculate_tfidf_similarity(doc_text: str, patent_text: str) -> float:
        """TF-IDF 기반 유사도 계산 (간단한 구현)"""
        # 단어 추출
        doc_words = set(re.findall(r'[가-힣a-zA-Z]{2,}', doc_text.lower()))
        patent_words = set(re.findall(r'[가-힣a-zA-Z]{2,}', patent_text.lower()))

        if not doc_words or not patent_words:
            return 0.0

        # Jaccard 유사도
        intersection = doc_words & patent_words
        union = doc_words | patent_words

        return len(intersection) / len(union) if union else 0.0

    @staticmethod
    def calculate_keyword_overlap(doc_keywords: List[str], patent: PatentResult) -> float:
        """키워드 중복도 계산"""
        patent_text = f"{patent.title} {patent.abstract}".lower()

        matches = 0
        for keyword in doc_keywords:
            if keyword.lower() in patent_text:
                matches += 1

        return matches / len(doc_keywords) if doc_keywords else 0.0

    @classmethod
    def rank_patents(cls, doc_text: str, doc_keywords: List[str],
                     patents: List[PatentResult]) -> List[PatentResult]:
        """특허 결과에 유사도 점수를 부여하고 순위 결정"""
        for patent in patents:
            patent_text = f"{patent.title} {patent.abstract}"

            # TF-IDF 유사도
            tfidf_score = cls.calculate_tfidf_similarity(doc_text, patent_text)

            # 키워드 중복도
            keyword_score = cls.calculate_keyword_overlap(doc_keywords, patent)

            # 종합 점수 (가중 평균)
            patent.similarity_score = (tfidf_score * 0.4 + keyword_score * 0.6)

        # 유사도 순으로 정렬
        patents.sort(key=lambda x: x.similarity_score, reverse=True)

        return patents


class PatentSearchApp:
    """선행특허조사 앱 메인 클래스"""

    def __init__(self, kipris_api_key: str = None):
        self.text_extractor = TextExtractor()
        self.keyword_extractor = KeywordExtractor()
        self.searcher = KIPRISSearcher(kipris_api_key)
        self.analyzer = SimilarityAnalyzer()

    def analyze_document(self, file_path: str) -> Dict:
        """문서 분석 및 특허 검색 수행"""
        result = {
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'extracted_text': '',
            'keywords': [],
            'technical_terms': [],
            'patents': [],
            'error': None
        }

        try:
            # 1. 텍스트 추출
            print(f"📄 파일에서 텍스트 추출 중: {file_path}")
            result['extracted_text'] = TextExtractor.extract(file_path)

            # 2. 키워드 추출
            print("🔍 키워드 추출 중...")
            keywords = KeywordExtractor.extract_keywords(result['extracted_text'])
            result['keywords'] = keywords

            # 3. 기술 용어 추출
            tech_terms = KeywordExtractor.extract_technical_terms(result['extracted_text'])
            result['technical_terms'] = tech_terms

            # 4. 특허 검색
            print("🔎 관련 특허 검색 중...")
            keyword_list = [kw[0] for kw in keywords[:10]]  # 상위 10개 키워드
            patents = self.searcher.search_patents(keyword_list)

            # 5. 유사도 분석
            print("📊 유사도 분석 중...")
            ranked_patents = self.analyzer.rank_patents(
                result['extracted_text'],
                keyword_list,
                patents
            )
            result['patents'] = ranked_patents

            print(f"✅ 분석 완료! {len(ranked_patents)}개의 관련 특허를 찾았습니다.")

        except Exception as e:
            result['error'] = str(e)
            print(f"❌ 오류 발생: {e}")

        return result

    def format_results(self, analysis_result: Dict) -> str:
        """분석 결과를 보기 좋게 포맷팅"""
        output = []
        output.append("=" * 70)
        output.append("📋 선행특허조사 결과 보고서")
        output.append("=" * 70)
        output.append("")

        # 파일 정보
        output.append(f"📁 분석 파일: {analysis_result['file_name']}")
        output.append("")

        # 추출된 키워드
        output.append("🔑 주요 키워드:")
        for i, (keyword, count) in enumerate(analysis_result['keywords'][:15], 1):
            output.append(f"   {i:2d}. {keyword} ({count}회)")
        output.append("")

        # 기술 용어
        if analysis_result['technical_terms']:
            output.append("🔧 기술 용어/약어:")
            output.append(f"   {', '.join(analysis_result['technical_terms'][:20])}")
            output.append("")

        # 관련 특허
        output.append("📜 관련 특허 목록:")
        output.append("-" * 70)

        for i, patent in enumerate(analysis_result['patents'], 1):
            output.append(f"\n{i}. {patent.title}")
            output.append(f"   출원인: {patent.applicant}")
            output.append(f"   출원번호: {patent.application_number}")
            output.append(f"   출원일: {patent.application_date}")
            output.append(f"   IPC: {patent.ipc_code}")
            output.append(f"   유사도: {patent.similarity_score:.1%}")
            output.append(f"   요약: {patent.abstract[:200]}...")
            output.append(f"   링크: {patent.kipris_url}")

        output.append("")
        output.append("=" * 70)

        return '\n'.join(output)

    def save_report(self, analysis_result: Dict, output_path: str = None):
        """분석 결과를 파일로 저장"""
        if output_path is None:
            base_name = os.path.splitext(analysis_result['file_name'])[0]
            output_path = f"{base_name}_특허조사결과.txt"

        report = self.format_results(analysis_result)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"📝 보고서가 저장되었습니다: {output_path}")
        return output_path

    def export_to_json(self, analysis_result: Dict, output_path: str = None) -> str:
        """분석 결과를 JSON으로 저장"""
        if output_path is None:
            base_name = os.path.splitext(analysis_result['file_name'])[0]
            output_path = f"{base_name}_특허조사결과.json"

        # PatentResult 객체를 딕셔너리로 변환
        export_data = {
            'file_name': analysis_result['file_name'],
            'keywords': analysis_result['keywords'],
            'technical_terms': analysis_result['technical_terms'],
            'patents': [
                {
                    'title': p.title,
                    'applicant': p.applicant,
                    'application_number': p.application_number,
                    'application_date': p.application_date,
                    'abstract': p.abstract,
                    'ipc_code': p.ipc_code,
                    'similarity_score': p.similarity_score,
                    'kipris_url': p.kipris_url
                }
                for p in analysis_result['patents']
            ]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        print(f"📊 JSON 결과가 저장되었습니다: {output_path}")
        return output_path


def main():
    """CLI 모드로 실행"""
    import sys

    print("=" * 50)
    print("🔍 선행특허조사 앱 (Prior Art Search)")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("\n사용법: python patent_search_app.py <파일경로>")
        print("\n지원 파일 형식:")
        print("  - Word: .docx, .doc")
        print("  - 한글: .hwp")
        print("  - PDF: .pdf")
        print("  - PowerPoint: .pptx, .ppt")
        print("  - Excel: .xlsx, .xls")
        print("  - 텍스트: .txt")
        print("\nAPI 키 설정 (선택사항):")
        print("  export KIPRIS_API_KEY='your-api-key'")
        print("\n또는 웹 UI를 사용하려면:")
        print("  streamlit run patent_search_web.py")
        return

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        return

    # 앱 실행
    app = PatentSearchApp()
    result = app.analyze_document(file_path)

    if result['error']:
        print(f"\n❌ 오류 발생: {result['error']}")
        return

    # 결과 출력
    print(app.format_results(result))

    # 결과 저장
    app.save_report(result)
    app.export_to_json(result)


if __name__ == "__main__":
    main()
