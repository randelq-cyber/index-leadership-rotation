# Candidate Rule v0 Validation

## Validation method
The candidate rule family was stress-tested using:
- **non-overlapping trades only**
- **next-open to next-open execution**
- simple total roundtrip cost assumptions of **0 / 10 / 20 / 40 bps** on excess return

This is a more realistic validation than the earlier overlapping close-to-close event-study framing.

## Main result
The core thesis survives validation, but the control setup weakens substantially.

That matters a lot.

## Key findings
### 1. T0 weakens sharply under validation
The naive setup-only control looked decent in the earlier event-study. Under non-overlap plus next-open execution, much of that edge degrades or disappears.

This is actually encouraging for the trigger thesis, because it means some of the trigger value is real and not just an artifact of the event-study framing.

### 2. T1 still survives
The best validated T1 configurations are:
- **T1_60_4**
  - 12 non-overlapping trades
  - average open-to-open excess: **0.9559%**
  - hit rate: **66.7%**
- **T1_252_4**
  - 7 trades
  - average open-to-open excess: **0.8657%**
  - hit rate: **57.1%**
- **T1_252_5**
  - 7 trades
  - average open-to-open excess: **1.0063%**
  - hit rate: **57.1%**

### 3. T5 is highly robust in the 252-day cluster
The strongest validated T5 configurations are:
- **T5_252_5**
  - 7 trades
  - average open-to-open excess: **1.3186%**
  - hit rate: **57.1%**
  - still averages **0.9186%** after **40 bps** total cost drag
- **T5_252_4**
  - 7 trades
  - average open-to-open excess: **1.0000%**
  - hit rate: **57.1%**
- **T5_60_5**
  - 10 trades
  - average open-to-open excess: **0.9161%**
  - hit rate: **60.0%**

### 4. T0 should remain a benchmark, not a preferred entry
Under the validation framing, T0 is no longer the branch to build around. It should stay in the research process as a control benchmark only.

## Interpretation
The validation points to two slightly different strengths:
- **T1** looks like the cleaner signal-quality trigger
- **T5**, especially at **252-day / 5-day**, looks like the more cost-robust slower trigger

## Shortlist after validation
### Primary shortlist
1. **T1_60_4**
2. **T1_252_5**
3. **T5_252_5**

### Secondary shortlist
4. **T5_60_5**
5. **T1_252_4**
6. **T5_252_4**

## What this means
The project should now stop treating `candidate-rule-v0.md` as one broad family and start treating the surviving configs as a **small validated shortlist**.
