# bdistill-skills

7 composable AI skills that turn any AI agent into a structured knowledge extraction and decision system. Works with Claude Code, VS Code Copilot, Cursor, Codex CLI, Windsurf, Cline, and 30+ other agents.

**No API key. No MCP server. No dependencies. Just markdown that teaches your agent new capabilities.**

## Install

```bash
# All 7 skills
npx skills add FrancyJGLisboa/bdistill-skills

# Just one skill
npx skills add FrancyJGLisboa/bdistill-skills --skill bdistill-extract
```

For full power (session management, quality scoring, compounding KB), also install the MCP server:

```bash
pipx install bdistill    # optional — every skill works without it
```

## The Skills

| Skill | What it does | You say |
|-------|-------------|---------|
| **bdistill-discover** | Map your domain into extractable topics | "I work in insurance" / "help me get started" |
| **bdistill-extract** | Build a validated knowledge base or decision rules | "extract rules about AML thresholds" |
| **bdistill-validate** | Detect confabulated numbers via consistency probing | "are these thresholds real or hallucinated?" |
| **bdistill-predict** | Structured predictions with evidence chains | "will the Fed cut rates before July?" |
| **bdistill-export** | Export KB to Claude/Cursor/Copilot/Excel/JSONL | "export as Claude Project prompt" |
| **bdistill-operationalize** | Contrast rules against live API data | "check current weather against yield rules" |
| **bdistill-xray** | Probe AI model behavioral patterns | "x-ray your own behavior" |

## How they chain

Skills are composable — each skill's output is the next skill's input.

```
bdistill-discover --> bdistill-extract --> bdistill-validate --> bdistill-export --> bdistill-operationalize
                            |
                            v
                      bdistill-predict
```

The shared data format is JSONL — one line per knowledge entry or rule. Every skill reads and writes the same format, so an agent can chain them without glue code.

## Example chains

**Compliance officer** — "Make my AI tool reliable for AML questions"
```
bdistill-extract(domain=aml-compliance) --> bdistill-export(platform=claude-project) --> paste into AI tool
```

**Insurance underwriter** — "I need deterministic rules for marine cargo risk"
```
bdistill-discover --> bdistill-extract(mode=rules) --> bdistill-validate --> bdistill-export(format=json)
```

**Macro trader** — "Will the Fed cut before July?"
```
bdistill-extract(domain=macro-rates) --> bdistill-predict(binary=true, grounded=true)
```

**Ag operations** — "Monitor weather against crop yield thresholds"
```
bdistill-extract(mode=rules) --> bdistill-validate --> bdistill-export(format=json) --> bdistill-operationalize(api=open-meteo)
```

**Agent builder** — "Inject domain knowledge deterministically"
```
bdistill-extract --> bdistill-export(format=harness-python) --> import RULES, build_prompt() in your code
```

## Agent-first design

These skills are designed to be called by agents, not just by humans:

- **Structured contracts**: Every skill declares typed input/output in YAML — agents parse these deterministically
- **Description as routing signal**: Skill descriptions contain trigger phrases so agent orchestrators auto-select the right skill
- **Composable outputs**: Each output is a valid input to downstream skills
- **Two modes**: With bdistill MCP (full session management) or standalone (agent writes JSONL directly)

## Individual skill docs

Each skill folder contains a `SKILL.md` with:
- When to use (specific scenarios)
- Input/output contracts (YAML)
- MCP workflow (tool call sequences)
- Standalone workflow (no dependencies)
- Edge cases
- Example with concrete input/output
- "Composes with" section (what to chain next)

Some skills include reference material in `references/` and scripts in `scripts/`.

## What each skill produces

| Skill | Output format | Output location |
|-------|--------------|-----------------|
| bdistill-discover | JSON (domain map + seed terms) | `data/discovery/{domain}-seeds.json` |
| bdistill-extract | JSONL (knowledge or rule entries) | `data/knowledge/base/{domain}.jsonl` or `data/rules/base/{domain}.jsonl` |
| bdistill-validate | JSON (stability scores per entry) | `data/consistency/{domain}-results.json` |
| bdistill-predict | JSON (prediction card) + HTML | `data/predictions/cards/{card_id}.json` |
| bdistill-export | Markdown, Python, JSON, Excel, CSV, JSONL | `data/knowledge/exports/` |
| bdistill-operationalize | JSON (decision report) | `data/reports/{domain}-{date}.json` |
| bdistill-xray | JSON (behavioral profile) + HTML report | `data/self-probe/` |

## Works with

Tested with: Claude Code, VS Code Copilot, Cursor, Codex CLI, Windsurf, Cline. Should work with any tool that supports the [SKILL.md open standard](https://agentskills.io/specification).

## Full power: bdistill MCP server

The skills work standalone, but installing the MCP server unlocks:
- Session management (resume interrupted extractions)
- Adversarial validation (automatic challenges during extraction)
- Quality scoring and deduplication across sessions
- Compounding knowledge base (sessions merge, not overwrite)
- HTML prediction cards and behavioral reports

```bash
pipx install bdistill
bdistill setup    # auto-detects and configures your AI tools
```

See [bdistill](https://github.com/FrancyJGLisboa/bdistill) for the full package.

## License

MIT
