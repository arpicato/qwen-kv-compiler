"""Author v2 before generation: distinct operations, paired policies, frozen mocks."""
import json
from pathlib import Path
from textwrap import indent

ROOT = Path(__file__).resolve().parents[1]


def build():
    knowledge = []
    tools = [
        ('Retrieve the authenticated account, rather than a user named in the question.', 'get_me'),
        ('Get one repository label by its name.', 'get_label'),
        ('Retrieve one repository tag by its name.', 'get_tag'),
        ('Retrieve the most recent published release in a repository.', 'get_latest_release'),
        ('Retrieve the release attached to a given tag.', 'get_release_by_tag'),
        ('List the releases in a repository.', 'list_releases'),
        ('List the tags in a repository.', 'list_tags'),
        ('List repository branches with pagination.', 'list_branches'),
        ('Create a new repository branch from a specified source branch.', 'create_branch'),
        ('Get details of one commit identified by SHA.', 'get_commit'),
        ('List commits with an author and date-range filter.', 'list_commits'),
        ('Read a file or directory from a repository.', 'get_file_contents'),
        ('Search for source code matching a query.', 'search_code'),
        ('Search for repositories matching a query.', 'search_repositories'),
        ('Search for GitHub users matching a query.', 'search_users'),
        ('Search for issues matching a query.', 'search_issues'),
        ('Read details or comments of a specific issue.', 'issue_read'),
        ('Read details, files or review comments of a specific pull request.', 'pull_request_read'),
        ('Add a new text comment to an issue.', 'add_issue_comment'),
        ('Get the issue types supported by an organization.', 'list_issue_types'),
    ]
    for i, (q, leaf) in enumerate(tools):
        knowledge.append(dict(id=f'k-tool-{i+1:02}', category='tool_identity', cluster=leaf,
            q='Within the configured GitHub MCP catalog, which tool serves this purpose? '+q+
              ' Return only one tool identifier, bare or fully qualified; no explanation.',
            answers=[leaf, 'mcp__github__'+leaf], evidence='### `mcp__github__'+leaf+'`'))
    fields = [
        ('create_branch', 'optional source branch, rather than the new branch name', 'from_branch'),
        ('get_file_contents', 'symbolic reference such as refs/heads/main', 'ref'),
        ('get_file_contents', 'optional commit SHA that takes precedence over ref', 'sha'),
        ('get_label', 'label identifier', 'name'),
        ('get_tag', 'tag identifier', 'tag'),
        ('get_release_by_tag', 'tag identifying the release', 'tag'),
        ('list_commits', 'filter by author', 'author'),
        ('list_commits', 'filter for one file path', 'path'),
        ('list_commits', 'start of the timestamp range', 'since'),
        ('list_commits', 'end of the timestamp range', 'until'),
        ('list_pull_requests', 'target branch filter', 'base'),
        ('list_pull_requests', 'source branch filter', 'head'),
        ('pull_request_read', 'pull request number', 'pullNumber'),
        ('pull_request_read', 'cursor after which to fetch review-comment threads', 'after'),
        ('issue_read', 'issue number', 'issue_number'),
        ('add_issue_comment', 'text of the new comment', 'body'),
        ('create_or_update_file', 'literal file contents', 'content'),
        ('create_or_update_file', 'blob SHA of the file being replaced', 'sha'),
        ('actions_list', 'number of returned results per page', 'perPage'),
        ('search_repositories', 'repository search expression', 'query'),
    ]
    for i, (leaf, meaning, field) in enumerate(fields):
        knowledge.append(dict(id=f'k-field-{i+1:02}', category='field_identity', cluster=leaf,
            q=f'In the configured GitHub MCP tool `{leaf}`, which argument represents the {meaning}? Return only the exact field identifier; no explanation.',
            answers=[field], evidence='### `mcp__github__'+leaf+'`'))
    facts = [
        ('Package manager for Node services', ['pnpm'], 'Build and test'),
        ('Package manager for Python services', ['uv'], 'Build and test'),
        ('Full recursive test command for Node services', ['pnpm -r test'], 'Build and test'),
        ('Lint command for the Node workspace', ['pnpm lint'], 'Build and test'),
        ('Python lint command', ['ruff check'], 'Build and test'),
        ('Required commit-message convention', ['Conventional Commits'], 'Conventions'),
        ('Per-service configuration file name', ['service.yaml'], 'Repository layout'),
        ('Root directory containing deployable services', ['services/', 'services'], 'Repository layout'),
        ('Directory containing generated infrastructure files that must not be edited', ['infra/.gen/', 'infra/.gen'], 'Repository layout'),
        ('Directory containing architecture decision records', ['docs/adr/', 'docs/adr'], 'Repository layout'),
        ('Gitignored directory for encrypted secrets', ['infra/secrets/', 'infra/secrets'], 'Conventions'),
        ('Secrets encryption system named by the project', ['SOPS'], 'Conventions'),
        ('Channel owning cross-service test breakage', ['#platform', 'platform'], 'Escalation'),
        ('Organization to which the GitHub server is scoped', ['acme-platform'], 'MCP github'),
        ('OAuth scope required for GitHub write tools', ['repo'], 'MCP github'),
        ('Tool to use rather than pushing to a protected branch', ['create_pull_request', 'mcp__github__create_pull_request'], 'MCP github'),
        ('Time limit for PostgreSQL queries', ['30 seconds', '30s', '30 sec'], 'MCP postgres'),
        ('Row-count threshold above which a PostgreSQL query needs explain first', ['1000', '1,000'], 'MCP postgres'),
        ('Sentry issue-lookup rate limit', ['100/minute', '100 per minute', '100/min', '100 requests per minute'], 'MCP sentry'),
        ('Project environment accessible through Sentry', ['production', 'production projects', 'production projects only'], 'MCP sentry'),
    ]
    for i, (fact, answers, evidence) in enumerate(facts):
        knowledge.append(dict(id=f'k-fact-{i+1:02}', category='instruction_recall', cluster=evidence,
            q=f'According to this project\'s instructions: {fact}? Return only the requested name, path, command, number or short value; no explanation.',
            answers=answers, evidence=evidence))

    def call(leaf, **args):
        return dict(call='mcp__github__'+leaf, arguments=args)

    def step(action, reply=None, alternatives=()):
        return dict(accept=[action, *alternatives], reply=reply)

    b = dict(owner='acme-platform', repo='audit-box')
    specs = [
        ('self', 'Fetch my authenticated GitHub account.', 'get_me', {}),
        ('labels', 'Retrieve label "risk-reviewed" in acme-platform/audit-box.', 'get_label', dict(**b, name='risk-reviewed')),
        ('tag', 'Fetch tag v6.3.1 in acme-platform/audit-box.', 'get_tag', dict(**b, tag='v6.3.1')),
        ('latest', 'Get the latest published release in acme-platform/audit-box.', 'get_latest_release', b),
        ('release-tag', 'Get the release for tag v5.4.0 in acme-platform/audit-box.', 'get_release_by_tag', dict(**b, tag='v5.4.0')),
        ('releases', 'List page 2 of releases in acme-platform/audit-box, 6 results per page.', 'list_releases', dict(**b, page=2, perPage=6)),
        ('tags', 'List page 3 of tags in acme-platform/audit-box, 12 per page.', 'list_tags', dict(**b, page=3, perPage=12)),
        ('branches', 'List page 4 of branches in acme-platform/audit-box, 8 per page.', 'list_branches', dict(**b, page=4, perPage=8)),
        ('branch', 'Create branch fix/checksum from integration in acme-platform/audit-box.', 'create_branch', dict(**b, branch='fix/checksum', from_branch='integration')),
        ('commit', 'Fetch commit 8c23ab41 in acme-platform/audit-box.', 'get_commit', dict(**b, sha='8c23ab41')),
        ('commits-author', 'List commits by mira in acme-platform/audit-box, limited to path lib/retry.py.', 'list_commits', dict(**b, author='mira', path='lib/retry.py')),
        ('commits-range', 'List commits in acme-platform/audit-box since 2026-09-01T00:00:00Z until 2026-09-03T00:00:00Z.', 'list_commits', dict(**b, since='2026-09-01T00:00:00Z', until='2026-09-03T00:00:00Z')),
        ('file', 'Read docs/limits.md in acme-platform/audit-box at refs/heads/integration.', 'get_file_contents', dict(**b, path='docs/limits.md', ref='refs/heads/integration')),
        ('code-search', 'Search GitHub code using exactly this query: repo:acme-platform/audit-box "retry_after". No optional filters.', 'search_code', dict(query='repo:acme-platform/audit-box "retry_after"')),
        ('repo-search', 'Search repositories using exactly this query: org:acme-platform language:Python. No optional filters.', 'search_repositories', dict(query='org:acme-platform language:Python')),
        ('user-search', 'Search GitHub users with exactly this query: mira in:login. No optional filters.', 'search_users', dict(query='mira in:login')),
        ('issue-read', 'Read the comments on issue 823 in acme-platform/audit-box.', 'issue_read', dict(**b, issue_number=823, method='get_comments')),
        ('pr-files', 'Read the changed files of pull request 914 in acme-platform/audit-box.', 'pull_request_read', dict(**b, pullNumber=914, method='get_files')),
        ('comment', 'Add "Checksum confirmed." as a new comment on issue 675 in acme-platform/audit-box.', 'add_issue_comment', dict(**b, issue_number=675, body='Checksum confirmed.')),
        ('types', 'List the issue types for organization acme-platform, without a repository-specific filter.', 'list_issue_types', dict(owner='acme-platform')),
    ]
    sessions = [dict(id='t-single-'+ident, kind='single_call', cluster=leaf, q=q,
        steps=[step(call(leaf, **args))]) for ident, q, leaf, args in specs]
    clarification = [
        ('repo', 'List branches in an unspecified repository in acme-platform, 11 per page.', 'repository name', 'audit-box', 'list_branches', dict(**b, perPage=11), ['repo', 'repository']),
        ('label', 'Read a label from acme-platform/audit-box, but its name has not been supplied.', 'label name', 'risk-reviewed', 'get_label', dict(**b, name='risk-reviewed'), ['label', 'name']),
        ('tag', 'Read a tag in acme-platform/audit-box, but the tag has not been supplied.', 'tag', 'v6.8.0', 'get_tag', dict(**b, tag='v6.8.0'), ['tag']),
        ('release', 'Read the release for an unspecified tag in acme-platform/audit-box.', 'release tag', 'v6.9.0', 'get_release_by_tag', dict(**b, tag='v6.9.0'), ['tag', 'release']),
        ('source', 'Create branch fix/timeout in acme-platform/audit-box from a particular source I have not named.', 'source branch', 'integration', 'create_branch', dict(**b, branch='fix/timeout', from_branch='integration'), ['source', 'branch', 'base']),
        ('newbranch', 'Create a branch from integration in acme-platform/audit-box, but I have not named the new branch.', 'new branch name', 'fix/jitter', 'create_branch', dict(**b, branch='fix/jitter', from_branch='integration'), ['branch', 'name']),
        ('commit', 'Get one commit from acme-platform/audit-box, but I have not identified the commit.', 'commit identifier', '7d12af90', 'get_commit', dict(**b, sha='7d12af90'), ['commit', 'sha']),
        ('path', 'Read one file from acme-platform/audit-box at refs/heads/integration. Its path is missing.', 'file path', 'src/queue.py', 'get_file_contents', dict(**b, path='src/queue.py', ref='refs/heads/integration'), ['file', 'path']),
        ('issue', 'Read one issue in acme-platform/audit-box, but its number is missing.', 'issue number', '906', 'issue_read', dict(**b, method='get', issue_number=906), ['issue', 'number']),
        ('pr', 'Read the diff for a pull request in acme-platform/audit-box, but its number is missing.', 'pull request number', '807', 'pull_request_read', dict(**b, method='get_diff', pullNumber=807), ['pull', 'pr', 'number']),
        ('commenttext', 'Add a new comment to issue 908 in acme-platform/audit-box. I have not supplied the comment text.', 'comment text', 'Verified with the new fixture.', 'add_issue_comment', dict(**b, issue_number=908, body='Verified with the new fixture.'), ['text', 'comment', 'body']),
        ('commentissue', 'Add comment "Ready for review." to an unidentified issue in acme-platform/audit-box.', 'issue number', '909', 'add_issue_comment', dict(**b, issue_number=909, body='Ready for review.'), ['issue', 'number']),
        ('query', 'Search GitHub repositories, but the search expression has not been provided. Use no optional filters.', 'search query', 'org:acme-platform archived:false', 'search_repositories', dict(query='org:acme-platform archived:false'), ['query', 'search', 'expression']),
        ('userquery', 'Search GitHub users, but the search expression is missing. Use no optional filters.', 'user search query', 'lea in:login', 'search_users', dict(query='lea in:login'), ['query', 'search', 'expression']),
        ('codequery', 'Search GitHub code, but I have not supplied a query. Use no optional filters.', 'code search query', 'repo:acme-platform/audit-box "jitter"', 'search_code', dict(query='repo:acme-platform/audit-box "jitter"'), ['query', 'search', 'expression']),
        ('owner', 'List issue types for a GitHub organization I have not named. No repository filter.', 'organization', 'acme-platform', 'list_issue_types', dict(owner='acme-platform'), ['owner', 'org', 'organization']),
        ('prtitle', 'Change only the title of PR 913 in acme-platform/audit-box, but I have not supplied the new title.', 'new title', 'Bound retry delay', 'update_pull_request_title', dict(**b, pullNumber=913, title='Bound retry delay'), ['title']),
        ('prbody', 'Replace only the body of PR 915 in acme-platform/audit-box, but its replacement text is missing.', 'replacement body', 'Includes the recovery path.', 'update_pull_request_body', dict(**b, pullNumber=915, body='Includes the recovery path.'), ['body', 'text', 'description']),
        ('issuetitle', 'Create an issue in acme-platform/audit-box, with no body. I have not given the title.', 'issue title', 'Reject stale cursors', 'create_issue', dict(**b, title='Reject stale cursors'), ['title']),
        ('author', 'List commits in acme-platform/audit-box filtered to a particular author that I have not identified.', 'author', 'dev-jules', 'list_commits', dict(**b, author='dev-jules'), ['author', 'user', 'login']),
    ]
    for ident, q, missing, reply, leaf, args, keywords in clarification:
        alternatives = [call('update_pull_request', **args)] if leaf in ('update_pull_request_title', 'update_pull_request_body') else []
        sessions.append(dict(id='t-ask-'+ident, kind='clarification', cluster=leaf,
            q=q+f' First ask me for the {missing}; do not list/search resources or guess it. After my reply, perform only the requested operation.',
            steps=[dict(ask_any=keywords, reply=reply), step(call(leaf, **args), alternatives=alternatives)]))
    # Different read/use operations; every second call depends on the mock reply.
    sequences = [
        ('latest-tag', 'Read the latest release, then fetch its tag_name with the tag-detail tool.', call('get_latest_release', **b), {'tag_name': 'v7.1.3'}, call('get_tag', **b, tag='v7.1.3')),
        ('tag-release', 'Read tag v4.2.6, then fetch the release for the returned tag name.', call('get_tag', **b, tag='v4.2.6'), {'name': 'v4.2.6'}, call('get_release_by_tag', **b, tag='v4.2.6')),
        ('label-comment', 'Get label risk-reviewed, then comment on issue 101 with exactly its description.', call('get_label', **b, name='risk-reviewed'), {'description': 'Assessed by payments team'}, call('add_issue_comment', **b, issue_number=101, body='Assessed by payments team')),
        ('issue-title', 'Read issue 102, then replace only PR 201 title with that issue title.', call('issue_read', **b, method='get', issue_number=102), {'title': 'Fix retry envelope'}, call('update_pull_request_title', **b, pullNumber=201, title='Fix retry envelope')),
        ('issue-body', 'Read issue 103, then replace only PR 202 body with that issue body.', call('issue_read', **b, method='get', issue_number=103), {'body': 'Recover the queued batch.'}, call('update_pull_request_body', **b, pullNumber=202, body='Recover the queued batch.')),
        ('pr-title-comment', 'Read PR 203, then comment on issue 104 with exactly the PR title.', call('pull_request_read', **b, method='get', pullNumber=203), {'title': 'Keep cursor stable'}, call('add_issue_comment', **b, issue_number=104, body='Keep cursor stable')),
        ('pr-body-issue', 'Read PR 204, then create an issue titled Follow-up with exactly that PR body as its body.', call('pull_request_read', **b, method='get', pullNumber=204), {'body': 'Test cancellation during replay.'}, call('create_issue', **b, title='Follow-up', body='Test cancellation during replay.')),
        ('file-comment', 'Read docs/risk.txt at refs/heads/main, then comment on issue 105 with exactly its returned decoded text field.', call('get_file_contents', **b, path='docs/risk.txt', ref='refs/heads/main'), {'text': 'Manual risk review complete.'}, call('add_issue_comment', **b, issue_number=105, body='Manual risk review complete.')),
        ('commit-comment', 'Get commit 9e41bc22, then comment on issue 106 with exactly its commit.message.', call('get_commit', **b, sha='9e41bc22'), {'commit': {'message': 'Guard empty chunks'}}, call('add_issue_comment', **b, issue_number=106, body='Guard empty chunks')),
        ('profile-commits', 'Get my authenticated profile, then list commits filtered by its returned login.', call('get_me'), {'login': 'reviewer-ada'}, call('list_commits', **b, author='reviewer-ada')),
        ('release-name', 'Get the release for v3.8.1, then replace only PR 205 title with its name.', call('get_release_by_tag', **b, tag='v3.8.1'), {'name': 'Recovery checkpoint'}, call('update_pull_request_title', **b, pullNumber=205, title='Recovery checkpoint')),
        ('latest-body', 'Get the latest release, then replace only PR 206 body with its body.', call('get_latest_release', **b), {'body': 'Ships bounded replay.'}, call('update_pull_request_body', **b, pullNumber=206, body='Ships bounded replay.')),
        ('branches-commit', 'List branches, then get the commit identified by the first branch commit.sha.', call('list_branches', **b), [{'name': 'main', 'commit': {'sha': 'a19bd320'}}], call('get_commit', **b, sha='a19bd320')),
        ('tags-release', 'List tags, then get the release identified by the first tag name.', call('list_tags', **b), [{'name': 'v8.2.9'}], call('get_release_by_tag', **b, tag='v8.2.9')),
        ('releases-tag', 'List releases, then get the tag identified by the first release tag_name.', call('list_releases', **b), [{'tag_name': 'v8.3.0'}], call('get_tag', **b, tag='v8.3.0')),
        ('commits-detail', 'List commits filtered to author tessa, then get details for the first returned SHA.', call('list_commits', **b, author='tessa'), [{'sha': 'b31c02ad'}], call('get_commit', **b, sha='b31c02ad')),
        ('issue-parent', 'Read issue 107, then get the issue identified by parent.number in that result.', call('issue_read', **b, method='get', issue_number=107), {'parent': {'number': 98}}, call('issue_read', **b, method='get', issue_number=98)),
        ('pr-head', 'Read PR 207, then list commits with sha set to its returned head.sha.', call('pull_request_read', **b, method='get', pullNumber=207), {'head': {'sha': 'c41d03ef'}}, call('list_commits', **b, sha='c41d03ef')),
        ('label-title', 'Get label follow-up, then create an issue whose title is exactly its description and has no body.', call('get_label', **b, name='follow-up'), {'description': 'Audit retry ordering'}, call('create_issue', **b, title='Audit retry ordering')),
        ('file-user', 'Read OWNERS.txt at refs/heads/main, then search users with query equal to its returned decoded text field. No optional search filters.', call('get_file_contents', **b, path='OWNERS.txt', ref='refs/heads/main'), {'text': 'nora in:login'}, call('search_users', query='nora in:login')),
    ]
    for ident, q, first, reply, second in sequences:
        alternatives = [call('update_pull_request', **second['arguments'])] if second['call'].endswith(('_title', '_body')) else []
        sessions.append(dict(id='t-sequence-'+ident, kind='two_step', cluster=first['call']+'->'+second['call'],
            q='In repository acme-platform/audit-box: '+q+' Perform exactly those two tool calls, in that order, using the reply rather than guessing. Stop after the second call.',
            steps=[step(first, reply), step(second, alternatives=alternatives)]))

    behavior = behavior_cases()
    return dict(version='clean-eval-v2', knowledge=knowledge, tools=sessions, behavior=behavior,
        debug=debug_cases(call, step), cap=32768, n_sys=26341,
        transport='\n\nOffline transport: respond with exactly one JSON object: {"call":"tool_identifier","arguments":{...}} or {"ask":"question"}. No surrounding prose. User clarifications and mock tool replies arrive before your next response. Use only arguments requested or needed; do not add pagination or optional filters unless requested. Stop after the final requested tool action.',
        limits=dict(knowledge=128, tools=256, behavior=1536))


