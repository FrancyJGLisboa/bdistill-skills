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

## Q&A

### "So what? How can I leverage this? I'm a Commodities Research Analyst at a big corporate pushing for AI solutions."

**Three things you'd do in your first week:**

**1. Extract your team's institutional knowledge into a validated, reusable KB.**
Your senior analysts have rules in their heads: "when MT basis widens past -50 during off-harvest, it's logistics — but during Feb-Apr it's normal seasonal." That knowledge lives in Slack threads, old decks, and people's memories. When someone leaves, it leaves with them.

Tell your AI agent: *"extract rules about soybean basis risk by Brazilian region, crush margin GPM critical levels, CBOT contango storage trade entry conditions, FOB premium breakpoints Paranagua vs Santos"*

In 20 minutes you have 50+ structured IF-THEN rules with numeric thresholds, adversarially validated (the AI challenged its own claims — "what about during harvest season?" — and corrected itself). Run `bdistill-validate` and it re-asks each threshold 5 different ways to check if the number is real or hallucinated. Keep the stable ones, flag the unstable for your team to verify.

Export as a Claude Project prompt. Every analyst on your desk gets the same validated rules in every conversation — not a different answer depending on how they prompt.

**2. Structured predictions your desk can actually use.**
Your PM asks: "What happens to Brazil soybean FOB premiums if China cuts imports 10%?" Right now someone writes a paragraph in an email.

With bdistill-predict you get: probability 0.68, decomposed into 4 evidence pillars (demand elasticity, logistics buffer, crusher absorption, historical precedent 2018), each tagged `[kb]` or `[web]` for provenance, plus 3 failure modes. Shareable as an HTML card — send it to your PM, your risk desk, your traders.

After the event, resolve it. Now you have a Brier score. After 20 predictions, you have a track record. That's what your corporate AI committee wants to see — not "we use ChatGPT sometimes."

**3. Monitor live data against your rules — automatically.**
You extracted weather-yield rules. You exported them as JSON. Tell your agent: *"check these rules against current weather in Sorriso MT."*

Output: "1 of 38 rules triggered — cumulative precip = 32mm (threshold: 50mm during R1-R3), estimated yield loss 15-25%." Every number traces to a validated rule with a confidence score. Run it weekly.

When the rule misses (predicted 15% loss, actual was 30%), re-extract with narrower terms. The rules get better each season.

**The pitch for your corporate AI committee:**
"We're not just chatting with AI. We're extracting our team's domain expertise into a structured, validated knowledge base that compounds over time, making predictions with tracked accuracy, and monitoring live data against validated thresholds. Every rule has a confidence score, every prediction has a Brier score, every threshold has been checked for hallucination. It works with the AI tools we already pay for — zero additional API costs."

This example uses commodities, but the same chain works for any threshold-heavy domain: compliance, insurance underwriting, pharma regulatory, macro trading, clinical trials.

---

### "How do I know when I have enough rules? How do I know the quality is good enough?"

**You don't know upfront. You discover it by closing the loop.**

Start small, check coverage, expand where gaps show up:

**Week 1:** Extract 30-50 rules on your core niche. Then pick 3 real decisions you made last week and check — did the rules cover the inputs to those decisions? If 2 of 3 are covered, you're already useful. Expand on the gap.

**Week 2:** Run `bdistill-validate`. You'll find ~70% stable (same numbers every time → real knowledge), ~15% moderate, ~15% unstable (hallucinated → drop or verify externally). Export and operationalize the stable ones against live data.

**Week 3+:** The feedback loop tells you when you're done. If all your decisions are covered and rules match reality, you've converged.

**Quality signals:**

| Signal | Meaning | Action |
|--------|---------|--------|
| confidence >= 0.8, tier: verified | Adversarially challenged and defended | Trust it |
| confidence 0.65-0.79, tier: solid | Validated but with caveats | Use with ±5% tolerance |
| confidence < 0.65, tier: approximate | Directionally right, thresholds uncertain | Don't use for deterministic decisions |
| consistency: stable | Same number 5/5 rephrasings | Real training knowledge |
| consistency: unstable | Number varies across rephrasings | Hallucinated — verify externally or drop |

**Rule of thumb:** 50 validated, stable rules > 500 unvalidated entries. If you have 30+ rules at verified tier AND stable consistency, you have a usable decision system. If you have 100+ rules but half are unstable, you have noise.

| Your goal | Minimum viable KB | How you know it's enough |
|-----------|-------------------|--------------------------|
| Claude Project prompt | 20-30 high-quality entries | Common questions get correct, specific answers |
| Monitoring system | 30-50 verified + stable rules | All monitored metrics have at least one rule |
| Predictions with evidence | 50-100 entries | Predictions cite [kb] evidence for every sub-question |
| Fine-tuning a LoRA | 200-300 entries | Validation loss plateaus |

---

### "How easy to find are the KB and other artifacts generated by the suite?"

Everything lives in one `data/` directory, created where you launched your AI tool. The structure is flat and predictable:

```
data/
├── knowledge/
│   └── base/                     ← YOUR KNOWLEDGE BASES
│       ├── aml-compliance.jsonl  ← one file per domain, human-readable JSON lines
│       ├── marine-cargo-uk.jsonl
│       └── macro-rates-us.jsonl
│
├── rules/
│   └── base/                     ← YOUR DECISION RULES
│       ├── aml-compliance.jsonl  ← same domain names, IF-THEN structured
│       └── macro-rates-us.jsonl
│
├── knowledge/exports/            ← YOUR EXPORTS (ready to use)
│   ├── prompts/                  ← paste into Claude/Cursor/Copilot
│   │   └── aml-compliance-claude-project-2026-03-30.md
│   ├── harness/                  ← import in Python code
│   │   └── aml_compliance_2026_03_30.json
│   ├── training/                 ← fine-tuning JSONL
│   │   ├── aml-compliance-train-alpaca.jsonl
│   │   └── aml-compliance-val-alpaca.jsonl
│   └── aml-compliance.xlsx       ← Excel with quality color-coding
│
├── predictions/
│   └── cards/                    ← YOUR PREDICTION CARDS
│       ├── 53114f81.json         ← structured data
│       └── 53114f81.html         ← open in browser, send to anyone
│
├── consistency/                  ← VALIDATION RESULTS
│   └── aml-compliance-results.json
│
├── reports/                      ← OPERATIONALIZE OUTPUT
│   └── aml-compliance-2026-03-30.json  ← which rules triggered
│
└── discovery/                    ← DOMAIN MAPS
    └── aml-compliance-seeds.json
```

**Key points:**
- Every domain gets its own file — `aml-compliance.jsonl`, `marine-cargo-uk.jsonl`. No mixing.
- All files are plain text (JSONL, JSON, markdown, CSV). Open them in any editor, `cat` them, `grep` them, pipe them. No database, no binary formats.
- Session state (internal bookkeeping) is tucked away in `sessions/` subdirectories — you never need to look at it.
- The `data/` directory is portable — copy it to another machine and everything works.
- Run `bdistill dashboard` (if MCP server installed) to browse visually at localhost:8741.

**To check where your data is:**
```bash
python -c "from bdistill import DATA_ROOT; print(DATA_ROOT)"
```

Or just look for a `data/` folder next to where you launched VS Code.

## License

MIT
