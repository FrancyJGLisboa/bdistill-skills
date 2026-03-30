"""
Standalone engine for bdistill-abstract skill.
Handles: skeleton dedup, round-trip scoring, pipeline checkpointing, JSONL writing.

No dependencies beyond stdlib.

Usage (called by the AI agent, not by humans directly):
    python abstract_engine.py dedup-skeletons --skeletons '[{"id":"1","text":"..."},...]'
    python abstract_engine.py round-trip-score --original "seed rule" --recovered "round-trip result"
    python abstract_engine.py checkpoint --session-id abc123 --step "novelty" --data '{...}'
    python abstract_engine.py resume --session-id abc123
    python abstract_engine.py write-correspondence --domain "grain-trading" --entry '{...}'
    python abstract_engine.py filter-summary --session-id abc123
"""

import argparse
import json
import hashlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# ── Vocabulary normalization for synonym-robust dedup ─────────

# Common synonym groups — when comparing skeletons, these are treated as identical
SYNONYM_GROUPS = [
    {"return", "yield", "reward", "payoff", "gain", "profit", "benefit"},
    {"cost", "expense", "price", "penalty", "burden", "carrying cost"},
    {"actor", "agent", "participant", "player", "entity", "operator"},
    {"enter", "join", "participate", "engage", "exploit", "respond"},
    {"equilibrium", "balance", "convergence", "stability", "steady state"},
    {"exceed", "surpass", "outweigh", "dominate", "overtake"},
    {"compress", "narrow", "converge", "decline", "reduce", "shrink"},
    {"threshold", "limit", "boundary", "cutoff", "trigger", "level"},
    {"holding", "carrying", "maintaining", "retaining", "storing"},
    {"rational", "optimizing", "profit-seeking", "self-interested"},
    {"mechanism", "process", "dynamic", "transmission", "pathway"},
    {"friction", "constraint", "bottleneck", "barrier", "impedance"},
    {"spike", "surge", "jump", "shock", "disruption"},
    {"revert", "normalize", "mean-revert", "return to", "recover"},
]

# Build lookup: word → canonical form (first word in group)
_CANON = {}
for group in SYNONYM_GROUPS:
    canonical = sorted(group)[0]  # alphabetically first as canonical
    for word in group:
        _CANON[word] = canonical


def normalize_skeleton(text: str) -> str:
    """Normalize a skeleton for comparison: lowercase, replace synonyms, strip filler."""
    text = text.lower()
    # Remove punctuation except hyphens
    text = re.sub(r"[^\w\s-]", " ", text)
    words = text.split()
    # Replace synonyms with canonical forms
    normalized = []
    for w in words:
        canonical = _CANON.get(w, w)
        normalized.append(canonical)
    # Remove common filler words
    filler = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
              "being", "have", "has", "had", "do", "does", "did", "will",
              "would", "could", "should", "may", "might", "shall", "can",
              "that", "which", "who", "whom", "this", "these", "those",
              "it", "its", "of", "in", "to", "for", "with", "on", "at",
              "from", "by", "as", "into", "through", "during", "until"}
    normalized = [w for w in normalized if w not in filler]
    return " ".join(normalized)


def skeleton_similarity(a: str, b: str) -> float:
    """Compare two skeletons after vocabulary normalization. Returns 0.0-1.0."""
    norm_a = set(normalize_skeleton(a).split())
    norm_b = set(normalize_skeleton(b).split())
    if not norm_a or not norm_b:
        return 0.0
    intersection = norm_a & norm_b
    union = norm_a | norm_b
    return len(intersection) / len(union)  # Jaccard similarity


def dedup_skeletons(skeletons: list[dict], threshold: float = 0.60) -> list[dict]:
    """Cluster skeletons by normalized similarity. Returns deduplicated list.

    Each skeleton dict must have: {"id": str, "text": str, "seed_rule": str}
    Returns: list with duplicates removed, merged seeds noted.
    """
    if not skeletons:
        return []

    clusters: list[list[dict]] = []
    for skel in skeletons:
        placed = False
        for cluster in clusters:
            rep = cluster[0]
            sim = skeleton_similarity(skel["text"], rep["text"])
            if sim >= threshold:
                cluster.append(skel)
                placed = True
                break
        if not placed:
            clusters.append([skel])

    # For each cluster, keep the richest skeleton (longest text), note merged seeds
    result = []
    for cluster in clusters:
        primary = max(cluster, key=lambda s: len(s["text"]))
        merged_seeds = [s["seed_rule"] for s in cluster if s["id"] != primary["id"]]
        primary["merged_from"] = merged_seeds
        primary["cluster_size"] = len(cluster)
        result.append(primary)

    return result


