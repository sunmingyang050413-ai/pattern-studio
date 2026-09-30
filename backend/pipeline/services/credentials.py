import json
from cryptography.fernet import Fernet
from django.conf import settings

def encrypt(values):
    return Fernet(settings.CREDENTIAL_KEY.encode()).encrypt(json.dumps(values).encode()).decode()

def decrypt(value):
    return json.loads(Fernet(settings.CREDENTIAL_KEY.encode()).decrypt(value.encode(), ttl=86400))
