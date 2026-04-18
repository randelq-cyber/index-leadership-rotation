from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd

from iteration01_utils import PROJECT_ROOT, prepare_market_data
from run_iteration_01 import LOOKBACKS, build_event_rows, build_setups


TARGET_TRIGGERS = {"T1", "T5"}
TARGET_LOOKBACKS = {60, 128, 252}
HORIZONS = [1, 2, 3, 4, 5]


def add_branch_id(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["branch_id"] = out.apply(lambda r: f"{r['setup_code']}_{r['trigger_code']}_{r['leader']}_leads", axis=1)
    out["direction"] = out.apply(lambda r: f"{r['leader']} leads / {r['laggard']} lags", axis=1)
    return out


def unique_trigger_events(events: pd.DataFrame) -> pd.DataFrame:
    triggered = events[
        (events["triggered"] == True)
        & (events["trigger_code"].isin(TARGET_TRIGGERS))
        & (events["high_lookback_days"].isin(TARGET_LOOKBACKS))
    ].copy()

    cols = [
        "setup_code",
        "setup_definition",
        "high_lookback_days",
        "leader",
        "laggard",
        "context_filter",
        "trigger_code",
        "trigger_definition",
        "setup_idx",
        "setup_date",
        "trigger_idx",
        "trigger_date",
        "leader_strength_definition",
        "laggard_definition",
    ]
    triggered = triggered[cols].drop_duplicates().reset_index(drop=True)
    return add_branch_id(triggered)


def compute_close_return(df: pd.DataFrame, idx: int, symbol: str, horizon: int) -> float | None:
    end_idx = idx + horizon
    if end_idx >= len(df):
        return None
    start_price = df.iloc[idx][f"{symbol}_close"]
    end_price = df.iloc[end_idx][f"{symbol}_close"]
    if pd.isna([start_price, end_price]).any():
        return None
    return (end_price / start_price) - 1.0


def build_event_horizon_rows(prices: pd.DataFrame, trigger_events: pd.DataFrame) -> pd.DataFrame:
    rows: List[dict] = []
    for _, event in trigger_events.iterrows():
        trigger_idx = int(event["trigger_idx"])
        for horizon in HORIZONS:
            laggard_abs = compute_close_return(prices, trigger_idx, event["laggard"], horizon)
            leader_abs = compute_close_return(prices, trigger_idx, event["leader"], horizon)
            if laggard_abs is None or leader_abs is None:
                continue
            rows.append({
                **event.to_dict(),
                "horizon_day": horizon,
                "laggard_abs_return": laggard_abs,
                "leader_abs_return": leader_abs,
                "excess_return": laggard_abs - leader_abs,
            })
    return pd.DataFrame(rows)


def summarize_event_horizons(event_rows: pd.DataFrame) -> pd.DataFrame:
    if event_rows.empty:
        return pd.DataFrame()

    summary = (
        event_rows.groupby([
            "setup_code",
            "setup_definition",
            "trigger_code",
            "trigger_definition",
            "high_lookback_days",
            "leader",
            "laggard",
            "direction",
            "horizon_day",
        ])
        .agg(
            sample_count=("excess_return", "size"),
            avg_excess_return=("excess_return", "mean"),
            median_excess_return=("excess_return", "median"),
            avg_laggard_abs_return=("laggard_abs_return", "mean"),
            median_laggard_abs_return=("laggard_abs_return", "median"),
            avg_leader_abs_return=("leader_abs_return", "mean"),
            median_leader_abs_return=("leader_abs_return", "median"),
        )
        .reset_index()
    )
    return summary.sort_values([
        "setup_code",
        "trigger_code",
        "high_lookback_days",
        "leader",
        "horizon_day",
    ]).reset_index(drop=True)


def main() -> None:
    results_dir = PROJECT_ROOT / "results"
    raw_dir = results_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    prices = prepare_market_data(LOOKBACKS)
    setups = build_setups(prices)
    events = build_event_rows(prices, setups)
    triggers = unique_trigger_events(events)
    event_rows = build_event_horizon_rows(prices, triggers)
    summary = summarize_event_horizons(event_rows)

    summary_path = results_dir / "t1_t5_day1_to_5_summary.csv"
    events_path = results_dir / "t1_t5_day1_to_5_events.csv"

    summary.to_csv(summary_path, index=False)
    if not event_rows.empty:
        out = event_rows.copy()
        out["setup_date"] = pd.to_datetime(out["setup_date"]).dt.strftime("%Y-%m-%d")
        out["trigger_date"] = pd.to_datetime(out["trigger_date"]).dt.strftime("%Y-%m-%d")
        out.to_csv(events_path, index=False)

    print(f"Unique trigger events: {len(triggers):,}")
    print(f"Event horizon rows: {len(event_rows):,}")
    print(f"Summary file: {summary_path}")
    print(f"Events file: {events_path}")


if __name__ == "__main__":
    main()
