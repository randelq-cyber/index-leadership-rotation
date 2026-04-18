# Candidate Rule v1 Comparison

## Question
Should the final output be:
- one rule, or
- a small 2-rule family?

## Shortlist compared
Primary shortlist:
- `T1_60_4`
- `T1_252_5`
- `T5_252_5`

Secondary shortlist:
- `T5_60_5`
- `T1_252_4`
- `T5_252_4`

## What the comparison says
### Best raw and cost-robust performer
**T5_252_5**
- highest average validated open-to-open excess in the shortlist
- remains strongest after 20 bps and 40 bps cost drag
- still keeps a positive median after 40 bps

Weakness:
- only **7 non-overlapping trades**

### Best faster / more active candidate
**T1_60_4**
- more trades than the 252-day candidates
- best hit rate in the shortlist at baseline
- still attractive after cost drag, though less robust than T5_252_5

Weakness:
- median turns negative sooner under cost drag

### Best same-family slower T1 variant
**T1_252_5**
- cleaner slower version of the T1 family
- remains positive under cost drag
- but not as strong as T5_252_5 on robustness

## Decision
A **2-rule family** is more faithful to the evidence than forcing one universal winner.

## Recommended final family
### Rule 1 — Fast primary rule
**T1_60_4**
- captures the faster expression of the thesis
- higher frequency than the 252-day rules
- strongest case if you want the cleaner active version of the T1 trigger

### Rule 2 — Slow robust rule
**T5_252_5**
- best cost robustness in the whole validated shortlist
- strongest slower expression of the thesis
- best candidate if robustness matters more than frequency

## If forced to choose only one rule
### Best robustness-first choice
**T5_252_5**

### Best frequency-first choice
**T1_60_4**

## What to drop from the primary output
- `T1_252_4`
- `T5_252_4`
- `T5_60_5`
- `T1_252_5` as a primary output rule, though it remains a useful family-relative benchmark

## Bottom line
The evidence is stronger for a **small 2-rule family** than for one universal final rule.
