import re
from datetime import datetime

path = 'chat_conv_dashboard.txt'
pattern = re.compile(r"^\{hash:\s*(?P<h>[^,]+),\s*author:\s*(?P<a>[^,]+),\s*date:\s*(?P<d>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [+-]\d{4}),\s*message:\s*(?P<m>.*)\},\s*$")

bad = []
count = 0
with open(path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, start=1):
        if not line.lstrip().startswith('{hash:'):
            continue
        m = pattern.match(line.strip())
        if not m:
            bad.append((i, line.rstrip('\n')))
            continue
        h = m.group('h').strip()
        a = m.group('a').strip()
        d = m.group('d').strip()
        msg = m.group('m')
        # unescape placeholder
        msg = msg.replace('<COMMA>', ', ')
        # rstrip trailing braces/commas if any remain
        msg = msg.rstrip('},').rstrip()

        # show what we'd run
        commit_date_iso = datetime.strptime(d, '%Y-%m-%d %H:%M:%S %z').isoformat()
        print(f"{i}: git commit --allow-empty -m {msg!r} --date {commit_date_iso}  (author: {a})")
        count += 1

print('\nParsed', count, 'records;', len(bad), 'failures')
if bad:
    print('\nFailures sample:')
    for b in bad[:20]:
        print(b)
