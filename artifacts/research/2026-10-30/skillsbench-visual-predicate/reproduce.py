"""Exercise a pinned theme-script predicate on synthetic local pages."""

from __future__ import annotations

import ast
import hashlib
import json
import platform
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.metadata import version
from pathlib import Path

from playwright.sync_api import sync_playwright

VERIFIER_SHA256 = "9cc657768472d6887c537f488264de967a931707a78c2a346924fb9fc5ef82cd"
PAGES = {
    "/none": "<!doctype html><html><head></head><body>Test</body></html>",
    "/decoy": "<!doctype html><html><head><script>/* localStorage theme classList */</script></head><body>Test</body></html>",
    "/working": "<!doctype html><html><head><script>const theme=localStorage.getItem('theme'); if(theme) document.documentElement.classList.add(theme);</script></head><body>Test</body></html>",
}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        content = PAGES.get(self.path)
        self.send_response(200 if content is not None else 404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write((content or "Not found").encode())

    def log_message(self, format, *args):
        pass


def predicate(path: Path) -> str:
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != VERIFIER_SHA256:
        raise ValueError("Unexpected verifier bytes")
    tree = ast.parse(data.decode("utf-8"))
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "TestFlickerFixed"]
    if len(classes) != 1:
        raise ValueError("Expected flicker test class changed")
    methods = [
        node for node in classes[0].body if isinstance(node, ast.FunctionDef) and node.name == "test_no_theme_flicker"
    ]
    if len(methods) != 1:
        raise ValueError("Expected flicker test method changed")
    calls = [
        node
        for node in ast.walk(methods[0])
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "evaluate"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and isinstance(node.args[0].value, str)
    ]
    if len(calls) != 1:
        raise ValueError("Expected one literal browser predicate")
    return calls[0].args[0].value


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--verifier", type=Path, required=True)
    args = parser.parse_args()
    js = predicate(args.verifier)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    cases = {}
    browser_version = ""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser_version = browser.version
            try:
                for name in ("none", "decoy", "working"):
                    context = browser.new_context()
                    try:
                        page = context.new_page()
                        page.set_default_timeout(5000)
                        if name == "working":
                            page.add_init_script("localStorage.setItem('theme', 'dark')")
                        page.goto(f"http://127.0.0.1:{server.server_port}/{name}", wait_until="domcontentloaded")
                        cases[name] = {
                            "predicate": page.evaluate(js),
                            "dark_class_applied": page.evaluate("document.documentElement.classList.contains('dark')"),
                        }
                    finally:
                        context.close()
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        if thread.is_alive():
            raise RuntimeError("Synthetic page server did not stop")
    expected = {
        "none": {"predicate": False, "dark_class_applied": False},
        "decoy": {"predicate": True, "dark_class_applied": False},
        "working": {"predicate": True, "dark_class_applied": True},
    }
    if cases != expected:
        raise AssertionError(f"Browser predicate outcomes changed: {cases}")
    print(
        json.dumps(
            {
                "platform": platform.system(),
                "python": platform.python_version(),
                "playwright": version("playwright"),
                "chromium": browser_version,
                "verifier_sha256": VERIFIER_SHA256,
                "predicate_sha256": hashlib.sha256(js.encode()).hexdigest(),
                "cases": cases,
                "full_benchmark_executed": False,
                "model_scored": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
