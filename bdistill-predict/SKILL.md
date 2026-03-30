---
name: bdistill-predict
description: Assemble structured predictions with decomposed evidence, adversarial self-challenge, and calibrated probability. Supports binary YES/NO mode (prediction markets, any yes/no question) and directional mode. Optionally recalls from your KB and searches the web for current data. Triggers on "predict", "forecast", "what happens if", "probability of", "will X happen". Outputs prediction card with evidence chain.
license: MIT
metadata:
  author: bdistill
  version: "1.0"
  suite: bdistill
---

# Structured Prediction Assembly

Build predictions through a disciplined 4-phase pipeline: decompose the question, extract evidence, challenge your own reasoning, then predict with calibrated confidence. Every prediction produces a portable card with full provenance.

## When to use

- Make a structured forecast with evidence, not a vibes-based answer
- Binary YES/NO questions with probability (prediction markets, Polymarket, Kalshi)
- Scenario analysis ("what happens if the Fed cuts?", "will this merger close?")
- Ground predictions in your extracted KB + current web data
- Track accuracy over time with Brier scores and a resolution ledger

## Input contract

```yaml
required:
  question: string   # The prediction question ("Will the Fed cut rates before July 2026?")
  domain: string     # Domain slug ("macro-rates", "us-politics", "ag-commodities")
optional:
  binary: bool       # YES/NO mode with probability output (default: false)
  grounded: bool     # Recall KB entries + search web for current data (default: false)
  deep: bool         # 36 knowledge probes before extraction, ~25 min (default: false)
  medium_depth: bool # 12-18 knowledge probes, ~12 min (default: false)
  market_price: float  # Market-implied probability 0-1, enables edge calculation (default: null)
  timeframe: enum[1d, 1w, 1m, 1q, 1y]  # Resolution horizon (default: inferred from question)
output:
  card_id: string
  prediction: string           # "YES"/"NO" or directional statement
  probability: float           # 0.0-1.0 (binary mode only)
  confidence_boundary: [float, float]  # [low, high]
  evidence: array              # Tagged [kb]/[web]/[model]
  failure_modes: array         # What could make this prediction wrong
  card_path: string            # Path to saved prediction card
```

## Output contract

```yaml
format: JSON prediction card
location: data/predictions/cards/{card_id}.json
fields:
  card_id: string              # UUID or slug
  question: string
  prediction: string           # "YES"/"NO" or directional text
  probability: float           # 0.0-1.0 for binary, null for directional
  confidence_boundary: [float, float]
  evidence:
    type: array
    items:
      text: string
      tag: enum[kb, web, model]
      source: string           # URL, KB entry ID, or "model-knowledge"
  failure_modes: array[string]
  domain: string
  timeframe: string
  market_price: float | null
  edge: float | null           # probability - market_price (binary only)
  created_at: string           # ISO 8601 UTC
also_generates:
  - data/predictions/cards/{card_id}.html  # Shareable HTML card
```

## With bdistill MCP (full power)

This is the primary workflow. The MCP server manages state, phases, and export.

1. **START**: Call `bdistill_predict_start` with question, domain, and optional flags (binary, grounded, deep, medium_depth, market_price, timeframe).

2. **DECOMPOSE**: Break the question into 4-6 sub-questions. Return a JSON array:
   ```json
   [
     {"text": "What does the latest dot plot signal?", "category": "event"},
     {"text": "Is PCE trending toward 2% target?", "category": "knowledge"},
     {"text": "What is the labor market signaling?", "category": "knowledge"},
     {"text": "How does a rate cut propagate to asset prices?", "category": "causal"}
   ]
   ```
   Categories: `rule` (IF-THEN logic), `event` (scheduled/observable), `knowledge` (facts/data), `causal` (mechanism/transmission).
   Call `bdistill_predict_respond` with your decomposition.

3. **DEEP PROBES** (if deep or medium_depth): The server generates knowledge probes automatically. Answer each probe with domain-specific detail. Call `bdistill_predict_respond` after each answer. Deep mode runs 36 probes; medium_depth runs 12-18.

4. **EXTRACT**: For each sub-question, gather detailed evidence. If grounded mode is on, search the web and recall KB entries. Tag every piece of evidence:
   - `[kb]` — from your extracted knowledge base
   - `[web]` — from web search during this session
   - `[model]` — from model training knowledge
   Call `bdistill_predict_respond` after each extraction.

