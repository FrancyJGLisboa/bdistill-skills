"""
Standalone extraction engine for bdistill-extract skill.
Generates questions, challenges answers, scores quality, writes JSONL.
Supports pipeline checkpointing and resume.

No MCP server needed. No dependencies beyond stdlib.

Usage (called by the AI agent, not by humans directly):
    python extract_engine.py generate-questions --terms "AML thresholds" "SAR filing" --mode rules
    python extract_engine.py challenge --answer "IF transaction > 50K THEN file SAR"
    python extract_engine.py score --original "..." --challenge-type evidence --response "..."
    python extract_engine.py write-entry --domain aml-compliance --entry '{...}'
    python extract_engine.py checkpoint --session-id abc123 --step "challenge" --data '{...}'
    python extract_engine.py resume --session-id abc123
"""

import argparse
import json
import hashlib
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# ── Question generation templates ──────────────────────────────

KNOWLEDGE_TEMPLATES = [
    "What are the key principles and mechanisms behind {term}? Include specific numbers and named sources.",
    "Explain {term} step by step. What are the critical thresholds, stages, and decision points?",
    "What does a practitioner need to know about {term} that a generalist would miss?",
    "What are the most common misconceptions about {term}? Correct each with evidence.",
    "How has {term} changed in the last 5 years? What drove the changes?",
]

RULES_TEMPLATES = [
    "What numeric thresholds determine outcomes in {term}? Express each as IF-THEN with specific numbers.",
    "What combination of conditions must ALL be met for a decision in {term}? Express as IF A AND B THEN outcome.",
    "What time-dependent rules govern {term}? Express as IF event within timeframe THEN action.",
    "What exception rules override the standard logic in {term}? Express as IF standard AND exception THEN override.",
    "What are the classification-based decision paths in {term}? For each branch, state criteria and action.",
    "When rules conflict in {term}, which takes priority? List the hierarchy with specific criteria.",
]


def generate_questions(terms: list[str], mode: str = "knowledge", per_term: int = 5) -> list[dict]:
    """Generate targeted extraction questions from seed terms."""
    templates = RULES_TEMPLATES if mode == "rules" else KNOWLEDGE_TEMPLATES
    rng = random.Random(42)
    questions = []

    for term in terms:
        available = list(templates)
        rng.shuffle(available)
        for t in available[:per_term]:
            questions.append({
                "question": t.format(term=term),
                "seed_term": term,
                "mode": mode,
            })

    rng.shuffle(questions)
    return questions


# ── Adversarial challenge engine ──────────────────────────────

EVIDENCE_CHALLENGES = [
    "You stated that {claim}. Name the specific studies, regulations, or data sources that support this.",
    "What is the empirical basis for the claim that {claim}? Cite specific findings with numbers.",
    "Has the claim that {claim} been challenged or contradicted by recent findings?",
]

EDGE_CASE_CHALLENGES = [
    "Name three specific edge cases or exceptions where this does NOT apply. Be concrete.",
    "In which specific populations, regions, or contexts does this fail?",
    "What are the most common exceptions to what you described? Give approximate frequency.",
]

CONTRADICTION_CHALLENGES = [
    "What are the known limitations or caveats of {claim}? List them explicitly.",
    "Is there a competing school of thought that disagrees with {claim}? Name proponents and objections.",
    "Under what conditions would {claim} NOT be true? Give at least two scenarios.",
]


def extract_claims(answer: str) -> list[str]:
    """Extract challengeable claims from an answer."""
    sentences = re.split(r'[.!?]+', answer)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    claims = []

    for sent in sentences:
        lower = sent.lower()
        # Quantitative claims
        if re.search(r'\d+%|\d{4}|\d+\s*(mg|ml|kg|mm|brl|usd|\$|r\$)', lower):
            claims.append(sent)
        # Causal claims
        elif any(w in lower for w in ["causes", "leads to", "results in", "because", "triggers"]):
            claims.append(sent)
        # Conditional claims
        elif re.search(r'\bif\b.*\bthen\b', lower):
            claims.append(sent)
        # Scope claims
        elif any(w in lower for w in ["all ", "every ", "never ", "always ", "must "]):
            claims.append(sent)

    return claims[:5]


