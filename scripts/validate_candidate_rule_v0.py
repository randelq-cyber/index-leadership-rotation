from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import pandas as pd

from iteration01_utils import PROJECT_ROOT, prepare_market_data
from run_iteration_01 import LOOKBACKS, build_event_rows, build_setups


@dataclass(frozen=True)
class RuleConfig:
    rule_id: str
    branch_id: str
    lookback: int
    hold: int
    family: str


RULES: List[RuleConfig] = [
    RuleConfig("T0_60_4", "S1_T0_QQQ_leads", 60, 4, "T0"),
    RuleConfig("T1_60_4", "S1_T1_QQQ_leads", 60, 4, "T1"),
    RuleConfig("T0_60_5", "S1_T0_QQQ_leads", 60, 5, "T0"),
    RuleConfig("T5_60_5", "S1_T5_QQQ_leads", 60, 5, "T5"),
    RuleConfig("T0_252_4", "S1_T0_QQQ_leads", 252, 4, "T0"),
    RuleConfig("T1_252_4", "S1_T1_QQQ_leads", 252, 4, "T1"),
    RuleConfig("T5_252_4", "S1_T5_QQQ_leads", 252, 4, "T5"),
    RuleConfig("T0_252_5", "S1_T0_QQQ_leads", 252, 5, "T0"),
    RuleConfig("T1_252_5", "S1_T1_QQQ_leads", 252, 5, "T1"),
    RuleConfig("T5_252_5", "S1_T5_QQQ_leads", 252, 5, "T5"),
]
COST_BPS_GRID = [0, 10, 20, 40]


