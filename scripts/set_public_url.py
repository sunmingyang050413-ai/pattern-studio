"""Prepare same-origin HTTPS settings. Does NOT start a tunnel or publish anything."""
import argparse
from pathlib import Path
import re
from urllib.parse import urlparse

def update_environment(text, url):
    parsed = urlparse(url)
    host = parsed.hostname or ''
    if (parsed.scheme != 'https' or parsed.username or parsed.password or parsed.port
            or parsed.path not in ('', '/') or parsed.query or parsed.fragment
            or not re.fullmatch(r'[a-z0-9-]+\.ngrok-free\.(?:app|dev)', host)):
        raise ValueError('Use the assigned HTTPS ngrok-free.app or ngrok-free.dev URL, without a path.')
    values = {'NGROK_DOMAIN': host, 'ALLOWED_HOSTS': f'{host},localhost,127.0.0.1,api',
              'CSRF_TRUSTED_ORIGINS': 'https://' + host, 'HTTPS': '1'}
    lines = []
    for line in text.splitlines():
        key = line.split('=', 1)[0]
        if key in values:
            lines.append(f'{key}={values.pop(key)}')
        else:
            lines.append(line)
    lines.extend(f'{key}={value}' for key, value in values.items())
    return '\n'.join(lines) + '\n'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('--env-file', type=Path, default=Path(__file__).resolve().parent.parent / '.env')
    args = parser.parse_args()
    try:
        updated = update_environment(args.env_file.read_text(encoding='utf-8'), args.url)
    except (ValueError, FileNotFoundError) as exc:
        raise SystemExit(str(exc)) from None
    args.env_file.write_text(updated, encoding='utf-8')
    print('Prepared HTTPS host and CSRF settings. No tunnel has been started. Use the HTTPS URL after deployment; Secure cookies will not work over plain HTTP.')

if __name__ == '__main__':
    main()
