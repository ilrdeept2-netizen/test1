# 안그래비티(Antigravity) 모바일 ↔ AG 연동 가이드

Google Antigravity에서 Claude Opus 모델을 사용하면서, 모바일에서도 AG 세션에 접근하거나 연동하는 방법을 정리합니다.

---

## 현재 상황 (2026년 3월 기준)

- Google Antigravity에는 **공식 모바일 앱이 아직 없음**
- 데스크톱 전용 IDE (Windows / macOS / Linux)
- 지원 모델: Gemini 3.1 Pro, Gemini 3 Flash, **Claude Opus 4.6**, Claude Sonnet 4.6, GPT-OSS 120B
- 모바일 리모트 컨트롤은 커뮤니티에서 활발히 요청 중이며, Google도 공식 기능 요청으로 등록 예정

---

## 방법 1: Antigravity Phone Connect (추천)

모바일에서 데스크톱 AG 세션을 실시간 모니터링하고 제어하는 커뮤니티 도구입니다.

### 특징
- Chrome DevTools Protocol(CDP) 기반으로 데스크톱 AG UI를 폰에 미러링
- 폰에서 스크롤하면 데스크톱 AG도 동기화
- 모델/모드 양방향 싱크
- OAuth 토큰 추출 없이 안전하게 동작
- 다크 테마, 터치 최적화 UI

### 설정 방법

```bash
# 1. Antigravity를 리모트 디버깅 포트로 시작
#    (설치 스크립트 실행 후, 우클릭 → "Open with Antigravity (Debug)")

# 2. Phone Connect 클론 및 실행
git clone https://github.com/krishnakanthb13/antigravity_phone_chat
cd antigravity_phone_chat
npm install
npm start

# 3. 같은 네트워크의 모바일 브라우저에서 접속
#    http://<PC의_IP주소>:포트번호
```

### 사용 시나리오
- AG에서 Claude Opus로 장시간 코드 생성 중 → 자리를 비워도 폰으로 진행 상황 확인
- 에이전트가 승인 대기 중일 때 폰으로 즉시 승인 가능

---

## 방법 2: Anti-API (크로스 디바이스 API 프록시)

Antigravity의 AI 모델을 OpenAI/Anthropic 호환 API로 변환하여, 모바일 등 다른 디바이스에서도 접근 가능하게 합니다.

### 특징
- Antigravity / Codex / GitHub Copilot / Zed 모델을 통합 API로 제공
- ngrok / cloudflared / localtunnel로 원클릭 원격 접속 설정
- 자동 계정 로테이션 (rate limit 도달 시 자동 전환)

### 설정 방법

```bash
# 1. Anti-API 설치
git clone https://github.com/ink1ing/anti-api
cd anti-api
npm install

# 2. 설정 파일에 Antigravity 계정 추가
# config.json에 Google 계정 정보 설정

# 3. 서버 시작 + 원격 접속 활성화
npm start
# ngrok 등으로 터널링하면 모바일에서도 API 접근 가능
```

### 모바일에서 사용
- 모바일의 AI 클라이언트 앱(예: BoltAI, TypingMind 등)에서 API 엔드포인트로 연결
- Claude Opus 모델을 모바일에서 직접 호출 가능

### 주의사항
- **Google이 역방향 프록시 사용을 공식 금지**했으므로, 계정 차단 위험 있음
- 장기적 사용에는 권장하지 않으며, Codex/Copilot 경유가 더 안전

---

## 방법 3: Porta (경량 채팅 전용)

Antigravity의 Language Server에 직접 연결하여 채팅 데이터만 전송하는 경량 도구입니다.

### 특징
- 스크린샷 전송 없이 채팅 데이터만 동기화 → 매우 빠름
- 모바일 데이터에서도 1초 이내 로딩
- PWA로 홈화면에 추가하면 네이티브 앱처럼 사용 가능

---

## 방법 4: 브라우저 직접 접속 (가장 간단)

Antigravity는 웹 기반 IDE이므로, 모바일 브라우저에서 직접 접속할 수도 있습니다.

### 방법
1. PC에서 Antigravity 실행
2. 모바일 브라우저(Chrome/Safari)에서 `https://antigravity.google/` 접속
3. 동일 Google 계정으로 로그인
4. 기존 워크스페이스에 접근

### 한계
- 모바일 화면에서 IDE 사용이 불편 (코드 편집은 사실상 어려움)
- 채팅/에이전트 대화 확인 및 간단한 승인 정도로 활용

---

## 실용적 워크플로우 제안

### Claude Opus + AG + 모바일 통합 활용법

```
[데스크톱 AG]                    [모바일]
     │                              │
     ├─ Claude Opus로 코드 생성 ──→ Phone Connect로 진행 상황 모니터
     │                              │
     ├─ 에이전트 승인 대기 ────→ 모바일에서 즉시 승인
     │                              │
     ├─ 장시간 빌드/테스트 ────→ 완료 알림 확인
     │                              │
     └─ 결과 리뷰 ←──────────── 모바일에서 결과 확인
```

### 추천 조합

| 용도 | 추천 방법 | 난이도 |
|------|-----------|--------|
| 진행 상황 모니터링 | Phone Connect | 중 |
| 에이전트 승인/간단한 대화 | Porta 또는 브라우저 | 하 |
| 모바일에서 Claude API 직접 호출 | Anti-API | 상 |
| 가장 간단한 확인 | 브라우저 직접 접속 | 하 |

---

## 참고 링크

- [Antigravity Phone Connect (GitHub)](https://github.com/krishnakanthb13/antigravity_phone_chat)
- [Anti-API (GitHub)](https://github.com/ink1ing/anti-api)
- [Antigravity Mobile 기능 요청 (Google Forum)](https://discuss.ai.google.dev/t/antigravity-mobile-remote-control/128282)
- [Google Antigravity 공식](https://antigravity.google/)
- [Antigravity + Claude Code 통합 가이드](https://scuti.asia/antigravity-claude-code-integration-overview-setup-and-sample-app/)
