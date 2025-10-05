from datetime import datetime

path = 'chat_conv_dashboard.txt'
problems = []
line_no = 0
with open(path, 'r', encoding='utf-8') as f:
    for line in f:
        line_no += 1
        ln = line.rstrip('\n')
        if not ln.startswith('{hash:'):
            continue
        stripped = ln.strip('{}')
        parts = stripped.split(', ')
        if len(parts) < 4:
            problems.append((line_no, 'too_few_parts', ln))
            continue
        try:
            commit_hash = parts[0].split(': ',1)[1]
            author = parts[1].split(': ',1)[1]
            date_str = parts[2].split(': ',1)[1]
            message = parts[3].split(': ',1)[1]
        except Exception as e:
            problems.append((line_no, 'parse_error', str(e), ln))
            continue
        # check date parse
        try:
            datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S %z')
        except Exception as e:
            problems.append((line_no, 'date_parse', str(e), date_str))
        # check for literal ', ' inside message (should be escaped to <COMMA>)
        if ', ' in message:
            # if that's just the trailing '},' after message it will be stripped by test.py via rstrip, but we care about ', ' inside message content
            # exclude if message ends with '},' or '}' etc
            trimmed = message.rstrip('},')
            if ', ' in trimmed:
                problems.append((line_no, 'unescaped_comma_in_message', trimmed))

print('Validation report for', path)
if not problems:
    print('No problems found — file is compatible with test.py parsing.')
else:
    print('Found', len(problems), 'problem(s):')
    for p in problems[:200]:
        print(p)

# show sample parsed lines
print('\nSample parsed entries (first 10):')
line_no = 0
count = 0
with open(path, 'r', encoding='utf-8') as f:
    for line in f:
        if not line.startswith('{hash:'):
            continue
        stripped = line.strip('{}')
        parts = stripped.split(', ')
        if len(parts) < 4:
            continue
        commit_hash = parts[0].split(': ',1)[1]
        author = parts[1].split(': ',1)[1]
        date_str = parts[2].split(': ',1)[1]
        message = parts[3].split(': ',1)[1].rstrip('},')
        print(f'{commit_hash} | {author} | {date_str} | {message[:80]}')
        count += 1
        if count >= 100:
            break
