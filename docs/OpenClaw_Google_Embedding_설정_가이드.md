# OpenClaw + Google Embedding 설정 가이드

> **대상:** 비개발자 / 초보자
> **소요 시간:** 약 15~20분
> **작성일:** 2026-03-15

---

## 목차

1. [OpenClaw이 뭔가요?](#1-openclaw이-뭔가요)
2. [Google Embedding이 뭔가요?](#2-google-embedding이-뭔가요)
3. [사전 준비](#3-사전-준비)
4. [1단계: OpenClaw 설치](#4-1단계-openclaw-설치)
5. [2단계: Gemini API 키 발급](#5-2단계-gemini-api-키-발급)
6. [3단계: Google Embedding 연결](#6-3단계-google-embedding-연결)
7. [4단계: 메모리 폴더 만들기](#7-4단계-메모리-폴더-만들기)
8. [5단계: 동작 확인](#8-5단계-동작-확인)
9. [자주 묻는 질문 (FAQ)](#9-자주-묻는-질문-faq)

---

## 1. OpenClaw이 뭔가요?

OpenClaw(오픈클로)은 **오픈소스 개인 AI 비서**입니다.

시리나 빅스비 같은 AI 비서와 비슷하지만, 결정적 차이가 있습니다:

| 일반 AI 비서 | OpenClaw |
|-------------|----------|
| 대화가 끝나면 기억 사라짐 | **내 파일을 통째로 기억** |
| 정해진 기능만 수행 | 컴퓨터로 할 수 있는 건 거의 다 가능 |
| 회사 서버에 데이터 저장 | **내 컴퓨터에 데이터 저장** (프라이버시) |

핵심 기능인 **메모리(Memory)** 덕분에, "전에 한 거 다시 해줘"라고 물어봐도 맥락을 정확히 기억합니다.

---

## 2. Google Embedding이 뭔가요?

**임베딩(Embedding)** = 텍스트를 숫자로 변환하는 기술

사람의 눈에는 똑같은 글자여도, AI는 "이 문장과 저 문장이 비슷한 의미인지" 판단하기 어렵습니다.
임베딩은 문장을 숫자 벡터(좌표)로 바꿔서, **의미가 비슷한 문장은 가까운 좌표에 놓이게** 합니다.

**Google Embedding (`text-embedding-004`)의 장점:**
- 완전 무료 (Gemini API 키만 있으면 됨)
- 한국어 이해력 우수
- 분당 수십 회 요청 가능 (개인 사용에 충분)
- 질문 의도를 정확하게 파악 (시맨틱 검색)

**연결하면 달라지는 것:**

| Before (임베딩 없음) | After (Google Embedding 연결) |
|----------------------|-------------------------------|
| 키워드가 정확히 일치해야 검색됨 | 의미가 비슷하면 검색됨 |
| "회의록" 검색 → "회의록"만 나옴 | "회의록" 검색 → "미팅 노트", "주간 보고"도 나옴 |
| 관련 없는 결과 섞여 나옴 | 질문 의도를 파악해서 정확한 결과만 |

---

## 3. 사전 준비

시작하기 전에 아래 2가지만 확인하세요.

### 3-1. 인터넷 연결

Google API를 사용하므로 인터넷이 필요합니다.

### 3-2. 터미널(명령 프롬프트) 열기

터미널은 텍스트로 컴퓨터에 명령을 내리는 프로그램입니다. 복잡하지 않으니 걱정 마세요!

| 운영체제 | 여는 방법 |
|---------|----------|
| **Windows** | 시작 메뉴에서 "PowerShell" 검색 → **우클릭** → **관리자 권한으로 실행** |
| **Mac** | `Cmd + Space` → "터미널" 검색 → 실행 |
| **Linux** | `Ctrl + Alt + T` |

---

## 4. 1단계: OpenClaw 설치

### 방법 A: 원클릭 설치 (가장 쉬움)

터미널에 아래 명령어를 **복사해서 붙여넣기** 하세요.

**Mac / Linux:**
```bash
curl -fsSL --proto '=https' --tlsv1.2 https://openclaw.ai/install.sh | bash
```

**Windows (PowerShell):**
```powershell
powershell -c "irm https://openclaw.ai/install.ps1 | iex"
```

> 이 명령어가 Node.js(필수 프로그램)까지 자동으로 설치해줍니다.

### 방법 B: 수동 설치 (Node.js가 이미 있는 경우)

```bash
npm install -g openclaw@latest
```

### 설치 확인

설치가 끝나면 아래 명령어로 확인:

```bash
openclaw --version
```

버전 번호가 나오면 성공입니다!

### 초기 설정 마법사 실행

```bash
openclaw onboard
```

화면에 나오는 질문에 답하면 기본 설정이 완료됩니다.
(잘 모르겠으면 기본값 그대로 Enter 누르면 됩니다)

---

## 5. 2단계: Gemini API 키 발급

Google Embedding을 사용하려면 **Gemini API 키**가 필요합니다. 무료이고 신용카드 불필요합니다.

### 발급 순서

1. **Google AI Studio 접속**
   - 브라우저에서 https://aistudio.google.com 에 접속
   - Google 계정으로 로그인 (Gmail 계정이면 됩니다)

2. **API 키 생성**
   - 왼쪽 메뉴에서 **"Get API Key"** 클릭
   - **"Create API Key"** 버튼 클릭
   - 프로젝트 선택 화면이 나오면 **"Create API key in new project"** 선택

3. **키 복사**
   - 생성된 API 키가 화면에 표시됩니다
   - `AIza...`로 시작하는 긴 문자열입니다
   - **복사** 버튼을 눌러 저장해두세요

> **중요:** API 키는 비밀번호와 같습니다. 다른 사람에게 공유하지 마세요!

### 무료 사용 한도

| 항목 | 무료 한도 |
|------|----------|
| 임베딩 요청 | 분당 최대 100회, 하루 1,000회 (개인 사용에 충분) |
| 비용 | 완전 무료 |
| 신용카드 | 불필요 |
| 참고 | 한도는 프로젝트 단위 적용, 매일 자정(태평양시간) 초기화 |

---

## 6. 3단계: Google Embedding 연결

이제 발급받은 API 키를 OpenClaw에 연결합니다.

### 6-1. API 키 등록

터미널에서 아래 명령어를 입력하세요. `여기에_API_키_붙여넣기` 부분을 실제 키로 교체하세요.

**Mac / Linux:**
```bash
export GEMINI_API_KEY="여기에_API_키_붙여넣기"
```

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="여기에_API_키_붙여넣기"
```

> **영구 저장하려면?**
> 위 명령은 터미널을 닫으면 사라집니다. 영구 저장하려면:
>
> - **Mac/Linux:** `~/.bashrc` 또는 `~/.zshrc` 파일 맨 아래에 `export GEMINI_API_KEY="키값"` 추가
> - **Windows:** 시스템 환경 변수에 `GEMINI_API_KEY` 추가 (제어판 → 시스템 → 고급 시스템 설정 → 환경 변수)

### 6-2. 설정 파일에 임베딩 프로바이더 추가

OpenClaw 설정 파일을 열어서 Google Embedding을 활성화합니다.

설정 파일 위치: `~/.openclaw/openclaw.json`

**방법 A: 명령어로 설정 (가장 쉬움)**

```bash
openclaw onboard --auth-choice google-api-key
```

화면의 안내를 따라가면 자동으로 설정됩니다.

**방법 B: 설정 파일 직접 수정**

아래 내용을 설정 파일의 `agents` 섹션에 추가하세요:

```json
{
  "agents": {
    "defaults": {
      "memorySearch": {
        "provider": "google",
        "model": "text-embedding-004"
      }
    }
  }
}
```

> **설정 팁:**
> - `"provider": "google"` → Google을 임베딩 제공자로 사용
> - `"model": "text-embedding-004"` → 가장 안정적인 무료 임베딩 모델 (768차원)
> - 최신 모델을 쓰고 싶다면 `"gemini-embedding-001"` (3072차원, 100개 이상 언어 지원)도 가능
> - API 키는 환경 변수에 두고, 설정 파일에 직접 넣지 마세요 (보안)

### 6-3. 설정 검증

```bash
openclaw doctor
```

이 명령어가 설정에 문제가 있으면 알려주고, 자동으로 수정을 시도합니다.

---

## 7. 4단계: 메모리 폴더 만들기

OpenClaw의 메모리는 내 컴퓨터에 있는 **일반 Markdown 파일**입니다.
AI가 잘못 기억한 게 있으면 파일을 직접 열어서 고칠 수 있습니다.

### 메모리 구조

```
내 워크스페이스/
├── MEMORY.md              ← 핵심 기억 (항상 참조)
└── memory/
    ├── 2026-03-15.md      ← 오늘의 기록 (자동 생성)
    ├── 2026-03-14.md      ← 어제의 기록
    ├── people/            ← 사람 정보
    │   └── 홍길동.md
    ├── projects/          ← 프로젝트 정보
    │   └── 특허출원.md
    └── topics/            ← 주제별 정보
        └── 회의록.md
```

### 폴더 만들기

```bash
mkdir -p memory/people memory/projects memory/topics
touch MEMORY.md
```

### MEMORY.md 예시

```markdown
# 핵심 기억

## 나에 대해
- 이름: 홍길동
- 직업: 특허 업무 담당

## 자주 하는 작업
- 특허 명세서 변환 (Word → HLT)
- 주간 회의록 정리
- AI 뉴스 확인

## 선호 사항
- 보고서는 한국어로 작성
- 파일 이름은 날짜_제목 형식
```

---

## 8. 5단계: 동작 확인

모든 설정이 끝났습니다! 제대로 작동하는지 확인해봅시다.

### 8-1. OpenClaw 게이트웨이 실행

```bash
openclaw gateway
```

### 8-2. 메모리 검색 테스트

OpenClaw에게 아래처럼 물어보세요:

> "내 메모리에서 특허 관련 내용 찾아줘"

임베딩이 제대로 연결되었다면:
- 키워드가 정확히 일치하지 않아도 관련 내용을 찾아줍니다
- "특허"라고 물어봤는데 "발명 신고서", "지식재산" 같은 관련 문서도 찾아줍니다

### 8-3. 문제가 생겼을 때

```bash
openclaw doctor
```

이 명령어를 실행하면 대부분의 문제를 자동 진단하고 해결합니다.

---

## 9. 자주 묻는 질문 (FAQ)

### Q: 정말 무료인가요?
**A:** 네. OpenClaw은 오픈소스(무료)이고, Google의 text-embedding-004 모델도 무료입니다.
Gemini API 키 발급에 신용카드가 필요 없습니다.

### Q: 내 파일이 Google 서버로 전송되나요?
**A:** 임베딩 생성 시 텍스트가 Google API로 전송됩니다. 하지만 Google은 무료 API를 통해 전송된 데이터를 모델 학습에 사용하지 않는다고 명시하고 있습니다. 민감한 데이터가 걱정된다면 로컬 임베딩(node-llama-cpp)을 사용할 수도 있습니다.

### Q: 파일이 몇 개까지 가능한가요?
**A:** 수백 개의 Markdown 파일을 문제없이 처리합니다. 사용자 사례 중 458개 파일을 인덱싱한 경우도 있습니다.

### Q: 임베딩 모델을 바꾸면 어떻게 되나요?
**A:** OpenClaw이 자동으로 감지하고 전체 인덱스를 다시 생성합니다. 수동 작업이 필요 없습니다.

### Q: 인덱스가 꼬인 것 같아요
**A:** `~/.openclaw/memory/` 폴더에서 SQLite 파일을 삭제하면 처음부터 다시 인덱싱합니다. 임베딩 모델을 변경하면 OpenClaw이 자동으로 감지하고 재인덱싱합니다.

### Q: 최신 임베딩 모델도 쓸 수 있나요?
**A:** 네. `gemini-embedding-001` (텍스트 전용, 3072차원) 또는 `gemini-embedding-2-preview` (멀티모달 — 텍스트, 이미지, 영상, 오디오, PDF 지원) 모델도 설정 가능합니다. 단, 모델을 바꾸면 차원 수가 달라져서 기존 인덱스를 삭제해야 합니다.

### Q: Windows에서도 되나요?
**A:** 네. WSL2(Windows Subsystem for Linux) 사용을 권장하지만, PowerShell에서도 설치 가능합니다.

---

## 요약: 전체 과정 한눈에

```
1. 터미널 열기
2. OpenClaw 설치      → curl 또는 npm 명령어 1줄
3. Gemini API 키 발급  → aistudio.google.com에서 클릭 3번
4. API 키 등록        → export GEMINI_API_KEY="키값"
5. 설정 파일 수정      → openclaw.json에 provider: "google" 추가
6. 메모리 폴더 생성    → mkdir + MEMORY.md 작성
7. 확인               → openclaw doctor
```

**설정 1줄이면 끝이고, 무료입니다.**

---

## 참고 자료

- [OpenClaw 공식 문서](https://docs.openclaw.ai)
- [OpenClaw GitHub](https://github.com/openclaw/openclaw)
- [OpenClaw 메모리 개념](https://docs.openclaw.ai/concepts/memory)
- [Google AI Studio (API 키 발급)](https://aistudio.google.com)
- [Google Embedding 문서](https://ai.google.dev/gemini-api/docs/embeddings)
- [Gemini API 무료 한도](https://ai.google.dev/gemini-api/docs/rate-limits)
- [OpenClaw memorySearch 가이드 (DEV Community)](https://dev.to/czmilo/2026-complete-guide-to-openclaw-memorysearch-supercharge-your-ai-assistant-49oc)