def generate_challenges(answer: str, num: int = 3) -> list[dict]:
    """Generate adversarial challenges for an answer."""
    claims = extract_claims(answer)
    if not claims:
        claims = [answer[:200]]

    challenges = []
    claim = random.choice(claims)

    # Always include one of each type
    templates = [
        ("evidence", EVIDENCE_CHALLENGES),
        ("edge_case", EDGE_CASE_CHALLENGES),
        ("contradiction", CONTRADICTION_CHALLENGES),
    ]

    for challenge_type, tmpls in templates[:num]:
        t = random.choice(tmpls)
        text = t.format(claim=claim) if "{claim}" in t else t
        challenges.append({
            "type": challenge_type,
            "text": text,
            "target_claim": claim,
        })

    return challenges


# ── Quality scoring ────────────────────────────────────────────

def score_entry(answer: str, challenge_responses: list[str] | None = None) -> dict:
    """Score an entry's quality based on content analysis."""
    lower = answer.lower()
    word_count = len(answer.split())

    # Base score from content quality
    score = 0.5

    # Specificity: numbers, named entities, regulations
    has_numbers = bool(re.search(r'\d+%|\d+\.\d+|\bBRL\b|\bR\$|\$\d', answer))
    named_entities = len(re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+', answer))
    has_regulations = bool(re.search(r'Art\.\s*\d+|Circular\s+\d+|Lei\s+\d+|Section\s+\d+', answer))

    if has_numbers:
        score += 0.10
    if named_entities >= 2:
        score += 0.10
    if has_regulations:
        score += 0.10

    # Depth
    if word_count >= 100:
        score += 0.05
    if word_count >= 200:
        score += 0.05

    # Structure
    if re.search(r'^\s*\d+[\.\)]\s', answer, re.MULTILINE):
        score += 0.05
    if any(w in lower for w in ["if ", "then ", "when "]):
        score += 0.05

    # Challenge response quality
    if challenge_responses:
        for resp in challenge_responses:
            resp_lower = resp.lower()
            if any(w in resp_lower for w in ["actually", "to correct", "more accurately", "i should clarify"]):
                score += 0.03  # self-correction = honest = good
            if any(w in resp_lower for w in ["study", "evidence", "according to", "data shows"]):
                score += 0.05
            if any(w in resp_lower for w in ["however", "limitation", "caveat", "exception"]):
                score += 0.03

    return {
        "confidence": round(min(1.0, score), 3),
        "tier": "verified" if score >= 0.8 else "solid" if score >= 0.65 else "approximate",
        "has_numbers": has_numbers,
        "named_entities": named_entities,
        "has_regulations": has_regulations,
        "word_count": word_count,
        "self_corrected": any(
            any(w in r.lower() for w in ["actually", "to correct", "more accurately"])
            for r in (challenge_responses or [])
        ),
    }


# ── JSONL writing ──────────────────────────────────────────────

def normalize_domain(domain: str) -> str:
    """Normalize domain name: lowercase, hyphens only."""
    return re.sub(r"[^a-z0-9-]", "-", domain.lower()).strip("-")


def entry_hash(domain: str, question: str) -> str:
    """Content hash for deduplication."""
    key = f"{domain}:{question.lower()}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def write_entry(domain: str, entry: dict, mode: str = "knowledge") -> dict:
    """Write a single entry to the appropriate JSONL file with deduplication."""
    domain = normalize_domain(domain)

    if mode == "rules":
        base_dir = Path("data/rules/base")
    else:
        base_dir = Path("data/knowledge/base")

    base_dir.mkdir(parents=True, exist_ok=True)
    path = base_dir / f"{domain}.jsonl"

    # Add metadata
    entry["domain"] = domain
    entry["extracted_at"] = datetime.now(timezone.utc).isoformat()
    h = entry_hash(domain, entry.get("question", entry.get("conditions", "")))
    entry["_hash"] = h

    # Deduplicate: check if same question exists
    existing = {}
    if path.exists():
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    e = json.loads(line)
                    existing[e.get("_hash", "")] = e

    if h in existing:
        old_conf = existing[h].get("confidence", 0)
        new_conf = entry.get("confidence", 0)
        if new_conf <= old_conf:
            return {"action": "skipped", "reason": "existing entry has higher confidence"}
        existing[h] = entry
        action = "updated"
    else:
        existing[h] = entry
        action = "added"

    # Validate JSON before writing
    try:
        for e in existing.values():
            json.dumps(e, ensure_ascii=False)
    except (TypeError, ValueError) as err:
        return {"action": "error", "reason": f"invalid JSON: {err}"}

    # Write back
    with open(path, "w") as f:
        for e in existing.values():
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    return {"action": action, "path": str(path), "total_entries": len(existing)}


# ── Pipeline checkpointing ────────────────────────────────────

CHECKPOINT_DIR = Path("data/extract/checkpoints")


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
    step_order = ["generate", "answer", "challenge", "score", "write"]
    last = state.get("last_step", "")
    if last in step_order:
        idx = step_order.index(last)
        next_step = step_order[idx + 1] if idx + 1 < len(step_order) else "done"
    else:
        next_step = "generate"

    # Count questions answered so far
    answer_data = state.get("answer", {}).get("data", {})
    questions_answered = answer_data.get("questions_answered", 0)
    total_questions = answer_data.get("total_questions", 0)
    entries_written = state.get("write", {}).get("data", {}).get("entries_written", 0)
    domain = state.get("generate", {}).get("data", {}).get("domain", "")

    return {
        "session_id": session_id,
        "domain": domain,
        "last_step": last,
        "next_step": next_step,
        "steps_completed": [s for s in step_order if s in state],
        "questions_answered": questions_answered,
        "total_questions": total_questions,
        "entries_written": entries_written,
        "data": state,
    }


# ── CLI ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="bdistill standalone extraction engine")
    sub = parser.add_subparsers(dest="command")

    # generate-questions
    gen = sub.add_parser("generate-questions")
    gen.add_argument("--terms", nargs="+", required=True)
    gen.add_argument("--mode", choices=["knowledge", "rules"], default="knowledge")
    gen.add_argument("--per-term", type=int, default=5)
    gen.add_argument("--session-id", default=None, help="Session ID for checkpoint tracking")

    # challenge
    ch = sub.add_parser("challenge")
    ch.add_argument("--answer", required=True)
    ch.add_argument("--num", type=int, default=3)
    ch.add_argument("--session-id", default=None, help="Session ID for checkpoint tracking")

    # score
    sc = sub.add_parser("score")
    sc.add_argument("--answer", required=True)
    sc.add_argument("--challenge-responses", nargs="*", default=[])
    sc.add_argument("--session-id", default=None, help="Session ID for checkpoint tracking")

    # write-entry
    wr = sub.add_parser("write-entry")
    wr.add_argument("--domain", required=True)
    wr.add_argument("--entry", required=True, help="JSON string")
    wr.add_argument("--mode", choices=["knowledge", "rules"], default="knowledge")
    wr.add_argument("--session-id", default=None, help="Session ID for checkpoint tracking")

    # checkpoint
    cp = sub.add_parser("checkpoint")
    cp.add_argument("--session-id", required=True)
    cp.add_argument("--step", required=True)
    cp.add_argument("--data", required=True, help="JSON string")

    # resume
    rs = sub.add_parser("resume")
    rs.add_argument("--session-id", required=True)

    args = parser.parse_args()

    if args.command == "generate-questions":
        questions = generate_questions(args.terms, args.mode, args.per_term)
        json.dump(questions, sys.stdout, indent=2)

    elif args.command == "challenge":
        challenges = generate_challenges(args.answer, args.num)
        json.dump(challenges, sys.stdout, indent=2)

    elif args.command == "score":
        result = score_entry(args.answer, args.challenge_responses or None)
        json.dump(result, sys.stdout, indent=2)

    elif args.command == "write-entry":
        entry = json.loads(args.entry)
        result = write_entry(args.domain, entry, args.mode)
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
