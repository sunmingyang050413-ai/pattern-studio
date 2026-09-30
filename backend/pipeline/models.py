import uuid
from django.db import models


class Connection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.CharField(max_length=64, db_index=True)
    bucket = models.CharField(max_length=63)
    region = models.CharField(max_length=40)
    encrypted_credentials = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Job(models.Model):
    class Status(models.TextChoices):
        QUEUED = 'QUEUED'
        RUNNING = 'RUNNING'
        SUCCESS = 'SUCCESS'
        FAILED = 'FAILED'
        CANCELLED = 'CANCELLED'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.CharField(max_length=64, db_index=True)
    connection = models.ForeignKey(Connection, on_delete=models.CASCADE)
    kind = models.CharField(max_length=16)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.QUEUED, db_index=True)
    progress = models.PositiveSmallIntegerField(default=0)
    stage = models.CharField(max_length=128, default='Waiting for a worker')
    output = models.JSONField(default=dict)
    error = models.CharField(max_length=512, blank=True)
    cancel_requested = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)
    run_token = models.CharField(max_length=36, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    heartbeat = models.DateTimeField(null=True)
