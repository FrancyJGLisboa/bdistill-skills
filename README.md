# bdistill-skills

**Everyone is building AI agents. But generic agents make generic decisions.**

Your agents need niche domain knowledge to be actually useful — the thresholds, rules, and edge cases that separate a junior from a senior in your field. That knowledge exists inside LLMs, but it's trapped in ephemeral chat sessions. bdistill-skills extracts it into structured, validated knowledge bases that make your agents smart on your niche.

7 composable protocols that distill real intelligence from the AI models you already use — decision rules with numeric thresholds, validated Q&A pairs, structured predictions with evidence. The distilled knowledge persists as a searchable, quality-scored KB that your AI agents consume downstream: specialized assistants, monitoring systems, recommendation engines, fine-tuned local models, or just a Claude Project that finally gives consistent domain answers.

Works with Claude Code, VS Code Copilot, Cursor, Codex CLI, Windsurf, Cline, and 30+ other agents. No API key. No MCP server. No dependencies.

## Quickstart (30 seconds)

```bash
# 1. Install (pick your tool)
npx skills add FrancyJGLisboa/bdistill-skills          # auto-detects your AI tools
# OR: git clone https://github.com/FrancyJGLisboa/bdistill-skills.git   # manual
```

```
# 2. Extract — tell your AI agent:
"Extract rules about [your niche topic]"

# The agent follows the extraction protocol automatically:
# → generates targeted questions → answers them → challenges its own claims
# → scores quality → writes validated rules to data/rules/base/your-domain.jsonl
```

```
# 3. Validate — immediately after extracting:
"Validate the KB"

# The agent re-asks every numeric claim 5 different ways + checks structural stability.
# Numbers that vary → flagged as hallucinated. Conditions that appear/disappear → flagged as unstable.
# Only stable entries survive. This is what separates a trusted KB from a chat log.
```

```
# 4. Use it:
"Export as system prompt for Claude Project"     # → paste into your AI tool, done
"Predict: will X happen?"                        # → structured forecast grounded in your KB
"Check rules against live data"                  # → which rules are triggered right now?
```

**Complex topics work too.** You don't need to pre-structure your request:

```
"Extract rules about crop stress — water balance, temperature, precipitation,
 soil moisture for soybeans in Mato Grosso"
# → Agent detects multi-variable system, structures extraction by variable,
#   then extracts compound interaction thresholds, then temporal windows.
#   All in one KB, validated together.

"Extract rules about price movements from Hormuz strait geopolitical tensions
 through to nitrogen fertilizer costs"
# → Agent detects causal chain, decomposes into linked domains:
#   energy-geopolitics → energy-fertilizer-linkage → fertilizer-economics.
#   Extracts upstream first, downstream second.
```

**Extract → Validate is the minimum viable workflow.** Don't skip validation — an unvalidated KB is just organized hallucinations. The scripts in `scripts/` add more rigor (adversarial depth levels, cross-KB contradiction detection, checkpointing) when you're ready.

## What you can extract

LLMs have absorbed vast structured knowledge from academic papers, regulatory filings, technical manuals, and professional literature. Most of it is inaccessible through normal chat — you get vague summaries instead of specific thresholds. bdistill-skills forces it out as validated, structured rules anyone can use downstream.

**Any topic where decisions depend on thresholds, conditions, or expert judgment is a target.**

