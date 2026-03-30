---
name: bdistill-abstract
description: Extract structural rules from one domain, abstract to bare skeletons at three granularity levels, then re-instantiate in other domains to discover non-obvious cross-domain correspondences. Filters with mandatory web-grounded novelty check AND adversarial validity challenge AND reverse round-trip validation. Triggers on "abstract rules", "cross-domain", "structural analogy", "what pattern in X applies to Y", "transfer rules between domains". Outputs validated cross-domain rule correspondences with structured testable predictions.
license: MIT
metadata:
  author: bdistill
  version: "2.0"
  suite: bdistill
---

# Structural Abstraction and Cross-Domain Re-instantiation

Take a rule that works in one domain. Abstract it to a structural skeleton. Re-instantiate that skeleton in other domains. Filter for correspondences that are non-obvious but valid. Verify with reverse round-trip.

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
  abstraction_level: enum[structural, universal]  # Default: structural (see Step 1)
  novelty_threshold: float   # 0.0-1.0 (default: 0.6)
  min_validity: float        # 0.0-1.0 (default: 0.7)
  min_round_trip: float      # 0.0-1.0 (default: 0.5) — reverse validation score
output:
  correspondences: array
  skeletons: array           # Deduplicated structural patterns
  stats: object              # Total candidates, web-filtered, adversarial-filtered, round-trip-filtered, survival rate
```

## Output contract

```yaml
format: JSONL at data/knowledge/base/{source_domain}-abstractions.jsonl
entry_schema:
  seed_rule: string
  source_domain: string
  skeleton: string                   # The structural-level abstraction used
  skeleton_level: enum[structural, universal]
  target_domain: string
  re_instantiation: string
  novelty_score: float               # 0.0-1.0 — web-grounded, not self-assessed
  novelty_search_results: string[]   # What web search found (or didn't)
  validity_score: float              # 0.0-1.0 — from adversarial challenge
  round_trip_score: float            # 0.0-1.0 — does target → source recover the original?
  predictions:                       # STRUCTURED, not free-text
    - claim: string                  # The specific prediction
      test_data: string              # What data you'd need to test it
      confirms_if: string            # What outcome would confirm it
      falsifies_if: string           # What outcome would falsify it
  where_it_breaks: string[]
  tags: string[]
  source_model: string
  extracted_at: string
```

## The 6-step pipeline

### Step 1: ABSTRACT — three levels, route to structural

Generate **three** abstraction levels for each seed rule. Route re-instantiation to the **structural** level by default — it's the sweet spot between too specific (only matches source domain) and too universal (matches everything, therefore useless).

```
Seed rule (domain-specific):
  "When carry exceeds storage cost in grain markets, arbitrageurs enter
   until the spread compresses to equal the cost-of-carry"

Structural skeleton (DEFAULT — use this for re-instantiation):
  "When the return on holding an asset exceeds the cost of holding it,
   rational actors exploit the gap by entering until return = cost.
   Mechanism: arbitrage. Equilibrium: convergence. Agents: profit-seeking."

Universal skeleton (too abstract — only use if structural produces no hits):
  "When reward > cost, actors enter until reward = cost"
```

The **structural** level preserves: causal mechanism, equilibrium condition, agent behavior, directionality, and the *type* of system (market, biological, network, etc.). The **universal** level strips even those, leaving only the bare mathematical relationship.

**Rule: always try structural first.** Only fall back to universal if structural produces zero re-instantiations in any target domain.

### Step 1b: DEDUPLICATE skeletons

When abstracting multiple seed rules from the same KB, cluster the structural skeletons before proceeding. Many domain-specific rules abstract to the same skeleton:

```
"Basis converges to carry"           ─┐
"Futures-spot spread reflects storage" ─┼─→ Same skeleton: "return-on-holding → cost convergence"
"Contango narrows as delivery nears"  ─┘

→ Deduplicate: keep the richest seed rule, merge the others as "also maps to this skeleton"
```

Without dedup, you'll re-instantiate the same skeleton 3 times and think you found 3 insights when you found 1. Compare skeletons by keyword overlap — if >70% of content words match, they're the same pattern.

### Step 2: RE-INSTANTIATE — apply the structural skeleton to each target domain

For each target domain, ask: "What concrete phenomenon in [target domain] follows this exact structural pattern? Be specific — name the actors, the variables, the equilibrium condition, the units."

Use the **structural** skeleton, not the universal one.

### Step 3a: NOVELTY CHECK — mandatory web search (not self-assessed)

**Do not ask the model "how novel is this?"** — the model's answer reflects what it saw in training data, which is exactly the corpus you're trying to go beyond.

Instead, **search the web** for each candidate correspondence:
- Search: `"{source concept}" AND "{target concept}" structural analogy` or `"{source concept}" isomorphic "{target concept}"`
- Search: the specific claim in academic databases (Google Scholar, arXiv, SSRN)
- If you find the correspondence published: floor novelty to 0.0-0.3 (known)
- If you find adjacent work but not the exact claim: score 0.4-0.6 (partially known)
- If you find nothing: score 0.7-1.0 (candidate for genuine discovery)

**This step runs BEFORE adversarial validation** — don't waste adversarial rounds on correspondences that are already published.

### Step 3b: ADVERSARIAL VALIDITY — 3 rounds on novel candidates only

For candidates that passed the novelty check (score >= novelty_threshold):

1. **PREDICTION challenge**: "If this analogy is real, what 3 specific predictions would it make about the target domain?" Each prediction must be structured:

```yaml
- claim: "CEX-DEX spread mean-reversion speed correlates with bridge uptime"
  test_data: "Historical CEX-DEX spreads + Ethereum bridge status logs"
  confirms_if: "Correlation > 0.6 between bridge downtime and spread duration"
  falsifies_if: "No correlation, or spreads persist regardless of bridge status"
