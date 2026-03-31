"""
Standalone engine for bdistill-predict skill.
Handles: prediction card writing, resolution/Brier scoring, ledger management, checkpointing.

No dependencies beyond stdlib.

Usage (called by the AI agent, not by humans directly):
    python predict_engine.py write-card --domain "macro-rates" --card '{"question":"...","prediction":"YES",...}'
    python predict_engine.py resolve --card-id abc123 --actual-outcome "yes" --notes "Fed cut 25bp"
    python predict_engine.py ledger --domain "macro-rates"
    python predict_engine.py checkpoint --session-id abc123 --step "challenge" --data '{...}'
    python predict_engine.py resume --session-id abc123
"""

import argparse
import json
import hashlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# ── Paths ────────────────────────────────────────────────────────

CARDS_DIR = Path("data/predictions/cards")
LEDGER_PATH = Path("data/predictions/ledger.jsonl")
CHECKPOINT_DIR = Path("data/predictions/checkpoints")

PREDICT_STEPS = ["decompose", "extract", "challenge", "predict"]


# ── Card writing ─────────────────────────────────────────────────

def write_card(domain: str, card: dict) -> dict:
    """Write a prediction card to disk. Auto-generates card_id from content hash."""
    CARDS_DIR.mkdir(parents=True, exist_ok=True)

    question = card.get("question", "")
    created_at = datetime.now(timezone.utc).isoformat()

    # Deterministic card_id from question + domain + timestamp
    raw = f"{question}:{domain}:{created_at}"
    card_id = hashlib.sha256(raw.encode()).hexdigest()[:16]

    card["card_id"] = card_id
    card["domain"] = re.sub(r"[^a-z0-9-]", "-", domain.lower()).strip("-")
    card["created_at"] = created_at
    card.setdefault("prediction", "")
    card.setdefault("probability", None)
    card.setdefault("confidence_boundary", [])
    card.setdefault("evidence", [])
    card.setdefault("failure_modes", [])
    card.setdefault("source_model", "")

    path = CARDS_DIR / f"{card_id}.json"
    with open(path, "w") as f:
        json.dump(card, f, indent=2, ensure_ascii=False)

    return {"action": "created", "card_id": card_id, "path": str(path)}


# ── Resolution + Brier scoring ───────────────────────────────────

def resolve_card(card_id: str, actual_outcome: str, notes: str = "") -> dict:
    """Resolve a prediction card and compute Brier score for binary predictions."""
    path = CARDS_DIR / f"{card_id}.json"
    if not path.exists():
        return {"error": f"Card not found: {card_id}"}

    with open(path) as f:
        card = json.load(f)

    outcome_lower = actual_outcome.strip().lower()
    actual_binary = 1.0 if outcome_lower in ("yes", "true", "1") else 0.0

    prob = card.get("probability")
    brier = None
    if prob is not None:
        brier = round((float(prob) - actual_binary) ** 2, 6)

    resolution = {
        "actual_outcome": actual_outcome,
        "actual_binary": actual_binary,
        "brier_score": brier,
        "resolved_at": datetime.now(timezone.utc).isoformat(),
        "notes": notes,
    }
    card["resolution"] = resolution

    with open(path, "w") as f:
        json.dump(card, f, indent=2, ensure_ascii=False)

    # Append to ledger
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    ledger_entry = {
        "card_id": card_id,
        "domain": card.get("domain", ""),
        "question": card.get("question", ""),
        "prediction": card.get("prediction", ""),
        "probability": prob,
        "actual_outcome": actual_outcome,
        "brier_score": brier,
        "resolved_at": resolution["resolved_at"],
        "notes": notes,
    }
    with open(LEDGER_PATH, "a") as f:
        f.write(json.dumps(ledger_entry, ensure_ascii=False) + "\n")

    return {"action": "resolved", "card_id": card_id, "brier_score": brier, "path": str(path)}


# ── Ledger aggregation ───────────────────────────────────────────

