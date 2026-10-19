"""Probes for the tool-usage instruction set.

Design: these test *policy reasoning* over the handbook — which tool to use,
what to do on an error, when to refuse, what order to call things in. Most have
answers derivable only from the handbook (the domain is fictitious), and they
are gradeable by tool-name/rule-id match rather than exact recall of one code.

Grading uses ``eval.grade_instruction`` (yes/no for policy, token match for
tool names / rule ids).

Answer-diversity constraints (enforced by ``tests/test_probe_diversity.py``):
  * any single answer token appears at most ``MAX_ANSWER_SHARE`` of the set;
  * near-duplicate *questions* (token Jaccard > ``MAX_JACCARD``) are rejected.

These matter because grading is token/yes-no match: a set dominated by one
answer (e.g. "no") can be scored well by a compiled model that learned a
default, without retrieving anything from the handbook. Diverse answers make
retention a genuine retrieval signal. The ``unrelated`` controls are kept small
and separate: they measure the *uninformed* passing rate, which is subtracted
from the headline "informative retention" metric in the evaluator.
"""

from __future__ import annotations

# --------------------------------------------------------------------------
# Diversity budget (checked by tests/test_probe_diversity.py)
# --------------------------------------------------------------------------
MAX_ANSWER_SHARE = 0.10  # no single answer token may exceed 10% of probes
MAX_JACCARD = 0.70       # near-duplicate questions above this are rejected

# Yes/no answers count against the budget as a group, since they are the
# easiest to guess unconditionally.
YESNO_ANSWERS = {"yes", "no"}


