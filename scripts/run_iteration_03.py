from __future__ import annotations

from pathlib import Path

import pandas as pd

from iteration01_utils import PROJECT_ROOT, prepare_market_data
from run_iteration_01 import LOOKBACKS, build_event_rows, build_setups, summarize_events


CORE_T0_T1_BRANCHES = {"S1_T0_QQQ_leads", "S1_T1_QQQ_leads"}
CORE_T5_BRANCH = {"S1_T5_QQQ_leads"}
WILDCARD_BRANCH = {"S2_T4_DIA_leads"}
CORE_LOOKBACKS = {60, 252}
CORE_HOLDS = {3, 4, 5}
T5_RULES = {(60, 5), (252, 3), (252, 4), (252, 5)}
WILDCARD_RULES = {(60, 2), (128, 2)}


def add_branch_id(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["branch_id"] = out.apply(lambda r: f"{r['setup_code']}_{r['trigger_code']}_{r['leader']}_leads", axis=1)
    return out


def filter_iteration_03_summary(summary: pd.DataFrame) -> pd.DataFrame:
    if summary.empty:
        return summary

    summary = summary.copy()
    core_mask = (
        summary["branch_id"].isin(CORE_T0_T1_BRANCHES)
        & summary["high_lookback_days"].isin(CORE_LOOKBACKS)
        & summary["holding_window_days"].isin(CORE_HOLDS)
    )
    t5_mask = summary.apply(
        lambda r: r["branch_id"] in CORE_T5_BRANCH and (r["high_lookback_days"], r["holding_window_days"]) in T5_RULES,
        axis=1,
    )
    wildcard_mask = summary.apply(
        lambda r: r["branch_id"] in WILDCARD_BRANCH and (r["high_lookback_days"], r["holding_window_days"]) in WILDCARD_RULES,
        axis=1,
    )

    filtered = summary[core_mask | t5_mask | wildcard_mask].copy()
    filtered["iteration_id"] = "iteration_03"
    filtered["notes"] = filtered["notes"].astype(str) + "; narrowed_from=iteration_02"
    return filtered.sort_values(["branch_id", "high_lookback_days", "holding_window_days"]).reset_index(drop=True)


def filter_iteration_03_events(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return events

    events = add_branch_id(events)
    core_mask = (
        events["branch_id"].isin(CORE_T0_T1_BRANCHES)
        & events["high_lookback_days"].isin(CORE_LOOKBACKS)
        & events["holding_window_days"].isin(CORE_HOLDS)
    )
    t5_mask = events.apply(
        lambda r: r["branch_id"] in CORE_T5_BRANCH and (r["high_lookback_days"], r["holding_window_days"]) in T5_RULES,
        axis=1,
    )
    wildcard_mask = events.apply(
        lambda r: r["branch_id"] in WILDCARD_BRANCH and (r["high_lookback_days"], r["holding_window_days"]) in WILDCARD_RULES,
        axis=1,
    )
    return events[core_mask | t5_mask | wildcard_mask].copy().reset_index(drop=True)


def build_comparison_tables(summary: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if summary.empty:
        return pd.DataFrame(), pd.DataFrame()

    t0_t1 = summary[summary["branch_id"].isin({"S1_T0_QQQ_leads", "S1_T1_QQQ_leads"})].copy()
    t0_t1["trigger_family"] = t0_t1["branch_id"].str.extract(r"S1_(T\d)_QQQ_leads")
    t0_t1 = t0_t1[[
        "trigger_family",
        "high_lookback_days",
        "holding_window_days",
        "sample_count",
        "avg_excess_return",
        "hit_rate",
        "headline_verdict",
    ]].sort_values(["high_lookback_days", "holding_window_days", "trigger_family"]).reset_index(drop=True)

    t0_t5 = summary[summary["branch_id"].isin({"S1_T0_QQQ_leads", "S1_T5_QQQ_leads"})].copy()
    t0_t5["trigger_family"] = t0_t5["branch_id"].str.extract(r"S1_(T\d)_QQQ_leads")
    t0_t5 = t0_t5[[
        "trigger_family",
        "high_lookback_days",
        "holding_window_days",
        "sample_count",
        "avg_excess_return",
        "hit_rate",
        "headline_verdict",
    ]].sort_values(["high_lookback_days", "holding_window_days", "trigger_family"]).reset_index(drop=True)

    return t0_t1, t0_t5


def update_registry(registry_path: Path, iteration_summary: pd.DataFrame) -> None:
    if registry_path.exists():
        existing = pd.read_csv(registry_path)
        existing = existing[existing["iteration_id"] != "iteration_03"].copy()
        combined = pd.concat([existing, iteration_summary], ignore_index=True)
    else:
        combined = iteration_summary.copy()
    combined.to_csv(registry_path, index=False)


def main() -> None:
    results_dir = PROJECT_ROOT / "results"
    raw_dir = results_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    df = prepare_market_data(LOOKBACKS)
    setups = build_setups(df)
    events = build_event_rows(df, setups)
    summary = summarize_events(events, setups)

    iteration_03_summary = filter_iteration_03_summary(summary)
    iteration_03_events = filter_iteration_03_events(events)
    t0_t1, t0_t5 = build_comparison_tables(iteration_03_summary)

    summary_path = results_dir / "iteration_03_summary.csv"
    t0_t1_path = results_dir / "iteration_03_t0_vs_t1.csv"
    t0_t5_path = results_dir / "iteration_03_t0_vs_t5.csv"
    events_path = raw_dir / "iteration_03_events.csv"
    registry_path = results_dir / "experiment_registry.csv"

    iteration_03_summary.to_csv(summary_path, index=False)
    if not t0_t1.empty:
        t0_t1.to_csv(t0_t1_path, index=False)
    if not t0_t5.empty:
        t0_t5.to_csv(t0_t5_path, index=False)
    if not iteration_03_events.empty:
        out = iteration_03_events.copy()
        if "setup_date" in out.columns:
            out["setup_date"] = pd.to_datetime(out["setup_date"]).dt.strftime("%Y-%m-%d")
        if "trigger_date" in out.columns:
            out["trigger_date"] = pd.to_datetime(out["trigger_date"]).dt.strftime("%Y-%m-%d")
        out.to_csv(events_path, index=False)

    update_registry(registry_path, iteration_03_summary)

    print(f"Iteration 03 summary rows: {len(iteration_03_summary):,}")
    print(f"Iteration 03 event rows: {len(iteration_03_events):,}")
    print(f"Summary file: {summary_path}")
    print(f"T0 vs T1 file: {t0_t1_path}")
    print(f"T0 vs T5 file: {t0_t5_path}")


if __name__ == "__main__":
    main()