| What you ask | What you get | Downstream use |
|---|---|---|
| "Oil price ripple effects on nitrogen fertilizers from Hormuz strait tensions" | Causal chain: chokepoint disruption scenarios → crude/gas price thresholds → ammonia production cost curves → urea/UAN pricing rules → farmer application rate responses | Monitoring agent watches oil + gas + urea prices, alerts when chain triggers |
| "Crop yield response to nitrogen fertilizer by soil classification" | IF-THEN rules: response curves by soil type (sandy loam vs clay vs cerrado latossolo), diminishing return thresholds, economic optimum rates per crop-soil combination | Precision ag recommendation system: given soil test + fertilizer price → recommend N rate |
| "Minimum soil requirements determining crop suitability" | Threshold rules per crop: pH range, drainage class, depth to hardpan, organic matter %, CEC, slope, frost risk — with exceptions and marginal conditions | Land evaluation tool: given soil survey data → which crops are viable? |
| "ANVISA drug approval pathway timelines and rejection triggers" | Stage-gate rules: pre-clinical requirements, Phase I/II/III criteria, dossier completeness thresholds, clock-stop triggers, post-market surveillance conditions | Regulatory tracker: monitors submission status, predicts approval timeline |
| "Marine cargo insurance classification by vessel and route" | Classification rules: hull age limits, flag state risk tiers, war-risk zone definitions, cargo hazard class interactions, seasonal weather exclusions | Underwriting engine: given vessel + route + cargo → risk class + premium adjustment |
| "Basel III capital adequacy impact on lending by asset class" | Transmission rules: RWA weights per asset class, capital buffer triggers, countercyclical surcharges, GSIB buffers, leverage ratio thresholds | Credit risk model: given bank capital position → lending capacity by sector |
| "Clinical trial eligibility criteria for Type 2 diabetes drugs" | Inclusion/exclusion rules: HbA1c range, eGFR thresholds, prior medication washout, cardiovascular risk exclusions, age/BMI boundaries | Patient screening system: given patient profile → eligible for which trials? |
| "Real estate rental comp analysis rules by market segment" | Valuation rules: comparable selection criteria (distance, age, size, amenity class), adjustment factors per differentiator, cap rate thresholds by submarket | Pricing tool: given property profile → recommended rent range with cited comps |
| "Cybersecurity incident severity classification and response timelines" | Triage rules: CVSS score → severity tier → response SLA → escalation path → notification obligations (GDPR 72h, SEC 4 days, sector-specific) | Incident response automation: given alert data → classify, route, set clock |
| "Podcast audience growth signals and monetization thresholds" | Milestone rules: download thresholds for sponsorship tiers, engagement rate benchmarks, niche vs broad audience economics, platform-specific monetization gates | Creator analytics dashboard: given show metrics → "ready for mid-roll ads" |

**The protocol is always the same:** describe what you need → agent structures the extraction → adversarial challenges force specificity → validation filters hallucinations → you get a KB file of structured rules your agents can consume.

The topics above span agriculture, pharma, insurance, banking, clinical trials, real estate, cybersecurity, and media. They all work because the protocol doesn't care about the domain — it cares about extracting **thresholds, conditions, and decision logic** from whatever the LLM knows.

## How it works

A knowledge worker extracts their niche expertise into a KB. An AI agent cross-checks that KB against current data. The result is a recommendation system built from real domain intelligence — no coding required.

```
YOU (the expert)                    YOUR AI AGENT (the operator)

"Extract rules about marine         Generates 40 targeted questions
 cargo insurance classification"    Answers each with specific thresholds
         │                          Challenges its own claims
         │                          Scores quality, flags hallucinations
         ▼
  ┌─────────────────┐
  │  KNOWLEDGE BASE  │  ◄── 35 validated IF-THEN rules
  │  marine-cargo.jsonl │     with confidence scores
  └────────┬────────┘
           │
     export as JSON
           │
           ▼
  ┌─────────────────┐    ┌──────────────────┐
  │  AGENT reads     │◄──│  LIVE DATA        │
  │  your rules      │    │  (API, CSV, feed) │
  └────────┬────────┘    └──────────────────┘
           │
     checks each rule
     against current data
           │
           ▼
  ┌─────────────────────────────────┐
  │  RECOMMENDATION                  │
  │                                  │
  │  "3 of 35 rules triggered:      │
  │   - Hull age 23y > 20y limit     │
  │   - Route passes piracy zone     │
  │   - Cargo value exceeds $2M      │
  │                                  │
  │   Recommendation: REFER to       │
  │   senior underwriter.            │
  │   Confidence: 0.89 (verified)"   │
  └─────────────────────────────────┘
```

**The knowledge worker provides the expertise. The agent provides the automation. The KB is the bridge.**

**Two extraction modes — the agent picks the right one based on what you say:**

| You say | Agent uses | KB contains | Downstream use |
|---------|-----------|-------------|----------------|
| "extract **rules** about AML thresholds" | `mode: rules` | IF-THEN with numeric thresholds | Monitoring, automation, recommendation systems |
| "extract **knowledge** about cardiac treatment" | `mode: knowledge` | Q&A pairs with explanations | Reference KB, Claude Project prompt, fine-tuning |

