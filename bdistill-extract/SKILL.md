---
name: bdistill-extract
description: Extract structured, adversarially validated domain knowledge or IF-THEN decision rules from AI training knowledge. Builds a compounding knowledge base — one file per domain, deduplicated across sessions. Triggers on "extract knowledge", "build KB", "distill", "extract rules", "decision thresholds", "what do you know about". Outputs JSONL entries to {domain}.jsonl.
license: MIT
metadata:
  author: bdistill
  version: "1.0"
  suite: bdistill
---

# Domain Knowledge and Rules Extraction

Extract structured domain knowledge or IF-THEN decision rules from an AI model's training knowledge. Each extraction session appends to a persistent, deduplicated JSONL file scoped by domain name. Adversarial validation is on by default — every answer gets challenged for evidence before it earns a high confidence score.

## When to use

- Build a reference knowledge base for your niche domain (one session or many)
- Extract IF-THEN decision rules with specific numeric thresholds
- Stop re-asking the same domain questions every session — persist answers to disk
- Generate adversarially validated entries where each claim is challenged for evidence
- Build training data for fine-tuning downstream models (feeds bdistill-export)

## Choosing mode: knowledge vs rules

**Use `mode: rules` when** the user needs IF-THEN logic for decision systems, monitoring, or automation. Signal words: "thresholds", "triggers", "rules", "criteria", "limits", "when should I", "at what point", "decision logic", "classification rules".

**Use `mode: knowledge` when** the user needs reference material, explanations, or training data. Signal words: "explain", "how does X work", "what is", "knowledge base", "reference", "training data", "Q&A".

**When ambiguous**, ask: "Do you need structured IF-THEN rules with numeric thresholds (for a decision system or monitoring), or Q&A reference knowledge (for a searchable KB or training data)?"

| User says | Mode | Why |
|-----------|------|-----|
| "extract AML transaction thresholds" | rules | "thresholds" = numeric decision boundaries |
| "extract knowledge about cardiac arrest treatment" | knowledge | "knowledge about" = reference Q&A |
| "I need rules for my underwriting system" | rules | "rules for my system" = automation |
| "build a KB on Kubernetes" | knowledge | "KB on" = reference material |
| "what are the criteria for SAR filing?" | rules | "criteria" = decision conditions |
| "help me understand FOMC mechanics" | knowledge | "understand" = explanatory |

## Input contract

```yaml
required (one of):
  domain: string           # Preset domain slug ("aml-compliance-brazil", "wheat-winter-ks")
  custom_terms: string[]   # Free-form terms — more specific extracts better
  seed_terms: string[]     # Output from bdistill-discover
optional:
  mode: enum[knowledge, rules]  # Default: knowledge
  adversarial: bool              # Default: true — challenge every answer
  target: int                    # Entry count for autonomous loop (no human in the loop)
output:
  domain: string
  entries_added: int
  avg_confidence: float
  kb_path: string          # Absolute path to the JSONL file written
```

## Output contract

```yaml
format: JSONL appended to domain-scoped file
paths:
  knowledge: data/knowledge/base/{domain}.jsonl
  rules: data/rules/base/{domain}.jsonl

knowledge_entry_schema:
  question: string
  answer: string
  domain: string
  category: string
  confidence: float        # 0.0-1.0
  tier: enum[verified, solid, approximate]
  validated: bool
  tags: string[]
  source_model: string
  extracted_at: string     # ISO 8601

rules_entry_schema:
  conditions: string[]     # IF clauses with numeric thresholds
  action: string           # THEN clause
  domain: string
  confidence: float
  tier: enum[verified, solid, approximate]
  validated: bool
  tags: string[]
  source_model: string
  extracted_at: string
```

## With bdistill MCP (full power)

### Knowledge mode

1. Call `bdistill_distill_start` with `model_name`, `domain` or `custom_terms`, and `adversarial=true`
2. Receive a domain question — answer it with detailed, specific knowledge (100+ words, named entities, numeric anchors)
3. Call `bdistill_distill_respond` with your answer
4. If adversarial: a challenge comes back — defend your claim with evidence, correct inaccuracies, or deepen with specifics
5. Call `bdistill_distill_respond` again with the defended answer
6. Repeat steps 2-5 until the server signals completion
7. Call `bdistill_distill_export` to write the JSONL file

### Rules mode

1. Call `bdistill_rules_start` with `model_name`, `domain` or `custom_terms`
2. Receive a prompt — answer with concrete IF-THEN rules including numeric thresholds
3. Call `bdistill_rules_respond` with your rules
4. Repeat until the server signals completion
5. Call `bdistill_rules_export` to write the JSONL file

### Adversarial flow detail

After each answer, the server sends one of:
- **CHALLENGE**: "What evidence supports this?" — cite sources, data, or reasoning
- **EDGE_CASE**: "What about [scenario]?" — address the boundary condition
- **CONTRADICTION**: "Earlier you said X, now Y" — reconcile or correct

