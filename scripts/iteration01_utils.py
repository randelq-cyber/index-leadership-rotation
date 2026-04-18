from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"


def load_data_config() -> dict:
    local_path = CONFIG_DIR / "data-sources.local.json"
    example_path = CONFIG_DIR / "data-sources.example.json"
    config_path = local_path if local_path.exists() else example_path
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_price_csv(price_dir: Path, symbol: str) -> pd.DataFrame:
    path = price_dir / f"{symbol}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing price file for {symbol}: {path}")

    df = pd.read_csv(path)
    required = {"Date", "Open", "High", "Low", "Close", "Volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path} missing columns: {sorted(missing)}")

    df["Date"] = pd.to_datetime(df["Date"], utc=True).dt.tz_localize(None).dt.normalize()
    df = df.rename(columns=str.lower)
    df = df[["date", "open", "high", "low", "close", "volume"]].copy()
    df = df.sort_values("date").drop_duplicates(subset=["date"], keep="last")
    df = df.set_index("date")
    return df


def load_market_data(symbols: Iterable[str]) -> pd.DataFrame:
    config = load_data_config()
    price_dir = Path(config["priceDir"])

    merged = None
    for symbol in symbols:
        df = load_price_csv(price_dir, symbol)
        df = df.rename(columns={col: f"{symbol}_{col}" for col in df.columns})
        merged = df if merged is None else merged.join(df, how="inner")

    if merged is None or merged.empty:
        raise ValueError("No market data loaded")

    merged = merged.sort_index()
    return merged


def add_symbol_features(df: pd.DataFrame, symbol: str, lookbacks: Iterable[int]) -> pd.DataFrame:
    close = df[f"{symbol}_close"]
    df[f"{symbol}_ret_1"] = close.pct_change(1)
    df[f"{symbol}_ret_2"] = close.pct_change(2)
    df[f"{symbol}_ret_3"] = close.pct_change(3)
    df[f"{symbol}_ret_10"] = close.pct_change(10)

    for lookback in lookbacks:
        roll_high = close.rolling(lookback, min_periods=lookback).max()
        gap = (roll_high - close) / roll_high
        at_high = (gap.abs() <= 1e-12) | (close >= roll_high)
        recent_high_3 = at_high.astype(int).rolling(3, min_periods=1).max().astype(bool)

        df[f"{symbol}_high_{lookback}"] = roll_high
        df[f"{symbol}_gap_{lookback}"] = gap
        df[f"{symbol}_at_high_{lookback}"] = at_high
        df[f"{symbol}_recent_high3_{lookback}"] = recent_high_3

    return df


def prepare_market_data(lookbacks: Iterable[int]) -> pd.DataFrame:
    df = load_market_data(["SPY", "QQQ", "DIA"])
    for symbol in ["SPY", "QQQ", "DIA"]:
        df = add_symbol_features(df, symbol, lookbacks)
    return df
