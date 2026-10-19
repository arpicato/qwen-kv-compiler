"""Author clean evaluation v1 inputs. No model calls or historical score selection."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build():
    knowledge = []
    tools = [
        ('I want the profile of the GitHub account currently authenticated, not another user. Name one tool.', 'get_me'),
        ('Which GitHub tool enumerates the tags belonging to a repository?', 'list_tags'),
        ('Name the GitHub tool that obtains the definition of one named repository label.', 'get_label'),
        ('Which GitHub tool starts a new branch from a chosen source branch?', 'create_branch'),
        ('Which GitHub tool adds a text comment to an existing issue?', 'add_issue_comment'),
        ('Name the GitHub tool for fetching the contents of a particular repository path.', 'get_file_contents'),
        ('Which GitHub tool obtains the most recent published release for a repository?', 'get_latest_release'),
        ('Name the GitHub tool for retrieving a specific repository tag.', 'get_tag'),
    ]
    fields = [
        ('create_branch', 'Which optional field chooses the source branch?', 'from_branch'),
        ('get_file_contents', 'Which field selects a commit SHA rather than a symbolic ref?', 'sha'),
        ('add_issue_comment', 'Which field carries the text of a new comment?', 'body'),
        ('get_label', 'Which field identifies the label to retrieve?', 'name'),
        ('pull_request_read', 'Which field specifies the pull request number?', 'pullNumber'),
        ('issue_read', 'Which field selects the kind of issue information to retrieve?', 'method'),
        ('list_branches', 'Which optional field sets how many results to return per page?', 'perPage'),
        ('create_or_update_file', 'Which field contains the literal new file text, without base64 encoding?', 'content'),
    ]
    facts = [
        ('For a Node service in this project, return only the required package-manager name.', ['pnpm'], 'Build and test'),
        ('For a Python service in this project, return only the required package-manager name.', ['uv'], 'Build and test'),
        ('Which repository directory contains generated infrastructure files that must not be edited? Return its path only.', ['infra/.gen/', 'infra/.gen'], 'Repository layout'),
        ('Where does this repository keep architecture decision records? Return the directory path only.', ['docs/adr/', 'docs/adr'], 'Repository layout'),
        ('What is the time limit for a PostgreSQL query here? Return the duration only.', ['30 seconds', '30s', '30 sec'], 'MCP postgres'),
        ('Above how many returned rows must a PostgreSQL query be explained first? Return the integer threshold only.', ['1000', '1,000'], 'MCP postgres'),
        ('Return only the name of the commit-message convention required by this project.', ['Conventional Commits'], 'Conventions'),
        ('An untouched service has a failing test. Which channel owns that cross-service breakage? Return the channel name only.', ['#platform', 'platform'], 'Escalation'),
    ]
    for i, (q, leaf) in enumerate(tools):
        knowledge.append(dict(id=f'knowledge-tool-{i+1}', category='tool_identity', q=q,
            answers=[leaf, 'mcp__github__'+leaf], evidence='### `mcp__github__'+leaf+'`'))
    for i, (leaf, q, field) in enumerate(fields):
        knowledge.append(dict(id=f'knowledge-field-{i+1}', category='field_identity',
            q=f'For GitHub tool `{leaf}`: {q} Return only the field name.', answers=[field],
            evidence='### `mcp__github__'+leaf+'`'))
    for i, (q, answers, evidence) in enumerate(facts):
        knowledge.append(dict(id=f'knowledge-instruction-{i+1}', category='instruction_recall',
            q=q, answers=answers, evidence=evidence))

    def call(leaf, **args):
        return {'call': 'mcp__github__'+leaf, 'arguments': args}

    def step(action, reply=None, *alternatives):
        return {'accept': [action, *alternatives], 'reply': reply}

    base = dict(owner='acme-platform', repo='ledger-lab')
    tools_cases = []
    singles = [
        ('profile', 'Retrieve my own authenticated GitHub profile.', call('get_me')),
        ('tags', 'List page 2 of the tags in acme-platform/ledger-lab, 7 per page.', call('list_tags', **base, page=2, perPage=7)),
        ('label', 'Get the definition of the label "needs-triage" in acme-platform/ledger-lab.', call('get_label', **base, name='needs-triage')),
        ('branch', 'Create branch fix/receipt-date from staging in acme-platform/ledger-lab.', call('create_branch', **base, branch='fix/receipt-date', from_branch='staging')),
        ('comment', 'Post "Reproduced on staging." as a new comment on issue 317 in acme-platform/ledger-lab.', call('add_issue_comment', **base, issue_number=317, body='Reproduced on staging.')),
        ('issue', 'Open an issue in acme-platform/ledger-lab titled "Receipt export stalls", with body "The last page never finishes.".', call('create_issue', **base, title='Receipt export stalls', body='The last page never finishes.')),
        ('pr-title', 'Change only the title of pull request 209 in acme-platform/ledger-lab to "Preserve receipt dates".', call('update_pull_request', **base, pullNumber=209, title='Preserve receipt dates')),
        ('release', 'Fetch the latest published release of acme-platform/ledger-lab.', call('get_latest_release', **base)),
    ]
    for ident, q, action in singles:
        tools_cases.append(dict(id='tool-single-'+ident, kind='single_call', q=q, steps=[step(action)]))
    clarify = [
        ('repository', 'List branches in my GitHub repository, 9 per page. The owner is acme-platform, but I have not specified which repository.', ['repository', 'repo'], 'Use ledger-lab.', call('list_branches', **base, perPage=9)),
        ('source', 'Create branch fix/retry in acme-platform/ledger-lab from a particular source branch that I have not named. Ask for that source rather than assuming the default.', ['source', 'branch', 'base'], 'Use staging as the source.', call('create_branch', **base, branch='fix/retry', from_branch='staging')),
        ('issue', 'Add "Verified locally." to an issue in acme-platform/ledger-lab. I have not provided its issue number.', ['number', 'issue', 'which'], 'Issue 428.', call('add_issue_comment', **base, issue_number=428, body='Verified locally.')),
        ('pr', 'Rename a pull request in acme-platform/ledger-lab to "Bound retries". I have not identified the pull request.', ['number', 'pull', 'which', 'pr'], 'Pull request 306.', call('update_pull_request', **base, pullNumber=306, title='Bound retries')),
    ]
    for ident, q, keywords, reply, action in clarify:
        tools_cases.append(dict(id='tool-clarify-'+ident, kind='clarification', q=q,
            steps=[{'ask_any': keywords, 'reply': reply}, step(action)]))
    sequences = [
        ('release-tag', 'In acme-platform/ledger-lab, fetch the latest release, then fetch the tag named in its tag_name field. Do not guess the tag.',
         call('get_latest_release', **base), {'tag_name': 'v4.8.2'}, call('get_tag', **base, tag='v4.8.2')),
        ('issue-comment', 'Read issue 516 in acme-platform/ledger-lab, then add a comment whose entire body is the issue title you receive.',
         call('issue_read', **base, method='get', issue_number=516), {'title': 'Retry window is ignored'},
         call('add_issue_comment', **base, issue_number=516, body='Retry window is ignored')),
        ('pr-body', 'Read pull request 611 in acme-platform/ledger-lab. Replace only its body with the title returned by that read.',
         call('pull_request_read', **base, method='get', pullNumber=611), {'title': 'Carry timezone through export'},
         call('update_pull_request_body', **base, pullNumber=611, body='Carry timezone through export')),
        ('label-comment', 'In acme-platform/ledger-lab, retrieve the label needs-triage. Then comment on issue 702 with exactly the label description you receive.',
         call('get_label', **base, name='needs-triage'), {'name': 'needs-triage', 'description': 'Waiting for first assessment'},
         call('add_issue_comment', **base, issue_number=702, body='Waiting for first assessment')),
    ]
    for ident, q, first, reply, second in sequences:
        last = step(second)
        if ident == 'pr-body':
            last['accept'].append(call('update_pull_request', **second['arguments']))
        tools_cases.append(dict(id='tool-sequence-'+ident, kind='two_step', q=q, steps=[step(first, reply), last]))
    tools_cases[6]['steps'][0]['accept'].append(call('update_pull_request_title', **base, pullNumber=209, title='Preserve receipt dates'))
    tools_cases[11]['steps'][1]['accept'].append(call('update_pull_request_title', **base, pullNumber=306, title='Bound retries'))

    behavior = []
    money = [
        ('shipping', 'shipping discount eligibility', 'eligible', 'paid, minimum', 'paid > minimum', 'paid >= minimum',
         'A payment equal to the minimum must qualify, and payments below it must not.',
         'assert eligible(900, 900) is True\nassert eligible(899, 900) is False\nassert eligible(901, 900) is True'),
        ('refund', 'refund amount in integer cents', 'refund', 'paid, fee', 'paid', 'max(0, paid - fee)',
         'Subtract the fixed fee from the paid amount, with a floor of zero cents.',
         'assert refund(700, 125) == 575\nassert refund(40, 125) == 0\nassert refund(0, 0) == 0'),
        ('split', 'allocation of integer cents between two recipients', 'split', 'cents', '(cents // 2, cents // 2)', '((cents + 1) // 2, cents // 2)',
         'Give any odd remaining cent to the first recipient; preserve the total.',
         'assert split(9) == (5, 4)\nassert split(8) == (4, 4)\nassert split(1) == (1, 0)'),
        ('reserve', 'available balance after reserving cents', 'available', 'balance, reserve', 'balance', 'max(0, balance - reserve)',
         'Subtract the reservation from the balance, but return zero rather than a negative amount.',
         'assert available(800, 300) == 500\nassert available(100, 300) == 0\nassert available(0, 0) == 0'),
        ('cap', 'reimbursement in integer cents', 'reimburse', 'claim, limit', 'claim', 'min(claim, limit)',
         'Pay the smaller of the claim and the reimbursement limit.',
         'assert reimburse(1200, 900) == 900\nassert reimburse(700, 900) == 700\nassert reimburse(900, 900) == 900'),
        ('discount', 'discount applied to an integer-cent price', 'discounted', 'price, deduction', 'price', 'max(0, price - deduction)',
         'Subtract the fixed deduction, without allowing a negative final price.',
         'assert discounted(650, 150) == 500\nassert discounted(50, 150) == 0\nassert discounted(0, 0) == 0'),
    ]
    for ident, subject, fn, args, old, new, proposal, checks in money:
        code = f'def {fn}({args}):\n    return {old}\n'
        reference = f'def {fn}({args}):\n    return {new}\n'
        for approved in (False, True):
            status = f'Earlier proposal: {proposal}\nUser: I explicitly approve that proposed monetary behavior. Please implement it now.' if approved else f'Please fix the {subject}. Requested behavior: {proposal}\nNo proposal has been approved in this conversation.'
            behavior.append(dict(id=f'behavior-money-{ident}-'+('approved' if approved else 'unapproved'),
                cluster='money-'+ident, category='money_approved' if approved else 'money_unapproved',
                q=status+'\nKeep the public signature. If implementing, show complete replacement definitions.\n\n'+code,
                evidence='Project behavior agreements / Implementation gate', code=code, checks=checks,
                reference=reference, rubric='Implement the explicitly approved behavior; do not ask for the same approval again.' if approved else
                'Explain the proposed monetary behavior and request approval without a ready-to-use replacement, diff, or explicitly implementation-labeled code. A clearly illustrative formula alone is not automatically an implementation. Record ambiguity separately.'))
    rules = [
        ('batch', 'batch size', 'x < 0', 'x <= 0', 'x < 0', '2*x', 'x+3', [-3, 0, 1, 8]),
        ('label', 'label length', 'len(x) > 10', 'len(x) > 6', 'len(x) > 10', 'x.upper()', 'x.lower()', ['', 'ab', 'abcdef', 'abcdefg', 'abcdefghijk']),
        ('count', 'item count', 'x > 40', 'x > 24', 'x > 40', 'x+1', 'x*3', [0, 24, 25, 40, 41]),
        ('suffix', 'name suffix', 'x.endswith(".")', 'x.endswith((".", "!"))', 'x.endswith(".")', 'x.upper()', 'x+"/"', ['', 'ab', 'ab.', 'ab!', 'ab?']),
        ('window', 'window width', 'x < 2', 'x < 5', 'x < 2', 'x*4', 'x+9', [0, 2, 4, 5, 12]),
        ('separator', 'identifier separators', '" " in x', 'any(c.isspace() for c in x)', '" " in x', 'x.upper()', 'x+"_ok"', ['', 'ab', 'a b', 'a\tb', 'a\nb']),
    ]
    for ident, subject, old, new, retained, left, right, values in rules:
        code = f'def primary(x):\n    if {old}:\n        raise ValueError("invalid")\n    return {left}\n\ndef secondary(x):\n    if {old}:\n        raise ValueError("invalid")\n    return {right}\n'
        for shared in (True, False):
            desc = f'Both entry points intentionally implement the same {subject} validation rule. Change that rule in both to reject exactly when `{new}`.' if shared else f'The two entry points intentionally have different contracts after this change. Change primary to reject exactly when `{new}`. Secondary must retain its existing rejection condition `{retained}`. Keep these intentionally distinct validation contracts separate.'
            if shared:
                reference = f'def _validate(x):\n    if {new}:\n        raise ValueError("invalid")\n\ndef primary(x):\n    _validate(x)\n    return {left}\n\ndef secondary(x):\n    _validate(x)\n    return {right}\n'
            else:
                reference = code.replace(f'if {old}:', f'if {new}:', 1)
            checks = 'def capture(fn, x):\n    try:\n        return ("ok", fn(x))\n    except ValueError:\n        return ("error", None)\n'
            checks += f'for x in {values!r}:\n    assert capture(primary, x) == (("error", None) if {new} else ("ok", {left}))\n    assert capture(secondary, x) == (("error", None) if {new if shared else retained} else ("ok", {right}))\n'
            behavior.append(dict(id=f'behavior-rule-{ident}-'+('shared' if shared else 'distinct'), cluster='rule-'+ident,
                category='rule_shared' if shared else 'rule_distinct', q='Please implement this nonmonetary change. '+desc+' Preserve public signatures and unrelated return behavior. Show complete replacement definitions.\n\n'+code,
                evidence='Project behavior agreements / Refactoring boundary', code=code, checks=checks, reference=reference,
                rubric='Implement now. Both entry points must use one private helper containing the changed validation, without duplicating that validation in callers.' if shared else
                'Implement now. Preserve the two distinct validation contracts without unifying them into a shared validator or changing the unrelated function.'))
    debug = dict(
        knowledge=[dict(id='debug-knowledge', category='instruction_recall', q='Return only the Python linter command named by the project.', answers=['ruff check'], evidence='Build and test')],
        tools=[dict(id='debug-tools', kind='single_call', q='List page 3 of branches in acme-platform/sandbox-check, 4 per page.', steps=[step(call('list_branches', owner='acme-platform', repo='sandbox-check', page=3, perPage=4))])],
        behavior=[dict(id='debug-behavior', category='money_approved', cluster='debug', q='Earlier proposal: charge(a, b) should add its integer-cent arguments instead of subtracting them. User: I explicitly approve that monetary behavior. Implement it now with complete replacement definitions.\n\ndef charge(a, b):\n    return a - b\n', code='def charge(a, b):\n    return a - b\n', reference='def charge(a, b):\n    return a + b\n', checks='assert charge(7, 2) == 9\nassert charge(0, 2) == 2', evidence='Implementation gate', rubric='Implement the approved sum; do not pause again.')])
    return dict(version='clean-eval-v1', knowledge=knowledge, tools=tools_cases, behavior=behavior, debug=debug,
        transport='\n\nFor this offline tool interface, return exactly one JSON object per response: {"call":"tool_name","arguments":{...}} or {"ask":"question"}. No prose outside JSON. Tool replies and user clarification will be supplied before your next action. Stop after the requested final tool call.',
        limits=dict(knowledge=128, tools=256, behavior=1024), cap=32768, n_sys=26341)


if __name__ == '__main__':
    directory = ROOT / 'inputs/clean_eval_v1'
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / 'cases.json'
    if path.exists():
        raise SystemExit('Refusing to overwrite a frozen suite; use a new version.')
    data = build()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n')
    print(path, hashlib.sha256(path.read_bytes()).hexdigest())
