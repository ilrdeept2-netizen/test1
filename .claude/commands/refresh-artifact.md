---
description: Refresh the live artifact dashboard data (live-artifacts/data.json)
allowed-tools: Bash(python3 live-artifacts/refresh.py)
---

Run `python3 live-artifacts/refresh.py` from the project root, then report the
new `updated_at` timestamp from `live-artifacts/data.json`. The Antigravity
preview panel showing `live-artifacts/dashboard.html` will pick up the change
on its next poll (every 3 seconds).
