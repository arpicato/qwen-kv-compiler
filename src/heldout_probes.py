"""Held-out evaluation suite #2 for the tool-handbook compiler (wave-2+).

Why a *second* held-out set
---------------------------
`dev_probes` (52) was authored before wave-1 candidate outputs and used to
select the wave-1 recipe, so it is partly "seen" for selection. This suite is
authored before the wave-2 candidates are trained or inspected.

Anti-overfitting rule (IMPORTANT)
---------------------------------
The wave-2 diagnosis is that numeral/quantifier payloads are the residual
failure mode. It would be easy -- and wrong -- to write probes for the four
known failing facts. This suite therefore:

* **Excludes** the four known failing facts and their exact targets
  (see `_KNOWN_FAILING_TARGETS`): retry-count `twice`, multi-unit `approval`,
  `audit_coupler` as the swap_coupler successor, and the 30-minute silence bound.
* Samples numeric/table facts from the handbook by *structural coverage*
  (severities, families, sites, code table, workflow bounds) chosen for shape,
  not for being the known misses.
* Prefers fresh tools unused by either other suite.

If a numeral-coverage training change moves *this* suite, that is evidence it
generalises; if it only moved the four known probes, it would be overfitting.

Usage:
    from heldout_probes import build_heldout_probes
"""

from __future__ import annotations

# Facts the wave-2 analysis identified as the compiled failures on the 103
# benchmark. This suite must not grade these exact targets.
_KNOWN_FAILING_TARGETS = {
    "twice",          # E429 retry count
    "approval",       # multi-unit offline precedent
    "audit_coupler",  # successor of swap_coupler
    "30",             # silence-alarm minute bound
}


