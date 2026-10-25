#!/usr/bin/env python3
"""Exercise native Crawl4AI result, launch-flag and Windows download contracts.

Run inside an explicitly qualified provider. This program installs nothing and
requests only its controlled loopback HTTP fixture. It never launches a browser.
The same evaluator and expectations apply to original and repaired packages.
"""

from __future__ import annotations

import argparse
import asyncio
import errno
import hashlib
import importlib.metadata
import json
import os
import threading
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def error_chain(error: BaseException) -> list[BaseException]:
    """Inspect wrapped native failures so an unrelated outage cannot pass rejection controls."""
    result = []
    while error not in result:
        result.append(error)
        following = error.__cause__ or error.__context__
        if following is None:
            break
        error = following
    return result


def model_controls(check: Callable[..., None]) -> dict[str, Any]:
    from crawl4ai.models import CrawlResult, MarkdownGenerationResult

    def failed():
        return CrawlResult(
            url="https://fixture.invalid/denied",
            html="",
            success=False,
            status_code=403,
            error_message="Controlled refusal",
        )

    def json_failure():
        value = failed().model_dump(mode="json")
        require(
            value["status_code"] == 403
            and value["success"] is False
            and value["error_message"] == "Controlled refusal",
            "native refusal changed",
        )
        require(value["fit_html"] is None, "unset optional value is not null")

    def cli_failure():
        value = json.loads(json.dumps(failed().model_dump()))
        require(value["fit_html"] is None, "property descriptor entered CLI-style JSON")

    def explicit():
        result = CrawlResult(
            url="https://fixture.invalid", html="content", success=True, fit_html="preprocessed content"
        )
        require(
            result.fit_html == result.model_dump(mode="json")["fit_html"] == "preprocessed content",
            "explicit data field was lost",
        )

    def assignment():
        result = failed()
        result.fit_html = "updated content"
        require(
            result.fit_html == result.model_dump(mode="json")["fit_html"] == "updated content",
            "assigned data field was lost",
        )

    def field_default():
        require(CrawlResult.model_fields["fit_html"].default is None, "data-field default is not null")

    def markdown():
        text = MarkdownGenerationResult(
            raw_markdown="substantive native text",
            markdown_with_citations="substantive native text",
            references_markdown="",
        )
        result = CrawlResult(
            url="https://fixture.invalid", html="content", success=True, fit_html="preprocessed content", markdown=text
        )
        value = result.model_dump(mode="json")
        require(
            value["markdown"]["raw_markdown"] == "substantive native text"
            and value["fit_html"] == "preprocessed content",
            "markdown/preprocessed data changed",
        )

    for name, operation in (
        ("native_failure_json", json_failure),
        ("cli_style_failure_json", cli_failure),
        ("explicit_fit_html", explicit),
        ("assigned_fit_html", assignment),
        ("null_field_default", field_default),
        ("markdown_and_preprocessed_data", markdown),
    ):
        check(name, operation)
    try:
        CrawlResult.model_json_schema()
        return {"whole_result_json_schema_supported": True}
    except Exception as exc:
        # This pre-existing arbitrary-SSLCertificate schema limitation remains
        # visible; the repairs do not claim to support every SDK operation.
        return {"whole_result_json_schema_supported": False, "error_type": type(exc).__name__, "error": str(exc)}


def flag_controls(check: Callable[..., None]) -> None:
    from crawl4ai import BrowserConfig
    from crawl4ai.browser_manager import BrowserManager, ManagedBrowser

    for mode in (False, True):
        configuration = BrowserConfig(enable_stealth=mode, verbose=False)
        for name in ("managed", "ordinary"):

            def operation(configuration=configuration, name=name, mode=mode):
                flags = (
                    ManagedBrowser.build_browser_flags(configuration)
                    if name == "managed"
                    else BrowserManager(browser_config=configuration)._build_browser_args()["args"]
                )
                require(
                    any("AutomationControlled" in flag for flag in flags) == mode,
                    "automation hiding does not follow explicit stealth mode",
                )

            check(f"{name}_explicit_stealth_{mode}", operation)


