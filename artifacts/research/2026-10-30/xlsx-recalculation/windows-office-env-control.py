import hashlib
import json
import runpy
import socket
import sys
from pathlib import Path

sources = {
    "pinned": (Path(sys.argv[1]), "f4ebbe4b638904d099eac915ada405b1031d1d7c5a80ecd5d733580d4eee1359"),
    "current": (Path(sys.argv[2]), "df2c8d7249c132a4512d744482e4b5ed0ecbe885f0bcfb1295e7e6a7ced0432c"),
}
if sys.platform != "win32" or hasattr(socket, "AF_UNIX"):
    raise RuntimeError("This control is restricted to Windows runtimes without socket.AF_UNIX")
results = {}
for name, (path, expected) in sources.items():
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError(f"Unexpected source bytes: {name}")
    namespace = runpy.run_path(str(path), run_name="source_control")
    try:
        namespace["get_soffice_env"]()
    except Exception as error:
        results[name] = {"error_type": type(error).__name__, "message": str(error)}
    else:
        raise AssertionError(f"Expected the checked Windows failure for {name}")
print(
    json.dumps(
        {
            "python": sys.version.split()[0],
            "platform": sys.platform,
            "has_af_unix": hasattr(socket, "AF_UNIX"),
            "libreoffice_started": False,
            "source_sha256": {name: digest for name, (_, digest) in sources.items()},
            "sources": results,
        },
        indent=2,
    )
)
