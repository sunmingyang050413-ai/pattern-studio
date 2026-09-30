import os
import tempfile
from cryptography.fernet import Fernet

os.environ.setdefault('DJANGO_SECRET_KEY', 'test-only-not-a-deployment-secret')
os.environ.setdefault('CREDENTIAL_KEY', Fernet.generate_key().decode())
os.environ.setdefault('TEST_SQLITE', '1')
os.environ.setdefault('DATA_ROOT', tempfile.mkdtemp(prefix='pattern-tests-'))
os.environ.setdefault('SPARK_LOCAL_IP', '127.0.0.1')
os.environ.setdefault('SPARK_PARTITIONS', '2')

import pytest

@pytest.fixture(autouse=True)
def local_cache(settings):
    settings.CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
    from django.core.cache import cache
    cache.clear()

@pytest.fixture
def connection(db):
    from pipeline.models import Connection
    from pipeline.services.credentials import encrypt
    return Connection.objects.create(owner='test-owner', bucket='test-bucket', region='us-east-1', encrypted_credentials=encrypt({'access_key': 'A' * 20, 'secret_key': 'S' * 40, 'session_token': ''}))
