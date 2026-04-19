from __future__ import annotations

import argparse
import datetime as dt
import logging
import math
import os
import sys
import threading
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from pandas.tseries.offsets import BDay
from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.wrapper import EWrapper


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "logs"
SIGNAL_DIR = PROJECT_ROOT / "live_signal"

LOG_DIR.mkdir(parents=True, exist_ok=True)
SIGNAL_DIR.mkdir(parents=True, exist_ok=True)

LOCAL_ADDRESS = os.environ.get("IB_HOST", "127.0.0.1")
PORT_NUMBER = int(os.environ.get("IB_PORT", "7496"))
ACCT_NO = os.environ.get("IB_ACCOUNT", "U13323114")

LOG_FILE = LOG_DIR / (
    Path(__file__).stem
    + "_"
    + dt.datetime.now().strftime("%Y%m%d%H%M%S")
    + ".log"
)

CHECK_HOUR_START = 16
CHECK_HOUR_END = 16
CHECK_MINUTE_START = 14
CHECK_MINUTE_END = 14
OFF_TMS = [dt.time(16, 45), dt.time(18, 0)]
SYSTEM_TMS = [dt.time(0, 10), dt.time(0, 50)]
CLOSE_TIME = dt.time(16, 5)
LOOP_SLEEP_SECONDS = 50

QUOTE_DURATION = "1 Y"
QUOTE_BARSIZE = "1 day"
HISTORICAL_REQUEST_SLEEP_SECONDS = 8
POSITION_REQUEST_SLEEP_SECONDS = 3

LOOKBACK_DAYS = 60
TRIGGER_SEARCH_DAYS = 10
HOLD_DAYS = 5
ORDER_MID_TO_LIMIT_TICKS = 10

PAIR_DIRECTIONS = [("NQ", "YM"), ("YM", "NQ")]
PAIR_QTY = {"NQ": 1, "YM": 2}
TICK_SIZE = {"ES": 0.25, "NQ": 0.25, "YM": 1.0}
MAIN_CONTRACT_MONTHS = {
    "ES": {3, 6, 9, 12},
    "NQ": {3, 6, 9, 12},
    "YM": {3, 6, 9, 12},
}

CONTRACTS = {
    "ES": {
        "type": "TRADES",
        "secType": "FUT",
        "contSecType": "CONTFUT",
        "symbol": "ES",
        "currency": "USD",
        "exchange": "CME",
        "ctxSel": 0,
        "qty": 0,
    },
    "NQ": {
        "type": "TRADES",
        "secType": "FUT",
        "contSecType": "CONTFUT",
        "symbol": "NQ",
        "currency": "USD",
        "exchange": "CME",
        "ctxSel": 0,
        "qty": 1,
    },
    "YM": {
        "type": "TRADES",
        "secType": "FUT",
        "contSecType": "CONTFUT",
        "symbol": "YM",
        "currency": "USD",
        "exchange": "CBOT",
        "ctxSel": 0,
        "qty": 2,
    },
}


logging.basicConfig(
    filename=str(LOG_FILE),
    filemode="w",
    level=logging.INFO,
    format="%(asctime)s %(pathname)s:%(lineno)d %(levelname)s - %(message)s",
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter("%(asctime)s %(levelname)s - %(message)s"))
logging.getLogger("").addHandler(console)
logger = logging.getLogger(__name__)


def floor_to_tick(price: float, tick: float) -> float:
    return math.floor(price / tick) * tick


def ceil_to_tick(price: float, tick: float) -> float:
    return math.ceil(price / tick) * tick


def entry_limit(price: float, tick: float, side: str) -> float:
    if side == "BUY":
        return ceil_to_tick(price + ORDER_MID_TO_LIMIT_TICKS * tick, tick)
    return floor_to_tick(price - ORDER_MID_TO_LIMIT_TICKS * tick, tick)


def hold_exit_timestamp(entry_time: dt.datetime, hold_days: int) -> str:
    exit_date = (pd.Timestamp(entry_time.date()) + BDay(hold_days)).date()
    return dt.datetime.combine(exit_date, CLOSE_TIME).strftime("%Y%m%d %H:%M:00")