Signal words like "thresholds", "triggers", "criteria", "at what point" → rules mode. Words like "explain", "how does", "knowledge about" → knowledge mode. When ambiguous, the agent asks.

This works for any domain: compliance analysts extracting AML thresholds, traders extracting basis risk rules, clinical researchers extracting trial criteria, insurance underwriters extracting classification rules. You extract once, validate, and your agents use it forever — improving the rules when reality proves them wrong.

## A factory for AI-driven recommendation systems

bdistill-skills is a repeatable pipeline. Pick a domain, run the assembly line, get a working recommendation system backed by validated knowledge. Then pick the next domain and do it again.

```
DOMAIN 1: AML Compliance              DOMAIN 2: Marine Insurance           DOMAIN 3: Your niche
─────────────────────────              ──────────────────────────           ─────────────────────

discover → "I audit banks"             discover → "I underwrite cargo"      discover → "I do X"
    │                                      │                                    │
extract → 50 AML rules                extract → 40 classification rules    extract → your rules
    │                                      │                                    │
validate → 43 stable, 7 dropped        validate → 35 stable, 5 dropped     validate → keep stable
    │                                      │                                    │
export → aml-compliance.json           export → marine-cargo.json           export → your-domain.json
    │                                      │                                    │
operationalize                         operationalize                       operationalize
  + transaction feed                     + claims data                        + your data source
    │                                      │                                    │
    ▼                                      ▼                                    ▼
"Flag account #4821 for EDD —          "Refer to senior underwriter —       Your agent recommends
 cumulative R$127K > R$100K limit,      hull age 23y exceeds 20y limit,      based on your rules
 confidence 0.91"                       piracy zone transit, conf 0.89"      vs current data
```

**Same pipeline, different domain, different data source, different recommendations. The factory pattern is:**

1. **Pick a domain** — any niche where decisions depend on thresholds, rules, or expert judgment
2. **Extract a KB** — 30-100 validated rules with confidence scores and consistency checks
3. **Wire it to data** — connect the exported rules to whatever data your agents already access (APIs, CSVs, databases, web search)
4. **Agent recommends** — your agent loads the KB, checks each rule against current data, and recommends with citations

**What you can build with this pattern:**

| Domain | KB contains | Data source | Agent recommends |
|--------|------------|-------------|------------------|
| AML compliance | Transaction monitoring thresholds | Transaction feed | Flag accounts, trigger EDD reviews |
| Insurance underwriting | Risk classification rules | Claims + vessel data | Accept, refer, or decline with cited criteria |
| Commodities trading | Basis risk, crush margin thresholds | Market prices (Yahoo Finance) | Trade signals with confidence |
| Clinical trials | Eligibility criteria, adverse event rules | Patient data | Screen patients, flag safety events |
| Pharma regulatory | ANVISA submission requirements | Submission tracker | Compliance gaps, missing documents |
| Real estate operations | Rent roll standards, comp analysis rules | Property data | Pricing recommendations, anomaly flags |
| Crop monitoring | Weather-yield thresholds by region | Weather API (Open-Meteo) | Yield risk alerts with impact estimates |
| Macro research | Rate decision rules, yield curve signals | FRED economic data | Regime change alerts, positioning signals |

**Each row is one run of the factory.** The compliance officer builds row 1. The underwriter builds row 2. The trader builds row 3. They all use the same 7 skills in the same sequence — only the domain knowledge and data source change.

**The KB is the moat.** Anyone can build an agent. Not everyone has 50 validated, adversarially tested, consistency-probed decision rules for Brazilian AML compliance. That's what bdistill-skills produces — and it compounds every time you re-extract on the gaps.

## Install

Pick your AI tool. Follow the steps. Takes 2 minutes.

### VS Code + GitHub Copilot (Windows, Mac, or Linux)

```bash
# 1. Open a terminal in your project folder

# 2. Clone bdistill-skills into your project
git clone https://github.com/FrancyJGLisboa/bdistill-skills.git .bdistill-skills

# 3. Copy the Copilot instructions file to where Copilot reads it
mkdir -p .github
cp .bdistill-skills/.github/copilot-instructions.md .github/copilot-instructions.md

# 4. That's it. Open VS Code, open Copilot Chat, and say:
#    "Extract rules about [your topic]"
```

