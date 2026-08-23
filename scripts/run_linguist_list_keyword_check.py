"""LINGUIST List 후보 Keyword Planner 조회 (2026-08-23, 사용자 지시).

candidates.csv(scripts/generate_linguist_list_candidates.py 산출물)를 이
프로젝트 기존 규칙(config/keyword_metrics.yaml의 avg_monthly_searches_min /
competition_index_exact 게이트, keyword_metrics_client.py)으로 그대로
조회한다 - SAAS_WORDS_TWO 표준 파이프라인의 공유 캐시(output/deliverables/
history/*)와는 완전히 분리된 별도 산출물이다(스키마가 다르고 - industry/
ai_approved 필드 없음 - 목적도 다름).

재시작 가능: 이미 조회된 후보는 자체 캐시에서 스킵하고, 하루 예산
(free_tier_budget)을 넘으면 KeywordMetricsBudgetExceeded를 잡아 정직하게
멈춘다 - 다음 날 이 스크립트를 다시 실행하면 남은 후보부터 이어서 조회한다.

사용:
    python scripts/run_linguist_list_keyword_check.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from saas_words_two import config, ids  # noqa: E402
from saas_words_two.contracts import atomic_write_text  # noqa: E402
from saas_words_two.keyword_metrics_client import (  # noqa: E402
    ApiRuntimeConfig,
    KeywordMetricsBudgetExceeded,
    KeywordMetricsClient,
    credentials_from_env,
    load_env_file,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "output" / "deliverables" / "linguist_list"
CANDIDATES_PATH = OUT_DIR / "candidates.csv"
CACHE_PATH = OUT_DIR / "keyword_metrics_cache.csv"
PASSED_PATH = OUT_DIR / "keyword_metrics_passed.csv"

_CACHE_COLUMNS = ("title", "avg_monthly_searches", "competition_index", "api_status", "gate_passed", "checked_at")


def _load_cache() -> dict[str, dict]:
    if not CACHE_PATH.exists():
        return {}
    with CACHE_PATH.open("r", encoding="utf-8", newline="") as f:
        return {row["title"]: row for row in csv.DictReader(f)}


def _write_cache(cache: dict[str, dict]) -> None:
    ordered = sorted(cache.values(), key=lambda r: r["title"])
    with_header = [dict(zip(_CACHE_COLUMNS, [r[c] for c in _CACHE_COLUMNS])) for r in ordered]

    import io

    full_buffer = io.StringIO()
    writer = csv.DictWriter(full_buffer, fieldnames=_CACHE_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(with_header)
    atomic_write_text(CACHE_PATH, full_buffer.getvalue())

    passed_buffer = io.StringIO()
    passed_writer = csv.DictWriter(passed_buffer, fieldnames=_CACHE_COLUMNS, lineterminator="\n")
    passed_writer.writeheader()
    passed_writer.writerows([r for r in with_header if r["gate_passed"] == "True"])
    atomic_write_text(PASSED_PATH, passed_buffer.getvalue())


def main() -> None:
    if not CANDIDATES_PATH.exists():
        raise SystemExit(f"candidates.csv not found: {CANDIDATES_PATH} - run generate_linguist_list_candidates.py first")

    with CANDIDATES_PATH.open("r", encoding="utf-8", newline="") as f:
        all_candidates = [row["candidate"] for row in csv.DictReader(f)]

    cache = _load_cache()
    pending = [c for c in all_candidates if c not in cache]
    # 2026-08-23: 후보가 알파벳순(candidates.csv)이라 하루 예산이 우연히
    # 가장 긴(4~5단어) 롱테일 조합에 먼저 소모돼 데이터가 거의 없었다
    # (1일차 20,400개 중 실제 metrics가 있던 건 8개뿐). 짧은 조합(단어 수
    # 적음 = 실제 검색량이 있을 확률이 높음)을 먼저 조회하도록 정렬 -
    # 이미 캐시된 항목은 건드리지 않고 순서만 바꾼다.
    pending.sort(key=lambda c: (len(c.split()), c))

    print(f"total candidates: {len(all_candidates)}, already checked: {len(cache)}, pending: {len(pending)}")
    if not pending:
        print("nothing to do - all candidates already checked")
        return

    cfg = config.load_keyword_metrics_config(PROJECT_ROOT)
    searches_min = cfg["avg_monthly_searches_min"]
    competition_exact = cfg["competition_index_exact"]
    api_cfg = cfg.get("api", {})
    runtime = ApiRuntimeConfig(
        batch_size=api_cfg.get("batch_size", 20),
        free_tier_budget=api_cfg.get("free_tier_budget", 1000),
        min_request_interval_ms=api_cfg.get("min_request_interval_ms", 500),
        geo_target_constants=api_cfg.get("geo_target_constants", ""),
        language=api_cfg.get("language", "languageConstants/1000"),
        keyword_plan_network=api_cfg.get("keyword_plan_network", "GOOGLE_SEARCH"),
    )
    credentials_path = Path(api_cfg.get("credentials_env_path", ".env.local"))
    if not credentials_path.is_absolute():
        credentials_path = PROJECT_ROOT / credentials_path
    env = load_env_file(credentials_path)
    creds = credentials_from_env(env)

    def _persist_batch(records: list) -> None:
        checked_at = ids.now_kst().isoformat()
        for record in records:
            gate_passed = (
                record.avg_monthly_searches is not None
                and record.competition_index is not None
                and record.avg_monthly_searches >= searches_min
                and record.competition_index == competition_exact
            )
            cache[record.word] = {
                "title": record.word,
                "avg_monthly_searches": "" if record.avg_monthly_searches is None else record.avg_monthly_searches,
                "competition_index": "" if record.competition_index is None else record.competition_index,
                "api_status": record.api_status,
                "gate_passed": str(gate_passed),
                "checked_at": checked_at,
            }
        _write_cache(cache)

    client = KeywordMetricsClient(creds, runtime, on_batch_fn=_persist_batch)

    try:
        client.fetch_metrics(pending)
    except KeywordMetricsBudgetExceeded as exc:
        print(f"budget exhausted this run: {exc}")
        print(f"checked so far (all-time): {len(cache)}/{len(all_candidates)} - re-run this script later to continue")
        return

    print(f"done - checked all {len(all_candidates)} candidates")


if __name__ == "__main__":
    main()
