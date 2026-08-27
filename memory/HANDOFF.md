# HANDOFF

- 상태: `PAUSED` (h0912ww 계정 잠금은 풀림·자격증명 검증 완료, `RUN-20260826-235551-KST`
  --resume은 아직 미실행 — 다음 세션이 이어서 할 일)

## 2026-08-27 갱신 — Termius SSH 세션 git push 정상화 (SSH 키 인증 적용)

Termius로 임의 단어(`sunset`/`harbor`) Keyword Planner 조회를 실제 API로 재검증
(둘 다 `api_status=success`, 검색량·경쟁지수 정상 반환 — 기존 검증과 일관됨,
추가 조치 불필요). 이어서 이 세션에서 `git push`를 시험해보니 실패
(`wincredman` 자격증명 저장소가 비대화형 SSH 세션에서 프롬프트를 못 띄움,
`origin`이 아직 HTTPS였고 `~/.ssh/`도 없어 `docs/operations/
14-remote-ssh-github-authentication.md`가 실제로는 한 번도 적용 안 된 상태였음
확인) → 문서 14 절차 그대로 실행: SSH 키 신규 생성 → 사용자가 GitHub에 공개키
등록 → `ssh -T git@github.com` 인증 성공 확인 → `origin`을 SSH URL로 전환 →
`git push` 정상 동작 확인(인증 프롬프트 없음). 상세는 `memory/ACTIVE_ISSUES.md`
`PROCESS-001`의 "2026-08-27 해결" 절 참고 — 이제 Termius 세션에서도 push가
PC 세션까지 미룰 필요 없이 정상 동작한다.

**다음 세션이 할 일**: 아래 "다음 세션이 할 일" 절(`RUN-20260826-235551-KST`
--resume)이 여전히 최우선 순위다 — 이번 갱신은 그 작업과 무관한 별도 확인.

## 2026-08-27 갱신 — h0912ww 계정 잠금 해제 확인, 자격증명 정상 작동 검증

사용자가 h0912ww 계정 잠금이 풀렸다고 확인해줘서, 기존 `.env.local`(h0912ww
소유 테스트 계층: 관리자 CID 7881658513/`LOGIN_CUSTOMER_ID`, 클라이언트 CID
5126977637/`CUSTOMER_ID`, 아래 "이번 세션에서 완료된 것" 절에서 이미 구성한 값
그대로)로 `keyword_metrics_client.KeywordMetricsClient.fetch_metrics(["fitness
tracker"])`를 실제 호출해 단어 1개를 조회했다. 결과: `avg_monthly_searches=135,000`,
`competition=HIGH`, `competition_index=100` — 검색량·경쟁지수 둘 다 정상 반환됨.
REFRESH_TOKEN 재발급 없이 기존 값 그대로 통과했다(즉 `invalid_grant`였던 원인은
토큰 자체 손상이 아니라 계정 잠금이었던 것으로 확인됨).

**다음 세션이 할 일**: `./.venv/Scripts/python.exe run.py --mode production --resume`으로
`RUN-20260826-235551-KST`를 이어서 실행 — 제목 생성/AI판정은 이미 끝났으므로
Keyword Planner 조회부터 바로 진행됨(재판정 불필요). h0913w 대체 계정 경로는
h0912ww가 정상 작동하는 것으로 확인됐으니 더 진행할 필요 없음(아래 절 참고,
필요 시 재검토).

## 2026-08-27 이전 진행 기록 — 대체 계정(h0913w) 시도 (h0912ww 정상화로 보류)

h0912ww 잠금이 안 풀려서, 완전히 새 계정으로 전환하는 대신 **h0913w(수년 전에
만든 기존 Google 계정, 옛 Ads 계정은 해지 상태라 무시)** 로 테스트 계층을 새로
만드는 중. 진행 상황:

- **완료**: h0913w 계정으로 테스트 관리자 계정 생성 완료 — 계정명 `H0913w`,
  **CID 890-341-2348** → `GOOGLE_ADS_LOGIN_CUSTOMER_ID` 후보값
  (`ads.google.com/aw/settings/manager` 화면 스크린샷으로 확인, 2026-08-27 01:10)
- **미확인**: 이 계정에 빨간 "테스트 계정" 배지가 실제로 떴는지 화면 캡처로는
  확인 안 됨 — 다음 스텝 진행 전에 확인 필요
- **미완료**: 2단계(그 밑에 테스트 클라이언트 계정 생성, `GOOGLE_ADS_CUSTOMER_ID`
  후보)는 아직 안 함
- **미완료**: 3단계(h0912w 프로덕션 계정으로 Cloud Console에서 h0913w를 OAuth
  테스터로 등록), 4단계(REFRESH_TOKEN 발급)도 아직

**다음 세션이 할 일(h0913w 경로로 계속 진행 시)**:
1. H0913w 관리자 계정에 빨간 "테스트 계정" 배지 확인
2. 그 밑에 테스트 클라이언트 계정 생성 → CID 기록
3. h0912w로 Cloud Console에서 h0913w(테스트 계정 소유 이메일)를 OAuth 테스터로 등록
4. h0913w로 REFRESH_TOKEN 발급, `.env.local` 4개 값(LOGIN_CUSTOMER_ID=890-341-2348,
   CUSTOMER_ID=신규, REFRESH_TOKEN=신규, 나머지는 기존 값 유지) 갱신
