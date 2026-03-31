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

## Detecting complex topic structures

Not every query is a single domain. Three patterns to detect:

### Pattern 1: Multi-variable system

The user wants rules about **multiple interacting variables** within one domain — e.g., "crop stress from water balance, temperature, precipitation, and soil moisture for soybeans."

**Signal words:** "variables", "factors", "combined effect", "interaction between", listing 3+ measurable quantities.

These are NOT separate domains — they interact. Extract into ONE domain but structure the seed terms to cover:
- **Individual variable thresholds**: "at what temperature does stress begin?"
- **Variable interactions**: "what happens when BOTH high temp AND low moisture?"
- **Compound thresholds**: "at what combination does yield loss exceed 20%?"
- **Temporal windows**: "during which growth stage does each variable matter most?"

**Output format for multi-variable systems:**

```yaml
type: multi_variable
domain: string                    # One domain for the whole system
variables:
  - name: string                  # e.g., "temperature"
    seed_terms: string[]          # Thresholds for this variable alone
  - name: string                  # e.g., "soil_moisture"
    seed_terms: string[]
interaction_terms: string[]       # Compound/interaction thresholds
temporal_terms: string[]          # Growth stage sensitivity windows
```

**Example:** "I need rules about crop stress weather variables — water balance, temperature, precipitation, soil moisture for soybeans in Mato Grosso"

```json
{
  "type": "multi_variable",
  "domain": "soy-mt-crop-stress",
  "variables": [
    {
      "name": "temperature",
      "seed_terms": [
        "Mato Grosso soybean heat stress threshold Tmax during R1-R5",
        "night temperature below which MT soybean recovery occurs",
        "accumulated heat units (GDD) above 30C during grain fill yield impact"
      ]
    },
    {
      "name": "precipitation",
      "seed_terms": [
        "cumulative precipitation below which MT soybean flowering yield drops",
        "consecutive dry days threshold during R1-R3 for rainfed soy MT",
        "excess precipitation threshold causing waterlogging in cerrado latossolo"
      ]
    },
    {
      "name": "soil_moisture",
      "seed_terms": [
        "available water capacity below which soybean stress begins in cerrado",
        "soil moisture recovery rate after drought event cerrado soil type",
        "permanent wilting point vs temporary stress threshold for soy MT"
      ]
    },
    {
      "name": "water_balance",
      "seed_terms": [
        "evapotranspiration vs precipitation ratio threshold for yield impact",
        "crop water demand by growth stage soybean tropical cerrado",
        "VPD vapor pressure deficit above which stomatal closure reduces yield"
      ]
    }
  ],
  "interaction_terms": [
    "compound effect high temperature AND low soil moisture on soy yield MT",
    "multiplicative vs additive yield loss when drought heat overlap simultaneously",
    "sequential stress: does prior water stress increase heat vulnerability?",
    "does irrigation fully offset heat stress or only partially?"
  ],
  "temporal_terms": [
    "which growth stage R1-R6 is most sensitive to each weather variable",
    "critical window duration: how many days of stress before irreversible damage",
    "planting date interaction: does late planting shift the stress sensitivity windows"
  ],
  "recommended_workflow": [
    "1. Extract individual variable thresholds first (4 sessions, same domain)",
    "2. Extract interaction rules (compound thresholds)",
    "3. Extract temporal windows (growth stage sensitivity)",
    "4. Validate ALL entries — compound thresholds are the most likely to be hallucinated",
    "5. Export as JSON for operationalize against Open-Meteo weather data"
  ]
}
```

**Key:** All extractions use the SAME domain name (`soy-mt-crop-stress`) so everything compounds into one KB. The agent runs `bdistill-extract` multiple times with different custom_terms — once per variable group, once for interactions, once for temporal windows.

### Pattern 2: Causal chain (cross-domain)

When the user's query spans multiple domains connected by cause-and-effect, **do not flatten into one domain**. Instead, decompose into a **chain of linked extraction sessions**, each with its own domain name.

**Signal words for causal chains:** "ripple effects", "consequences of", "impact on", "leads to", "as a result of", "downstream effects", "transmission from X to Y".

**Output format for causal chains:**

```yaml
type: causal_chain
domains:
  - domain: string
    seed_terms: string[]
    mode: rules | knowledge
    extracts_from: null | string  # Which upstream domain feeds this one
    linkage_terms: string[]       # Terms that describe the connection to the next domain
```

The agent runs extraction sessions in **chain order** — upstream first, downstream second — because downstream rules may reference upstream thresholds ("IF oil price > $X" is an upstream threshold that feeds the downstream rule "IF ammonia cost > $Y THEN reduce application rate").

## Edge cases

