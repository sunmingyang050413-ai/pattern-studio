"""Isolated test-only settings. Never use this module for deployment."""
import os
import tempfile
from cryptography.fernet import Fernet
os.environ.setdefault('DJANGO_SECRET_KEY', 'test-only-not-a-deployment-secret')
os.environ.setdefault('CREDENTIAL_KEY', Fernet.generate_key().decode())
os.environ['TEST_SQLITE'] = '1'
os.environ.setdefault('DATA_ROOT', tempfile.mkdtemp(prefix='pattern-tests-'))
from .settings import *  # noqa: F403
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
