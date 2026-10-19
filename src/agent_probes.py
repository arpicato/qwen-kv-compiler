"""Deterministic probe suite for the realistic agent-prompt regime.

Target: ``prompts/agent_resident.txt`` (~26k resident tokens: guidelines +
AGENTS.md + <mcp_instructions> + <available_skills> + 131 GitHub MCP tool
schemas). This suite tests whether a *compressed* prefix still supplies the
facts/rules/tools/skills the full prompt supplies.

Design (EXPERIMENT_PLAN §3, adapted):
* **Deterministic grading only.** No LLM judge. Every probe has a canonical
  answer token graded by ``eval.grade_instruction`` with the existing kind
  strings (so the evaluator needs no new grader).
* **Grounded in the prompt.** Every answer appears verbatim (or as a
  normalised form) in the system prompt; verified by ``--audit``.
* **Probe types** map to the new regime:
    - fact/rule (kind ``lookup``/``style``): a policy the guidelines state.
    - tool_select: which tool handles a request -> exact tool name.
    - argument (kind ``lookup``): a required argument of a named tool.
    - skill_select (kind ``tool_select``): which skill matches -> skill name.
* **Held-out discipline.** Authored before any compiled candidate for this
  regime exists.
"""

from __future__ import annotations


def build_agent_probes() -> list[dict]:
    P = []

    def add(q, answer, kind, topic=None):
        d = {"q": q, "answer": answer, "kind": kind}
        if topic:
            d["topic"] = topic
        P.append(d)

    # ======================================================================
    # Guidelines / AGENTS.md facts (lookup, style) -- 12
    # ======================================================================
    add("Which package manager do Node services use?", "pnpm", "lookup")
    add("Which package manager do Python services use?", "uv", "lookup")
    add("What command runs the full test suite across the repo?", "pnpm -r test",
        "lookup")
    add("Which Python linter must pass before commit?", "ruff", "lookup")
    add("Which JavaScript linter must pass before commit?", "eslint", "lookup")
    add("Where do secrets live in this repo?", "infra/secrets/", "lookup")
    add("How are the secrets in infra/secrets/ encrypted?", "sops", "lookup")
    add("What commit-message convention is required?", "conventional commits",
        "style")
    add("May database migrations be edited after they are merged?", "no", "style")
    add("How many logical changes belong in one pull request?", "one", "style")
    add("Which directory holds architecture decision records?", "docs/adr/",
        "lookup")
    add("What should you do if a test fails in a service you did not touch?",
        "report it", "style")

    # ======================================================================
    # MCP server facts (<mcp_instructions>) -- 5
    # ======================================================================
    add("Which GitHub organisation is the GitHub MCP server scoped to?",
        "acme-platform", "lookup")
    add("Is the postgres MCP server read-only or read-write?", "read-only",
        "lookup")
    add("How long may a postgres MCP query run?", "30 seconds", "lookup")
    add("Which projects does the sentry MCP server cover?", "production",
        "lookup")
    add("Should you force-push when using the GitHub server?", "no", "lookup")

    # ======================================================================
    # Skill selection (<available_skills>) -- 6
    # ======================================================================
    add("Which skill covers pre-release verification for a service?",
        "release-checklist", "tool_select")
    add("Which skill guides triage and postmortem for a production incident?",
        "incident-response", "tool_select")
    add("Which skill authors and reviews a reversible database migration?",
        "db-migration", "tool_select")
    add("Which skill reviews API changes for backwards compatibility?",
        "api-review", "tool_select")
    add("Which skill audits cloud spend for a service?", "cost-audit",
        "tool_select")
    add("Which skill produces onboarding steps for a new engineer?",
        "onboarding-guide", "tool_select")

    # ======================================================================
    # Tool selection (131 GitHub MCP tools) -- 8
    # ======================================================================
    add("Which tool creates a new issue in a repository?", "create_issue",
        "tool_select")
    add("Which tool creates a pull request?", "create_pull_request",
        "tool_select")
    add("Which tool creates a new branch?", "create_branch", "tool_select")
    add("Which tool adds a comment to an issue?", "add_issue_comment",
        "tool_select")
    add("Which tool forks a repository?", "fork_repository", "tool_select")
    add("Which tool creates a gist?", "create_gist", "tool_select")
    add("Which tool lists workflow runs for a repository?", "actions_list",
        "tool_select")
    add("Which tool deletes a repository?", "delete_repository", "tool_select")

    # ======================================================================
    # Argument binding (required args of named tools) -- 6
    # ======================================================================
    add("For the tool `create_issue`, name one required argument.", "title",
        "lookup")
    add("For the tool `create_branch`, what is the required branch argument?",
        "branch", "lookup")
    add("For the tool `fork_repository`, which argument names the target owner?",
        "owner", "lookup")
    add("For the tool `create_pull_request`, which argument names the source "
        "branch?", "head", "lookup")

    # ======================================================================
    # unrelated controls -- 4 (never counted as informative)
    # ======================================================================
    add("What is the capital of Spain?", "Madrid", "unrelated")
    add("What is 8 times 7?", "56", "unrelated")
    add("What is the chemical symbol for iron?", "Fe", "unrelated")
    add("How many months are in a year?", "12", "unrelated")

    return P


