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
LOCAL_CATALOG_LIMIT = 256 * 1024


@dataclass(frozen=True, repr=False)
class LocalCatalog:
    """Archive explicitly declared local metadata without depending on its original host."""

    location: str
    sha256: str
    content: str

    def path(self) -> PurePath:
        location: PurePath = PureWindowsPath(self.location)
        if not location.is_absolute():
            location = PurePosixPath(self.location)
        if (
            not location.is_absolute()
            or str(location) != self.location
            or ".." in location.parts
            or "\0" in self.location
            or (isinstance(location, PureWindowsPath) and len(location.drive) != 2)
        ):
            raise ValueError("Local catalog requires a canonical absolute recorded path")
        return location

    def metadata(self) -> dict[str, Any]:
        self.path()
        if (
            not isinstance(self.content, str)
            or not 0 < len(self.content.encode("utf-8")) <= LOCAL_CATALOG_LIMIT
            or not isinstance(self.sha256, str)
            or re.fullmatch(r"[a-f0-9]{64}", self.sha256) is None
            or hashlib.sha256(self.content.encode("utf-8")).hexdigest() != self.sha256
        ):
            raise ValueError("Local catalog content differs from its bounded frozen identity")
        catalog = strict_json(self.content)
        if (
            not isinstance(catalog, dict)
            or set(catalog) != {"models"}
            or not isinstance(catalog["models"], list)
            or len(catalog["models"]) != 1
            or not isinstance(catalog["models"][0], dict)
        ):
            raise ValueError("Local catalog must declare exactly one model")
        model = catalog["models"][0]
        slug, window = model.get("slug"), model.get("context_window")
        if (
            not isinstance(slug, str)
            or not slug.strip()
            or any(ord(character) < 32 for character in slug)
            or type(window) is not int
            or not 1 <= window <= 2_000_000
        ):
            raise ValueError("Local catalog model identity or context window is invalid")
        messages = model.get("model_messages")
        if messages is not None and not isinstance(messages, dict):
            raise ValueError("Local catalog model messages must be an object")
        template = messages.get("instructions_template") if messages is not None else None
        legacy = model.get("base_instructions")
        if template is not None and legacy is not None and template != legacy:
            raise ValueError("Local catalog contains conflicting instruction templates")
        instructions = template if template is not None else legacy
        if not isinstance(instructions, str) or not instructions.strip():
            raise ValueError("Local catalog must explicitly retain substantive model instructions")
        return model

    def asset(self) -> dict[str, str]:
        return {"path": self.location, "sha256": self.sha256}

    def record(self) -> dict[str, str]:
        return {**self.asset(), "content": self.content}


def decode_local_record(value: Any) -> LocalCatalog:
    """Replay declared metadata without reading original filesystem paths."""
    if (
        not isinstance(value, dict)
        or set(value) != {"path", "sha256", "content"}
        or any(not isinstance(item, str) for item in value.values())
    ):
        raise ValueError("Local catalog record is incomplete or invalid")
    catalog = LocalCatalog(value["path"], value["sha256"], value["content"])
    catalog.metadata()
    return catalog


def load_local_catalog(entry: Any) -> LocalCatalog:
    """Bind a small native catalog asset before any subject execution."""
    if (
        not isinstance(entry, dict)
        or set(entry) != {"path", "sha256"}
        or any(not isinstance(item, str) for item in entry.values())
        or not Path(entry["path"]).is_absolute()
    ):
        raise ValueError("Local catalog requires an explicit frozen asset")
    path = checked_path(Path(entry["path"]))
    if not path.is_file() or not 0 < path.stat().st_size <= LOCAL_CATALOG_LIMIT:
        raise ValueError("Local catalog exceeds its input bounds or is missing")
    with path.open("rb") as stream:
        raw = stream.read(LOCAL_CATALOG_LIMIT + 1)
    catalog = LocalCatalog(str(path), entry["sha256"], raw.decode("utf-8"))
    catalog.metadata()
    return catalog


def verify_local_catalog(catalog: LocalCatalog) -> None:
    if load_local_catalog(catalog.asset()) != catalog:
        raise ValueError("Local catalog changed during execution")


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
def catalog_lease(context: TrialContext, provider: Any, *, local: LocalCatalog | None = None) -> Iterator[TrialContext]:
    """Freeze vendor sign-in metadata or an explicitly declared anonymous catalog.

    Account/quota/model metadata probes retain their distinct selected-profile
    contract. This lease never copies, edits or exports authentication storage.
    """
    if local is not None:
        if (
            provider is None
            or validate_provider(provider).get("authentication") != "none"
            or context.signin is not None
            or context.native_catalog is not None
            or context.local_catalog is not None
        ):
            raise ValueError("Local catalog requires an anonymous provider and no prior catalog or sign-in binding")
        verify_local_catalog(local)
        try:
            yield replace(context, local_catalog=local)
        finally:
            verify_local_catalog(local)
        return
    if context.local_catalog is not None:
        raise ValueError("A prior local catalog binding must not enter another lease")
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
