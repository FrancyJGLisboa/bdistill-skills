---
name: bdistill-abstract
description: Extract structural rules from one domain, abstract away domain-specific vocabulary to get bare skeletons, then re-instantiate in other domains to discover non-obvious cross-domain correspondences. Filters for re-instantiations that are novel (unlikely in published literature) AND valid (survive adversarial challenge). Triggers on "abstract rules", "cross-domain", "structural analogy", "what pattern in X applies to Y", "transfer rules between domains". Outputs validated cross-domain rule correspondences.
license: MIT
metadata:
  author: bdistill
  version: "1.0"
  suite: bdistill
---

# Structural Abstraction and Cross-Domain Re-instantiation

Take a rule that works in one domain. Strip the domain-specific words. Get the bare structural skeleton. Re-instantiate that skeleton in other domains. Filter for correspondences that are non-obvious but valid.

This is how you discover that cost-of-carry arbitrage in commodities and enzyme saturation kinetics in biochemistry and bandwidth throttling in networking are the same structural pattern — and that knowing one deeply gives you predictive power in the others.

## When to use

- You have validated rules in one domain (from bdistill-extract) and want to find structural equivalents in other domains
- You're looking for non-obvious cross-domain insights that don't appear in published literature
- You want to transfer decision rules from a domain you know deeply to one you're entering
- You suspect two domains share structural patterns but can't articulate why
- You want to stress-test a rule by seeing if its abstract form holds across unrelated contexts

## Input contract

```yaml
required:
  seed_rule: string          # A concrete domain-specific rule (from your KB or stated directly)
  source_domain: string      # Where the rule comes from
  target_domains: string[]   # Domains to re-instantiate into (the more unrelated, the better)
optional:
  kb_path: string            # Path to existing KB — extract seed rules automatically
  num_seeds: int             # How many rules to abstract from the KB (default: 10, top by confidence)
  novelty_threshold: float   # 0.0-1.0, how unlikely in published literature (default: 0.6)
  min_validity: float        # 0.0-1.0, minimum adversarial survival score (default: 0.7)
output:
  correspondences: array     # Each: {seed_rule, skeleton, target_domain, re_instantiation, novelty, validity, predictions[]}
  skeletons: array           # Abstract structural patterns extracted
  stats: object              # Total candidates, filtered, survival rate
```

## Output contract

```yaml
format: JSONL at data/knowledge/base/{source_domain}-abstractions.jsonl
entry_schema:
  seed_rule: string              # Original domain-specific rule
  source_domain: string
  skeleton: string               # Abstract structural pattern (domain-free)
  target_domain: string          # Where it was re-instantiated
  re_instantiation: string       # The rule in target domain vocabulary
  novelty_score: float           # 0.0-1.0 (1.0 = never published)
  validity_score: float          # 0.0-1.0 (1.0 = survived all challenges)
  predictions: string[]          # Testable predictions that follow from the analogy
  where_it_breaks: string[]      # Where the analogy fails (from adversarial challenge)
  tags: string[]
  source_model: string
  extracted_at: string
```

## The 4-step pipeline

### Step 1: ABSTRACT — strip domain vocabulary, get the skeleton

Take the seed rule and ask: "Remove all domain-specific terms. What is the bare structural pattern?"

**Example:**
```
Seed rule (commodities):
  "When carry exceeds storage cost, arbitrageurs enter until
   the spread compresses to equal the cost-of-carry"

Skeleton:
  "When the return on holding exceeds the cost of holding,
   rational actors enter the trade until the return equals the cost"

Even more abstract:
  "When reward > cost, actors enter until reward = cost"
  Pattern type: equilibrium convergence via arbitrage
```

The abstraction should preserve:
- The **causal mechanism** (what drives what)
- The **equilibrium condition** (what stabilizes)
- The **agent behavior** (who acts and why)
- The **directionality** (what goes up, what goes down)

But strip: specific instruments, units, market names, regulatory references.

### Step 2: RE-INSTANTIATE — apply the skeleton to each target domain

For each target domain, ask: "What concrete phenomenon in [target domain] follows this exact structural pattern? Be specific — name the actors, the variables, the equilibrium condition, the units."

**Example re-instantiations of "when reward > cost, actors enter until reward = cost":**

