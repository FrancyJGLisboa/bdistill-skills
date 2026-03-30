# Free API Catalog for Rules Monitoring

Reference table of free APIs usable with bdistill-operationalize. All APIs listed here have a free tier sufficient for periodic rule checks.

## API Reference

| API | Domain | Auth | Rate limit | Base URL | Example endpoint |
|-----|--------|------|------------|----------|-----------------|
| Open-Meteo | Weather / climate | None | Unlimited (non-commercial) | `api.open-meteo.com/v1/forecast` | `?latitude=-12.68&longitude=-56.92&daily=precipitation_sum` |
| FRED | Macro economics | Free API key | 120 req/min | `api.stlouisfed.org/fred/series/observations` | `?series_id=DGS10&api_key=YOUR_KEY&sort_order=desc&limit=1` |
| Yahoo Finance | Market prices | None | ~2,000 req/hour | `query1.finance.yahoo.com/v8/finance/chart` | `/ZS=F?interval=1d&range=5d` |
| CoinGecko | Crypto prices | None | 30 req/min | `api.coingecko.com/api/v3` | `/simple/price?ids=bitcoin&vs_currencies=usd` |
| GNews | News headlines | Free API key | 100 req/day | `gnews.io/api/v4/search` | `?q=soybean+tariff&token=YOUR_KEY&lang=en` |
| Open-Meteo Historical | Historical weather | None | Unlimited (non-commercial) | `archive-api.open-meteo.com/v1/archive` | `?latitude=-12.68&longitude=-56.92&start_date=2025-01-01&end_date=2025-12-31&daily=precipitation_sum` |

## Notes on specific APIs

- **FRED**: Register at `fred.stlouisfed.org/docs/api/api_key.html`. Key is free and instant. Useful series: DGS10 (10Y yield), DGS2 (2Y yield), T10Y2Y (spread), UNRATE, CPIAUCSL.
- **Yahoo Finance**: No official API key. Use `query1.finance.yahoo.com` or `query2.finance.yahoo.com`. Futures tickers use `=F` suffix (e.g., `ZS=F` for soybeans, `ZC=F` for corn).
- **Open-Meteo**: No key, no signup. Supports forecast (16 days), historical (1940-present), and marine endpoints. Daily and hourly granularity.
- **CoinGecko**: Free tier requires no key. Pro tier available for higher limits. Use `/coins/{id}/market_chart` for historical data.

## Using custom data sources

When the built-in fetchers don't cover your domain, you have two options:

### Local CSV file

Place your data file anywhere accessible and use `--source csv`:

```bash
python rules_monitor.py --rules my-rules.json --source csv --params '{"path": "/path/to/data.csv"}'
```

The CSV must have a header row. Column names are matched against rule condition field names.

### Remote JSON endpoint

Point to any URL that returns JSON with `--source json-url`:

```bash
python rules_monitor.py --rules my-rules.json --source json-url --params '{"url": "https://my-api.com/latest"}'
```

The returned JSON object's top-level keys are matched against rule condition field names. For nested responses, pre-process with `jq` or extend the `fetch_json_url` function.
