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

# Structured condition: field > 123
_OPERATOR_RE = re.compile(r"([a-z_]+)\s*(>=|<=|>|<|==|!=)\s*([0-9.]+)")

# Natural language threshold: "exceeds BRL 50,000" or "above 100,000" or "> R$50K"
_NL_THRESHOLD_RE = re.compile(
    r"(?:exceeds?|above|over|greater\s+than|more\s+than|surpass(?:es)?|>)\s+"
    r"(?:R\$|BRL|US\$|USD|\$|€|£)?\s*"
    r"([\d,]+(?:\.\d+)?)\s*"
    r"([KkMmBb])?",
    re.IGNORECASE,
)
_NL_BELOW_RE = re.compile(
    r"(?:below|under|less\s+than|fewer\s+than|<)\s+"
    r"(?:R\$|BRL|US\$|USD|\$|€|£)?\s*"
    r"([\d,]+(?:\.\d+)?)\s*"
    r"([KkMmBb])?",
    re.IGNORECASE,
)

# Keyword → CSV column name mapping (common patterns)
_FIELD_KEYWORDS = {
    "transaction": ["transaction_amount", "amount", "value", "transaction_value"],
    "cash": ["transaction_amount", "cash_amount", "amount"],
    "cumulative": ["cumulative_30d", "cumulative", "total_30d", "rolling_30d"],
    "pep": ["is_pep", "pep", "pep_status"],
    "age": ["age", "hull_age", "customer_age"],
    "temperature": ["temperature", "temp", "temperature_2m_max"],
    "precipitation": ["precipitation", "precip", "precipitation_sum"],
    "price": ["price", "close", "last_price"],
    "spread": ["spread", "basis", "differential"],
    "volume": ["volume", "transaction_volume", "trade_volume"],
}

_SUFFIX_MAP = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}


def _parse_threshold(text: str) -> tuple[float | None, str]:
    """Extract threshold and direction from natural language conditions."""
    # Try structured format first
    m = _OPERATOR_RE.search(text.lower().replace(",", "").replace("$", ""))
    if m:
        return float(m.group(3)), m.group(2)

    # Try natural language "exceeds X"
    m = _NL_THRESHOLD_RE.search(text)
    if m:
        val = float(m.group(1).replace(",", ""))
        suffix = (m.group(2) or "").lower()
        val *= _SUFFIX_MAP.get(suffix, 1)
        return val, ">"

    # Try "below X"
    m = _NL_BELOW_RE.search(text)
    if m:
        val = float(m.group(1).replace(",", ""))
        suffix = (m.group(2) or "").lower()
        val *= _SUFFIX_MAP.get(suffix, 1)
        return val, "<"

    return None, ""


def _find_field(conditions: str, data_fields: list[str]) -> str | None:
    """Map a natural language condition to a data field by keyword matching."""
    cond_lower = conditions.lower()

    # First: try direct field name match
    for field in data_fields:
        if field.lower() in cond_lower:
            return field

    # Second: try keyword → field mapping
    # Prefer the keyword that appears EARLIEST in the condition (likely the subject)
    matches = []
    for keyword, candidate_fields in _FIELD_KEYWORDS.items():
        pos = cond_lower.find(keyword)
        if pos >= 0:
            for cf in candidate_fields:
                if cf in data_fields:
                    matches.append((pos, cf))
                    break

    if matches:
        # Return the field whose keyword appears earliest in the condition
        matches.sort()  # lowest position = earliest mention
        return matches[0][1]

    return None


def check_rule(rule: dict, data: dict | list) -> dict | None:
    """Check a single rule against fetched data.

    Returns a triggered-report dict if the rule fires, None otherwise.
    Handles both structured conditions (field > 123) and natural language
    ("single cash transaction exceeds BRL 50,000").
    """
    conditions = rule.get("conditions", "") or rule.get("text", "") or rule.get("answer", "")
    threshold, operator = _parse_threshold(conditions)
    if threshold is None:
        return None

    # Get available data fields
    if isinstance(data, dict):
        data_fields = list(data.keys())
    elif isinstance(data, list) and data:
        data_fields = list(data[0].keys()) if isinstance(data[0], dict) else []
    else:
        return None

    field = _find_field(conditions, data_fields)
    if field is None:
        return None

    # Get current value(s)
    if isinstance(data, dict):
        current = data.get(field)
    elif isinstance(data, list):
        # For CSV with multiple rows: check each row, trigger on any
        for row in data:
            val = row.get(field)
            try:
                val = float(val)
            except (ValueError, TypeError):
                continue
            ops = {">": val > threshold, "<": val < threshold,
                   ">=": val >= threshold, "<=": val <= threshold,
                   "==": val == threshold, "!=": val != threshold}
            if ops.get(operator, False):
                return {
                    "rule_id": rule.get("id", rule.get("_hash", "unknown")),
                    "confidence": rule.get("confidence", 0),
                    "conditions": conditions[:200],
                    "current_value": val,
                    "threshold": threshold,
                    "field": field,
                    "operator": operator,
                    "unit": "",
                    "impact": rule.get("action", ""),
                    "matched_row": row,
                }
        return None
    else:
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
        text = path.read_text().strip()
        if text.startswith("{"):
            # JSON object — likely bdistill export format {metadata, rules, context}
            data = json.loads(text)
            if "rules" in data and isinstance(data["rules"], list):
                entries = data["rules"]
            else:
                entries = [data]
        elif text.startswith("["):
            # JSON array
            entries = json.loads(text)
        else:
            # JSONL — one entry per line
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