def add_symbol_features(df: pd.DataFrame, symbol: str, lookback: int) -> pd.DataFrame:
    close = df[f"{symbol}_close"]
    df[f"{symbol}_ret_1"] = close.pct_change(1)
    df[f"{symbol}_ret_2"] = close.pct_change(2)
    df[f"{symbol}_ret_3"] = close.pct_change(3)
    df[f"{symbol}_ret_10"] = close.pct_change(10)

    roll_high = close.rolling(lookback, min_periods=lookback).max()
    gap = (roll_high - close) / roll_high
    at_high = (gap.abs() <= 1e-12) | (close >= roll_high)

    df[f"{symbol}_high_{lookback}"] = roll_high
    df[f"{symbol}_gap_{lookback}"] = gap
    df[f"{symbol}_at_high_{lookback}"] = at_high
    return df


def prepare_market_data(histories: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    merged: Optional[pd.DataFrame] = None
    for symbol in ["ES", "NQ", "YM"]:
        if symbol not in histories or histories[symbol].empty:
            raise ValueError(f"Missing history for {symbol}")
        df = histories[symbol].copy()
        df["date"] = pd.to_datetime(df["date"]).dt.normalize()
        df = df.sort_values("date").drop_duplicates(subset=["date"], keep="last")
        df = df[["date", "open", "high", "low", "close", "volume", "localSymbol"]].copy()
        df = df.rename(columns={col: f"{symbol}_{col}" for col in df.columns if col != "date"})
        merged = df if merged is None else merged.merge(df, on="date", how="inner")

    if merged is None or merged.empty:
        raise ValueError("No market data merged")

    merged = merged.sort_values("date").set_index("date")
    for symbol in ["ES", "NQ", "YM"]:
        merged = add_symbol_features(merged, symbol, LOOKBACK_DAYS)
    return merged


def setup_s1(prices: pd.DataFrame, idx: int, leader: str, laggard: str) -> bool:
    """Return True when the strict same-day non-confirmation setup is active.

    Rule definition for the 60-day production variant:
    1. ES, our SPY proxy, closes at a fresh 60-day high.
    2. The leader leg, NQ or YM, also closes at a fresh 60-day high.
    3. The laggard leg is not at a fresh 60-day high and is at least 1% below it.
    4. Over the prior 10 trading days, the leader outperformed the laggard by at least 2%.

    This is the "divergence exists" state. It does not trade yet. The trade waits for
    the T1 trigger, where the laggard starts to turn relative to the leader.
    """
    # Context filter, ES stands in for SPY and must confirm the broader market strength.
    es_at_high = bool(prices.iloc[idx][f"ES_at_high_{LOOKBACK_DAYS}"])

    # One of NQ or YM is designated the current leader, and it must also be at a fresh high.
    leader_at_high = bool(prices.iloc[idx][f"{leader}_at_high_{LOOKBACK_DAYS}"])

    # The laggard must still be below its own high, otherwise there is no non-confirmation.
    laggard_at_high = bool(prices.iloc[idx][f"{laggard}_at_high_{LOOKBACK_DAYS}"])
    laggard_gap = prices.iloc[idx][f"{laggard}_gap_{LOOKBACK_DAYS}"]

    # Relative-performance filter over the last 10 daily bars.
    leader_ret10 = prices.iloc[idx][f"{leader}_ret_10"]
    laggard_ret10 = prices.iloc[idx][f"{laggard}_ret_10"]

    if pd.isna([laggard_gap, leader_ret10, laggard_ret10]).any():
        return False

    return (
        es_at_high
        and leader_at_high
        and (not laggard_at_high)
        and laggard_gap >= 0.01
        and (leader_ret10 - laggard_ret10) >= 0.02
    )


def find_t1_trigger(prices: pd.DataFrame, setup_idx: int, leader: str, laggard: str) -> Optional[int]:
    """Find the first T1 trigger after a valid setup.

    T1 is the 3-day relative-strength turn:
    - compute 3-day return of laggard minus 3-day return of leader
    - yesterday that spread must be <= 0
    - today that spread must be > 0

    In plain English, we wait for the laggard to start outperforming the leader on a
    short rolling window after the divergence setup has already formed.
    """
    # Trigger must happen after the setup day, inside the 10-trading-day search window.
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

        # Positive means the laggard has now outperformed the leader on a rolling 3-day basis.
        curr_rel = lag_ret - lead_ret
        prev_rel = None if idx == 0 or pd.isna([prev_lag_ret, prev_lead_ret]).any() else prev_lag_ret - prev_lead_ret

        # This is the actual crossover event: non-positive yesterday, positive today.
        if prev_rel is not None and curr_rel > 0 and prev_rel <= 0:
            return idx
    return None


def find_live_signals(prices: pd.DataFrame) -> pd.DataFrame:
    """Build same-day live signals from all eligible setups.

    Multiple historical setup dates can sometimes map to the same trigger date. We sort by
    setup date and keep the earliest setup for each direction/trigger pair so the live layer
    sees one clean signal per direction.
    """
    rows: List[dict] = []
    for leader, laggard in PAIR_DIRECTIONS:
        for setup_idx in range(len(prices)):
            # Skip rows before the 60-day lookback is fully available.
            if pd.isna(prices.iloc[setup_idx][f"ES_high_{LOOKBACK_DAYS}"]):
                continue

            # First require the setup state, then search forward for the T1 trigger.
            if not setup_s1(prices, setup_idx, leader, laggard):
                continue
            trigger_idx = find_t1_trigger(prices, setup_idx, leader, laggard)
            if trigger_idx is None:
                continue
            rows.append(
                {
                    "direction": f"{leader}_leads",
                    "leader": leader,
                    "laggard": laggard,
                    "setup_idx": setup_idx,
                    "setup_date": prices.index[setup_idx],
                    "trigger_idx": trigger_idx,
                    "trigger_date": prices.index[trigger_idx],
                    # We enter immediately after the daily signal check on the trigger day.
                    "entry_date": prices.index[trigger_idx],
                }
            )

    signal_df = pd.DataFrame(rows)
    if signal_df.empty:
        return signal_df

    signal_df = signal_df.sort_values(["direction", "trigger_idx", "setup_idx"]).drop_duplicates(
        subset=["direction", "leader", "laggard", "trigger_idx"], keep="first"
    )

    # Live trading only cares about signals whose trigger is today, the latest bar available.
    live_idx = len(prices) - 1
    return signal_df[signal_df["trigger_idx"] == live_idx].reset_index(drop=True)


class IBapi(EWrapper, EClient):
    def __init__(self) -> None:
        EClient.__init__(self, self)
        self.is_connected = False
        self.nextValidOrderId: Optional[int] = None
        self.reqId = 0
        self.id_temp_hist = defaultdict(list)
        self.histId_key: Dict[int, str] = {}
        self.contractId_key: Dict[int, str] = {}
        self.contracts_data = defaultdict(lambda: defaultdict(dict))
        self.positions: Dict[str, float] = {}
        self.contract_details_complete = False
        self.hist_complete = False
        self.position_complete = False

    def set_contracts(self, contracts: Dict[str, dict]) -> None:
        for key, cfg in contracts.items():
            template = Contract()
            template.secType = cfg["secType"]
            template.symbol = cfg["symbol"]
            template.currency = cfg["currency"]
            template.exchange = cfg["exchange"]

            cont = Contract()
            cont.secType = cfg["contSecType"]
            cont.symbol = cfg["symbol"]
            cont.currency = cfg["currency"]
            cont.exchange = cfg["exchange"]

            self.contracts_data[key]["template"] = template
            self.contracts_data[key]["contract"] = None
            self.contracts_data[key]["contract_cont"] = cont
            self.contracts_data[key]["type"] = cfg["type"]
            self.contracts_data[key]["ctxSel"] = cfg.get("ctxSel", 0)
            self.contracts_data[key]["eligible_contracts"] = []
            self.contracts_data[key]["data"] = pd.DataFrame()

    def set_req_contracts(self) -> None:
        for key, data in self.contracts_data.items():
            self.reqId += 1
            req_id = self.reqId
            self.contractId_key[req_id] = key
            self.reqContractDetails(req_id, data["template"])

    def contractDetails(self, reqId: int, contractDetails) -> None:
        if reqId not in self.contractId_key:
            return
        key = self.contractId_key[reqId]
        contract = contractDetails.contract
        expiry_raw = contract.lastTradeDateOrContractMonth
        try:
            expiry = pd.to_datetime(expiry_raw, format="%Y%m%d")
        except Exception:
            try:
                expiry = pd.to_datetime(expiry_raw)
            except Exception:
                logger.warning("Could not parse expiry for %s: %s", key, expiry_raw)
                return

        if expiry <= pd.Timestamp.today() + pd.Timedelta(days=30):
            return
        if expiry.month not in MAIN_CONTRACT_MONTHS.get(contract.symbol, set()):
            return

        self.contracts_data[key]["eligible_contracts"].append((expiry, contract))

    def contractDetailsEnd(self, reqId: int) -> None:
        key = self.contractId_key[reqId]
        eligible = self.contracts_data[key]["eligible_contracts"]
        if not eligible:
            raise RuntimeError(f"No eligible contracts found for {key}")
        eligible.sort(key=lambda x: x[0])
        idx = min(self.contracts_data[key]["ctxSel"], len(eligible) - 1)
        selected = eligible[idx][1]
        self.contracts_data[key]["contract"] = selected
        logger.info("Selected %s contract: %s (%s)", key, selected.localSymbol, selected.lastTradeDateOrContractMonth)

        self.contract_details_complete = all(v["contract"] is not None for v in self.contracts_data.values())

    def nextValidId(self, orderId: int) -> None:
        super().nextValidId(orderId)
        self.nextValidOrderId = orderId
        logger.info("nextValidOrderId=%s", orderId)

    def nextOrderId(self) -> int:
        if self.nextValidOrderId is None:
            raise RuntimeError("nextValidOrderId not initialized")
        order_id = self.nextValidOrderId
        self.nextValidOrderId += 1
        return order_id

    def historicalData(self, reqId, bar) -> None:
        self.id_temp_hist[reqId].append(vars(bar))

    def historicalDataEnd(self, reqId: int, start: str, end: str) -> None:
        logger.info("HistoricalDataEnd reqId=%s start=%s end=%s", reqId, start, end)
        key = self.histId_key[reqId]
        df = pd.DataFrame(self.id_temp_hist[reqId])
        if df.empty:
            raise RuntimeError(f"No historical data returned for {key}")
        df["date"] = pd.to_datetime(df["date"]).dt.normalize()
        df["symbol"] = key
        selected = self.contracts_data[key]["contract"]
        df["localSymbol"] = getattr(selected, "localSymbol", key)
        self.contracts_data[key]["data"] = df
        self.hist_complete = all(not v["data"].empty for v in self.contracts_data.values())

    def position(self, account: str, contract: Contract, position: float, avgCost: float) -> None:
        super().position(account, contract, position, avgCost)
        if account != ACCT_NO:
            return
        if contract.symbol in {"NQ", "YM"}:
            self.positions[contract.symbol] = position
            logger.info("Position %s %s", contract.symbol, position)

    def positionEnd(self) -> None:
        super().positionEnd()
        self.position_complete = True
        logger.info("positionEnd")

    def openOrder(self, orderId, contract, order, orderState) -> None:
        super().openOrder(orderId, contract, order, orderState)
        logger.info(
            "openOrder id=%s %s %s %s qty=%s status=%s",
            orderId,
            order.orderRef,
            contract.symbol,
            order.action,
            order.totalQuantity,
            orderState.status,
        )

    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice) -> None:
        super().orderStatus(orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice)
        logger.info(
            "orderStatus id=%s status=%s filled=%s remaining=%s avgFill=%s parentId=%s",
            orderId,
            status,
            filled,
            remaining,
            avgFillPrice,
            parentId,
        )

    def error(self, reqId, errorCode, errorString) -> None:
        if errorCode in (2104, 2106, 2158, 2174, 2109, 202):
            logger.info("IB message reqId=%s code=%s msg=%s", reqId, errorCode, errorString)
            return
        logger.warning("IB error reqId=%s code=%s msg=%s", reqId, errorCode, errorString)

    def run_loop(self) -> None:
        self.run()

    def request_histories(self) -> None:
        for key, data in self.contracts_data.items():
            self.reqId += 1
            req_id = self.reqId
            self.histId_key[req_id] = key
            self.reqHistoricalData(
                req_id,
                data["contract_cont"],
                "",
                QUOTE_DURATION,
                QUOTE_BARSIZE,
                data["type"],
                0,
                1,
                False,
                [],
            )

    def build_timed_exit_orders(self, strategy: str, action: str, quantity: int, limit_price: float, exit_ts: str) -> List[Order]:
        parent_id = self.nextOrderId()

        parent = Order()
        parent.orderId = parent_id
        parent.account = ACCT_NO
        parent.action = action
        parent.orderType = "LMT"
        parent.tif = "IOC"
        parent.outsideRth = True
        parent.totalQuantity = quantity
        parent.lmtPrice = limit_price
        parent.eTradeOnly = False
        parent.firmQuoteOnly = False
        parent.orderRef = f"IndexRotation|{strategy}|Open"
        parent.transmit = False

        exit_order = Order()
        exit_order.orderId = self.nextOrderId()
        exit_order.account = ACCT_NO
        exit_order.action = "SELL" if action == "BUY" else "BUY"
        exit_order.orderType = "MKT PRT"
        exit_order.tif = "GAT"
        exit_order.goodAfterTime = exit_ts
        exit_order.outsideRth = True
        exit_order.totalQuantity = quantity
        exit_order.parentId = parent_id
        exit_order.eTradeOnly = False
        exit_order.firmQuoteOnly = False
        exit_order.orderRef = f"IndexRotation|{strategy}|TimedExit"
        exit_order.transmit = True

        return [parent, exit_order]

    def submit_orders(self, key: str, orders: List[Order]) -> None:
        contract = self.contracts_data[key]["contract"]
        if contract is None:
            raise RuntimeError(f"No selected contract for {key}")
        for order in orders:
            logger.info(
                "Submitting %s %s qty=%s limit=%s goodAfter=%s",
                key,
                order.action,
                order.totalQuantity,
                getattr(order, "lmtPrice", None),
                getattr(order, "goodAfterTime", None),
            )
            self.placeOrder(order.orderId, contract, order)