| Target domain | Re-instantiation | Obvious? |
|--------------|-----------------|----------|
| Labor markets | "When wages exceed reservation wage, workers enter until wages fall to reservation level" | Yes — textbook |
| Enzyme kinetics | "When substrate concentration exceeds Km, reaction rate increases until saturation at Vmax" | Moderate — structural parallel but different mechanism (not agent-based) |
| Network routing | "When a route's bandwidth reward exceeds latency cost, traffic shifts until congestion equalizes cost across routes" | Less obvious — Wardrop equilibrium |
| Microbial ecology | "When nutrient concentration exceeds metabolic cost, organisms proliferate until nutrient = maintenance cost" | Non-obvious — Monod kinetics as arbitrage |
| Attention markets | "When content engagement reward exceeds production cost, creators enter until engagement per creator equals production cost" | Non-obvious — creator economy as cost-of-carry |

### Step 3: FILTER — rate novelty and validate

For each re-instantiation, two scores:

**Novelty score (0.0-1.0):** "How likely is this correspondence to appear in published academic literature?"
- 0.0-0.3: Textbook knowledge (labor market wage equilibrium = obvious)
- 0.4-0.6: Known in specialized interdisciplinary work but not widely
- 0.7-1.0: Unlikely to have been published — genuine structural discovery

**Validity score (0.0-1.0):** Adversarial challenge — 3 rounds:

1. **PREDICTION challenge**: "If this analogy is real, what 3 specific predictions would it make about the target domain? Be precise enough to test."
2. **BREAKPOINT challenge**: "Where exactly does this analogy fail? What feature of the source domain has no counterpart in the target? Be specific."
3. **EXPERT challenge**: "A domain expert in [target domain] reads this. What's their strongest objection? Respond to it."

Validity = how well the re-instantiation survives all 3 challenges. An analogy that generates testable predictions AND acknowledges its limits AND withstands expert objection scores high.

**Keep only:** novelty >= threshold AND validity >= min_validity

### Step 4: WRITE — persist the survivors

Write each surviving correspondence to the abstractions KB. Include the skeleton, both domain instantiations, predictions, and breakpoints. This becomes a cross-domain knowledge asset — rules that transfer.

## With bdistill MCP

Use bdistill-extract to build the source KB first, then run this skill on the extracted rules. The MCP server handles session management and JSONL writing. The adversarial challenges use the same `challenger.py` engine.

## Standalone (no dependencies)

The agent performs all 4 steps in sequence. For each seed rule:

1. Generate the abstraction (ask yourself to strip domain vocabulary)
2. Re-instantiate in each target domain (one at a time)
3. Rate novelty (be honest — is this in textbooks?)
4. Run 3 adversarial challenges on each non-trivial re-instantiation
5. Write survivors as JSONL

Use `scripts/extract_engine.py challenge` for the adversarial rounds — same engine, different application.

**Critical: include unrelated target domains.** The whole point is to bypass your intuition about what's related. Include domains that feel absurd. Grain trading × music theory. Hydrology × compiler design. Insurance × evolutionary biology. Most will produce garbage. You're looking for the 5% that surface a genuine structural parallel nobody wrote about.

## Edge cases

- Skeleton too abstract ("things change"): Push for more structure — preserve the mechanism, the equilibrium condition, the agent behavior. "When reward > cost, actors enter until reward = cost" is good. "Stuff balances out" is useless.
- All re-instantiations are textbook: Your seed rule may be too generic. Try a more specific rule with more structural constraints.
- Novelty and validity anti-correlated: The most novel correspondences are often the least valid (speculative). That's expected. You're looking for the rare quadrant: high novelty AND high validity. Expect 5-10% survival rate.
- Model rates its own re-instantiation as novel when it isn't: Use web search (grounded mode) to check if the correspondence has been published. If yes, lower the novelty score.

## Examples

See `references/worked-examples.md` for 3 full worked examples showing different entry points.

## Composes with

- **bdistill-extract**: Build the source KB first. This skill operates on extracted rules.
- **bdistill-validate**: Run consistency probing on the re-instantiated rules — do they produce stable thresholds in the target domain?
- **bdistill-predict**: Use a cross-domain correspondence as the basis for a prediction. "If cloud spot pricing follows the same mean-reversion pattern as soybean basis, then..."
- **bdistill-operationalize**: Monitor the target domain against the transferred rule. If the analogy holds, the rule should trigger correctly on target-domain data.