# ── Round-trip scoring ────────────────────────────────────────

def round_trip_score(original: str, recovered: str) -> dict:
    """Score round-trip recovery using the 4-feature structural rubric.

    Returns per-feature scores and overall average.
    The agent provides the raw texts; this function uses normalized
    similarity as a proxy. For full structural scoring, the agent
    should call this AND provide its own feature-level judgments.
    """
    norm_orig = normalize_skeleton(original)
    norm_recv = normalize_skeleton(recovered)

    # Keyword-based feature detection
    features = {
        "mechanism": _feature_score(norm_orig, norm_recv, [
            "arbitrage", "competition", "convergence", "transmission",
            "feedback", "amplification", "diffusion", "cascade",
        ]),
        "equilibrium": _feature_score(norm_orig, norm_recv, [
            "balance", "convergence", "equal", "steady", "stable",
            "compress", "normalize", "revert",
        ]),
        "agents": _feature_score(norm_orig, norm_recv, [
            "actor", "rational", "optimizing", "participant",
            "enter", "respond", "exploit",
        ]),
        "directionality": _feature_score(norm_orig, norm_recv, [
            "increase", "decrease", "compress", "expand",
            "enter", "exit", "spike", "decline",
        ]),
    }

    avg = sum(features.values()) / len(features)

    return {
        "features": features,
        "overall": round(avg, 3),
        "note": "Proxy scores from keyword matching. Agent should override with structural judgment where this is insufficient.",
    }


def _feature_score(orig: str, recv: str, keywords: list[str]) -> float:
    """Score a single structural feature by keyword overlap."""
    orig_kw = {k for k in keywords if k in orig}
    recv_kw = {k for k in keywords if k in recv}
    if not orig_kw:
        return 0.5  # Can't assess — feature not present in original
    if not recv_kw:
        return 0.0  # Feature present in original but not recovered
    overlap = orig_kw & recv_kw
    return len(overlap) / len(orig_kw)


# ── Pipeline checkpointing ────────────────────────────────────

CHECKPOINT_DIR = Path("data/abstract/checkpoints")


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
    """Load checkpoint state to resume an interrupted pipeline."""
    path = CHECKPOINT_DIR / f"{session_id}.json"
    if not path.exists():
        return {"error": f"No checkpoint found for session {session_id}"}

    with open(path) as f:
        state = json.load(f)

    # Determine next step
    step_order = ["abstract", "dedup", "re_instantiate", "novelty", "adversarial", "round_trip", "write"]
    last = state.get("last_step", "")
    if last in step_order:
        idx = step_order.index(last)
        next_step = step_order[idx + 1] if idx + 1 < len(step_order) else "done"
    else:
        next_step = "abstract"

    return {
        "session_id": session_id,
        "last_step": last,
        "next_step": next_step,
        "steps_completed": [s for s in step_order if s in state],
        "data": state,
    }


# ── JSONL writing for correspondences ─────────────────────────

def write_correspondence(domain: str, entry: dict) -> dict:
    """Write a validated cross-domain correspondence to JSONL."""
    domain = re.sub(r"[^a-z0-9-]", "-", domain.lower()).strip("-")
    base_dir = Path("data/knowledge/base")
    base_dir.mkdir(parents=True, exist_ok=True)
    path = base_dir / f"{domain}-abstractions.jsonl"

    entry["domain"] = domain
    entry["extracted_at"] = datetime.now(timezone.utc).isoformat()

    # Content hash for dedup
    key = f"{domain}:{entry.get('skeleton', '')}:{entry.get('target_domain', '')}"
    entry["_hash"] = hashlib.sha256(key.encode()).hexdigest()[:16]

    # Validate JSON
    try:
        json.dumps(entry, ensure_ascii=False)
    except (TypeError, ValueError) as err:
        return {"action": "error", "reason": f"invalid JSON: {err}"}

    # Dedup check
    existing = {}
    if path.exists():
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    e = json.loads(line)
                    existing[e.get("_hash", "")] = e

    h = entry["_hash"]
    if h in existing:
        old_validity = existing[h].get("validity_score", 0)
        new_validity = entry.get("validity_score", 0)
        if new_validity <= old_validity:
            return {"action": "skipped", "reason": "existing entry has higher validity"}
        existing[h] = entry
        action = "updated"
    else:
        existing[h] = entry
        action = "added"

    with open(path, "w") as f:
        for e in existing.values():
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    return {"action": action, "path": str(path), "total_entries": len(existing)}


