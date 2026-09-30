from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=False)

class Connect(StrictModel):
    bucket: str = Field(min_length=3, max_length=63, pattern=r'^[a-z0-9][a-z0-9.-]+[a-z0-9]$')
    region: str = Field(default='us-east-1', pattern=r'^[a-z]{2}(?:-[a-z]+)+-\d$', max_length=40)
    access_key: str = Field(min_length=16, max_length=128)
    secret_key: str = Field(min_length=16, max_length=256)
    session_token: str = Field(default='', max_length=8192)

class Submit(StrictModel):
    connection_id: UUID
    kind: Literal['list', 'inspect', 'transform']
    key: str = Field(default='', max_length=1024)
    cursor: str = Field(default='', max_length=4096)
    prefix: str = Field(default='', max_length=1024)
    source_id: UUID | None = None
    mode: Literal['replace', 'extract', 'normalize'] = 'replace'
    prompt: str = Field(default='', max_length=2000)
    replacement: str = Field(default='', max_length=1000)
    columns: list[str] = Field(default_factory=list, max_length=50)

class Plan(StrictModel):
    pattern: str = Field(default='', max_length=512)
    operations: list[Literal['trim', 'lowercase', 'uppercase', 'collapse_spaces']] = Field(default_factory=list, max_length=4)
    explanation: str = Field(max_length=500)