**Windows PowerShell alternative for step 2-3:**
```powershell
git clone https://github.com/FrancyJGLisboa/bdistill-skills.git .bdistill-skills
New-Item -ItemType Directory -Force -Path .github
Copy-Item .bdistill-skills\.github\copilot-instructions.md .github\copilot-instructions.md
```

**To also use the scripts** (adversarial depth, checkpointing, validation engine):
```bash
# Make sure Python 3.10+ is installed, then:
python .bdistill-skills/bdistill-extract/scripts/extract_engine.py --help
# Copilot in agent mode can run these scripts directly from the terminal
```

### Claude Code (Mac, Linux, or WSL on Windows)

```bash
# 1. Open a terminal in your project folder

# 2. Clone bdistill-skills — Claude Code auto-discovers skills/ directories
git clone https://github.com/FrancyJGLisboa/bdistill-skills.git skills

# 3. That's it. Start Claude Code and say:
#    "Extract rules about [your topic]"
```

Claude Code reads SKILL.md files from `skills/` automatically. All 8 skills are immediately available as invocable skills.

### Cursor (Windows, Mac, or Linux)

```bash
# 1. Open a terminal in your project folder

# 2. Clone bdistill-skills
git clone https://github.com/FrancyJGLisboa/bdistill-skills.git .bdistill-skills

# 3. Copy the Cursor rules file
mkdir -p .cursor/rules
cp .bdistill-skills/.cursor/rules/bdistill.mdc .cursor/rules/bdistill.mdc

# 4. Open Cursor and say:
#    "Extract rules about [your topic]"
```

### Codex CLI / GitHub Copilot CLI

```bash
# 1. Clone bdistill-skills
git clone https://github.com/FrancyJGLisboa/bdistill-skills.git .bdistill-skills

# 2. Copy AGENTS.md to your project root
cp .bdistill-skills/AGENTS.md AGENTS.md

# 3. Run Codex and say:
#    "Extract rules about [your topic]"
```

### npx skills (auto-detect, if you have Node.js)

```bash
# Installs to all detected AI tools at once
npx skills add FrancyJGLisboa/bdistill-skills

# Or just one skill
npx skills add FrancyJGLisboa/bdistill-skills --skill bdistill-extract
```

### Any other AI tool (ChatGPT, Windsurf, Cline, etc.)

Open `bdistill-extract/SKILL.md` from this repo and paste its content into your tool's system prompt or custom instructions. The instructions are plain markdown — they work anywhere.

### Optional: MCP server (full power)

Not required. Every skill works without it. But if you want session management, automatic quality scoring, compounding KB with deduplication, and HTML reports:

```bash
pip install bdistill        # or: pipx install bdistill
bdistill setup              # auto-detects and configures your AI tools
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
| **bdistill-abstract** | Abstract rules from one domain, re-instantiate in others, find non-obvious structural correspondences | "cross-domain", "what pattern in X applies to Y", "abstract this rule" |

## How they chain

Skills are composable — each skill's output is the next skill's input.

```
bdistill-discover --> bdistill-extract --> bdistill-validate --> bdistill-export --> bdistill-operationalize
                            |                   ↑                    |
                            v                   |                    v
                      bdistill-predict     bdistill-abstract --------┘
                                          (re-instantiated rules feed back into validate)
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

## Complex workflows: multi-domain causal chains

Simple extraction handles one domain. Real-world decisions often span multiple domains connected by cause-and-effect. bdistill-skills handles this by decomposing causal chains into linked extraction sessions.

**Example: "I need decision rules for crude oil price and ripple effects on nitrogen fertilizers from Hormuz strait geopolitical tensions"**

This crosses 3 domains:
```
Hormuz geopolitics ──→ oil/gas prices ──→ nitrogen fertilizer costs ──→ farm-level impact
     (cause)            (transmission)         (downstream effect)        (decision point)
```

The agent runs `bdistill-discover`, which detects the causal chain and decomposes it:

```
Session 1: domain="energy-geopolitics-hormuz"
  Extract rules about: strait closure triggers, disruption scenarios,
  oil price spike magnitudes, tanker war-risk premium thresholds
  → 40 rules about WHEN and HOW MUCH oil spikes

Session 2: domain="energy-fertilizer-linkage"
  Extract rules about: gas-to-ammonia cost transmission, urea pricing
  as function of ammonia cost, China/Russia export restriction triggers
  → 35 rules about HOW oil price transmits to fertilizer cost

Session 3: domain="fertilizer-application-economics"
  Extract rules about: at what $/ton farmers cut nitrogen rates,
  yield response curves to reduced application, substitution options
  → 30 rules about WHAT FARMERS DO when fertilizer costs spike
```