Defend honestly. If the original answer was wrong or vague, correct it. Corrected answers that cite evidence score higher than unchallenged ones.

## Standalone (no dependencies)

Use this flow when bdistill MCP tools are unavailable.

1. **Generate questions** (30-50 per session). Mix these question types from the seed/custom terms:
   - **Threshold**: "At what level does X trigger Y?"
   - **Mechanism**: "How does X work step by step?"
   - **Precedent**: "What happened when X occurred in [year/context]?"
   - **Edge case**: "What breaks when X is combined with Y?"
   - **Regulation**: "What does [law/standard] require for X?"
   - **Quantitative**: "What is the typical range for X?"

2. **Answer each question** with detailed domain knowledge:
   - Minimum 100 words per answer
   - Include specific numbers, named entities, dates where possible
   - Cite regulations, standards, or data sources by name

3. **Adversarial self-challenge** (on by default — this is what separates extraction from prompting):

   After EACH answer, run 3 challenges before moving to the next question:

   **Challenge 1 — EVIDENCE**: "What specific evidence supports this? Cite a regulation number, dataset, study, or named source. If you cannot cite evidence, lower the confidence score."

   **Challenge 2 — EDGE CASE**: "What's an exception or boundary condition where this breaks? What about [specific scenario that tests the limits]?" Revise the answer to include the exception.

   **Challenge 3 — CONTRADICTION CHECK**: "Does this conflict with anything else in this KB? If you said X earlier but now say Y, reconcile or correct." (In standalone mode, re-read the JSONL file to check for conflicts with previously written entries.)

   After all 3 challenges, revise the original answer to incorporate corrections, exceptions, and evidence. The revised answer — not the original — is what gets scored and written to the KB.

   **Why this matters:** Without adversarial challenges, the model gives its first-pass answer — often vague, sometimes hallucinated, missing edge cases. After challenges, the same model produces entries with cited evidence, acknowledged exceptions, and corrected thresholds. Entries that survive 3 challenges earn the "verified" tier. Entries that were corrected during challenges are tagged `self-corrected` — which is actually a quality signal (the model knew enough to fix itself).

   **Cross-model adversarial:** For even stronger validation, extract the initial answer from Model A, then run the 3 challenges using Model B. Model B has no loyalty to Model A's claims and will challenge more aggressively. Tag these entries `cross-model-challenged`.

4. **Quality-score each entry** on a 0.0-1.0 scale:
   - 0.8-1.0 (verified): Specific numbers, named sources, adversarially defended
   - 0.65-0.79 (solid): Accurate mechanisms, some specificity, minor gaps
   - 0.5-0.64 (approximate): General knowledge, directionally right, thresholds uncertain
   - Below 0.5: Reject — do not write to file

5. **Write each entry** as one JSON line to the appropriate file:
   - Knowledge: `data/knowledge/base/{domain}.jsonl`
   - Rules: `data/rules/base/{domain}.jsonl`

6. **Deduplicate**: Before appending, check if a question with the same domain and similar text already exists in the file. If so, keep the version with higher confidence.

7. **Validate each JSON line before writing.** Parse the JSON string back to verify it's valid before appending to the file. Common agent errors: trailing commas, unescaped quotes in answer text, missing closing braces. If a line fails validation, fix it and retry — do not write malformed JSONL.

8. **Normalize the domain name**: lowercase, hyphens only, no spaces or special characters. `"AML Compliance Brazil"` → `"aml-compliance-brazil"`. This ensures sessions always merge into the same file regardless of how the user capitalizes or spaces the name.

## How compounding works (critical)

**All sessions with the same domain name merge into the same file.** This is how knowledge compounds — not by creating new files, but by appending to the existing one.

```
Session 1:  domain="aml-compliance-brazil", custom_terms=["BCB 3978", "SAR thresholds"]
            → 30 entries written to data/rules/base/aml-compliance-brazil.jsonl

Session 2:  domain="aml-compliance-brazil", custom_terms=["PEP screening", "beneficial ownership"]
            → 25 MORE entries merged into the SAME aml-compliance-brazil.jsonl (now 55)

Session 3:  domain="aml-compliance-brazil", custom_terms=["crypto AML", "travel rule"]
            → 20 MORE entries merged (now 75, deduplicated)
```

**The domain name is the key.** Different terms, different sessions, different days, **different models** — as long as the domain name is the same, everything compounds into one KB.

### Multi-model extraction

You can extract from Claude, GPT, Gemini, Llama, or any other model into the same KB. Each entry carries a `source_model` field so you always know where it came from.

