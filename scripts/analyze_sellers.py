import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.etl.db import get_engine
import pandas as pd

engine = get_engine()
query = """
    SELECT 
        s.seller_id,
        s.seller_state,
        COUNT(DISTINCT foi.order_id) as total_orders,
        COUNT(foi.order_item_key) as total_items,
        COALESCE(SUM(foi.price), 0) as total_revenue
    FROM dw.dim_sellers s
    LEFT JOIN dw.fact_order_items foi ON s.seller_key = foi.seller_key
    GROUP BY s.seller_id, s.seller_state
"""
df = pd.read_sql(query, engine)
print("Total sellers:", len(df))
print(df[['total_orders', 'total_items', 'total_revenue']].describe(percentiles=[0.5, 0.75, 0.8, 0.85, 0.9]))
p10k = (df['total_revenue'] >= 10000).mean()
p5k = (df['total_revenue'] >= 5000).mean()
p30ord = (df['total_orders'] >= 30).mean()
print(f"Revenue >= R$ 10,000: {(df['total_revenue'] >= 10000).sum()} sellers ({p10k:.1%})")
print(f"Revenue >= R$ 5,000:  {(df['total_revenue'] >= 5000).sum()} sellers ({p5k:.1%})")
print(f"Orders >= 30:        {(df['total_orders'] >= 30).sum()} sellers ({p30ord:.1%})")
