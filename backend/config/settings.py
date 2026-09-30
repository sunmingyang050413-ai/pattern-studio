import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
DEBUG = False
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,api,testserver').split(',')
INSTALLED_APPS = ['django.contrib.contenttypes', 'django.contrib.sessions', 'pipeline']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware']
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': os.getenv('POSTGRES_DB', 'regex'), 'USER': os.getenv('POSTGRES_USER', 'regex'), 'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''), 'HOST': os.getenv('POSTGRES_HOST', 'db'), 'PORT': 5432}}
if os.getenv('TEST_SQLITE') == '1':
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'test.sqlite3'}}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
USE_TZ = True
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = os.getenv('REDIS_RESULT_URL', 'redis://redis:6379/1')
CELERY_TASK_IGNORE_RESULT = False
CELERY_RESULT_EXPIRES = 86400
CELERY_TASK_PUBLISH_RETRY = False
CELERY_BROKER_CONNECTION_TIMEOUT = 1
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_SEND_SENT_EVENT = True
CELERY_WORKER_SEND_TASK_EVENTS = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_TASK_TIME_LIMIT = 3600
CELERY_TASK_SOFT_TIME_LIMIT = 3540
CELERY_BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3900, 'socket_connect_timeout': 1, 'socket_timeout': 1}
CELERY_BEAT_SCHEDULE = {'recover-jobs': {'task': 'pipeline.tasks.recover_jobs', 'schedule': 30.0}, 'expire-data': {'task': 'pipeline.tasks.expire_data', 'schedule': 3600.0}}
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.redis.RedisCache', 'LOCATION': os.getenv('REDIS_CACHE_URL', 'redis://redis:6379/2')}}
DATA_ROOT = Path(os.getenv('DATA_ROOT', '/data'))
CREDENTIAL_KEY = os.environ['CREDENTIAL_KEY']
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 86400
SESSION_COOKIE_SECURE = os.getenv('HTTPS', '0') == '1'
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
CSRF_TRUSTED_ORIGINS = [x for x in os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:8080').split(',') if x]
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_CONTENT_TYPE_NOSNIFF = True
DATA_UPLOAD_MAX_MEMORY_SIZE = 32768
LOGGING = {'version': 1, 'disable_existing_loggers': False, 'handlers': {'console': {'class': 'logging.StreamHandler'}}, 'root': {'handlers': ['console'], 'level': 'WARNING'}, 'loggers': {'pipeline': {'handlers': ['console'], 'level': 'INFO', 'propagate': False}}}
