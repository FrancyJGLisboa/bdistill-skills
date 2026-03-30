---
name: bdistill-discover
description: Map any professional domain into extractable topics with seed terms and a recommended extraction plan. Triggers on "I work in", "what can you extract about", "help me get started", "map my domain", "I don't know what to extract". Outputs structured domain map with seed terms for bdistill-extract.
license: MIT
metadata:
  author: bdistill
  version: "1.0"
  suite: bdistill
---

# Domain Discovery

Turn a vague description of your work into a structured extraction plan. You describe your field, the agent maps it into extractable topics with seed terms, and you pick what to extract first.

## When to use

- You know your field but not what's worth extracting ("I work in insurance")
- You want a structured starting point before running bdistill-extract
- You're exploring what domain knowledge an AI model can provide
- You want to scope a large domain into focused extraction sessions

## Input contract

```yaml
required:
  description: string  # Vague domain description ("I trade grain futures", "I audit banks", "I manage clinical trials")
output:
  domain: string       # Suggested domain slug (e.g. "grain-trading", "aml-compliance", "pharma-regulatory")
  seed_terms: string[] # Extraction-ready terms for bdistill-extract
  recommended_mode: enum[knowledge, rules, predict]
  topic_map: object    # {category: [subtopics]}
```

## Output contract

```yaml
format: JSON object
fields:
  domain: string
  seed_terms: string[]
  recommended_mode: string
  topic_map:
    type: object
    example:
      regulatory: ["BCB Circular 3978", "COAF reporting", "PEP screening"]
      thresholds: ["SAR filing triggers", "EDD limits", "CTF travel rule"]
      mechanisms: ["transaction monitoring", "risk scoring", "beneficial ownership"]
```

## With bdistill MCP (full power)

1. Call `bdistill_discover` with the user's description
2. Generate a domain map: 4-6 categories with 3-5 subtopics each as JSON
3. Call `bdistill_discover_respond` with the JSON
4. Present topics to user. Ask which areas to extract.
5. Call `bdistill_discover_select` with chosen topic names
6. Generate specific seed terms as JSON
7. Call `bdistill_discover_respond` with seed terms
8. Pass seed_terms to bdistill-extract

## Standalone (no dependencies)

1. Ask the user: "Describe your work in one sentence."
2. Generate a domain map with 4-6 categories and 3-5 subtopics each:
   - **Thresholds**: numeric decision boundaries in the domain
   - **Mechanisms**: how things work step-by-step
   - **Precedents**: historical examples and what happened
   - **Edge cases**: exceptions, special conditions, gotchas
   - **Regulations**: rules, standards, compliance requirements
   - **Quantitative**: formulas, ratios, benchmarks
3. Present as numbered list. Ask user to pick.
4. For each selected category, generate 3-5 specific seed terms.
5. Write output as JSON to `data/discovery/{domain}-seeds.json`
6. Suggest: "Run bdistill-extract with these terms: ..."

## Edge cases

- User description too vague ("I work in finance"): Ask for specifics — "What decisions do you make day to day? What numbers matter?"
- Domain too broad: Split into sub-domains. "Insurance" → "marine-cargo", "cyber-risk", "professional-liability"
- User picks all topics: Suggest starting with thresholds + mechanisms (highest extraction value), defer precedents to second session

## Example

**Input:** "I do AML compliance audits for a Brazilian fintech"

**Output:**
```json
{
  "domain": "aml-compliance-brazil",
  "seed_terms": [
    "BCB Circular 3978 AML requirements",
    "COAF SAR reporting thresholds",
    "EDD enhanced due diligence triggers",
    "PEP screening criteria Brazil",
    "beneficial ownership identification rules",
    "transaction monitoring alert calibration"
  ],
  "recommended_mode": "rules",
  "topic_map": {
    "regulatory_framework": ["BCB Circular 3978", "Lei 9613", "COAF obligations"],
    "thresholds": ["SAR filing triggers", "EDD transaction limits", "CTF travel rule amounts"],
    "mechanisms": ["transaction monitoring pipeline", "risk scoring methodology", "STR workflow"],
    "edge_cases": ["structuring detection", "PEP family members", "crypto AML gaps"]
  }
}
```

## Composes with

- **bdistill-extract**: Pass `seed_terms` as `custom_terms` and `domain` as the domain name
- **bdistill-predict**: Pass `domain` for grounded predictions on the discovered domain
