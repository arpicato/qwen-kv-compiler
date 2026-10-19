"""Programmatic evaluation: teacher vs compiled vs no-system-prompt.

Deterministic/greedy decoding. Grades by normalized string containment of the
expected answer, plus logit-distribution comparisons (KL, top-1, top-k).
"""

from __future__ import annotations

import re
from typing import Optional

import numpy as np

# mlx is only needed by the generation/logit helpers (greedy_generate,
# kl_divergence, ...). Import lazily so the pure grading functions can be
# reused on the ROCm box without an mlx install.
try:  # pragma: no cover - environment dependent
    import mlx.core as mx
except ImportError:  # pragma: no cover
    mx = None


def normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def grade(pred: str, answer: Optional[str]) -> bool:
    """Lenient containment: the answer's alphanumerics must appear in the pred.

    Handles verbose preambles and hyphenation (e.g. 'WEX-462' matched by
    'coolant **WEX-462**').
    """
    if answer is None:
        return True
    a = normalize(answer)
    if not a:
        return True
    p = normalize(pred)
    if a in p:
        return True
    # allow trailing-digit truncation (model may be cut mid-code)
    if len(a) >= 4 and a[:-1] in p:
        return True
    return False


_CODE_RE = re.compile(r"\b([A-Z]{2,7}-\d{2,4})\b")


def extract_codes(text: str) -> list[str]:
    """Pull identifier-like tokens (ARP-091, VEK-462) out of free text."""
    return _CODE_RE.findall(text.upper())


def grade_strict(pred: str, answer: Optional[str]) -> bool:
    """Strict grading with NO partial-digit credit.

    Rationale: the lenient grader accepts a truncated code ('YOR-83' matches
    'YOR-831'), which lets a wrong-then-cut answer pass. For a retrieval task
    about *confusable* identifiers, that is exactly the failure mode we must
    not reward.

    Rules:
      * answer None            -> True (e.g. unrelated probes; behaviour graded
                                  separately)
      * answer looks like CODE-> pred must contain that exact code token
      * otherwise              -> normalized whole-answer containment
    """
    if answer is None:
        return True
    a = answer.strip()
    if not a:
        return True
    codes = extract_codes(a)
    if codes:
        return codes[0] in extract_codes(pred)
    return normalize(a) in normalize(pred)


def grade_multi(pred: str, answers: list[str]) -> bool:
    """True if every expected code appears (for ordered-operation answers)."""
    pcodes = set(extract_codes(pred))
    return all(extract_codes(a)[0] in pcodes for a in answers if extract_codes(a))


# ---- policy / instruction grading -----------------------------------------
# Instruction-regime answers are short and semantic ("no", "logical",
# "rope_offset"). Naive containment is unsafe: normalize("no") would match
# inside "not listed". These graders are token-boundary aware.

# A *policy refusal* is syntactically distinct from an arbitrary negated
# clause. "it is not a LoRA" is a denial of fact; "do not / must not / never /
# not allowed" is a prohibition; a leading bare "no"/"no," is a verdict.
_PROHIB = re.compile(
    r"\b(never|cannot|can't|must not|mustn't|should not|shouldn't|"
    r"do not|don't|not allowed|not permitted|not ok|not okay|refuse|"
    r"not (possible|feasible|recommended|correct)|unable)\b", re.I)
_AFF = re.compile(r"\b(yes|sure|ok|okay|correct|allowed|permitted|go ahead)\b", re.I)


def _tokens(s: str) -> list[str]:
    return re.findall(r"[a-z0-9_]+", s.lower())


def grade_yesno(pred: str, want_no: bool, topic: list[str] | None = None) -> bool:
    """Grade a policy question expecting yes or no.

    Uses prohibition/verdict syntax rather than bare negation. A copular denial
    ("it is not a LoRA") counts only when it is *about the proposal*, i.e. one
    of ``topic`` keyword stems appears in the same opening window — otherwise
    a factual denial ("the machine is not listed") would be misread.

    ``topic`` should be the content words of the proposal under discussion.
    """
    toks = _tokens(pred)
    head = " ".join(toks[:14])
    if not toks:
        return False
    leading_verdict = bool(re.match(r"^\s*no\s*(?:[.,;:!?—–-]|$)", pred, re.I))
    prohibits = bool(_PROHIB.search(head))
    affirms = bool(_AFF.search(head))

    copular_denial = False
    if re.search(r"\b(is|are|was|were)\s+not\b", head, re.I):
        if not topic:
            copular_denial = True
        else:
            stems = [t.lower() for t in topic]
            copular_denial = any(s in head for s in stems)

    looks_like_no = leading_verdict or prohibits or copular_denial
    if want_no:
        return looks_like_no and not (affirms and not prohibits)
    return affirms


