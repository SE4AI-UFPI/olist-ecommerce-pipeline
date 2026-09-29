"""
Download and verify raw Olist CSV datasets from Hugging Face mirror.
"""

import os
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.etl.kaggle_ingestion import EXPECTED_CSV_FILES, MIN_ROWS, KaggleIngestion, _count_lines

BASE_URL = (
    "https://huggingface.co/datasets/shawnzzzh/AgenticDataBench/resolve/main/datasets/ecommerce/Brazilian%20E-Commerce/"
)
DEST_DIR = PROJECT_ROOT / "data" / "raw"


def format_bytes(size: float) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"


def download_file(url: str, dest_file: Path) -> None:
    temp_file = dest_file.with_suffix(".csv.tmp")
    print(f"Connecting to {url} ...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req) as response, open(temp_file, "wb") as out_file:
        total_size = response.getheader("Content-Length")
        total_size = int(total_size) if total_size else None
        
        bytes_read = 0
        start_time = time.time()
        last_print = start_time
        block_size = 1024 * 256  # 256 KB chunks

        while True:
            buffer = response.read(block_size)
            if not buffer:
                break
            out_file.write(buffer)
            bytes_read += len(buffer)
            now = time.time()
            if now - last_print >= 0.5:
                elapsed = now - start_time
                speed = bytes_read / elapsed if elapsed > 0 else 0
                if total_size:
                    percent = (bytes_read / total_size) * 100
                    print(
                        f"\r  Downloading {dest_file.name}: {percent:5.1f}% "
                        f"({format_bytes(bytes_read)} / {format_bytes(total_size)}) "
                        f"at {format_bytes(speed)}/s",
                        end="",
                        flush=True,
                    )
                else:
                    print(
                        f"\r  Downloading {dest_file.name}: {format_bytes(bytes_read)} "
                        f"at {format_bytes(speed)}/s",
                        end="",
                        flush=True,
                    )
                last_print = now

        elapsed = time.time() - start_time
        speed = bytes_read / elapsed if elapsed > 0 else 0
        print(
            f"\r  Downloaded {dest_file.name}: 100% "
            f"({format_bytes(bytes_read)}) in {elapsed:.1f}s ({format_bytes(speed)}/s)       ",
            flush=True,
        )

    # Rename tmp file to final file
    if dest_file.exists():
        dest_file.unlink()
    temp_file.rename(dest_file)


def main():
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Target directory: {DEST_DIR}")
    print(f"Files to verify/download: {len(EXPECTED_CSV_FILES)}")

    for filename in EXPECTED_CSV_FILES:
        dest_file = DEST_DIR / filename
        min_rows = MIN_ROWS[filename]
        needs_download = False

        if not dest_file.exists():
            print(f"File missing: {filename}")
            needs_download = True
        else:
            line_count = _count_lines(dest_file)
            if line_count < min_rows:
                print(f"File incomplete: {filename} ({line_count} < {min_rows} rows)")
                needs_download = True
            else:
                print(f"File already complete: {filename} ({line_count} rows, {format_bytes(dest_file.stat().st_size)})")

        if needs_download:
            # Construct download URL (URL encode filename if needed)
            url = BASE_URL + urllib.parse.quote(filename)
            download_file(url, dest_file)
            line_count = _count_lines(dest_file)
            print(f"  Verified row count: {line_count} (min required: {min_rows})")
            if line_count < min_rows:
                raise RuntimeError(f"Downloaded file {filename} has {line_count} rows, which is less than min {min_rows}!")

    print("\n--- Summary Verification ---")
    print(f"{'Filename':<40} {'Size':<12} {'Rows':<12} {'Min Rows':<10} {'Status':<8}")
    print("-" * 84)
    all_ok = True
    for filename in EXPECTED_CSV_FILES:
        dest_file = DEST_DIR / filename
        size_str = format_bytes(dest_file.stat().st_size)
        rows = _count_lines(dest_file)
        min_rows = MIN_ROWS[filename]
        status = "OK" if rows >= min_rows else "FAIL"
        if status != "OK":
            all_ok = False
        print(f"{filename:<40} {size_str:<12} {rows:<12} {min_rows:<10} {status:<8}")

    print("-" * 84)
    if not all_ok:
        sys.exit(1)

    print("\nTesting KaggleIngestion().download_dataset()...")
    ingestion = KaggleIngestion()
    ready_files = ingestion.download_dataset(dest_dir=str(DEST_DIR))
    print(f"KaggleIngestion successfully returned {len(ready_files)} ready files:")
    for f in ready_files:
        print(f"  - {f}")


if __name__ == "__main__":
    main()
