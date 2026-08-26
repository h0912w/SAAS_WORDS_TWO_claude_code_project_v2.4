# 15. Google Ads API 자격증명 설정 절차 (테스트 계층 방식)

**작성 배경(2026-08-26)**: daramg 계정 기반 자격증명을 h0912w 소유 자격증명으로
교체하는 작업에서, 아래 순서대로 다섯 가지 서로 다른 원인의 실패를 실측으로
겪고 전부 해결했다. 이 문서는 그 시행착오를 재현 가능한 절차로 정리한 것이다.
같은 문제(자격증명 교체, 새 Google 계정으로 재설정, REFRESH_TOKEN 재발급 등)가
다시 발생하면 이 문서부터 참고할 것 — `memory/HANDOFF.md`의 2026-08-26 항목에
당시 진단 과정이 시간순으로 더 상세히 남아있다.

## 핵심 아키텍처 (결론)

Google Ads API의 `generateKeywordIdeas`(Keyword Planner 조회)는 **계정별 데이터가
아니라 공개 키워드 코퍼스를 조회하는 API**라서, 실제 프로덕션 계정 없이 **테스트
전용 계층**만으로 진짜 검색량 데이터를 조회할 수 있다. 이 프로젝트는 아래 4개
자격증명 조합을 최종적으로 사용한다:

| 환경변수 | 값의 출처 | 비고 |
|---|---|---|
| `GOOGLE_ADS_CLIENT_ID` / `_CLIENT_SECRET` | Google Cloud Console (임의의 한 프로젝트) OAuth 클라이언트 | 프로덕션/테스트 공용, 계정과 무관 |
| `GOOGLE_ADS_DEVELOPER_TOKEN` | **프로덕션 Manager 계정**(예: h0912w)의 API 센터 | 테스트 계정에도 그대로 재사용 가능(공식 문서 확인) |
| `GOOGLE_ADS_CUSTOMER_ID` | **테스트 관리자 계정 밑에 새로 만든 테스트 클라이언트 계정**의 CID | 프로덕션 계정 CID 사용 금지 |
| `GOOGLE_ADS_LOGIN_CUSTOMER_ID` | 그 **테스트 관리자 계정** 자신의 CID | 프로덕션 Manager CID 사용 금지 |
| `GOOGLE_ADS_REFRESH_TOKEN` | **테스트 관리자 계정을 소유한 Google 계정**으로 발급 | 개발자 토큰 소유 계정과 다를 수 있음(달라도 됨) |

프로덕션 Manager 계정(h0912w)이 하는 역할은 **개발자 토큰 발급처** 하나뿐이다.
CUSTOMER_ID/LOGIN_CUSTOMER_ID/REFRESH_TOKEN은 전부 테스트 계층에서 나온다.

## 왜 이렇게 됐는가 — 근본 제약 (공식 문서 근거)

