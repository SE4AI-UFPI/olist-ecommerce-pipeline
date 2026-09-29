"""
Executes Jupyter notebooks in order, updating them in-place with outputs.
"""

import sys
import time
from pathlib import Path
import nbformat
from nbclient import NotebookClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent

NOTEBOOKS = [
    "notebooks/01_exploracao_dados_olist.ipynb",
    "notebooks/02_extract_kaggle_e_raw_load.ipynb",
    "notebooks/03_staging_limpeza.ipynb",
    "notebooks/04_modelagem_dw_star_schema.ipynb",
    "notebooks/05_validacao_e_consultas_dw.ipynb",
    "notebooks/06_preview_dashboard.ipynb",
    "notebooks/fabricaia_example.ipynb",
]


def execute_notebook(nb_rel_path: str, timeout: int = 600):
    nb_path = PROJECT_ROOT / nb_rel_path
    print(f"\n=======================================================")
    print(f"Executing: {nb_rel_path}")
    print(f"Path: {nb_path}")
    print(f"=======================================================")

    start_time = time.time()
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    client = NotebookClient(
        nb,
        timeout=timeout,
        kernel_name="python3",
        resources={"metadata": {"path": str(PROJECT_ROOT)}},
    )

    try:
        client.execute()
        duration = time.time() - start_time
        print(f" SUCCESS: {nb_rel_path} executed in {duration:.2f}s")

        with open(nb_path, "w", encoding="utf-8") as f:
            nbformat.write(nb, f)
        print(f" Saved updated notebook with outputs: {nb_path}")
        return True, duration, None
    except Exception as e:
        duration = time.time() - start_time
        print(f" ERROR in {nb_rel_path} after {duration:.2f}s: {e}")
        # Save whatever executed so far
        with open(nb_path, "w", encoding="utf-8") as f:
            nbformat.write(nb, f)
        return False, duration, str(e)


def main():
    target_nb = sys.argv[1] if len(sys.argv) > 1 else None
    to_run = [target_nb] if target_nb else NOTEBOOKS

    results = []
    for nb in to_run:
        success, duration, err = execute_notebook(nb)
        results.append((nb, success, duration, err))
        if not success:
            print(f"\nExecution stopped due to error in {nb}")
            break

    print("\n\n=================== EXECUTION SUMMARY ===================")
    print(f"{'Notebook':<45} {'Status':<10} {'Time (s)':<10}")
    print("-" * 65)
    for nb, success, duration, err in results:
        status_str = "OK" if success else "FAILED"
        print(f"{nb:<45} {status_str:<10} {duration:<10.2f}")
    print("=========================================================")

    all_passed = all(r[1] for r in results)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