Then chain the outputs:

```
bdistill-validate on all 3 domains → drop unstable thresholds

bdistill-export all 3 as JSON → load together in bdistill-operationalize

bdistill-operationalize with:
  rules = [energy-geopolitics-hormuz.json,
           energy-fertilizer-linkage.json,
           fertilizer-application-economics.json]
  data_sources = [yahoo-finance (oil), fred (gas), market-data (urea)]

Output: "3 of 105 rules triggered across the chain:
  [1] Oil price $94 > $90 threshold (Hormuz tension scenario B)
  [2] Henry Hub gas $6.20 pushes ammonia cost above $500/t
  [3] At urea >$580/t, corn belt farmers historically cut N rates 15-20%

  Causal chain: Hormuz tension → oil spike → gas spike → ammonia cost
  → urea above $580 → farmer N rate reduction → potential yield drag"
```

**105 validated rules across 3 domains, checked against 3 live data feeds, producing a causal chain recommendation.** The knowledge worker provided the question. The agent ran the factory.

### More causal chains that extract reliably

These work well because LLMs have deep quantitative training data on the transmission mechanisms — academic papers, central bank research, USDA reports, actuarial studies, regulatory filings. The thresholds are real, not hallucinated.

**Reliability rating:** How likely the extracted thresholds are stable (pass bdistill-validate consistency probing).

#### High reliability (well-documented transmission mechanisms, quantitative literature)

**Central bank policy → real economy**
```
Fed funds rate change → Treasury yield curve shift → corporate credit spreads widen
→ mortgage rate increase → housing demand decline → construction materials demand drop
→ lumber/copper price decline
```
Why reliable: Fed transmission mechanism is the most studied topic in economics. Thousands of papers with specific elasticities. LLMs have IMF working papers, Fed FEDS notes, BIS quarterly reviews in training data.

**El Nino/La Nina → global food prices**
```
ENSO phase shift → regional precipitation anomalies (Australia, India, Brazil, US)
→ crop yield deviations by region and crop → export supply changes
→ CBOT futures price moves → FOB price adjustments → importing country food CPI
```
Why reliable: NOAA, USDA FAS, FAO, World Bank Commodity Markets Outlook all publish quantified ENSO-crop-price relationships. LLMs have USDA ERS research reports with specific yield impact coefficients per region.

**Basel III/IV capital rules → credit availability**
```
New capital requirement announced → bank RWA calculation changes
→ capital buffer squeeze → lending standard tightening (Senior Loan Officer Survey)
→ credit spread widening → corporate borrowing cost increase
→ capex reduction for marginal borrowers → sector-specific output effects
```
Why reliable: BIS publishes quantitative impact studies. Every major bank publishes capital adequacy reports. The transmission lags and magnitudes are studied extensively.

**Drug patent cliff → healthcare costs**
```
Blockbuster drug patent expires → generic/biosimilar entry within 6-18 months
→ drug price drops 80-90% (small molecule) or 30-50% (biosimilar)
→ PBM formulary changes → insurance reimbursement rate adjustments
→ hospital pharmacy budget reallocation → physician prescribing pattern shift
```
Why reliable: FDA Orange Book data, CMS pricing data, IQVIA market reports all have specific timelines and price erosion curves. This is actuarial-grade data.

**Oil sanctions → downstream industrial costs**
```
Sanctions on oil-producing country → crude supply reduction (quantified by IEA)
→ refinery margin changes → diesel/jet fuel price spike
→ freight/logistics cost increase (fuel surcharge formulas are public)
→ manufactured goods input cost increase → PPI by sector → selective CPI pass-through
```
Why reliable: IEA Oil Market Reports, EIA Short-Term Energy Outlook, and shipping industry fuel surcharge formulas are all quantitative and public.

#### Medium reliability (mechanisms understood, some thresholds may vary)

