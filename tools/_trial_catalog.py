"""Keep shared sign-in model caches outside frozen native benchmark conditions."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath
from typing import TYPE_CHECKING, Any

from _trial_provider import validate_provider
from _trial_transcript import strict_json
from _windows_appcontainer import checked_path

if TYPE_CHECKING:
    from _trial_context import TrialContext

PIN = Path(__file__).resolve().parents[1] / "toolchains/bootstrap/codex.json"
PIN_SOURCE = "toolchains/bootstrap/codex.json"
RESOURCE = "models.json"


@dataclass(frozen=True, repr=False)
class NativeCatalog:
    """Retain public pin bytes so archived command validation needs no host files."""

    pin: str

    @property
    def source_sha256(self) -> str:
        return hashlib.sha256(self.pin.encode("utf-8")).hexdigest()

    def record(self) -> dict[str, str]:
        return {"pin": self.pin}

    def definition(self) -> dict[str, Any]:
        if not isinstance(self.pin, str) or not 0 < len(self.pin.encode("utf-8")) <= 128 * 1024:
            raise ValueError("Native model catalog pin exceeds its input bounds")
        pin = strict_json(self.pin)
        if not isinstance(pin, dict):
            raise ValueError("Native model catalog pin must be an object")
        try:
            executable = PurePosixPath(pin["executable"])
            resource = pin["resources"][RESOURCE]
            commit = pin["source_commit"]
            if (
                not executable.parts
                or executable.is_absolute()
                or executable.as_posix() != pin["executable"]
                or any(part in {".", ".."} or ":" in part or "\\" in part for part in executable.parts)
                or re.fullmatch(r"[a-f0-9]{40}", commit) is None
                or resource["url"]
                != f"https://raw.githubusercontent.com/openai/codex/{commit}/codex-rs/models-manager/models.json"
                or type(resource["bytes"]) is not int
                or not 0 < resource["bytes"] <= 2 * 1024**2
                or re.fullmatch(r"[a-f0-9]{64}", resource["sha256"]) is None
            ):
                raise ValueError("Native model catalog pin is incomplete or outside its declared source")
        except (KeyError, TypeError) as error:
            raise ValueError("Native model catalog pin is incomplete or invalid") from error
        return pin

    def path(self, cli: Path) -> PurePath:
        pin = self.definition()
        windows = PureWindowsPath(str(cli))
        location: PurePath = windows if windows.is_absolute() else cli
        suffix = PurePosixPath(pin["executable"]).parts
        if (
            not location.is_absolute()
            or len(location.parts) <= len(suffix)
            or type(location)(*location.parts[-len(suffix) :]) != type(location)(*suffix)
        ):
            raise ValueError("Native CLI location differs from its declared package layout")
        return location.parents[len(suffix) - 1] / RESOURCE


def decode_record(value: Any, cli: Path) -> NativeCatalog:
    """Validate recorded public metadata without reading the original installation."""
    if not isinstance(value, dict) or set(value) != {"pin"} or not isinstance(value["pin"], str):
        raise ValueError("Native model catalog evidence is incomplete")
    catalog = NativeCatalog(value["pin"])
    catalog.path(cli)
    return catalog


def verify(catalog: NativeCatalog, cli: Path) -> None:
    """Check the selected executable and vendor metadata with bounded reads."""
    pin = catalog.definition()
    try:
        executable = pin["files"][pin["executable"]]
        resources = (
            (cli, executable, 512 * 1024**2),
            (Path(str(catalog.path(cli))), pin["resources"][RESOURCE], 2 * 1024**2),
        )
        for path, identity, limit in resources:
            source = checked_path(path)
            if type(identity["bytes"]) is not int or not 0 < identity["bytes"] <= limit:
                raise ValueError("Native catalog resource exceeds its pinned bounds")
            if not source.is_file() or source.stat().st_size != identity["bytes"]:
                raise ValueError("Native executable or vendor model catalog changed")
            digest, size = hashlib.sha256(), 0
            with source.open("rb") as stream:
                while block := stream.read(1024**2):
                    size += len(block)
                    if size > identity["bytes"]:
                        raise ValueError("Native catalog resource grew beyond its pinned size")
                    digest.update(block)
            if size != identity["bytes"] or digest.hexdigest() != identity["sha256"]:
                raise ValueError("Native executable or vendor model catalog changed")
    except (KeyError, TypeError) as error:
        raise ValueError("Native executable or vendor model catalog identity is invalid") from error


@contextmanager
def catalog_lease(context: TrialContext, provider: Any) -> Iterator[TrialContext]:
    """Freeze bundled vendor metadata for a native signed-in subject only.

    Account/quota/model metadata probes retain their distinct selected-profile
    contract. This lease never copies, edits or exports authentication storage.
    """
    if provider is None or validate_provider(provider).get("authentication") != "codex_signin":
        yield context
        return
    if context.signin is None or context.native_catalog is not None:
        raise ValueError("A catalog lease requires an admitted native sign-in and no prior catalog binding")
    catalog = NativeCatalog(PIN.read_text(encoding="utf-8"))
    verify(catalog, context.cli)
    try:
        yield replace(context, native_catalog=catalog)
    finally:
        verify(catalog, context.cli)
