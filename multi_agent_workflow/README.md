# 멀티 에이전트 자동화 워크플로우 설계

## 개요

이 프로젝트는 **Claude Agent SDK**를 활용하여 멀티 에이전트 기반 자동화 워크플로우를 구축합니다.
기존의 특허 관련 도구들(특허 형식 변환기, 특허 검색 앱, AI 뉴스 다이제스트)을 AI 에이전트로 통합하여
더 지능적이고 자동화된 워크플로우를 제공합니다.

---

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────────┐
│                        오케스트레이터 에이전트                          │
│              (Orchestrator Agent - 워크플로우 조정)                    │
└────────────────────────────┬────────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  특허 분석      │ │  특허 검색      │ │  문서 처리      │
│  에이전트       │ │  에이전트       │ │  에이전트       │
│  (Patent       │ │  (Patent       │ │  (Document     │
│   Analyzer)    │ │   Searcher)    │ │   Processor)   │
└─────────────────┘ └─────────────────┘ └─────────────────┘
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  리포트 생성    │ │  뉴스 수집      │ │  품질 검증      │
│  에이전트       │ │  에이전트       │ │  에이전트       │
│  (Report       │ │  (News         │ │  (Quality      │
│   Generator)   │ │   Collector)   │ │   Validator)   │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## 에이전트 역할 정의

### 1. 오케스트레이터 에이전트 (Orchestrator Agent)
- **역할**: 전체 워크플로우 조정 및 에이전트 간 통신 관리
- **도구**: 모든 도구 접근 가능
- **책임**:
  - 사용자 요청 분석 및 작업 분배
  - 에이전트 간 의존성 관리
  - 결과 취합 및 최종 응답 생성

### 2. 특허 분석 에이전트 (Patent Analyzer Agent)
- **역할**: 특허 문서 분석 및 핵심 내용 추출
- **도구**: `read`, `grep`, `bash`
- **책임**:
  - 특허 명세서 구조 분석
  - 청구항 해석 및 요약
  - 기술 분야 분류

### 3. 특허 검색 에이전트 (Patent Searcher Agent)
- **역할**: 선행 기술 조사 및 유사 특허 검색
- **도구**: `read`, `bash`, `web_search`
- **책임**:
  - KIPRIS API 연동 검색
  - 키워드 기반 특허 검색
  - 유사도 분석 및 순위화

### 4. 문서 처리 에이전트 (Document Processor Agent)
- **역할**: 다양한 문서 형식 변환 및 처리
- **도구**: `read`, `write`, `bash`
- **책임**:
  - Word/HWP/PDF 파일 처리
  - HLT 형식 변환
  - 문서 구조 표준화

### 5. 리포트 생성 에이전트 (Report Generator Agent)
- **역할**: 분석 결과를 보고서로 작성
- **도구**: `read`, `write`, `edit`
- **책임**:
  - 특허 분석 보고서 생성
  - 선행 기술 조사 보고서 작성
  - 시각화 자료 생성

### 6. 뉴스 수집 에이전트 (News Collector Agent)
- **역할**: AI/특허 관련 최신 뉴스 수집
- **도구**: `bash`, `web_fetch`
- **책임**:
  - RSS 피드 모니터링
  - 뉴스 요약 및 분류
  - 일일 다이제스트 생성

### 7. 품질 검증 에이전트 (Quality Validator Agent)
- **역할**: 출력물 품질 검증 및 오류 수정
- **도구**: `read`, `grep`, `edit`
- **책임**:
  - 형식 검증
  - 내용 일관성 검토
  - 오류 감지 및 수정 제안

---

## 워크플로우 시나리오

### 시나리오 1: 완전 자동화 특허 출원 지원

```
사용자 입력: "발명 아이디어 문서"
    │
    ▼
[오케스트레이터] → 작업 분배
    │
    ├──► [문서 처리] → 문서 파싱 및 구조화
    │
    ├──► [특허 검색] → 선행 기술 조사
    │         │
    │         ▼
    │    [특허 분석] → 유사 특허 분석
    │
    └──► [리포트 생성] → 선행 기술 보고서
              │
              ▼
         [품질 검증] → 최종 검토
              │
              ▼
         최종 출력: 특허 명세서 초안 + 선행 기술 보고서
```

