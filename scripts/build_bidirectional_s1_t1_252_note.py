from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd

from iteration01_utils import PROJECT_ROOT, prepare_market_data
from run_iteration_01 import LOOKBACKS, build_setups


LOOKBACK = 252
HORIZONS = [1, 2, 3, 4, 5]
TRIGGER_SEARCH_DAYS = 10


def filtered_setups(prices: pd.DataFrame) -> pd.DataFrame:
    setups = build_setups(prices)
    setups = setups[
        (setups["setup_code"] == "S1")
        & (setups["high_lookback_days"] == LOOKBACK)
        & (setups["leader"].isin(["QQQ", "DIA"]))
        & (setups["laggard"].isin(["QQQ", "DIA"]))
        & (setups["leader"] != setups["laggard"])
    ].copy()
    setups["direction"] = setups.apply(lambda r: f"{r['leader']} leads / {r['laggard']} lags", axis=1)
    return setups.sort_values(["leader", "setup_idx"]).reset_index(drop=True)


def find_t1_3d_trigger(prices: pd.DataFrame, setup_idx: int, leader: str, laggard: str) -> int | None:
    start_idx = setup_idx + 1
    end_idx = min(len(prices) - 1, setup_idx + TRIGGER_SEARCH_DAYS)
    if start_idx > end_idx:
        return None

    for idx in range(start_idx, end_idx + 1):
        lag_ret = prices.iloc[idx][f"{laggard}_ret_3"]
        lead_ret = prices.iloc[idx][f"{leader}_ret_3"]
        prev_lag_ret = prices.iloc[idx - 1][f"{laggard}_ret_3"] if idx > 0 else None
        prev_lead_ret = prices.iloc[idx - 1][f"{leader}_ret_3"] if idx > 0 else None

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
    signals: List[dict] = []
    for _, setup in setups.iterrows():
        trigger_idx = find_t1_3d_trigger(prices, int(setup["setup_idx"]), setup["leader"], setup["laggard"])
        if trigger_idx is None:
            continue
        signals.append({
            "setup_code": setup["setup_code"],
            "setup_definition": setup["setup_definition"],
            "high_lookback_days": int(setup["high_lookback_days"]),
            "leader": setup["leader"],
            "laggard": setup["laggard"],
            "direction": setup["direction"],
            "setup_idx": int(setup["setup_idx"]),
            "setup_date": setup["setup_date"],
            "trigger_code": "T1_3d_turn",
            "trigger_idx": int(trigger_idx),
            "trigger_date": prices.index[trigger_idx],
        })

    if not signals:
        return pd.DataFrame()

    signal_df = pd.DataFrame(signals)
    signal_df = signal_df.sort_values(["direction", "trigger_idx", "setup_idx"]).drop_duplicates(
        subset=["direction", "leader", "laggard", "trigger_idx"], keep="first"
    )

    rows: List[dict] = []
    for _, signal in signal_df.iterrows():
        for horizon in HORIZONS:
            lag_abs = close_return(prices, int(signal["trigger_idx"]), signal["laggard"], horizon)
            lead_abs = close_return(prices, int(signal["trigger_idx"]), signal["leader"], horizon)
            if lag_abs is None or lead_abs is None:
                continue
            rows.append({
                **signal.to_dict(),
                "horizon_day": horizon,
                "laggard_abs_return": lag_abs,
                "leader_abs_return": lead_abs,
                "excess_return": lag_abs - lead_abs,
            })
    return pd.DataFrame(rows)


def max_drawdown(series: pd.Series) -> float:
    equity = (1 + series.fillna(0)).cumprod()
    peak = equity.cummax()
    drawdown = (equity / peak) - 1.0
    return drawdown.min()


def summarize(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame()

    rows = []
    for (direction, horizon), group in events.sort_values("trigger_date").groupby(["direction", "horizon_day"]):
        rows.append({
            "direction": direction,
            "horizon_day": horizon,
            "sample_count": len(group),
            "avg_excess_return": group["excess_return"].mean(),
            "avg_laggard_abs_return": group["laggard_abs_return"].mean(),
            "avg_leader_abs_return": group["leader_abs_return"].mean(),
            "hit_rate": (group["excess_return"] > 0).mean(),
            "max_drawdown_excess": max_drawdown(group["excess_return"]),
            "max_drawdown_laggard_abs": max_drawdown(group["laggard_abs_return"]),
        })
    return pd.DataFrame(rows).sort_values(["direction", "horizon_day"]).reset_index(drop=True)


def build_note(note_path: Path, setups: pd.DataFrame, summary: pd.DataFrame, events_path: Path, summary_path: Path) -> None:
    qqq_count = len(setups[setups["leader"] == "QQQ"])
    dia_count = len(setups[setups["leader"] == "DIA"])
    text = f"""# Production Note — S1 + T1 3-day turn + 252-day lookback

## Strategy template
This note packages the current production-style research definition for a symmetric version of the rule.

### Shared setup
On setup day:
1. SPY closes at a fresh 252-day high
2. The leader (QQQ or DIA) closes at a fresh 252-day high
3. The laggard is at least 1.0% below its own 252-day high
4. The laggard trails the leader by at least 2.0% over the prior 10 trading days

### Trigger
Within 10 trading days after setup, trigger when:
- laggard 3-day return minus leader 3-day return turns positive,
- after being non-positive on the prior day

### Holding horizons evaluated
- 1, 2, 3, 4, 5 trading days after the trigger

## Directions included
- QQQ leads / DIA lags
- DIA leads / QQQ lags

Setups found under this rule definition:
- QQQ leading setups: {qqq_count}
- DIA leading setups: {dia_count}

## Output files
- Summary metrics: `{summary_path}`
- Full trigger-date event log: `{events_path}`

## Included metrics
For each direction and holding horizon, the summary file includes:
- average excess return
- average laggard absolute return
- average leader absolute return
- hit rate
- max drawdown of excess-return sequence
- max drawdown of laggard absolute-return sequence

## Important note
This note makes the rule definition explicit and symmetric across both directions, but the historical strength of the two directions is not necessarily equal. The downstream production decision should still be informed by the summary metrics.
"""
    note_path.write_text(text, encoding="utf-8")


def main() -> None:
    results_dir = PROJECT_ROOT / "results"
    knowledge_dir = PROJECT_ROOT / "knowledge"

    prices = prepare_market_data(LOOKBACKS)
    setups = filtered_setups(prices)
    events = build_event_rows(prices, setups)
    summary = summarize(events)

    events_path = results_dir / "production_s1_t1_252_events.csv"
    summary_path = results_dir / "production_s1_t1_252_summary.csv"
    note_path = knowledge_dir / "production-note-s1-t1-252.md"

    if not events.empty:
        out = events.copy()
        out["setup_date"] = pd.to_datetime(out["setup_date"]).dt.strftime("%Y-%m-%d")
        out["trigger_date"] = pd.to_datetime(out["trigger_date"]).dt.strftime("%Y-%m-%d")
        out.to_csv(events_path, index=False)
    summary.to_csv(summary_path, index=False)
    build_note(note_path, setups, summary, events_path, summary_path)

    print(f"Setups included: {len(setups):,}")
    print(f"Triggered event rows: {len(events):,}")
    print(f"Summary file: {summary_path}")
    print(f"Events file: {events_path}")
    print(f"Note file: {note_path}")


if __name__ == "__main__":
    main()
