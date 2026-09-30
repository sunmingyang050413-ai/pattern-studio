import io
from unittest.mock import Mock, patch
import openpyxl
import pytest
from pipeline.services.storage import download, list_files, UserError

def test_listing_filters_and_preserves_continuation(connection):
    s3 = Mock()
    s3.list_objects_v2.return_value = {'Contents': [{'Key': 'folder/a.csv', 'Size': 10}, {'Key': 'b.XLSX', 'Size': 20}, {'Key': 'not.txt', 'Size': 3}], 'NextContinuationToken': 'next'}
    with patch('pipeline.services.storage.client', return_value=s3):
        result = list_files(connection, {'prefix': 'folder/', 'cursor': 'current'})
    assert len(result['files']) == 2 and result['cursor'] == 'next'
    assert s3.list_objects_v2.call_args.kwargs['ContinuationToken'] == 'current'

def test_excel_stream_conversion(connection, tmp_path):
    from botocore.response import StreamingBody
    book = openpyxl.Workbook()
    book.active.append(['ID', 'Name'])
    book.active.append(['001', 'Alice'])
    buffer = io.BytesIO()
    book.save(buffer)
    content = buffer.getvalue()
    s3 = Mock()
    s3.get_object.return_value = {'ContentLength': len(content), 'Body': StreamingBody(io.BytesIO(content), len(content))}
    with patch('pipeline.services.storage.client', return_value=s3):
        path = download(connection, 'arbitrary/prefix/book.xlsx', tmp_path, lambda: None)
    assert path.read_text().splitlines() == ['ID,Name', '001,Alice']

def test_large_excel_rejected_before_download(connection, tmp_path):
    s3 = Mock()
    s3.get_object.return_value = {'ContentLength': 200 * 1024 * 1024, 'Body': Mock()}
    with patch('pipeline.services.storage.client', return_value=s3), pytest.raises(UserError):
        download(connection, 'book.xlsx', tmp_path, lambda: None)
    s3.get_object.return_value['Body'].close.assert_called_once()