```
Session 1:  model=Claude Opus, domain="aml-compliance-brazil", terms=["BCB 3978"]
            → 30 entries, each tagged source_model="claude-opus-4-6"

Session 2:  model=GPT-4o, domain="aml-compliance-brazil", terms=["SAR thresholds"]
            → 25 entries merged into SAME file, tagged source_model="gpt-4o"

Session 3:  model=Llama 3.1 70B (via Ollama), domain="aml-compliance-brazil"
            → 20 entries merged, tagged source_model="llama-3.1-70b"
```

Result: one KB with 75 entries from 3 models. Deduplication keeps the higher-quality version when two models answer the same question.

**Why this is valuable:**
- **Cross-model validation**: If Claude says the SAR threshold is R$50,000 and GPT also says R$50,000, that's stronger evidence than either alone
- **Coverage**: Different models have different training data — one might know BCB circulars better, another might know FATF guidelines better
- **Consistency probing across models**: Run `bdistill-validate` and entries where models disagree on the number are flagged as unstable — that's a real signal

**The caution:** Different models may use different terminology for the same concept ("SAR" vs "STR", "EDD" vs "enhanced due diligence"). Deduplication is by question text similarity, so slightly different phrasings may both survive. This is fine — downstream consumers (export, operationalize) handle synonyms. If you want to force deduplication, use the exact same custom_terms across models.

**The footgun:** If you accidentally use a different domain name, you split your KB:

```
BAD:
  Session 1: domain="aml-compliance"        → aml-compliance.jsonl (30 entries)
  Session 2: domain="aml-brazil"            → aml-brazil.jsonl (25 entries)  ← SPLIT!
  Session 3: domain="compliance-aml-brazil"  → compliance-aml-brazil.jsonl   ← SPLIT AGAIN!

GOOD:
  Session 1: domain="aml-compliance-brazil"  → aml-compliance-brazil.jsonl (30 entries)
  Session 2: domain="aml-compliance-brazil"  → same file (now 55 entries)
  Session 3: domain="aml-compliance-brazil"  → same file (now 75 entries, deduplicated)
```

**Agent behavior:** When starting a new extraction session, ALWAYS check if the user has an existing KB for a similar domain. If `data/knowledge/base/` or `data/rules/base/` contains a file with a similar name, suggest reusing that domain name instead of creating a new one. Ask: "You have an existing KB called 'aml-compliance-brazil' with 55 entries. Should I add to that, or create a separate KB?"

## Edge cases

- **Prefer custom_terms over preset domains.** "BCB Circular 3978 AML requirements" extracts better than "finance." Encode geography, regulations, and numeric anchors directly in the terms. See [references/domain-scoping-strategy.md](references/domain-scoping-strategy.md).
- **One domain per niche.** Use "aml-compliance-brazil" not "compliance." The export filters by domain name only, and deduplication collides across broad domains.
- **Quality drops below 0.5 average**: Stop extraction and suggest narrower custom_terms. Broad domains produce vague answers.
- **Model says "I don't know"**: Skip the question. Do not fabricate an answer to fill the entry count.
- **Conflicting entries**: When two entries contradict, keep both but tag the newer one with `supersedes: {entry_id}` so downstream consumers can resolve.

## Example

**Input:**
```yaml
custom_terms: ["BCB Circular 3978", "SAR filing thresholds"]
mode: rules
domain: aml-compliance-brazil
```

**Output (2 sample JSONL entries):**

```jsonl
{"conditions": ["IF cash transaction exceeds BRL 50,000", "IF transaction has no apparent economic purpose", "IF customer is PEP or PEP-related"], "action": "THEN file SAR with COAF within 24 hours per BCB Circular 3978 Art. 13", "domain": "aml-compliance-brazil", "confidence": 0.92, "tier": "verified", "validated": true, "tags": ["sar", "coaf", "threshold", "pep"], "source_model": "claude-opus-4-6", "extracted_at": "2026-03-30T14:00:00Z"}
{"conditions": ["IF wire transfer exceeds BRL 10,000", "IF originator or beneficiary information is incomplete", "IF destination is FATF grey-list jurisdiction"], "action": "THEN apply enhanced due diligence and retain records for 10 years per Lei 9613 Art. 10", "domain": "aml-compliance-brazil", "confidence": 0.87, "tier": "solid", "validated": true, "tags": ["edd", "wire-transfer", "fatf", "record-retention"], "source_model": "claude-opus-4-6", "extracted_at": "2026-03-30T14:00:00Z"}
```

## Composes with

- **bdistill-discover**: Provides seed_terms and domain slug as input to this skill
- **bdistill-validate**: Run after extraction to verify numeric thresholds are not confabulated
- **bdistill-consistency**: Re-probe numeric claims to detect unstable thresholds
- **bdistill-evaluate**: LLM-backed batch quality audit — grades entries on 5 semantic dimensions
- **bdistill-export**: Deploy the KB as a system prompt, harness module, training JSONL, or Excel workbook
- **bdistill-predict**: Recalled as grounded context when `grounded=true` is set on a prediction
