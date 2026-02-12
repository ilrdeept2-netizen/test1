# claude.com/download XML NoSuchKey 에러 조사 보고서

**날짜**: 2026-02-12
**증상**: claude.com/download 에서 Windows 설치 파일 다운로드 시 아래 XML 에러 출력

```xml
<Error>
  <Code>NoSuchKey</Code>
  <Message>The specified key does not exist.</Message>
</Error>
```

---

## 1. NoSuchKey 에러란?

### 정의
AWS S3(Simple Storage Service)에서 반환하는 **HTTP 404 에러**입니다.
요청한 파일(Object Key)이 S3 버킷에 존재하지 않을 때 발생합니다.

### 왜 XML로 표시되는가?
- S3는 에러 응답을 **XML 형식**으로 반환
- 브라우저가 이 XML을 그대로 렌더링하면 사용자에게 위 화면이 보임
- "This XML file does not appear to have any style information associated with it"
  → 브라우저가 XML에 연결된 스타일시트(XSL/CSS)가 없어서 원본 XML 트리를 표시한 것

### 발생 조건
```
사용자 → claude.com/download 클릭
       → 서버가 S3 다운로드 URL로 리다이렉트
       → S3 버킷에서 해당 키(파일 경로) 조회
       → 파일 없음 → NoSuchKey XML 에러 반환
```

---

## 2. 근본 원인: AWS CloudFront DNS 장애 (2026-02-10)

### 사건 개요
2026년 2월 10일, **AWS CloudFront에서 DNS 해석 장애**가 발생했습니다.

### 타임라인 (UTC)
```
2/10 21:15  CloudFront가 특정 배포에 NXDOMAIN 응답 시작
2/10 21:38  IsDown에서 사용자 보고 시작 (공식 발표 23분 전)
2/10 21:xx  AWS 공식 상태 업데이트 시작
2/10 22:34  급성 DNS 해석 장애 완화 (~1시간 소요)
2/11 04:00  변경 전파 지연 복구 완료 (추가 ~5.5시간)
```

### 영향 범위
- **8개 AWS 서비스**: CloudFront, Route 53, API Gateway, WAF, AppSync, Pinpoint, Transfer Family, VPC Lattice
- **20개+ 다운스트림 플랫폼**: Salesforce, Adobe, Discord, **Claude**, McGraw Hill, UKG 등

### AWS 공식 확인
> "We can confirm errors for DNS resolution for some CloudFront distributions.
> During this time, customers may receive an NXDOMAIN response."

### Claude 다운로드와의 연관성

```
claude.com/download
  ↓ 리다이렉트
CloudFront CDN (*.cloudfront.net)
  ↓ DNS 해석
S3 버킷 (설치 파일 저장)
  ↓ 파일 조회
NoSuchKey 에러 반환
```

CloudFront DNS 장애로 인해:
1. CDN이 올바른 S3 버킷으로 라우팅하지 못하거나
2. S3 버킷 자체의 DNS가 꼬여서 파일을 찾지 못하거나
3. 복구 과정에서 새 배포/키 전파가 지연되어 이전 키가 무효화된 상태

**급성 장애는 ~1시간에 해결됐지만, 전파 지연 복구가 2/11 04:00 UTC까지 지속되었고,
이 기간 동안 "새 배포, DNS 변경, TLS 인증서 프로비저닝"이 영향을 받았습니다.**

→ Anthropic이 이 시기에 Windows 빌드를 업데이트/재배포하려 했다면,
  새 파일의 S3 키가 전파되지 않아 NoSuchKey가 지속될 수 있습니다.

---

## 3. 다른 사용자 장애 보고 현황

### 수치 근거
| 시점 | 사용자 장애 보고 수 | 비고 |
|---|---|---|
| 2/9 | 15건/24h | IsDown |
| 2/10 | 37건/24h | StatusGator |
| 2/11 | **153건/24h** | StatusGator (10배 급증) |

### 2/10~11 공식 인시던트
1. **Opus 4.6 Fast Mode 에러** (2/10 ~10:05 UTC → 16:28 UTC 해결)
2. **AWS CloudFront DNS 장애** (2/10 21:15 UTC → 2/11 04:00 UTC)
3. **Haiku 4.5 에러 상승** (2/11)

