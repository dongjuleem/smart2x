"""Manage 10x Genomics barcode whitelists from local data directory."""

import gzip
from pathlib import Path
from typing import List

# Local whitelist directory (relative to this file: ../data/whitelists/)
_LOCAL_DIR = Path(__file__).parent.parent / "data" / "whitelists"

WHITELISTS = {
    "3pv3": {
        "filename": "3M-february-2018.txt.gz",
        "description": "10x Chromium Single Cell 3' Gene Expression v3/v3.1 (6.7M barcodes, 16bp) [default]",
    },
    "3pv4": {
        "filename": "3M-3pgex-may-2023.txt.gz",
        "description": "10x Chromium Single Cell 3' Gene Expression v4 / GEX v4 (6.7M barcodes, 16bp)",
    },
    "3pv2": {
        "filename": "737K-august-2016.txt.gz",
        "description": "10x Chromium Single Cell 3' Gene Expression v2 (737K barcodes, 16bp)",
    },
    "5pv2": {
        "filename": "737K-august-2016.txt.gz",
        "description": "10x Chromium Single Cell 5' Gene Expression v1/v2 (737K barcodes, 16bp)",
    },
}

DEFAULT_KIT = "3pv3"


def get_whitelist_path(kit: str = DEFAULT_KIT) -> Path:
    if kit not in WHITELISTS:
        raise ValueError(f"Unknown kit '{kit}'. Available: {list(WHITELISTS.keys())}")
    path = _LOCAL_DIR / WHITELISTS[kit]["filename"]
    if not path.exists():
        raise FileNotFoundError(
            f"Whitelist file not found: {path}\n"
            f"Please place the whitelist file in: {_LOCAL_DIR}"
        )
    return path


def load_whitelist(kit: str = DEFAULT_KIT) -> List[str]:
    """Return list of barcodes for the given kit."""
    path = get_whitelist_path(kit)
    if path.suffix == ".gz":
        with gzip.open(path, "rt") as f:
            return [line.strip() for line in f if line.strip()]
    else:
        with open(path) as f:
            return [line.strip() for line in f if line.strip()]


def list_kits() -> None:
    print("Available 10x kits:")
    for key, info in WHITELISTS.items():
        marker = " (default)" if key == DEFAULT_KIT else ""
        status = "OK" if (_LOCAL_DIR / info["filename"]).exists() else "MISSING"
        print(f"  {key:<12} [{status}]  {info['description']}{marker}")