**Cyber attack on critical infrastructure → economic disruption**
```
Ransomware hits port management system → port operations halt 3-14 days
→ vessel queue builds → container redirect to alternate ports (capacity constrained)
→ spot freight rate spike → import delay → retailer inventory drawdown
→ selective stockout → consumer substitution
```
Why medium: NIST and insurance actuarial models have scenario data, but specific thresholds (days of disruption, freight rate multipliers) vary by incident. LLMs have NotPetya/Colonial Pipeline case studies but may overgeneralize.

**Sovereign credit downgrade → capital flight**
```
Rating agency downgrades sovereign debt → bond yield spike (basis points vary by tier)
→ currency depreciation → central bank intervention (reserve drawdown)
→ import cost increase → domestic inflation → consumer purchasing power erosion
→ political pressure for fiscal response
```
Why medium: Transmission is well-studied (Reinhart & Rogoff, IMF), but the specific basis point moves and currency impacts are highly country-dependent. LLMs will give good frameworks but thresholds need per-country calibration.

**Supply chain reshoring/friendshoring → cost structure**
```
Tariff or policy shock → company evaluates reshoring vs tariff absorption
→ capex for new facility (18-36 month lead time) → labor market tightening in target region
→ unit cost increase 15-30% (BCG/McKinsey estimates) → pricing decision (absorb vs pass-through)
→ competitor response → market share rebalancing
```
Why medium: McKinsey, BCG, Kearney publish reshoring cost studies. LLMs have these but the specific cost premiums are rapidly evolving post-2023.

#### Lower reliability (use for scenario framing, validate thresholds externally)

**AI regulation → tech sector → broader market**
```
EU AI Act enforcement begins → compliance cost for covered AI systems
→ smaller AI companies can't afford compliance → consolidation/exits
→ reduced AI startup investment → tech sector valuation compression
→ index-level impact (tech weight in S&P 500)
```
Why lower: This chain is plausible but the EU AI Act enforcement is too recent (2024-2025) for LLMs to have reliable quantitative impact data. Thresholds will be speculative. Use for scenario framing, then ground with web search via bdistill-predict --grounded.

**Climate transition → stranded assets → financial stability**
```
Carbon pricing reaches $X/ton → coal/oil assets become uneconomic
→ asset writedowns on bank balance sheets → capital adequacy pressure
→ credit tightening in carbon-intensive sectors → economic restructuring
```
Why lower: The mechanism is well-described (Mark Carney speeches, NGFS scenarios) but the specific carbon price threshold where assets strand varies wildly across models ($50-$250/ton depending on assumptions). LLMs will give a range, not a threshold. Useful for scenario analysis, not for deterministic rules.

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

---

### "How does it force the LLM to distill specific intelligence into a KB? What makes this different from standard prompting? Are these just markdown instructions?"

Yes, they are markdown instructions. And that's the point — but what the instructions *encode* is a **multi-pass extraction protocol** that produces fundamentally different output than a single prompt ever could. Here's what's actually happening under the hood:

**Standard prompting:**
```
You: "What are the AML thresholds for Brazilian fintechs?"
AI:  "Generally, transactions above R$10,000 should be monitored... [vague, generic, no structure]"
```

One question, one answer, gone forever. No validation. No structure. No persistence. Ask again tomorrow, get a slightly different answer.

**What bdistill-extract does with the same topic:**

```
Step 1 — SEED: Your custom terms ("BCB Circular 3978", "SAR filing thresholds")
  are decomposed into 30-50 targeted questions, each designed to extract a
  different facet: thresholds, mechanisms, exceptions, edge cases, precedents.
  Not one question — thirty.

Step 2 — EXTRACT: The AI answers each question in detail (100+ words, forced
  to include specific numbers, named regulations, concrete conditions).
  The instructions explicitly say: "Use concrete numeric thresholds:
  'IF transaction > R$50,000' not 'IF transaction is large'."

Step 3 — CHALLENGE: Each answer is adversarially probed. The AI is told to
  attack its own claims:
  - "What evidence supports that R$50,000 threshold?"
  - "Does this apply to crypto transactions?"
  - "What about structured transactions just below the limit?"
  The AI corrects itself, adds exceptions, cites specific regulations.
  Entries that survive challenges get higher confidence scores.

Step 4 — SCORE: Each entry is quality-scored (0.0-1.0) based on:
  - Specificity (named entities, exact numbers vs vague language)
  - Evidence cited (regulation numbers, data sources)
  - Precision (IF-THEN with thresholds vs prose descriptions)
  Entries below 0.4 are dropped. Entries above 0.8 are marked "verified."

Step 5 — PERSIST: Entries are written as structured JSONL — one record per
  rule with typed fields (conditions, action, confidence, domain, tags).
  Not a chat log. A queryable, filterable, exportable dataset.

Step 6 — DEDUPLICATE: Run it again next week with different terms. Same
  domain file. If a similar question already exists, the higher-quality
  version is kept. The KB compounds, not duplicates.

Step 7 — VALIDATE: bdistill-validate re-asks each numeric claim 5 times
  with different phrasings. If the AI says "R$50,000" every time → stable,
  real knowledge. If it says R$50K, R$80K, R$100K, R$75K, R$100K →
  unstable, probably hallucinated. Flag or drop.
```

