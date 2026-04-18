from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from iteration01_utils import PROJECT_ROOT, prepare_market_data


LOOKBACKS = [60, 128, 252]
HOLD_WINDOWS = [2, 3, 4, 5]
TRIGGER_SEARCH_DAYS = 10
LEADER_LAGGARD_PAIRS = [("QQQ", "DIA"), ("DIA", "QQQ")]
SETUP_LABELS = {
    "S1": "same-day strict non-confirmation",
    "S2": "rolling divergence",
}
TRIGGER_LABELS = {
    "T0": "baseline control",
    "T1": "relative-strength turn",
    "T2": "laggard 5-day breakout",
    "T3": "two-day relative thrust",
    "T4": "leader stall plus laggard strength",
    "T5": "gap compression",
}


def setup_s1(df: pd.DataFrame, idx: int, lookback: int, leader: str, laggard: str) -> bool:
    spy_at_high = bool(df.iloc[idx][f"SPY_at_high_{lookback}"])
    leader_at_high = bool(df.iloc[idx][f"{leader}_at_high_{lookback}"])
    laggard_at_high = bool(df.iloc[idx][f"{laggard}_at_high_{lookback}"])
    laggard_gap = df.iloc[idx][f"{laggard}_gap_{lookback}"]
    leader_ret10 = df.iloc[idx][f"{leader}_ret_10"]
    laggard_ret10 = df.iloc[idx][f"{laggard}_ret_10"]

    if pd.isna([laggard_gap, leader_ret10, laggard_ret10]).any():
        return False

    return (
        spy_at_high
        and leader_at_high
        and (not laggard_at_high)
        and laggard_gap >= 0.01
        and (leader_ret10 - laggard_ret10) >= 0.02
    )


def setup_s2(df: pd.DataFrame, idx: int, lookback: int, leader: str, laggard: str, s1_active: bool) -> bool:
    if s1_active:
        return False

    spy_gap = df.iloc[idx][f"SPY_gap_{lookback}"]
    leader_recent = bool(df.iloc[idx][f"{leader}_recent_high3_{lookback}"])
    laggard_recent = bool(df.iloc[idx][f"{laggard}_recent_high3_{lookback}"])
    leader_ret10 = df.iloc[idx][f"{leader}_ret_10"]
    laggard_ret10 = df.iloc[idx][f"{laggard}_ret_10"]

    if pd.isna([spy_gap, leader_ret10, laggard_ret10]).any():
        return False

    return (
        spy_gap <= 0.0025
        and leader_recent
        and (not laggard_recent)
        and (leader_ret10 - laggard_ret10) >= 0.02
    )


def find_trigger_index(df: pd.DataFrame, setup_idx: int, lookback: int, leader: str, laggard: str, trigger_code: str) -> Optional[int]:
    if trigger_code == "T0":
        return setup_idx

    start_idx = setup_idx + 1
    end_idx = min(len(df) - 1, setup_idx + TRIGGER_SEARCH_DAYS)
    if start_idx > end_idx:
        return None

    setup_gap = df.iloc[setup_idx][f"{laggard}_gap_{lookback}"]

    for idx in range(start_idx, end_idx + 1):
        leader_ret1 = df.iloc[idx][f"{leader}_ret_1"]
        leader_ret2 = df.iloc[idx][f"{leader}_ret_2"]
        leader_ret3 = df.iloc[idx][f"{leader}_ret_3"]
        laggard_ret1 = df.iloc[idx][f"{laggard}_ret_1"]
        laggard_ret2 = df.iloc[idx][f"{laggard}_ret_2"]
        laggard_ret3 = df.iloc[idx][f"{laggard}_ret_3"]
        laggard_gap = df.iloc[idx][f"{laggard}_gap_{lookback}"]

        if trigger_code == "T1":
            if idx == 0:
                continue
            prev_rel3 = df.iloc[idx - 1][f"{laggard}_ret_3"] - df.iloc[idx - 1][f"{leader}_ret_3"]
            curr_rel3 = laggard_ret3 - leader_ret3
            if pd.notna(curr_rel3) and pd.notna(prev_rel3) and curr_rel3 > 0 and prev_rel3 <= 0:
                return idx

        elif trigger_code == "T2":
            if idx < 5:
                continue
            prior_5d_high = df.iloc[idx - 5:idx][f"{laggard}_close"].max()
            if pd.notna(prior_5d_high) and df.iloc[idx][f"{laggard}_close"] > prior_5d_high:
                return idx

        elif trigger_code == "T3":
            rel2 = laggard_ret2 - leader_ret2
            if pd.notna(rel2) and rel2 >= 0.01:
                return idx

        elif trigger_code == "T4":
            if pd.notna(laggard_ret1) and pd.notna(leader_ret1) and laggard_ret1 > 0.005 and leader_ret1 <= 0.0:
                return idx

        elif trigger_code == "T5":
            if pd.notna(laggard_gap) and pd.notna(setup_gap) and setup_gap > 0 and laggard_gap <= 0.5 * setup_gap:
                return idx

    return None


