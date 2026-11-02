"""Fetch the pinned upstream tutorial FCS bytes without storing them in Git."""

from __future__ import annotations

import argparse
import hashlib
import urllib.request
from pathlib import Path

URL = (
    "https://raw.githubusercontent.com/whitews/FlowIO/9ae65421cbe64d3ff17eeaf81f9dd0fbb9079436/data/fcs_files/data1.fcs"
)
SHA256 = "cba7812f5bbce700786d22d97cf9858c1301878aa840c64eadcd263a3a0a5508"
SIZE = 216432


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    with urllib.request.urlopen(URL, timeout=30) as response:
        if response.status != 200:
            raise ValueError("Unexpected tutorial fixture status")
        data = response.read(SIZE + 1)
    if len(data) != SIZE or hashlib.sha256(data).hexdigest() != SHA256:
        raise ValueError("Tutorial fixture size or digest differs from the pinned source")
    with args.output.open("xb") as output:
        output.write(data)
    print(f"Verified tutorial fixture: {SHA256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
