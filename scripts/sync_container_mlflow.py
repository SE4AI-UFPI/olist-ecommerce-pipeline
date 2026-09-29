import sqlite3
import shutil
from pathlib import Path

# Conectar aos dois bancos
conn_host = sqlite3.connect('mlflow.db')
conn_cnt = sqlite3.connect('mlflow.db.from_container')

c_host = conn_host.cursor()
c_cnt = conn_cnt.cursor()

# Descobrir exp_id de 'olist_power_seller_classification' no host
c_host.execute("SELECT experiment_id FROM experiments WHERE name = 'olist_power_seller_classification'")
res = c_host.fetchone()
if not res:
    print("Experimento não encontrado no host")
    exit(1)
host_exp_id = res[0]
print(f"Host experiment_id for olist_power_seller_classification: {host_exp_id}")

# Buscar runs do container pertencentes a 'olist_power_seller_classification' (exp_id = 1 no container)
cnt_runs = c_cnt.execute("SELECT * FROM runs WHERE experiment_id = 1").fetchall()
run_col_names = [col[0] for col in c_cnt.description]
print(f"Found {len(cnt_runs)} runs in container for olist_power_seller_classification")

for r in cnt_runs:
    r_dict = dict(zip(run_col_names, r))
    run_id = r_dict['run_uuid']
    
    # Atualizar experiment_id para o host
    r_dict['experiment_id'] = host_exp_id
    if r_dict['artifact_uri']:
        r_dict['artifact_uri'] = f"file:{Path.cwd().resolve().as_posix()}/mlruns/{host_exp_id}/{run_id}/artifacts"
    
    # Inserir ou ignorar se ja existir
    cols = ', '.join(r_dict.keys())
    placeholders = ', '.join(['?'] * len(r_dict))
    c_host.execute(f"INSERT OR REPLACE INTO runs ({cols}) VALUES ({placeholders})", list(r_dict.values()))
    
    # Copiar params
    for p in c_cnt.execute("SELECT key, value, run_uuid FROM params WHERE run_uuid = ?", (run_id,)).fetchall():
        c_host.execute("INSERT OR REPLACE INTO params (key, value, run_uuid) VALUES (?, ?, ?)", p)
        
    # Copiar metrics
    for m in c_cnt.execute("SELECT key, value, timestamp, step, is_nan, run_uuid FROM metrics WHERE run_uuid = ?", (run_id,)).fetchall():
        c_host.execute("INSERT OR REPLACE INTO metrics (key, value, timestamp, step, is_nan, run_uuid) VALUES (?, ?, ?, ?, ?, ?)", m)
        
    # Copiar latest_metrics
    for lm in c_cnt.execute("SELECT key, value, timestamp, step, is_nan, run_uuid FROM latest_metrics WHERE run_uuid = ?", (run_id,)).fetchall():
        c_host.execute("INSERT OR REPLACE INTO latest_metrics (key, value, timestamp, step, is_nan, run_uuid) VALUES (?, ?, ?, ?, ?, ?)", lm)
        
    # Copiar tags
    for t in c_cnt.execute("SELECT key, value, run_uuid FROM tags WHERE run_uuid = ?", (run_id,)).fetchall():
        c_host.execute("INSERT OR REPLACE INTO tags (key, value, run_uuid) VALUES (?, ?, ?)", t)

conn_host.commit()
conn_host.close()
conn_cnt.close()

# Copiar arquivos de artifacts
src_dir = Path("mlruns_container/1")
dst_dir = Path(f"mlruns/{host_exp_id}")
dst_dir.mkdir(parents=True, exist_ok=True)
if src_dir.exists():
    for item in src_dir.iterdir():
        target = dst_dir / item.name
        if not target.exists() and item.is_dir():
            shutil.copytree(item, target)

print("Sync completed successfully!")