```

2. **BREAKPOINT challenge**: "Where exactly does this analogy fail? What feature of the source domain has no counterpart in the target? Be specific."

3. **EXPERT challenge**: "A domain expert in [target domain] reads this. What's their strongest objection? Respond to it."

Validity = how well the re-instantiation survives all 3 challenges.

### Step 4: REVERSE ROUND-TRIP — validate bidirectionality

For each surviving correspondence, test the reverse direction:

1. Take the re-instantiated rule in the target domain
2. Abstract it back to a structural skeleton
3. Re-instantiate that skeleton back into the source domain
4. Compare to the original seed rule

**Round-trip score:**
- 1.0: Recovered the original rule exactly (or a known equivalent)
- 0.7-0.9: Recovered a related rule in the source domain (looser but valid)
- 0.3-0.6: Recovered something in the same area but structurally different
- 0.0-0.2: Failed to recover anything recognizable — the analogy is one-directional

**Keep only:** round_trip_score >= min_round_trip (default 0.5). One-directional analogies are surface-level — they sound right but the structural mapping doesn't actually hold.

### Step 5: WRITE — persist the survivors

Write each surviving correspondence with all metadata: skeleton, both instantiations, web search results, adversarial results, round-trip score, and structured predictions.

**Filter summary:**
```
Started with:        10 seed rules × 5 target domains = 50 candidates
After skeleton dedup: 7 unique skeletons × 5 targets = 35 candidates
After novelty check:  18 candidates (17 were already published)
After adversarial:    9 survived (9 killed by challenges)
After round-trip:     6 survived (3 failed reverse validation)
Survival rate:        6/50 = 12%
```

## With bdistill MCP

Use bdistill-extract to build the source KB first, then run this skill on the extracted rules. The MCP server handles session management and JSONL writing. The adversarial challenges use the same `challenger.py` engine.

## Standalone (no dependencies)

The agent performs all 6 steps in sequence:

1. Abstract each seed rule to 3 levels, select structural
2. Deduplicate skeletons (cluster by keyword overlap > 70%)
3. Re-instantiate in each target domain
4. Web search for each candidate (mandatory — do not skip)
5. Adversarial challenge on novel candidates only (3 rounds)
6. Reverse round-trip validation on adversarial survivors
7. Write survivors as JSONL with full metadata

Use `scripts/extract_engine.py challenge` for adversarial rounds. Use web search for novelty grounding.

**Critical: include unrelated target domains.** The whole point is to bypass your intuition about what's related. Most will produce garbage. You're looking for the 5% that surface a genuine structural parallel nobody wrote about.

## Edge cases

- **Skeleton too abstract** ("things change"): You hit the universal level. Back up to structural — preserve the mechanism, equilibrium, agent behavior. If structural is still too vague, the seed rule itself may be too generic.
- **All re-instantiations are textbook**: The seed rule abstracts to a well-known pattern. Try a more specific rule with more structural constraints (add temporal dynamics, exception conditions, threshold interactions).
- **Novelty and validity anti-correlated**: The most novel correspondences are often the least valid. Expected. You're looking for the rare quadrant: high novelty AND high validity AND survives round-trip. Expect 5-12% survival rate.
- **Web search finds nothing**: Absence of evidence isn't evidence of discovery. The correspondence might just be too niche for web indexing. Mark novelty as "ungrounded" and increase adversarial rigor to compensate.
- **Round-trip recovers a different rule**: The analogy may be valid but asymmetric — it transfers in one direction but not the other. Document this as `"asymmetric_transfer": true`. Still potentially useful, but lower confidence.
- **Multiple seed rules from KB abstract to same skeleton**: The dedup step catches this. If >3 seed rules map to the same skeleton, that skeleton is a **core structural pattern** of your domain — flag it as high-priority for cross-domain exploration.

## Examples

See `references/worked-examples.md` for 3 full worked examples showing different entry points.

## Composes with

- **bdistill-extract**: Build the source KB first. This skill reads from it. If using `kb_path`, the KB must have been created by bdistill-extract (checks for `source_model` and `extracted_at` fields as provenance markers).
- **bdistill-validate**: Run consistency probing on re-instantiated rules — do the transferred thresholds hold when re-asked in target-domain vocabulary?
- **bdistill-predict**: Use a cross-domain correspondence as evidence for a prediction. "If cloud spot pricing follows soybean basis dynamics, then..."
- **bdistill-operationalize**: Monitor the target domain against the transferred rule. If the analogy holds, the rule should trigger correctly on target-domain data.
