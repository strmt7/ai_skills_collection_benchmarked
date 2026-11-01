const fs = require('node:fs');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const playwright = require(process.argv[2]);
const playwrightVersion = require(`${process.argv[2]}/package.json`).version;
const reference = fs.readFileSync(process.argv[3], 'utf8');
const canonical = reference.replace(/\r\n/g, '\n');
const digest = data => crypto.createHash('sha256').update(data).digest('hex');
const expectedSource = 'fd5b051a37365fc6059c75bb388ec6f64daf1bd9ae938b287b6d762dc83c0c35';
assert.equal(digest(canonical), expectedSource, 'Source differs from the pinned upstream template');
assert.equal(playwrightVersion, '1.64.1', 'Unexpected Playwright version');
const match = canonical.match(/```html\n([\s\S]*?)\n```/);
assert(match, 'Base HTML code fence was not found');
const placeholder = '<!-- More slides... (always wrap content in .slide-content) -->';
assert.equal(match[1].split(placeholder).length, 2, 'Expected exactly one placeholder');
const second = '<div class="slide"><div class="slide-content"><h2>Second slide</h2><p>Control content</p></div></div>';
const third = '<div class="slide"><div class="slide-content"><h2>Third slide</h2><p>Control content</p></div></div>';
const html = match[1].replace(placeholder, second + '\n' + third + '\n' + placeholder);
const handler = "document.addEventListener('keydown', (e) => {";
assert.equal(html.split(handler).length, 2, 'Expected exactly one keydown handler');
const guarded = html.replace(
  handler,
  handler + "\n            if (e.key === ' ' && e.target.closest('button')) return;",
);

(async () => {
  const browser = await playwright.chromium.launch({ headless: true, executablePath: process.argv[4] });
  try {
    const blocked = [];
    const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
    await page.route('**/*', route => { blocked.push(route.request().url()); return route.abort(); });
    const current = async () => Number(await page.locator('#current').innerText());
    const previous = page.locator('button.nav-btn').first();
    const next = page.locator('button.nav-btn').last();
    await page.setContent(html, { waitUntil: 'load', timeout: 15000 });
    assert.equal(await current(), 1);
    await next.click();
    assert.equal(await current(), 2);
    await previous.click();
    assert.equal(await current(), 1);
    await next.click();
    await previous.focus();
    await page.keyboard.press('Space');
    const afterSpace = await current();
    assert.equal(afterSpace, 3, 'Observed Space behavior changed');
    await previous.click();
    assert.equal(await current(), 2);
    await previous.focus();
    await page.keyboard.press('Enter');
    assert.equal(await current(), 1, 'Native Enter control failed');

    const guardedPage = await browser.newPage({ viewport: { width: 1280, height: 720 } });
    await guardedPage.route('**/*', route => { blocked.push(route.request().url()); return route.abort(); });
    await guardedPage.setContent(guarded, { waitUntil: 'load', timeout: 15000 });
    const guardedCurrent = async () => Number(await guardedPage.locator('#current').innerText());
    const guardedPrevious = guardedPage.locator('button.nav-btn').first();
    await guardedPage.locator('button.nav-btn').last().click();
    await guardedPrevious.focus();
    await guardedPage.keyboard.press('Space');
    const guardedSpace = await guardedCurrent();
    assert.equal(guardedSpace, 1, 'Diagnostic guard did not restore button activation');
    await guardedPage.evaluate(() => document.activeElement.blur());
    await guardedPage.keyboard.press('Space');
    const guardedBodySpace = await guardedCurrent();
    assert.equal(guardedBodySpace, 2, 'Diagnostic guard changed body Space navigation');
    assert.equal(blocked.length, 2, 'Unexpected external request count');
    assert(blocked.every(url => url.startsWith('https://cdn.jsdelivr.net/npm/chart.js@4.4.1/')));

    console.log(JSON.stringify({
      source_canonical_sha256: digest(canonical), original_html_sha256: digest(match[1]),
      fixture_html_sha256: digest(html), diagnostic_guarded_fixture_sha256: digest(guarded),
      node_version: process.version, playwright_version: playwrightVersion, browser_version: browser.version(),
      viewport: { width: 1280, height: 720 }, additional_slides: 2, blocked_chart_requests: blocked.length,
      original_previous_button_click_from_slide_2: 1, original_previous_button_space_from_slide_2: afterSpace,
      original_previous_button_enter_from_slide_2: 1, guarded_previous_button_space_from_slide_2: guardedSpace,
      guarded_body_space_from_slide_1: guardedBodySpace, full_deck_visual_quality_tested: false,
      agent_performance_tested: false,
    }, null, 2));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