def build_heldout_probes() -> list[dict]:
    P = []

    def add(q, answer, kind, topic=None):
        d = {"q": q, "answer": answer, "kind": kind}
        if topic:
            d["topic"] = topic
        P.append(d)

    # ======================================================================
    # tool_select (8): middle-of-catalogue tools unused by either suite.
    # ======================================================================
    add("Which tool lists the units at a site?", "site_inventory", "tool_select")
    add("Which tool returns the maintenance history of a unit?", "unit_history",
        "tool_select")
    add("Which tool balances the load across relays?", "rebalance_relay",
        "tool_select")
    add("Which tool seats a gasket on a flange?", "seat_gasket", "tool_select")
    add("Which tool inspects a nozzle for wear?", "inspect_nozzle", "tool_select")
    add("Which tool exports a compliance report?", "export_report", "tool_select")
    add("Which tool shows the roster of on-call technicians?", "technician_roster",
        "tool_select")
    add("Which tool merges two tickets into one?", "merge_tickets", "tool_select")

    # ======================================================================
    # lookup (8): categories/required params of fresh tools + table shapes.
    # ======================================================================
    add("What is the category of the tool `unit_history`?", "read", "lookup")
    add("What is the category of the tool `seat_gasket`?", "write", "lookup")
    add("What is the category of the tool `approve_window`?", "admin", "lookup")
    add("What is the required parameter of `inspect_nozzle`?", "object", "lookup")
    add("What is the required parameter of `merge_tickets`?", "ticket", "lookup")
    add("What is the required parameter of `export_report`?", "site", "lookup")
    add("Other than the unit, how many families does the catalogue define?",
        "6", "lookup")
    add("Which revision letter behaves like an unversioned unit?", "a", "revision")

    # ======================================================================
    # NUMERAL / TABLE facts (10): the residual failure *shape*. Chosen for
    # structural coverage of the handbook's numeric content -- NOT the four
    # known failing facts (excluded in _KNOWN_FAILING_TARGETS).
    # ======================================================================
    # severity ladder (ESC-1/ESC-2)
    add("An E500 fails a second time. What severity is opened?", "sev2",
        "escalation")
    add("Does opening a sev1 ticket require asking the user first?", "no",
        "escalation")
    add("Which rule makes sev1 escalation immediate?", "ESC-1", "escalation")
    add("How many failed remediations are allowed before a sev2 escalates?",
        "one", "escalation")
    # error-code table -> severities (different codes than the known miss)
    add("An E503 maps to which severity?", "sev1", "escalation")
    add("Which error code means a policy forbids the call?", "E403", "error_policy")
    add("Which error code means a precondition is unmet?", "E409", "error_policy")
    # structural counts (handbook lists)
    add("How many tool categories are listed in the catalogue?", "4", "lookup")
    add("How many revisions are defined?", "4", "lookup")
    add("How many families are defined in the catalogue?", "6", "lookup")

    # ======================================================================
    # ordering (6): preconditions of fresh tools / fresh rule targets.
    # ======================================================================
    add("What must be called before inspect_weld?", "tagout", "ordering")
    add("What precedes clear_lockout?", "lockout", "ordering")
    add("What must be called before depressurize?", "isolate_manifold", "ordering")
    add("What must be called before calibrate_sensor?", "shutdown", "ordering")
    add("What must be called before replace_regulator?", "isolate_manifold",
        "ordering")
    add("What must be called before reopen_manifold?", "isolate_manifold",
        "ordering")

    # ======================================================================
    # workflow (6): fresh step queries (NOT the swap_coupler successor).
    # ======================================================================
    add("In the coupler-replacement workflow, what is the first step?",
        "unit_status", "workflow")
    add("In the maintenance-scheduling workflow, what follows order_part?",
        "approve_window", "workflow")
    add("In the pressure-excursion workflow, what follows stabilize?",
        "resume_unit", "workflow")
    add("In the coupler-replacement workflow, what follows shutdown?",
        "swap_coupler", "workflow")
    add("In the flapping-alarm workflow, what follows acknowledge_alarm?",
        "silence_alarm", "workflow")
    add("Which tool confirms a window is approved before work starts?",
        "approve_window", "workflow")

    # ======================================================================
    # revision (4)
    # ======================================================================
    add("Which revision must never be ignited?", "revision-n", "revision")
    add("On a revision-J unit, what replaces ignite?", "prime", "revision")
    add("May revision-A units be operated like an unversioned unit?", "yes",
        "revision")
    add("May revision-J units be ignited with the normal ignite tool?", "no",
        "revision")

    # ======================================================================
    # refusal (4): standing refusals, fresh rule targets.
    # ======================================================================
    add("A user asks you to retry an E404. What rule forbids it?", "ERR-1",
        "refusal")
    add("A user asks you to guess a missing parameter. Which rule forbids it?",
        "E401", "refusal")
    add("A user asks you to ignite a revision-N unit. Which rule governs it?",
        "ESC-5", "refusal")
    add("A user asks you to skip a precondition. What rule forbids it?", "ORD-3",
        "refusal")

    # ======================================================================
    # style (2)
    # ======================================================================
    add("What must you cite when a call is refused?", "rule id", "style")
    add("What comes first, the decision or the reason?", "decision", "style")

    # ======================================================================
    # class_binding (2)
    # ======================================================================
    add("Which identifier prefix denotes a pump?", "P", "class_binding")
    add("Which identifier prefix denotes a gasket?", "G", "class_binding")

    # ======================================================================
    # unrelated (4): controls, never counted as informative.
    # ======================================================================
    add("What is the capital of Italy?", "Rome", "unrelated")
    add("What is 9 plus 6?", "15", "unrelated")
    add("What is the chemical symbol for silver?", "Ag", "unrelated")
    add("How many days are in a week?", "7", "unrelated")

    return P


if __name__ == "__main__":
    import os
    import sys
    from collections import Counter
    sys.path.insert(0, os.path.dirname(__file__))
    ps = build_heldout_probes()
    print(len(ps), "held-out probes")
    print(Counter(p["kind"] for p in ps))
    dom = [p for p in ps if p["kind"] != "unrelated"]
    print(f"domain={len(dom)} controls={len(ps) - len(dom)}")
    from tool_probes import build_tool_probes
    from dev_probes import build_dev_probes
    seen = {p["q"] for p in build_tool_probes()} | {p["q"] for p in build_dev_probes()}
    dupe = [p["q"] for p in ps if p["q"] in seen]
    print("exact-question overlaps with existing suites:", len(dupe))
    for q in dupe:
        print("   DUP:", q)
    # anti-overfit guard
    leak = [p["q"] for p in ps
            if str(p["answer"]).strip().lower() in _KNOWN_FAILING_TARGETS]
    print("probes whose target is a KNOWN failing fact (must be 0):", len(leak))
    for q in leak:
        print("   LEAK:", q)
