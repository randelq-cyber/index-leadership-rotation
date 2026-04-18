# Output Schema

Every experiment branch should log a single row to `results/experiment_registry.csv`.

## Required fields
- `iteration_id`
- `branch_id`
- `setup_definition`
- `high_lookback_days`
- `leader_strength_definition`
- `laggard_definition`
- `trigger_definition`
- `context_filter`
- `comparison_target`
- `holding_window_days`
- `sample_count`
- `avg_excess_return`
- `median_excess_return`
- `hit_rate`
- `subperiod_consistency`
- `headline_verdict`
- `notes`

## Conventions
- `context_filter` is currently fixed to `SPY`.
- `comparison_target` should be `QQQ` or `DIA`, whichever is the non-laggard leg in the branch.
- `holding_window_days` must be one of: 2, 3, 4, 5.
- `high_lookback_days` must be one of: 60, 128, 252.
- `headline_verdict` should be one of: `promote`, `revise`, `kill`, `needs_review`.
- `subperiod_consistency` should be brief and specific, e.g. `positive pre-2020, mixed post-2020`.

## Interpretation rule
A branch is interesting when it shows:
- positive average excess return,
- hit rate above 50%, and
- some consistency across subperiods.

Sparse samples are expected, so sample size is informative but not a hard promotion gate.