### 자동 업데이트 관련 버그
- [Issue #22609](https://github.com/anthropics/claude-code/issues/22609): "Claude desktop이 자동으로 새로운/깨진 버전으로 업데이트됨"
- 사용자 요청: 자동 업데이트 전 사용자 확인을 받아야 함
- 이 버그로 인해 사용자가 깨진 버전으로 강제 업데이트되고, 다시 다운로드하려 하면 S3 에러에 막히는 이중 트랩 발생

### 14일간 누적 불안정 보고
- [GitHub Gist](https://gist.github.com/LEX8888/675867b7f130b7ad614905c9dd86b57a): "Claude Desktop/Code: 19 incidents in 14 days, memory leak shipped to production (Jan 27 ~ Feb 3, 2026)"
- GitHub에 **5,788개 오픈 이슈** (2/3 기준)
- "Anthropic은 OpenAI, Google 대비 지속적으로 더 많은 다운타임과 에러를 발생시킴"

---

## 4. 왜 한국 사용자에게 더 심한가?

### 시간대 불일치
```
AWS CloudFront 장애: 2/10 21:15 UTC = 2/11 06:15 KST (한국 새벽~아침)
전파 지연 복구 완료: 2/11 04:00 UTC = 2/11 13:00 KST (한국 오후 1시)
```
→ 한국 사용자의 **업무 시작 시간(오전 9시)**이 정확히 복구 지연 기간과 겹침
→ 미국은 밤이라 대부분 잠들어 있어 체감 영향 적음

### CDN 전파 지연
- CloudFront 엣지 로케이션별 전파 속도 차이
- 서울 엣지는 미국 본토 대비 전파 우선순위가 낮을 수 있음
- DNS TTL(Time to Live)로 인해 이전의 잘못된 캐시가 더 오래 유지

---

## 5. 현재 상태 및 전망

### 현재 상태 (2/12 기준)
- AWS CloudFront: 복구 완료
- Claude 공식 상태: "Operational"
- 다운로드 링크: Anthropic의 S3 키 업데이트/전파 상태에 따라 다름

### 확인 방법
1. https://claude.com/download 재접속 시도
2. 여전히 NoSuchKey → Anthropic이 아직 S3 키를 복구하지 않은 상태
3. 정상 다운로드 → 복구 완료

### 대안
- 웹 버전: https://claude.ai
- TechSpot 미러: https://www.techspot.com/downloads/7833-claude-desktop-app.html
- Uptodown 미러: https://claude.en.uptodown.com/windows/download

---

## 6. 결론

| 항목 | 결론 |
|---|---|
| **개인 PC 문제인가?** | 아니오 |
| **원인** | AWS CloudFront DNS 장애 + Anthropic S3 배포 전파 지연 |
| **영향 범위** | 전 세계 (2/11 153건 보고), 한국 시간대 특히 심함 |
| **해결 주체** | Anthropic (사용자가 해결 불가) |
| **예상 복구** | AWS는 복구됨, Anthropic의 S3 키 재배포 대기 |

---

## Sources
- [IsDown - AWS CloudFront Outage Feb 2026](https://isdown.app/blog/aws-cloudfront-outage-february-2026)
- [CircleID - Massive AWS Outage Disrupts Global Internet](https://circleid.com/posts/massive-aws-outage-disrupts-global-internet-services-dns-failure)
- [The Nightly - AWS CloudFront Global Outage](https://thenightly.com.au/society/technology/aws-outage-update-amazon-web-services-cloudfront-experience-global-outage-operation-issue-c-21597705)
- [AWS Health Dashboard - Feb 10 2026 Event](https://health.aws.amazon.com/health/status?eventID=arn:aws:health:us-east-1::event/MULTIPLE_SERVICES/AWS_MULTIPLE_SERVICES_OPERATIONAL_ISSUE/AWS_MULTIPLE_SERVICES_OPERATIONAL_ISSUE_BA540_514A652BE1A)
- [Adrian Cockcroft - The Internet is Down, It was DNS Again](https://adrianco.medium.com/the-internet-is-down-it-was-dns-again-e86341db21d5)
- [GitHub Issue #22609 - Auto-update to broken versions](https://github.com/anthropics/claude-code/issues/22609)
- [GitHub Gist - 19 incidents in 14 days](https://gist.github.com/LEX8888/675867b7f130b7ad614905c9dd86b57a)
- [StatusGator - Claude Status](https://statusgator.com/services/claude)
- [Claude Status Page](https://status.claude.com/)
