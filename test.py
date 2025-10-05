import argparse
import os
import re
import subprocess
import sys
from datetime import datetime


def parse_args():
    p = argparse.ArgumentParser(description='Create empty commits from a formatted export file')
    p.add_argument('--file', '-f', default='translation_tool_fe.txt', help='input file')
    p.add_argument('--dry-run', action='store_true', default=True, help='print commands instead of running')
    p.add_argument('--no-dry-run', dest='dry_run', action='store_false', help='actually run git commit')
    p.add_argument('--prefix', default='[Translation Tool FE] ', help='prefix to add to commit message')
    return p.parse_args()


def main():
    args = parse_args()

    pattern = re.compile(r"^\{hash:\s*(?P<h>[^,}]+),\s*author:\s*(?P<a>[^,}]+),\s*date:\s*(?P<d>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [+-]\d{4}),\s*message:\s*(?P<m>.*)\},?\s*$")

    path = args.file
    if not os.path.exists(path):
        print(f'Input file not found: {path}', file=sys.stderr)
        sys.exit(2)

    total = 0
    succeeded = 0
    failed = 0

    with open(path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, start=1):
            if not line.lstrip().startswith('{hash:'):
                continue
            m = pattern.match(line.strip())
            if not m:
                print(f'Line {i}: failed to parse: {line.strip()}', file=sys.stderr)
                failed += 1
                continue

            commit_hash = m.group('h').strip()
            author = m.group('a').strip()
            date_str = m.group('d').strip()
            message = m.group('m')

            # Unescape placeholders and normalize
            message = message.replace('<COMMA>', ', ')
            message = message.rstrip('},').rstrip()
            message = f"{args.prefix}{message}"

            try:
                commit_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S %z')
            except Exception as e:
                print(f'Line {i}: date parse error "{date_str}": {e}', file=sys.stderr)
                failed += 1
                continue

            env = os.environ.copy()
            env['GIT_AUTHOR_DATE'] = commit_date.isoformat()
            env['GIT_COMMITTER_DATE'] = commit_date.isoformat()
            # preserve parsed author name (no email available) — Git will fall back to config for email
            env['GIT_AUTHOR_NAME'] = author
            env['GIT_COMMITTER_NAME'] = author

            cmd = ['git', 'commit', '--allow-empty', '-m', message, '--date', commit_date.isoformat()]

            total += 1
            if args.dry_run:
                print(f'{i}: DRY-RUN -> {" ".join(cmd)}  (author: {author})')
                succeeded += 1
                continue

            print(f'Line {i}: running git commit for {commit_hash} (author: {author})')
            p = subprocess.run(cmd, env=env)
            if p.returncode == 0:
                succeeded += 1
            else:
                print(f'Line {i}: git commit failed with exit {p.returncode}', file=sys.stderr)
                failed += 1

    print('\nSummary:')
    print(f'  total lines processed: {total}')
    print(f'  succeeded (or would succeed in dry-run): {succeeded}')
    print(f'  failed: {failed}')


if __name__ == '__main__':
    main()