def grade_term(pred: str, term: str) -> bool:
    """Grade a technical term answer using token-sequence containment.

    Multi-word and underscore terms are matched as whole tokens so that
    'rope_offset' does not match 'offset' and 'logical' does not match
    'logically' incorrectly as a different term.
    """
    pt = _tokens(pred)
    tt = _tokens(term)
    if not tt:
        return False
    n = len(tt)
    for i in range(len(pt) - n + 1):
        if pt[i:i + n] == tt:
            return True
    # allow intra-token substring only for longer distinctive terms
    if n == 1 and len(tt[0]) >= 5:
        return tt[0] in pt
    return False


def grade_instruction(pred: str, answer: str, kind: str, topic: list[str] | None = None) -> bool:
    """Dispatch grading for instruction-regime probes.

    Routing is by the *answer shape*, because a category can contain both
    yes/no questions ("is this a LoRA?" -> "no") and term questions ("which
    class?" -> "SyntheticKVCache"):

    * answer is yes/no  -> yes/no policy grading (``topic`` disambiguates
      copular denial)
    * numeric-ish answer-> token grading (e.g. "one", "E409", "sev1")
    * else              -> technical-term token grading for tool/recall/naming
      kinds, ordinary containment otherwise
    """
    a = answer.strip().lower()
    if a in ("no", "not", "never", "yes"):
        return grade_yesno(pred, want_no=(a != "yes"), topic=topic)

    # MCP tools are namespaced as mcp__<server>__<tool>. Accept either the bare
    # tool name or the fully-qualified form (the teacher sometimes emits the
    # qualified name and the compiled model the bare one, or vice versa).
    if kind in ("tool_select", "tool"):
        pred_bare = re.sub(r"mcp__[A-Za-z0-9_]+__", "", pred)
        ans_bare = re.sub(r"mcp__[A-Za-z0-9_]+__", "", answer)
        if grade_term(pred_bare, ans_bare) or grade_term(pred, ans_bare):
            return True

    # Tool names, rule ids, codes, severity labels: strict token match.
    term_kinds = ("recall", "naming", "convention", "tool_select", "ordering",
                  "error_policy", "revision", "style", "escalation", "tool")
    if kind in term_kinds:
        # allow the answer to appear as an exact token, with light variants
        if grade_term(pred, answer):
            return True
        # tolerant fallbacks for natural phrasings
        alt = {
            "backticks": ["backticks", "backtick", "`"],
            "precondition": ["precondition", "pre-condition", "satisfy"],
            "once": ["once", "one retry", "at most once", "1"],
            "immediately": ["immediately", "right away", "at once"],
            "one": ["one", "1", "single"],
            "decision": ["decision", "decide", "verdict"],
            "rule": ["rule", "rule id", "rule_id"],
            "prime": ["prime"],
        }.get(answer.strip().lower(), [])
        head = " ".join(_tokens(pred)[:20])
        return any(x.lower() in head or x.lower() in pred.lower() for x in alt)

    return normalize(answer) in normalize(pred)


def greedy_generate(model, tok, prompt: str, cache=None, max_tokens: int = 24):
    tokens = tok.encode(prompt)
    cur = mx.array([tokens])
    lg = model(cur, cache=cache)
    mx.eval(lg)
    out_tokens = []
    for _ in range(max_tokens):
        nxt = int(mx.argmax(lg[0, -1]).item())
        out_tokens.append(nxt)
        if tok.eos_token_id is not None and nxt == tok.eos_token_id:
            break
        lg = model(mx.array([[nxt]]), cache=cache)
        mx.eval(lg)
    return tok.decode(out_tokens), np.array(lg[0, -1].astype(mx.float32), copy=False)


def kl_divergence(p_logits: np.ndarray, q_logits: np.ndarray) -> float:
    p = p_logits.astype(np.float64)
    q = q_logits.astype(np.float64)
    p = p - p.max()
    q = q - q.max()
    pp = np.exp(p); pp /= pp.sum()
    pq = np.exp(q); pq /= pq.sum()
    return float(np.sum(pp * (np.log(pp + 1e-12) - np.log(pq + 1e-12))))


def topk_overlap(a: np.ndarray, b: np.ndarray, k: int = 10) -> float:
    ta = set(np.argsort(a)[-k:].tolist())
    tb = set(np.argsort(b)[-k:].tolist())
    return len(ta & tb) / k


def answer_token_rank(logits: np.ndarray, tok, answer: str) -> int:
    """Rank of the first token of `answer` in the next-token logits."""
    if not answer:
        return 0
    ids = tok.encode(" " + answer)
    if not ids:
        return 0
    tid = ids[0]
    order = np.argsort(logits)[::-1]
    pos = np.where(order == tid)[0]
    return int(pos[0]) if len(pos) else -1