def build_agent_probes_extended() -> list[dict]:
    """Additional hand-written probes (realistic paraphrase, not verbatim)."""
    P = []

    def add(q, answer, kind, topic=None):
        d = {"q": q, "answer": answer, "kind": kind}
        if topic:
            d["topic"] = topic
        P.append(d)

    # ---- guidelines / tone / safety -- 10 ----
    add("Should the assistant guess a URL it is not sure about?", "no", "style")
    add("Is the assistant allowed to use emojis without being asked?", "no",
        "style")
    add("How long should a normal answer be, in lines?", "4", "style")
    add("What markdown flavour should responses use?", "github-flavored",
        "style")
    add("Should the assistant add explanatory comments to code by default?",
        "no", "style")
    add("Where should bugs in the opencode tool be reported?", "github", "lookup")
    add("Which command shows help for the CLI tool?", "/help", "lookup")
    add("Should the assistant summarise what it did after finishing a task?",
        "no", "style")
    add("Should the assistant commit changes on its own?", "no", "style")
    add("What does the assistant use to answer questions about opencode itself?",
        "webfetch", "lookup")

    # ---- AGENTS.md / repo facts -- 12 ----
    add("What file gives each deployable service its configuration?", "service.yaml",
        "lookup")
    add("Which directory must never have generated files edited by hand?",
        "infra/.gen/", "lookup")
    add("Are architecture decision records editable after they are written?",
        "no", "style")
    add("How large should a pull request diff ideally stay, in lines?",
        "400", "style")
    add("Which channel owns cross-service breakage?", "#platform", "lookup")
    add("What prefix does a feature commit use?", "feat", "style")
    add("What prefix does a bug-fix commit use?", "fix", "style")
    add("What prefix does a maintenance commit use?", "chore", "style")
    add("Do Python services use pnpm?", "no", "style")
    add("Which tool runs tests for a single named service?", "pnpm --filter",
        "lookup")
    add("Name one directory that holds terraform modules.", "infra/", "lookup")
    add("What kind of change must every database migration support?",
        "rollback", "style")

    # ---- MCP instructions -- 5 ----
    add("Can the postgres MCP server run DDL statements?", "no", "style")
    add("Before a postgres query returning over 1000 rows, what must you run?",
        "explain", "lookup")
    add("What scope do GitHub write tools require?", "repo", "lookup")
    add("How many sentry issue lookups are allowed per minute?", "100", "lookup")
    add("Should you push directly to a protected branch?", "no", "style")

    # ---- skills -- 4 ----
    add("Which skill would you use to plan a staged rollout?", "release-checklist",
        "tool_select")
    add("Which skill handles postmortems?", "incident-response", "tool_select")
    add("Which skill covers a backfill strategy?", "db-migration", "tool_select")
    add("Which skill checks gRPC compatibility?", "api-review", "tool_select")

    # ---- GitHub tool facts -- 8 ----
    add("Which tool updates a single file's contents in a repository?",
        "create_or_update_file", "tool_select")
    add("Which tool removes a repository?", "delete_repository", "tool_select")
    add("Which tool retrieves details about a specific Actions run?",
        "actions_get", "tool_select")
    add("Which tool assigns a copilot agent to an issue?",
        "assign_copilot_to_issue", "tool_select")
    add("Which tool creates a repository ruleset?", "create_repository_ruleset",
        "tool_select")
    add("Which tool dismisses a notification?", "dismiss_notification",
        "tool_select")
    add("Which tool lists the user's notifications?", "list_notifications",
        "tool_select")
    add("Which tool searches code across repositories?", "search_code",
        "tool_select")

    return P


def build_agent_probes_full() -> list[dict]:
    return build_agent_probes() + build_agent_probes_extended()



def audit(probes: list[dict], system_text: str) -> list[str]:
    """Return probes whose canonical answer is NOT present in the prompt."""
    import re
    low = system_text.lower()
    missing = []
    for p in probes:
        if p["kind"] == "unrelated":
            continue
        a = p["answer"].lower()
        # normalise a few multiword answers
        variants = {a, a.replace(" ", ""), a.replace("/", ""), a.replace(" ", "-")}
        if not any(v in low for v in variants):
            missing.append(p["q"])
    return missing


if __name__ == "__main__":
    import os
    import sys
    from collections import Counter
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
    ps = build_agent_probes()
    print(len(ps), "agent probes")
    print(Counter(p["kind"] for p in ps))
    path = os.path.join(os.path.dirname(__file__), "..", "prompts", "agent_resident.txt")
    text = open(path).read()
    miss = audit(ps, text)
    print("answers not found verbatim in prompt:", len(miss))
    for q in miss:
        print("   MISS:", q)
