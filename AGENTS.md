# bdistill-skills Agent Instructions

This repository contains 7 composable AI skills for structured knowledge extraction. Each skill has a SKILL.md file with input/output contracts, workflows, and examples.

## Skill routing

| User intent | Skill directory |
|-------------|----------------|
| Domain mapping, cold start | `bdistill-discover/` |
| Knowledge or rules extraction | `bdistill-extract/` |
| Consistency validation | `bdistill-validate/` |
| Structured predictions | `bdistill-predict/` |
| KB export (prompt, JSON, Excel) | `bdistill-export/` |
| Rules vs live data monitoring | `bdistill-operationalize/` |
| Behavioral self-probe | `bdistill-xray/` |
| Cross-domain rule transfer | `bdistill-abstract/` |

## Composability

```
bdistill-discover → bdistill-extract → bdistill-validate → bdistill-export → bdistill-operationalize
                          ↓
                    bdistill-predict
```

Each skill's output contract matches the next skill's input contract. Chain them by passing outputs as inputs.

## Shared data format

JSONL entries in `data/knowledge/base/{domain}.jsonl` and `data/rules/base/{domain}.jsonl`. Domain name is the merge key — same name = same file across sessions and models.

## Extraction protocol

For every answer during extraction, run 3 adversarial challenges (evidence, edge case, contradiction) before scoring and writing. Use `bdistill-extract/scripts/extract_engine.py` if available, or follow the standalone instructions in the SKILL.md.
