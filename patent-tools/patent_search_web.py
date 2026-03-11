"""
선행특허조사 웹 앱 (Streamlit 기반)
=====================================
사용자 친화적인 웹 인터페이스로 특허 검색
"""

import streamlit as st
import os
import tempfile
import json
from patent_search_app import (
    PatentSearchApp,
    TextExtractor,
    KeywordExtractor,
    PatentResult
)


# 페이지 설정
st.set_page_config(
    page_title="선행특허조사 앱",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .patent-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #1f77b4;
    }
    .similarity-high {
        color: #28a745;
        font-weight: bold;
    }
    .similarity-medium {
        color: #ffc107;
        font-weight: bold;
    }
    .similarity-low {
        color: #dc3545;
        font-weight: bold;
    }
    .keyword-tag {
        display: inline-block;
        background-color: #e9ecef;
        padding: 0.25rem 0.5rem;
        border-radius: 15px;
        margin: 0.2rem;
        font-size: 0.9rem;
    }
    .stProgress > div > div > div > div {
        background-color: #1f77b4;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """세션 상태 초기화"""
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    if 'uploaded_file_name' not in st.session_state:
        st.session_state.uploaded_file_name = None


def render_sidebar():
    """사이드바 렌더링"""
    with st.sidebar:
        st.header("⚙️ 설정")

        # API 키 설정
        st.subheader("KIPRIS API 키")
        api_key = st.text_input(
            "API 키 입력 (선택사항)",
            type="password",
            help="KIPRIS Plus에서 발급받은 API 키를 입력하세요. 미입력 시 데모 모드로 작동합니다."
        )

        if not api_key:
            st.info("💡 데모 모드로 작동 중입니다. 실제 검색을 위해서는 KIPRIS API 키가 필요합니다.")

        st.divider()

        # 검색 설정
        st.subheader("검색 설정")
        max_results = st.slider("최대 검색 결과 수", 5, 50, 20)
        keyword_count = st.slider("추출 키워드 수", 5, 30, 15)

        st.divider()

        # 지원 파일 형식
        st.subheader("📁 지원 파일 형식")
        st.markdown("""
        - **Word**: .docx, .doc
        - **한글**: .hwp
        - **PDF**: .pdf
        - **PowerPoint**: .pptx, .ppt
        - **Excel**: .xlsx, .xls
        - **텍스트**: .txt
        """)

        st.divider()

        # 도움말
        st.subheader("❓ 도움말")
        with st.expander("사용 방법"):
            st.markdown("""
            1. 특허 관련 문서를 업로드합니다.
            2. '분석 시작' 버튼을 클릭합니다.
            3. 자동으로 키워드를 추출하고 유사 특허를 검색합니다.
            4. 결과를 확인하고 필요시 보고서를 다운로드합니다.
            """)

        with st.expander("API 키 발급 방법"):
            st.markdown("""
            1. [KIPRIS Plus](http://plus.kipris.or.kr) 접속
            2. 회원 가입 및 로그인
            3. 'Open API 신청' 메뉴에서 API 키 발급
            4. 발급받은 키를 위 입력란에 입력
            """)

        return {
            'api_key': api_key,
            'max_results': max_results,
            'keyword_count': keyword_count
        }


def render_file_upload():
    """파일 업로드 섹션"""
    st.markdown('<p class="main-header">🔍 선행특허조사 앱</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">특허 관련 문서를 업로드하면 유사한 선행특허를 자동으로 검색합니다</p>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        uploaded_file = st.file_uploader(
            "특허 관련 문서를 업로드하세요",
            type=['docx', 'doc', 'pdf', 'pptx', 'ppt', 'xlsx', 'xls', 'txt', 'hwp'],
            help="발명설명서, 기술문서, 논문 등 특허 관련 자료를 업로드하세요."
        )

    return uploaded_file


def analyze_document(uploaded_file, settings):
    """문서 분석 수행"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    try:
        # 앱 초기화
        app = PatentSearchApp(kipris_api_key=settings['api_key'])

        # 진행 상황 표시
        progress_bar = st.progress(0)
        status_text = st.empty()

        # 1. 텍스트 추출
        status_text.text("📄 문서에서 텍스트 추출 중...")
        progress_bar.progress(20)
        extracted_text = TextExtractor.extract(tmp_path)

        # 2. 키워드 추출
        status_text.text("🔑 키워드 추출 중...")
        progress_bar.progress(40)
        keywords = KeywordExtractor.extract_keywords(extracted_text, settings['keyword_count'])
        tech_terms = KeywordExtractor.extract_technical_terms(extracted_text)

        # 3. 특허 검색
        status_text.text("🔎 관련 특허 검색 중...")
        progress_bar.progress(60)
        keyword_list = [kw[0] for kw in keywords[:10]]
        patents = app.searcher.search_patents(keyword_list, settings['max_results'])

        # 4. 유사도 분석
        status_text.text("📊 유사도 분석 중...")
        progress_bar.progress(80)
        ranked_patents = app.analyzer.rank_patents(extracted_text, keyword_list, patents)

        progress_bar.progress(100)
        status_text.text("✅ 분석 완료!")

        # 결과 저장
        result = {
            'file_name': uploaded_file.name,
            'extracted_text': extracted_text,
            'keywords': keywords,
            'technical_terms': tech_terms,
            'patents': ranked_patents,
            'error': None
        }

        st.session_state.analysis_result = result
        st.session_state.uploaded_file_name = uploaded_file.name

        return result

    except Exception as e:
        st.error(f"❌ 오류 발생: {str(e)}")
        return {'error': str(e)}

    finally:
        # 임시 파일 삭제
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def render_keywords(keywords, tech_terms):
    """키워드 결과 표시"""
    st.subheader("🔑 추출된 키워드")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**주요 키워드 (빈도순)**")
        keyword_html = ""
        for kw, count in keywords[:15]:
            keyword_html += f'<span class="keyword-tag">{kw} ({count})</span>'
        st.markdown(keyword_html, unsafe_allow_html=True)

    with col2:
        st.markdown("**기술 용어/약어**")
        if tech_terms:
            term_html = ""
            for term in tech_terms[:20]:
                term_html += f'<span class="keyword-tag">{term}</span>'
            st.markdown(term_html, unsafe_allow_html=True)
        else:
            st.info("검출된 기술 용어가 없습니다.")


def get_similarity_class(score):
    """유사도에 따른 CSS 클래스 반환"""
    if score >= 0.7:
        return "similarity-high"
    elif score >= 0.4:
        return "similarity-medium"
    else:
        return "similarity-low"


def render_patent_results(patents):
    """특허 검색 결과 표시"""
    st.subheader(f"📜 관련 특허 목록 ({len(patents)}건)")

    # 유사도 필터
    min_similarity = st.slider(
        "최소 유사도 필터",
        0.0, 1.0, 0.0,
        format="%.1f%%",
        help="선택한 유사도 이상의 특허만 표시합니다."
    )

    filtered_patents = [p for p in patents if p.similarity_score >= min_similarity]

    if not filtered_patents:
        st.warning("해당 유사도 기준을 만족하는 특허가 없습니다.")
        return

    for i, patent in enumerate(filtered_patents, 1):
        with st.expander(f"**{i}. {patent.title}** (유사도: {patent.similarity_score:.1%})", expanded=(i <= 3)):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**출원인:** {patent.applicant}")
                st.markdown(f"**출원번호:** {patent.application_number}")
                st.markdown(f"**출원일:** {patent.application_date}")
                st.markdown(f"**IPC 분류:** {patent.ipc_code}")

            with col2:
                similarity_class = get_similarity_class(patent.similarity_score)
                st.markdown(f"<p class='{similarity_class}'>유사도: {patent.similarity_score:.1%}</p>",
                            unsafe_allow_html=True)

                st.link_button("📋 KIPRIS에서 보기", patent.kipris_url)

            st.markdown("**요약:**")
            st.write(patent.abstract[:500] + "..." if len(patent.abstract) > 500 else patent.abstract)


def render_extracted_text(text):
    """추출된 텍스트 표시"""
    with st.expander("📄 추출된 원문 텍스트 보기"):
        st.text_area("원문", text[:5000] + "..." if len(text) > 5000 else text, height=300)


def render_download_section(result):
    """다운로드 섹션"""
    st.subheader("📥 결과 다운로드")

    col1, col2, col3 = st.columns(3)

    # 텍스트 보고서
    with col1:
        report = generate_text_report(result)
        st.download_button(
            label="📝 텍스트 보고서 다운로드",
            data=report,
            file_name=f"{os.path.splitext(result['file_name'])[0]}_특허조사결과.txt",
            mime="text/plain"
        )

    # JSON 결과
    with col2:
        json_data = generate_json_report(result)
        st.download_button(
            label="📊 JSON 데이터 다운로드",
            data=json_data,
            file_name=f"{os.path.splitext(result['file_name'])[0]}_특허조사결과.json",
            mime="application/json"
        )

    # CSV 결과
    with col3:
        csv_data = generate_csv_report(result)
        st.download_button(
            label="📈 CSV 데이터 다운로드",
            data=csv_data,
            file_name=f"{os.path.splitext(result['file_name'])[0]}_특허조사결과.csv",
            mime="text/csv"
        )


def generate_text_report(result):
    """텍스트 형식 보고서 생성"""
    lines = []
    lines.append("=" * 70)
    lines.append("📋 선행특허조사 결과 보고서")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"📁 분석 파일: {result['file_name']}")
    lines.append("")

    lines.append("🔑 주요 키워드:")
    for i, (keyword, count) in enumerate(result['keywords'][:15], 1):
        lines.append(f"   {i:2d}. {keyword} ({count}회)")
    lines.append("")

    if result['technical_terms']:
        lines.append("🔧 기술 용어/약어:")
        lines.append(f"   {', '.join(result['technical_terms'][:20])}")
        lines.append("")

    lines.append("📜 관련 특허 목록:")
    lines.append("-" * 70)

    for i, patent in enumerate(result['patents'], 1):
        lines.append(f"\n{i}. {patent.title}")
        lines.append(f"   출원인: {patent.applicant}")
        lines.append(f"   출원번호: {patent.application_number}")
        lines.append(f"   출원일: {patent.application_date}")
        lines.append(f"   IPC: {patent.ipc_code}")
        lines.append(f"   유사도: {patent.similarity_score:.1%}")
        lines.append(f"   요약: {patent.abstract[:200]}...")
        lines.append(f"   링크: {patent.kipris_url}")

    lines.append("")
    lines.append("=" * 70)

    return '\n'.join(lines)


def generate_json_report(result):
    """JSON 형식 보고서 생성"""
    export_data = {
        'file_name': result['file_name'],
        'keywords': result['keywords'],
        'technical_terms': result['technical_terms'],
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
            for p in result['patents']
        ]
    }
    return json.dumps(export_data, ensure_ascii=False, indent=2)


def generate_csv_report(result):
    """CSV 형식 보고서 생성"""
    lines = ["순위,제목,출원인,출원번호,출원일,IPC,유사도,링크"]

    for i, p in enumerate(result['patents'], 1):
        # CSV 특수문자 처리
        title = p.title.replace('"', '""')
        applicant = p.applicant.replace('"', '""')
        abstract_short = p.abstract[:100].replace('"', '""')

        line = f'{i},"{title}","{applicant}",{p.application_number},{p.application_date},{p.ipc_code},{p.similarity_score:.2%},{p.kipris_url}'
        lines.append(line)

    return '\n'.join(lines)


def main():
    """메인 함수"""
    init_session_state()

    # 사이드바
    settings = render_sidebar()

    # 메인 콘텐츠
    uploaded_file = render_file_upload()

    if uploaded_file:
        st.divider()

        # 분석 시작 버튼
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            analyze_button = st.button("🚀 분석 시작", type="primary", use_container_width=True)

        if analyze_button:
            with st.spinner("분석 중..."):
                result = analyze_document(uploaded_file, settings)

    # 결과 표시
    if st.session_state.analysis_result and not st.session_state.analysis_result.get('error'):
        result = st.session_state.analysis_result

        st.divider()
        st.success(f"✅ '{result['file_name']}' 분석 완료! {len(result['patents'])}개의 관련 특허를 찾았습니다.")

        # 탭 구성
        tab1, tab2, tab3 = st.tabs(["📜 특허 검색 결과", "🔑 키워드 분석", "📄 원문 보기"])

        with tab1:
            render_patent_results(result['patents'])

        with tab2:
            render_keywords(result['keywords'], result['technical_terms'])

        with tab3:
            render_extracted_text(result['extracted_text'])

        st.divider()
        render_download_section(result)

    elif st.session_state.analysis_result and st.session_state.analysis_result.get('error'):
        st.error(f"❌ 분석 중 오류 발생: {st.session_state.analysis_result['error']}")


if __name__ == "__main__":
    main()