5. h0912ww 잠금이 그 사이 풀렸으면 h0912ww 경로(아래 "지금 막힌 지점" 섹션)와
   h0913w 경로 중 어느 쪽으로 최종 확정할지 결정 필요 — 현재 두 경로가 동시에
   미완료 상태로 남아있음
- **이번 세션 결론 요약**: 자격증명 교체는 완료·검증됐고, QA 라운드는 끝까지
  성공했다. 이어서 돌린 production 라운드는 **"생성+AI판정"까지만 끝나고
  "Keyword Planner 통과 확정"은 미완료** — 즉 이번 세션 목표(자격증명 교체 →
  QA → 단어생성 1라운드) 중 마지막 한 조각(라운드 최종 완주)이 Google 계정
  보안 잠금 때문에 못 끝났다. 코드/판정 로직 문제 아님, 순수 외부 인증 이슈.
- 현재 단계: run RUN-20260826-235551-KST(mode=production)가 `generate_and_review_titles`
  단계에서 `FAILED` — 제목 생성·AI 판정(3,320개 생성, 2,250 승인/1,070 거절)은
  이미 ledger(`output/deliverables/history/generated_candidates.csv`)에 정상 기록되고
  git에도 커밋+푸시됨(`9281f9a`). 실패 지점은 그 다음 Keyword Planner 조회 직전
  OAuth 토큰 갱신(`invalid_grant`)이었음 — **문서②③④(KP 통과표/단어리스트)는
  아직 이번 라운드분 갱신 안 됨, 최종 산출물 없음.**
- 마지막으로 성공 완료된 실행: QA-20260826-222651-KST (mode=qa, DONE, 커밋+푸시 완료)

## 지금 막힌 지점 (2026-08-27 새벽) — **해제됨, 위 2026-08-27 갱신 절 참고**

REFRESH_TOKEN이 몇 시간 전 정상 발급됐음에도 `invalid_grant`로 무효화되어 재발급을
시도하던 중, **Google이 h0912ww@gmail.com 계정의 로그인 자체를 보안상 일시 차단**했다
(짧은 시간에 반복된 OAuth 인증 시도가 "평소와 다른 활동"으로 감지됨).
브라우저 화면: "전화번호를 인증할 수 없습니다 — 실패한 시도 횟수가 너무 많음,
몇 시간 후에 다시 시도해주세요."

**다음 세션이 할 일 (몇 시간 후, 잠금 풀린 뒤)**:
1. h0912ww@gmail.com으로 https://accounts.google.com 정상 로그인되는지 먼저 확인
   (로그인 자체가 안 되면 아직 잠금이 안 풀린 것 - 더 기다릴 것)
2. 로그인 확인되면 REFRESH_TOKEN 재발급 (`docs/operations/15-google-ads-credential-setup.md`
   4단계 절차 그대로, curl 기반 — Python 불필요)
3. `.env.local`의 `GOOGLE_ADS_REFRESH_TOKEN` 갱신
4. `./.venv/Scripts/python.exe run.py --mode production --resume` 재실행
   (제목 생성/판정은 이미 끝났으므로 이번엔 Keyword Planner 조회부터 바로 진행됨 -
   재판정 불필요, 그대로 이어짐)
5. **주의**: OAuth 인증 시도를 짧은 시간에 반복하지 말 것 - 이번 잠금이 그것 때문에
   발생한 것으로 추정됨. 실패해도 몇 분 간격을 두고 재시도할 것.

## 이번 세션에서 완료된 것 (2026-08-26~27)

- Google Ads API 자격증명 전체 재구성 완료 및 실측 검증(`docs/operations/15-google-ads-credential-setup.md`
  참고 — 테스트 관리자(SAAS_WORDS_TWO_TEST, CID 7881658513, h0912ww 소유) + 테스트
  클라이언트(CID 5126977637) 신규 구성, 개발자 토큰은 h0912w API 센터에서 재설정)
- `.venv` 재생성 완료(Python 3.12 신규 설치, 기존 venv는 존재하지 않는 계정 경로를
  가리키고 있어 못 쓰는 상태였음)
- `scripts/git_checkpoint.py`의 `.env.example`이 `.env` 패턴에 걸려 매 라운드
  `SENSITIVE_FILES_BLOCKED`로 막히던 실제 버그 발견·수정(정규 테스트 추가, 144개
  전체 PASS 확인)
- QA-20260826-222651-KST 라운드 완주(DONE, 커밋 `a497ac3` 로컬+원격 푸시 확인)
  — 신규생성 50개, AI승인 45개, KP통과 0개(round-size 50 규모에서 정상)
- RUN-20260826-235551-KST(production, round-size 기본 10000이지만 조합공간
  제약으로 실제 3,320개 생성) 제목 생성+AI 판정까지 완료(2,250 승인) — Keyword
  Planner 조회 단계에서 위 인증 문제로 중단, `--resume`으로 이어갈 수 있음

## 다음 세션 참고

- 개발자 토큰 등급은 여전히 "테스트 계정 액세스"이며 문제 없음(Basic 신청 불필요,
  `generateKeywordIdeas`는 테스트 계정으로도 실제 검색량 반환 확인됨)
- REFRESH_TOKEN 발급 시 매번 새 Google 계정 로그인 세션이 필요 - 브라우저에
  h0912w로 이미 로그인돼 있으면 실수로 그 계정이 승인될 수 있으니
  `prompt=select_account+consent`로 계정 선택 화면을 강제할 것(이번 세션에서
  실제로 h0912w를 잘못 승인한 시행착오 있었음)
