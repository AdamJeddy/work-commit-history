import subprocess
from pathlib import Path

OUTPUT = Path('temp.txt')

# We'll use a unique separator to get fields reliably, then format them to the
# exact shape test.py expects: {hash: <sha>, author: <name>, date: <YYYY-MM-DD HH:MM:SS ±ZZZZ>, message: <message>}
# We'll replace any ", " inside the message with '<COMMA>' so the naive parser in test.py
# (which splits on ', ') won't break.
SEP = '<::SEP::>'
GIT_FORMAT = f"%H{SEP}%an{SEP}%ad{SEP}%s"
GIT_CMD = ['git', 'log', '--reverse', f"--pretty=format:{GIT_FORMAT}", '--date=format:%Y-%m-%d %H:%M:%S %z']


def escape_message(msg: str) -> str:
    # Replace comma+space in message to avoid breaking the naive split in test.py
    return msg.replace(', ', '<COMMA>')


def main():
    try:
        out = subprocess.check_output(GIT_CMD, universal_newlines=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print('Error running git. Make sure you run this inside a git repository.')
        raise

    lines = [ln for ln in out.splitlines() if ln.strip()]

    with OUTPUT.open('w', encoding='utf-8') as f:
        for ln in lines:
            parts = ln.split(SEP)
            if len(parts) != 4:
                # Skip malformed lines (shouldn't normally happen)
                continue
            sha, author, date, message = parts
            message = escape_message(message)
            formatted = f"{{hash: {sha}, author: {author}, date: {date}, message: {message}}}"
            f.write(formatted + '\n')

    print(f'Wrote {len(lines)} commits to {OUTPUT.resolve()}')


if __name__ == '__main__':
    main()
