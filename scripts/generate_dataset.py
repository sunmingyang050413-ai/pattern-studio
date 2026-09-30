import argparse
import csv
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--rows', type=int, default=1_000_000)
parser.add_argument('--output', type=Path, default=Path('artifacts/million.csv'))
args = parser.parse_args()
args.output.parent.mkdir(parents=True, exist_ok=True)
with args.output.open('w', encoding='utf-8', newline='') as stream:
    writer = csv.writer(stream)
    writer.writerow(['ID', 'Name', 'Email', 'Notes'])
    for i in range(args.rows):
        writer.writerow([str(i).zfill(8), f'  Person {i}  ', f'person{i}@example.com', f'Contact person{i}@example.com; ticket #{i}'])
print(f'Wrote {args.rows:,} rows to {args.output}')
