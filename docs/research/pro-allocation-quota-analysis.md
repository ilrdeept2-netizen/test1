# Google AI Pro (Antigravity) 할당량 잠금 문제 분석

> 2026년 3월 12일 기준 조사 결과

## 문제 요약

Google AI Pro (Antigravity IDE) 유료 구독자들이 광고된 5시간 할당량 갱신 대신 **수일간 모델 접근이 차단**되는 문제를 광범위하게 보고하고 있습니다.

### 보고된 증상

| 항목 | 광고된 정책 | 실제 경험 |
|------|-----------|----------|
| 할당량 갱신 주기 | 5시간마다 | 3~7일 |
| Gemini Pro | 5시간 후 리셋 | 5일 이상 잠금 |
| Sonnet 4.6 (Claude) | 5시간 후 리셋 | 6~7일 잠금 |
| 전날 밤 잔여 할당량 | 유지 | 다음날 갑자기 소진/잠금 |

---

## 1. Google AI Pro (Antigravity) 할당 정책 및 버그

### 공식 정책
- **Pro 구독자**: 5시간마다 할당량 갱신, 주간 상한(weekly cap)까지
- **Ultra 구독자**: 5시간 갱신 + 주간 상한 없음
- 2026년 1월부터 **모델별 독립 할당량** 적용 (Gemini 3 Thinking과 Pro가 풀을 공유하지 않음)
- Pro 구독자는 Thinking 모델에 300개 프롬프트 할당

### 확인된 버그 (2026년 2월~3월)

2026년 2월 19~20일경 Gemini 3.1이 Antigravity IDE에 배포된 시점부터 광범위한 잠금 버그 발생:

- **Gemini 3.1 Pro (High/Low)** 모델: "5일 0시간 후 갱신" 표시 (5시간이 아님)
- 일부 사용자는 **모델 미사용 상태에서도** 7일간 할당량 제한
- Gemini뿐 아니라 **Claude 모델(Sonnet, Opus)** 에도 영향 (Claude Opus 6일 잠금 보고)
- 2026년 3월 12일 현재 **미해결 상태** — Google이 문서를 업데이트했으나 버그 자체는 수정되지 않음

### 배경: 2025년 12월 무료 할당량 대폭 삭감
- Google이 "사기 및 남용" 방지를 이유로 무료 API 할당량을 50~92% 삭감
- 수만 개 개발 프로젝트에 영향

### 주요 버그 리포트 (Google AI Developers Forum)