def filter_summary(session_id: str) -> dict:
    """Generate the filter funnel summary from checkpoint data."""
    path = CHECKPOINT_DIR / f"{session_id}.json"
    if not path.exists():
        return {"error": "No checkpoint found"}

    with open(path) as f:
        state = json.load(f)

    summary = {
        "session_id": session_id,
        "funnel": {},
    }

    if "abstract" in state:
        n = len(state["abstract"].get("data", {}).get("skeletons", []))
        summary["funnel"]["seed_rules"] = n

    if "dedup" in state:
        n = len(state["dedup"].get("data", {}).get("deduplicated", []))
        summary["funnel"]["after_dedup"] = n

    if "re_instantiate" in state:
        n = len(state["re_instantiate"].get("data", {}).get("candidates", []))
        summary["funnel"]["candidates"] = n

    if "novelty" in state:
        n = len(state["novelty"].get("data", {}).get("novel", []))
        summary["funnel"]["after_novelty"] = n

    if "adversarial" in state:
        n = len(state["adversarial"].get("data", {}).get("valid", []))
        summary["funnel"]["after_adversarial"] = n

    if "round_trip" in state:
        n = len(state["round_trip"].get("data", {}).get("survivors", []))
        summary["funnel"]["after_round_trip"] = n

    # Survival rate
    total = summary["funnel"].get("candidates", 0)
    survived = summary["funnel"].get("after_round_trip", 0)
    summary["survival_rate"] = f"{survived}/{total} = {survived/total*100:.0f}%" if total > 0 else "N/A"

    return summary


# ── CLI ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="bdistill-abstract standalone engine")
    sub = parser.add_subparsers(dest="command")

    # dedup-skeletons
    ds = sub.add_parser("dedup-skeletons")
    ds.add_argument("--skeletons", required=True, help="JSON array of {id, text, seed_rule}")
    ds.add_argument("--threshold", type=float, default=0.60)

    # round-trip-score
    rt = sub.add_parser("round-trip-score")
    rt.add_argument("--original", required=True)
    rt.add_argument("--recovered", required=True)

    # checkpoint
    cp = sub.add_parser("checkpoint")
    cp.add_argument("--session-id", required=True)
    cp.add_argument("--step", required=True)
    cp.add_argument("--data", required=True, help="JSON string")

    # resume
    rs = sub.add_parser("resume")
    rs.add_argument("--session-id", required=True)

    # write-correspondence
    wc = sub.add_parser("write-correspondence")
    wc.add_argument("--domain", required=True)
    wc.add_argument("--entry", required=True, help="JSON string")

    # filter-summary
    fs = sub.add_parser("filter-summary")
    fs.add_argument("--session-id", required=True)

    args = parser.parse_args()

    if args.command == "dedup-skeletons":
        skeletons = json.loads(args.skeletons)
        result = dedup_skeletons(skeletons, args.threshold)
        json.dump(result, sys.stdout, indent=2)

    elif args.command == "round-trip-score":
        result = round_trip_score(args.original, args.recovered)
        json.dump(result, sys.stdout, indent=2)

    elif args.command == "checkpoint":
        data = json.loads(args.data)
        result = save_checkpoint(args.session_id, args.step, data)
        json.dump(result, sys.stdout, indent=2)

    elif args.command == "resume":
        result = resume_checkpoint(args.session_id)
        json.dump(result, sys.stdout, indent=2)

    elif args.command == "write-correspondence":
        entry = json.loads(args.entry)
        result = write_correspondence(args.domain, entry)
        json.dump(result, sys.stdout, indent=2)

    elif args.command == "filter-summary":
        result = filter_summary(args.session_id)
        json.dump(result, sys.stdout, indent=2)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
