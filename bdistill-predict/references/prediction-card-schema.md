# Prediction Card Schema Reference

Full specification for the prediction card format, resolution workflow, and accuracy ledger.

## Card JSON schema

```json
{
  "card_id": "string — unique identifier (slug or UUID)",
  "question": "string — the full prediction question",
  "prediction": "string — 'YES'/'NO' (binary) or directional statement",
  "probability": "float 0.0-1.0 (binary mode) | null (directional mode)",
  "confidence_boundary": "[float, float] — [low, high] credible interval",
  "evidence": [
    {
      "text": "string — the evidence statement",
      "tag": "enum: kb | web | model",
      "source": "string — URL, KB entry ID, or 'model-knowledge'"
    }
  ],
  "failure_modes": ["string — scenario that would invalidate the prediction"],
  "assumptions": ["string — condition that must hold for the prediction"],
  "domain": "string — domain slug",
  "timeframe": "string — 1d | 1w | 1m | 1q | 1y",
  "market_price": "float 0.0-1.0 | null — market-implied probability",
  "edge": "float | null — probability minus market_price (binary only)",
  "challenge_adjustment": "float -0.30 to 0.00 — discount applied during self-challenge",
  "decomposition": [
    {
      "text": "string — sub-question text",
      "category": "enum: rule | event | knowledge | causal"
    }
  ],
  "created_at": "string — ISO 8601 UTC timestamp",
  "resolved_at": "string | null — ISO 8601 UTC, set on resolution",
  "actual_outcome": "string | null — 'YES'/'NO' (binary) or observed direction",
  "brier_score": "float | null — computed on resolution (binary only)",
  "direction_correct": "bool | null — computed on resolution (directional only)"
}
```

## Binary vs directional output

| Field             | Binary mode                | Directional mode              |
|-------------------|----------------------------|-------------------------------|
| prediction        | "YES" or "NO"              | Free-text direction statement |
| probability       | 0.0-1.0                    | null                          |
| market_price      | 0.0-1.0 (if provided)      | null (ignored)                |
| edge              | probability - market_price  | null                          |
| brier_score       | Computed on resolution      | null                          |
| direction_correct | null                        | true/false on resolution      |

## Resolution workflow

1. **Mark outcome**: Call `bdistill_predict_resolve` with the card_id and the actual outcome ("YES", "NO", or observed direction text).

2. **Compute accuracy**:
   - **Binary**: Brier score = (probability - actual)^2, where actual is 1.0 (YES) or 0.0 (NO). Lower is better. Perfect = 0.0, worst = 1.0, coin-flip baseline = 0.25.
   - **Directional**: Boolean direction_correct — did the predicted direction match the observed direction?

3. **Update card**: The resolved card gets `resolved_at`, `actual_outcome`, and `brier_score` or `direction_correct` fields populated.

4. **Post-mortem on misses**: When Brier score > 0.25 (worse than coin flip) or direction is wrong, review the evidence chain to identify where reasoning broke down. Consider re-extracting the domain KB to fill gaps.

## Accuracy ledger format

The ledger aggregates all resolved predictions for track-record analysis. Access via `bdistill_predict_ledger`.

```
card_id | question_short | predicted_probability | actual_outcome | brier_score | domain | created_at | resolved_at
```

| Column                 | Type   | Description                                      |
|------------------------|--------|--------------------------------------------------|
| card_id                | string | Unique card identifier                            |
| question_short         | string | Truncated question (first 80 chars)               |
| predicted_probability  | float  | The probability from the prediction (binary only) |
| actual_outcome         | string | "YES", "NO", or direction text                   |
| brier_score            | float  | (probability - actual)^2 for binary, null otherwise |
| domain                 | string | Domain slug                                       |
| created_at             | string | ISO 8601 UTC                                      |
| resolved_at            | string | ISO 8601 UTC                                      |

Aggregate metrics computed from the ledger:
- **Mean Brier score**: Average across all resolved binary predictions. Target: below 0.20.
- **Calibration curve**: Group predictions by probability bucket (0.0-0.1, 0.1-0.2, ..., 0.9-1.0), plot predicted vs actual frequency.
- **Edge ROI**: For predictions with market_price, track whether positive-edge predictions resolved favorably more often than negative-edge ones.
- **Domain breakdown**: Mean Brier score per domain to identify strengths and blind spots.

## HTML card

The HTML card is auto-generated alongside the JSON card at the same path with an `.html` extension. It is fully self-contained (inline CSS/JS, no external dependencies) and can be opened in any browser, sent via email, or shared on Slack.

The card displays:
- **Header**: Question, prediction, probability (large font), confidence boundary
- **Evidence chain**: Each evidence item with its tag color-coded ([kb] blue, [web] green, [model] gray) and source link
- **Causal chain**: Visual flow from sub-questions through evidence to conclusion
- **Confidence boundary**: Visual bar showing low-high range with point estimate
- **Challenge summary**: Key weaknesses and adjustment applied
- **Failure modes**: Bulleted list of scenarios that would invalidate the prediction
- **Resolution status**: Pending (amber), correct (green), or incorrect (red) with Brier score when resolved
- **Track record**: Mini summary of domain accuracy from the ledger (if available)