def wait_for(predicate, timeout_seconds: int, interval_seconds: float = 0.5, label: str = "condition") -> None:
    start = time.time()
    while time.time() - start < timeout_seconds:
        if predicate():
            return
        time.sleep(interval_seconds)
    raise TimeoutError(f"Timed out waiting for {label}")


def has_live_exposure(app: IBapi) -> bool:
    return any(abs(app.positions.get(symbol, 0)) > 0 for symbol in ["NQ", "YM"])


def execute_signal(app: IBapi, prices: pd.DataFrame, signal_row: pd.Series) -> None:
    leader = str(signal_row["leader"])
    laggard = str(signal_row["laggard"])
    strategy = str(signal_row["direction"])
    entry_time = dt.datetime.now()
    exit_ts = hold_exit_timestamp(entry_time, HOLD_DAYS)

    orders_to_send = []
    for symbol in [laggard, leader]:
        side = "BUY" if symbol == laggard else "SELL"
        qty = PAIR_QTY[symbol]
        last_close = float(prices.iloc[-1][f"{symbol}_close"])
        limit_price = entry_limit(last_close, TICK_SIZE[symbol], side)
        orders = app.build_timed_exit_orders(strategy, side, qty, limit_price, exit_ts)
        orders_to_send.append((symbol, orders, limit_price, side, qty))

    for symbol, orders, limit_price, side, qty in orders_to_send:
        logger.info("Signal %s: %s %s x%s @ %s", strategy, side, symbol, qty, limit_price)
        app.submit_orders(symbol, orders)
        time.sleep(1)


