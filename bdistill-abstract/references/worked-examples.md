# bdistill-abstract — Worked Examples

Three entry points: from an existing KB, from a domain you're leaving, and from a single curious rule.

---

## Example 1: From an existing KB — "What else do my grain trading rules apply to?"

You're a commodities analyst. You extracted 50 rules about grain trading last week. Now you're curious — do any of these patterns exist in other markets?

**You say:**
> "Take my top 5 rules from grain-trading KB and find cross-domain equivalents in energy markets, crypto, and insurance"

**The agent:**
1. Reads `data/rules/base/grain-trading.jsonl`, picks top 5 by confidence
2. Abstracts each into a structural skeleton
3. Re-instantiates in energy, crypto, insurance
4. Runs adversarial challenges, filters

**You get:**

```
SEED RULE 1 (grain-trading, conf 0.92):
  "IF basis widens > -50 cents during non-harvest AND persists > 10 days
   THEN signal is logistics friction, expect mean-reversion in 6-8 weeks"

SKELETON:
  "IF local-vs-reference price discount exceeds threshold during off-peak
   AND persists beyond normal duration THEN cause is supply-chain friction
   not fundamental shift, expect mean-reversion as flexible capacity responds"

RE-INSTANTIATIONS THAT SURVIVED:

  [1] Energy — natural gas basis (novelty: 0.35, validity: 0.90)
      "IF Henry Hub vs Waha spread > $1.50 during non-winter AND persists > 7 days
       THEN Permian takeaway pipeline constraint, reverts as LNG export absorbs"
      Status: KNOWN — Waha basis dynamics are well-documented
      → Low novelty but confirms the pattern transfers

  [2] Crypto — CEX vs DEX price (novelty: 0.72, validity: 0.78)
      "IF centralized exchange price exceeds DEX price > 3% during non-event periods
       AND persists > 4 hours THEN signal is bridge/withdrawal friction not demand,
       expect arbitrage bots to close within 12 hours"
      Status: NON-OBVIOUS — basis trading framework applied to CEX-DEX spreads
      → Prediction: mean-reversion speed should correlate with bridge uptime,
        same way grain basis reverts with truck availability

  [3] Insurance — reinsurance pricing (novelty: 0.68, validity: 0.73)
      "IF reinsurance rate-on-line exceeds actuarial expected loss > 40%
       during non-catastrophe renewal AND persists > 1 quarter THEN signal is
       capital supply friction, expect alternative capital (ILS/cat bonds) to enter
       and compress spread over 6-12 months"
      Status: NON-OBVIOUS — cost-of-carry arbitrage mapped to reinsurance capital cycle
      → Where it breaks: reinsurance capital is slower than grain trucks (months vs weeks)

FILTERED OUT (did not survive challenge):
  - Crypto mining hashrate analogy — adversary killed it: "miners don't arbitrage
    a price spread, they produce a commodity. Wrong structural pattern."
  - Insurance claims reserves — too far from the original mechanism
```

**Why this matters:** You didn't learn crypto or insurance. You transferred structural knowledge from a domain you know deeply. The CEX-DEX correspondence is a genuinely non-obvious insight — and it comes with a testable prediction.

---

## Example 2: Entering a new domain — "Transfer my AML expertise to healthcare fraud"

You're a compliance officer who built a strong AML rules KB. Your company is expanding into health insurance fraud detection. You suspect the patterns are similar but can't articulate why.

**You say:**
> "Abstract my top rules from aml-compliance-brazil and re-instantiate them in healthcare-fraud-detection and procurement-fraud"

**The agent abstracts and re-instantiates:**

