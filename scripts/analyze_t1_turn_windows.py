from __future__ import annotations

from typing import List

import pandas as pd

from iteration01_utils import PROJECT_ROOT, prepare_market_data
from run_iteration_01 import LOOKBACKS, build_setups


TARGET_LOOKBACKS = {60, 128, 252}
TURN_WINDOWS = [1, 2, 3]
HORIZONS = [1, 2, 3, 4, 5]
TRIGGER_SEARCH_DAYS = 10


def core_setups(prices: pd.DataFrame) -> pd.DataFrame:
    setups = build_setups(prices)
    setups = setups[
        (setups["setup_code"] == "S1")
        & (setups["leader"] == "QQQ")
        & (setups["laggard"] == "DIA")
        & (setups["high_lookback_days"].isin(TARGET_LOOKBACKS))
    ].copy()
    return setups.sort_values(["high_lookback_days", "setup_idx"]).reset_index(drop=True)


def find_t1_variant_trigger(prices: pd.DataFrame, setup_idx: int, window: int) -> int | None:
    start_idx = setup_idx + 1
    end_idx = min(len(prices) - 1, setup_idx + TRIGGER_SEARCH_DAYS)
    if start_idx > end_idx:
        return None

    for idx in range(start_idx, end_idx + 1):
        lag_ret = prices.iloc[idx][f"DIA_ret_{window}"]
        lead_ret = prices.iloc[idx][f"QQQ_ret_{window}"]
        prev_lag_ret = prices.iloc[idx - 1][f"DIA_ret_{window}"] if idx > 0 else None
        prev_lead_ret = prices.iloc[idx - 1][f"QQQ_ret_{window}"] if idx > 0 else None

        if pd.isna([lag_ret, lead_ret]).any():
            continue
        curr_rel = lag_ret - lead_ret
        prev_rel = None if idx == 0 or pd.isna([prev_lag_ret, prev_lead_ret]).any() else prev_lag_ret - prev_lead_ret

        if prev_rel is not None and curr_rel > 0 and prev_rel <= 0:
            return idx
    return None


def close_return(prices: pd.DataFrame, idx: int, symbol: str, horizon: int) -> float | None:
    end_idx = idx + horizon
    if end_idx >= len(prices):
        return None
    start_price = prices.iloc[idx][f"{symbol}_close"]
    end_price = prices.iloc[end_idx][f"{symbol}_close"]
    if pd.isna([start_price, end_price]).any():
        return None
    return (end_price / start_price) - 1.0


def build_event_rows(prices: pd.DataFrame, setups: pd.DataFrame) -> pd.DataFrame:
    rows: List[dict] = []
    for _, setup in setups.iterrows():
        for window in TURN_WINDOWS:
            trigger_idx = find_t1_variant_trigger(prices, int(setup["setup_idx"]), window)
            if trigger_idx is None:
                continue
            trigger_date = prices.index[trigger_idx]
            for horizon in HORIZONS:
                lag_abs = close_return(prices, trigger_idx, "DIA", horizon)
                lead_abs = close_return(prices, trigger_idx, "QQQ", horizon)
                if lag_abs is None or lead_abs is None:
                    continue
                rows.append({
                    "setup_code": setup["setup_code"],
                    "setup_definition": setup["setup_definition"],
                    "high_lookback_days": int(setup["high_lookback_days"]),
                    "leader": setup["leader"],
                    "laggard": setup["laggard"],
                    "direction": "QQQ leads / DIA lags",
                    "setup_idx": int(setup["setup_idx"]),
                    "setup_date": setup["setup_date"],
                    "trigger_code": f"T1_{window}d_turn",
                    "trigger_window_days": window,
                    "trigger_idx": int(trigger_idx),
                    "trigger_date": trigger_date,
                    "horizon_day": horizon,
                    "laggard_abs_return": lag_abs,
                    "leader_abs_return": lead_abs,
                    "excess_return": lag_abs - lead_abs,
                })
    return pd.DataFrame(rows)


def summarize(event_rows: pd.DataFrame) -> pd.DataFrame:
    if event_rows.empty:
        return pd.DataFrame()

    summary = (
        event_rows.groupby([
            "setup_code",
            "setup_definition",
            "trigger_code",
            "trigger_window_days",
            "high_lookback_days",
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
    return summary.sort_values(["trigger_window_days", "high_lookback_days", "horizon_day"]).reset_index(drop=True)


def main() -> None:
    results_dir = PROJECT_ROOT / "results"
    prices = prepare_market_data(LOOKBACKS)
    setups = core_setups(prices)
    event_rows = build_event_rows(prices, setups)
    summary = summarize(event_rows)

    summary_path = results_dir / "t1_turn_windows_summary.csv"
    events_path = results_dir / "t1_turn_windows_events.csv"

    summary.to_csv(summary_path, index=False)
    if not event_rows.empty:
        out = event_rows.copy()
        out["setup_date"] = pd.to_datetime(out["setup_date"]).dt.strftime("%Y-%m-%d")
        out["trigger_date"] = pd.to_datetime(out["trigger_date"]).dt.strftime("%Y-%m-%d")
        out.to_csv(events_path, index=False)

    print(f"Core setups analyzed: {len(setups):,}")
    print(f"Event rows: {len(event_rows):,}")
    print(f"Summary file: {summary_path}")
    print(f"Events file: {events_path}")


if __name__ == "__main__":
    main()
