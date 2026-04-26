"""
Refresh data.json from configured data sources.

Antigravity's preview panel renders dashboard.html, which polls data.json.
Run this script (manually, on a cron, or via /refresh-artifact) to update it.

Stub connectors below return mock data — replace with real API calls
(Stripe, Slack, Notion, HubSpot, internal DB, etc.) as needed.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data.json"


def fetch_stripe():
    # TODO: replace with stripe.BalanceTransaction.list(...) etc.
    return {
        "mrr": "$48,200",
        "new_customers": 17,
        "churn_pct": 1.8,
    }


def fetch_support_queue():
    # TODO: replace with Zendesk / Intercom / Slack channel scrape.
    return {
        "open_tickets": 9,
        "rows": [
            {"source": "Zendesk", "item": "#4821 Refund request", "value": "P2", "time": "10:14"},
            {"source": "Slack",   "item": "#cs-escalations",      "value": "3 unread", "time": "10:22"},
        ],
    }


def build_payload() -> dict:
    stripe = fetch_stripe()
    support = fetch_support_queue()

    return {
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "title": "Sales & Support — Live",
        "kpis": [
            {"label": "MRR",           "value": stripe["mrr"],                    "delta": "+4.2% wow"},
            {"label": "New Customers", "value": str(stripe["new_customers"]),     "delta": "+3 vs yesterday"},
            {"label": "Churn",         "value": f'{stripe["churn_pct"]}%',        "delta": "-0.2pp"},
            {"label": "Open Tickets",  "value": str(support["open_tickets"]),     "delta": "P2: 4 / P3: 5"},
        ],
        "rows": support["rows"],
    }


def main() -> None:
    payload = build_payload()
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"wrote {DATA_FILE} at {payload['updated_at']}")


if __name__ == "__main__":
    main()
