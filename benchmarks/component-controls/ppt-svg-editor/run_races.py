"""Check asynchronous selection and slide changes in the repaired SVG editor."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

REPAIRED = "25aad0d453babd2df3c4f3b9185308a5b94bae738868ad520044f55792b74cb7"
BASE = "http://127.0.0.1:1"


def exercise(browser, html: str, source: bytes, css: str, action: str, transition: str) -> dict:
    first = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450"><text id="parent" x="50" y="80" font-size="36"><tspan id="line">Hello world</tspan></text>'
    if transition == "selection":
        first += '<rect id="next" x="400" y="100" width="150" height="100" fill="blue"/>'
    first += "</svg>"
    second = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450"><rect id="next" x="40" y="40" width="150" height="100" fill="blue"/></svg>'
    context = browser.new_context(viewport={"width": 1400, "height": 900}, service_workers="block")
    try:
        page = context.new_page()
        errors, unexpected = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))

        def route(request_route):
            path = request_route.request.url.removeprefix(BASE)
            if path == "/":
                request_route.fulfill(content_type="text/html; charset=utf-8", body=html)
            elif path == "/static/app.js":
                request_route.fulfill(content_type="application/javascript; charset=utf-8", body=source)
            elif path == "/static/style.css":
                request_route.fulfill(content_type="text/css; charset=utf-8", body=css)
            elif path == "/api/config":
                request_route.fulfill(json={"live": False})
            elif path == "/api/slides":
                request_route.fulfill(
                    json={"slides": [{"name": "one.svg", "mtime": 1}, {"name": "two.svg", "mtime": 1}]}
                )
            elif path in {"/api/slide/one.svg", "/api/slide/two.svg"}:
                request_route.fulfill(
                    json={
                        "content": first if "one.svg" in path else second,
                        "annotations": [],
                        "mtime": 1,
                        "undo_depth": 0,
                    }
                )
            else:
                unexpected.append(path)
                request_route.abort()

        context.route("**/*", route)
        page.goto(BASE + "/", wait_until="load", timeout=15000)
        line = page.locator("#line")
        line.wait_for(state="visible")
        line.click()
        page.evaluate(
            """failure => {
          const original = window.fetch;
          window.fetch = function (url, options) {
            if (String(url).endsWith('/edit')) return new Promise(resolve => {
              window.releaseEdit = () => resolve(failure
                ? {ok:false,status:500,json:async()=>({error:'controlled rejection'})}
                : {ok:true,status:200,json:async()=>({undo_depth:1})});
            });
            return original(url, options);
          };
        }""",
            action == "keyboard",
        )
        if action == "keyboard":
            page.keyboard.press("ArrowRight")
        elif action == "drag":
            box = line.bounding_box()
            x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
            page.mouse.move(x, y)
            page.mouse.down()
            page.mouse.move(x + 30, y, steps=4)
            page.mouse.up()
        else:
            geo = page.locator('input.prop-edit-geo[data-geo="x"]')
            geo.fill("70")
            geo.dispatch_event("change")
        page.wait_for_function("()=>typeof window.releaseEdit==='function'", timeout=5000)
        if transition == "slide":
            page.locator('.slide-item[data-name="two.svg"]').click()
        page.locator("#next").wait_for(state="visible")
        page.locator("#next").click()
        before_selection = page.locator("#selected-element").inner_text()
        before_x = page.locator('input.prop-edit-geo[data-geo="x"]').input_value()
        page.evaluate("()=>window.releaseEdit()")
        page.wait_for_timeout(200)
        after_selection = page.locator("#selected-element").inner_text()
        after_x = page.locator('input.prop-edit-geo[data-geo="x"]').input_value()
        assert before_selection == after_selection and before_x == after_x, (
            before_selection,
            after_selection,
            before_x,
            after_x,
        )
        assert not errors and not unexpected, (errors, unexpected)
        return {
            "action": action,
            "transition": transition,
            "selection_preserved": True,
            "geometry_preserved": True,
            "external_requests": 0,
        }
    finally:
        context.close()


def main() -> int:
    if not __debug__:
        raise RuntimeError("run controls without Python optimization")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repaired-skill", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    skill = args.repaired_skill.resolve(strict=True)
    output = args.output.absolute()
    if output.exists() or output.is_symlink() or not output.parent.is_dir():
        raise ValueError("output must be a new directory with an existing parent")
    if output.resolve().is_relative_to(skill) or skill.is_relative_to(output.resolve()):
        raise ValueError("output must not overlap the skill")
    static = skill / "scripts/svg_editor/static"
    source = (static / "app.js").read_bytes()
    if hashlib.sha256(source).hexdigest() != REPAIRED:
        raise ValueError("unqualified editor bytes")
    html = (static / "index.html").read_text(encoding="utf-8")
    css = (static / "style.css").read_text(encoding="utf-8")
    output.mkdir()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, chromium_sandbox=True)
        try:
            rows = [
                exercise(browser, html, source, css, action, transition)
                for action in ("keyboard", "drag", "geometry")
                for transition in ("slide", "selection")
            ]
            result = {
                "cases": rows,
                "browser_version": browser.version,
                "source_sha256": REPAIRED,
                "sandbox_requested": True,
                "real_server": False,
                "model_performance_claim": False,
            }
        finally:
            browser.close()
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