**That's 7 steps where standard prompting has 1.** The difference isn't the markdown — it's the protocol the markdown encodes.

**What you get at the end:**

| Standard prompting | bdistill extraction |
|---|---|
| A chat response that disappears | A persistent JSONL file on disk |
| Vague: "transactions should be monitored" | Specific: `IF single_transaction > R$50,000 THEN trigger EDD` |
| One answer, no validation | 30+ answers, adversarially challenged |
| No quality signal | Confidence score 0.0-1.0, verified/solid/approximate tiers |
| No consistency check | Stability score: real knowledge vs hallucinated |
| Ask again, get different answer | Same file, deduplicates, compounds across sessions |
| Can't export | Export as prompt, JSON, Python module, Excel, training JSONL |
| Can't operationalize | Feed to monitoring system, check against live data |

**"Are these just markdown files?"**

Yes. And a recipe is just text on paper. The value isn't the paper — it's that the recipe encodes a specific sequence of actions that produces a predictable result. These markdown files encode extraction protocols that turn a general-purpose LLM into a structured knowledge extraction pipeline. The LLM follows the protocol because the instructions are precise enough to constrain its behavior: force specificity, challenge claims, score quality, persist output, deduplicate, validate.

A single prompt says "tell me about AML." These skills say "generate 30 targeted questions from these seed terms, answer each with specific thresholds, challenge every claim, score quality, write structured output, validate consistency, export in 6 formats." That's the difference.

---

### "Do I need to be careful to use the same KB name across sessions so extractions compound into one validated KB?"

**Yes — the domain name is the key.** All sessions with the same domain name merge into the same file. Different terms, different days, different sessions — as long as the domain name matches, everything compounds.

```
Session 1:  domain="aml-compliance-brazil", terms=["BCB 3978", "SAR thresholds"]
            → 30 entries in aml-compliance-brazil.jsonl

Session 2:  domain="aml-compliance-brazil", terms=["PEP screening", "beneficial ownership"]
            → 25 MORE entries merged into the SAME file (now 55, deduplicated)

Session 3:  domain="aml-compliance-brazil", terms=["crypto AML", "travel rule"]
            → 20 MORE entries merged (now 75)
```

**The footgun to avoid:** using slightly different names for the same domain.

```
BAD:   "aml-compliance" → "aml-brazil" → "compliance-aml-brazil"  (3 separate files!)
GOOD:  "aml-compliance-brazil" → "aml-compliance-brazil" → "aml-compliance-brazil"  (1 compounding file)
```

Pick your domain name once, write it down, reuse it. The agent is instructed to check for existing KBs before creating a new one — if you already have `aml-compliance-brazil.jsonl`, it will ask "Should I add to your existing KB?" instead of creating a new file.

Deduplication is automatic: if two sessions produce answers to the same question, the higher-quality version is kept.

---

### "If extraction is in-session with one model, what about other LLMs? How do extractions from different models route to the same KB?"

**The domain name is the merge key, not the model.** Extract from Claude on Monday, GPT on Tuesday, Llama locally on Wednesday — as long as you use the same domain name, all entries compound into one KB file.

```
Claude session:  domain="aml-compliance-brazil" → 30 entries (source_model: claude-opus-4-6)
GPT session:     domain="aml-compliance-brazil" → 25 entries merged into same file (source_model: gpt-4o)
Llama session:   domain="aml-compliance-brazil" → 20 entries merged (source_model: llama-3.1-70b)
Result: 1 file, 75 entries, 3 models
```

