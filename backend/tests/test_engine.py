import json
import pyarrow as pa
import pytest
from pipeline.schemas import Plan
from pipeline.services.engine import arrow_transform, read_page
from pipeline.services.planner import validate_plan
from pipeline.services.storage import UserError

EMAIL = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'

def test_replace_all_matches_preserves_null_and_literal_replacement():
    values = pa.array(['a@example.com + b@example.org', None, '', 'unchanged'])
    assert arrow_transform(values, 'replace', EMAIL, r'$1\1').to_pylist() == [r'$1\1 + $1\1', None, '', 'unchanged']

def test_extract_new_value_and_missing_match():
    result = arrow_transform(pa.array(['Mail a@example.com now', 'no match', None]), 'extract', EMAIL).to_pylist()
    assert result == ['a@example.com', None, None]

def test_normalization_order_and_unicode():
    result = arrow_transform(pa.array(['  HÉLLO   WORLD  ', None]), 'normalize', operations=['trim', 'collapse_spaces', 'lowercase'])
    assert result.to_pylist() == ['héllo world', None]

@pytest.mark.parametrize('pattern', ['(', r'(a)\1', r'(?<=x)y'])
def test_unsupported_regex_rejected(pattern):
    with pytest.raises(UserError):
        validate_plan(Plan(pattern=pattern, explanation='test'), 'replace')

def test_nested_quantifiers_have_linear_engine():
    plan = validate_plan(Plan(pattern='(a+)+$', explanation='test'), 'replace')
    assert arrow_transform(pa.array(['a' * 100_000 + '!']), 'replace', plan.pattern, 'x').to_pylist() == ['a' * 100_000 + '!']

def test_pagination_crosses_partition_and_block_boundaries(tmp_path):
    partitions = []
    expected = []
    for index, count in enumerate([501, 0, 602]):
        folder = tmp_path / str(index)
        folder.mkdir()
        data = [[len(expected) + i] for i in range(count)]
        expected.extend(data)
        for block in range(0, count, 500):
            (folder / f'{block // 500}.json').write_text(json.dumps(data[block:block + 500]))
        partitions.append({'folder': str(index), 'count': count})
    manifest = {'partitions': partitions, 'directory': str(tmp_path), 'columns': ['ID'], 'total': len(expected)}
    result = [row for page in range(1, 13) for row in read_page(manifest, page, 100)['rows']]
    assert result == expected
    assert read_page(manifest, 100, 100)['rows'] == []

def test_cache_avoids_second_llm_call(monkeypatch):
    from unittest.mock import Mock
    from pipeline.services import planner
    response = Mock()
    response.choices = [Mock(message=Mock(content=json.dumps({'pattern': EMAIL, 'operations': [], 'explanation': 'Find emails'})))]
    client = Mock()
    client.chat.completions.create.return_value = response
    monkeypatch.setenv('OPENAI_API_KEY', 'fake-test-key')
    monkeypatch.setenv('LLM_PROVIDER', 'openai')
    monkeypatch.setattr(planner, 'OpenAI', Mock(return_value=client))
    assert planner.plan_request('find email addresses', 'replace')[1] is False
    assert planner.plan_request('find email addresses', 'replace')[1] is True
    assert client.chat.completions.create.call_count == 1

@pytest.mark.spark
def test_real_spark_pipeline(tmp_path):
    from pipeline.services.engine import spark_session, load_csv, transform, materialize
    source = tmp_path / 'source.csv'
    source.write_text('ID,Email,Name\n001,a@example.com,  Alice  \n002,b@example.org,BOB\n', encoding='utf-8')
    spark = spark_session()
    try:
        frame = load_csv(spark, source)
        transformed = transform(frame, ['Email'], 'replace', Plan(pattern=EMAIL, explanation='emails'), 'REDACTED')
        manifest = materialize(transformed, tmp_path / 'result')
        rows = read_page(manifest, 1, 100)['rows']
        assert sorted(row[0] for row in rows) == ['001', '002']
        assert all(row[1] == 'REDACTED' for row in rows)
        extracted = transform(frame, ['Email'], 'extract', Plan(pattern=EMAIL, explanation='emails'), '')
        assert extracted.columns[-1] == 'Email_extracted'
        assert sorted(r[-1] for r in extracted.collect()) == ['a@example.com', 'b@example.org']
        cleaned = transform(frame, ['Name'], 'normalize', Plan(operations=['trim', 'lowercase'], explanation='clean'), '')
        assert sorted(r['Name'] for r in cleaned.collect()) == ['alice', 'bob']
        empty_source = tmp_path / 'empty.csv'
        empty_source.write_text('Email\n', encoding='utf-8')
        empty = materialize(load_csv(spark, empty_source), tmp_path / 'empty-result')
        assert empty['total'] == 0 and read_page(empty, 1, 25)['rows'] == []
        case_source = tmp_path / 'case.csv'
        case_source.write_text('Email,email\na@example.com,keep\n', encoding='utf-8')
        case_frame = transform(load_csv(spark, case_source), ['Email'], 'replace', Plan(pattern=EMAIL, explanation='emails'), 'REDACTED')
        assert list(case_frame.collect()[0]) == ['REDACTED', 'keep']
    finally:
        spark.stop()
