from __future__ import annotations
import csv
import json
import logging
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def write_json_safely(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    tmp.replace(path)

def write_csv_rows(path: Path, header: List[str], rows: List[List[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)

def csv_shape(path: Path) -> Tuple[int, int]:
    """Return (n_rows_without_header, n_cols). Robust to quoted newlines.
    If the file is empty/invalid, returns (0, 0).
    """
    try:
        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header is None:
                return 0, 0
            ncols = len(header)
            nrows = 0
            for row in reader:
                # count only non-empty rows
                if any((c or "").strip() for c in row):
                    nrows += 1
            return nrows, ncols
    except UnicodeDecodeError:
        # Fallback with latin-1
        try:
            with path.open("r", newline="", encoding="latin-1") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if header is None:
                    return 0, 0
                ncols = len(header)
                nrows = 0
                for row in reader:
                    if any((c or "").strip() for c in row):
                        nrows += 1
                return nrows, ncols
        except Exception as e:
            logger.exception("csv_shape failed on %s", path)
            return 0, 0
    except Exception:
        logger.exception("csv_shape failed on %s", path)
        return 0, 0

def file_size_bytes(path: Path) -> Optional[int]:
    try:
        return path.stat().st_size
    except Exception:
        return None