```
SEED RULE (aml-compliance, conf 0.91):
  "IF transaction volume spikes > 3x 90-day average AND transactions are
   round numbers AND multiple beneficiaries share address/phone
   THEN structuring pattern, file SAR"

SKELETON:
  "IF activity volume spikes abnormally AND individual events show
   artificial regularity AND multiple entities share identity markers
   THEN coordinated evasion pattern, escalate"

RE-INSTANTIATIONS:

  [1] Healthcare fraud — billing mill (novelty: 0.45, validity: 0.88)
      "IF claims volume from a single provider spikes > 3x peer average
       AND procedure codes cluster on maximum-reimbursement items
       AND multiple patients share address or refer each other
       THEN billing mill pattern, flag for SIU investigation"
      Predictions:
        (a) flagging accuracy improves if you add "provider age < 2 years"
        (b) the round-number signal maps to "always billing at code ceiling"

  [2] Procurement fraud — split purchasing (novelty: 0.55, validity: 0.82)
      "IF purchase order volume from a single vendor spikes > 3x historical
       AND PO amounts cluster just below approval thresholds
       AND multiple POs share delivery addresses or approver
       THEN split-purchase evasion, escalate to internal audit"
      Predictions: the AML "round number" signal maps to "just below threshold"
      Where it breaks: procurement has fewer entities than banking — false positive
      rate will be higher because legitimate vendor concentration is common

  [3] Healthcare fraud — upcoding (novelty: 0.65, validity: 0.75)
      "IF a provider's average reimbursement per visit exceeds peer 90th percentile
       AND visit duration codes are consistently maximum
       AND patient mix doesn't justify complexity (age, diagnosis mix normal)
       THEN upcoding pattern — the 'structuring' equivalent is systematic
       over-coding rather than amount manipulation"
      Non-obvious: maps AML structuring to a completely different fraud mechanic
      (amount manipulation → code manipulation) through the abstract skeleton
```

**Why this matters:** Instead of building healthcare fraud rules from scratch (months of work), you transferred your AML expertise in one session. The adversarial challenge caught where the analogy breaks (procurement has legitimate vendor concentration) and where it extends in non-obvious ways (the "round number" signal maps to "just below threshold").

---

## Example 3: Exploring from a single curious rule — "Does this tidal pattern exist elsewhere?"

You read something about how tidal forces create predictable harmonic patterns in ocean currents. You wonder if this pattern exists in completely different systems.

**You say:**
> "Abstract this rule and re-instantiate in commodity markets, social media, epidemiology, and urban traffic: 'Tidal forces create predictable harmonic patterns with known frequencies, but local geography (bays, straits, shelves) creates resonance that amplifies specific harmonics and suppresses others, making each location's tidal signature unique despite the universal forcing function'"

**The agent:**

```
SKELETON:
  "A universal periodic forcing function creates predictable base patterns,
   but local structural constraints create resonance that amplifies specific
   frequencies and suppresses others, making each local instance unique
   despite identical forcing"

RE-INSTANTIATIONS:

  [1] Commodity markets — seasonality (novelty: 0.60, validity: 0.85)
      "Global agricultural crop cycles create predictable seasonal price
       patterns (universal forcing), but local infrastructure constraints
       (port capacity, storage, transport) create resonance — amplifying
       seasonal moves in constrained regions (Mato Grosso interior) and
       dampening them in well-connected ones (Gulf ports)"
      Prediction: basis seasonality amplitude should correlate with
      infrastructure constraint severity, the way tidal amplitude
      correlates with bay geometry
      → TESTABLE against historical basis data by region

  [2] Social media virality (novelty: 0.78, validity: 0.70)
      "Algorithmic content cycles create predictable engagement patterns
       (universal forcing: posting time, day-of-week), but network topology
       (community structure, bridge nodes) creates resonance — amplifying
       specific content types in tightly clustered communities and damping
       them in loosely connected ones"
      Where it breaks: social networks rewire dynamically (bays don't move)
      → Partially valid — holds for short time windows where topology is stable

  [3] Epidemiology — endemic oscillation (novelty: 0.50, validity: 0.88)
      "Seasonal immune cycling creates predictable disease incidence patterns
       (universal forcing), but local population structure (age distribution,
       density, vaccination pockets) creates resonance — amplifying outbreaks
       in susceptible clusters and suppressing them in highly immune ones"
      Known in epidemiology as "resonant epidemic dynamics" — lower novelty
      but HIGH validity. The structural parallel is real and well-studied.
      → Confirms the abstract pattern is not just a metaphor

  [4] Urban traffic (novelty: 0.70, validity: 0.77)
      "Commute cycles create predictable traffic patterns (universal forcing),
       but road network topology (bottlenecks, on-ramp spacing, signal timing)
       creates resonance — amplifying congestion at specific nodes and times
       that aren't explained by demand alone"
      Prediction: traffic congestion amplitude at a node should correlate with
      the node's topological betweenness centrality, the way tidal range
      correlates with strait narrowness
      → TESTABLE against traffic sensor data

FILTERED OUT:
  - Music theory ("chord progressions as tidal harmonics") — adversary: "harmonic
    in music is a technical term with different mechanics, analogy is surface-level"
  - Cryptocurrency price cycles — adversary: "crypto has no universal forcing
    function (no 'tide'), cycles are endogenous not exogenous"
```

