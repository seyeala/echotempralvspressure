from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class EchoEntry:
    echo: str          # path to echo CSV (relative to dataset folder)
    press: Optional[str]  # path to pressure.csv (relative to dataset folder) or None
