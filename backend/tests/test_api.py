import json
import pytest
from unittest.mock import patch
from django.test import Client
from pipeline.models import Connection, Job
from pipeline.services.credentials import decrypt

pytestmark = pytest.mark.django_db

def authenticate(client, owner='test-owner'):
    session = client.session
    session['owner'] = owner
    session.save()

def test_connection_encrypts_credentials_and_returns_immediately(client):
    payload = {'bucket': 'my-bucket', 'region': 'us-east-1', 'access_key': 'A' * 20, 'secret_key': 'S' * 40}
    with patch('pipeline.views.enqueue'):
        response = client.post('/api/connections/', json.dumps(payload), content_type='application/json')
    assert response.status_code == 202
    connection = Connection.objects.get()
    assert 'S' * 40 not in connection.encrypted_credentials
    assert decrypt(connection.encrypted_credentials)['secret_key'] == 'S' * 40
    assert 'secret_key' not in response.content.decode()
    assert Job.objects.get().status == 'QUEUED'

def test_invalid_credentials_validation_never_echoes_secrets(client):
    response = client.post('/api/connections/', json.dumps({'secret_key': 'sensitive'}), content_type='application/json')
    assert response.status_code == 400
    assert b'sensitive' not in response.content

def test_job_isolation_and_private_paths(client, connection):
    job = Job.objects.create(owner=connection.owner, connection=connection, kind='inspect', output={'source_path': '/secret/path', 'manifest': {}, 'total': 1})
    assert client.get(f'/api/jobs/{job.id}/').status_code == 404
    authenticate(client)
    response = client.get(f'/api/jobs/{job.id}/')
    assert response.status_code == 200
    assert b'/secret/path' not in response.content

def test_csrf_required():
    client = Client(enforce_csrf_checks=True)
    assert client.post('/api/connections/', '{}', content_type='application/json').status_code == 403

def test_cancel_is_terminal_and_idempotent(client, connection):
    authenticate(client)
    job = Job.objects.create(owner=connection.owner, connection=connection, kind='list')
    for _ in range(2):
        assert client.post(f'/api/jobs/{job.id}/cancel/').json()['status'] == 'CANCELLED'
    job.refresh_from_db()
    assert job.cancel_requested

def test_result_page_limits(client, connection):
    authenticate(client)
    job = Job.objects.create(owner=connection.owner, connection=connection, kind='inspect', status='SUCCESS', output={'manifest': {'columns': [], 'partitions': [], 'directory': '', 'total': 0}})
    for query in ['page_size=101', 'page=0', 'page=abc']:
        assert client.get(f'/api/jobs/{job.id}/result/?{query}').status_code == 400
    assert client.get(f'/api/jobs/{job.id}/result/').json()['rows'] == []

def test_transform_rejects_foreign_or_invalid_columns(client, connection):
    authenticate(client)
    source = Job.objects.create(owner=connection.owner, connection=connection, kind='inspect', status='SUCCESS', output={'columns': ['Email']})
    payload = {'connection_id': str(connection.id), 'kind': 'transform', 'source_id': str(source.id), 'prompt': 'emails', 'columns': ['NotAColumn']}
    assert client.post('/api/jobs/submit/', json.dumps(payload), content_type='application/json').status_code == 400