def query_ledger(domain: str | None = None) -> dict:
    """Read the ledger, optionally filter by domain, compute aggregate stats."""
    if not LEDGER_PATH.exists():
        return {"entries": [], "stats": {}, "note": "No ledger file found"}

    entries = []
    with open(LEDGER_PATH) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if domain and entry.get("domain", "") != domain:
                continue
            entries.append(entry)

    if not entries:
        return {"entries": [], "stats": {"note": f"No entries for domain '{domain}'"}}

    scored = [e for e in entries if e.get("brier_score") is not None]
    brier_values = [e["brier_score"] for e in scored]

    stats = {
        "total_predictions": len(entries),
        "total_resolved": len(scored),
    }

    if brier_values:
        stats["mean_brier"] = round(sum(brier_values) / len(brier_values), 4)
        best = min(scored, key=lambda e: e["brier_score"])
        worst = max(scored, key=lambda e: e["brier_score"])
        stats["best"] = {"card_id": best["card_id"], "question": best.get("question", ""), "brier": best["brier_score"]}
        stats["worst"] = {"card_id": worst["card_id"], "question": worst.get("question", ""), "brier": worst["brier_score"]}

        # Accuracy: correct if (prob >= 0.5 and actual == 1) or (prob < 0.5 and actual == 0)
        correct = 0
        for e in scored:
            prob = e.get("probability")
            if prob is None:
                continue
            actual = 1.0 if str(e.get("actual_outcome", "")).strip().lower() in ("yes", "true", "1") else 0.0
            predicted_yes = float(prob) >= 0.5
            if (predicted_yes and actual == 1.0) or (not predicted_yes and actual == 0.0):
                correct += 1
        stats["accuracy"] = round(correct / len(scored), 4) if scored else None

        # Per-domain breakdown
        domains: dict[str, list[float]] = {}
        for e in scored:
            d = e.get("domain", "unknown")
            domains.setdefault(d, []).append(e["brier_score"])
        stats["by_domain"] = {
            d: {"count": len(vals), "mean_brier": round(sum(vals) / len(vals), 4)}
            for d, vals in sorted(domains.items())
        }

    return {"entries": entries, "stats": stats}


# ── Pipeline checkpointing ───────────────────────────────────────

def save_checkpoint(session_id: str, step: str, data: dict) -> dict:
    """Save prediction pipeline state so it can resume after interruption."""
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
    """Load checkpoint state to determine which prediction phase to continue from."""
    path = CHECKPOINT_DIR / f"{session_id}.json"
    if not path.exists():
        return {"error": f"No checkpoint found for session {session_id}"}

    with open(path) as f:
        state = json.load(f)

    last = state.get("last_step", "")
    if last in PREDICT_STEPS:
        idx = PREDICT_STEPS.index(last)
        next_step = PREDICT_STEPS[idx + 1] if idx + 1 < len(PREDICT_STEPS) else "done"
    else:
        next_step = PREDICT_STEPS[0]

    return {
        "session_id": session_id,
        "last_step": last,
        "next_step": next_step,
        "steps_completed": [s for s in PREDICT_STEPS if s in state],
        "data": state,
    }


# ── CLI ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="bdistill-predict standalone engine")
    sub = parser.add_subparsers(dest="command")

    # write-card
    wc = sub.add_parser("write-card")
    wc.add_argument("--domain", required=True)
    wc.add_argument("--card", required=True, help="JSON string of prediction card")

    # resolve
    rv = sub.add_parser("resolve")
    rv.add_argument("--card-id", required=True)
    rv.add_argument("--actual-outcome", required=True)
    rv.add_argument("--notes", default="")

    # ledger
    lg = sub.add_parser("ledger")
    lg.add_argument("--domain", default=None)

    # checkpoint
    cp = sub.add_parser("checkpoint")
    cp.add_argument("--session-id", required=True)
    cp.add_argument("--step", required=True)
    cp.add_argument("--data", required=True, help="JSON string")

    # resume
    rs = sub.add_parser("resume")
    rs.add_argument("--session-id", required=True)

    args = parser.parse_args()

    if args.command == "write-card":
        card = json.loads(args.card)
        result = write_card(args.domain, card)
        json.dump(result, sys.stdout, indent=2)

    elif args.command == "resolve":
        result = resolve_card(args.card_id, args.actual_outcome, args.notes)
        json.dump(result, sys.stdout, indent=2)

    elif args.command == "ledger":
        result = query_ledger(args.domain)
        json.dump(result, sys.stdout, indent=2)

    elif args.command == "checkpoint":
        data = json.loads(args.data)
        result = save_checkpoint(args.session_id, args.step, data)
        json.dump(result, sys.stdout, indent=2)

    elif args.command == "resume":
        result = resume_checkpoint(args.session_id)
        json.dump(result, sys.stdout, indent=2)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
