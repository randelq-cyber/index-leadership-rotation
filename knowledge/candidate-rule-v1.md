# Candidate Rule v1

_This is the narrowed post-validation shortlist, not yet a final live-trading rule._

## Rule family focus
All surviving core candidates share the same structure:
- **SPY** confirms the backdrop
- **QQQ** is at the important high
- **DIA** lags and underperforms
- enter only after a validated trigger, not just on setup alone

## Validated shortlist
### Candidate A — Fast primary rule
- **Setup:** strict QQQ-leading / DIA-lagging setup
- **Trigger:** **T1** relative-strength turn
- **Lookback:** **60-day high**
- **Hold:** **4 trading days**

Why it matters:
- strongest combination of frequency and signal quality in the faster cluster
- survives non-overlap and next-open validation

### Candidate B — Slower primary rule
- **Setup:** strict QQQ-leading / DIA-lagging setup
- **Trigger:** **T1** relative-strength turn
- **Lookback:** **252-day high**
- **Hold:** **5 trading days**

Why it matters:
- stronger longer-lookback version of the same trigger family
- remains positive after validation and cost drag

### Candidate C — Slower secondary / confirmation rule
- **Setup:** strict QQQ-leading / DIA-lagging setup
- **Trigger:** **T5** gap compression
- **Lookback:** **252-day high**
- **Hold:** **5 trading days**

Why it matters:
- strongest cost robustness among the validated candidates
- likely the best secondary confirmation-style version of the thesis

## Keep only as secondary checks
- **T5_60_5**
- **T1_252_4**
- **T5_252_4**

## Keep only as research benchmark
- setup-day **T0** control

## Not part of v1 core
- DIA-leading cases
- the DIA-leading 2-day wildcard

## Next validation step
If this becomes a final candidate rule, the next job is not more branch expansion.
It is:
- compare Candidate A vs B vs C directly
- decide whether to keep one rule or a small 2-rule family
- test a simple position-management assumption on the non-overlapping trade log
