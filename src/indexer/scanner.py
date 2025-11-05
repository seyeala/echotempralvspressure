from __future__ import annotations

import logging
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .models import EchoEntry
from .io_helpers import csv_shape, file_size_bytes

logger = logging.getLogger(__name__)

CSV_EXT = ".csv"

def is_csv(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() == CSV_EXT

def find_all_dataset_folders(address: Path) -> List[Path]:
    """Return a list of folders that contain at least one CSV.
    If `address` is a file, use its parent.
    If `address` is a directory containing CSVs, include it.
    Recurse into subfolders.
    """
    start = address
    if start.is_file():
        start = start.parent

    if not start.exists():
        raise FileNotFoundError(f"Address does not exist: {address}")

    try:
        start_entries = list(start.iterdir())
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Address does not exist: {address}") from exc
    except PermissionError:
        logger.warning("Permission denied: %s", start)
        return []

    result: List[Path] = []
    # Include the root if it has CSVs
    if any(is_csv(p) for p in start_entries if p.is_file()):
        result.append(start)

    # Recurse into subdirs
    for p in start.rglob("*"):
        if p.is_dir():
            try:
                if any(is_csv(x) for x in p.iterdir() if x.is_file()):
                    result.append(p)
            except PermissionError:
                logger.warning("Permission denied: %s", p)
            except Exception:
                logger.exception("Error scanning folder: %s", p)

    # Remove duplicates while preserving order
    seen = set()
    uniq: List[Path] = []
    for f in result:
        if f.resolve() not in seen:
            uniq.append(f)
            seen.add(f.resolve())
    return uniq

def pick_pressure_csv(files: Iterable[Path]) -> Optional[Path]:
    # exact filename match (case-insensitive)
    for f in files:
        if f.name.lower() == "pressure.csv":
            return f
    return None

def folder_key(base: str, used: Dict[str, str]) -> str:
    key = base
    i = 2
    while key in used:
        key = f"{base}#{i}"
        i += 1
    used[key] = key
    return key

def scan_dataset_folder(folder: Path) -> Tuple[List[EchoEntry], List[List[object]], List[str]]:
    """Scan a single folder.
    Returns: (entries, summary_rows, errors)
    where `entries` is a list[EchoEntry],
          `summary_rows` is list of CSV rows for summary.csv,
          `errors` is list of error strings
    """
    errors: List[str] = []
    files = sorted([p for p in folder.iterdir() if is_csv(p)], key=lambda p: p.name.lower())
    if not files:
        return [], [], []

    press = pick_pressure_csv(files)
    if press is None:
        errors.append(f"pressure.csv not found in {folder}")

    # Compute pressure stats once
    press_rows, press_cols = (0, 0)
    press_size = None
    if press is not None:
        press_rows, press_cols = csv_shape(press)
        press_size = file_size_bytes(press)

    # Build entries for each echo CSV (every CSV except pressure.csv)
    entries: List[EchoEntry] = []
    summary_rows: List[List[object]] = []
    for f in files:
        if press is not None and f.resolve() == press.resolve():
            continue
        # Echo file stats
        e_rows, e_cols = csv_shape(f)
        e_size = file_size_bytes(f)

        entry = EchoEntry(
            echo=f.name,  # store relative filename (not full path)
            press=press.name if press is not None else None
        )
        entries.append(entry)

        note = ""
        if e_rows == 0 and e_cols == 0:
            note = "empty_or_unreadable"
        if press is None:
            note = (note + "; " if note else "") + "missing_pressure_csv"

        summary_rows.append([
            str(folder),
            f.name,
            e_rows,
            e_cols,
            e_size,
            (press.name if press is not None else None),
            press_rows,
            press_cols,
            press_size,
            note or ""
        ])

    # Edge case: folder has ONLY pressure.csv (no echoes) -> still add a summary row for visibility
    if len(entries) == 0 and press is not None:
        summary_rows.append([
            str(folder),
            None,
            None,
            None,
            None,
            press.name,
            press_rows,
            press_cols,
            press_size,
            "only_pressure_csv"
        ])

    return entries, summary_rows, errors

def scan_address(address: Path) -> Tuple[Dict[str, List[Dict[str, str]]], List[List[object]], List[str]]:
    """Scan an address and produce:
    - index_dict: {folder_key: [ {echo: ..., press: ...}, ... ] }
    - summary_rows: rows for summary.csv
    - errors: list of string errors
    """
    folders = find_all_dataset_folders(address)
    index_dict: Dict[str, List[Dict[str, str]]] = {}
    summary_rows: List[List[object]] = []
    errors: List[str] = []
    used_keys: Dict[str, str] = {}

    for folder in folders:
        entries, rows, errs = scan_dataset_folder(folder)
        base = folder.name
        key = folder_key(base, used_keys)
        # Convert dataclasses to plain dict
        index_dict[key] = [asdict(e) for e in entries]
        summary_rows.extend(rows)
        errors.extend(errs)

    return index_dict, summary_rows, errors
