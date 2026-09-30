"""Real HTTP/Celery/Redis/Spark/Groq integration, with explicitly emulated S3.

Run only with compose.integration.yaml. Never uses real AWS credentials.
"""
import csv
import io
import json
import os
import time
import urllib.request
from http.cookiejar import CookieJar
import boto3

assert os.environ.get('AWS_ENDPOINT_URL_S3') == 'http://moto:5000', 'Isolated Moto endpoint required'
BASE = 'http://api:8000'
ROWS = 10000
ACCESS = 'INTEGRATION_TEST_ACCESS'
SECRET = 'INTEGRATION_TEST_SECRET'
BUCKET = 'pattern-studio-integration'
s3 = boto3.client('s3', region_name='us-east-1', aws_access_key_id=ACCESS, aws_secret_access_key=SECRET)
for attempt in range(30):
    try:
        s3.create_bucket(Bucket=BUCKET)
        break
    except Exception:
        if attempt == 29:
            raise
        time.sleep(2)
data = io.StringIO(newline='')
writer = csv.writer(data)
writer.writerow(['id', 'contact', 'name'])
for index in range(ROWS):
    writer.writerow([str(index).zfill(6), f'Contact user{index}@example.com today', '  ALICE   SMITH  '])
s3.put_object(Bucket=BUCKET, Key='fixtures/contacts.csv', Body=data.getvalue().encode())
client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
csrf = ''

def request(path, payload=None):
    headers = {'Content-Type': 'application/json', 'X-CSRFToken': csrf}
    raw = None if payload is None else json.dumps(payload).encode()
    with client.open(urllib.request.Request(BASE + path, data=raw, headers=headers), timeout=30) as response:
        return json.load(response)

def wait_job(job_id):
    deadline = time.monotonic() + 300
    while time.monotonic() < deadline:
        job = request(f'/api/jobs/{job_id}/')
        if job['status'] == 'SUCCESS':
            return job
        assert job['status'] not in ('FAILED', 'CANCELLED'), job
        time.sleep(1)
    raise AssertionError('Job timed out: ' + job_id)

csrf = request('/api/session/')['csrf']
connection = request('/api/connections/', {'bucket': BUCKET, 'region': 'us-east-1', 'access_key': ACCESS, 'secret_key': SECRET})
listing = wait_job(connection['job_id'])
assert any(f['key'] == 'fixtures/contacts.csv' for f in listing['output']['files'])
common = {'connection_id': connection['connection_id']}
source = wait_job(request('/api/jobs/submit/', dict(common, kind='inspect', key='fixtures/contacts.csv'))['job_id'])
evidence = {'storage': 'Moto 5.1.2 emulation, NOT Amazon S3', 'llm': 'real configured provider', 'rows_per_mode': ROWS, 'modes': []}
for mode, prompt, columns in [
    ('replace', 'Match email addresses', ['contact']),
    ('extract', 'Extract an email address', ['contact']),
    ('normalize', 'Trim spaces, collapse whitespace and lowercase text', ['name']),
]:
    job = wait_job(request('/api/jobs/submit/', dict(common, kind='transform', source_id=source['id'], mode=mode, prompt=prompt, columns=columns, replacement='REDACTED'))['job_id'])
    seen = set()
    for page in range(1, ROWS // 100 + 1):
        result = request(f"/api/jobs/{job['id']}/result/?page={page}&page_size=100")
        for values in result['rows']:
            row = dict(zip(result['columns'], values))
            index = int(row['id'])
            assert row['id'] == str(index).zfill(6)
            assert index not in seen
            seen.add(index)
            if mode == 'replace':
                assert row['contact'] == 'Contact REDACTED today'
            elif mode == 'extract':
                assert row['contact_extracted'] == f'user{index}@example.com'
                assert row['contact'] == f'Contact user{index}@example.com today'
            else:
                assert row['name'] == 'alice smith'
    assert seen == set(range(ROWS))
    evidence['modes'].append({'mode': mode, 'verified_rows': len(seen), 'job_status': job['status']})
    print('Verified', mode, len(seen), 'rows across 100 result pages', flush=True)
assert s3.get_object(Bucket=BUCKET, Key='fixtures/contacts.csv')['Body'].read() == data.getvalue().encode()
evidence['source_unchanged'] = True
print(json.dumps(evidence, indent=2), flush=True)
