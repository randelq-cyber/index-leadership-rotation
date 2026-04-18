# Iteration 02 Plan

## Objective
Narrow the search space around the strongest Iteration 01 survivors and test whether the apparent edge remains when the branch set is pruned.

## Why this iteration exists
Iteration 01 found that the broad symmetric hypothesis was too loose. The cleaner working hypothesis now is:
- **QQQ leads / DIA lags** is the main direction worth pursuing
- the best trigger families are **relative-strength turn** and **gap compression**
- the baseline setup itself also matters enough that a control branch must be retained

## Core branch set
### Keep
1. **S1_T1_QQQ_leads**
2. **S1_T5_QQQ_leads**
3. **S1_T0_QQQ_leads** (control)
4. **S1_T3_QQQ_leads**

### Keep as asymmetric wildcard
5. **S2_T4_DIA_leads**

## Branches dropped from Iteration 02
- all other **S2 + QQQ_leads** branches
- most **DIA leads / QQQ lags** branches
- broad low-conviction trigger families that were mostly `kill` or weak `revise`

## Parameter narrowing
### For the QQQ-leading core set
- prioritize **60-day** and **252-day** highs
- prioritize **3 / 4 / 5-day** holding windows
- keep **2-day** only as a secondary check if implementation cost is low

### For the DIA-leading wildcard
- keep **2-day** and **3-day** windows first
- allow **60-day** and **128-day** highs
- treat it as a separate asymmetric hypothesis, not proof of symmetry

## Questions Iteration 02 should answer
1. Does the QQQ-leading edge survive after branch pruning?
2. Does **T1** truly outperform the baseline control **T0**, or is the setup itself doing most of the work?
3. Is **T5** genuinely additive, or just selecting a smaller but not better subset?
4. Is **S2_T4_DIA_leads** a real asymmetric exception or just noise?

## Expected outputs
- updated experiment registry limited to the Iteration 02 branch set
- direct comparison table for **T0 vs T1 vs T5** under the QQQ-leading core setup
- short reflection note stating whether the hypothesis is tightening or collapsing

## Success condition
Iteration 02 is successful if it either:
- strengthens the case for a small durable branch family, or
- cleanly disproves the apparent edge from Iteration 01.

Both outcomes are useful.
