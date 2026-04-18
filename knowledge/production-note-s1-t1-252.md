# Production Note — S1 + T1 3-day turn + 252-day lookback

## Strategy template
This note packages the current production-style research definition for a symmetric version of the rule.

### Shared setup
On setup day:
1. SPY closes at a fresh 252-day high
2. The leader (QQQ or DIA) closes at a fresh 252-day high
3. The laggard is at least 1.0% below its own 252-day high
4. The laggard trails the leader by at least 2.0% over the prior 10 trading days

### Trigger
Within 10 trading days after setup, trigger when:
- laggard 3-day return minus leader 3-day return turns positive,
- after being non-positive on the prior day

### Holding horizons evaluated
- 1, 2, 3, 4, 5 trading days after the trigger

## Directions included
- QQQ leads / DIA lags
- DIA leads / QQQ lags

Setups found under this rule definition:
- QQQ leading setups: 25
- DIA leading setups: 20

## Output files
- Summary metrics: `/home/yqin/.openclaw/workspace/projects/index-leadership-rotation/results/production_s1_t1_252_summary.csv`
- Full trigger-date event log: `/home/yqin/.openclaw/workspace/projects/index-leadership-rotation/results/production_s1_t1_252_events.csv`

## Included metrics
For each direction and holding horizon, the summary file includes:
- average excess return
- average laggard absolute return
- average leader absolute return
- hit rate
- max drawdown of excess-return sequence
- max drawdown of laggard absolute-return sequence

## Important note
This note makes the rule definition explicit and symmetric across both directions, but the historical strength of the two directions is not necessarily equal. The downstream production decision should still be informed by the summary metrics.
