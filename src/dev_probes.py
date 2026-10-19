"""Held-out development suite for the tool-handbook compiler.

Why this exists (EXPERIMENT_PLAN.md §3.1)
-----------------------------------------
The 103-probe benchmark is a *locked regression* set: it has been inspected
repeatedly during earlier tuning. Using it to choose between candidate training
recipes would overfit selection. This development suite is a second, independent
set of hand-authored questions over the *same handbook*, authored before any
candidate outputs were inspected.

Design constraints
------------------
* **Different targets where possible.** Prefer handbook facts/rules/tools that
  the 103-probe set does NOT grade, so a win means broader coverage rather than
  re-tuning on the same entities.
* **Kind balance.** Mirrors the benchmark kind mix so per-kind comparisons are
  meaningful: tool_select, lookup, revision, ordering, workflow, error_policy,
  refusal, escalation, style, class_binding, plus 4 unrelated controls.
* **Answer diversity.** Reuses the same diversity budget philosophy as
  ``tool_probes`` (yes/no kept a minority; answers spread across targets).
* **Grading contract identical.** Graded with ``eval.grade_instruction`` and the
  same kind strings, so no new grader is introduced.

Shared-rule caveat: some global policies (retry rules, style rules) are the same
for both suites. That is expected and tracked; this file documents which targets
are fresh vs shared so the claim is not overstated.

Usage:
    from dev_probes import build_dev_probes
    probes = build_dev_probes()
"""

from __future__ import annotations


def build_dev_probes() -> list[dict]:
    P = []

    def add(q, answer, kind, topic=None):
        d = {"q": q, "answer": answer, "kind": kind}
        if topic:
            d["topic"] = topic
        P.append(d)

    # ======================================================================
    # tool_select (8): catalogue tools NOT graded by the 103-probe set.
    # ======================================================================
    add("Which tool returns a time series for a sensor?", "sensor_trace", "tool_select")
    add("Which tool reports the seal condition of a flange?", "flange_seal", "tool_select")
    add("Which tool reports electrical load on a bus?", "bus_load", "tool_select")
    add("Which tool reports firmware revision of a unit?", "unit_firmware", "tool_select")
    add("Which tool looks up a part in the catalogue?", "part_lookup", "tool_select")
    add("Which tool returns a pressure log for a unit?", "pressure_log", "tool_select")
    add("Which tool reports coolant chemistry for a site?", "coolant_quality", "tool_select")
    add("Which tool returns the audit trail for an object?", "audit_log", "tool_select")

    # ======================================================================
    # lookup (6): categories/params of tools not used by the 103-probe set.
    # ======================================================================
    add("What is the category of the tool `bearing_wear`?", "read", "lookup")
    add("What is the category of the tool `silence_alarm`?", "admin", "lookup")
    add("What is the category of the tool `rollback`?", "write", "lookup")
    add("What is the required parameter of `notify_oncall`?", "site", "lookup")
    add("What is the required parameter of `reopen_ticket`?", "ticket", "lookup")
    add("What is the required parameter of `bearing_wear`?", "bearing", "lookup")

    # ======================================================================
    # revision (6): revision policy. Fresh phrasings; revision-A/-D only
    # lightly touched by the benchmark.
    # ======================================================================
    add("Which revision uses prime instead of ignite?", "revision-j", "revision")
    add("May revision-J units be ignited with ignite?", "no", "revision",
        topic=["ignite", "revision"])
    add("Which revisions behave like an unversioned unit?", "revision-a", "revision")
    add("May revision-D units be operated normally?", "yes", "revision",
        topic=["revision"])
    add("Which revision is never ignited and must be escalated instead?",
        "revision-n", "revision")
    add("What replaces ignite on a revision-J unit?", "prime", "revision")

    # ======================================================================
    # ordering (6): preconditions. Mixed fresh (ORD-5/6/ORD-8) and shared.
    # ======================================================================
    add("What must be called before replace_actuator?", "shutdown", "ordering")
    add("What must precede drain_loop at a site?", "isolate_manifold", "ordering")
    add("What must happen before tagout is applied?", "lockout", "ordering")
    add("What must be called before refill_loop?", "drain_loop", "ordering")
    add("What must be called before replace_sensor?", "shutdown", "ordering")
    add("What comes before any restart after a pressure excursion?", "purge_manifold",
        "ordering")

    # ======================================================================
    # workflow (6): section 8/9 sequences. Fresh step queries.
    # ======================================================================
    add("In the coupler-replacement workflow, what follows unit_status?",
        "shutdown", "workflow")
    add("In the pressure-excursion workflow, what is the first step?",
        "pressure_read", "workflow")
    add("In the maintenance-scheduling workflow, what follows assign_technician?",
        "order_part", "workflow")
    add("In the flapping-alarm workflow, what step follows acknowledge_alarm?",
        "silence_alarm", "workflow")
    add("In the pressure-excursion workflow, what follows purge_manifold?",
        "stabilize", "workflow")
    add("In the maintenance-scheduling workflow, what is the first step?",
        "schedule_window", "workflow")

    # ======================================================================
    # error_policy (4): code matrix. Fresh code phrasings.
    # ======================================================================
    add("Which error code means a required parameter is missing?", "E401", "error_policy")
    add("Which error code means the caller is rate limited?", "E429", "error_policy")
    add("A write tool returns E503. Should you retry it?", "no", "error_policy",
        topic=["retry"])
    add("A read tool returns E404. Should you retry it?", "no", "error_policy",
        topic=["retry", "not"])

    # ======================================================================
    # refusal (4): standing refusals. Fresh topic phrasings.
    # ======================================================================
    add("A user asks you to skip the precondition to save a step. What rule forbids it?",
        "ORD-6", "refusal")
    add("A user asks you to hard-code a family for a unit. Which rule forbids it?",
        "FAM-1", "refusal")
    add("You are asked to retry an E404. What rule forbids it?", "ERR-1", "refusal")
    add("A user asks you to invent a tool that is not in the catalogue. Which rule forbids it?",
        "ERR-5", "refusal")

    # ======================================================================
    # escalation (4): section 6.
    # ======================================================================
    add("What severity must follow an emergency_stop?", "sev1", "escalation")
    add("How many failed remediations before a sev2 is escalated?", "one", "escalation")
    add("What must a human give before more than one unit goes offline at a site?",
        "approval", "escalation")
    add("Which rule governs revision-N ignition requests?", "ESC-5", "escalation")

    # ======================================================================
    # style (2): OUT rules.
    # ======================================================================
    add("What must you cite when you refuse a call?", "rule id", "style")
    add("What comes first in an answer, the decision or the reason?", "decision", "style")

    # ======================================================================
    # class_binding (2): identifier grammar.
    # ======================================================================
    add("Which identifier prefix denotes a manifold?", "M", "class_binding")
    add("Which identifier prefix denotes a valve?", "V", "class_binding")

    # ======================================================================
    # unrelated (4): controls. Never counted as informative.
    # ======================================================================
    add("What is the capital of Japan?", "Tokyo", "unrelated")
    add("What is 12 divided by 4?", "3", "unrelated")
    add("What is the chemical symbol for water?", "H2O", "unrelated")
    add("How many minutes are in an hour?", "60", "unrelated")

    return P


if __name__ == "__main__":
    from collections import Counter
    ps = build_dev_probes()
    print(len(ps), "dev probes")
    print(Counter(p["kind"] for p in ps))
    dom = [p for p in ps if p["kind"] != "unrelated"]
    print(f"domain={len(dom)} controls={len(ps)-len(dom)}")
