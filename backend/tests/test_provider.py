import json
from unittest.mock import Mock
import pytest
from pipeline.services import planner
from pipeline.services.storage import UserError

@pytest.fixture
def groq(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER', 'groq')
    monkeypatch.delenv('LLM_MODEL', raising=False)
    monkeypatch.setenv('GROQ_API_KEY', 'test-groq-key')
    monkeypatch.setenv('LLM_DAILY_CALL_LIMIT', '100')
    response = Mock()
    response.choices = [Mock(message=Mock(content=json.dumps({'pattern': '[0-9]+', 'operations': [], 'explanation': 'Find digits'})))]
    client = Mock()
    client.chat.completions.create.return_value = response
    constructor = Mock(return_value=client)
    monkeypatch.setattr(planner, 'OpenAI', constructor)
    return constructor, client

def test_groq_uses_its_own_key_and_endpoint(groq, monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'must-not-be-used')
    plan, hit = planner.plan_request('find numbers', 'replace')
    constructor, client = groq
    assert not hit and plan.pattern == '[0-9]+'
    assert constructor.call_args.kwargs['base_url'] == 'https://api.groq.com/openai/v1'
    assert constructor.call_args.kwargs['api_key'] == 'test-groq-key'
    assert client.chat.completions.create.call_args.kwargs['model'] == 'openai/gpt-oss-20b'

def test_missing_groq_key_never_falls_back_to_paid_provider(groq, monkeypatch):
    monkeypatch.delenv('GROQ_API_KEY')
    monkeypatch.setenv('OPENAI_API_KEY', 'must-not-be-used')
    with pytest.raises(UserError, match='not configured'):
        planner.plan_request('find numbers', 'replace')
    groq[0].assert_not_called()

def test_daily_cap_keeps_cached_plans_available(groq, monkeypatch):
    monkeypatch.setenv('LLM_DAILY_CALL_LIMIT', '1')
    planner.plan_request('find numbers', 'replace')
    assert planner.plan_request('find numbers', 'replace')[1] is True
    with pytest.raises(UserError, match='Daily LLM'):
        planner.plan_request('find digits', 'replace')
    assert groq[1].chat.completions.create.call_count == 1

def test_provider_is_part_of_cache_identity(groq, monkeypatch):
    planner.plan_request('find numbers', 'replace')
    monkeypatch.setenv('LLM_PROVIDER', 'openai')
    monkeypatch.setenv('OPENAI_API_KEY', 'test-openai-key')
    assert planner.plan_request('find numbers', 'replace')[1] is False
    assert groq[1].chat.completions.create.call_count == 2

def test_invalid_budget_does_not_call_provider(groq, monkeypatch):
    monkeypatch.setenv('LLM_DAILY_CALL_LIMIT', '0')
    with pytest.raises(UserError, match='LLM_DAILY_CALL_LIMIT'):
        planner.plan_request('numbers', 'replace')
    groq[0].assert_not_called()
