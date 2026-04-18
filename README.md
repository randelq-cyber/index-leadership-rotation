# index-leadership-rotation

Improved multi-agent research scaffold for testing leadership divergence and laggard catch-up among SPY, QQQ, and DIA.

## Structure
- `agents/` — role definitions and execution contracts
- `knowledge/` — shared schema, findings, and hypothesis history
- `state/` — live coordination and progress tracking
- `results/` — experiment registry and analysis outputs
- `scripts/` — project-specific code
- `config/` — example path/config files for local environments

## Project Principles
1. Separate **setup**, **trigger**, and **next phase** explicitly.
2. Separate **idea generation** from **evaluation**.
3. Use the **experiment registry** as the canonical ledger of tests.
4. Reflection decides whether a branch is continued, revised, or killed.
5. Report writing is delayed until there is something worth summarizing.

## Repo Boundary
This project should be organized so it can become its own standalone repo later.

### Keep in repo
- prompts / agent specs
- scripts
- schema and knowledge files
- progress / state files
- compact result summaries and experiment registry
- config examples and documentation

### Keep out of repo
- raw downloaded market data
- large intermediate datasets
- bulky caches or scratch outputs

## External Dependency
Reusable price download infrastructure lives at:
- `/home/yqin/repos/stock_trend_rq`

Use its downloader before writing a new one.

## Local Runtime
Use:
- `/home/yqin/repos/stock_trend_rq/.venv/bin/python`

Do not assume global Python has the required market-data dependencies.

See `config/data-sources.example.json` for the expected local path contract.