def run_once(client_id: int = 129) -> int:
    app = IBapi()
    app.set_contracts(CONTRACTS)
    app.connect(LOCAL_ADDRESS, PORT_NUMBER, client_id)
    api_thread = threading.Thread(target=app.run_loop, daemon=True)
    api_thread.start()

    try:
        wait_for(lambda: isinstance(app.nextValidOrderId, int), timeout_seconds=15, label="IB connection")
        app.is_connected = True

        app.set_req_contracts()
        wait_for(lambda: app.contract_details_complete, timeout_seconds=20, label="contract details")

        app.request_histories()
        wait_for(lambda: app.hist_complete, timeout_seconds=20, label="historical data")
        time.sleep(HISTORICAL_REQUEST_SLEEP_SECONDS)

        app.reqPositions()
        wait_for(lambda: app.position_complete, timeout_seconds=10, label="positions")
        time.sleep(POSITION_REQUEST_SLEEP_SECONDS)

        histories = {key: data["data"] for key, data in app.contracts_data.items()}
        prices = prepare_market_data(histories)
        signal_df = find_live_signals(prices)

        signal_path = SIGNAL_DIR / f"index_rotation_signals_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        if signal_df.empty:
            logger.info("No live signal found for latest bar")
            signal_df.to_csv(signal_path, index=False)
            return 0

        signal_out = signal_df.copy()
        for col in ["setup_date", "trigger_date", "entry_date"]:
            signal_out[col] = pd.to_datetime(signal_out[col]).dt.strftime("%Y-%m-%d")
        signal_out.to_csv(signal_path, index=False)
        logger.info("Saved signal snapshot to %s", signal_path)

        if signal_df["direction"].nunique() > 1:
            logger.error("Conflicting same-day signals found, refusing to trade: %s", signal_df[["direction", "leader", "laggard"]].to_dict("records"))
            return 1

        if has_live_exposure(app):
            logger.warning("Existing NQ/YM exposure detected, refusing to open new pair: %s", app.positions)
            return 1

        execute_signal(app, prices, signal_df.iloc[0])
        return 1

    finally:
        try:
            app.cancelPositions()
        except Exception:
            pass
        time.sleep(3)
        app.disconnect()
        logger.info("Disconnected")