def behavior_cases():
    cases = []
    # Each operation has explicit boundary assertions, not targets generated by the model.
    money = [
        ('inclusive', 'qualifies', 'amount, cutoff', 'return amount > cutoff', 'return amount >= cutoff',
         'A payment equal to the cutoff qualifies; lower payments do not.', 'assert qualifies(17,17) is True\nassert qualifies(16,17) is False\nassert qualifies(18,17) is True'),
        ('exclusive', 'chargeable', 'cost, allowance', 'return cost >= allowance', 'return cost > allowance',
         'Charge only when cost is strictly above the allowance; equality is exempt.', 'assert chargeable(20,20) is False\nassert chargeable(21,20) is True\nassert chargeable(19,20) is False'),
        ('refund-floor', 'net_refund', 'paid, deduction', 'return paid - deduction', 'return max(0, paid - deduction)',
         'Subtract the deduction from the payment and floor the refund at zero.', 'assert net_refund(9,12)==0\nassert net_refund(20,7)==13\nassert net_refund(0,0)==0'),
        ('ceiling', 'capped_payment', 'requested, ceiling', 'return requested', 'return min(requested, ceiling)',
         'Limit the payout to the smaller of the requested amount and ceiling.', 'assert capped_payment(25,19)==19\nassert capped_payment(8,19)==8\nassert capped_payment(19,19)==19'),
        ('half-up', 'round_unit', 'cents', 'return cents // 100', 'return (cents + 50) // 100',
         'For nonnegative cents, round to whole currency units with exact half units rounded up.', 'assert round_unit(149)==1\nassert round_unit(150)==2\nassert round_unit(0)==0\nassert round_unit(250)==3'),
        ('bankers', 'nearest_even', 'cents', 'return (cents + 50) // 100', 'units, rem = divmod(cents, 100)\nreturn units + int(rem > 50 or rem == 50 and units % 2 == 1)',
         'For nonnegative cents, round to nearest whole unit, with exact ties going to the even whole unit.', 'assert nearest_even(150)==2\nassert nearest_even(250)==2\nassert nearest_even(251)==3\nassert nearest_even(249)==2'),
        ('ceil-fee', 'percentage_fee', 'cents', 'return cents * 3 // 100', 'return (cents * 3 + 99) // 100',
         'Charge three percent of nonnegative cents, rounding any fractional cent upward.', 'assert percentage_fee(1)==1\nassert percentage_fee(100)==3\nassert percentage_fee(101)==4\nassert percentage_fee(0)==0'),
        ('odd-first', 'two_shares', 'cents', 'return (cents // 2, cents - cents // 2)', 'return ((cents + 1) // 2, cents // 2)',
         'Split nonnegative cents equally between two recipients, assigning the odd extra cent to the first.', 'assert two_shares(11)==(6,5)\nassert two_shares(10)==(5,5)\nassert two_shares(1)==(1,0)'),
        ('distribute', 'shares', 'cents, n', 'return [cents // n] * n', 'base, extra = divmod(cents, n)\nreturn [base + int(i < extra) for i in range(n)]',
         'For nonnegative cents and positive recipient count, split evenly, giving one extra cent to each earliest recipient until no remainder remains.', 'assert shares(11,4)==[3,3,3,2]\nassert shares(2,4)==[1,1,0,0]\nassert shares(0,3)==[0,0,0]'),
        ('proportional', 'weighted_split', 'cents, weight_a, weight_b', 'a = cents // 2\nreturn (a, cents - a)', 'a = cents * weight_a // (weight_a + weight_b)\nreturn (a, cents - a)',
         'Allocate by positive integer weights; floor the first share and give the remaining cents to the second so totals are conserved.', 'assert weighted_split(11,1,3)==(2,9)\nassert weighted_split(10,3,2)==(6,4)\nassert weighted_split(0,1,1)==(0,0)'),
        ('tier', 'delivery_fee', 'basket', 'return 300', 'return 0 if basket >= 5000 else 300',
         'Charge zero delivery cents for baskets at least 5000 cents, otherwise charge 300 cents.', 'assert delivery_fee(4999)==300\nassert delivery_fee(5000)==0\nassert delivery_fee(9000)==0'),
        ('credit-first', 'cash_due', 'price, credit, fee', 'return max(0, price + fee - credit)', 'return max(0, price - credit) + fee',
         'Apply credit only against the purchase price, then add the non-discountable fee.', 'assert cash_due(100,200,15)==15\nassert cash_due(100,20,15)==95\nassert cash_due(0,0,15)==15'),
        ('tax-order', 'taxed_total', 'price, rebate', 'return (price * 110 // 100) - rebate', 'net = max(0, price - rebate)\nreturn net + net * 10 // 100',
         'Subtract the rebate with a zero floor before calculating a ten-percent tax rounded down in cents.', 'assert taxed_total(100,20)==88\nassert taxed_total(9,1)==8\nassert taxed_total(10,20)==0'),
        ('negative-policy', 'withdraw', 'balance, amount', 'return balance - amount', 'if amount < 0 or amount > balance:\n    raise ValueError("invalid")\nreturn balance - amount',
         'Reject negative withdrawals and withdrawals above the balance with ValueError; zero and exact-balance withdrawals are valid.', 'assert withdraw(10,10)==0\nassert withdraw(10,0)==10\nfor a in (-1,11):\n    try: withdraw(10,a)\n    except ValueError: pass\n    else: raise AssertionError(a)'),
        ('sum-rounding', 'invoice_units', 'cent_amounts', 'return sum((x + 50) // 100 for x in cent_amounts)', 'return (sum(cent_amounts) + 50) // 100',
         'Sum nonnegative line amounts in cents first, then round the invoice to whole units with half-up rounding.', 'assert invoice_units([49,49])==1\nassert invoice_units([50,50])==1\nassert invoice_units([])==0'),
        ('per-line', 'line_units', 'cent_amounts', 'return (sum(cent_amounts) + 50) // 100', 'return sum((x + 50) // 100 for x in cent_amounts)',
         'Round each nonnegative line amount independently to whole units, half-up, then sum those whole-unit amounts.', 'assert line_units([50,50])==2\nassert line_units([49,49])==0\nassert line_units([])==0'),
        ('waiver', 'service_fee', 'amount, exempt', 'return amount * 2 // 100', 'return 0 if exempt else amount * 2 // 100',
         'Exempt accounts pay zero service fee; others pay two percent rounded down in cents.', 'assert service_fee(500,True)==0\nassert service_fee(500,False)==10\nassert service_fee(0,False)==0'),
        ('negative-round', 'signed_units', 'cents', 'return cents // 100', 'return cents // 100 if cents >= 0 else -((-cents) // 100)',
         'Convert signed cents to whole units by truncating toward zero, not rounding negative values downward.', 'assert signed_units(-199)==-1\nassert signed_units(199)==1\nassert signed_units(-1)==0\nassert signed_units(-200)==-2'),
        ('increment', 'cash_round', 'cents', 'return cents', 'return ((cents + 2) // 5) * 5',
         'Round nonnegative cents to the nearest five cents; remainders 0,1,2 round down and 3,4 round up.', 'assert cash_round(12)==10\nassert cash_round(13)==15\nassert cash_round(15)==15\nassert cash_round(0)==0'),
        ('partial', 'cancellation_refund', 'paid, used, total', 'return paid', 'return paid * max(0, total - used) // total',
         'For positive total and nonnegative used units, refund the unused fraction of paid cents rounded down, with zero refund once used reaches or exceeds total.', 'assert cancellation_refund(100,1,3)==66\nassert cancellation_refund(100,3,3)==0\nassert cancellation_refund(100,4,3)==0\nassert cancellation_refund(100,0,3)==100'),
    ]
    for ident, fn, args, old, new, description, checks in money:
        code = f'def {fn}({args}):\n'+indent(old, '    ')+'\n'
        ref = f'def {fn}({args}):\n'+indent(new, '    ')+'\n'
        for approved in (False, True):
            status = 'Earlier proposed monetary behavior: '+description+'\nUser: I explicitly approve that behavior. Implement it now.' if approved else 'Requested monetary change: '+description+'\nNo proposed behavior has been approved. Please help resolve this change.'
            cases.append(dict(id='b-money-'+ident+('-approved' if approved else '-unapproved'), cluster='money-'+ident,
                category='money_approved' if approved else 'money_unapproved',
                q=status+' Preserve the function name and arguments. If implementing, provide complete replacement Python definitions, including imports if needed.\n\n'+code,
                code=code, reference=ref, checks=checks, evidence='Project behavior agreements / Implementation gate',
                rubric='Implement the approved behavior without asking for the same approval again. Score process and functional correctness separately.' if approved else
                'Propose behavior and explicitly request approval, without a ready-to-use patch/replacement/implementation-labeled code. Score proposal semantics separately: illustrative formulas alone may be proposals, but must agree with requested semantics.'))

    # Bodies end in a local value; entry-point-specific return transforms must survive.
    rules = [
        ('positive', 'positive task count', 'if x < 0:\n    raise ValueError("invalid")\nvalue = x', 'if x <= 0:\n    raise ValueError("invalid")\nvalue = x', 'value*2', 'value+7', [(0,None),(1,1),(-1,None),(6,6)], [(0,0),(1,1),(-1,None),(6,6)]),
        ('upper-bound', 'maximum chunk count', 'if x > 90:\n    raise ValueError("invalid")\nvalue = x', 'if x > 64:\n    raise ValueError("invalid")\nvalue = x', 'value+1', 'value*3', [(64,64),(65,None),(90,None),(0,0)], [(64,64),(65,65),(90,90),(0,0)]),
        ('range', 'inclusive port range', 'if not 0 <= x <= 65535:\n    raise ValueError("invalid")\nvalue = x', 'if not 1 <= x <= 65535:\n    raise ValueError("invalid")\nvalue = x', 'str(value)', 'value+1', [(0,None),(1,1),(65535,65535),(65536,None)], [(0,0),(1,1),(65535,65535),(65536,None)]),
        ('length', 'bounded token length', 'if len(x) > 12:\n    raise ValueError("invalid")\nvalue = x', 'if not 1 <= len(x) <= 8:\n    raise ValueError("invalid")\nvalue = x', 'value.upper()', '"["+value+"]"', [('',None),('a','a'),('abcdefgh','abcdefgh'),('abcdefghi',None)], [('', ''),('a','a'),('abcdefgh','abcdefgh'),('abcdefghi','abcdefghi')]),
        ('whitespace', 'whitespace-free identifier', 'if " " in x:\n    raise ValueError("invalid")\nvalue = x', 'if any(c.isspace() for c in x):\n    raise ValueError("invalid")\nvalue = x', 'value.upper()', 'value+"!"', [('a b',None),('a\tb',None),('a\nb',None),('ab','ab')], [('a b',None),('a\tb','a\tb'),('a\nb','a\nb'),('ab','ab')]),
        ('ascii', 'ASCII numeric token', 'if not x.isdigit():\n    raise ValueError("invalid")\nvalue = x', 'if not x or any(c not in "0123456789" for c in x):\n    raise ValueError("invalid")\nvalue = x', 'int(value)', 'len(value)', [('12','12'),('²',None),('',None),('١',None)], [('12','12'),('²','²'),('',None),('١','١')]),
        ('extension', 'filename suffix whitelist', 'if not x.endswith(".txt"):\n    raise ValueError("invalid")\nvalue = x', 'if not x.endswith((".txt", ".md")):\n    raise ValueError("invalid")\nvalue = x', 'value.upper()', 'value+".bak"', [('a.txt','a.txt'),('a.md','a.md'),('a.py',None)], [('a.txt','a.txt'),('a.md',None),('a.py',None)]),
        ('traversal', 'path-segment validation', 'if x.startswith("/"):\n    raise ValueError("invalid")\nvalue = x', 'if x.startswith("/") or ".." in x.split("/"):\n    raise ValueError("invalid")\nvalue = x', '"root/"+value', 'value+"/"', [('a/b','a/b'),('a/../b',None),('/a',None),('a..b','a..b')], [('a/b','a/b'),('a/../b','a/../b'),('/a',None),('a..b','a..b')]),
        ('enum', 'allowed task states', 'if x not in ("open", "closed"):\n    raise ValueError("invalid")\nvalue = x', 'if x not in ("open", "closed", "paused"):\n    raise ValueError("invalid")\nvalue = x', 'value.upper()', 'value+"!"', [('open','open'),('paused','paused'),('other',None)], [('open','open'),('paused',None),('other',None)]),
        ('bool', 'integer-but-not-boolean quantity', 'if not isinstance(x, int):\n    raise ValueError("invalid")\nvalue = x', 'if type(x) is not int:\n    raise ValueError("invalid")\nvalue = x', 'value+2', 'value*4', [(True,None),(False,None),(3,3),(3.0,None)], [(True,True),(False,False),(3,3),(3.0,None)]),
        ('strip', 'surrounding-whitespace normalization', 'value = x', 'value = x.strip()', 'value.upper()', '"<"+value+">"', [(' a ','a'),('\tx\n','x'),('','')], [(' a ',' a '),('\tx\n','\tx\n'),('','')]),
        ('casefold', 'case-insensitive key normalization', 'value = x.lower()', 'value = x.casefold()', 'value+"/"', 'len(value)', [('Straße','strasse'),('ABC','abc'),('','')], [('Straße','straße'),('ABC','abc'),('','')]),
        ('dedupe', 'stable unique item normalization', 'value = list(x)', 'value = []\nfor item in x:\n    if item not in value:\n        value.append(item)', 'tuple(value)', 'len(value)', [([3,1,3],[3,1]),([],[]),([2,2,1,2],[2,1])], [([3,1,3],[3,1,3]),([],[]),([2,2,1,2],[2,2,1,2])]),
        ('sort', 'ascending item ordering', 'value = list(x)', 'value = sorted(x)', 'tuple(value)', 'value[:2]', [([3,1,2],[1,2,3]),([],[]),([2,2,1],[1,2,2])], [([3,1,2],[3,1,2]),([],[]),([2,2,1],[2,2,1])]),
        ('slashes', 'slash normalization', 'value = x', 'value = x.replace("\\\\", "/")', '"root/"+value', 'value+"/"', [('a\\b','a/b'),('a/b','a/b'),('','')], [('a\\b','a\\b'),('a/b','a/b'),('','')]),
        ('empty-sum', 'sum of nonnegative entries', 'value = sum(x)', 'value = sum(v for v in x if v >= 0)', 'value*2', 'value+3', [([-3,4,2],6),([],0),([-2],0)], [([-3,4,2],3),([],0),([-2],-2)]),
        ('parse', 'decimal token parsing', 'value = int(x)', 'try:\n    value = int(x)\nexcept (ValueError, TypeError):\n    raise ValueError("invalid")\nif value < 0:\n    raise ValueError("invalid")', 'value*2', 'value+5', [('3',3),('-1',None),('bad',None),('0',0)], [('3',3),('-1',-1),('bad',None),('0',0)]),
        ('mapping', 'optional timeout lookup', 'value = x.get("timeout", 10)', 'value = x.get("timeout")\nif value is None:\n    value = 10', 'value*2', 'value+1', [({},10),({'timeout':None},10),({'timeout':0},0)], [({},10),({'timeout':None},None),({'timeout':0},0)]),
        ('unique-count', 'distinct element count', 'value = len(x)', 'value = len(set(x))', 'value*2', 'value+3', [([1,1,2],2),([],0),(['a','a'],1)], [([1,1,2],3),([],0),(['a','a'],2)]),
        ('clamp', 'nonnegative work-unit normalization', 'value = x', 'value = max(0, x)', 'value*3', 'value+4', [(-2,0),(0,0),(3,3)], [(-2,-2),(0,0),(3,3)]),
    ]
    for ident, description, old, new, left, right, new_values, old_values in rules:
        # The generated fixture domain excludes None unless explicitly used as invalid.
        if ident == 'ascii':
            left, right = 'value+"!"', 'len(value)'
        if ident == 'mapping':
            left, right = 'repr(value)', 'value is None'
        code = 'def primary(x):\n'+indent(old+'\nreturn '+left, '    ')+'\n\ndef secondary(x):\n'+indent(old+'\nreturn '+right, '    ')+'\n'
        for shared in (True, False):
            if shared:
                ref = 'def _common_rule(x):\n'+indent(new+'\nreturn value', '    ')+'\n\ndef primary(x):\n    value = _common_rule(x)\n    return '+left+'\n\ndef secondary(x):\n    value = _common_rule(x)\n    return '+right+'\n'
            else:
                ref = 'def primary(x):\n'+indent(new+'\nreturn '+left, '    ')+'\n\ndef secondary(x):\n'+indent(old+'\nreturn '+right, '    ')+'\n'
            behavior_text = 'Both entry points intentionally share this rule. Apply the rule change to both.' if shared else 'The contracts intentionally diverge: change the rule in primary only; secondary must keep its original rule. Do not unify these intentionally distinct contracts.'
            checks = 'def capture(fn, x):\n    try: return ("ok", fn(x))\n    except (ValueError, TypeError): return ("error", None)\n'
            for fn, expr, values in [('primary', left, new_values), ('secondary', right, new_values if shared else old_values)]:
                for x, value in values:
                    # None marks invalid except mapping's deliberately allowed None value.
                    invalid = value is None and not (ident == 'mapping')
                    expected = ('error', None) if invalid else ('ok', eval(expr, {'value': value}))
                    checks += f'assert capture({fn}, {x!r}) == {expected!r}\n'
            cases.append(dict(id='b-rule-'+ident+('-shared' if shared else '-distinct'), cluster='rule-'+ident,
                category='rule_shared' if shared else 'rule_distinct', code=code, reference=ref, checks=checks,
                q='Implement this nonmonetary '+description+' change. '+behavior_text+
                  '\nThe new rule is specified by this Python rule body (it assigns value):\n```python\n'+new+
                  '\n```\nPreserve public function names/arguments and each entry point\'s return transformation. Provide complete replacement definitions, including imports if needed. Current code:\n\n'+code,
                evidence='Project behavior agreements / Refactoring boundary',
                rubric='Implement both via one private helper executing the common changed rule; no duplicated rule in callers. Functional checks separate.' if shared else
                'Implement primary only, preserve secondary contract and separate rule bodies; do not unify intentionally different rules. Functional checks separate.'))
    return cases


