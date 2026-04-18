# Candidate Rule v0

_This is a research-stage candidate rule, not a final tradable strategy._

## Core idea
Exploit short-horizon catch-up when **QQQ is leading**, **DIA is lagging**, and the laggard begins to recover under a strong SPY backdrop.

## Market context
- **SPY** acts as the broad-market confirmation filter

## Setup (strict non-confirmation)
Use lookback `L` in {**60**, **252**}.

On setup day:
1. **SPY** closes at a fresh `L`-day high
2. **QQQ** closes at a fresh `L`-day high
3. **DIA** is at least **1.0% below** its own `L`-day high
4. **DIA** trails **QQQ** by at least **2.0%** over the prior **10 trading days**

## Primary trigger
### T1 — Relative-strength turn
After setup, trigger when:
- **DIA 3-day return minus QQQ 3-day return** turns **positive**,
- after being non-positive on the prior day

## Secondary trigger
### T5 — Gap compression
After setup, trigger when:
- DIA's percentage gap to its own `L`-day high shrinks by at least **50%** versus the setup-day gap

## Preferred horizons
### Primary T1 focus
- **60-day / 4-day hold**
- **252-day / 4-day hold**
- **252-day / 5-day hold**

### Secondary T5 focus
- **252-day / 4-day hold**
- **252-day / 5-day hold**
- optional: **60-day / 5-day hold**

## Benchmark
Use the setup-day entry **T0** as a research control, not as the main candidate rule.

## Not part of the main rule
- DIA-leading cases are not part of the core candidate rule family
- the DIA-leading 2-day wildcard remains exploratory only

## What still needs validation
- overlapping-event handling
- robustness to execution assumptions
- whether the rule remains attractive after simple transaction-cost assumptions
- whether the T1 improvement over T0 is stable enough to justify trigger complexity
