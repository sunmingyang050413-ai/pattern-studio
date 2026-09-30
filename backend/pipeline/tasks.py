import logging
import shutil
import threading
import time
import uuid
from datetime import timedelta
from celery import shared_task
from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone
from botocore.exceptions import ClientError, EndpointConnectionError, ReadTimeoutError
from cryptography.fernet import InvalidToken
from openai import APIConnectionError, APITimeoutError, RateLimitError
from .models import Connection, Job
from .services import engine, storage
from .services.planner import plan_request

logger = logging.getLogger('pipeline')
TERMINAL = ['SUCCESS', 'FAILED', 'CANCELLED']

class Cancelled(Exception):
    pass

@shared_task(bind=True, max_retries=2, name='pipeline.tasks.run_job')
def run_job(self, job_id):
    started = time.monotonic()
    token = str(uuid.uuid4())
    if not Job.objects.filter(pk=job_id, status='QUEUED', cancel_requested=False).update(status='RUNNING', run_token=token, heartbeat=timezone.now(), stage='Starting worker', progress=2):
        return
    job = Job.objects.select_related('connection').get(pk=job_id)
    job.attempts += 1
    Job.objects.filter(pk=job_id, run_token=token).update(attempts=job.attempts)
    stop = threading.Event()
    spark = None
    directory = settings.DATA_ROOT / str(job.id) / token
    directory.mkdir(parents=True, exist_ok=True)

    def checkpoint():
        state = Job.objects.filter(pk=job_id, run_token=token).values('cancel_requested', 'status').first()
        if not state or state['cancel_requested'] or state['status'] != 'RUNNING':
            raise Cancelled()

    def progress(value, stage):
        checkpoint()
        Job.objects.filter(pk=job_id, run_token=token).update(progress=value, stage=stage, heartbeat=timezone.now())

    def heartbeat():
        close_old_connections()
        try:
            while not stop.wait(3):
                state = Job.objects.filter(pk=job_id, run_token=token).values('cancel_requested', 'status').first()
                if not state or state['cancel_requested'] or state['status'] != 'RUNNING':
                    if spark:
                        spark.sparkContext.cancelJobGroup(token)
                    return
                Job.objects.filter(pk=job_id, run_token=token).update(heartbeat=timezone.now())
        finally:
            close_old_connections()

    monitor = threading.Thread(target=heartbeat, daemon=True)
    monitor.start()
    try:
        if job.kind == 'list':
            progress(20, 'Connecting to Amazon S3')
            output = storage.list_files(job.connection, job.payload)
        else:
            if job.kind == 'inspect':
                progress(10, 'Downloading selected S3 object')
                path = storage.download(job.connection, job.payload['key'], directory, checkpoint)
            else:
                source = Job.objects.get(pk=job.payload['source_id'], owner=job.owner, status='SUCCESS', kind='inspect')
                path = source.output['source_path']
            progress(30, 'Starting Spark and parsing data')
            spark = engine.spark_session()
            spark.sparkContext.setLogLevel('ERROR')
            spark.sparkContext.setJobGroup(token, 'Data processing', interruptOnCancel=True)
            frame = engine.load_csv(spark, path)
            output = {}
            if job.kind == 'transform':
                progress(40, 'Generating and validating transformation plan')
                plan, hit = plan_request(job.payload['prompt'], job.payload['mode'])
                frame = engine.transform(frame, job.payload['columns'], job.payload['mode'], plan, job.payload['replacement'])
                output.update(plan=plan.model_dump(), cache_hit=hit)
            progress(60, 'Processing Spark partitions and writing result pages')
            manifest = engine.materialize(frame, directory / 'result')
            output.update(manifest=manifest, columns=manifest['columns'], total=manifest['total'])
            if job.kind == 'inspect':
                output['source_path'] = str(path)
        checkpoint()
        updated = Job.objects.filter(pk=job_id, run_token=token, status='RUNNING', cancel_requested=False).update(status='SUCCESS', progress=100, stage='Complete', output=output, updated_at=timezone.now())
        if not updated:
            raise Cancelled()
        logger.info('job_complete id=%s kind=%s attempts=%s rows=%s seconds=%.3f', job_id, job.kind, job.attempts, output.get('total', 0), time.monotonic() - started)
    except Exception as exc:
        current = Job.objects.filter(pk=job_id, run_token=token).first()
        cancelled = isinstance(exc, Cancelled) or not current or current.cancel_requested or current.status == 'CANCELLED'
        transient = isinstance(exc, (EndpointConnectionError, ReadTimeoutError, APIConnectionError, APITimeoutError, RateLimitError))
        if isinstance(exc, ClientError):
            transient = exc.response.get('ResponseMetadata', {}).get('HTTPStatusCode', 0) >= 500
        if cancelled:
            Job.objects.filter(pk=job_id, run_token=token).update(status='CANCELLED', stage='Cancelled', output={})
        elif transient and job.attempts < 3:
            Job.objects.filter(pk=job_id, run_token=token).update(status='QUEUED', stage='Temporary service failure; retry scheduled', progress=0)
            # Beat's persistent outbox will republish if the broker is unavailable here.
            run_job.apply_async(args=[job_id], countdown=10 * job.attempts)
        else:
            if isinstance(exc, storage.UserError):
                message = str(exc)
            elif isinstance(exc, (ClientError, EndpointConnectionError, ReadTimeoutError)):
                message = 'S3 access failed. Check credentials, region, bucket, object key and ListBucket/GetObject permissions.'
            elif isinstance(exc, InvalidToken):
                message = 'Credentials have expired. Reconnect to your S3 bucket.'
            else:
                message = 'Processing failed. Check file format and service configuration; retry the job. Reference: ' + str(job.id)
            Job.objects.filter(pk=job_id, run_token=token).update(status='FAILED', stage='Failed', error=message, updated_at=timezone.now())
            # Never log exception messages: vendor exceptions may contain request data.
            logger.warning('job_failed id=%s error_type=%s', job_id, type(exc).__name__)
        shutil.rmtree(directory, ignore_errors=True)
    finally:
        stop.set()
        monitor.join(timeout=5)
        if spark:
            spark.stop()
        Job.objects.filter(pk=job_id, run_token=token).update(run_token='')

