"""Spark owns distribution; Arrow's RE2 kernels own bounded-time regex execution."""
import csv
import json
import os
from pathlib import Path
from .storage import UserError

def spark_session():
    from pyspark.sql import SparkSession
    builder = (SparkSession.builder.appName('Pattern Studio')
            .master(os.getenv('SPARK_MASTER', 'local[2]'))
            .config('spark.sql.shuffle.partitions', os.getenv('SPARK_PARTITIONS', '8'))
            .config('spark.sql.caseSensitive', 'true')
            .config('spark.sql.execution.arrow.maxRecordsPerBatch', '4096')
            .config('spark.driver.memory', os.getenv('SPARK_DRIVER_MEMORY', '2g'))
            .config('spark.executor.memory', os.getenv('SPARK_EXECUTOR_MEMORY', '2g'))
            .config('spark.task.maxFailures', '2')
            .config('spark.ui.enabled', 'false'))
    if os.getenv('SPARK_DRIVER_HOST'):
        builder = builder.config('spark.driver.host', os.environ['SPARK_DRIVER_HOST']).config('spark.driver.bindAddress', '0.0.0.0')
    return builder.getOrCreate()

def load_csv(spark, path):
    with Path(path).open(encoding='utf-8-sig', newline='') as source:
        header = next(csv.reader(source), None)
    if not header or len(header) > 200 or any(not c or len(c) > 200 for c in header) or len(set(header)) != len(header):
        raise UserError('CSV needs 1–200 uniquely named, non-empty columns (UTF-8 encoding).')
    # Preserve leading zeros and IDs; users explicitly select text columns.
    frame = (spark.read.option('header', True).option('inferSchema', False)
             .option('multiLine', os.getenv('CSV_MULTILINE', 'true')).option('escape', '"')
             .option('maxColumns', '200').option('maxCharsPerColumn', '32768')
             .option('mode', 'FAILFAST').csv(str(path)))
    return frame.repartition(int(os.getenv('SPARK_PARTITIONS', '8')))

def arrow_transform(values, mode, pattern='', replacement='', operations=()):
    import pyarrow.compute as pc
    if mode == 'replace':
        # Arrow interprets backslash captures; escape backslashes for literal replacement.
        return pc.replace_substring_regex(values, pattern=pattern, replacement=replacement.replace('\\', '\\\\'))
    if mode == 'extract':
        extracted = pc.extract_regex(values, pattern='(?P<value>' + pattern + ')')
        return pc.struct_field(extracted, 'value')
    for operation in operations:
        if operation == 'trim':
            values = pc.utf8_trim_whitespace(values)
        elif operation == 'lowercase':
            values = pc.utf8_lower(values)
        elif operation == 'uppercase':
            values = pc.utf8_upper(values)
        elif operation == 'collapse_spaces':
            values = pc.replace_substring_regex(values, pattern=r'\s+', replacement=' ')
        else:
            raise ValueError('Unsupported operation')
    return values

def transform(frame, columns, mode, plan, replacement):
    from pyspark.sql import functions as F
    import pandas as pd
    import pyarrow as pa
    if not columns or any(c not in frame.columns for c in columns):
        raise UserError('Choose at least one existing column.')
    if mode == 'extract' and any(c + '_extracted' in frame.columns for c in columns):
        raise UserError('An extracted output column already exists.')
    pattern, operations = plan.pattern, plan.operations

    @F.pandas_udf('string')
    def apply_batch(batch: pd.Series) -> pd.Series:
        result = arrow_transform(pa.Array.from_pandas(batch, type=pa.string()), mode, pattern, replacement, operations)
        return result.to_pandas()

    for column in columns:
        name = column + '_extracted' if mode == 'extract' else column
        frame = frame.withColumn(name, apply_batch(F.col('`' + column.replace('`', '``') + '`')))
    return frame

def materialize(frame, directory):
    """Workers write immutable blocks. Driver collects O(partitions) metadata only."""
    directory = str(Path(directory).resolve())
    columns = frame.columns

    def write_partition(index, rows):
        from pyspark import TaskContext
        context = TaskContext.get()
        folder = Path(directory) / f'p{index}-a{context.taskAttemptId()}'
        folder.mkdir(parents=True, exist_ok=True)
        block, count, part = [], 0, 0
        for row in rows:
            block.append(list(row))
            count += 1
            if len(block) == 500:
                (folder / f'{part}.json').write_text(json.dumps(block, ensure_ascii=False), encoding='utf-8')
                block, part = [], part + 1
        if block:
            (folder / f'{part}.json').write_text(json.dumps(block, ensure_ascii=False), encoding='utf-8')
        yield {'partition': index, 'folder': folder.name, 'count': count}

    partitions = sorted(frame.rdd.mapPartitionsWithIndex(write_partition).collect(), key=lambda p: p['partition'])
    return {'columns': columns, 'total': sum(p['count'] for p in partitions), 'partitions': partitions, 'directory': directory}

def read_page(manifest, page, page_size):
    start, stop = (page - 1) * page_size, page * page_size
    rows, offset = [], 0
    for partition in manifest['partitions']:
        end = offset + partition['count']
        if start < end and stop > offset:
            lo, hi = max(0, start - offset), min(partition['count'], stop - offset)
            for block in range(lo // 500, (hi - 1) // 500 + 1):
                path = Path(manifest['directory']) / partition['folder'] / f'{block}.json'
                data = json.loads(path.read_text(encoding='utf-8'))
                rows.extend(data[max(0, lo - block * 500):min(500, hi - block * 500)])
        offset = end
        if offset >= stop:
            break
    return {'columns': manifest['columns'], 'rows': rows, 'total': manifest['total'], 'page': page, 'page_size': page_size}
