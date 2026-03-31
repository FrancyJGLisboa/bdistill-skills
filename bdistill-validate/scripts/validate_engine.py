"""
Standalone engine for bdistill-validate skill.
Handles: rephrase generation, number extraction, consistency scoring,
pipeline checkpointing, and results writing.

No dependencies beyond stdlib.

Usage (called by the AI agent, not by humans directly):
    python validate_engine.py generate-rephrases --claim "SAR threshold is R$50,000" --num 5
    python validate_engine.py extract-numbers --text "The threshold is R$50,000 or about 50K BRL"
    python validate_engine.py consistency-score --values '[50000, 50000, 50000, 48000, 50000]'
    python validate_engine.py checkpoint --session-id abc123 --step "probe_3" --data '{...}'
    python validate_engine.py resume --session-id abc123
    python validate_engine.py write-results --domain "aml-compliance" --results '[{...}]'
"""

import argparse
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# -- Rephrase generation ----------------------------------------------------

STRATEGIES = [
    ("direct", "What is the {concept}?"),
    ("scenario", "At what point does {concept} trigger?"),
    ("confirm_wrong", 'Is it true that {concept} is {wrong_value}?'),
    ("context_shift", "From a practitioner's perspective, what value for {concept}?"),
    ("precision", "What is the exact numeric value for {concept}?"),
]


def _extract_concept_and_number(claim: str) -> tuple[str, str | None]:
    """Pull a rough concept phrase and the first number from a claim."""
    # Find the first number (with optional currency/suffix)
    num_match = re.search(
        r"[R$€£]*\s*[\d,]+(?:\.\d+)?(?:\s*[KMBkmb])?", claim
    )
    number = num_match.group(0).strip() if num_match else None

    # Concept: strip the number portion and common filler
    concept = claim
    if num_match:
        concept = claim[: num_match.start()] + claim[num_match.end() :]
    concept = re.sub(r"\b(is|are|was|the|a|an|about|approximately)\b", "", concept, flags=re.I)
    concept = re.sub(r"\s{2,}", " ", concept).strip(" ,.-")
    return concept, number


def _make_wrong_value(number_str: str | None) -> str:
    """Generate a deliberately wrong number for the confirm-wrong strategy."""
    if number_str is None:
        return "10,000"
    raw = _parse_single_number(number_str)
    if raw is None or raw == 0:
        return "10,000"
    # Offset by ~40% to be clearly wrong but plausible
    wrong = raw * 1.4
    if wrong == int(wrong):
        return f"{int(wrong):,}"
    return f"{wrong:,.2f}"


def generate_rephrases(claim: str, num: int = 5) -> list[dict]:
    """Return up to `num` rephrased probe questions from a claim."""
    concept, number = _extract_concept_and_number(claim)
    wrong = _make_wrong_value(number)

    results = []
    for strategy, template in STRATEGIES[: num]:
        text = template.format(concept=concept, wrong_value=wrong)
        results.append({"strategy": strategy, "question": text})
    return results


# -- Number extraction ------------------------------------------------------

_SUFFIX_MAP = {
    "k": 1_000,
    "m": 1_000_000,
    "b": 1_000_000_000,
    "thousand": 1_000,
    "million": 1_000_000,
    "billion": 1_000_000_000,
}

_NUMBER_PATTERN = re.compile(
    r"""
    (?:R\$|US\$|\$|€|£|BRL|USD|EUR|GBP)?\s*   # optional currency
    (\d{1,3}(?:[,.\s]\d{3})*(?:[.,]\d+)?)       # digits with grouping
    \s*(%|[KkMmBb](?:illion|housand)?)?          # optional suffix
    """,
    re.VERBOSE,
)


def _parse_single_number(raw: str) -> float | None:
    """Parse a single numeric string, handling commas and dots as grouping."""
    raw = raw.strip().replace(" ", "")
    # Strip currency prefixes
    raw = re.sub(r"^(?:R\$|US\$|\$|€|£|BRL|USD|EUR|GBP)\s*", "", raw)
    if not raw:
        return None

    # Determine if the last separator is decimal or grouping
    # Heuristic: if string has both , and . the last one is decimal
    has_comma = "," in raw
    has_dot = "." in raw

    if has_comma and has_dot:
        # Last separator is decimal
        last_comma = raw.rfind(",")
        last_dot = raw.rfind(".")
        if last_dot > last_comma:
            raw = raw.replace(",", "")  # commas are grouping
        else:
            raw = raw.replace(".", "").replace(",", ".")  # dots are grouping
    elif has_comma:
        # Check if comma is decimal (e.g., "50,5") or grouping (e.g., "50,000")
        parts = raw.split(",")
        if len(parts) == 2 and len(parts[1]) != 3:
            raw = raw.replace(",", ".")  # decimal comma
        else:
            raw = raw.replace(",", "")  # grouping commas
    # else: dots only or no separators -- float() handles it

    try:
        return float(raw)
    except ValueError:
        return None


def extract_numbers(text: str) -> list[float]:
    """Extract all numeric values from text, normalizing currencies and suffixes."""
    results = []
    for match in _NUMBER_PATTERN.finditer(text):
        digits_raw = match.group(1)
        suffix_raw = (match.group(2) or "").strip().lower()

        value = _parse_single_number(digits_raw)
        if value is None:
            continue

        # Apply suffix multiplier
        if suffix_raw == "%":
            pass  # keep as-is (percentage)
        else:
            multiplier = _SUFFIX_MAP.get(suffix_raw, 1)
            value *= multiplier

        results.append(value)
    return results


# -- Consistency scoring ----------------------------------------------------

