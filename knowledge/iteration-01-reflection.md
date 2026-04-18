# Iteration 01 Reflection

## Verdict
Iteration 01 was useful and should be considered a successful exploratory pass.

It did **not** produce a balanced symmetric signal across both directions. Instead, it showed a strong directional asymmetry:
- **QQQ leads / DIA lags** is the more promising side
- **DIA leads / QQQ lags** is weaker and less consistent overall

## What changed from prior expectation
Before running, the working hypothesis was that both directions might show a similar catch-up effect.

After the first implementation pass, that symmetry does **not** hold in the data as cleanly as expected.

## Strongest surviving branch clusters
### 1. Primary survivor
**S1_T1_QQQ_leads**
- best overall branch cluster in Iteration 01
- 6 promote rows, 0 kill rows
- strong average excess return and strong hit rate
- positive pre/post-2020 consistency

Interpretation:
When QQQ is the clear leader, the cleanest catch-up signal for DIA may be a **relative-strength turn** rather than a raw breakout alone.

### 2. Secondary survivor
**S1_T5_QQQ_leads**
- 5 promote rows
- strongest single-row average excess return in the whole pass
- more mixed than T1, but still clearly alive

Interpretation:
The laggard beginning to materially close its gap to the high may be an important change-point indicator.

### 3. Control worth keeping
**S1_T0_QQQ_leads**
- 3 promote rows
- no kill rows
- baseline remains positive enough to matter

Interpretation:
Part of the effect may already begin around the setup itself, so triggers should be judged against this control, not against zero alone.

### 4. Secondary QQQ-leading branch
**S1_T3_QQQ_leads**
- 3 promote rows
- mostly revise rather than kill
- potentially worth keeping as a secondary momentum-style trigger

### 5. Asymmetric wildcard
**S2_T4_DIA_leads**
- only 2 promote rows, but unusually strong mean excess return and hit rate
- this is the best surviving DIA-leading branch

Interpretation:
If DIA-leading cases survive at all, they may need a different trigger shape, specifically a **leader stall + laggard strength** pattern rather than the same trigger family used for QQQ-leading cases.

## Branches to kill or deprioritize
### Kill as broad families
- all **S2 + QQQ_leads** branches
- **S1_T3_DIA_leads**
- **S1_T4_QQQ_leads**
- **S2_T4_QQQ_leads**

### Deprioritize heavily
- most **DIA leads / QQQ lags** branches outside the single wildcard above
- most branches whose verdict mix is dominated by `kill` or weak `revise`

## Lookback and holding-window takeaways
### Lookbacks
The best rows cluster more around:
- **60-day highs**
- **252-day highs**

The **128-day** window is less convincing overall, though it shows up in a few DIA-leading wildcard rows.

### Holding windows
The strongest QQQ-leading rows lean more toward:
- **3-day**
- **4-day**
- **5-day**

The **2-day** window still matters, but it does not look like the center of gravity for the main QQQ-leading thesis.

## Recommended Iteration 02 narrowed branch set
### Core set
1. **S1_T1_QQQ_leads**
2. **S1_T5_QQQ_leads**
3. **S1_T0_QQQ_leads** (control)
4. **S1_T3_QQQ_leads**

### Wildcard set
5. **S2_T4_DIA_leads**

## Recommended Iteration 02 narrowing rules
- focus primarily on **QQQ leads / DIA lags**
- prioritize **60** and **252** day highs
- prioritize **3 / 4 / 5-day** holding windows for the QQQ-leading core set
- keep **2-day** mostly for the DIA-leading wildcard and sanity checks

## Bottom line
The first pass says the idea is **real enough to keep going**, but not in the broad symmetric form we started with.

The cleaner emerging hypothesis is:
- when **QQQ leads**, **DIA catch-up** has evidence of a short-horizon effect,
- especially when the catch-up is confirmed by **relative-strength turn** or **gap compression**,
- while the reverse direction appears weaker and may require a different trigger family entirely.