@shared_task(name='pipeline.tasks.recover_jobs')
def recover_jobs():
    now = timezone.now()
    Job.objects.filter(status='CANCELLED', heartbeat__lt=now - timedelta(minutes=2)).update(run_token='')
    for job in Job.objects.filter(status='RUNNING', heartbeat__lt=now - timedelta(minutes=2)):
        status = 'CANCELLED' if job.cancel_requested else ('FAILED' if job.attempts >= 3 else 'QUEUED')
        Job.objects.filter(pk=job.pk, run_token=job.run_token, heartbeat__lt=now - timedelta(minutes=2)).update(status=status, run_token='', progress=0, stage='Worker interrupted; recovering' if status == 'QUEUED' else status, error='Worker stopped repeatedly.' if status == 'FAILED' else '')
    for job in Job.objects.filter(status='QUEUED', cancel_requested=False, created_at__lt=now - timedelta(seconds=20)).only('id')[:100]:
        run_job.delay(str(job.id))

@shared_task(name='pipeline.tasks.expire_data')
def expire_data():
    cutoff = timezone.now() - timedelta(hours=24)
    for connection in Connection.objects.filter(created_at__lt=cutoff):
        if connection.job_set.filter(status__in=['QUEUED', 'RUNNING']).exists() or connection.job_set.filter(cancel_requested=True).exclude(run_token='').exists():
            continue
        for job in connection.job_set.all():
            shutil.rmtree(settings.DATA_ROOT / str(job.id), ignore_errors=True)
        connection.delete()
