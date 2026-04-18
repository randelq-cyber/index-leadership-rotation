# Iteration 01 Plan

## Objective
Run a small curated first pass that tests whether a lagging non-SPY ETF begins a meaningful catch-up phase after a leadership divergence setup.

## Core model
- **SPY** = market context / confirmation filter
- **QQQ and DIA** = comparison pair
- **Outcome** = laggard forward return minus the other non-SPY ETF's forward return
- **Bars** = daily only
- **Forward windows** = 2, 3, 4, 5 trading days
- **High lookbacks** = 60, 128, 252 trading days

## Execution convention
- Setup is identified on day `t_setup`
- Trigger is identified on day `t_trigger`
- Trade entry is approximated at the **close of the trigger day**
- Forward returns are measured **close-to-close** from the trigger date
- If no trigger appears within the trigger-search window, the setup expires

## Trigger search window
- Search for triggers for up to **10 trading days after setup**
- If nothing triggers in 10 days, mark the setup as expired

## Setup candidates

### S1 — Same-day strict non-confirmation
Use when the divergence is obvious on the day it appears.

Conditions on setup day:
1. **SPY** closes at a fresh `L`-day high
2. Exactly one of **QQQ** or **DIA** closes at a fresh `L`-day high, this is the **leader**
3. The other non-SPY ETF, the **laggard**, is at least **1.0% below** its own `L`-day high
4. The laggard trails the leader by at least **2.0%** over the last **10 trading days**

### S2 — Rolling divergence
Use when leadership is clear but not perfectly synchronized on one exact day.

Conditions on setup day:
1. **SPY** is at a fresh `L`-day high, or within **0.25%** of it
2. Exactly one of **QQQ** or **DIA** has made a fresh `L`-day high within the last **3 trading days**, this is the **leader**
3. The laggard has **not** made a fresh `L`-day high within the last **3 trading days**
4. The laggard trails the leader by at least **2.0%** over the last **10 trading days**

## Trigger candidates

### T0 — Baseline control
- No extra trigger
- Enter at the **setup-day close**

Purpose: this is a control branch to test whether the trigger logic adds value.

### T1 — Relative-strength turn
Trigger when, after setup:
- the laggard's **3-day return minus leader's 3-day return** turns **positive**,
- after being **negative** on the prior day

Idea: the laggard has started outperforming on a short basis.

### T2 — Laggard 5-day breakout
Trigger when the laggard closes above its own **prior 5-day high** after setup.

Idea: catch-up begins when the laggard actually breaks short-term resistance.

### T3 — Two-day relative thrust
Trigger when the laggard outperforms the leader by at least **1.0%** over a **2-day window** after setup.

Idea: fast rotation may show up as a short burst rather than a single-day signal.

### T4 — Leader stall plus laggard strength
Trigger when both are true on the same day after setup:
- laggard daily return is **> +0.5%**
- leader daily return is **<= 0.0%**

Idea: catch-up may start when the leader pauses and the laggard starts moving.

### T5 — Gap compression
Trigger when the laggard's percentage gap to its own `L`-day high shrinks by at least **50%** versus the setup-day gap.

Idea: the laggard is not just bouncing, it is materially closing the distance to the high.

## Evaluation grid
For each branch:
- setup family: `S1`, `S2`
- trigger: `T0`, `T1`, `T2`, `T3`, `T4`, `T5`
- high lookback: `60`, `128`, `252`
- holding window: `2`, `3`, `4`, `5`

## Primary metrics
- average excess return of laggard vs other non-SPY ETF
- median excess return
- hit rate
- subperiod consistency
- sample count

## Promotion rule
Promote a branch when it shows:
- positive average excess return
- hit rate above 50%
- some subperiod consistency

Sparse samples are acceptable for now.

## Why this is a good first iteration
- small enough to run cleanly
- includes a control branch (`T0`)
- tests both **strict** and **rolling** divergence setups
- tests multiple trigger styles without exploding the search space
- respects the core thesis that the change point is **not necessarily the setup day**
