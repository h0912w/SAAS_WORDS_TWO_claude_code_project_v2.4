# HANDOFF

- 상태: `PAUSED` (Google 계정 보안 잠금으로 API 인증 일시 불가 — 코드/판정 문제 아님)
- 현재 단계: run RUN-20260826-235551-KST(mode=production)가 `generate_and_review_titles`
  단계에서 `FAILED` — 제목 생성·AI 판정(3,320개 생성, 2,250 승인/1,070 거절)은
  이미 ledger(`output/deliverables/history/generated_candidates.csv`)에 정상 기록됨.
  실패 지점은 그 다음 Keyword Planner 조회 직전 OAuth 토큰 갱신(`invalid_grant`)이었음.
- 마지막으로 성공 완료된 실행: QA-20260826-222651-KST (mode=qa, DONE, 커밋+푸시 완료)

## 지금 막힌 지점 (2026-08-27 새벽)

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
