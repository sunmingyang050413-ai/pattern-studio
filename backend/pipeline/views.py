import json
import uuid
from functools import wraps
from django.db import transaction
from django.db.models import Count
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from pydantic import ValidationError
from .models import Connection, Job
from .schemas import Connect, Submit
from .services.credentials import encrypt
from .services.engine import read_page
from .tasks import run_job

def owner(request):
    if 'owner' not in request.session:
        request.session['owner'] = str(uuid.uuid4())
    return request.session['owner']

def validation(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        try:
            return view(request, *args, **kwargs)
        except (ValidationError, ValueError, KeyError, TypeError):
            return JsonResponse({'error': 'Invalid request. Check required fields and input limits.'}, status=400)
    return wrapped

def enqueue(job):
    try:
        run_job.delay(str(job.id))
    except Exception:
        # A committed QUEUED row is an outbox entry; Beat retries delivery.
        pass

def create_job(user, connection, kind, payload):
    job = Job.objects.create(owner=user, connection=connection, kind=kind, payload=payload)
    transaction.on_commit(lambda: enqueue(job))
    return job

@require_GET
def session(request):
    user = owner(request)
    connections = [{'id': str(c.id), 'bucket': c.bucket} for c in Connection.objects.filter(owner=user).order_by('-created_at')]
    return JsonResponse({'csrf': get_token(request), 'connections': connections})

@require_GET
def health(request):
    return JsonResponse({'status': 'ok'})

@require_POST
@validation
def connect(request):
    data = Connect.model_validate_json(request.body)
    user = owner(request)
    if Connection.objects.filter(owner=user).count() >= 10:
        return JsonResponse({'error': 'Connection limit reached. Disconnect an old connection first.'}, status=429)
    with transaction.atomic():
        connection = Connection.objects.create(owner=user, bucket=data.bucket, region=data.region, encrypted_credentials=encrypt(data.model_dump(include={'access_key', 'secret_key', 'session_token'})))
        job = create_job(user, connection, 'list', {})
    return JsonResponse({'connection_id': str(connection.id), 'job_id': str(job.id)}, status=202)

@require_POST
def disconnect(request, connection_id):
    connection = get_object_or_404(Connection, pk=connection_id, owner=owner(request))
    if connection.job_set.filter(status__in=['RUNNING', 'QUEUED']).exists() or connection.job_set.filter(cancel_requested=True).exclude(run_token='').exists():
        return JsonResponse({'error': 'Cancel active jobs before disconnecting.'}, status=409)
    import shutil
    from django.conf import settings
    for job in connection.job_set.all():
        shutil.rmtree(settings.DATA_ROOT / str(job.id), ignore_errors=True)
    connection.delete()
    return JsonResponse({'disconnected': True})

@require_POST
@validation
def submit(request):
    data = Submit.model_validate_json(request.body)
    user = owner(request)
    with transaction.atomic():
        connection = get_object_or_404(Connection.objects.select_for_update(), pk=data.connection_id, owner=user)
        if Job.objects.filter(owner=user, status__in=['QUEUED', 'RUNNING']).count() >= 3:
            return JsonResponse({'error': 'Wait for an active job to finish before starting another.'}, status=429)
        if data.kind == 'inspect' and not data.key:
            raise ValueError()
        if data.kind == 'transform':
            source = get_object_or_404(Job, pk=data.source_id, owner=user, connection=connection, kind='inspect', status='SUCCESS')
            if not data.prompt.strip() or not data.columns or len(set(data.columns)) != len(data.columns) or any(c not in source.output['columns'] for c in data.columns):
                raise ValueError()
        job = create_job(user, connection, data.kind, data.model_dump(mode='json', exclude={'connection_id', 'kind'}))
    return JsonResponse({'job_id': str(job.id)}, status=202)

def serialize(job):
    output = {k: v for k, v in job.output.items() if k not in ['manifest', 'source_path']}
    return {'id': str(job.id), 'connection_id': str(job.connection_id), 'kind': job.kind, 'status': job.status, 'progress': job.progress, 'stage': job.stage, 'error': job.error, 'attempts': job.attempts, 'cancel_requested': job.cancel_requested, 'created_at': job.created_at.isoformat(), 'output': output}

@require_GET
def jobs(request):
    return JsonResponse({'jobs': [serialize(j) for j in Job.objects.filter(owner=owner(request)).order_by('-created_at')[:25]]})

@require_GET
def detail(request, job_id):
    return JsonResponse(serialize(get_object_or_404(Job, pk=job_id, owner=owner(request))))

@require_GET
@validation
def result(request, job_id):
    job = get_object_or_404(Job, pk=job_id, owner=owner(request))
    if job.status != 'SUCCESS' or 'manifest' not in job.output:
        return JsonResponse({'error': 'Result is not ready.'}, status=409)
    page, size = int(request.GET.get('page', 1)), int(request.GET.get('page_size', 50))
    if page < 1 or size < 1 or size > 100:
        raise ValueError()
    response = JsonResponse(read_page(job.output['manifest'], page, size))
    response['Cache-Control'] = 'no-store'
    return response

@require_POST
def cancel(request, job_id):
    job = get_object_or_404(Job, pk=job_id, owner=owner(request))
    Job.objects.filter(pk=job.id, status__in=['QUEUED', 'RUNNING']).update(cancel_requested=True, status='CANCELLED', stage='Cancellation requested', updated_at=timezone.now())
    job.refresh_from_db()
    return JsonResponse(serialize(job))

@require_GET
def metrics(request):
    # Session-scoped metrics; global infrastructure metrics are exposed through Flower.
    return JsonResponse({'jobs': list(Job.objects.filter(owner=owner(request)).values('status').annotate(count=Count('id')))})
