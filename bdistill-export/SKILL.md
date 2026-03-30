---
name: bdistill-export
description: Export a bdistill knowledge base into any format — system prompt for Claude Projects/Cursor/Copilot/ChatGPT, Python harness module with build_prompt(), JSON for agent consumption, Excel with quality color-coding, audit checklist CSV, or fine-tuning JSONL. Triggers on "export", "system prompt", "harness", "training data", "Excel export", "export for Claude Project". Outputs file on disk.
license: MIT
metadata:
  author: bdistill
  version: "1.0"
  suite: bdistill
---

## When to use

- Make your AI tool domain-reliable — paste validated rules into Claude Project/Cursor/Copilot
- Feed rules to a deterministic agent — export as Python module with RULES + build_prompt()
- Export JSON for bdistill-operationalize to contrast against live data
- Generate fine-tuning JSONL for LoRA training (alpaca/sharegpt/openai formats)
- Share with non-technical team — Excel with quality color-coding or audit checklist CSV

## Input contract

```yaml
required:
  domain: string          # Knowledge base domain name (e.g. "aml-compliance")
  format: enum            # prompt | harness-json | harness-python | excel | checklist | training-jsonl

optional:
  platform: enum          # claude-project | cursor-rules | copilot-instructions | chatgpt-custom | generic
  training_format: enum   # alpaca | sharegpt | openai
  min_quality: float      # Minimum quality score threshold (default: 0.7)
  max_rules: int          # Maximum number of rules to include (default: 50)
  max_context: int        # Maximum number of context entries to include (default: 20)
```

## Output contract

```yaml
format: File on disk. Path depends on format:
  prompt:         data/knowledge/exports/prompts/{domain}-{platform}-{date}.md
  harness-json:   data/knowledge/exports/harness/{domain}_{date}.json
  harness-python: data/knowledge/exports/harness/{domain}_{date}.py
  excel:          data/knowledge/exports/{domain}.xlsx
  checklist:      data/knowledge/exports/{domain}-checklist.csv
  training-jsonl: data/knowledge/exports/training/{domain}-{date}-train-{fmt}.jsonl  # + val split

returns:
  path: string            # Absolute path to exported file
  format: string          # Format used
  entries_exported: int   # Total entries written
  stats:
    rules_count: int
    context_count: int
    quality_distribution: object   # e.g. {A: 12, B: 8, C: 3}
```

## Format comparison table

| Format | For | Contains | Who uses it |
|--------|-----|----------|-------------|
| prompt | AI tools | Markdown rules + context | Compliance officer pasting into Claude Project |
| harness-json | Agent code | JSON with rules/context arrays | Developer building a monitoring agent |
| harness-python | Python harness | RULES list + build_prompt() | Developer importing into sub-agent |
| excel | Review | Color-coded quality, filterable | Manager reviewing extracted knowledge |
| checklist | Audit | Blank status/evidence/owner columns | Auditor doing compliance review |
| training-jsonl | Fine-tuning | Instruction/output pairs + train/val | ML engineer training a LoRA adapter |

## With bdistill MCP (full power)

- **prompt**: Call `bdistill_export_prompt` with domain, platform, min_quality, max_rules, max_context
- **harness**: Call `bdistill_export_harness` with domain, format (json/python-dict/python-dataclass), min_quality, max_rules
- **excel**: Call `bdistill_export_excel` with domain, min_quality
- **checklist**: Call `bdistill_export_checklist` with domain
- **training**: Call `bdistill_training_export` with domain, format (alpaca/sharegpt/openai)

## Standalone (no dependencies)

1. Read entries from `data/knowledge/base/{domain}.jsonl` + `data/rules/base/{domain}.jsonl`
2. Filter by min_quality, sort by confidence descending
3. Partition into rules (entries containing IF/THEN/WHEN/THRESHOLD) and context (everything else)
4. Cap at max_rules and max_context
5. Format according to chosen format:
   - **prompt**: Generate markdown with `## Rules` section (IF-THEN formatted) + `## Context` section (Q&A formatted). Add platform-specific header.
   - **harness-json**: Write JSON with metadata, rules array, context array
   - **training-jsonl**: Convert to instruction/output pairs, split 80/20 train/val

## Platform paste instructions

- **Claude Project**: paste into Custom Instructions field
- **Cursor**: save as `.cursor/rules/{domain}.mdc`
- **Copilot**: append to `.github/copilot-instructions.md`
- **ChatGPT**: paste into Custom GPT Builder Instructions (8K char limit -- export truncates)

## Edge cases

- Domain has no entries: return error "No entries found for domain: {domain}"
- All entries below min_quality: lower threshold to 0.5 and warn
- Training export < 50 entries: warn "LoRA fine-tuning works best with 200+ entries"

## Example

Export "aml-compliance" as claude-project prompt:

- Input: domain="aml-compliance", format="prompt", platform="claude-project"
- Output: Markdown with 15 rules + 8 context entries, saved to exports/prompts/

## Composes with

- **bdistill-operationalize**: harness-json output is loaded as rules_path
- **Any AI tool**: prompt output is pasted into the tool's instruction field
- **bdistill-extract**: builds the KB that this skill exports
