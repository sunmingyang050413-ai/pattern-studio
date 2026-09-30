from datetime import timedelta
from unittest.mock import patch
import pytest
from django.utils import timezone
from botocore.exceptions import ClientError, EndpointConnectionError
from pipeline.models import Job
from pipeline.tasks import run_job, recover_jobs

pytestmark = pytest.mark.django_db(transaction=True)

def make_job(connection, **kwargs):
    return Job.objects.create(owner=connection.owner, connection=connection, kind='list', **kwargs)

def test_task_success_and_duplicate_delivery(connection):
    job = make_job(connection)
    with patch('pipeline.tasks.storage.list_files', return_value={'files': [], 'cursor': ''}) as listing:
        run_job.run(str(job.id))
        run_job.run(str(job.id))
    job.refresh_from_db()
    assert job.status == 'SUCCESS' and job.progress == 100 and job.attempts == 1
    assert listing.call_count == 1

def test_cancelled_task_never_touches_s3(connection):
    job = make_job(connection, status='CANCELLED', cancel_requested=True)
    with patch('pipeline.tasks.storage.list_files') as listing:
        run_job.run(str(job.id))
    listing.assert_not_called()

def test_access_failure_has_safe_error(connection):
    job = make_job(connection)
    error = ClientError({'Error': {'Code': 'AccessDenied', 'Message': 'SECRET'}}, 'ListObjectsV2')
    with patch('pipeline.tasks.storage.list_files', side_effect=error):
        run_job.run(str(job.id))
    job.refresh_from_db()
    assert job.status == 'FAILED'
    assert 'SECRET' not in job.error
    assert 'S3 access failed' in job.error

def test_transient_failure_retries_bounded(connection):
    job = make_job(connection)
    with patch('pipeline.tasks.storage.list_files', side_effect=EndpointConnectionError(endpoint_url='https://example.com')), patch.object(run_job, 'apply_async') as retry:
        for _ in range(3):
            run_job.run(str(job.id))
    job.refresh_from_db()
    assert job.status == 'FAILED' and job.attempts == 3
    assert retry.call_count == 2

def test_worker_loss_recovery_and_outbox(connection):
    job = make_job(connection, status='RUNNING', attempts=1, heartbeat=timezone.now() - timedelta(minutes=5), run_token='old')
    Job.objects.filter(pk=job.id).update(created_at=timezone.now() - timedelta(minutes=5))
    with patch.object(run_job, 'delay') as publish:
        recover_jobs.run()
    job.refresh_from_db()
    assert job.status == 'QUEUED' and job.run_token == ''
    publish.assert_called_once_with(str(job.id))
