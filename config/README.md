# Config

Keep only example config files in repo.

## Pattern
- Track: `*.example.*`
- Do not track: machine-specific local config such as `data-sources.local.json`

This lets the future dedicated repo stay portable while still pointing at external raw data on each machine.
