"""Capture one native Crawl4AI result using the admitted strict browser policy.

This product includes software developed by UncleCode (https://x.com/unclecode)
as part of the Crawl4AI project (https://github.com/unclecode/crawl4ai).
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
AGENT = "AI-Skills-Research/0.9.5 (+https://github.com/strmt7/ai_skills_collection_benchmarked)"


def admit_sources() -> dict[str, Any]:
    pin = json.loads((ROOT / "toolchains/crawl4ai/source.json").read_bytes())
    distribution = importlib.metadata.distribution("crawl4ai")
    if distribution.version != pin["version"]:
        raise ValueError("Installed provider version differs from the admitted source build")
    for record in pin["runtime_files"]:
        path = Path(str(distribution.locate_file(record["path"])))
        if not path.resolve().is_relative_to(Path(sys.prefix).resolve()):
            raise ValueError("Provider source lies outside the isolated interpreter")
        if hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
            raise ValueError("Installed provider source differs: " + record["path"])
    return pin


def validate_url(url: str) -> None:
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.hostname or parts.username is not None or parts.password is not None:
        raise ValueError("Research requires an explicit HTTPS URL without embedded credentials")


async def capture(url: str, home: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig

    browser = BrowserConfig(
        headless=True,
        use_managed_browser=False,
        use_persistent_context=False,
        user_data_dir=None,
        enable_stealth=False,
        ignore_https_errors=False,
        user_agent=AGENT,
        verbose=False,
        accept_downloads=False,
    )
    run = CrawlerRunConfig(
        check_robots_txt=True,
        page_timeout=45000,
        cache_mode=CacheMode.BYPASS,
        verbose=False,
        max_retries=0,
        fallback_fetch_function=None,
        proxy_config=None,
        proxy_rotation_strategy=None,
        extraction_strategy=None,
        magic=False,
        simulate_user=False,
        override_navigator=False,
        user_agent=AGENT,
    )
    observations = []
    async with AsyncWebCrawler(config=browser) as crawler:

        async def observe(page: Any, **_kwargs: Any) -> Any:
            import psutil

            if urlsplit(page.url).scheme != "https":
                raise ValueError("The browser redirected research to an unencrypted page")
            webdriver = await page.evaluate("navigator.webdriver")
            if webdriver is not True:
                raise ValueError("The live browser is hiding automation")
            profiles = []
            browser_count = 0
            for child in psutil.Process().children(recursive=True):
                try:
                    if not any(name in child.name().lower() for name in ["chrome", "headless_shell"]):
                        continue
                    arguments = child.cmdline()
                except psutil.NoSuchProcess:
                    continue
                browser_count += 1
                if any("AutomationControlled" in value for value in arguments) or any(
                    value in {"--no-sandbox", "--disable-setuid-sandbox"} for value in arguments
                ):
                    raise ValueError("The live browser has a forbidden automation or sandbox flag")
                for value in arguments:
                    if value.startswith("--user-data-dir="):
                        profile = Path(value.split("=", 1)[1]).resolve()
                        if not profile.is_relative_to(home.resolve()):
                            raise ValueError("The live browser profile is outside the owned provider home")
                        profiles.append(hashlib.sha256(str(profile).encode()).hexdigest())
            if not browser_count or not profiles:
                raise ValueError("Actual browser process and isolated profile evidence are missing")
            observations.append(
                {
                    "navigator_webdriver": True,
                    "final_page_url": page.url,
                    "browser_processes": browser_count,
                    "profile_sha256": sorted(set(profiles)),
                    "forbidden_flags": [],
                }
            )
            return page

        crawler.crawler_strategy.set_hook("after_goto", observe)
        result = await crawler.arun(url, config=run)
        return result.model_dump(mode="json"), observations


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--home", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    validate_url(args.url)
    if args.output.exists() or args.metadata.exists():
        raise ValueError("Preserve existing result and metadata files; select new destinations")
    if os.environ.get("CRAWL4AI_CHROMIUM_SANDBOX") != "true":
        raise ValueError("Chromium sandbox opt-in is mandatory")
    pin = admit_sources()
    native, observations = asyncio.run(capture(args.url, args.home))
    data = (json.dumps(native, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    with args.output.open("xb") as stream:
        stream.write(data)
    markdown = native.get("markdown", {})
    text = markdown.get("raw_markdown", "") if isinstance(markdown, dict) else markdown or ""
    eligible = (
        native.get("success") is True
        and native.get("status_code") == 200
        and native.get("url") == args.url
        and len(text.strip()) >= 80
        and bool(observations)
    )
    metadata = {
        "provider_version": pin["version"],
        "intended_url": args.url,
        "native_url": native.get("url"),
        "native_result_sha256": hashlib.sha256(data).hexdigest(),
        "native_result_bytes": len(data),
        "status_code": native.get("status_code"),
        "success": native.get("success"),
        "error": native.get("error_message"),
        "markdown_characters": len(text),
        "scope_reviewed": False,
        "eligible_for_scope_review": eligible,
        "source_files_admitted": len(pin["runtime_files"]),
        "capture_implementation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "browser_observations": observations,
        "strict_policy": {
            "robots": True,
            "tls_verification": True,
            "sandbox": True,
            "stealth": False,
            "automation_disclosed": True,
            "personal_profile": False,
            "external_llm": False,
            "max_retries": 0,
            "fallback": False,
        },
        "agent_efficacy_claim": False,
    }
    with args.metadata.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(metadata, indent=2) + "\n")
    print(
        json.dumps(
            {
                "eligible_for_scope_review": eligible,
                "status_code": metadata["status_code"],
                "markdown_characters": len(text),
                "provider_version": pin["version"],
            }
        )
    )
    return int(not eligible)


if __name__ == "__main__":
    raise SystemExit(main())
