"""Exercise a browser's latest-intent contract under fixed response ordering."""

import asyncio
import importlib.metadata
import json
from pathlib import Path

from playwright.async_api import Route, async_playwright, expect

ORIGIN = "https://catalog-fixture.invalid"
PAGE = """<!doctype html>
<title>Parts directory</title>
<form>
  <label>Filter <input name="filter"></label>
  <button type="submit">Search</button>
</form>
<section aria-label="Matches"><output id="result">None</output></section>
<script>
const form = document.querySelector('form');
const result = document.querySelector('#result');
let issued = 0;
let handled = 0;
form.addEventListener('submit', async event => {
  event.preventDefault();
  const requestNumber = ++issued;
  try {
    const filter = new FormData(form).get('filter');
    const request = await fetch('/parts?filter=' + encodeURIComponent(filter));
    const parts = await request.json();
    if (APPLY_ALL || requestNumber === issued) result.textContent = parts[0];
  } finally {
    document.body.dataset.completed = String(++handled);
  }
});
</script>
"""


async def exercise(browser, apply_all):
    context = await browser.new_context(service_workers="block")
    try:
        page = await context.new_page()
        page.set_default_timeout(4000)
        filters = {"fastener": "Washers", "seal": "Gaskets"}
        intercepted = {key: asyncio.Future() for key in filters}

        async def handle(route: Route):
            url = route.request.url
            if url == ORIGIN + "/":
                await route.fulfill(
                    content_type="text/html",
                    body=PAGE.replace("APPLY_ALL", json.dumps(apply_all)),
                )
                return
            for term in filters:
                if url == f"{ORIGIN}/parts?filter={term}" and route.request.method == "GET":
                    intercepted[term].set_result(route)
                    return
            await route.abort()

        await context.route("**/*", handle)
        await page.goto(ORIGIN + "/", wait_until="domcontentloaded")
        box = page.get_by_role("textbox", name="Filter")
        search = page.get_by_role("button", name="Search")
        output = page.locator("output")
        for term in filters:
            await box.fill(term)
            await search.click()
            await asyncio.wait_for(intercepted[term], timeout=4)
        for term in reversed(filters):
            await intercepted[term].result().fulfill(json=[filters[term]])
            if term == "seal":
                await expect(output).to_have_text("Gaskets", timeout=3000)
        await expect(page.locator("body")).to_have_attribute("data-completed", "2", timeout=3000)
        visible = await output.inner_text()
        return {"visible_result": visible, "settled_responses": 2, "latest_intent_preserved": visible == "Gaskets"}
    finally:
        await context.close()


async def main():
    async with async_playwright() as provider:
        browser = await provider.chromium.launch(
            executable_path=Path(provider.chromium.executable_path), chromium_sandbox=True
        )
        try:
            rows = {"current_intent": [], "late_result_overwrites": []}
            for _ in range(3):
                rows["current_intent"].append(await exercise(browser, False))
                rows["late_result_overwrites"].append(await exercise(browser, True))
            print(json.dumps({
                "playwright": importlib.metadata.version("playwright"),
                "chromium": browser.version,
                "rounds": rows,
                "mocked_network": True,
            }, indent=2))
            if not all(row["latest_intent_preserved"] for row in rows["current_intent"]):
                raise SystemExit("Correct application failed its independent UI contract")
            if not all(row["visible_result"] == "Washers" for row in rows["late_result_overwrites"]):
                raise SystemExit("Broken application escaped its independent UI contract")
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
