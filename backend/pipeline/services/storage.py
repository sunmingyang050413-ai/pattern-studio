from pathlib import Path
import csv
import os
import boto3
from botocore.config import Config
from .credentials import decrypt

class UserError(Exception):
    pass

def client(connection):
    credentials = decrypt(connection.encrypted_credentials)
    return boto3.client('s3', region_name=connection.region, aws_access_key_id=credentials['access_key'], aws_secret_access_key=credentials['secret_key'], aws_session_token=credentials.get('session_token') or None, config=Config(connect_timeout=10, read_timeout=30, retries={'max_attempts': 2}))

def list_files(connection, payload):
    s3 = client(connection)
    args = {'Bucket': connection.bucket, 'MaxKeys': 100, 'Prefix': payload.get('prefix', '')}
    if payload.get('cursor'):
        args['ContinuationToken'] = payload['cursor']
    result = s3.list_objects_v2(**args)
    return {'files': [{'key': x['Key'], 'size': x['Size']} for x in result.get('Contents', []) if Path(x['Key']).suffix.lower() in {'.csv', '.xlsx', '.xls'}], 'cursor': result.get('NextContinuationToken', ''), 'bucket': connection.bucket}

def download(connection, key, directory, checkpoint):
    suffix = Path(key).suffix.lower()
    if suffix not in {'.csv', '.xlsx', '.xls'}:
        raise UserError('Select a CSV, XLSX or XLS file.')
    s3 = client(connection)
    obj = s3.get_object(Bucket=connection.bucket, Key=key)
    limit = int(os.getenv('MAX_SOURCE_BYTES', '5368709120'))
    if suffix != '.csv':
        limit = min(limit, int(os.getenv('MAX_EXCEL_BYTES', '104857600')))
    if obj['ContentLength'] > limit:
        obj['Body'].close()
        raise UserError('File exceeds the configured size limit. Convert large Excel files to CSV.')
    target = directory / ('source' + suffix)
    try:
        with target.open('wb') as output:
            size = 0
            for chunk in obj['Body'].iter_chunks(chunk_size=1024 * 1024):
                checkpoint()
                size += len(chunk)
                if size > limit:
                    raise UserError('File exceeds the configured size limit.')
                output.write(chunk)
    finally:
        obj['Body'].close()
    if suffix == '.csv':
        return target
    csv_path = directory / 'source.csv'
    if suffix == '.xlsx':
        import openpyxl
        book = openpyxl.load_workbook(target, read_only=True, data_only=True)
        rows = book.worksheets[0].iter_rows(values_only=True)
    else:
        import xlrd
        book = xlrd.open_workbook(target, on_demand=True)
        sheet = book.sheet_by_index(0)
        rows = (sheet.row_values(i) for i in range(sheet.nrows))
    try:
        with csv_path.open('w', encoding='utf-8', newline='') as output:
            writer = csv.writer(output)
            for index, row in enumerate(rows):
                if index % 1000 == 0:
                    checkpoint()
                writer.writerow(row)
    finally:
        if suffix == '.xlsx':
            book.close()
        else:
            book.release_resources()
    return csv_path
