# 크래프톤 CEO, ChatGPT 조언 따르다 3,250억 원 소송 패소 - 케이스 스터디

## 1. 사건 개요

| 항목 | 내용 |
|------|------|
| **인수 시점** | 2021년 10월 |
| **피인수 기업** | Unknown Worlds (서브노티카 시리즈 개발사) |
| **인수가** | 5억 달러 (선불) + 최대 2.5억 달러 (성과급/Earnout) |
| **Earnout 조건** | 서브노티카 2 매출이 6,980만 달러 초과 시, 초과분 1달러당 3.12달러 지급 (최대 2.5억 달러) |
| **판결일** | 2026년 3월 16일, 델라웨어주 형평법원 |

## 2. 사건 경위

1. **크래프톤 자체 재무 예측**에 따르면 서브노티카 2의 Earnout 지급액은 1.9억~2.4억 달러로 추정
2. CEO 김창한은 이를 "나쁜 계약"이라 부르며, 전액 지급 시 **"호구(pushover)"로 보일 것**을 우려
3. 사내 법무팀(Maria Park)이 **"정당한 해고 사유 없이는 패소할 것"**이라고 Slack으로 경고
4. 김 대표는 이를 무시하고 **ChatGPT에 "계약을 이행하지 않는 방법"을 질의**
5. ChatGPT의 조언에 따라 **"Project X"** 태스크포스를 구성하고 다음을 실행:
   - Steam 퍼블리싱 권한 강탈 (게임 출시 차단)
   - 팬 커뮤니티 대상 허위 공지 게시
   - 핵심 경영진 3인(CEO Ted Gill, 공동창업자 Cleveland & McGuire) 해고
6. 재판 과정에서 **ChatGPT 대화 기록을 삭제**했으나, 법원에서 이를 확인

## 3. 판결 결과

- 해고된 CEO **Ted Gill 복직** 및 운영권 전면 회복
- Earnout 산정 기간 **258일 연장** (2026.09.15까지, 최대 2027.03까지 추가 연장 가능)
- **2단계 소송 예정**: 금전적 손해배상 규모 결정

## 4. 핵심 인사이트

### (1) AI는 법률 자문을 대체할 수 없다

ChatGPT는 **계약법의 맥락, 판례, 법적 리스크**를 전문가처럼 평가하지 못한다. "방법"은 알려줄 수 있어도, 그것이 **합법적이고 실행 가능한지**는 판단하지 못한다. 사내 변호사의 경고가 정확했다.

### (2) AI 대화는 법적 증거가 된다

이 판결과 함께 *United States v. Heppner* (2026.02) 판례가 확립한 원칙:
- **ChatGPT 대화에는 법적 특권(attorney-client privilege)이 없음**
- 삭제해도 OpenAI 서버에 기록이 남아 **소환장(subpoena) 대상**
- Sam Altman도 "ChatGPT 대화에 법적 기밀은 없다"고 인정

### (3) Earnout 구조의 위험성

인수가의 33%에 달하는 거대한 Earnout은 **인수자에게 인센티브 왜곡**을 일으킬 수 있다. 피인수 기업의 성공이 곧 추가 비용이 되는 구조는 이해충돌의 근본 원인이었다.

### (4) 기업 거버넌스의 실패

- CEO 개인의 체면 의식("호구로 보일까")이 **수천억 원 규모의 의사결정을 좌우**
- 내부 법무팀의 전문적 경고를 무시하는 **독단적 의사결정 구조**
- 증거 인멸 시도(ChatGPT 기록 삭제)로 **법원의 심증 악화**

### (5) 기술 기업 M&A에 주는 교훈

- 핵심 인력 보호 조항(Key Employee Protection)의 중요성 입증
- Earnout 분쟁은 게임 산업뿐 아니라 **모든 기술 M&A의 핵심 리스크**
- 계약서에 명시된 해고 사유 제한("중범죄, 사기, 중대 비위" 등)이 **실제로 작동**함을 확인

## 5. 참고 자료

- [404 Media - CEO Asks ChatGPT How to Void $250M Contract](https://www.404media.co/ceo-ignores-lawyers-asks-chatgpt-how-to-void-250-million-contract-loses-terribly-in-court/)
- [서울와이어 - 김창한의 '챗GPT 경영' 패착](https://www.seoulwire.com/news/articleView.html?idxno=711595)
- [뉴스1 - 美법원 크래프톤 부당해고 판결](https://www.news1.kr/world/usa-canada/6103646)
- [The Hill - ChatGPT conversations discoverable in court](https://thehill.com/opinion/judiciary/5413932-chatgpt-promised-to-forget-user-conversations-a-federal-court-ended-that/)
- [DataFence - Krafton ChatGPT Subpoena Legal Risk](https://www.datafence.ai/blog/krafton-chatgpt-subpoena-legal-risk.html)
