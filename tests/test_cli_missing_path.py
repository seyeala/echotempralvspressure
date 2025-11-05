from pathlib import Path
import sys

import pytest

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from indexer.main import cli


def test_cli_missing_address(tmp_path, capsys):
    missing = tmp_path / "does_not_exist"

    with pytest.raises(SystemExit) as exc:
        cli(["--address", str(missing), "--outdir", str(tmp_path / "out")])

    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert "Address does not exist" in captured.err