5. **CHALLENGE**: Critique your own evidence. Structure as:
   - **Weak points**: Which evidence is thin or stale?
   - **Missing angles**: What did you not investigate?
   - **Key assumptions**: What must hold true for your prediction?
   - **ADJUSTMENT**: A number from -0.30 to 0.00 representing how much to discount your initial probability estimate. Typical range: -0.05 to -0.15.
   Call `bdistill_predict_respond` with your critique.

6. **PREDICT**: Final prediction as a JSON object:
   ```json
   {
     "prediction": "YES",
     "probability": 0.62,
     "confidence_boundary": [0.55, 0.70],
     "magnitude": "25bp cut, possibly 50bp",
     "assumptions": ["inflation continues declining", "no labor market shock"],
     "failure_modes": ["sticky services inflation", "geopolitical supply shock"],
     "timeframe": "1q"
   }
   ```
   Call `bdistill_predict_respond` with your prediction.

7. **EXPORT**: Call `bdistill_predict_export` to save the card (JSON + HTML). Offer to open the HTML card in the browser.

## Standalone (no dependencies)

Same 4-phase pipeline. The agent manages state and writes output directly.

1. **DECOMPOSE**: Break the question into 4-6 sub-questions with categories. Write to a scratch variable or temporary file.

2. **EXTRACT**: For each sub-question, gather evidence. If grounded, use web search. Tag each piece `[kb]`, `[web]`, or `[model]`.

3. **CHALLENGE**: Self-critique. Identify weak evidence, missing angles, key assumptions. Apply a probability adjustment (-0.30 to 0.00).

4. **PREDICT**: Assemble the final prediction card and write JSON to `data/predictions/cards/{id}.json`.

Card JSON schema for standalone mode:

```json
{
  "card_id": "fed-rate-cut-jul-2026-a1b2c3",
  "question": "Will the Fed cut rates before July 2026?",
  "prediction": "YES",
  "probability": 0.62,
  "confidence_boundary": [0.55, 0.70],
  "evidence": [
    {"text": "March dot plot shows median expectation of 2 cuts in 2026", "tag": "web", "source": "https://..."},
    {"text": "PCE at 2.4% and declining", "tag": "model", "source": "model-knowledge"}
  ],
  "failure_modes": ["sticky services inflation", "geopolitical supply shock"],
  "assumptions": ["inflation continues declining", "no labor market shock"],
  "domain": "macro-rates",
  "timeframe": "1q",
  "market_price": 0.40,
  "edge": 0.22,
  "created_at": "2026-03-30T14:00:00Z"
}
```

## Edge cases

- **Question too vague** ("what happens next?"): Ask the user for specifics — timeframe, domain, binary or directional?
- **No KB entries for domain**: Proceed with model-only and web evidence. Note lower confidence in the card and widen the confidence boundary.
- **market_price provided without binary**: Ignore market_price, use directional mode. Warn the user that edge calculation requires binary mode.
- **Deep + grounded**: Both flags compose. Deep probes run first to build context, then extraction uses KB + web. This is the highest-fidelity mode (~30 min).
- **Contradictory evidence**: Surface the contradiction explicitly in the CHALLENGE phase. Do not paper over it — let the confidence boundary reflect the disagreement.

## Example

**Input**: "Will the Fed cut rates before July 2026?" --binary --grounded --market_price 0.40

**DECOMPOSE** into 4 sub-questions:
1. What does the latest dot plot signal about rate expectations? (event)
2. Is PCE/CPI trending toward the 2% target? (knowledge)
3. What is the labor market signaling — cooling or resilient? (knowledge)
4. How are fed funds futures pricing cuts? (rule)

**EXTRACT** with [web] tags for current FRED data and dot plot, [model] for transmission mechanisms.

**CHALLENGE**: "Assuming inflation continues current trend, but services inflation is sticky at 3.1%. Labor market resilient — unemployment at 4.0%. Dot plot signals cuts but FOMC is data-dependent. ADJUSTMENT: -0.08"

**PREDICT**: YES, probability 0.62, confidence [0.55, 0.70], edge +0.22 vs market price of 0.40.

## Composes with

- **bdistill-distill / bdistill-extract**: Build a domain KB first for richer evidence when using grounded mode.
- **bdistill-calendar**: Check upcoming events, use them as prediction scenarios.
- **Resolution workflow**: Mark actual outcome on the card, compute Brier score (binary) or direction accuracy, re-extract on misses.
- **bdistill-predict-ledger**: `bdistill_predict_ledger` returns your track record across all resolved predictions.
- See `references/prediction-card-schema.md` for the full card format and resolution workflow.