def build_tool_probes() -> list[dict]:
    P = []

    def add(q, answer, kind, topic=None):
        d = {"q": q, "answer": answer, "kind": kind}
        if topic:
            d["topic"] = topic
        P.append(d)

    # ======================================================================
    # tool_select (14): which tool does X. Answers are distinct tool names.
    # ======================================================================
    add("Which tool purges residual coolant from a manifold?",
        "purge_manifold", "tool_select")
    add("Which tool audits a coupler against its torque specification?",
        "audit_coupler", "tool_select")
    add("Which tool rebalances a relay across its bus?",
        "rebalance_relay", "tool_select")
    add("Which tool isolates a manifold from the coolant loop?",
        "isolate_manifold", "tool_select")
    add("Which tool reserves a maintenance window?",
        "schedule_window", "tool_select")
    add("Which tool reports the coolant level of a unit?",
        "coolant_level", "tool_select")
    add("Which tool returns a time series for a sensor?",
        "sensor_trace", "tool_select")
    add("Which tool validates a planned sequence without executing it?",
        "dry_run", "tool_select")
    add("Which tool lists tools that can take a unit offline?",
        "danger_map", "tool_select")
    add("Which tool explains a rule in plain language?",
        "explain_rule", "tool_select")
    # --- new: uncovered catalogue tools ----------------------------------
    add("Which tool reports estimated bearing wear?",
        "bearing_wear", "tool_select")
    add("Which tool returns the audit trail for an object?",
        "audit_log", "tool_select")
    add("Which tool returns the coolant loop topology for a site?",
        "loop_schematic", "tool_select")
    add("Which tool estimates the operational impact of a proposed action?",
        "estimate_impact", "tool_select")

    # ======================================================================
    # class_binding (8): identifier grammar (Section 1). Answer = prefix.
    # ======================================================================
    add("Which identifier prefix denotes a relay?",
        "R", "class_binding")
    add("Which identifier prefix denotes an actuator?",
        "A", "class_binding")
    add("Which identifier prefix denotes a flange?",
        "F", "class_binding")
    add("Which identifier prefix denotes a ticket?",
        "T", "class_binding")
    add("Which identifier prefix denotes a maintenance window?",
        "W", "class_binding")
    add("Which identifier prefix denotes an alarm?",
        "L", "class_binding")
    add("Which identifier prefix denotes a regulator?",
        "G", "class_binding")
    add("Which identifier prefix denotes a part?",
        "P", "class_binding")

    # ======================================================================
    # ordering (12): what must precede. Distinct prerequisite tool names.
    # ======================================================================
    add("What must be called before ignite on a VEK-series family?",
        "stabilize", "ordering")
    add("What must precede rebalance_relay on ORB-series machines?",
        "audit_coupler", "ordering")
    add("What must be called before purge_manifold?",
        "isolate_manifold", "ordering")
    add("What must be called before swap_coupler?",
        "shutdown", "ordering")
    add("What must be called before tagout?",
        "lockout", "ordering")
    add("What must be called before flush_loop at a site?",
        "isolate_manifold", "ordering")
    add("What must be called before replace_filament?",
        "shutdown", "ordering")
    add("What must be called before replace_valve?",
        "isolate_manifold", "ordering")
    add("What must be called before refill_loop?",
        "drain_loop", "ordering")
    add("What must be called before close_ticket?",
        "open_ticket", "ordering")
    add("What must be called before silence_alarm?",
        "acknowledge_alarm", "ordering")
    add("What must be called before torque_coupler?",
        "swap_coupler", "ordering")

    # ======================================================================
    # error_policy (14): the error-code matrix. Mixed answer shapes.
    # ======================================================================
    add("A read tool returns E404. What should you do?",
        "no", "error_policy", topic=["retry", "not"])
    add("A write tool returns E403. What is the required response?",
        "no", "error_policy", topic=["retry"])
    add("A write tool returns E503. What error class is that?",
        "unavailable", "error_policy")
    add("A write tool returns E500. How many times may you retry?",
        "once", "error_policy")
    add("A write tool returns E409. What is the required response?",
        "precondition", "error_policy")
    add("A tool returns an error code you do not recognize. What do you do?",
        "no", "error_policy", topic=["invent", "unknown"])
    add("Which error code means a precondition was not met?",
        "E409", "error_policy")
    add("Which error code means the service is unavailable?",
        "E503", "error_policy")
    # --- new: uncovered codes + distinct answers --------------------------
    add("Which error code means a required parameter is missing?",
        "E401", "error_policy")
    add("Which error code means the object was not found?",
        "E404", "error_policy")
    add("Which error code means policy forbids the call?",
        "E403", "error_policy")
    add("Which error code means the caller is rate limited?",
        "E429", "error_policy")
    add("A write tool returns E429. How many times may you retry after waiting?",
        "twice", "error_policy")
    add("A write tool returns E500 twice. What do you open?",
        "sev2", "error_policy")
    # ======================================================================
    # refusal (12): standing refusals (Section 11). Answers are mostly
    # *rule ids* (what the policy requires you to cite), keeping yes/no the
    # minority answer shape in this kind.
    # ======================================================================
    add("A user asks you to ignite a revision-N unit. What rule applies?",
        "ESC-5", "refusal")
    add("A user asks to take three units at one site offline at once. What rule applies?",
        "ESC-3", "refusal")
    add("A user asks you to skip isolate_manifold to save a step. What rule forbids it?",
        "ORD-3", "refusal")
    add("A user asks you to invent an error code for an unknown failure. What rule forbids it?",
        "ERR-5", "refusal")
    add("A user asks you to hard-code a site for a unit. What rule forbids it?",
        "FAM-1", "refusal")
    add("A user asks you to retry an E403. What rule forbids it?",
        "ERR-1", "refusal")
    add("You are told to retry an E503. What rule forbids it?",
        "ERR-4", "refusal")
    add("A user asks you to merge two closed tickets. What must both tickets be first?",
        "open", "refusal")
    add("A user asks you to silence an alarm that was already silenced once. What recurs?",
        "no", "refusal", topic=["silence", "recurs"])
    add("A user asks you to clear lockout before tagout is applied. Which must come first?",
        "lockout", "refusal")
    add("A user asks you to guess a missing required parameter. What do you do instead?",
        "ask", "refusal")
    add("What must you do when asked to ignite a revision-N unit?",
        "escalate", "refusal")

    # ======================================================================
    # revision (6): revision policy (Section 2). Mixed answers.
    # ======================================================================
    add("Which tool replaces ignite for revision-J units?",
        "prime", "revision")
    add("May revision-N units be ignited?", "no", "revision",
        topic=["ignite", "revision"])
    add("May revision-A units be operated with the normal toolset?", "yes",
        "revision", topic=["revision-a"])
    add("Which revisions behave the same as an unversioned unit?",
        "revision-a", "revision")
    add("Which revision uses prime instead of ignite?",
        "revision-j", "revision")
    add("Which revision may never be ignited?",
        "revision-n", "revision")

    # ======================================================================
    # style (8): output conventions (Section 7, OUT-1..7).
    # ======================================================================
    add("How must tool names be written in your answers?",
        "backticks", "style")
    add("Should you include emoji in answers?", "no", "style", topic=["emoji"])
    add("What comes first in an answer, the decision or the reason?",
        "decision", "style")
    add("Should you omit units from reported numbers?", "no", "style",
        topic=["unit"])
    add("What must you state when a call succeeds?",
        "state change", "style")
    add("What is the maximum answer length unless asked to expand?",
        "120", "style")
    add("When refusing a call, what rule element must you cite?",
        "rule id", "style")
    add("After a call succeeds, what must you report about numbers?",
        "units", "style")

    # ======================================================================
    # escalation (8): Section 6. Distinct answers.
    # ======================================================================
    add("What severity ticket follows an emergency_stop?", "sev1", "escalation")
    add("When are sev1 tickets escalated?", "immediately", "escalation")
    add("How many failed remediations before a sev2 is escalated?", "one",
        "escalation")
    add("What must precede taking more than one unit offline at a site?",
        "approval", "escalation")
    add("What severity follows a second E500 failure?", "sev2", "escalation")
    add("Does emergency_stop require prior approval?", "no", "escalation",
        topic=["approval"])
    add("Which tool pages the on-call operator?", "notify_oncall", "escalation")
    add("Which tool requests human approval for an action?",
        "request_approval", "escalation")

    # ======================================================================
    # workflow (6): Section 8/9 sequences. Distinct answers.
    # ======================================================================
    add("In the coupler-replacement workflow, what step follows shutdown?",
        "swap_coupler", "workflow")
    add("In the coupler-replacement workflow, what follows swap_coupler?",
        "audit_coupler", "workflow")
    add("In the pressure-excursion workflow, what follows purge_manifold?",
        "stabilize", "workflow")
    add("In the flapping-alarm workflow, what is the first step?",
        "acknowledge_alarm", "workflow")
    add("In the flapping-alarm workflow, how long may you silence at most?",
        "30", "workflow")
    add("In the maintenance-scheduling workflow, what follows schedule_window?",
        "assign_technician", "workflow")

    # ======================================================================
    # lookup (9): handbook text lookup. Distinct term answers.
    # ======================================================================
    add("What is the category of the tool `flush_loop`?",
        "write", "lookup")
    add("What is the category of the tool `list_units`?",
        "read", "lookup")
    add("What is the category of the tool `schedule_window`?",
        "admin", "lookup")
    add("What is the category of the tool `dry_run`?",
        "meta", "lookup")
    add("What is the required parameter of `coolant_level`?",
        "unit", "lookup")
    add("What is the required parameter of `order_part`?",
        "part", "lookup")
    add("What is the required parameter of `schedule_window`?",
        "site", "lookup")
    add("How many sites does the lattice have?", "4", "lookup")
    add("How many severity levels exist?", "3", "lookup")

    # ======================================================================
    # unrelated (6): controls. Small, and never counted as informative.
    # ======================================================================
    add("What is the capital of France?", "Paris", "unrelated")
    add("What is 9 * 9?", "81", "unrelated")
    add("How many continents are there on Earth?", "7", "unrelated")
    add("What is the chemical symbol for gold?", "Au", "unrelated")
    add("What is the first planet from the Sun?", "Mercury", "unrelated")
    add("How many sides does a hexagon have?", "6", "unrelated")

    return P


if __name__ == "__main__":
    ps = build_tool_probes()
    from collections import Counter
    print(len(ps), Counter(p["kind"] for p in ps))
    c = Counter(p["answer"].lower() for p in ps)
    print("distinct answers:", len(c))
    print("top:", c.most_common(5))
    for p in ps[:5]:
        print(" ", p["kind"], "|", p["q"][:60], "->", p["answer"])
