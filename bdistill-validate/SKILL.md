---
name: bdistill-validate
description: Detect confabulated numeric claims by re-asking extracted entries with rephrased questions. Flags entries as stable (consistent across 5 rephrasings) or unstable (numbers vary). Use after bdistill-extract to filter your KB before export. Triggers on "validate KB", "consistency check", "are these numbers real", "verify thresholds", "detect hallucination". Outputs stability scores per entry.
license: MIT
metadata:
  author: bdistill
  version: "1.0"
  suite: bdistill
---

## When to use

- **After bdistill-extract, before exporting** -- filter out unreliable entries so your exported KB only contains claims the model reproduces consistently.
- **When thresholds in your KB seem suspiciously precise** -- a rule that says "trigger at 47.3%" deserves a consistency check. Real knowledge reproduces; confabulations drift.
- **When building rules for a deterministic system** -- if the rules will drive automation or monitoring, every numeric threshold must survive rephrasing. One unstable number can cascade into bad decisions.
- **Before bdistill-operationalize** -- only promote entries to production monitoring if they are stable. Unstable entries need re-extraction or external sourcing.

## Input contract

```yaml
required:
  domain: string          # Domain name matching your KB (e.g. "aml-compliance")
optional:
  source_type: string     # "knowledge" or "rules" (default: "rules")
  num_rephrases: int      # Number of rephrased questions per entry (default: 5)
  max_entries: int        # Maximum entries to probe (default: 20)
```

## Output contract

```yaml
format: JSON
top_level:
  domain: string
  total_probed: int
  stable: int
  unstable: int
  results: array
per_entry:
  entry_id: string
  original_claim: string
  stable: bool
  consistency_score: float   # 0.0 to 1.0
  values: array              # Numbers extracted from each rephrase
tiers:
  stable: ">= 0.85"
  moderate: "0.60 - 0.85"
  unstable: "< 0.60"
```

## With bdistill MCP (full power)

1. Call `bdistill_consistency_start` with domain, source_type, and max_entries.
2. For each probe the server sends back, answer naturally from your knowledge. Do NOT try to be consistent with previous answers -- the whole point is to test whether consistency emerges on its own.
3. Call `bdistill_consistency_respond` with your answer.
4. The server extracts numbers from each response, tracks variance across rephrasings, and computes a consistency score per entry.
5. When all probes are done, call `bdistill_consistency_export` to save results to `data/consistency/{domain}-results.json`.

## Standalone (no dependencies)

Use this procedure when the MCP server is not available.

1. Read KB entries from `data/knowledge/base/{domain}.jsonl` or `data/rules/base/{domain}.jsonl` (based on source_type).
2. For each entry containing numeric claims, generate 5 rephrased questions using these strategies:

| Strategy | Template | What it tests |
|----------|----------|---------------|
| Direct | "What is the threshold for X?" | Baseline recall |
| Scenario | "At what point does X trigger?" | Different framing |
| Confirm wrong | "Is it true the value is [wrong number]?" | Anchoring susceptibility |
| Context shift | "From a practitioner's perspective, what value?" | Role-based drift |
| Precision | "What is the exact numeric value for X?" | Forces specificity |

3. Answer each rephrase independently. Do not reference previous answers.
4. Extract all numbers from each answer.
5. Compute the coefficient of variation (CV) across the extracted values:
   - **stable**: CV < 0.15
   - **moderate**: CV between 0.15 and 0.40
   - **unstable**: CV > 0.40
6. Write the results array to `data/consistency/{domain}-results.json`.

## Edge cases

- **No numeric claims found**: Report `"0 entries probed -- KB has no numeric thresholds to validate"` and exit cleanly. This is not an error.
- **KB too large**: Sample the top 20 entries ranked by confidence score. Pass `max_entries` to override.
- **Anchoring test**: If the model parrots back the deliberately wrong number from the "Confirm wrong" strategy, flag that entry as unstable regardless of other scores. Anchoring susceptibility is a strong signal of confabulation.

## Example

Two entries probed from the `aml-compliance` domain:

```
Entry: "SAR filing threshold R$50,000"
  Rephrase 1 (Direct):        R$50,000
  Rephrase 2 (Scenario):      R$50,000
  Rephrase 3 (Confirm wrong): "No, it is R$50,000"
  Rephrase 4 (Context shift): R$50,000
  Rephrase 5 (Precision):     R$50,000
  -> consistency_score: 1.0, stable: true

Entry: "EDD cumulative transaction limit"
  Rephrase 1 (Direct):        R$80,000
  Rephrase 2 (Scenario):      R$100,000
  Rephrase 3 (Confirm wrong): "Yes, R$90,000 sounds right" (anchored!)
  Rephrase 4 (Context shift): R$100,000
  Rephrase 5 (Precision):     R$75,000
  -> consistency_score: 0.67, stable: false
```

The first entry is real regulatory knowledge. The second is likely confabulated -- the model does not have a stable representation of that number.

## Composes with

- **bdistill-export**: Filter unstable entries before exporting. Keep only stable and moderate tiers to produce a trustworthy KB.
- **bdistill-extract**: Re-extract on topics where entries were flagged unstable. Provide external sources or narrower prompts to ground the knowledge.
