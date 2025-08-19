from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import List

from .scanner import scan_address
from .io_helpers import ensure_dir, write_csv_rows, write_json_safely

LOG_FORMAT = "[%(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("indexer")

def cli(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Scan a folder ('address') for pressure.csv and other CSVs (echo files) and build an index + summary."
    )
    parser.add_argument(
        "--address",
        required=True,
        help="Path to a directory containing CSVs (or a file whose parent contains CSVs)."
    )
    parser.add_argument(
        "--outdir",
        default="artifacts",
        help="Directory to write outputs: dataset_index.json, summary.csv, errors.log (default: artifacts)"
    )
    args = parser.parse_args(argv)

    address = Path(args.address).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()
    ensure_dir(outdir)

    logger.info("Scanning address: %s", address)
    index_dict, summary_rows, errors = scan_address(address)

    # Write JSON index
    index_path = outdir / "dataset_index.json"
    write_json_safely(index_path, index_dict)
    logger.info("Wrote %s", index_path)

    # Write summary CSV
    summary_path = outdir / "summary.csv"
    header = [
        "folder_path",
        "echo_file",
        "echo_rows",
        "echo_cols",
        "echo_size_bytes",
        "pressure_file",
        "pressure_rows",
        "pressure_cols",
        "pressure_size_bytes",
        "note"
    ]
    write_csv_rows(summary_path, header, summary_rows)
    logger.info("Wrote %s", summary_path)

    # Write errors.log
    errors_path = outdir / "errors.log"
    if errors:
        errors_path.write_text("\n".join(errors) + "\n", encoding="utf-8")
        logger.warning("Completed with %d error(s). See %s", len(errors), errors_path)
    else:
        errors_path.write_text("", encoding="utf-8")
        logger.info("Completed with no critical errors.")

if __name__ == "__main__":
    cli()