def forward_return(df: pd.DataFrame, idx: int, symbol: str, hold_days: int) -> Optional[float]:
    end_idx = idx + hold_days
    if end_idx >= len(df):
        return None

    entry = df.iloc[idx][f"{symbol}_close"]
    exit_ = df.iloc[end_idx][f"{symbol}_close"]
    if pd.isna(entry) or pd.isna(exit_):
        return None
    return (exit_ / entry) - 1.0


def build_setups(df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict] = []

    for lookback in LOOKBACKS:
        for idx in range(len(df)):
            if pd.isna(df.iloc[idx][f"SPY_high_{lookback}"]):
                continue

            for leader, laggard in LEADER_LAGGARD_PAIRS:
                s1 = setup_s1(df, idx, lookback, leader, laggard)
                s2 = setup_s2(df, idx, lookback, leader, laggard, s1)

                if s1:
                    rows.append({
                        "setup_code": "S1",
                        "setup_definition": SETUP_LABELS["S1"],
                        "setup_idx": idx,
                        "setup_date": df.index[idx],
                        "high_lookback_days": lookback,
                        "leader": leader,
                        "laggard": laggard,
                        "context_filter": "SPY",
                        "leader_strength_definition": "leader at/near important high and >=2% ahead of laggard over prior 10 days",
                        "laggard_definition": "other non-SPY ETF not confirming high and trailing prior 10-day return",
                    })
                if s2:
                    rows.append({
                        "setup_code": "S2",
                        "setup_definition": SETUP_LABELS["S2"],
                        "setup_idx": idx,
                        "setup_date": df.index[idx],
                        "high_lookback_days": lookback,
                        "leader": leader,
                        "laggard": laggard,
                        "context_filter": "SPY",
                        "leader_strength_definition": "leader made a recent important high and >=2% ahead of laggard over prior 10 days",
                        "laggard_definition": "other non-SPY ETF failed to confirm recent high and trailed prior 10-day return",
                    })

    return pd.DataFrame(rows)


def build_event_rows(df: pd.DataFrame, setups: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict] = []
    trigger_codes = list(TRIGGER_LABELS.keys())

    for setup in setups.to_dict("records"):
        for trigger_code in trigger_codes:
            trigger_idx = find_trigger_index(
                df=df,
                setup_idx=setup["setup_idx"],
                lookback=setup["high_lookback_days"],
                leader=setup["leader"],
                laggard=setup["laggard"],
                trigger_code=trigger_code,
            )

            if trigger_idx is None:
                rows.append({
                    **setup,
                    "trigger_code": trigger_code,
                    "trigger_definition": TRIGGER_LABELS[trigger_code],
                    "trigger_idx": None,
                    "trigger_date": None,
                    "holding_window_days": None,
                    "laggard_return": None,
                    "comparison_return": None,
                    "excess_return": None,
                    "triggered": False,
                })
                continue

            for hold_days in HOLD_WINDOWS:
                laggard_return = forward_return(df, trigger_idx, setup["laggard"], hold_days)
                comparison_return = forward_return(df, trigger_idx, setup["leader"], hold_days)
                if laggard_return is None or comparison_return is None:
                    continue

                rows.append({
                    **setup,
                    "trigger_code": trigger_code,
                    "trigger_definition": TRIGGER_LABELS[trigger_code],
                    "trigger_idx": trigger_idx,
                    "trigger_date": df.index[trigger_idx],
                    "holding_window_days": hold_days,
                    "laggard_return": laggard_return,
                    "comparison_return": comparison_return,
                    "excess_return": laggard_return - comparison_return,
                    "triggered": True,
                })

    return pd.DataFrame(rows)


