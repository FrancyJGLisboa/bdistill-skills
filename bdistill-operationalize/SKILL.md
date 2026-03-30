---
name: bdistill-operationalize
description: Connect exported rules to live data for automated monitoring. Loads a bdistill rules export, fetches current data from free APIs or local feeds, contrasts each rule's conditions against reality, and reports which rules triggered with current values and impact estimates. Works with any domain — weather, market, compliance, clinical. Triggers on "operationalize", "monitor", "check against live data", "contrast rules", "what's triggered". Outputs decision report.
license: MIT
metadata:
  author: bdistill
  version: "1.0"
  suite: bdistill
---

# Operationalize Rules Against Live Data

Connect extracted IF-THEN rules to real-world data sources. Load one or more bdistill rules exports, fetch current values from free APIs or local files, check each rule's conditions against reality, and produce a decision report listing which rules triggered, with current values, thresholds, and impact estimates.

## When to use

- Check AML transaction rules against a batch of transactions
- Monitor weather thresholds against crop yield rules
- Compare current market prices against trading signal thresholds
- Verify lab results against clinical trial criteria
- Run scheduled compliance checks against regulatory rules
- Any domain where you have IF-THEN rules and a data feed

## Input contract

```yaml
required:
  rules_path: string | string[]   # Path(s) to bdistill rules export JSON (multi-domain supported)
  data_source: enum               # open-meteo | fred | yahoo-finance | csv | json-url | custom
optional:
  lat: float                      # Latitude (required for open-meteo)
  lon: float                      # Longitude (required for open-meteo)
  ticker: string                  # Ticker symbol (required for yahoo-finance)
  series_id: string               # FRED series ID (required for fred)
  data_path: string               # Local file path (required for csv)
  data_url: string                # Remote JSON endpoint (required for json-url)
  api_key: string                 # API key (required for fred, gnews)
  context: object                 # Free-form context passed to condition matching
output:
  rules_checked: int
  triggered: array
  data_source: string
  checked_at: string              # ISO 8601 timestamp
  report_path: string             # Path to saved decision report JSON
```

## Output contract

```yaml
format: JSON decision report
path: data/reports/{domain}-{YYYY-MM-DD}.json
schema:
  context:
    domain: string
    data_source: string
    fetched_at: string
  checked_at: string
  rules_checked: int
  rules_source: string | string[]
  triggered:
    - rule_id: string
      confidence: float
      conditions: string
      current_value: float | string
      threshold: float | string
      unit: string
      impact: string
  skipped:                         # Rules that couldn't be mapped to available data
    - rule_id: string
      reason: string               # "Could not map 'soil_moisture' to available fields"
  data_source: object              # Raw or summary of fetched data
```

## The chain

This skill is the final step in the bdistill production pipeline:

```
bdistill-extract  -->  bdistill-export (format=harness-json)  -->  bdistill-operationalize
    (build KB)            (export rules)                           (check against reality)
```

## Standalone mode (primary — no MCP needed)

1. **Load rules** from one or more exported JSON files. Filter to verified/solid tier entries only.
2. **Fetch current data** from the specified source:
   - `open-meteo`: HTTP GET with lat/lon, returns daily weather (precipitation, temperature, wind)
   - `fred`: HTTP GET series observations with api_key, returns economic data points
   - `yahoo-finance`: HTTP GET quote endpoint, returns latest price data
   - `csv`: Read local CSV file into records
   - `json-url`: HTTP GET any JSON endpoint, parse response
   - `custom`: User provides data inline via the context object
