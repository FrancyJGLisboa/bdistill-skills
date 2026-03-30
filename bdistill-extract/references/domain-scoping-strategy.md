# Domain Scoping Strategy

How to name domains and write custom_terms so that extraction sessions produce high-quality, non-colliding knowledge bases.

## Why one domain per niche

The bdistill knowledge base is organized by domain name. Three systems depend on this:

1. **export_harness** filters entries by `domain` field only. A broad domain like "compliance" mixes AML, data privacy, and tax entries into one export — the resulting system prompt is noisy and diluted.
2. **Deduplication** matches on `domain + question similarity`. Two questions about different niches (AML vs GDPR) can collide if they share a broad domain, causing one to overwrite the other.
3. **Prediction recall** with `grounded=true` pulls all entries for the domain. A tight domain means every recalled entry is relevant context. A broad domain pollutes the prediction with unrelated facts.

One domain per niche. When in doubt, split.

## Naming convention

Use the pattern `{topic}-{qualifier}-{region}`:

```
aml-compliance-brazil       not  compliance
marine-cargo-uk             not  insurance
wheat-winter-ks             not  agriculture
macro-rates-us              not  economics
cyber-risk-smb              not  security
clinical-trials-phase3      not  pharma
```

Rules:
- Lowercase, hyphen-separated
- Topic comes first (what), qualifier narrows (which kind), region or scope last
- 2-4 segments. More than 4 is over-specified and hard to type.
- Avoid generic suffixes like "-general" or "-misc" — if you need them, the domain is too broad

## Encoding specificity in custom_terms

The custom_terms you pass to bdistill-extract determine the quality of generated questions. Vague terms produce vague questions. Encode three types of specificity directly in the terms:

**Geography**: Include the country, region, or jurisdiction.
- "BCB Circular 3978" not "AML regulation"
- "Kansas HRW wheat basis" not "wheat prices"

**Regulations and standards**: Name the specific law, circular, or standard.
- "SUSEP Circular 621 cyber coverage" not "cyber insurance rules"
- "USDA WASDE corn yield methodology" not "crop forecasting"

**Numeric anchors**: Include known thresholds, units, or ranges.
- "SAR filing threshold BRL 50,000" not "SAR filing"
- "Fed funds rate 25bp increments" not "interest rate changes"

## Examples across domains

### Compliance: `aml-compliance-brazil`

```yaml
custom_terms:
  - "BCB Circular 3978 AML program requirements"
  - "COAF SAR reporting thresholds BRL"
  - "PEP screening criteria and family member rules"
  - "beneficial ownership 25% threshold identification"
  - "Lei 9613 record retention 10-year obligation"
```

### Insurance: `marine-cargo-uk`

```yaml
custom_terms:
  - "Institute Cargo Clauses A/B/C coverage differences"
  - "general average contribution York-Antwerp Rules"
  - "subrogation rights after cargo damage claim"
  - "war risk exclusion and K&R reinstatement"
  - "deviation clause effect on coverage"
```

### Agriculture: `wheat-winter-ks`

```yaml
custom_terms:
  - "Kansas HRW wheat basis calculation vs CBOT"
  - "protein premium discount schedule 11-14%"
  - "Hessian fly free date planting window"
  - "USDA WASDE winter wheat yield revision triggers"
  - "crop insurance APH yield floor calculation"
```

### Macro trading: `macro-rates-us`

```yaml
custom_terms:
  - "Fed funds futures implied probability calculation"
  - "2s10s curve inversion recession lead time"
  - "SOFR-OIS spread stress signal thresholds"
  - "Treasury auction tail basis points significance"
  - "real yield breakeven inflation 5y5y forward"
```

## When to split a domain

Split when any of these are true:

- The same question text could mean different things depending on sub-domain (e.g., "filing threshold" in AML vs tax)
- You need different custom_terms for different geographic jurisdictions
- The export prompt would exceed 4,000 tokens if all entries were included
- Two practitioners in the field would consider themselves in different specialties

Split does not mean discard. You can always query multiple domains in a single prediction by passing them as a list to `grounded=true`.
