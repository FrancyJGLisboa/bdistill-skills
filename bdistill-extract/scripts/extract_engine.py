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


def generate_challenges(
    answer: str,
    num: int = 3,
    depth: str = "standard",
    existing_kb_path: str | None = None,
) -> list[dict]:
    """Generate adversarial challenges for an answer.

    Depth levels:
      - "standard" (default): 3 challenges targeting the strongest claim
      - "thorough": one challenge per extracted claim (up to 5 claims × 1 each)
      - "deep": every claim gets evidence + edge_case + contradiction (up to 5 × 3 = 15)

    If existing_kb_path is provided, also generates CONTRADICTION challenges
    by checking for conflicting entries already in the KB.
    """
    claims = extract_claims(answer)
    if not claims:
        claims = [answer[:200]]

    challenge_types = [
        ("evidence", EVIDENCE_CHALLENGES),
        ("edge_case", EDGE_CASE_CHALLENGES),
        ("contradiction", CONTRADICTION_CHALLENGES),
    ]

    challenges = []

    if depth == "standard":
        # Original behavior: 3 challenges on the strongest claim (most specific)
        claim = max(claims, key=lambda c: len(re.findall(r'\d', c)), default=claims[0])
        for ctype, tmpls in challenge_types[:num]:
            t = random.choice(tmpls)
            text = t.format(claim=claim) if "{claim}" in t else t
            challenges.append({"type": ctype, "text": text, "target_claim": claim})

    elif depth == "thorough":
        # One challenge per claim, rotating types
        for i, claim in enumerate(claims):
            ctype, tmpls = challenge_types[i % len(challenge_types)]
            t = random.choice(tmpls)
            text = t.format(claim=claim) if "{claim}" in t else t
            challenges.append({"type": ctype, "text": text, "target_claim": claim})

    elif depth == "deep":
        # Every claim gets all 3 challenge types
        for claim in claims:
            for ctype, tmpls in challenge_types:
                t = random.choice(tmpls)
                text = t.format(claim=claim) if "{claim}" in t else t
                challenges.append({"type": ctype, "text": text, "target_claim": claim})

    # Cross-KB contradiction check: compare against existing entries
    if existing_kb_path:
        kb_contradictions = _check_kb_contradictions(answer, existing_kb_path)
        challenges.extend(kb_contradictions)

    return challenges


def _check_kb_contradictions(answer: str, kb_path: str) -> list[dict]:
    """Check if the answer contradicts any existing KB entry."""
    path = Path(kb_path)
    if not path.exists():
        return []

    answer_claims = extract_claims(answer)
    if not answer_claims:
        return []

    contradictions = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                existing_text = entry.get("answer", entry.get("action", ""))
                existing_claims = extract_claims(existing_text)

                for new_claim in answer_claims:
                    for old_claim in existing_claims:
                        # Check for numeric disagreement on same topic
                        new_nums = set(re.findall(r'\d+(?:\.\d+)?', new_claim))
                        old_nums = set(re.findall(r'\d+(?:\.\d+)?', old_claim))
                        # Same topic (>40% word overlap) but different numbers
                        new_words = set(new_claim.lower().split())
                        old_words = set(old_claim.lower().split())
                        overlap = len(new_words & old_words) / max(len(new_words | old_words), 1)
                        if overlap > 0.4 and new_nums != old_nums and new_nums and old_nums:
                            contradictions.append({
                                "type": "kb_contradiction",
                                "text": f"Your answer says '{new_claim.strip()}' but an existing KB entry says '{old_claim.strip()}'. The numbers differ ({new_nums} vs {old_nums}). Which is correct? Reconcile with evidence.",
                                "target_claim": new_claim.strip(),
                                "existing_entry_id": entry.get("_hash", "unknown"),
                            })
    except (json.JSONDecodeError, OSError):
        pass

    return contradictions[:3]  # Cap at 3 KB contradictions


# ── Quality scoring ────────────────────────────────────────────

def score_entry(answer: str, challenge_responses: list[str] | None = None) -> dict:
    """Score an entry's quality based on content analysis.

    Analyzes BOTH the original answer AND the challenge responses together.
    """
    # Combine all text for analysis (answer + challenge responses)
    all_text = answer
    if challenge_responses:
        all_text = answer + " " + " ".join(challenge_responses)

    lower = all_text.lower()
    word_count = len(answer.split())  # word count is answer only (not inflated by challenges)

    # Base score from content quality
    score = 0.5

    # Specificity: numbers — match decimals, percentages, currencies, plain integers
    has_numbers = bool(re.search(r'\d+[%.]|\d+\s*(?:hours?|days?|minutes?|seconds?|months?)|\bBRL\b|\bR\$|\$\d|\b\d{2,}\b', all_text))

    # Named entities: Title Case multi-word + ALL-CAPS acronyms (CVSS, CISA, NIST, CISO, etc.)
    title_case = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+', all_text)
    acronyms = re.findall(r'\b[A-Z]{2,6}\b', all_text)
    # Filter common words that happen to be caps (IF, THEN, AND, OR, NOT, SLA, EDD)
    acronym_stopwords = {"IF", "THEN", "AND", "OR", "NOT", "THE", "FOR", "BUT", "ALL", "ANY", "SLA"}
    acronyms = [a for a in acronyms if a not in acronym_stopwords]
    named_entities = len(set(title_case)) + len(set(acronyms))

    # Regulations: broader pattern matching
    has_regulations = bool(re.search(
        r'Art\.\s*\d+|Circular\s+\d+|Lei\s+\d+|Section\s+\d+|'
        r'BOD\s+\d+|NIST\s+SP\s+\d+|ISO\s+\d+|CFR\s+\d+|'
        r'RDC\s+\d+|Directive\s+\d+|Regulation\s+\d+|'
        r'PCI\s+DSS|SOX|GDPR|HIPAA|CCPA|Basel\s+III',
        all_text, re.IGNORECASE
    ))

    if has_numbers:
        score += 0.10
    if named_entities >= 3:
        score += 0.10
    elif named_entities >= 1:
        score += 0.05
    if has_regulations:
        score += 0.10

    # Depth
    if word_count >= 50:
        score += 0.03
    if word_count >= 100:
        score += 0.05
    if word_count >= 200:
        score += 0.05

    # Structure
    if re.search(r'^\s*\d+[\.\)]\s', answer, re.MULTILINE):
        score += 0.05
    if any(w in answer.lower() for w in ["if ", "then ", "when "]):
        score += 0.05

    # Challenge response quality (self-correction is the strongest signal)
    self_corrected = False
    if challenge_responses:
        for resp in challenge_responses:
            resp_lower = resp.lower()
            if any(w in resp_lower for w in [
                "actually", "to correct", "more accurately", "i should clarify",
                "i was imprecise", "upon reflection", "to be more precise",
                "i need to revise", "i misstated", "correction:",
            ]):
                score += 0.05
                self_corrected = True
            if any(w in resp_lower for w in [
                "study", "evidence", "according to", "data shows",
                "published", "research", "documented", "per ",
            ]):
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
        "self_corrected": self_corrected,
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
    ch.add_argument("--depth", choices=["standard", "thorough", "deep"], default="standard",
                    help="standard=3 on best claim, thorough=1 per claim, deep=3 per claim")
    ch.add_argument("--kb-path", default=None, help="Path to existing KB for contradiction detection")
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
        challenges = generate_challenges(
            args.answer, args.num,
            depth=args.depth,
            existing_kb_path=args.kb_path,
        )
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