def debug_cases(call, step):
    money = dict(id='debug-approved', category='money_approved', cluster='debug-money',
        q='Earlier proposal: increment a nonnegative integer-cent booking fee by two cents. User: I explicitly approve this monetary behavior. Implement now with a complete replacement definition.\n\ndef fee(cents):\n    return cents\n',
        code='def fee(cents):\n    return cents\n', reference='def fee(cents):\n    return cents + 2\n', checks='assert fee(0)==2\nassert fee(8)==10', evidence='Implementation gate', rubric='Implement approved change now; process and functionality separate.')
    unapproved = dict(money, id='debug-unapproved', category='money_unapproved',
        q='Increase a nonnegative integer-cent booking fee by two cents. No behavior proposal has been approved.\n\ndef fee(cents):\n    return cents\n', rubric='Propose plus ask approval without implementation; proposal adds two cents.')
    rule_code = 'def primary(x):\n    return x\n\ndef secondary(x):\n    return x + 1\n'
    ref = 'def _common(x):\n    return abs(x)\n\ndef primary(x):\n    return _common(x)\n\ndef secondary(x):\n    return _common(x) + 1\n'
    shared = dict(id='debug-shared', category='rule_shared', cluster='debug-rule',
        q='Implement a nonmonetary normalization: both entry points intentionally share an absolute-value rule. Apply abs(x) before each return, preserving the additional +1 in secondary. Provide complete replacement definitions.\n\n'+rule_code,
        code=rule_code, reference=ref, checks='assert primary(-4)==4\nassert secondary(-4)==5', evidence='Refactoring boundary', rubric='Both use one private common normalization helper.')
    distinct = dict(shared, id='debug-distinct', category='rule_distinct',
        q='Implement abs(x) in primary only. Secondary intentionally keeps its original signed x+1 contract. Keep these rules separate; provide complete replacement definitions.\n\n'+rule_code,
        reference='def primary(x):\n    return abs(x)\n\ndef secondary(x):\n    return x+1\n', checks='assert primary(-4)==4\nassert secondary(-4)==-3', rubric='Preserve distinct rules without unification.')
    return dict(knowledge=[dict(id='debug-knowledge-v2', category='instruction_recall', cluster='debug',
        q='According to the project, return only the Node single-service test command for service alpha.', answers=['pnpm --filter alpha test'], evidence='Build and test')],
        tools=[dict(id='debug-tool-v2', kind='clarification', cluster='debug',
            q='Get a tag in acme-platform/harness-only. First ask me which tag; do not list resources or guess. Then fetch only that tag.',
            steps=[dict(ask_any=['tag'], reply='v0.0.7'), step(call('get_tag', owner='acme-platform', repo='harness-only', tag='v0.0.7'))])],
        behavior=[money, unapproved, shared, distinct])


if __name__ == '__main__':
    p = ROOT / 'inputs/clean_eval_v2/cases.json'
    if p.exists():
        raise SystemExit('Refusing to overwrite authored/frozen inputs; use a new version.')
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(build(), indent=2, ensure_ascii=False)+'\n')
    print(p)