def summarize_events(events: pd.DataFrame, setups: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame()

    triggered = events[events["triggered"] == True].copy()
    if triggered.empty:
        return pd.DataFrame()

    setup_counts = (
        setups.groupby(["setup_code", "high_lookback_days", "leader"]) 
        .size()
        .rename("setup_count")
        .reset_index()
    )
    triggered_counts = (
        triggered.groupby(["setup_code", "trigger_code", "high_lookback_days", "leader"]) 
        .agg(triggered_setups=("setup_idx", "nunique"))
        .reset_index()
    )

    summary = (
        triggered.groupby([
            "setup_code",
            "setup_definition",
            "trigger_code",
            "trigger_definition",
            "high_lookback_days",
            "leader",
            "laggard",
            "context_filter",
            "leader_strength_definition",
            "laggard_definition",
            "holding_window_days",
        ])
        .agg(
            sample_count=("excess_return", "size"),
            avg_excess_return=("excess_return", "mean"),
            median_excess_return=("excess_return", "median"),
            hit_rate=("excess_return", lambda s: (s > 0).mean()),
        )
        .reset_index()
    )

    summary = summary.merge(setup_counts, on=["setup_code", "high_lookback_days", "leader"], how="left")
    summary = summary.merge(triggered_counts, on=["setup_code", "trigger_code", "high_lookback_days", "leader"], how="left")
    summary["expired_count"] = summary["setup_count"] - summary["triggered_setups"]

    def consistency_label(group: pd.DataFrame) -> str:
        years = pd.to_datetime(group["trigger_date"]).dt.year
        pre = group.loc[years < 2020, "excess_return"].mean() if (years < 2020).any() else None
        post = group.loc[years >= 2020, "excess_return"].mean() if (years >= 2020).any() else None
        if pre is None and post is None:
            return "insufficient"
        if pre is None:
            return "post-2020 only"
        if post is None:
            return "pre-2020 only"
        if pre > 0 and post > 0:
            return "positive pre/post 2020"
        if pre <= 0 and post <= 0:
            return "negative pre/post 2020"
        return "mixed pre/post 2020"

    consistency_rows = []
    for keys, group in triggered.groupby([
        "setup_code",
        "trigger_code",
        "high_lookback_days",
        "leader",
        "holding_window_days",
    ]):
        consistency_rows.append({
            "setup_code": keys[0],
            "trigger_code": keys[1],
            "high_lookback_days": keys[2],
            "leader": keys[3],
            "holding_window_days": keys[4],
            "subperiod_consistency": consistency_label(group),
        })
    consistency = pd.DataFrame(consistency_rows)
    summary = summary.merge(
        consistency,
        on=["setup_code", "trigger_code", "high_lookback_days", "leader", "holding_window_days"],
        how="left",
    )

    summary["headline_verdict"] = "needs_review"
    summary.loc[
        (summary["avg_excess_return"] > 0)
        & (summary["hit_rate"] > 0.5)
        & (summary["subperiod_consistency"].str.contains("positive", na=False)),
        "headline_verdict",
    ] = "promote"
    summary.loc[
        (summary["avg_excess_return"] <= 0)
        & (summary["hit_rate"] <= 0.5),
        "headline_verdict",
    ] = "kill"
    summary.loc[
        (summary["headline_verdict"] == "needs_review")
        & ((summary["avg_excess_return"] > 0) | (summary["hit_rate"] > 0.5)),
        "headline_verdict",
    ] = "revise"

    summary["branch_id"] = summary.apply(
        lambda r: f"{r['setup_code']}_{r['trigger_code']}_{r['leader']}_leads",
        axis=1,
    )
    summary["comparison_target"] = summary["leader"]
    summary["notes"] = summary.apply(
        lambda r: f"setups={int(r['setup_count'])}; triggered={int(r['triggered_setups'])}; expired={int(r['expired_count'])}; laggard={r['laggard']}",
        axis=1,
    )

    summary = summary[[
        "branch_id",
        "setup_definition",
        "high_lookback_days",
        "leader_strength_definition",
        "laggard_definition",
        "trigger_definition",
        "context_filter",
        "comparison_target",
        "holding_window_days",
        "sample_count",
        "avg_excess_return",
        "median_excess_return",
        "hit_rate",
        "subperiod_consistency",
        "headline_verdict",
        "notes",
    ]].copy()
    summary.insert(0, "iteration_id", "iteration_01")
    return summary.sort_values(["branch_id", "high_lookback_days", "holding_window_days"]).reset_index(drop=True)


def main() -> None:
    results_dir = PROJECT_ROOT / "results"
    raw_dir = results_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    df = prepare_market_data(LOOKBACKS)
    setups = build_setups(df)
    events = build_event_rows(df, setups)
    summary = summarize_events(events, setups)

    setups_path = raw_dir / "iteration_01_setups.csv"
    events_path = raw_dir / "iteration_01_events.csv"
    summary_path = results_dir / "iteration_01_summary.csv"
    registry_path = results_dir / "experiment_registry.csv"

    if not setups.empty:
        setups_out = setups.copy()
        setups_out["setup_date"] = pd.to_datetime(setups_out["setup_date"]).dt.strftime("%Y-%m-%d")
        setups_out.to_csv(setups_path, index=False)
    if not events.empty:
        events_out = events.copy()
        if "setup_date" in events_out.columns:
            events_out["setup_date"] = pd.to_datetime(events_out["setup_date"]).dt.strftime("%Y-%m-%d")
        if "trigger_date" in events_out.columns:
            events_out["trigger_date"] = pd.to_datetime(events_out["trigger_date"]).dt.strftime("%Y-%m-%d")
        events_out.to_csv(events_path, index=False)
    if not summary.empty:
        summary.to_csv(summary_path, index=False)
        summary.to_csv(registry_path, index=False)

    print(f"Loaded {len(df):,} aligned trading days")
    print(f"Setups found: {len(setups):,}")
    if not events.empty:
        triggered_count = int(events['triggered'].fillna(False).sum())
        print(f"Triggered event rows (including holding windows): {triggered_count:,}")
    else:
        print("Triggered event rows (including holding windows): 0")
    print(f"Summary rows: {len(summary):,}")
    print(f"Summary file: {summary_path}")


if __name__ == "__main__":
    main()
