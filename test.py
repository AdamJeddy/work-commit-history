import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(description='Create empty commits from a formatted export file')
    p.add_argument('--file', '-f', default='layla_dashboard_FE - adam_commits.json', help='input file')
    p.add_argument('--dry-run', action='store_true', default=True, help='print commands instead of running')
    p.add_argument('--no-dry-run', dest='dry_run', action='store_false', help='actually run git commit')
    p.add_argument('--prefix', default='[Layla Dashboard FE] ', help='prefix to add to commit message')
    return p.parse_args()


def load_json_records(path_obj: Path):
    records = []
    fallback = re.compile(r'^\{"hash": "(?P<hash>.+?)", "author": "(?P<author>.+?)", "date": "(?P<date>.+?)", "message": "(?P<message>.*)"\},?$')
    with path_obj.open('r', encoding='utf-8') as f:
        for line_no, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line:
                continue
            if line.endswith(','):
                line = line[:-1]
            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                m = fallback.match(line)
                if not m:
                    print(f'Line {line_no}: JSON decode error: {e}', file=sys.stderr)
                    continue
                data = {
                    'hash': m.group('hash'),
                    'author': m.group('author'),
                    'date': m.group('date'),
                    'message': m.group('message')
                }
            records.append((line_no, data))
    return records


def load_text_records(path_obj: Path):
    pattern = re.compile(r"^\{hash:\s*(?P<h>[^,}]+),\s*author:\s*(?P<a>[^,}]+),\s*date:\s*(?P<d>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [+-]\d{4}),\s*message:\s*(?P<m>.*)\},?\s*$")
    records = []
    with path_obj.open('r', encoding='utf-8') as f:
        for line_no, line in enumerate(f, start=1):
            if not line.lstrip().startswith('{hash:'):
                continue
            m = pattern.match(line.strip())
            if not m:
                print(f'Line {line_no}: failed to parse: {line.strip()}', file=sys.stderr)
                continue
            records.append((line_no, {
                'hash': m.group('h').strip(),
                'author': m.group('a').strip(),
                'date': m.group('d').strip(),
                'message': m.group('m')
            }))
    return records


def iter_records(path: str):
    path_obj = Path(path)
    if not path_obj.exists():
        print(f'Input file not found: {path}', file=sys.stderr)
        sys.exit(2)

    if path_obj.suffix.lower() == '.json':
        return load_json_records(path_obj)
    return load_text_records(path_obj)


def main():
    args = parse_args()

    total = 0
    succeeded = 0
    failed = 0

    for line_no, record in iter_records(args.file):
        commit_hash = record.get('hash', '').strip()
        author = record.get('author', 'Unknown').strip() or 'Unknown'
        date_str = record.get('date', '').strip()
        message = record.get('message', '')

        if not commit_hash or not date_str:
            print(f'Line {line_no}: missing hash or date', file=sys.stderr)
            failed += 1
            continue

        message = message.replace('<COMMA>', ', ')
        message = message.rstrip('},').rstrip()
        message = f"{args.prefix}{message}"

        try:
            commit_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S %z')
        except Exception as e:
            print(f'Line {line_no}: date parse error "{date_str}": {e}', file=sys.stderr)
            failed += 1
            continue

        env = os.environ.copy()
        env['GIT_AUTHOR_DATE'] = commit_date.isoformat()
        env['GIT_COMMITTER_DATE'] = commit_date.isoformat()
        env['GIT_AUTHOR_NAME'] = author
        env['GIT_COMMITTER_NAME'] = author

        cmd = ['git', 'commit', '--allow-empty', '-m', message, '--date', commit_date.isoformat()]

        total += 1
        if args.dry_run:
            print(f'{line_no}: DRY-RUN -> {" ".join(cmd)}  (author: {author})')
            succeeded += 1
            continue

        print(f'Line {line_no}: running git commit for {commit_hash} (author: {author})')
        p = subprocess.run(cmd, env=env)
        if p.returncode == 0:
            succeeded += 1
        else:
            print(f'Line {line_no}: git commit failed with exit {p.returncode}', file=sys.stderr)
            failed += 1

    print('\nSummary:')
    print(f'  total lines processed: {total}')
    print(f'  succeeded (or would succeed in dry-run): {succeeded}')
    print(f'  failed: {failed}')


if __name__ == '__main__':
    main()