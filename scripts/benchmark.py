"""Run inside the worker container. This measures Spark only, not S3/LLM latency."""
import json
import os
from pathlib import Path
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from pipeline.schemas import Plan
from pipeline.services.engine import spark_session, transform, materialize, read_page
from pyspark.sql import functions as F

rows = int(sys.argv[1]) if len(sys.argv) > 1 else 1_000_000
root = Path(os.getenv('DATA_ROOT', '/data')) / 'benchmarks' / str(uuid.uuid4())
root.mkdir(parents=True)
spark = spark_session()
try:
    started = time.perf_counter()
    frame = spark.range(rows, numPartitions=int(os.getenv('SPARK_PARTITIONS', '8'))).select(F.col('id').cast('string').alias('ID'), F.concat(F.lit('person'), F.col('id'), F.lit('@example.com')).alias('Email'))
    processed = transform(frame, ['Email'], 'replace', Plan(pattern=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', explanation='Benchmark fixed email regex'), 'REDACTED')
    manifest = materialize(processed, root / 'result')
    elapsed = time.perf_counter() - started
    # Full correctness scan, bounded memory: uniqueness, count and replacement for every row.
    seen = bytearray(rows)
    valid_count = 0
    for part in manifest['partitions']:
        for block in range((part['count'] + 499) // 500):
            data = json.loads((root / 'result' / part['folder'] / f'{block}.json').read_text(encoding='utf-8'))
            for identifier, email in data:
                index = int(identifier)
                assert 0 <= index < rows and not seen[index] and email == 'REDACTED'
                seen[index] = 1
                valid_count += 1
    assert valid_count == rows and manifest['total'] == rows
    page_start = time.perf_counter()
    first = read_page(manifest, 1, 50)
    page_ms = (time.perf_counter() - page_start) * 1000
    report = {'rows': rows, 'rows_verified': valid_count, 'spark_seconds': round(elapsed, 3), 'rows_per_second': round(rows / elapsed), 'partitions': len(manifest['partitions']), 'first_page_ms': round(page_ms, 3), 'spark_version': spark.version, 'master': spark.sparkContext.master, 'note': 'Synthetic Spark-only benchmark. Excludes S3, LLM, HTTP and Excel.'}
    (root / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    print('Report:', root / 'report.json')
finally:
    spark.stop()
