import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.etl.db import get_engine
import pandas as pd

engine = get_engine()
query = """
    SELECT table_name, column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'dw' 
    ORDER BY table_name, ordinal_position
"""
df = pd.read_sql(query, engine)
for table, grp in df.groupby('table_name'):
    print(f"=== dw.{table} ===")
    for _, row in grp.iterrows():
        print(f"  {row['column_name']} ({row['data_type']})")