Every entry carries a `source_model` field, so you always know which model produced it. Deduplication keeps the higher-quality version when two models answer the same question differently.

**This is actually a feature, not a limitation.** Multi-model extraction gives you:
- **Cross-validation**: If Claude and GPT agree on a threshold, it's more likely real
- **Better coverage**: Different models have different training data strengths
- **Stronger consistency probing**: Run `bdistill-validate` on a multi-model KB — entries where models disagree on the number get flagged as unstable, which is a genuine signal worth investigating

---

### "How does adversarial validation work? Is the model just checking its own homework?"

Adversarial validation is the step that separates bdistill extraction from standard prompting. After every answer, the model is forced to attack its own claims through 3 structured challenges before the entry earns a quality score:

```
Question: "At what transaction threshold does BCB require enhanced due diligence?"

First-pass answer: "Transactions above R$50,000 require EDD."
  → vague, no citation, no exceptions

Challenge 1 — EVIDENCE:
  "What specific regulation states R$50,000? Cite the article number."
  → Model adds: "BCB Circular 3978, Art. 12, §2"

Challenge 2 — EDGE CASE:
  "Does this apply to crypto transactions? What about cumulative thresholds?"
  → Model adds: "Also applies to cumulative R$100,000 over 30 days.
     Crypto transactions follow the same thresholds per BCB Normative 2024."

Challenge 3 — CONTRADICTION CHECK:
  "Earlier you mentioned R$10,000 for wire transfers. How does that relate?"
  → Model clarifies: "R$10,000 is the reporting threshold (COAF),
     R$50,000 is the EDD trigger. Different obligations."

Final entry (what gets written to the KB):
  "IF single_transaction > R$50,000 OR cumulative_30d > R$100,000
   THEN trigger EDD per BCB Circular 3978 Art. 12 §2.
   Note: R$10,000 is the separate COAF reporting threshold.
   Applies equally to fiat and crypto (BCB Normative 2024)."
  confidence: 0.91, tier: verified, tags: [self-corrected, evidence-cited]
```

The first-pass answer scored ~0.5 (vague, no citation). After 3 challenges it's 0.91 (specific regulation, exceptions covered, related thresholds clarified). The `self-corrected` tag means the model improved its own answer under pressure — which is actually a quality signal.

**Is the model just checking its own homework?** Partially — yes, a model challenging itself is weaker than an external challenge. That's why bdistill also offers:
- **`bdistill-validate`** (consistency probing): re-asks the same claim 5 times with different phrasings to check if the number is real or hallucinated — a different kind of validation
- **Cross-model adversarial**: extract with Model A, challenge with Model B. Model B has no loyalty to Model A's claims
- **Human review**: export as Excel or checklist, let a domain expert verify the entries that matter most

Three layers: adversarial self-challenge (during extraction) → consistency probing (after extraction) → human spot-check (before deployment). Each catches different failure modes.

---

### Known limitations

**Standalone mode requires file I/O.** Skills that write JSONL/JSON to disk (extract, validate, export, operationalize) need an agent that can create files. Claude Code, Cursor, Codex CLI, VS Code Copilot (agent mode), Windsurf, and Cline all support this. Claude.ai (web chat), ChatGPT (without code interpreter), and mobile-only agents do not — for those platforms, install the bdistill MCP server (`pipx install bdistill`) which handles all file operations server-side.

**Consistency probe is weaker in standalone mode.** The validate skill re-asks the same claim 5 times. With MCP, each probe is isolated (separate context). In standalone mode, all 5 happen in the same conversation — the model can see its previous answers and will appear more consistent than it really is. Mitigation: use sub-agent calls per rephrase if your platform supports it, or use MCP mode for validation.

**Quality scores are model-relative.** A confidence of 0.85 from Claude Opus is not the same as 0.85 from GPT-4o-mini. Don't mix entries from different models in the same KB unless you re-validate with `bdistill-validate`.

**Condition-to-data mapping requires agent reasoning.** When operationalizing rules against live data, the agent must map natural language conditions ("precip < 50mm during flowering") to API response fields (`precipitation_sum`). This mapping is imperfect. The skill instructs agents to skip unmappable rules rather than guess — check the `skipped` array in the decision report.

## License

MIT
