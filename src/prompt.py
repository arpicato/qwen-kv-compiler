"""Single source of truth for chat-template construction.

The model is a *thinking* model: without an explicit empty thinking block it
spends the whole token budget inside ``<think>``. Historically the capture path
and the evaluation path built the user turn differently (one omitted the
no-think block), so the optimizer was calibrated on a query distribution that
never occurred at inference time.

Everything that builds a prompt MUST come from here.
"""

from __future__ import annotations

NO_THINK = "<think>\n\n</think>\n\n"
IM_START = "<|im_start|>"
IM_END = "<|im_end|>\n"


def system_block(body: str) -> str:
    """The system message containing the (large) manual."""
    return f"{IM_START}system\n{body}{IM_END}"


def user_turn(question: str, *, think: bool = False) -> str:
    """User message + assistant prefix.

    ``think=False`` (default) forces the empty thinking block, matching the
    evaluation-time behaviour.
    """
    pre = f"{IM_START}user\n{question}{IM_END}{IM_START}assistant\n"
    return pre + (NO_THINK if not think else "<think>\n")


def assistant_turn(answer: str) -> str:
    """A canonical assistant answer, used for teacher-forced trajectories."""
    return f"{answer}{IM_END}"
