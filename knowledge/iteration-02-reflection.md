# Iteration 02 Reflection

## Verdict
Iteration 02 strengthened the core thesis.

The project is no longer just saying "maybe there is some catch-up effect." It is now saying something much tighter:
- the main effect is in **QQQ leads / DIA lags**
- the best primary trigger is **T1 (relative-strength turn)**
- **T5 (gap compression)** remains useful, but more selectively
- the baseline setup itself (**T0**) still matters and must remain as a control
- the asymmetric **DIA leads / QQQ lags** case survives only as a narrow short-horizon wildcard

## What Iteration 02 clarified
### 1. T1 is earning its keep
This was the main question going in.

Compared with the baseline control **T0**, **T1** looks clearly stronger in the core QQQ-leading setup, especially:
- **60-day lookback, 3-day hold**
- **60-day lookback, 4-day hold**
- **252-day lookback, 4-day hold**
- **252-day lookback, 5-day hold**

The strongest clean row remains around **T1 + 252-day high + 4-day hold**.

### 2. T5 is real, but more conditional
T5 did not behave like a universal replacement for T1.

Instead:
- weaker at **60-day / 3-day**
- mixed at **60-day / 4-day**
- stronger at **60-day / 5-day**
- clearly strong at **252-day / 3 to 5-day**

Interpretation:
Gap compression seems more useful in the larger, slower high-lookback setup than in the short lookback fast-rotation setup.

### 3. T0 still matters
T0 remains too strong to discard.

This means the setup itself still contains real information, especially in the **252-day** cluster. Any trigger should therefore be judged against T0, not only against zero.

### 4. T3 is losing its case
T3 survived Iteration 01 as a plausible secondary candidate, but in Iteration 02 it looks more mixed and less compelling than T1 or T5.

Verdict: **deprioritize or drop**.

### 5. DIA-leading wildcard remains narrow
**S2_T4_DIA_leads** is still alive, but mainly as a **2-day** effect. The 3-day version is weaker and less convincing.

Verdict: keep only as a small asymmetric wildcard.

## Surviving branch logic
### Primary core
- **S1_T1_QQQ_leads**

### Secondary core
- **S1_T5_QQQ_leads**

### Required control
- **S1_T0_QQQ_leads**

### Small asymmetric wildcard
- **S2_T4_DIA_leads** at **2-day** only

## Branches to prune after Iteration 02
- **S1_T3_QQQ_leads** as an active focus branch
- **S2_T4_DIA_leads** beyond the 2-day case
- weaker T5 combinations outside the stronger 252-day cluster

## Recommended Iteration 03 direction
### QQQ-leading core
Focus on:
- **T1** as primary
- **T5** as selective secondary
- **T0** as control

### Parameter narrowing
For the QQQ-leading core:
- keep **60-day** and **252-day** highs
- prioritize:
  - **T1:** 3 / 4 / 5-day windows, especially 4-day
  - **T5:** 252-day with 3 / 4 / 5-day windows, and 60-day with 5-day only
  - **T0:** same windows for direct comparison

For the DIA-leading wildcard:
- keep only **60-day or 128-day**
- keep only **2-day** holding window

## Bottom line
Iteration 02 says the project should now stop searching broadly and start treating this as a **small family of specific candidate rules**.

The main emerging claim is:
- when **QQQ leads** and **DIA lags** under the strict setup,
- the best entry may be a **relative-strength turn**,
- with **gap compression** as a secondary confirmation-style trigger,
- and the real edge seems to live mostly in the **3 to 5-day** horizon.
