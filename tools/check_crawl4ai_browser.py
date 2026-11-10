"""Exercise real crawler processes against independent local HTTP fixtures."""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import crawl4ai_capture as strict
import crawl4ai_runtime as runtime


def run_controls(home: Path) -> dict[str, Any]:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig

    runtime.check_runtime(home)
    runtime.check_browser(home)
    requests: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    results: dict[str, Any] = {}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, _format: str, *args: Any) -> None:
            pass

        def do_GET(self) -> None:
            path = urlsplit(self.path).path
            requests.append({"path": path, "user_agent": self.headers.get("User-Agent")})
            if path == "/robots.txt":
                body, mime = b"User-agent: *\nDisallow: /denied\n", "text/plain"
            else:
                if path == "/slow":
                    time.sleep(2)
                body = (
                    b"<html><head><title>Independent crawler qualification</title></head><body>"
                    b"<h1>Browser contract fixture</h1><p>Exact qualification content alpha beta gamma delta. "
                    b"This paragraph is independent from crawler implementation and verifies substantive "
                    b"native extraction.</p></body></html>"
                )
                mime = "text/html"
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            # The timeout control deliberately closes its HTTP connection.
            with contextlib.suppress(BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                self.wfile.write(body)

    def require(condition: bool, message: str) -> None:
        checks.append({"name": message, "passed": bool(condition)})
        if not condition:
            raise ValueError(message)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    async def controls() -> None:
        browser = BrowserConfig(
            headless=True,
            use_managed_browser=False,
            use_persistent_context=False,
            user_data_dir=None,
            enable_stealth=False,
            ignore_https_errors=False,
            user_agent=strict.AGENT,
            verbose=False,
            accept_downloads=False,
        )
        config = CrawlerRunConfig(
            check_robots_txt=True,
            page_timeout=10000,
            cache_mode=CacheMode.BYPASS,
            verbose=False,
            max_retries=0,
            fallback_fetch_function=None,
            extraction_strategy=None,
            magic=False,
            simulate_user=False,
            override_navigator=False,
            user_agent=strict.AGENT,
        )
        async with AsyncWebCrawler(config=browser) as crawler:

            async def observe(page: Any, **_kwargs: Any) -> Any:
                observations.append(
                    {
                        "webdriver": await page.evaluate("navigator.webdriver"),
                        "user_agent": await page.evaluate("navigator.userAgent"),
                        "url": page.url,
                        **strict.browser_evidence(home),
                        "commands": strict.browser_commands(),
                    }
                )
                return page

            crawler.crawler_strategy.set_hook("after_goto", observe)
            base = "http://127.0.0.1:" + str(server.server_port)
            allowed = await crawler.arun(base + "/allowed", config=config)
            results["allowed"] = allowed.model_dump(mode="json")
            require(
                allowed.success is True
                and allowed.status_code == 200
                and "Exact qualification content alpha beta gamma delta." in allowed.markdown.raw_markdown,
                "allowed page native content and status",
            )
            require(
                bool(observations) and all(item["webdriver"] is True for item in observations),
                "live automation disclosure",
            )
            require(all(item["user_agent"] == strict.AGENT for item in observations), "identifying browser user agent")
            require(
                all(
                    item["browser_processes"] > 0 and item["profile_sha256"] and not item["forbidden_flags"]
                    for item in observations
                ),
                "actual isolated browser processes and strict sandbox flags",
            )
            require(
                all(
                    Path(command[0]).resolve().is_relative_to((home / "browsers").resolve())
                    for item in observations
                    for command in item["commands"]
                ),
                "owned browser executable paths",
            )
            denied = await crawler.arun(base + "/denied", config=config)
            results["denied"] = denied.model_dump(mode="json")
            require(
                denied.success is False
                and "robots.txt" in denied.error_message
                and not any(item["path"] == "/denied" for item in requests),
                "robots denial prevents page request",
            )
            require(any(item["path"] == "/robots.txt" for item in requests), "robots rules actually requested")
            slow = await crawler.arun(base + "/slow", config=config.clone(page_timeout=500))
            results["timeout"] = slow.model_dump(mode="json")
            require(
                slow.success is False and sum(item["path"] == "/slow" for item in requests) == 1,
                "bounded timeout without retry or fallback",
            )

    error = None
    try:
        asyncio.run(controls())
        require(not strict.browser_commands(), "browser children closed by crawler context")
        require(
            not any(
                key in os.environ
                for key in [
                    "OPENAI_API_KEY",
                    "ANTHROPIC_API_KEY",
                    "GOOGLE_API_KEY",
                    "AZURE_OPENAI_API_KEY",
                ]
            ),
            "no external model credentials inherited",
        )
    except Exception as failure:
        error = str(failure)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
    return {
        "passed": error is None and len(checks) == 10,
        "error": error,
        "checks": checks,
        "observations": observations,
        "results": results,
        "requests": requests,
        "external_page_qualified": False,
        "agent_efficacy_scored": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.output.exists():
        raise ValueError("Preserve existing browser-control evidence; select a new output")
    result = run_controls(args.home)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": result["passed"], "checks": len(result["checks"]), "error": result["error"]}))
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
