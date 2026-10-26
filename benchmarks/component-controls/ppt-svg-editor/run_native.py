"""Exercise the PPT Master SVG text-move repair in Chromium and a real local backend."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import subprocess
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from playwright.sync_api import sync_playwright

ORIGINAL = "57b6139bfab8be058e8ced99e47dde86a89dddcc58bfb9cc53baa9ab175c747a"
REPAIRED = "25aad0d453babd2df3c4f3b9185308a5b94bae738868ad520044f55792b74cb7"
SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450"><text id="parent" x="50" y="80" font-size="36"><tspan id="line">Hello world</tspan></text></svg>'
POSITION = "el => { const b=el.getBBox(), m=el.getCTM(); return {x:b.x*m.a+b.y*m.c+m.e,y:b.x*m.b+b.y*m.d+m.f} }"


def run_case(browser, skill: Path, backend_python: Path, output: Path, mode: str) -> dict:
    source = skill / "scripts/svg_editor/static/app.js"
    source_bytes = source.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    normalized_hash = hashlib.sha256(source_bytes.replace(b"\r\n", b"\n")).hexdigest()
    assert normalized_hash == ORIGINAL if mode == "original" else source_hash == REPAIRED, "unqualified editor bytes"
    project = output / mode
    (project / "svg_output").mkdir(parents=True)
    slide = project / "svg_output/one.svg"
    slide.write_text(SVG, encoding="utf-8")
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    with (project / "server.log").open("xb") as log:
        proc = subprocess.Popen(
            [
                str(backend_python),
                str(skill / "scripts/svg_editor/server.py"),
                str(project),
                "--port",
                str(port),
                "--no-browser",
            ],
            stdout=log,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            env=env,
            creationflags=flags,
        )
        try:
            for _ in range(100):
                if proc.poll() is not None:
                    raise RuntimeError("test server exited before readiness")
                try:
                    with urllib.request.urlopen(base + "/api/health", timeout=0.25) as response:
                        health = json.load(response)
                    if Path(health["project"]).resolve() != project.resolve():
                        raise RuntimeError("unexpected server on test port")
                    break
                except (urllib.error.URLError, TimeoutError):
                    time.sleep(0.1)
            else:
                raise RuntimeError("test server did not become ready")
            errors, external, responses, edits = [], [], [], []
            context = browser.new_context(viewport={"width": 1400, "height": 900}, service_workers="block")
            try:
                page = context.new_page()
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on(
                    "response",
                    lambda response: responses.append(response.status) if response.url.endswith("/edit") else None,
                )
                page.on(
                    "request",
                    lambda request: (
                        edits.append(request.post_data_json)
                        if request.url.endswith("/edit") and request.method == "POST"
                        else None
                    ),
                )

                def guard(route):
                    if route.request.url.startswith(base + "/"):
                        route.continue_()
                    else:
                        external.append(route.request.url)
                        route.abort()

                context.route("**/*", guard)
                page.goto(base + "/", wait_until="load", timeout=15000)
                line = page.locator("#svg-content #line")
                line.wait_for(state="visible", timeout=10000)
                before = line.evaluate(POSITION)
                line.click()
                assert "svg-selected" in line.get_attribute("class").split()
                if mode.endswith("reject"):
                    slide.write_text(SVG.replace('id="line"', 'id="removed"'), encoding="utf-8")
                if mode.startswith("drag"):
                    box = line.bounding_box()
                    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
                    page.mouse.move(x, y)
                    page.mouse.down()
                    page.mouse.move(x + 30, y, steps=4)
                    page.mouse.up()
                elif mode.startswith("geometry"):
                    geo = page.locator('input.prop-edit-geo[data-geo="x"]')
                    geo.fill("70")
                    geo.press("Tab")
                else:
                    page.keyboard.press("ArrowRight")
                if mode == "original":
                    page.wait_for_timeout(150)
                    assert any("markSelection is not defined" in item for item in errors), errors
                    assert not responses
                else:
                    for _ in range(50):
                        page.wait_for_timeout(100)
                        if responses and (
                            not mode.endswith("reject")
                            or page.locator("#line").evaluate("el=>el.tagName.toLowerCase()") == "tspan"
                        ):
                            break
                    assert responses == [404 if mode.endswith("reject") else 200], responses
                    assert not errors, errors
                    selected = page.locator("#line")
                    assert "svg-selected" in selected.get_attribute("class").split()
                    if mode.endswith("reject"):
                        assert selected.evaluate("el=>el.tagName.toLowerCase()") == "tspan"
                        after = selected.evaluate(POSITION)
                        assert abs(after["x"] - before["x"]) < 0.001 and abs(after["y"] - before["y"]) < 0.001, (
                            before,
                            after,
                        )
                    else:
                        assert selected.evaluate("el=>el.tagName.toLowerCase()") == "text"
                        saved = page.evaluate(
                            "async()=>{let r=await fetch('/api/save-all',{method:'POST'});return {status:r.status,data:await r.json()}}"
                        )
                        assert saved["status"] == 200, saved
                        element = next(x for x in ET.parse(slide).getroot().iter() if x.get("id") == "line")
                        assert element.tag.endswith("text") and len(edits) == 1
                        assert float(element.get("x")) == float(edits[0]["promote_tspan"]["x"]) > 50
                        assert "".join(element.itertext()) == "Hello world"
                assert not external, external
                return {
                    "case": mode,
                    "source_sha256": source_hash,
                    "edit_statuses": responses,
                    "page_errors": errors,
                    "external_requests": len(external),
                    "saved_svg_sha256": hashlib.sha256(slide.read_bytes()).hexdigest(),
                }
            finally:
                context.close()
        finally:
            if proc.poll() is None:
                proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)


def main() -> int:
    if not __debug__:
        raise RuntimeError("run controls without Python optimization")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-skill", type=Path, required=True)
    parser.add_argument("--repaired-skill", type=Path, required=True)
    parser.add_argument("--backend-python", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    original = args.original_skill.resolve(strict=True)
    repaired = args.repaired_skill.resolve(strict=True)
    backend = args.backend_python.resolve(strict=True)
    output = args.output.absolute()
    if output.exists() or output.is_symlink() or not output.parent.is_dir():
        raise ValueError("output must be a new directory with an existing parent")
    if any(
        output.resolve().is_relative_to(path) or path.is_relative_to(output.resolve()) for path in (original, repaired)
    ):
        raise ValueError("output must not overlap either skill")
    output.mkdir()
    cases = (
        "original",
        "keyboard-success",
        "keyboard-reject",
        "drag-success",
        "drag-reject",
        "geometry-success",
        "geometry-reject",
    )
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, chromium_sandbox=True)
        try:
            rows = [
                run_case(browser, original if case == "original" else repaired, backend, output, case) for case in cases
            ]
            result = {
                "cases": rows,
                "browser_version": browser.version,
                "sandbox_requested": True,
                "real_server": True,
                "external_requests": 0,
                "model_performance_claim": False,
            }
        finally:
            browser.close()
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
