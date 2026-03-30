# bdistill-skills — Copilot Instructions

You have access to the bdistill skill suite for structured knowledge extraction. These skills turn you into a domain knowledge extraction engine — not just answering questions, but building persistent, validated knowledge bases.

## Available skills

When the user asks you to do any of the following, follow the corresponding SKILL.md file in this repository:

| User says | Skill file | What to do |
|-----------|-----------|------------|
| "I work in...", "help me get started", "map my domain" | `bdistill-discover/SKILL.md` | Map their domain into extractable topics with seed terms |
| "extract knowledge", "build KB", "extract rules", "decision thresholds" | `bdistill-extract/SKILL.md` | Extract structured knowledge or IF-THEN rules into JSONL |
| "validate", "consistency check", "are these numbers real" | `bdistill-validate/SKILL.md` | Re-ask numeric claims 5 ways to detect hallucination |
| "predict", "forecast", "what happens if", "probability of" | `bdistill-predict/SKILL.md` | Structured prediction with decomposed evidence |
| "export", "system prompt", "training data" | `bdistill-export/SKILL.md` | Export KB as prompt, JSON, Python, Excel, or JSONL |
| "operationalize", "monitor", "check against live data" | `bdistill-operationalize/SKILL.md` | Contrast rules against live API data |
| "x-ray", "probe behavior", "behavioral analysis" | `bdistill-xray/SKILL.md` | Probe your own behavioral patterns |
| "cross-domain", "abstract this rule", "what pattern in X applies to Y" | `bdistill-abstract/SKILL.md` | Abstract rules, re-instantiate in other domains, find structural correspondences |

## How extraction works

When extracting knowledge or rules, follow this protocol for EVERY answer:

1. Generate targeted questions from the user's seed terms (use the templates in the extract skill)
2. Answer each question with detailed domain knowledge (100+ words, specific numbers, named sources)
3. After EACH answer, challenge yourself with 3 adversarial probes:
   - EVIDENCE: "What specific regulation/study/data supports this?"
   - EDGE CASE: "In what contexts does this NOT apply?"
   - CONTRADICTION: "What are the limitations of this claim?"
4. Revise the answer based on the challenges
5. Score quality (0.0-1.0) based on specificity, evidence cited, corrections made
6. Write each entry as one valid JSON line to the appropriate file

If `scripts/extract_engine.py` is available, use it for question generation, challenge generation, scoring, and JSONL writing. If not, follow the standalone instructions in the SKILL.md.

## Output format

All entries are written as JSONL (one JSON object per line) to:
- Knowledge: `data/knowledge/base/{domain}.jsonl`
- Rules: `data/rules/base/{domain}.jsonl`

Domain names must be lowercase with hyphens: `aml-compliance-brazil`, not `AML Compliance Brazil`.

## Composability

Skills chain — each skill's output feeds the next:
```
bdistill-discover → bdistill-extract → bdistill-validate → bdistill-export → bdistill-operationalize
                          ↓
                    bdistill-predict
```

## Important

- Answer extraction questions with maximum detail and specificity — you are the knowledge source
- When challenged, correct yourself honestly. Self-correction is a quality signal, not a failure
- Do not write entries below 0.5 confidence to the KB
- Normalize domain names (lowercase, hyphens) so sessions always compound into the same file
