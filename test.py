import os
import subprocess
from datetime import datetime

# Path to the text file containing commit information
commit_file_path = 'item_creation_fe.txt'

# Read the commit information from the text file
with open(commit_file_path, 'r') as file:
    commit_lines = file.readlines()

# Extract commit details and create commits
for line in commit_lines:
    if line.startswith('{hash:'):
        # Extract commit details
        parts = line.strip('{}').split(', ')
        commit_hash = parts[0].split(': ')[1]
        author = parts[1].split(': ')[1]
        date_str = parts[2].split(': ')[1]
        message = parts[3].split(': ')[1]

        # Unescape any '<COMMA>' placeholders (we replace ', ' when exporting)
        message = message.replace('<COMMA>', ', ')
        # Trim any accidental trailing commas or braces that might appear
        message = message.rstrip('},')

        # Add the prefix to the commit message
        message = f"[Temperature Dashboard] {message}"

        # Convert date string to datetime object
        commit_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S %z')

        # Set the environment variables for the commit
        env = os.environ.copy()
        env['GIT_AUTHOR_DATE'] = commit_date.isoformat()
        env['GIT_COMMITTER_DATE'] = commit_date.isoformat()

        # Create the commit with the specific date and time
        subprocess.run(['git', 'commit', '--allow-empty', '-m', message, '--date', commit_date.isoformat()], env=env)

print("Commits created successfully.")