def consistency_score(values: list[float]) -> dict:
    """Score consistency of repeated numeric answers.

    Returns mean, std, cv (coefficient of variation), score (0-1), tier.
    """
    if not values:
        return {"mean": 0, "std": 0, "cv": 0, "score": 0, "tier": "unstable"}

    n = len(values)
    mean = sum(values) / n

    if n < 2:
        return {"mean": mean, "std": 0.0, "cv": 0.0, "score": 1.0, "tier": "stable"}

    variance = sum((v - mean) ** 2 for v in values) / (n - 1)
    std = math.sqrt(variance)

    cv = std / abs(mean) if mean != 0 else (0.0 if std == 0 else 1.0)
    score = round(1.0 - min(cv * 2, 1.0), 4)

    if score >= 0.85:
        tier = "stable"
    elif score >= 0.60:
        tier = "moderate"
    else:
        tier = "unstable"

    return {
        "mean": round(mean, 4),
        "std": round(std, 4),
        "cv": round(cv, 4),
        "score": score,
        "tier": tier,
    }


# -- Pipeline checkpointing ------------------------------------------------

CHECKPOINT_DIR = Path("data/validate/checkpoints")


def save_checkpoint(session_id: str, step: str, data: dict) -> dict:
    """Save pipeline state so it can resume after interruption."""
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    path = CHECKPOINT_DIR / f"{session_id}.json"

    state = {}
    if path.exists():
        with open(path) as f:
            state = json.load(f)

    state[step] = {
        "data": data,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    state["last_step"] = step
    state["session_id"] = session_id

    with open(path, "w") as f:
        json.dump(state, f, indent=2, default=str)

    return {"saved": str(path), "step": step, "steps_completed": list(state.keys())}


def resume_checkpoint(session_id: str) -> dict:
    """Load checkpoint state to determine which probe to continue from."""
    path = CHECKPOINT_DIR / f"{session_id}.json"
    if not path.exists():
        return {"error": f"No checkpoint found for session {session_id}"}

    with open(path) as f:
        state = json.load(f)

    # Find the highest completed probe index
    probe_steps = sorted(
        [k for k in state if k.startswith("probe_")],
        key=lambda k: int(k.split("_")[1]),
    )
    last = state.get("last_step", "")

    if probe_steps:
        last_idx = int(probe_steps[-1].split("_")[1])
        next_step = f"probe_{last_idx + 1}"
    else:
        next_step = "probe_0"

    return {
        "session_id": session_id,
        "last_step": last,
        "next_step": next_step,
        "steps_completed": probe_steps,
        "data": state,
    }


# -- Results writing --------------------------------------------------------

def write_results(domain: str, results: list[dict]) -> dict:
    """Write consistency validation results to JSON."""
    domain = re.sub(r"[^a-z0-9-]", "-", domain.lower()).strip("-")
    base_dir = Path("data/consistency")
    base_dir.mkdir(parents=True, exist_ok=True)
    path = base_dir / f"{domain}-results.json"

    # Load existing results if present
    existing = []
    if path.exists():
        with open(path) as f:
            existing = json.load(f)

    # Index existing by entry_id for dedup/update
    by_id = {e.get("entry_id"): e for e in existing if "entry_id" in e}

    for entry in results:
        entry["validated_at"] = datetime.now(timezone.utc).isoformat()
        eid = entry.get("entry_id")
        if eid:
            by_id[eid] = entry  # upsert
        else:
            existing.append(entry)

    # Merge back
    merged = list(by_id.values()) + [e for e in existing if e.get("entry_id") not in by_id]

    with open(path, "w") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    stable = sum(1 for e in merged if e.get("tier") == "stable" or e.get("stable") is True)
    return {
        "path": str(path),
        "total_entries": len(merged),
        "stable": stable,
        "unstable": len(merged) - stable,
    }


# -- CLI --------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="bdistill-validate standalone engine")
    sub = parser.add_subparsers(dest="command")

    # generate-rephrases
    gr = sub.add_parser("generate-rephrases")
    gr.add_argument("--claim", required=True, help="Claim containing a numeric assertion")
    gr.add_argument("--num", type=int, default=5)

    # extract-numbers
    en = sub.add_parser("extract-numbers")
    en.add_argument("--text", required=True, help="Text to extract numbers from")

    # consistency-score
    cs = sub.add_parser("consistency-score")
    cs.add_argument("--values", required=True, help="JSON array of numbers")

    # checkpoint
    cp = sub.add_parser("checkpoint")
    cp.add_argument("--session-id", required=True)
    cp.add_argument("--step", required=True)
    cp.add_argument("--data", required=True, help="JSON string")

    # resume
    rs = sub.add_parser("resume")
    rs.add_argument("--session-id", required=True)

    # write-results
    wr = sub.add_parser("write-results")
    wr.add_argument("--domain", required=True)
    wr.add_argument("--results", required=True, help="JSON array of result objects")

    args = parser.parse_args()

    if args.command == "generate-rephrases":
        result = generate_rephrases(args.claim, args.num)
        json.dump(result, sys.stdout, indent=2)

    elif args.command == "extract-numbers":
        result = extract_numbers(args.text)
        json.dump(result, sys.stdout, indent=2)

    elif args.command == "consistency-score":
        values = json.loads(args.values)
        result = consistency_score(values)
        json.dump(result, sys.stdout, indent=2)

    elif args.command == "checkpoint":
        data = json.loads(args.data)
        result = save_checkpoint(args.session_id, args.step, data)
        json.dump(result, sys.stdout, indent=2)

    elif args.command == "resume":
        result = resume_checkpoint(args.session_id)
        json.dump(result, sys.stdout, indent=2)

    elif args.command == "write-results":
        results = json.loads(args.results)
        result = write_results(args.domain, results)
        json.dump(result, sys.stdout, indent=2)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