3. **Map conditions to data fields.** This is the hard step. Rule conditions are natural language (`"cumulative_precip < 50mm during flowering"`), but API responses have structured fields (`"precipitation_sum": [1.2, 0.0, 3.4, ...]`). The agent must build a mapping:

   **Mapping strategy:**
   - For each rule, identify the **metric** (what to measure), **operator** (< > = !=), **threshold** (the number), and **unit**
   - Match the metric to an available data field by keyword similarity:
     - "precip" / "precipitation" / "rainfall" → `precipitation_sum`
     - "temp" / "temperature" / "Tmax" → `temperature_2m_max`
     - "spread" / "10Y-2Y" → compute from multiple FRED series
     - "price" / "close" → `regularMarketPrice` (Yahoo Finance)
   - If a condition references a **derived metric** (e.g., "cumulative_30d", "consecutive_dry_days"), compute it from raw data before checking
   - If a condition **cannot be mapped** to any available data field, skip it and log: `"SKIPPED: rule {id} — could not map '{metric}' to available fields: {list of fields}"`

   **Do not guess.** If the mapping is ambiguous, skip the rule rather than check against the wrong field. A false "not triggered" is worse than an honest "could not check."

4. **Check each mapped rule**: Compare current value against threshold using the parsed operator.
5. **If conditions are met** → rule triggered → add to report with current value, threshold, and impact.
6. **Write decision report** JSON to `data/reports/{domain}-{YYYY-MM-DD}.json`. Include a `skipped` array alongside `triggered` for rules that couldn't be mapped.
7. **Print summary**: "X of Y rules triggered, Z skipped (unmappable conditions)".

## Domain examples

| Domain | Data source | Example rule | Example check |
|--------|------------|-------------|---------------|
| AML compliance | Transaction CSV | cumulative_30d > R$100K | R$127,500 > R$100,000 -> triggered |
| Marine insurance | Claims JSON | hull_age > 20 years | 23 years > 20 -> triggered |
| Agriculture | Open-Meteo | precip < 50mm during R1-R3 | 32mm < 50mm -> triggered |
| Macro trading | FRED | 10Y-2Y spread < 0 | -0.15 < 0 -> triggered |
| Clinical trials | Lab CSV | ALT > 3x ULN | 156 U/L > 120 U/L -> triggered |
| Crypto | CoinGecko | btc_price < 20000 | $19,450 < $20,000 -> triggered |

## The feedback loop

When rules miss (predicted 15% yield loss, actual was 35%), feed back to bdistill-extract:

1. **Identify** which rules were wrong or missing coverage
2. **Re-extract** with `bdistill-extract` using narrower custom_terms targeting the gap
3. **Re-export** updated rules with `bdistill-export` (format=harness-json)
4. **Re-run** operationalize with the updated rules file

This creates a closed loop: extract -> export -> operationalize -> measure -> re-extract.

## Edge cases

- **Rule conditions can't be parsed**: Skip rule, log warning "Could not match rule {id} to available data fields". Include in report as `skipped`.
- **API returns no data**: Report error with API response details. Do not trigger any rules. Set `rules_checked: 0`.
- **Multiple rules triggered**: Report all, sorted by confidence descending.
- **Stale data**: If fetched data is older than 24 hours, add a `stale_warning` field to the report.
- **Multi-domain**: When `rules_path` is an array, check each file independently and merge triggered rules into a single report.

## Example

Load AML rules, check against a transaction batch:

```
Input:
  rules_path: "data/rules/base/aml-compliance-brazil.json"
  data_source: "csv"
  data_path: "transactions.csv"

Output:
  rules_checked: 14
  triggered:
    - rule_id: "aml-003"
      confidence: 0.92
      conditions: "cumulative_30d > 100000"
      current_value: 127500
      threshold: 100000
      unit: "BRL"
      impact: "Trigger Enhanced Due Diligence (EDD) review"
  report_path: "data/reports/aml-compliance-brazil-2026-03-30.json"
```

## Composes with

- **bdistill-export**: Produces the rules JSON this skill consumes (use `format=harness-json`)
- **bdistill-extract**: Re-extract when rules miss -> re-export -> re-operationalize
- **bdistill-calendar**: Schedule operationalize runs around known events (e.g., WASDE release day)
- **bdistill-predict**: Use triggered rules as evidence inputs for structured predictions
- See `references/api-catalog.md` for free API details
- See `scripts/rules_monitor.py` for a reference Python implementation
