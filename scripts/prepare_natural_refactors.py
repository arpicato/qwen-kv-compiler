"""Author natural validation-change tasks; never reads model outputs or scores."""
import json
from pathlib import Path
from textwrap import indent

ROOT = Path(__file__).resolve().parents[1]


def build():
    # id, family, arguments, old rejection, new rejection, natural request,
    # two public functions/return expressions, accepted and rejected argument tuples.
    specs = [
        ('count-zero', 'numeric', 'count', 'count < 0', 'count <= 0',
         'Zero-sized jobs currently get scheduled. Reject zero as well as negative counts in both job entry points; positive jobs should behave as before.',
         ('schedule_batch', 'count * 2'), ('preview_batch', 'count + 1'), [(1,), (7,)], [(0,), (-1,)]),
        ('retry-limit', 'numeric', 'retries', 'retries > 12', 'not 0 <= retries <= 12',
         'Negative retry budgets slip through the worker and preview paths. Allow budgets from zero through twelve inclusive, and reject anything outside that range.',
         ('start_worker', 'retries + 1'), ('preview_worker', 'retries * 3'), [(0,), (12,)], [(-1,), (13,)]),
        ('batch-multiple', 'numeric', 'size', 'size <= 0', 'size <= 0 or size % 8 != 0',
         'The encoder now accepts only positive batch sizes divisible by eight. Update both upload and dry-run entry points without changing what they return for accepted sizes.',
         ('encode_upload', 'size // 8'), ('preview_upload', 'size + 8'), [(8,), (24,)], [(0,), (-8,), (7,), (9,)]),
        ('integer-bool', 'numeric', 'workers', 'not isinstance(workers, int)', 'type(workers) is not int',
         'True and False are being treated as worker counts. Reject booleans while continuing to accept ordinary integers in the launch and estimate paths.',
         ('launch_pool', 'workers + 2'), ('estimate_pool', 'workers * 4'), [(0,), (3,), (-2,)], [(True,), (False,), (2.0,)]),
        ('finite-number', 'numeric', 'reading', 'reading < 0', 'not math.isfinite(reading) or reading < 0',
         'Non-finite sensor readings are reaching the storage and display paths. Reject NaN and both infinities as well as negative readings; keep finite nonnegative readings valid.',
         ('store_reading', 'reading * 2'), ('display_reading', 'str(reading)'), [(0.0,), (2.5,)], [(-1.0,), ('@nan',), ('@inf',), ('@-inf',)]),
        ('name-empty', 'text', 'name', 'len(name) > 16', 'not name or len(name) > 16',
         'Empty names are accepted by the registration and preview endpoints. Names must have one through sixteen characters; keep existing accepted-name output formatting.',
         ('register_name', 'name.upper()'), ('preview_name', '"[" + name + "]"'), [('a',), ('abcdefghijklmnop',)], [('',), ('abcdefghijklmnopq',)]),
        ('unicode-space', 'text', 'key', '" " in key', 'any(c.isspace() for c in key)',
         'Tab and newline characters bypass the identifier checks. In the save and lookup entry points, reject any whitespace character, not just a space.',
         ('save_key', 'key.upper()'), ('lookup_key', 'key + ":"'), [('alpha',), ('',)], [('a b',), ('a\tb',), ('a\nb',), ('a\u00a0b',)]),
        ('ascii-digits', 'text', 'token', 'not token.isdigit()', 'not token or any(c not in "0123456789" for c in token)',
         'The wire format requires ASCII digits, but Unicode digits currently pass validation. Both submission paths should accept a nonempty sequence of ASCII digits only.',
         ('submit_token', 'token + "!"'), ('inspect_token', 'len(token)'), [('0',), ('0012',)], [('',), ('١',), ('²',), ('12a',)]),
        ('case-sensitive-prefix', 'text', 'code', 'not code.lower().startswith("job-")', 'not code.startswith("job-")',
         'Job identifiers are case-sensitive on the server. Stop accepting JOB- and Job- prefixes in both queue operations; only the exact lowercase job- prefix is valid.',
         ('enqueue_code', 'code + ":queued"'), ('inspect_code', 'len(code)'), [('job-a',), ('job-',)], [('JOB-a',), ('Job-a',), ('task-a',)]),
        ('control-chars', 'text', 'label', '"\\n" in label', 'any(ord(c) < 32 or ord(c) == 127 for c in label)',
         'The export and display labels must contain no ASCII control characters, including DEL. They currently reject only newlines. Preserve ordinary spaces and printable Unicode.',
         ('export_label', 'label + ";"'), ('display_label', 'label.upper()'), [('a b',), ('é',), ('',)], [('a\tb',), ('a\x00b',), ('a\x7fb',), ('a\nb',)]),
        ('relative-path', 'path', 'path', 'path.startswith("/")', 'path.startswith("/") or ".." in path.split("/")',
         'Relative asset paths can still contain parent-directory segments. Both fetch and preview must reject a complete .. segment anywhere, while retaining names such as a..b.',
         ('fetch_asset', '"assets/" + path'), ('preview_asset', 'path + "?preview"'), [('a/b',), ('a..b',)], [('/a',), ('../a',), ('a/../b',)]),
        ('file-extension', 'path', 'filename', 'not filename.endswith(".json")', 'not filename.endswith((".json", ".jsonl"))',
         'Add support for .jsonl files to the import and validation endpoints. Keep .json valid, and continue rejecting other suffixes and uppercase variants.',
         ('import_file', 'filename + ":import"'), ('validate_file', 'len(filename)'), [('a.json',), ('a.jsonl',)], [('a.csv',), ('a.JSONL',), ('a.jsonl.bak',)]),
        ('hidden-component', 'path', 'path', 'path.startswith(".")', 'any(part.startswith(".") for part in path.split("/"))',
         'Hidden directories nested below a visible directory bypass the scan and archive checks. Reject paths with any dot-prefixed component, not only a leading dot.',
         ('scan_path', 'path + ":scan"'), ('archive_path', '"archive/" + path'), [('a/b',), ('a/b.c',)], [('.cache/a',), ('a/.cache/b',), ('a/.file',)]),
        ('empty-segment', 'path', 'path', 'path == ""', 'any(part == "" for part in path.split("/"))',
         'Route paths with empty segments are producing inconsistent URLs. Reject empty segments in the publish and preview functions, including leading, trailing, and doubled slashes.',
         ('publish_route', '"/v1/" + path'), ('preview_route', 'path.upper()'), [('a',), ('a/b',)], [('',), ('/a',), ('a/',), ('a//b',)]),
        ('backslash', 'path', 'path', 'path.startswith("/")', 'path.startswith("/") or "\\\\" in path',
         'These paths use forward slashes only. Reject any backslash in both manifest operations, in addition to the existing absolute-path check.',
         ('load_manifest', '"data/" + path'), ('preview_manifest', 'len(path)'), [('a/b',), ('a.txt',)], [('/a',), ('a\\b',), ('\\a',)]),
        ('unique-items', 'collection', 'items', 'not items', 'not items or len(set(items)) != len(items)',
         'Duplicate integer IDs cause duplicate work. Reject an empty list or repeated IDs in both indexing and preview; preserve the supplied order for unique IDs.',
         ('index_items', 'tuple(items)'), ('preview_items', 'len(items)'), [([3, 1],), ([0],)], [([],), ([1, 1],), ([2, 3, 2],)]),
        ('all-positive', 'collection', 'items', 'not items', 'not items or any(v <= 0 for v in items)',
         'Batches must now contain at least one strictly positive count and no zero or negative counts. Apply this to submission and estimation without sorting the batch.',
         ('submit_counts', 'tuple(items)'), ('estimate_counts', 'sum(items)'), [([1],), ([2, 4],)], [([],), ([0, 2],), ([2, -1],)]),
        ('sorted-input', 'collection', 'items', 'not items', 'not items or any(a > b for a, b in zip(items, items[1:]))',
         'Merge inputs must already be in nondecreasing order. Reject descending pairs in both merge paths; duplicates are allowed, and the functions must not sort the input for the caller.',
         ('merge_input', 'tuple(items)'), ('preview_merge', 'len(items)'), [([1],), ([1, 1, 3],)], [([],), ([2, 1],), ([1, 3, 2],)]),
        ('maximum-items', 'collection', 'items', 'len(items) > 8', 'len(items) > 4',
         'The remote API lowered its batch limit from eight items to four. Enforce the new limit in both send and preview. Empty batches remain valid.',
         ('send_batch', 'tuple(items)'), ('preview_send', 'len(items)'), [([],), ([1, 2, 3, 4],)], [([1, 2, 3, 4, 5],), (list(range(9)),)]),
        ('pair-width', 'collection', 'rows', 'not rows', 'not rows or any(len(row) != 2 for row in rows)',
         'Each row must contain exactly two cells. The writer and preview currently only check that there are rows; reject short or wide rows too.',
         ('write_rows', 'tuple(tuple(row) for row in rows)'), ('preview_rows', 'len(rows)'), [([[1, 2]],), ([[1, 2], [3, 4]],)], [([],), ([[1]],), ([[1, 2, 3]],)]),
        ('required-keys', 'mapping', 'record', '"id" not in record', '"id" not in record or "version" not in record',
         'Records without a version cannot be replayed. Both ingestion and preview must require the presence of id and version. Zero and None values are allowed; this is a key-presence check.',
         ('ingest_record', 'record["id"]'), ('preview_record', 'len(record)'), [({'id': 0, 'version': None},), ({'id': 2, 'version': 1},)], [({},), ({'id': 2},), ({'version': 1},)]),
        ('unknown-keys', 'mapping', 'options', '"timeout" not in options', '"timeout" not in options or bool(set(options) - {"timeout", "retries"})',
         'Misspelled option names are silently accepted. For both execution and preview, timeout is required and retries is the only optional key. Reject any other key.',
         ('execute_options', 'options["timeout"]'), ('preview_options', 'len(options)'), [({'timeout': 0},), ({'timeout': 5, 'retries': 2},)], [({},), ({'timeout': 5, 'retry': 2},)]),
        ('duplicate-values', 'mapping', 'aliases', 'not aliases', 'not aliases or len(set(aliases.values())) != len(aliases)',
         'Two aliases must not point at the same integer destination. Reject empty mappings and duplicate destinations in both alias entry points; alias names may differ freely.',
         ('register_aliases', 'tuple(aliases)'), ('preview_aliases', 'len(aliases)'), [({'a': 1},), ({'a': 1, 'b': 2},)], [({},), ({'a': 1, 'b': 1},)]),
        ('exclusive-options', 'mapping', 'options', 'not options', '("cursor" in options) == ("offset" in options)',
         'Paging requests must specify exactly one of cursor or offset. Enforce that in fetch and preview; a present empty cursor or zero offset still counts as supplied.',
         ('fetch_page', 'dict(options)'), ('preview_page', 'len(options)'), [({'cursor': ''},), ({'offset': 0},)], [({},), ({'cursor': 'a', 'offset': 0},)]),
        ('nested-config', 'mapping', 'config', '"limits" not in config', '"limits" not in config or not isinstance(config["limits"], dict) or "workers" not in config["limits"]',
         'The planner and preview assume limits is a mapping with a workers key. Reject configurations that do not meet that shape instead of failing later. Worker zero remains allowed.',
         ('plan_config', 'dict(config)'), ('preview_config', 'len(config)'), [({'limits': {'workers': 0}},), ({'limits': {'workers': 3}},)], [({},), ({'limits': []},), ({'limits': {}},)]),
        ('interval', 'compound', 'start, end', 'start > end', 'start >= end',
         'Zero-width intervals should no longer be accepted by booking or preview. Require the end to be strictly later than the start; negative endpoints themselves are allowed.',
         ('book_interval', 'end - start'), ('preview_interval', '(start, end)'), [(0, 1), (-3, -1)], [(1, 1), (2, 1)]),
        ('page-size', 'compound', 'page, size', 'page < 1', 'page < 1 or not 1 <= size <= 100',
         'Page sizes outside one through one hundred bypass the list and count endpoints. Keep page numbering positive and enforce the inclusive size limits in both.',
         ('list_page', '(page - 1) * size'), ('count_page', 'size'), [(1, 1), (3, 100)], [(0, 2), (1, 0), (1, 101)]),
        ('offset-alignment', 'compound', 'offset, block', 'offset < 0 or block <= 0', 'offset < 0 or block <= 0 or offset % block != 0',
         'Offsets must be aligned to a positive block size. Add the alignment check to both read and preview while keeping nonnegative offsets, including zero.',
         ('read_block', 'offset // block'), ('preview_block', '(offset, block)'), [(0, 4), (12, 4)], [(-4, 4), (3, 0), (3, 4)]),
        ('dimensions', 'compound', 'width, height', 'width <= 0 or height <= 0', 'width <= 0 or height <= 0 or width * height > 64',
         'Images larger than sixty-four pixels in area must be rejected before render or preview. Width and height must still each be positive; exactly sixty-four pixels is valid.',
         ('render_tile', 'width * height'), ('preview_tile', '(width, height)'), [(8, 8), (1, 1)], [(0, 4), (9, 8), (1, -1)]),
        ('bounded-window', 'compound', 'offset, length, total', 'offset < 0 or length < 0', 'offset < 0 or length < 0 or offset + length > total',
         'Requested byte windows can extend beyond the buffer. Both slice and preview must reject a window whose end exceeds total. Empty windows ending exactly at total remain valid.',
         ('slice_window', '(offset, offset + length)'), ('preview_window', 'length'), [(0, 4, 4), (4, 0, 4)], [(3, 2, 4), (-1, 1, 4), (0, -1, 4)]),
        ('date-validity', 'stdlib', 'year, month, day', 'not 1 <= month <= 12 or not 1 <= day <= 31', 'not valid_date(year, month, day)',
         'Calendar-invalid dates pass the storage and display checks. Validate actual Gregorian dates, including leap years, rather than independent month and day ranges.',
         ('store_date', '(year, month, day)'), ('display_date', 'f"{year:04}-{month:02}-{day:02}"'), [(2024, 2, 29), (2023, 12, 31)], [(2023, 2, 29), (2024, 4, 31), (2024, 13, 1)]),
        ('ipv4', 'stdlib', 'address', 'len(address.split(".")) != 4', 'not valid_ipv4(address)',
         'Four dot-separated pieces are not enough to validate an IPv4 address. Both connection and preview must reject invalid octets, nonnumeric pieces and IPv6; accept valid IPv4 only.',
         ('connect_ipv4', 'address'), ('preview_ipv4', '"host=" + address'), [('127.0.0.1',), ('255.255.255.255',)], [('256.1.2.3',), ('a.b.c.d',), ('::1',)]),
        ('json-object', 'stdlib', 'text', 'not text', 'not valid_object(text)',
         'These two settings entry points require a JSON object. Reject malformed JSON, arrays, scalars and null instead of accepting every nonempty string.',
         ('load_settings', 'text.strip()'), ('preview_settings', 'len(text)'), [('{}',), ('{"a":1}',)], [('',), ('[]',), ('null',), ('{bad}',), ('2',)]),
        ('hex-bytes', 'stdlib', 'text', 'len(text) % 2 != 0', 'len(text) % 2 != 0 or any(c not in "0123456789abcdefABCDEF" for c in text)',
         'Even-length strings with non-hex characters currently pass both digest entry points. Require an even number of ASCII hexadecimal characters; the empty digest is valid and whitespace is not.',
         ('load_digest', 'text.lower()'), ('preview_digest', 'len(text) // 2'), [('',), ('00aF',)], [('0',), ('gg',), ('aa bb',), ('  ',)]),
        ('utf8-length', 'stdlib', 'text', 'len(text) > 8', 'len(text.encode("utf-8")) > 8',
         'The storage limit is eight UTF-8 bytes, not eight characters. Enforce the byte limit in both message paths; exactly eight bytes and an empty string are valid.',
         ('store_message', 'text'), ('preview_message', 'text.upper()'), [('',), ('éééé',), ('abcdefgh',)], [('ééééé',), ('abcdefghi',)]),
        ('reserved-names', 'protocol', 'name', 'name in ("admin", "root")', 'name.casefold() in ("admin", "root")',
         'Mixed-case spellings bypass the reserved-name checks. Reject admin and root case-insensitively in both account paths; do not reject names merely containing those words.',
         ('open_account', 'name + ":open"'), ('preview_account', 'len(name)'), [('rooted',), ('administrator',)], [('admin',), ('ROOT',), ('AdMiN',)]),
        ('newline-header', 'protocol', 'value', '"\\n" in value', '"\\n" in value or "\\r" in value',
         'Carriage returns can still enter a header value. Both write and preview must reject CR as well as LF, while spaces and tabs remain valid.',
         ('write_header', '"X-Value: " + value'), ('preview_header', 'len(value)'), [('a b',), ('a\tb',)], [('a\rb',), ('a\nb',), ('\r\n',)]),
        ('delimiter', 'protocol', 'name', '":" in name', 'any(c in name for c in (":", ",", ";"))',
         'The separator format now reserves comma and semicolon as well as colon. Reject any of those delimiters in both field-name entry points; periods and underscores remain valid.',
         ('write_field', 'name + "=1"'), ('preview_field', 'name.upper()'), [('a.b',), ('a_b',)], [('a:b',), ('a,b',), ('a;b',)]),
        ('version-parts', 'protocol', 'version', 'len(version.split(".")) != 3', 'len(version.split(".")) != 3 or any(not p or any(c not in "0123456789" for c in p) for p in version.split("."))',
         'Release versions require exactly three nonempty ASCII numeric components. Update the publish and preview checks so forms like 1.x.3 or 1..3 are rejected; leading zeroes are allowed.',
         ('publish_version', '"v" + version'), ('preview_version', 'version.split(".")'), [('1.2.3',), ('01.0.3',)], [('1.x.3',), ('1..3',), ('1.2',), ('١.2.3',)]),
        ('token-alphabet', 'protocol', 'token', 'not token', 'not token or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in token)',
         'Tokens sent by the encode and preview entry points must use only ASCII letters, digits, underscore or hyphen. Keep empty tokens invalid and reject spaces, Unicode letters and punctuation.',
         ('encode_token', 'token + "="'), ('preview_token', 'len(token)'), [('Ab_09-',), ('x',)], [('',), ('a b',), ('é',), ('a!',)]),
    ]
    support = {
        'date-validity': 'from datetime import date\n\ndef valid_date(year, month, day):\n    try:\n        date(year, month, day)\n        return True\n    except ValueError:\n        return False\n',
        'ipv4': 'import ipaddress\n\ndef valid_ipv4(address):\n    try:\n        ipaddress.IPv4Address(address)\n        return True\n    except ValueError:\n        return False\n',
        'json-object': 'import json\n\ndef valid_object(text):\n    try:\n        return isinstance(json.loads(text), dict)\n    except ValueError:\n        return False\n',
        'finite-number': 'import math\n',
    }
    cases = []
    for ident, family, args, old, new, request, left, right, valid, invalid in specs:
        # Non-finite fixtures use string sentinels solely for JSON portability.
        def literal(values):
            return '(' + ', '.join({'@nan': 'float("nan")', '@inf': 'float("inf")', '@-inf': '-float("inf")'}.get(x, repr(x)) if isinstance(x, str) else repr(x) for x in values) + ',)'
        original_support = 'import math\n' if ident == 'finite-number' else ''
        def public(function, predicate, helper=False):
            body = f'_validate({args})\n' if helper else f'if {predicate}:\n    raise ValueError("invalid")\n'
            return f'def {function[0]}({args}):\n'+indent(body+'return '+function[1], '    ')+'\n'
        code = original_support + '\n'+public(left, old)+'\n'+public(right, old)
        reference = support.get(ident, '')+'\ndef _validate('+args+'):\n'+indent(f'if {new}:\n    raise ValueError("invalid")', '    ')+'\n\n'+public(left, new, True)+'\n'+public(right, new, True)
        # Keep original return expressions, omitting the obsolete validation so
        # newly permitted inputs (e.g. .jsonl) have independently specified outputs.
        returns = '\n'.join(f'def {fn}({args}):\n    return {expr}\n' for fn, expr in (left, right))
        checks = 'original = {}\nexec('+repr(returns)+', original)\n'
        checks += 'for values in ['+', '.join(literal(v) for v in valid)+']:\n'
        for fn in (left[0], right[0]):
            checks += f'    assert {fn}(*values) == original[{fn!r}](*values), ({fn!r}, values)\n'
        checks += 'for values in ['+', '.join(literal(v) for v in invalid)+']:\n'
        for fn in (left[0], right[0]):
            checks += f'    try:\n        {fn}(*values)\n    except ValueError:\n        pass\n    else:\n        raise AssertionError(({fn!r}, values, "accepted invalid"))\n'
        cases.append(dict(id='natural-'+ident, family=family, cluster=ident, functions=[left[0], right[0]],
            q=request+' Keep the public names, arguments and unrelated behavior unchanged. Invalid inputs should raise ValueError. Show complete replacement Python definitions, including any needed imports.\n\n'+code,
            code=code, reference=reference, checks=checks, valid_inputs=valid, invalid_inputs=invalid,
            evidence='Project behavior agreements / Refactoring boundary',
            rubric='Functional: accept/reject specified inputs and preserve accepted-input outputs/signatures. Structural: both entry points use one private helper actually executing the common changed validation; no duplicated changed validation in callers. Judge structure and functionality separately and jointly.'))
    return dict(version='natural-refactors-v3', cases=cases, max_tokens=1536,
        policy_scope='Targeted shared-validation changes only. No approval, recall, distinct-contract or approved-money controls. No broad policy-compliance claim.')


if __name__ == '__main__':
    path = ROOT / 'inputs/natural_refactors_v3/cases.json'
    if path.exists():
        raise SystemExit('Refusing to overwrite existing cases')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build(), indent=2, ensure_ascii=False, allow_nan=False)+'\n')
    print(path)
