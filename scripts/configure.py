"""Generate local secrets using only the Python standard library; never overwrite .env."""
import base64
from pathlib import Path
import secrets

root = Path(__file__).resolve().parent.parent
target = root / '.env'
if target.exists():
    raise SystemExit('.env already exists; edit it directly. Nothing overwritten.')
text = (root / '.env.example').read_text()
values = {'DJANGO_SECRET_KEY': secrets.token_urlsafe(48), 'CREDENTIAL_KEY': base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(), 'POSTGRES_PASSWORD': secrets.token_hex(24), 'FLOWER_PASSWORD': secrets.token_hex(24)}
for key, value in values.items():
    text = text.replace(f'{key}=run-python-scripts-configure.py', f'{key}={value}')
target.write_text(text, encoding='utf-8')
target.chmod(0o600)
print('Created .env with fresh secrets. Free-first configuration: Groq. Set GROQ_API_KEY before running transformations. No cloud services were created.')
