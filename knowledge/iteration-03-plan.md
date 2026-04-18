# Iteration 03 Plan

## Objective
Stop broad branch exploration and focus on the smallest credible rule family that still explains the Iteration 02 results.

## Core question
Can the apparent edge be reduced to a compact set of QQQ-leading rules where:
- **T1** is the main trigger,
- **T5** is a selective secondary trigger,
- and **T0** remains the control benchmark?

## Iteration 03 branch set
### Keep as core comparison trio
1. **S1_T0_QQQ_leads**
2. **S1_T1_QQQ_leads**
3. **S1_T5_QQQ_leads**

### Keep as small wildcard
4. **S2_T4_DIA_leads**

### Drop from active focus
- **S1_T3_QQQ_leads**
- all other branches

## Parameter narrowing
### For T0 and T1
- lookbacks: **60**, **252**
- holds: **3**, **4**, **5**

### For T5
- lookbacks: **252** for **3 / 4 / 5-day** holds
- also keep **60-day / 5-day** as a secondary check

### For the DIA-leading wildcard
- lookbacks: **60**, **128**
- hold: **2-day** only

## What Iteration 03 should test
1. Does **T1** beat **T0** reliably enough to justify trigger complexity?
2. Is **T5** additive beyond T0, or just a different slice of the same effect?
3. Is the best horizon really centered on **4 to 5 days**?
4. Does the DIA-leading wildcard still survive when forced into its narrowest form?

## Expected outputs
- compact Iteration 03 summary
- explicit comparison table:
  - **T0 vs T1**
  - **T0 vs T5**
  - by lookback and hold window
- reflection note deciding whether this is now specific enough to translate into a candidate rule

## Success condition
Iteration 03 succeeds if it either:
- confirms a small stable rule family worth formalizing, or
- shows that the apparent edge vanishes once the branch set gets tight enough.
