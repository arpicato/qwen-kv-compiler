"""Synthetic task cases authored from the resident prompt, not model outputs."""
import json


TRANSPORT = '''\nThis is an offline simulation. Do not contact services. For your next action return one JSON object only:
{"call":"fully_qualified_tool_name","arguments":{...}} to use a connected tool;
{"ask":"question"} if required information is missing;
{"answer":"text"} for advice without a tool call.
Use the connected tools and repository rules from your system instructions. Do not invent missing identifiers. Stop after the next action.'''


def call(name, args):
    return {'call': 'mcp__github__' + name, 'arguments': args}


def cases():
    repo = {'owner': 'acme-platform', 'repo': 'widget'}
    out = []

    def add(id, kind, q, actions):
        out.append({'id': id, 'kind': kind, 'q': q, 'steps': actions})

    def step(name, args, alternatives=(), reply=None):
        return {'accept': [call(name, args), *alternatives], 'reply': reply}

    singles = [
        ('pr-body', 'Set PR #42 description in acme-platform/widget to "Release notes updated". Leave the title alone.', 'update_pull_request_body', dict(repo, pullNumber=42, body='Release notes updated'), [call('update_pull_request', dict(repo, pullNumber=42, body='Release notes updated'))]),
        ('pr-title', 'Rename PR #18 in acme-platform/widget to "Handle empty batches". Change nothing else.', 'update_pull_request_title', dict(repo, pullNumber=18, title='Handle empty batches'), [call('update_pull_request', dict(repo, pullNumber=18, title='Handle empty batches'))]),
        ('pr-ready', 'Mark PR #23 in acme-platform/widget ready for review, leaving its content unchanged.', 'update_pull_request_draft_state', dict(repo, pullNumber=23, draft=False), [call('update_pull_request', dict(repo, pullNumber=23, draft=False))]),
        ('pr-close', 'Close PR #36 in acme-platform/widget without merging it.', 'update_pull_request_state', dict(repo, pullNumber=36, state='closed'), [call('update_pull_request', dict(repo, pullNumber=36, state='closed'))]),
        ('pr-create', 'Open a draft PR in acme-platform/widget from fix/timeout into release with title "Bound retries" and description "Avoid infinite waits".', 'create_pull_request', dict(repo, head='fix/timeout', base='release', title='Bound retries', body='Avoid infinite waits', draft=True), []),
        ('branch', 'Create branch docs/setup in acme-platform/widget from release, not the default branch.', 'create_branch', dict(repo, branch='docs/setup', from_branch='release'), []),
        ('issue-create', 'File an issue in acme-platform/widget titled "Cache stalls" with body "Occurs after reconnect".', 'create_issue', dict(repo, title='Cache stalls', body='Occurs after reconnect'), []),
        ('issue-body', 'Replace the description of issue #31 in acme-platform/widget with "Fixed in nightly".', 'update_issue_body', dict(repo, issue_number=31, body='Fixed in nightly'), []),
        ('issue-title', 'Rename issue #57 in acme-platform/widget to "Reconnect freezes".', 'update_issue_title', dict(repo, issue_number=57, title='Reconnect freezes'), []),
        ('comment-edit', 'Edit conversation comment 882 in acme-platform/widget to read "Retested successfully". This is not a review comment.', 'update_issue_comment', dict(repo, comment_id=882, body='Retested successfully'), []),
        ('tag', 'Retrieve the git tag object for v2.7 in acme-platform/widget, not its release notes.', 'get_tag', dict(repo, tag='v2.7'), []),
        ('release', 'Retrieve the release notes for v2.7 in acme-platform/widget, not the git tag object.', 'get_release_by_tag', dict(repo, tag='v2.7'), []),
        ('gist', 'Fetch the stored content of gist a91bc0. Do not list gists.', 'get_gist', {'gist_id': 'a91bc0'}, []),
        ('advisory', 'Fetch global advisory GHSA-abcd-2345-6789, not repository alerts.', 'get_global_security_advisory', {'ghsaId': 'GHSA-abcd-2345-6789'}, []),
        ('file', 'Read src/queue.py in acme-platform/widget at refs/heads/release.', 'get_file_contents', dict(repo, path='src/queue.py', ref='refs/heads/release'), []),
        ('blame', 'Find who last changed lines 20 through 35 of src/queue.py in acme-platform/widget at release.', 'get_file_blame', dict(repo, path='src/queue.py', ref='release', start_line=20, end_line=35), []),
        ('code-alert', 'Inspect code-scanning alert 17 in acme-platform/widget, not a dependency alert.', 'get_code_scanning_alert', dict(repo, alertNumber=17), []),
        ('dependency-alert', 'Inspect Dependabot alert 17 in acme-platform/widget, not a code-scanning alert.', 'get_dependabot_alert', dict(repo, alertNumber=17), []),
        ('team', 'List the usernames on team runtime in the acme-platform organization.', 'get_team_members', {'org': 'acme-platform', 'team_slug': 'runtime'}, []),
        ('failed-logs', 'Return the actual content of only failed-job logs for workflow run 709 in acme-platform/widget. Show the last 25 lines.', 'get_job_logs', dict(repo, run_id=709, failed_only=True, return_content=True, tail_lines=25), []),
    ]
    for id, q, name, args, alternatives in singles:
        if name in ('create_issue', 'update_issue_body', 'update_issue_title'):
            alternatives.append(call('issue_write', dict(args, method='create' if name == 'create_issue' else 'update')))
        add(id, 'single_call', q, [step(name, args, alternatives)])

    clarifications = [
        ('missing-repo', 'Set PR #42 description to "Ready" in acme-platform. I have not specified which repository.', ['repo', 'repository'], 'The repository is widget.', 'update_pull_request_body', dict(repo, pullNumber=42, body='Ready'), [call('update_pull_request', dict(repo, pullNumber=42, body='Ready'))]),
        ('missing-pr', 'Set a PR description in acme-platform/widget to "Ready". I have not provided its number.', ['number', 'which pr', 'which pull'], 'PR number 42.', 'update_pull_request_body', dict(repo, pullNumber=42, body='Ready'), [call('update_pull_request', dict(repo, pullNumber=42, body='Ready'))]),
        ('missing-gist', 'Fetch a particular gist for me. I have not provided its ID.', ['id', 'which gist'], 'The gist ID is a91bc0.', 'get_gist', {'gist_id': 'a91bc0'}, []),
        ('missing-tag', 'Fetch a specific git tag in acme-platform/widget. I have not specified which tag.', ['tag', 'version'], 'Use tag v2.7.', 'get_tag', dict(repo, tag='v2.7'), []),
        ('missing-comment', 'Change a conversation comment in acme-platform/widget to "Retested". I have not supplied its identifier.', ['id', 'which comment'], 'Its comment ID is 882.', 'update_issue_comment', dict(repo, comment_id=882, body='Retested'), []),
        ('missing-branch', 'Create a branch from release in acme-platform/widget. I have not chosen the new name.', ['name', 'branch'], 'Name it fix/reconnect.', 'create_branch', dict(repo, branch='fix/reconnect', from_branch='release'), []),
        ('missing-team', 'List members of a specific team in acme-platform. I have not said which team.', ['team', 'slug'], 'The team slug is runtime.', 'get_team_members', {'org': 'acme-platform', 'team_slug': 'runtime'}, []),
        ('missing-advisory', 'Fetch a particular global security advisory. I have not given you its identifier.', ['id', 'ghsa', 'which advisory'], 'Use GHSA-abcd-2345-6789.', 'get_global_security_advisory', {'ghsaId': 'GHSA-abcd-2345-6789'}, []),
    ]
    for id, q, words, reply, name, args, alternatives in clarifications:
        add(id, 'clarification', q, [{'ask_any': words, 'reply': reply}, step(name, args, alternatives)])

    for n, path in enumerate(('config/a.txt', 'config/b.txt', 'docs/status.txt')):
        sha = ('a', 'b', 'c')[n] * 40
        add(f'file-update-{n}', 'two_step', f'Update existing file {path} on branch maintenance in acme-platform/widget to exactly "enabled\\n" (enabled followed by a newline), commit message "chore: enable". Retrieve its current SHA first.', [
            step('get_file_contents', dict(repo, path=path, ref='maintenance'),
                 [call('get_file_contents', dict(repo, path=path, ref='refs/heads/maintenance'))], reply={'sha': sha, 'content': 'disabled\n'}),
            step('create_or_update_file', dict(repo, path=path, branch='maintenance', content='enabled\n', message='chore: enable', sha=sha))])
    for n, number in enumerate((41, 52, 63)):
        thread = f'PRRT_mock_{n}'
        add(f'resolve-{n}', 'two_step', f'In acme-platform/widget PR #{number}, retrieve review threads, then resolve the single thread returned. Do not post a comment.', [
            step('pull_request_read', dict(repo, pullNumber=number, method='get_review_comments'), reply={'threads': [{'id': thread, 'isResolved': False}]}),
            step('resolve_review_thread', {'threadID': thread},
                 [call('pull_request_review_write', dict(repo, pullNumber=number, method='resolve_thread', threadId=thread))])])

    policies = [
        ('node', 'For a Node service here, give the package manager and the exact command to test only service billing. Do not run it.', [['pnpm'], ['pnpm --filter billing test']], ['use npm', 'yarn ']),
        ('python', 'Which package manager should I use for Python services in this repository? Answer only, do not run anything.', [['uv']], ['pip ', 'poetry']),
        ('generated', 'I need to change generated Terraform under infra/.gen/. What should you do under the repository rules? Advice only.', [['not edit', "don't edit", 'do not edit', 'never edit', 'avoid editing'], ['generated', 'infra/.gen/']], []),
        ('migration', 'An old database migration needs changing. State the repository constraints before proceeding; do not edit anything.', [['append-only', 'append only', 'new migration'], ['reversible', 'rollback']], []),
        ('unrelated-failure', 'Tests failed in an untouched service. Under our repository rules, who owns this and should you quietly fix it? Advice only.', [['platform'], ['report', 'escalat'], ['not', "don't", 'never', 'no,']], []),
        ('lint', 'Before committing a change spanning Node and Python services, which two lint commands are required? Advice only.', [['pnpm lint'], ['ruff check']], []),
    ]
    for id, q, groups, forbidden in policies:
        add(id, 'policy_advice', q, [{'answer_all': groups, 'forbidden': forbidden}])
    assert len(out) == 40 and len({c['id'] for c in out}) == 40
    return out


def debug_cases():
    return [
        {'id': 'debug-direct', 'kind': 'debug', 'q': 'Fetch git tag debug-v1 in acme-platform/sandbox.', 'steps': [{'accept': [call('get_tag', {'owner': 'acme-platform', 'repo': 'sandbox', 'tag': 'debug-v1'})]}]},
        {'id': 'debug-ask', 'kind': 'debug', 'q': 'Fetch a gist. Its ID is not provided.', 'steps': [{'ask_any': ['id', 'which gist'], 'reply': 'Its ID is debug123.'}, {'accept': [call('get_gist', {'gist_id': 'debug123'})]}]},
    ]


if __name__ == '__main__':
    print(json.dumps({'transport': TRANSPORT, 'debug': debug_cases(), 'test': cases()}, indent=2))