def add_branch_id(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["branch_id"] = out.apply(lambda r: f"{r['setup_code']}_{r['trigger_code']}_{r['leader']}_leads", axis=1)
    return out


def compute_open_to_open_excess(df: pd.DataFrame, row: pd.Series) -> float | None:
    trigger_idx = int(row["trigger_idx"])
    hold = int(row["holding_window_days"])
    leader = row["leader"]
    laggard = row["laggard"]

    entry_idx = trigger_idx + 1
    exit_idx = entry_idx + hold
    if exit_idx >= len(df):
        return None

    lag_entry = df.iloc[entry_idx][f"{laggard}_open"]
    lag_exit = df.iloc[exit_idx][f"{laggard}_open"]
    lead_entry = df.iloc[entry_idx][f"{leader}_open"]
    lead_exit = df.iloc[exit_idx][f"{leader}_open"]

    if pd.isna([lag_entry, lag_exit, lead_entry, lead_exit]).any():
        return None

    lag_ret = (lag_exit / lag_entry) - 1.0
    lead_ret = (lead_exit / lead_entry) - 1.0
    return lag_ret - lead_ret


def select_non_overlapping(df_prices: pd.DataFrame, events: pd.DataFrame, rule: RuleConfig) -> pd.DataFrame:
    subset = events[
        (events["branch_id"] == rule.branch_id)
        & (events["high_lookback_days"] == rule.lookback)
        & (events["holding_window_days"] == rule.hold)
        & (events["triggered"] == True)
    ].copy()

    if subset.empty:
        return subset

    subset = subset.sort_values(["trigger_idx", "setup_idx"]).reset_index(drop=True)
    chosen_rows = []
    last_exit_idx = -1

    for _, row in subset.iterrows():
        trigger_idx = int(row["trigger_idx"])
        entry_idx = trigger_idx + 1
        exit_idx = entry_idx + rule.hold
        if exit_idx >= len(df_prices):
            continue
        if entry_idx <= last_exit_idx:
            continue

        open_excess = compute_open_to_open_excess(df_prices, row)
        if open_excess is None:
            continue

        chosen = row.copy()
        chosen["rule_id"] = rule.rule_id
        chosen["family"] = rule.family
        chosen["entry_idx"] = entry_idx
        chosen["exit_idx"] = exit_idx
        chosen["entry_date"] = df_prices.index[entry_idx]
        chosen["exit_date"] = df_prices.index[exit_idx]
        chosen["open_to_open_excess"] = open_excess
        chosen_rows.append(chosen)
        last_exit_idx = exit_idx

    if not chosen_rows:
        return pd.DataFrame()
    return pd.DataFrame(chosen_rows)


def build_validation_summary(all_events: pd.DataFrame) -> pd.DataFrame:
    if all_events.empty:
        return pd.DataFrame()

    rows = []
    for rule_id, group in all_events.groupby("rule_id"):
        rows.append({
            "rule_id": rule_id,
            "family": group["family"].iloc[0],
            "branch_id": group["branch_id"].iloc[0],
            "lookback": int(group["high_lookback_days"].iloc[0]),
            "hold": int(group["holding_window_days"].iloc[0]),
            "trade_count_nonoverlap": len(group),
            "avg_excess_close_to_close": group["excess_return"].mean(),
            "hit_rate_close_to_close": (group["excess_return"] > 0).mean(),
            "avg_excess_open_to_open": group["open_to_open_excess"].mean(),
            "median_excess_open_to_open": group["open_to_open_excess"].median(),
            "hit_rate_open_to_open": (group["open_to_open_excess"] > 0).mean(),
        })

    summary = pd.DataFrame(rows).sort_values(["family", "lookback", "hold"]).reset_index(drop=True)
    return summary


def build_cost_sensitivity(all_events: pd.DataFrame) -> pd.DataFrame:
    if all_events.empty:
        return pd.DataFrame()

    rows = []
    for rule_id, group in all_events.groupby("rule_id"):
        base = group["open_to_open_excess"].astype(float)
        for bps in COST_BPS_GRID:
            cost = bps / 10000.0
            net = base - cost
            rows.append({
                "rule_id": rule_id,
                "family": group["family"].iloc[0],
                "lookback": int(group["high_lookback_days"].iloc[0]),
                "hold": int(group["holding_window_days"].iloc[0]),
                "total_roundtrip_cost_bps": bps,
                "avg_net_excess": net.mean(),
                "median_net_excess": net.median(),
                "hit_rate_net": (net > 0).mean(),
                "trade_count_nonoverlap": len(group),
            })
    return pd.DataFrame(rows).sort_values(["rule_id", "total_roundtrip_cost_bps"]).reset_index(drop=True)


def main() -> None:
    results_dir = PROJECT_ROOT / "results"
    raw_dir = results_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    prices = prepare_market_data(LOOKBACKS)
    setups = build_setups(prices)
    events = build_event_rows(prices, setups)
    events = add_branch_id(events)

    selected = []
    for rule in RULES:
        chosen = select_non_overlapping(prices, events, rule)
        if not chosen.empty:
            selected.append(chosen)

    all_events = pd.concat(selected, ignore_index=True) if selected else pd.DataFrame()
    validation = build_validation_summary(all_events)
    cost_sensitivity = build_cost_sensitivity(all_events)

    validation_path = results_dir / "candidate_rule_v0_validation.csv"
    cost_path = results_dir / "candidate_rule_v0_cost_sensitivity.csv"
    events_path = raw_dir / "candidate_rule_v0_trades.csv"

    validation.to_csv(validation_path, index=False)
    cost_sensitivity.to_csv(cost_path, index=False)
    if not all_events.empty:
        out = all_events.copy()
        out["setup_date"] = pd.to_datetime(out["setup_date"]).dt.strftime("%Y-%m-%d")
        out["trigger_date"] = pd.to_datetime(out["trigger_date"]).dt.strftime("%Y-%m-%d")
        out["entry_date"] = pd.to_datetime(out["entry_date"]).dt.strftime("%Y-%m-%d")
        out["exit_date"] = pd.to_datetime(out["exit_date"]).dt.strftime("%Y-%m-%d")
        out.to_csv(events_path, index=False)

    print(f"Validated rule configs: {validation['rule_id'].nunique() if not validation.empty else 0}")
    print(f"Non-overlapping trades: {len(all_events):,}")
    print(f"Validation summary: {validation_path}")
    print(f"Cost sensitivity: {cost_path}")


if __name__ == "__main__":
    main()
