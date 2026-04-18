from __future__ import annotations

from pathlib import Path

import pandas as pd

from iteration01_utils import PROJECT_ROOT, prepare_market_data
from run_iteration_01 import LOOKBACKS, build_event_rows, build_setups, summarize_events


CORE_BRANCHES = {"S1_T1_QQQ_leads", "S1_T5_QQQ_leads", "S1_T0_QQQ_leads", "S1_T3_QQQ_leads"}
WILDCARD_BRANCHES = {"S2_T4_DIA_leads"}
CORE_LOOKBACKS = {60, 252}
CORE_HOLDS = {3, 4, 5}
WILDCARD_LOOKBACKS = {60, 128}
WILDCARD_HOLDS = {2, 3}


def add_branch_id(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["branch_id"] = out.apply(lambda r: f"{r['setup_code']}_{r['trigger_code']}_{r['leader']}_leads", axis=1)
    return out


def filter_iteration_02_summary(summary: pd.DataFrame) -> pd.DataFrame:
    if summary.empty:
        return summary

    core_mask = (
        summary["branch_id"].isin(CORE_BRANCHES)
        & summary["high_lookback_days"].isin(CORE_LOOKBACKS)
        & summary["holding_window_days"].isin(CORE_HOLDS)
    )
    wildcard_mask = (
        summary["branch_id"].isin(WILDCARD_BRANCHES)
        & summary["high_lookback_days"].isin(WILDCARD_LOOKBACKS)
        & summary["holding_window_days"].isin(WILDCARD_HOLDS)
    )
    filtered = summary[core_mask | wildcard_mask].copy()
    filtered["iteration_id"] = "iteration_02"
    filtered["notes"] = filtered["notes"].astype(str) + "; narrowed_from=iteration_01"
    return filtered.sort_values(["branch_id", "high_lookback_days", "holding_window_days"]).reset_index(drop=True)


def filter_iteration_02_events(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return events

    events = add_branch_id(events)
    core_mask = (
        events["branch_id"].isin(CORE_BRANCHES)
        & events["high_lookback_days"].isin(CORE_LOOKBACKS)
        & events["holding_window_days"].isin(CORE_HOLDS)
    )
    wildcard_mask = (
        events["branch_id"].isin(WILDCARD_BRANCHES)
        & events["high_lookback_days"].isin(WILDCARD_LOOKBACKS)
        & events["holding_window_days"].isin(WILDCARD_HOLDS)
    )
    return events[core_mask | wildcard_mask].copy().reset_index(drop=True)


def build_control_comparison(summary: pd.DataFrame) -> pd.DataFrame:
    if summary.empty:
        return pd.DataFrame()

    compare_rows = summary[
        summary["branch_id"].isin({"S1_T0_QQQ_leads", "S1_T1_QQQ_leads", "S1_T5_QQQ_leads"})
    ].copy()
    if compare_rows.empty:
        return compare_rows

    compare_rows["trigger_family"] = compare_rows["branch_id"].str.extract(r"S1_(T\d)_QQQ_leads")
    compare_rows = compare_rows[[
        "trigger_family",
        "high_lookback_days",
        "holding_window_days",
        "sample_count",
        "avg_excess_return",
        "hit_rate",
        "headline_verdict",
    ]].copy()
    return compare_rows.sort_values(["high_lookback_days", "holding_window_days", "trigger_family"]).reset_index(drop=True)


def update_registry(registry_path: Path, iteration_summary: pd.DataFrame) -> None:
    if registry_path.exists():
        existing = pd.read_csv(registry_path)
        existing = existing[existing["iteration_id"] != "iteration_02"].copy()
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

    iteration_02_summary = filter_iteration_02_summary(summary)
    iteration_02_events = filter_iteration_02_events(events)
    control_comparison = build_control_comparison(iteration_02_summary)

    summary_path = results_dir / "iteration_02_summary.csv"
    comparison_path = results_dir / "iteration_02_control_comparison.csv"
    registry_path = results_dir / "experiment_registry.csv"
    events_path = raw_dir / "iteration_02_events.csv"

    iteration_02_summary.to_csv(summary_path, index=False)
    if not control_comparison.empty:
        control_comparison.to_csv(comparison_path, index=False)
    if not iteration_02_events.empty:
        out = iteration_02_events.copy()
        if "setup_date" in out.columns:
            out["setup_date"] = pd.to_datetime(out["setup_date"]).dt.strftime("%Y-%m-%d")
        if "trigger_date" in out.columns:
            out["trigger_date"] = pd.to_datetime(out["trigger_date"]).dt.strftime("%Y-%m-%d")
        out.to_csv(events_path, index=False)

    update_registry(registry_path, iteration_02_summary)

    print(f"Iteration 02 summary rows: {len(iteration_02_summary):,}")
    print(f"Iteration 02 event rows: {len(iteration_02_events):,}")
    print(f"Summary file: {summary_path}")
    print(f"Control comparison: {comparison_path}")


if __name__ == "__main__":
    main()