**Why this matters:** Starting from oceanography, you discovered that commodity basis seasonality, epidemic dynamics, and urban traffic congestion share the same structural pattern — "universal forcing + local resonance." Two of the four re-instantiations come with testable predictions against real data. The adversarial filter killed the ones that were just surface-level wordplay (music, crypto).

---

## What to do with the survivors

---

## Example 4: A healthy failure — zero survivors (this is correct behavior)

Not every rule transfers. The pipeline is designed to kill weak correspondences. Here's what it looks like when nothing survives.

**You say:**
> "Abstract this ANVISA regulation and find cross-domain equivalents in energy trading and software engineering: 'IF clinical trial Phase III fails to meet primary endpoint with p < 0.05 AND sponsor has not filed for protocol amendment within 60 days THEN ANVISA automatically suspends the IND and requires new pre-clinical data package per RDC 9/2015 Art. 42'"

**The agent:**

```
ABSTRACTION ATTEMPT:

  Domain-specific: [the full ANVISA rule above]

  Structural: "IF a multi-stage approval process fails its primary
    criterion AND the applicant doesn't request modification within
    a regulatory deadline THEN the authority reverts the process to
    an earlier stage requiring new foundational evidence"

  Universal: "IF test fails AND no corrective action within deadline
    THEN revert to earlier stage"

DEDUP: Only 1 seed rule, no dedup needed.

RE-INSTANTIATION:

  Energy trading:
    "IF a power plant capacity test fails to meet minimum output AND
     the operator doesn't file remediation plan within 60 days THEN
     the grid operator revokes capacity market qualification"
    → Structural match: partial. Both have fail → deadline → revert.
    → But: the "new foundational evidence" concept has no equivalent
      in capacity markets (you just retest, you don't start over).

  Software engineering:
    "IF a production deployment fails acceptance tests AND the team
     doesn't file a rollback within the SLA window THEN CI/CD pipeline
     reverts to last known good state"
    → Structural match: surface-level. Both have fail → deadline → revert.
    → But: software rollback is instantaneous and automated; regulatory
      reversion requires months of new pre-clinical work. The TIME
      SCALE and REVERSIBILITY are fundamentally different.

NOVELTY CHECK (Step 3a):
  Energy: Query 3 (target-only) finds: capacity market qualification rules
    are well-documented in PJM/MISO tariffs. Novelty: 0.2 (known).
    → FILTERED OUT before adversarial round.

  Software: Query 3 finds: CI/CD rollback patterns are extensively
    documented. Novelty: 0.1 (textbook).
    → FILTERED OUT before adversarial round.

RESULT:
  Started with:     1 seed × 2 targets = 2 candidates
  After novelty:    0 candidates (both known in target domains)
  After adversarial: N/A (nothing to challenge)
  After round-trip:  N/A
  Survival rate:     0/2 = 0%

  WHY NOTHING SURVIVED: The seed rule is heavily regulatory — its structure
  is tied to a specific institutional process (multi-stage approval with
  statutory deadlines). Regulatory processes DON'T abstract well because
  their structure comes from legal text, not from underlying mechanisms.
  The "fail → deadline → revert" skeleton is too generic (universal level)
  and the structural level adds regulatory specifics that are jurisdiction-bound.

  RECOMMENDATION: Try extracting the MECHANISM underneath the regulation
  instead of the regulation itself. E.g., "Why does Phase III failure
  with no amendment lead to full reversion?" → because the regulatory
  body treats unaddressed failure as evidence that the foundational
  hypothesis is wrong. THAT mechanism might transfer.
```

**This is a correct result, not a bug.** The pipeline correctly identified that:
1. The re-instantiations were already known in target domains (novelty killed them)
2. The structural match was surface-level (fail → deadline → revert is too generic)
3. Regulatory rules abstract poorly because their structure is institutional, not mechanistic

The recommendation ("extract the mechanism underneath the regulation") is the actionable output of a failure — it tells you what to try next.

---

## What to do with the survivors

Each surviving correspondence is a **hypothesis** with testable predictions. Three next steps:

1. **Validate in the target domain:** Run `bdistill-validate` on the re-instantiated rules. Do the thresholds hold when re-asked 5 ways in target-domain vocabulary?

2. **Predict from the analogy:** Run `bdistill-predict` using the cross-domain rule as evidence. "If CEX-DEX price spreads follow soybean basis dynamics, what happens when Ethereum bridge maintenance is scheduled?"

3. **Operationalize:** Export the re-instantiated rules as JSON, feed to `bdistill-operationalize` with target-domain data. If the transferred rule triggers correctly on live data, the structural correspondence is real — not just a thought experiment.
