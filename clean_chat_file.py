from pathlib import Path

p = Path('chat_conv_dashboard.txt')
bak = p.with_suffix('.txt.bak')

# Read original and write a backup (overwrite existing backup only if missing)
orig_text = p.read_text(encoding='utf-8')
if not bak.exists():
    bak.write_text(orig_text, encoding='utf-8')

lines = orig_text.splitlines()

records = []
buffer = []

# Join lines until we encounter a line that ends a record (we expect records to end with '},')
for line in lines:
    if not line.strip():
        # preserve blank lines as-is
        if buffer:
            # treat any dangling buffer as a single record
            records.append(''.join(buffer))
            buffer = []
        records.append('')
        continue

    if line.lstrip().startswith('{hash:') and not buffer:
        buffer.append(line.rstrip('\n'))
        # if this line already completes the record
        if line.rstrip().endswith('},') or line.rstrip().endswith('}'):
            records.append(''.join(buffer))
            buffer = []
        continue

    # continuation lines (either we are buffering or unexpected line)
    if buffer:
        buffer.append(line.rstrip('\n'))
        if line.rstrip().endswith('},') or line.rstrip().endswith('}'):
            records.append(''.join(buffer))
            buffer = []
        continue

    # any other non-record-starting line, keep as-is
    records.append(line)

# If anything left in buffer, flush it
if buffer:
    records.append(''.join(buffer))

out_lines = []
for rec in records:
    if not rec or not rec.lstrip().startswith('{hash:'):
        out_lines.append(rec)
        continue

    # collapse internal newlines that may have split words (join without adding spaces)
    rec_single = ''.join(part.strip() for part in rec.splitlines())
    # ensure record ends with '},' for consistency
    if not rec_single.rstrip().endswith('},') and rec_single.rstrip().endswith('}'):
        rec_single = rec_single.rstrip() + ','
    # strip outer braces for parsing
    stripped = rec_single.strip()
    if stripped.startswith('{'):
        stripped = stripped[1:]
    if stripped.endswith('},'):
        stripped = stripped[:-2]
    elif stripped.endswith('}'):
        stripped = stripped[:-1]

    parts = stripped.split(', ', 3)
    if len(parts) < 4:
        # fallback: keep the original single-line record but normalized
        out_lines.append(rec_single)
        continue

    sha = parts[0].split(': ', 1)[1].strip()
    author = parts[1].split(': ', 1)[1].strip()
    date = parts[2].split(': ', 1)[1].strip()
    message = parts[3].split(': ', 1)[1]

    # remove trailing record commas/braces from message
    message = message.rstrip('},').rstrip()
    # if message ends with a stray '}', remove it
    if message.endswith('}'):
        message = message[:-1].rstrip()

    # Reconstruct normalized record and ensure trailing '},'
    out_lines.append(f"{{hash: {sha}, author: {author}, date: {date}, message: {message}}},")

# write cleaned file
p.write_text('\n'.join(out_lines) + '\n', encoding='utf-8')
print(f'Backup written to: {bak}')
print('Wrote cleaned chat_conv_dashboard.txt')
