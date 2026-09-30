"""Read configuration without printing secrets or calling paid/external APIs."""
from pathlib import Path
import argparse
import shutil
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--env-file', type=Path, default=Path(__file__).resolve().parent.parent / '.env')
args = parser.parse_args()
if not args.env_file.exists():
    raise SystemExit('NOT READY: run python scripts/configure.py first.')
values = {}
for line in args.env_file.read_text(encoding='utf-8').splitlines():
    if '=' in line and not line.lstrip().startswith('#'):
        key, value = line.split('=', 1)
        values[key.strip()] = value.strip()
provider = values.get('LLM_PROVIDER', 'openai')
key_name = {'groq': 'GROQ_API_KEY', 'openai': 'OPENAI_API_KEY'}.get(provider)
checks = {
    'Supported LLM provider': key_name is not None,
    'Provider key configured (value hidden)': bool(values.get(key_name or '')),
    'Docker CLI installed': shutil.which('docker') is not None,
    'Encryption key configured': bool(values.get('CREDENTIAL_KEY')) and 'run-python' not in values.get('CREDENTIAL_KEY', ''),
    'Django secret configured': bool(values.get('DJANGO_SECRET_KEY')) and 'run-python' not in values.get('DJANGO_SECRET_KEY', ''),
}
for name, ok in checks.items():
    print(('OK   ' if ok else 'TODO ') + name)
print('This check does not validate credentials, billing tier, server health or public deployment.')
sys.exit(0 if all(checks.values()) else 1)