1. [5일 잠금 — Gemini 3.1 이후 낮은 사용량에도 잠금](https://discuss.ai.google.dev/t/bug-google-ai-pro-5-day-gemini-lockout-since-gemini-3-1-update-very-low-usage-pro-5-hour-refresh-not-honored/124839)
2. [5시간 갱신 미이행 — Claude Opus 6일 차단](https://discuss.ai.google.dev/t/google-ai-pro-quota-limits-not-resetting-every-5-hours-as-advertised-claude-opus-blocked-for-6-days/123368)
3. [Gemini 3.1 Pro 4일 잠금](https://discuss.ai.google.dev/t/gemini-3-1-pro-quota-locked-for-4-days-on-google-ai-pro-subscription-antigravity-ide/129659)
4. [Pro 티어 불일치 — 5시간 대신 5일 잠금](https://discuss.ai.google.dev/t/bug-pro-tier-misalignment-models-locked-for-5-days-instead-of-5-hours-in-antigravity/130631)
5. [7일 무기한 연장 — 미사용 상태에서 잠금](https://discuss.ai.google.dev/t/bug-pro-user-the-reset-time-for-gemini-3-1-pro-and-claude-quotas-has-been-extended-indefinitely-by-7-days/130777)
6. [Claude Sonnet 4.6 — 7일 잠금](https://discuss.ai.google.dev/t/urgent-bug-google-ai-pro-claude-sonnet-4-6-quota-reached-7-day-lockout-until-04-03-2026-baseline-refresh/127183)
7. [74시간 잠금 (5시간 아님)](https://discuss.ai.google.dev/t/pro-plan-quota-bug-models-locked-for-74-hours-instead-of-5-hour-refresh/129464)

---

## 2. Anthropic Claude Pro 할당 정책 (참고)

Anthropic claude.ai 직접 구독 시의 정책 (Antigravity 경유와는 별도):

### 이중 레이어 시스템

| 레이어 | 설명 | 리셋 방식 |
|--------|------|----------|
| 5시간 롤링 윈도우 | 버스트 제어용 | 첫 요청 후 5시간, 점진적 만료 |
| 주간 상한 | 총 사용량 제한 | 7일 주기 리셋 |

- Pro 사용자: 주당 약 **40~80시간** Claude Code 사용 가능 (Sonnet 4 기준)
- 메시지는 **토큰 기반**으로 측정 — Claude Code 파일 읽기+변경은 1건당 ~50,000 토큰 소모 가능
- Claude Code와 claude.ai가 **할당량 공유**
- Pro 플랜에서는 추가 사용량 구매 불가 — Max 플랜($100 또는 $200/월)으로 업그레이드 필요

### 최근 이슈 (2026년 초)
- 2025년 12월 연말 2배 보너스 → 2026년 1월 원복 시 사용자들이 "한도 감소"로 인식
- Claude Code 프롬프트 캐싱 버그로 비정상적 할당량 소진 → v2.1.62 핫픽스 + 전 사용자 한도 리셋
- Claude 4.6 출시(2026년 2월 말) 이후 일부 Pro 사용자가 주간 한도 급속 소진 보고

---

## 3. 할당량 관리 모범 사례

### 범용 전략

1. **프롬프트 일괄 처리**: 관련 질문을 하나의 메시지로 결합 → 소비 60~80% 절감
2. **대화 자주 초기화**: 긴 대화는 컨텍스트 누적으로 메시지당 토큰 비용이 ~200 → 15,000+ 증가
3. **구체적 프롬프트 작성**: 파일 경로, 라인 번호, 정확한 요구사항 포함으로 왕복 절감
4. **적절한 모델 선택**: Opus는 Sonnet 대비 ~3배 할당량 소모. 80% 작업은 Sonnet으로
5. **비피크 시간 활용**: 북미/유럽 저녁~주말 시간대에 상대적으로 여유로운 경우 보고

### Claude 전용 팁

6. **CLAUDE.md 파일 사용**: 프로젝트 구조 재탐색 방지로 토큰 소비 20~30% 절감
7. **프로젝트 시스템 프롬프트 활용**: 매 메시지마다 컨텍스트 재설명 방지
8. **`/usage` 명령어**: Claude Code에서 한도 리셋 시점 확인 (현재 유일한 모니터링 방법)

### 구조적 대안

9. **API 직접 사용**: 사용량 기반 과금, "잠금" 없음
10. **다중 제공자 전략**: Google AI Pro, Anthropic, OpenAI 등 병행
11. **플랜 업그레이드**: Claude Max ($100/5x, $200/20x) 또는 Google Ultra (주간 상한 없음)
12. **로컬 모델 병행**: Ollama 등으로 기본 작업 처리

---

## 4. 결론 및 권장사항

### 핵심 결론

1. **귀하의 문제는 확인된 버그입니다.** Gemini 3.1 마이그레이션과 관련된 광범위한 할당량 시스템 버그로, Google AI Developers Forum에 수십 건의 동일 보고가 존재합니다.

2. **두 플랫폼 모두 할당량 투명성이 부족합니다.** 사용량 대시보드가 없어 남은 할당량을 사전에 파악할 수 없다는 것이 가장 빈번한 사용자 불만입니다.

3. **Google 측 미해결.** 문서는 업데이트되었으나, 최소 사용량에서 수일간 잠금이 발생하는 버그는 2026년 3월 중순 현재 수정되지 않았습니다.

### 즉시 조치 권장

| 조치 | 방법 |
|------|------|
| 버그 리포트 | [Google AI Developers Forum](https://discuss.ai.google.dev/)에 증상, 스크린샷 포함 보고 |
| 환불 요청 | 광고 기능(5시간 갱신) 미제공 → 소비자 보호법에 따른 정당한 사유 |
| 대안 전환 | Anthropic claude.ai 직접 구독 ($20/월) 또는 API 직접 사용 |
| 일부 사용자 보고 | Google 지원팀 접촉 후 수동 리셋을 받은 사례 존재 |
