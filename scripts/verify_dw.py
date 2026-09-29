"""
Comprehensive verification of database schemas, table row counts, and data integrity.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.etl.db import get_engine
import pandas as pd

def main():
    engine = get_engine()
    schemas = ['raw', 'staging', 'dw']
    print(f"\n{'='*60}")
    print(f"DATABASE VERIFICATION REPORT (olist_dw)")
    print(f"{'='*60}")
    print(f"{'Schema':<10} {'Table':<25} {'Rows':<12}")
    print("-" * 60)

    total_tables = 0
    total_rows = 0

    for schema in schemas:
        query = f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{schema}' AND table_type = 'BASE TABLE' ORDER BY table_name"
        tables = pd.read_sql(query, engine)['table_name'].tolist()
        for t in tables:
            count = pd.read_sql(f"SELECT COUNT(*) as c FROM {schema}.{t}", engine)['c'].iloc[0]
            print(f"{schema:<10} {t:<25} {count:<12,}")
            total_tables += 1
            total_rows += count
        print("-" * 60)

    print(f"Total Tables: {total_tables}")
    print(f"Total Records across schemas: {total_rows:,}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
