# Address Indexer (echo ↔ pressure.csv)

A tiny, robust tool to **scan a folder ("address")**, find one `pressure.csv` and all the **other CSVs** ("echo" files), and produce:

1. A JSON index mapping **folder name → list of pairs** `{ "echo": "<echo file>", "press": "<pressure.csv>" }`
2. A `summary.csv` with shapes, file sizes, and basic validation results
3. Logs to help you spot problems

Works great on **Google Colab** and locally.

---

## JSON shape (what it writes to `artifacts/dataset_index.json`)

```json
{
  "MyFolder": [
    {"echo": "echo_A.csv", "press": "pressure.csv"},
    {"echo": "echo_B.csv", "press": "pressure.csv"}
  ],
  "AnotherFolder": [
    {"echo": "wave01.csv", "press": "pressure.csv"}
  ]
}
```

- The **key** is the *folder name*. If the same base name repeats elsewhere, a suffix like `#2` is added.
- `echo` is every CSV file **except** `pressure.csv` (case-insensitive, exact filename match).
- `press` is the path (relative to that folder) to `pressure.csv`. If missing, `press` will be `null` and an error will be logged.

---

## What counts as a "dataset folder"?
- If the provided address **is a folder and contains any `.csv`**, that folder is treated as **one dataset**.
- All **subfolders** that contain CSVs are also scanned **recursively**.
- If you pass a **file path**, the tool will scan that file's **parent folder**.

---

## Quick CLI usage

```bash
python -m indexer.main --address /path/to/your/data --outdir artifacts
# or, if installed in editable mode (see below), use the console script:
dset-index --address /path/to/your/data --outdir artifacts
```

Outputs land under `artifacts/` by default:

- `artifacts/dataset_index.json`
- `artifacts/summary.csv`
- `artifacts/errors.log`

---

## Error handling
- Missing `pressure.csv` → allowed; `press` becomes `null` and a row is added to `summary.csv` + `errors.log`.
- Unreadable/empty CSV → recorded in `summary.csv` with an `error` note.
- Duplicate folder base names → suffixed (`FolderName#2`, `FolderName#3`, ...).

---

## Google Colab quick start (copy/paste)

> **Option A: install package locally in the notebook (recommended)**

```python
# 1) Create the repo files in Colab (if you didn't clone from GitHub)
import os, pathlib, textwrap

repo = pathlib.Path('/content/address-indexer')
repo.mkdir(parents=True, exist_ok=True)
(src := repo/'src'/'indexer').mkdir(parents=True, exist_ok=True)

# Write all files (copy from this README or from the zip you downloaded)
# -- Skip: in Colab, you'll likely `git clone` your own repo instead.

# 2) Install in editable mode so you get the console script `dset-index`
!pip -q install -e /content/address-indexer

# 3) (Optional) Mount Drive if your data lives there
from google.colab import drive
drive.mount('/content/drive')

# 4) Run it
!dset-index --address "/content/drive/MyDrive/your_folder" --outdir "/content/address-indexer/artifacts"
```

> **Option B: run module directly without installing**

```python
import sys
sys.path.append('/content/address-indexer/src')
!python -m indexer.main --address "/content/drive/MyDrive/your_folder" --outdir "/content/address-indexer/artifacts"
```

---

## Development

```bash
pip install -e .          # installs console script: dset-index
python -m indexer.main --help
```

---

## Notes
- Row counts use the CSV parser to be robust to quoted newlines (but may be slower for very large files).
- Columns are taken from the first row (header). If a file has no header, column count may be 0.