출처: [Google Ads API - Test accounts](https://developers.google.com/google-ads/api/docs/first-call/test-accounts),
[Test accounts best practices](https://developers.google.com/google-ads/api/docs/best-practices/test-accounts)

> "Because test and production accounts cannot interact in any way, you cannot use
> a test account under your existing production manager account. To use test
> accounts, you need a new account hierarchy, with a test manager account as the root."

> "Use the developer token of your production manager account when making requests
> against the test manager account. Even if it's not approved yet, the token still
> works on test accounts."

> "test accounts appear in the Google Ads UI as cancelled accounts since there is
> no active billing" — 이건 정상 동작이며, 진짜 테스트 계정이면 화면에 빨간
> **"테스트 계정"** 배지가 뜬다. 배지가 없이 "해지된 계정이며 재활성화할 수
> 없습니다"만 뜨면 그건 테스트 계정이 아니라 **진짜 폐기된 계정**이다.

> "Since test accounts don't have budgets, you might see an error when creating a
> test sub-account in a manager account. You can safely ignore this error."

## 단계별 절차 (처음부터 다시 할 경우)

### 1단계 — 테스트 관리자 계정 생성
1. **프로덕션 관리자 계정(h0912w)과 무관한 별도 Google 계정**으로 로그인한다
   (같은 계정으로 로그인된 브라우저가 있으면 로그아웃하거나 시크릿 창 사용).
   기존 프로덕션 계정에 사용자로 등록된 적 있는 이메일은 "연결된 계정"으로
   취급되어 실패할 수 있다 — 완전히 새 Gmail을 쓰는 게 가장 확실하다.
2. **https://ads.google.com/nav/selectaccount?sf=mt** 접속 → 안내에 따라 생성.
3. 완료되면 우측 상단에 빨간 **"테스트 계정"** 배지가 뜬다. 이 계정의 CID를
   기록한다 → `GOOGLE_ADS_LOGIN_CUSTOMER_ID`.

### 2단계 — 테스트 클라이언트 계정 생성
공식 경로(출처: [Create new Google Ads accounts from your manager accounts](https://support.google.com/google-ads/answer/7456139?hl=en)):
좌측 **"계정"** 아이콘 → **"하위 계정 설정"** → **"+"** → **"새 계정 만들기"**.

- 이후 "첫 캠페인 만들기" 마법사(업체 정보 → 광고 → 예산)가 뜬다 — **이건 무시해도
  된다.** 업체 이름만 대충 입력하고, 캠페인/예산/결제 단계에서 막히거나 에러가
  나면 좌측 상단 **"X"**로 나가면 된다. 계정 자체(CID)는 이미 생성된 상태로
  남는다 — 공식 문서가 이 에러를 "안전하게 무시 가능"이라고 명시함.
- 생성된 CID를 기록한다 → `GOOGLE_ADS_CUSTOMER_ID`.

### 3단계 — OAuth 앱에 테스트 계정 소유 Google 계정을 "테스터"로 등록
OAuth 클라이언트가 속한 GCP 프로젝트가 "테스트" 게시 상태면, 사전에 등록된
이메일만 로그인 동의가 가능하다. 1단계에서 쓴 새 Google 계정이 등록돼 있지
않으면 `access_denied` 에러가 난다.

1. **프로덕션 계정(h0912w)**으로 로그인 → **https://console.cloud.google.com/auth/audience**
   (2026년 개편된 "Google Auth Platform" UI, 구 "OAuth 동의 화면"의 후신).
2. 프로젝트 선택기에서 CLIENT_ID를 발급한 프로젝트가 맞는지 확인.
3. **"Test users"** 섹션 → **"Add users"** → 1단계에서 쓴 이메일 추가 → **"Save"**.

출처: [Google Workspace 공식 문서](https://developers.google.com/workspace/guides/configure-oauth-consent),
[Google Cloud 지원 문서](https://support.google.com/cloud/answer/15549945?hl=en)

### 4단계 — 테스트 계정 소유 Google 계정으로 REFRESH_TOKEN 발급
**중요**: developer-token은 프로덕션 계정 것을 재사용하지만, **REFRESH_TOKEN은
반드시 테스트 계층에 접근 권한이 있는 사용자(1단계 계정)로 발급해야 한다.**
프로덕션 계정(h0912w)의 기존 REFRESH_TOKEN으로 테스트 계정을 조회하면
`USER_PERMISSION_DENIED`가 난다 — developer-token과 REFRESH_TOKEN(호출자 신원)은
서로 다른 개념이다.

`tools/get_refresh_token.py`가 Python 환경에서 이 과정을 자동화한다(로컬
8080 포트로 인가 코드를 받는 방식). Python이 없는 환경에서는 curl만으로도
가능하다:

```bash
# 1) 인가 URL을 브라우저로 열고 테스트 계정 소유 Google 계정으로 로그인/승인
echo "https://accounts.google.com/o/oauth2/auth?client_id=$CLIENT_ID&redirect_uri=http://localhost:8080&response_type=code&scope=https://www.googleapis.com/auth/adwords&access_type=offline&prompt=consent"

# 2) 로컬에 리스너가 없으면 브라우저가 "연결 불가" 에러를 띄우지만 주소창에
#    code=... 파라미터가 그대로 남아있다 - 그 값을 복사한다.

# 3) code를 refresh_token으로 교환
curl -s -X POST https://oauth2.googleapis.com/token \
  --data-urlencode "code=$CODE" \
  --data-urlencode "client_id=$CLIENT_ID" \
  --data-urlencode "client_secret=$CLIENT_SECRET" \
  --data-urlencode "redirect_uri=http://localhost:8080" \
  --data-urlencode "grant_type=authorization_code"
```

**주의**: OAuth 앱이 "테스트" 게시 상태인 동안 발급되는 REFRESH_TOKEN은
`refresh_token_expires_in`이 약 **7일(604799초)**로 제한된다(응답 JSON에서
직접 확인됨). 7일마다 재발급이 필요하다 — 영구적으로 쓰려면 GCP 프로젝트를
"프로덕션" 게시 상태로 전환(Google 검증 절차 필요)해야 한다.

### 5단계 — 개발자 토큰이 다른 프로젝트에 페어링된 경우
개발자 토큰은 **처음 성공한 API 요청의 GCP 프로젝트에 영구적으로 고정**된다
(Google 공식 동작, 재변경 불가). CLIENT_ID를 새 프로젝트로 바꿨는데 기존
개발자 토큰을 그대로 쓰면 `DEVELOPER_TOKEN_PROHIBITED`("Developer token is not
allowed with project 'N'")가 난다.

출처: [Google Ads API 개발자 커뮤니티](https://groups.google.com/g/adwords-api/c/oNv7MRPGyAY)

해결: 프로덕션 계정 API 센터(`https://ads.google.com/aw/apicenter`)에서
**개발자 토큰을 재설정(reset)**한다. 재설정된 새 토큰으로 새 프로젝트를 대상으로
첫 API 호출을 하면, 그 시점부터 새 프로젝트에 페어링된다.

## 최종 검증 방법 (curl, Python 불필요)

```bash
curl -s -X POST "https://googleads.googleapis.com/v23/customers/$CUSTOMER_ID:generateKeywordIdeas" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "developer-token: $DEVELOPER_TOKEN" \
  -H "login-customer-id: $LOGIN_CUSTOMER_ID" \
  -H "Content-Type: application/json" \
  -d '{"keywordSeed":{"keywords":["fitness tracker"]},"keywordPlanNetwork":"GOOGLE_SEARCH","language":"languageConstants/1000","includeAdultKeywords":false}'
```

`avgMonthlySearches`/`competitionIndex`가 포함된 정상 응답이 오면 5개 값
조합이 전부 맞다는 뜻이다 — `python run.py --mode qa`로 넘어가도 된다.

## 겪었던 에러와 원인 요약표

| 에러 | 원인 | 해결 |
|---|---|---|
| 계정 선택 화면에 "관리자 (폐쇄)" | 정말로 폐기된 계정 (테스트 계정의 정상 취소 표시와는 다름 — 빨간 "테스트 계정" 배지 유무로 구분) | 그 계정 포기, 새 테스트 계층 생성 |
| `USER_PERMISSION_DENIED` | 호출에 쓴 REFRESH_TOKEN의 사용자가 대상 계정 계층에 접근 권한 없음 | 대상 계층 소유 계정으로 REFRESH_TOKEN 재발급 |
| `access_denied` ("OAuth 앱이 테스트 중, 테스터 아님") | GCP 프로젝트 OAuth 동의 화면이 테스트 게시 상태, 로그인 계정이 테스터 명단에 없음 | Cloud Console Audience 페이지에서 테스터 추가 |
| `DEVELOPER_TOKEN_PROHIBITED` | 개발자 토큰이 이전 GCP 프로젝트에 영구 페어링됨 | API 센터에서 토큰 재설정 |
| `DEVELOPER_TOKEN_NOT_APPROVED` | 토큰이 "테스트 계정 액세스" 등급인데 진짜 프로덕션 계정을 조회 시도 | 테스트 계정으로 대상 변경 (Basic 액세스 신청은 불필요 — 키워드 조회는 테스트 등급으로 충분) |
| 캠페인 마법사에서 예산/결제 에러 | 테스트 계정은 결제수단이 없어서 발생하는 정상 동작 | 무시하고 "X"로 나가기, 계정은 이미 생성됨 |

## 관련 문서
- `memory/HANDOFF.md` 2026-08-26 항목 — 이 절차를 실측으로 밟은 시간순 기록
- `memory/ACTIVE_ISSUES.md`의 `GKP-001` — Keyword Planner 게이트 자체의 설계 결정 배경
