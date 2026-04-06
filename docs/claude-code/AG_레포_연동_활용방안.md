# AntiGravity(AG)에서 이 레포 활용방안 정리

> 작성일: 2026-04-06 | 레포 구조 정리 후 AG 연동 전략

---

## 1. 레포 구조와 AG 활용 매핑

이 레포(`test1`)는 **5개 주요 영역**으로 구성되어 있으며, 각각 AG에서 다른 방식으로 활용 가능합니다.

| 레포 영역 | AG 활용 시나리오 | 추천 모델 |
|-----------|-----------------|-----------|
| `patent-tools/` | 특허 도구 기능 확장/디버깅 | Claude Opus 4.6 |
| `tools/` | 유틸리티 개선, 새 도구 추가 | Claude Sonnet 4.6 |
| `docs/claude-code/` | 가이드 참조하며 Claude Code 설정 | Gemini 3.1 Pro |
| `docs/research/` | 리서치 문서 기반 후속 분석 | Gemini 3.1 Pro (High) |
| `docs/personal/` | 개인 메모 업데이트 | Gemini 3 Flash |

---

## 2. AG 워크스페이스에서 레포 활용법

### 2-1. 레포 클론 후 AG에서 바로 작업

```bash
# AG 터미널에서
git clone https://github.com/ilrdeept2-netizen/test1.git
cd test1
```

AG는 로컬 코드베이스를 **100만 토큰 컨텍스트**로 인식하므로, 레포 전체를 올려두면 파일 간 관계를 파악하며 작업 가능합니다.

### 2-2. AG 에이전트에게 레포 구조 활용 지시

AG 대화창에서 다음과 같이 지시하면 효과적입니다:

```
이 레포의 docs/research/ 폴더에 있는 AI 관련 분석 문서들을 참고해서,
최신 AI 트렌드와 비교 분석해줘.
```

```
patent-tools/patent_format_converter.py를 분석하고,
HWP 파일 지원을 개선할 방안을 제안해줘.
```

---

## 3. 주요 활용 시나리오

### 시나리오 1: 특허 도구 고도화

AG의 Claude Opus를 활용해 `patent-tools/`의 코드를 개선합니다.

| 작업 | 방법 |
|------|------|
| HLT 변환 정확도 개선 | `patent_format_converter.py` 분석 → 엣지 케이스 수정 |
| 선행특허 검색 고도화 | `patent_search_app.py`에 필터링/정렬 기능 추가 |
| 웹 UI 개선 | `templates/index.html` + `app.py` 리팩토링 |
| 테스트 보강 | `tests/` 폴더에 새 테스트 케이스 추가 |

**AG 프롬프트 예시:**
```
patent-tools/tests/test_patent_converter.py의 테스트 커버리지를 분석하고,
누락된 엣지 케이스에 대한 테스트를 추가해줘.
patent_format_converter.py의 실제 로직을 참고해서 작성해.
```

### 시나리오 2: 리서치 문서 기반 후속 작업

`docs/research/`의 기존 분석을 AG의 대용량 컨텍스트로 확장합니다.

| 기존 문서 | AG 후속 작업 |
|-----------|-------------|
| `AI_GPU_커널_최적화_심층분석.md` | 최신 GPU 아키텍처와 비교 업데이트 |
| `hanwha-solution-capital-increase.md` | 최근 주가/실적 반영한 후속 분석 |
| `이란전쟁_유가_TACO_시나리오_분석.md` | 최신 지정학 상황 반영 시나리오 갱신 |
| `바이브코딩_도구_총정리_2026.md` | 신규 도구 추가 및 비교표 업데이트 |

**AG 프롬프트 예시:**
```
docs/research/바이브코딩_도구_총정리_2026.md를 읽고,
2026년 4월 기준으로 새로 나온 바이브코딩 도구가 있으면 추가해줘.
```

### 시나리오 3: Claude Code 가이드 실시간 적용

`docs/claude-code/`의 가이드를 AG에서 바로 참조하며 설정합니다.

```
docs/claude-code/Claude_Code_플러그인_MCP_연동_정리.md를 참고해서,
현재 .mcp.json 설정을 검토하고 개선 사항을 제안해줘.
```

### 시나리오 4: 새 유틸리티 도구 개발

`tools/` 폴더에 새로운 도구를 AG에서 빠르게 프로토타이핑합니다.

- 기존 `pdf_to_ppt.py` 패턴을 참고해 새 변환기 제작
- `compound-interest-visualization.html` 스타일로 새 인터랙티브 시각화 제작
- `ai-news-digest/` 구조를 참고해 새 RSS 기반 도구 제작

---

## 4. AG + GitHub 자동화 워크플로우

### 일일 루틴

```
1. AG에서 레포 pull → 최신 상태 동기화
2. 특허 도구 작업 또는 리서치 문서 업데이트
3. AG에서 테스트 실행 (pytest patent-tools/tests/)
4. 커밋 & 푸시 → GitHub Actions로 AI 뉴스 자동 수집
```

### 모바일 연동 (AG Phone Connect)

`docs/claude-code/안그래비티_모바일_AG_연동_가이드.md`에 정리된 대로:
- AG에서 장시간 작업 중 → 모바일로 진행 상황 모니터링
- 에이전트 승인 대기 → 모바일에서 즉시 승인

---

## 5. 모델별 활용 전략

AG의 Ultra 구독(하루 2,000회)을 효율적으로 사용하는 전략:

| 작업 유형 | 모델 | 이유 |
|-----------|------|------|
| 특허 청구항 정밀 작성 | **Claude Opus 4.6** | 논리적 정밀도 최고 |
| 코드 리팩토링/디버깅 | **Claude Opus 4.6** | 깊은 추론 필요 |
| 긴 문서 분석/요약 | **Gemini 3.1 Pro (High)** | 100만 토큰 컨텍스트 |
| 빠른 수정/간단한 작업 | **Gemini 3 Flash** | 속도 우선, 한도 절약 |
| 일반 코딩/문서 작성 | **Claude Sonnet 4.6** | 속도+품질 균형 |

> **팁:** Opus는 연산량이 높아 한도를 빨리 소진하므로, 정밀 작업에만 집중 사용하고 나머지는 Sonnet/Flash로 처리합니다.

---

## 6. 레포 구조 기반 AG 컨텍스트 최적화

AG에서 전체 레포를 올리면 컨텍스트가 분산될 수 있으므로, 작업별로 포커스를 지정합니다:

```
# 특허 작업 시
@workspace patent-tools/ 폴더에 집중해서 작업해줘

# 리서치 시  
@workspace docs/research/ 폴더의 기존 분석을 참고해줘

# 도구 개발 시
@workspace tools/ 폴더의 기존 패턴을 따라줘
```

---

## 요약

| 핵심 포인트 | 내용 |
|------------|------|
| 레포 구조 | 5개 영역으로 깔끔하게 분류 완료 |
| AG 장점 | 100만 토큰 컨텍스트로 레포 전체 인식 |
| 모델 선택 | 작업별 최적 모델 배정으로 한도 효율화 |
| 자동화 | GitHub Actions + AG 일일 워크플로우 |
| 모바일 | Phone Connect로 이동 중 모니터링 |
