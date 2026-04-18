# Candidate Rule v2

_This is the current best distilled output of the project._

## Final recommendation
Use a **2-rule family** rather than a single universal rule.

## Shared setup logic
On setup day:
1. **SPY** closes at a fresh important high
2. **QQQ** closes at the same important high window
3. **DIA** is at least **1.0% below** its own high for that window
4. **DIA** trails **QQQ** by at least **2.0%** over the prior **10 trading days**

## Rule A — Fast primary rule
### Setup window
- **60-day high**

### Trigger
- **T1 relative-strength turn**
- DIA 3-day return minus QQQ 3-day return turns positive after being non-positive

### Hold
- **4 trading days**

### Why keep it
- best faster rule in the validated shortlist
- more trade frequency than the slower 252-day rules
- strongest active expression of the T1 trigger

## Rule B — Slow robust rule
### Setup window
- **252-day high**

### Trigger
- **T5 gap compression**
- DIA's gap to its own 252-day high shrinks by at least **50%** versus the setup-day gap

### Hold
- **5 trading days**

### Why keep it
- strongest cost robustness in the validated shortlist
- best slower expression of the thesis
- good complement to Rule A rather than a duplicate of it

## Research benchmark only
- setup-day **T0** control stays in analysis, but is not part of the final recommended rule family

## If only one rule is allowed
- choose **Rule B (T5_252_5)** if robustness matters most
- choose **Rule A (T1_60_4)** if frequency matters most

## Still needed before any live use
- simple portfolio / position-management assumptions
- exposure rules when both signals are active near each other
- realistic implementation frictions beyond the simple cost drag already tested
