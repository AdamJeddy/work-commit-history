from datetime import datetime

path = 'chat_conv_dashboard.txt'
errors = []
count = 0
with open(path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, start=1):
        if not line.lstrip().startswith('{hash:'):
            continue
        stripped = line.strip().lstrip('{').rstrip('\n')
        # keep the trailing parts so we can inspect them
        parts = stripped.split(', ', 3)
        if len(parts) < 4:
            errors.append((i, 'too_few_parts', line))
            continue
        commit_hash = parts[0].split(': ',1)[1]
        author = parts[1].split(': ',1)[1]
        date_str = parts[2].split(': ',1)[1]
        message_raw = parts[3].split(': ',1)[1]

        message_stripped = message_raw.rstrip('},').rstrip()

        # print sample for first 50
        if count < 200:
            print(f'{i}: hash={commit_hash!r} author={author!r} date={date_str!r}')
            print(f'    raw_message_repr: {message_raw!r}')
            print(f'    after_rstrip_repr: {message_stripped!r}\n')
        count += 1

print('\nFinished parsing. Sample lines shown:', min(count, 200))
if errors:
    print('Errors:', errors[:20])
