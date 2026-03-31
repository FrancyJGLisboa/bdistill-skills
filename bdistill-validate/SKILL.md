---
name: bdistill-validate
description: Detect confabulated claims by re-asking entries with rephrased questions and measuring variance — both numeric stability (do the numbers stay the same?) and structural stability (do the conditions, scope, and reasoning stay the same?). Use after bdistill-extract to filter your KB before export. Triggers on "validate KB", "consistency check", "are these numbers real", "verify thresholds", "detect hallucination", "stability check". Outputs stability scores per entry.
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
  numeric_consistency:
    score: float             # 0.0 to 1.0
    values: array            # Numbers extracted from each rephrase
  structural_consistency:
    condition_stability: float    # Do IF/WHEN conditions appear in all answers?
    scope_stability: float        # Do scope qualifiers stay the same?
    structure_stability: float    # Does the answer shape stay the same (IF-THEN, lists, exceptions)?
    length_stability: float       # Do answer lengths stay similar?
    overall: float
  combined_tier: string      # stable / moderate / unstable
tiers:
  stable: ">= 0.80 on both numeric AND structural"
  moderate: ">= 0.60 on both"
  unstable: "either below 0.60"
```

## Two dimensions of stability

| Dimension | What it catches | Example |
|-----------|----------------|---------|
| **Numeric** | The model says R$50K one time and R$80K another | Numbers are hallucinated — no stable training signal |
| **Structural** | The model includes "except during harvest" in 3/5 answers but drops it in 2 | Conditions are unreliable — the model isn't sure about the exception |

A rule can be numerically stable (same R$50K every time) but structurally unstable (sometimes includes "except for PEPs", sometimes doesn't). Both dimensions matter. An unstable condition is as dangerous as an unstable number — it means the agent might apply the rule when it shouldn't, or miss applying it when it should.

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

3. Answer each rephrase independently. **Critical: do not reference previous answers.** To reduce contamination in standalone mode, insert unrelated reasoning between rephrasings (e.g., summarize an unrelated topic) to flush the model's short-term activation. If running as a sub-agent, dispatch each rephrase as a separate sub-agent call so context is truly isolated.
4. **Numeric stability:** Extract numbers from each answer using the script:
   ```bash
   python scripts/validate_engine.py extract-numbers --text "the answer text"
   python scripts/validate_engine.py consistency-score --values '[50000, 50000, 48000, 50000, 50000]'
   ```
   Tiers: stable (CV < 0.15), moderate (0.15-0.40), unstable (> 0.40)

5. **Structural stability:** Pass ALL 5 freeform answers to measure non-numeric variance:
   ```bash
   python scripts/validate_engine.py structural-stability --answers '["answer1...", "answer2...", "answer3...", "answer4...", "answer5..."]'
   ```
   Returns 4 sub-scores:
   - **condition_stability**: Do IF/WHEN conditions appear in ALL answers, or only some? (e.g., "except during harvest" present in 3/5 = 0.60)
   - **scope_stability**: Do scope qualifiers stay the same? ("all financial institutions" in 3 answers but "banks only" in 2 = unstable)
   - **structure_stability**: Does the answer shape stay the same? (IF-THEN in all 5 vs IF-THEN in 3 and prose in 2)
   - **length_stability**: Are answers similar length, or does one answer have 200 words and another 40?

6. **Combined score:** An entry is only "stable" if BOTH numeric AND structural scores are >= 0.80. A rule where the number is stable but the conditions vary is unreliable.

7. Write results to `data/consistency/{domain}-results.json`.

## Edge cases

- **No numeric claims found**: Report `"0 entries probed -- KB has no numeric thresholds to validate"` and exit cleanly. This is not an error.
- **KB too large**: Sample the top 20 entries ranked by confidence score. Pass `max_entries` to override.
- **Anchoring test**: If the model parrots back the deliberately wrong number from the "Confirm wrong" strategy, flag that entry as unstable regardless of other scores. Anchoring susceptibility is a strong signal of confabulation.
- **Context contamination (standalone mode)**: All 5 rephrasings in the same context window means the model can see its previous answers. This inflates consistency scores — the model appears stable because it's copying itself, not because the knowledge is real. Mitigation: use MCP mode (isolates each probe), or dispatch each rephrase as a separate sub-agent, or insert unrelated content between rephrasings to flush context. Mark standalone results with `"isolation": "same-context"` so downstream consumers know the scores may be optimistic.
- **Cross-model score incompatibility**: A consistency score of 0.85 from Claude does not equal 0.85 from GPT-4o. Different models have different verbosity, numeric precision habits, and anchoring susceptibility. Do not mix validation results from different models in the same results file.

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
