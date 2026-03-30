#!/usr/bin/env python3
"""rules_monitor.py — Domain-agnostic rules monitor for bdistill exports.

Loads rules from one or more bdistill export JSON files, fetches current data
from a pluggable source, checks each rule's conditions against reality, and
outputs a decision report JSON to stdout.

Usage:
    python rules_monitor.py --rules aml.json --source csv --params '{"path": "txns.csv"}'
    python rules_monitor.py --rules weather.json --source open-meteo --params '{"lat": -12.68, "lon": -56.92}'
    python rules_monitor.py --rules macro.json --source fred --params '{"series_id": "DGS10", "api_key": "..."}'
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

# ---------------------------------------------------------------------------
# Data fetchers — one per source type
# ---------------------------------------------------------------------------

def fetch_open_meteo(params: dict) -> dict:
    """Fetch daily weather from Open-Meteo (no auth required)."""
    lat, lon = params["lat"], params["lon"]
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&daily=precipitation_sum,temperature_2m_max,temperature_2m_min,windspeed_10m_max"
        f"&timezone=auto&forecast_days=1"
    )
    resp = httpx.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    daily = data.get("daily", {})
    return {k: v[0] if isinstance(v, list) and v else v for k, v in daily.items()}


def fetch_fred(params: dict) -> dict:
    """Fetch latest observation from FRED (free API key required)."""
    series_id = params["series_id"]
    api_key = params["api_key"]
    url = (
        f"https://api.stlouisfed.org/fred/series/observations"
        f"?series_id={series_id}&api_key={api_key}"
        f"&sort_order=desc&limit=1&file_type=json"
    )
    resp = httpx.get(url, timeout=15)
    resp.raise_for_status()
    obs = resp.json().get("observations", [])
    if not obs:
        return {}
    latest = obs[0]
    return {"date": latest["date"], "value": float(latest["value"]), "series_id": series_id}


def fetch_yahoo_finance(params: dict) -> dict:
    """Fetch latest quote from Yahoo Finance (no auth required)."""
    ticker = params["ticker"]
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1d"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = httpx.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    result = resp.json().get("chart", {}).get("result", [{}])[0]
    meta = result.get("meta", {})
    return {
        "ticker": ticker,
        "price": meta.get("regularMarketPrice"),
        "previous_close": meta.get("previousClose"),
        "currency": meta.get("currency"),
    }


def read_csv_source(params: dict) -> list[dict]:
    """Read a local CSV file and return rows as list of dicts."""
    path = Path(params["path"])
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def fetch_json_url(params: dict) -> dict | list:
    """Fetch arbitrary JSON from a URL."""
    resp = httpx.get(params["url"], timeout=15)
    resp.raise_for_status()
    return resp.json()


FETCHERS = {
    "open-meteo": fetch_open_meteo,
    "fred": fetch_fred,
    "yahoo-finance": fetch_yahoo_finance,
    "csv": read_csv_source,
    "json-url": fetch_json_url,
}

# ---------------------------------------------------------------------------
# Rule checking
# ---------------------------------------------------------------------------

_OPERATOR_RE = re.compile(r"([a-z_]+)\s*(>=|<=|>|<|==|!=)\s*([0-9.]+)")


def check_rule(rule: dict, data: dict | list) -> dict | None:
    """Check a single rule against fetched data.

    Returns a triggered-report dict if the rule fires, None otherwise.
    Matching is best-effort keyword parsing of the conditions text.
    """
    conditions = rule.get("conditions", "") or rule.get("answer", "")
    match = _OPERATOR_RE.search(conditions.lower().replace(",", "").replace("$", ""))
    if not match:
        return None

    field, op, threshold_str = match.group(1), match.group(2), match.group(3)
    threshold = float(threshold_str)

    # Resolve current value from data
    current = None
    if isinstance(data, dict):
        current = data.get(field)
    elif isinstance(data, list) and data:
        # For CSV: try to aggregate or use the last row
        current = data[-1].get(field)

    if current is None:
        return None

    try:
        current = float(current)
    except (ValueError, TypeError):
        return None

    ops = {">": current > threshold, "<": current < threshold,
           ">=": current >= threshold, "<=": current <= threshold,
           "==": current == threshold, "!=": current != threshold}

    if ops.get(op, False):
        return {
            "rule_id": rule.get("id", rule.get("question", "unknown")),
            "confidence": rule.get("confidence", rule.get("quality_score", 0.5)),
            "conditions": conditions,
            "current_value": current,
            "threshold": threshold,
            "unit": rule.get("unit", ""),
            "impact": rule.get("impact", rule.get("answer", "")),
        }
    return None

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_rules(paths: list[str]) -> list[dict]:
    """Load and merge rules from one or more JSON/JSONL files.

    Filters to verified/solid tier when a quality_score or confidence field
    is present (>= 0.6).
    """
    rules: list[dict] = []
    for p in paths:
        path = Path(p)
        text = path.read_text()
        if text.strip().startswith("["):
            entries = json.loads(text)
        else:
            entries = [json.loads(line) for line in text.splitlines() if line.strip()]
        for entry in entries:
            score = entry.get("confidence", entry.get("quality_score", 1.0))
            if score >= 0.6:
                rules.append(entry)
    return rules


def main() -> None:
    parser = argparse.ArgumentParser(description="Check bdistill rules against live data")
    parser.add_argument("--rules", nargs="+", required=True, help="Path(s) to rules JSON export")
    parser.add_argument("--source", required=True, choices=list(FETCHERS.keys()), help="Data source type")
    parser.add_argument("--params", required=True, help="JSON string with source parameters")
    args = parser.parse_args()

    params = json.loads(args.params)
    rules = load_rules(args.rules)
    fetcher = FETCHERS[args.source]
    data = fetcher(params)

    triggered = []
    skipped = 0
    for rule in rules:
        result = check_rule(rule, data)
        if result is not None:
            triggered.append(result)
        elif not _OPERATOR_RE.search((rule.get("conditions", "") or rule.get("answer", "")).lower()):
            skipped += 1

    triggered.sort(key=lambda r: r["confidence"], reverse=True)

    report = {
        "context": {"data_source": args.source, "fetched_at": datetime.now(timezone.utc).isoformat()},
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "rules_checked": len(rules),
        "rules_skipped": skipped,
        "rules_source": args.rules if len(args.rules) > 1 else args.rules[0],
        "triggered": triggered,
        "data_source": {"type": args.source, "params": params},
    }

    json.dump(report, sys.stdout, indent=2, default=str)
    print(f"\n# {len(triggered)} of {len(rules)} rules triggered", file=sys.stderr)


if __name__ == "__main__":
    main()
