"""Fetch the exact Yarn CLI used by the offline component control."""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import tarfile
import urllib.request
from pathlib import Path

URL = "https://registry.npmjs.org/@yarnpkg/cli-dist/-/cli-dist-4.18.1.tgz"
INTEGRITY = "EH+A4TxAtBWXKE0DGQxW9Bo9crXHLJ73mfxjTQJuv8XonNWWTpei8BQ5JjczHJNU9GROTycwMFn8iOvRIZXUcA=="
CLI_SHA256 = "a28ad591febb769f939c11f82f89bacad0b0fac0c884d3b78fa2aaaee970907e"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    with urllib.request.urlopen(URL, timeout=60) as response:
        archive = response.read()
    if base64.b64encode(hashlib.sha512(archive).digest()).decode() != INTEGRITY:
        raise ValueError("Yarn archive integrity mismatch")
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        stream = tar.extractfile("package/bin/yarn.js")
        if stream is None:
            raise ValueError("Yarn CLI missing from archive")
        with stream:
            cli = stream.read()
    if hashlib.sha256(cli).hexdigest() != CLI_SHA256:
        raise ValueError("Yarn CLI digest mismatch")
    with args.output.open("xb") as output:
        output.write(cli)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