async def http_controls(checks: list[dict[str, Any]], fixture: Path) -> list[str]:
    import psutil
    from crawl4ai import CrawlerRunConfig
    from crawl4ai.async_configs import HTTPCrawlerConfig
    from crawl4ai.async_crawler_strategy import AsyncHTTPCrawlerStrategy, _nofollow_opener
    from crawl4ai.async_logger import AsyncLogger

    body = b"native download bytes\x00\x01\x02\xff"
    requests: list[str] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Content-Disposition", f'attachment; filename="{self.path.removeprefix("/")}"')
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    async def download(directory, name):
        configuration = HTTPCrawlerConfig(
            downloads_path=str(directory),
            verify_ssl=True,
            follow_redirects=False,
            headers={"User-Agent": "AI-Skills-Qualification/0.9.5"},
        )
        async with AsyncHTTPCrawlerStrategy(browser_config=configuration, logger=AsyncLogger(verbose=False)) as crawler:
            return await crawler.crawl(
                f"http://127.0.0.1:{server.server_port}/{name}", config=CrawlerRunConfig(page_timeout=10000)
            )

    async def check(name, operation):
        try:
            observed = await operation()
            checks.append({"name": name, "passed": True, "observed": observed})
        except Exception as exc:
            checks.append({"name": name, "passed": False, "error_type": type(exc).__name__, "error": str(exc)})

    async def valid_http():
        directory = fixture / "http-normal"
        response = await download(directory, "fixture.bin")
        require(response.status_code == 200 and len(response.downloaded_files) == 1, "native HTTP download failed")
        path = Path(response.downloaded_files[0])
        require(
            path.resolve().is_relative_to(directory.resolve()) and path.read_bytes() == body,
            "native download changed bytes or destination",
        )

    async def ordinary():
        path = fixture / "ordinary.bin"
        with open(path, "wb", opener=_nofollow_opener) as stream:
            stream.write(body)
        with open(path, "rb", opener=_nofollow_opener) as stream:
            require(stream.read() == body, "binary readback differs")

    async def append():
        path = fixture / "append.bin"
        path.write_bytes(b"prefix:")
        with open(path, "ab", opener=_nofollow_opener) as stream:
            stream.write(body)
        require(path.read_bytes() == b"prefix:" + body, "append overwrote existing bytes")

    async def unicode():
        path = fixture / "unicode-δείγμα.bin"
        with open(path, "wb", opener=_nofollow_opener) as stream:
            stream.write(body)
        require(path.read_bytes() == body, "Unicode destination changed bytes")

    async def hardlink():
        target = fixture / "target"
        target.write_bytes(b"preserve existing target")
        directory = fixture / "hardlink"
        directory.mkdir()
        link = directory / "linked.bin"
        os.link(target, link)
        try:
            await download(directory, "linked.bin")
        except Exception as error:
            require(
                any(isinstance(item, OSError) and item.errno == errno.EPERM for item in error_chain(error)),
                "download failed without enforcing the hardlink contract",
            )
            require(
                target.read_bytes() == link.read_bytes() == b"preserve existing target", "rejected target was truncated"
            )
            return
        raise ValueError("multiply linked download destination was accepted")

    async def handles():
        target, link = fixture / "handle-target", fixture / "handle-link"
        target.write_bytes(b"preserve this")
        os.link(target, link)

        def attempt():
            try:
                with open(link, "wb", opener=_nofollow_opener):
                    pass
            except OSError:
                return
            raise ValueError("multiply linked target was accepted")

        attempt()
        process = psutil.Process()
        before = process.num_handles()
        for _ in range(100):
            attempt()
        after = process.num_handles()
        require(
            after <= before + 2 and target.read_bytes() == b"preserve this",
            "rejection leaked handles or truncated bytes",
        )
        return {"failed_operations": 100, "handles_before": before, "handles_after": after}

    try:
        for name, operation in (
            ("http_exact_binary_download", valid_http),
            ("binary_write_and_read", ordinary),
            ("append_keeps_prefix", append),
            ("unicode_destination", unicode),
        ):
            await check(name, operation)
        for name in ("NUL", "CON", "AUX", "COM1"):

            async def reserved(name=name):
                directory = fixture / ("reserved-" + name)
                try:
                    await download(directory, name)
                except Exception as error:
                    require(
                        any(
                            isinstance(item, ValueError) and "reserved" in str(item).lower()
                            for item in error_chain(error)
                        ),
                        "download failed without reserved-name admission",
                    )
                    require(not list(directory.glob("*")), "reserved name wrote a file")
                    return
                raise ValueError("reserved Windows download name was accepted")

            await check("reserved_" + name, reserved)
        await check("hardlink_target_preserved", hardlink)
        await check("failure_path_handle_cleanup", handles)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    return requests


def run(fixture: Path) -> dict[str, Any]:
    if os.name != "nt":
        raise ValueError("these download controls require Windows; no other platform is qualified")
    fixture.mkdir()  # Never overwrite a prior fixture or reuse its files.
    checks: list[dict[str, Any]] = []

    def check(name: str, operation: Callable[[], Any]) -> None:
        try:
            operation()
            checks.append({"name": name, "passed": True})
        except Exception as exc:
            checks.append({"name": name, "passed": False, "error_type": type(exc).__name__, "error": str(exc)})

    capability = model_controls(check)
    flag_controls(check)
    requests = asyncio.run(http_controls(checks, fixture))
    return {
        "schema_version": 1,
        "evidence_class": "crawl4ai-native-component-controls",
        "provider_version": importlib.metadata.version("crawl4ai"),
        "pydantic_version": importlib.metadata.version("pydantic"),
        "nltk_version": importlib.metadata.version("nltk"),
        "evaluator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "checks": checks,
        "passed": len(checks) == 20 and all(item["passed"] for item in checks),
        "capability_probe": capability,
        "loopback_requests": requests,
        "external_pages_requested_by_evaluator": 0,
        "browser_launches": 0,
        "browser_or_external_page_qualified": False,
        "agent_efficacy_scored": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="New JSON receipt; never replaces prior results")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    # Reserve the evidence file before any native package import or fixture work.
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        try:
            result = run(args.fixture_root)
        except Exception as exc:
            result = {
                "passed": False,
                "errors": [{"error_type": type(exc).__name__, "error": str(exc)}],
                "agent_efficacy_scored": False,
            }
        stream.write(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": result["passed"], "checks": len(result.get("checks", []))}))
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