### 시나리오 2: 일일 특허/AI 동향 리포트

```
[스케줄러] 매일 오전 8시 트리거
    │
    ▼
[오케스트레이터] → 병렬 작업 실행
    │
    ├──► [뉴스 수집] → AI 뉴스 수집
    │
    ├──► [특허 검색] → 최신 특허 검색
    │
    └──► [리포트 생성] → 일일 다이제스트 생성
              │
              ▼
         [품질 검증] → 형식 검증
              │
              ▼
         최종 출력: 일일 동향 리포트
```

### 시나리오 3: 특허 침해 분석

```
사용자 입력: "분석 대상 특허번호" + "자사 기술 문서"
    │
    ▼
[오케스트레이터] → 순차 작업 실행
    │
    ├──1. [특허 검색] → 대상 특허 상세 조회
    │
    ├──2. [문서 처리] → 자사 기술 문서 파싱
    │
    ├──3. [특허 분석] → 청구항 대 기술 매칭 분석
    │
    └──4. [리포트 생성] → 침해 분석 보고서
              │
              ▼
         [품질 검증] → 법률 용어 검토
              │
              ▼
         최종 출력: 특허 침해 분석 보고서
```

---

## 기술 스택

| 구성요소 | 기술 |
|---------|------|
| 에이전트 프레임워크 | Claude Agent SDK (Python) |
| 모델 | Claude Opus 4.5 / Sonnet |
| 문서 처리 | python-docx, PyPDF2, olefile |
| 웹 인터페이스 | Streamlit / Flask |
| 데이터 저장 | SQLite / PostgreSQL |
| 스케줄링 | APScheduler |
| API 연동 | KIPRIS API, RSS feeds |

---

## 디렉토리 구조

```
multi_agent_workflow/
├── README.md                    # 이 문서
├── requirements.txt             # Python 의존성
├── config/
│   ├── agents.yaml             # 에이전트 설정
│   ├── workflows.yaml          # 워크플로우 정의
│   └── settings.json           # 전역 설정
├── agents/
│   ├── __init__.py
│   ├── base_agent.py           # 기본 에이전트 클래스
│   ├── orchestrator.py         # 오케스트레이터 에이전트
│   ├── patent_analyzer.py      # 특허 분석 에이전트
│   ├── patent_searcher.py      # 특허 검색 에이전트
│   ├── document_processor.py   # 문서 처리 에이전트
│   ├── report_generator.py     # 리포트 생성 에이전트
│   ├── news_collector.py       # 뉴스 수집 에이전트
│   └── quality_validator.py    # 품질 검증 에이전트
├── workflows/
│   ├── __init__.py
│   ├── patent_application.py   # 특허 출원 워크플로우
│   ├── daily_report.py         # 일일 리포트 워크플로우
│   └── infringement_analysis.py # 침해 분석 워크플로우
├── tools/
│   ├── __init__.py
│   ├── kipris_api.py           # KIPRIS API 클라이언트
│   ├── document_parser.py      # 문서 파서
│   └── report_template.py      # 리포트 템플릿
├── web/
│   ├── app.py                  # 웹 애플리케이션
│   └── templates/
│       └── index.html          # 웹 UI
├── tests/
│   ├── test_agents.py
│   └── test_workflows.py
└── main.py                     # 메인 진입점
```

---

## 다음 단계

1. **환경 설정**: Claude Agent SDK 설치 및 API 키 설정
2. **기본 에이전트 구현**: base_agent.py 작성
3. **개별 에이전트 구현**: 각 역할별 에이전트 구현
4. **워크플로우 구현**: 시나리오별 워크플로우 코드 작성
5. **통합 테스트**: 전체 시스템 테스트
6. **웹 인터페이스**: 사용자 친화적 UI 구현

---

## 참고 자료

- [Claude Agent SDK 공식 문서](https://docs.anthropic.com/claude-agent-sdk)
- [GitHub - claude-agent-sdk-python](https://github.com/anthropics/claude-agent-sdk-python)
- [멀티 에이전트 시스템 설계 패턴](https://www.anthropic.com/research/multi-agent-systems)