def should_run_now(force: bool) -> bool:
    if force:
        return True

    now = dt.datetime.now()
    cur_tm = now.time()
    if OFF_TMS[0] < cur_tm < OFF_TMS[1]:
        logger.info("Out of business hours")
        return False

    in_system_window = SYSTEM_TMS[0] <= cur_tm <= SYSTEM_TMS[1]
    in_check_window = (
        CHECK_HOUR_START <= now.hour <= CHECK_HOUR_END
        and CHECK_MINUTE_START <= now.minute <= CHECK_MINUTE_END
    )
    return in_check_window and not in_system_window


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="run immediately instead of waiting for the scheduled minute")
    parser.add_argument("--client-id", type=int, default=129)
    args = parser.parse_args()

    if args.force:
        run_once(client_id=args.client_id)
        return

    while True:
        if should_run_now(force=False):
            try:
                run_once(client_id=args.client_id)
            except KeyboardInterrupt:
                raise
            except Exception as err:
                exc_type, _, exc_tb = sys.exc_info()
                logger.error("run_once failed: %s line=%s type=%s", err, getattr(exc_tb, "tb_lineno", None), exc_type)
            time.sleep(LOOP_SLEEP_SECONDS)
        else:
            time.sleep(LOOP_SLEEP_SECONDS)


if __name__ == "__main__":
    main()