- User description too vague ("I work in finance"): Ask for specifics — "What decisions do you make day to day? What numbers matter?"
- Domain too broad: Split into sub-domains. "Insurance" → "marine-cargo", "cyber-risk", "professional-liability"
- User picks all topics: Suggest starting with thresholds + mechanisms (highest extraction value), defer precedents to second session
- Choosing recommended_mode: If the user's work involves decisions, monitoring, or automation → recommend "rules". If they need reference material, explanations, or training data → recommend "knowledge". If they want forecasts → recommend "predict". When unclear, ask: "Are you building a decision system, or a reference knowledge base?"
- **Multi-domain queries**: If the user's description crosses 2+ domains connected by causation, use the causal chain output format (see above). Do NOT force everything into one domain.

## Example 1: Single domain

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

## Example 2: Multi-domain causal chain

**Input:** "I need decision rules for crude oil price and ripple effects on nitrogen fertilizers as consequence of geopolitical tensions in the Hormuz strait"

This crosses 3 domains connected by causation:
```
Hormuz geopolitics → oil/gas price → nitrogen fertilizer cost → downstream ag impact
```

**Output:**
```json
{
  "type": "causal_chain",
  "summary": "Geopolitical tension in Hormuz strait → crude oil spike → natural gas spike → ammonia/urea production cost surge → fertilizer price impact → farmer application rate changes",
  "domains": [
    {
      "domain": "energy-geopolitics-hormuz",
      "order": 1,
      "seed_terms": [
        "Hormuz strait closure probability triggers and historical precedents",
        "Iran-Saudi tension escalation ladder and oil supply disruption thresholds",
        "Hormuz chokepoint: volume of oil transit (21M bbl/day) and bypass capacity",
        "US Fifth Fleet response timelines and deterrence thresholds",
        "insurance war-risk premium triggers for tanker transit Hormuz",
        "oil price spike magnitude by disruption scenario: harassment vs blockade vs closure"
      ],
      "mode": "rules",
      "extracts_from": null,
      "linkage_to_next": "Oil price thresholds from disruption scenarios feed into energy-fertilizer linkage"
    },
    {
      "domain": "energy-fertilizer-linkage",
      "order": 2,
      "seed_terms": [
        "crude oil to natural gas price transmission: Henry Hub, TTF, JKM benchmarks",
        "natural gas as feedstock for ammonia: cost share 70-90% of production cost",
        "ammonia production cost curve by gas price: $2/MMBtu to $15/MMBtu scenarios",
        "urea price as function of ammonia cost plus conversion margin",
        "UAN-28 and UAN-32 pricing relative to urea and ammonia",
        "nitrogen fertilizer supply elasticity: can production shift to non-gas regions?",
        "China and Russia export restrictions on urea and ammonium nitrate triggers"
      ],
      "mode": "rules",
      "extracts_from": "energy-geopolitics-hormuz",
      "linkage_to_next": "Fertilizer price thresholds feed into application rate decisions"
    },
    {
      "domain": "fertilizer-application-economics",
      "order": 3,
      "seed_terms": [
        "nitrogen fertilizer cost as share of total crop production cost by crop",
        "farmer application rate response to urea price: at what $/ton do farmers cut rates?",
        "yield response curve to nitrogen application: diminishing returns thresholds",
        "optimal vs economic nitrogen rate: when does marginal cost exceed marginal yield value?",
        "regional differences: US corn belt vs Brazil cerrado vs EU wheat nitrogen economics",
        "substitution options: precision application, biological nitrogen, cover crops, timing shifts"
      ],
      "mode": "rules",
      "extracts_from": "energy-fertilizer-linkage",
      "linkage_to_next": null
    }
  ],
  "recommended_workflow": [
    "1. Extract energy-geopolitics-hormuz rules first (upstream triggers)",
    "2. Extract energy-fertilizer-linkage rules (transmission mechanism)",
    "3. Extract fertilizer-application-economics rules (downstream impact)",
    "4. Validate all 3 domains with bdistill-validate",
    "5. Export all 3 as JSON, load together in bdistill-operationalize",
    "6. Monitor: oil price from Yahoo Finance + gas from FRED + urea from market data",
    "7. Predict: 'Will urea exceed $600/t if Hormuz tensions escalate?' with bdistill-predict grounded across all 3 KBs"
  ]
}
```

## Composes with

- **bdistill-extract**: Pass `seed_terms` as `custom_terms` and `domain` as the domain name. For causal chains, run extractions in chain order (upstream first).
- **bdistill-predict**: Pass `domain` for grounded predictions. For causal chains, the predict skill recalls from all linked domains.
- **bdistill-operationalize**: Load rules from multiple domains simultaneously to monitor the full causal chain.
