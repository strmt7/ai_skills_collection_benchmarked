const fs = require('node:fs');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const playwright = require(process.argv[2]);
const engine = process.argv[5] || 'chromium';
const layout = process.argv[6] || 'landscape';
const viewport = layout === 'narrow' ? { width: 390, height: 844 } : { width: 844, height: 390 };
const digest = (data) => crypto.createHash('sha256').update(data).digest('hex');
const source = fs.readFileSync(process.argv[3], 'utf8').replace(/\r\n/g, '\n');
const candidate = fs.readFileSync(process.argv[4], 'utf8').replace(/\r\n/g, '\n');
assert.equal(digest(source), 'fd5b051a37365fc6059c75bb388ec6f64daf1bd9ae938b287b6d762dc83c0c35');
assert.equal(digest(candidate), '0ed28b587e769cd036f1f1e46f31dee7f9149c263ea8be8c95d4e51f3e1d908d');
assert.equal(require(`${process.argv[2]}/package.json`).version, '1.64.1');
const placeholder = '<!-- More slides... (always wrap content in .slide-content) -->';
const paragraphs = Array.from(
  { length: 32 },
  (_, i) => `<p id="paragraph-${i}">Paragraph ${i + 1}: example content that must remain reachable and readable.</p>`,
).join('');
const extra = `<div class="slide"><div class="slide-content"><h2>Long slide</h2>${paragraphs}</div></div>`;
function fixture(text) {
  const match = text.match(/```html\n([\s\S]*?)\n```/);
  assert(match && match[1].split(placeholder).length === 2);
  return match[1].replace(placeholder, extra + '\n' + placeholder);
}
(async () => {
  const browser = await playwright[engine].launch({ headless: true });
  async function probe(text) {
    const page = await browser.newPage({ viewport, hasTouch: true });
    let blocked = 0;
    await page.route('**/*', (route) => {
      blocked += 1;
      return route.abort();
    });
    try {
      await page.setContent(fixture(text), { waitUntil: 'load', timeout: 15000 });
      assert(blocked >= 1);
      await page.locator('.nav-controls button').last().click();
      const slide = page.locator('.slide.active');
      const initial = await slide.evaluate((el) => ({
        height: el.clientHeight,
        scroll_height: el.scrollHeight,
        top: el.scrollTop,
        tabindex: el.getAttribute('tabindex'),
        first_top: document.querySelector('#paragraph-0').getBoundingClientRect().top,
        slide_top: el.getBoundingClientRect().top,
      }));
      await page.mouse.move(viewport.width / 2, 80);
      await page.mouse.wheel(0, 350);
      let wheelScrolled = true;
      try {
        await page.waitForFunction(() => document.querySelector('.slide.active').scrollTop > 0, null, {
          timeout: 1500,
        });
      } catch (error) {
        if (error.name !== 'TimeoutError') throw error;
        wheelScrolled = false;
      }
      await slide.evaluate((el) => {
        el.scrollTop = 0;
      });
      await slide.focus();
      const focused = await slide.evaluate((el) => document.activeElement === el);
      await page.keyboard.press('ArrowDown');
      let keyboardScrolled = true;
      try {
        await page.waitForFunction(() => document.querySelector('.slide.active').scrollTop > 0, null, {
          timeout: 1500,
        });
      } catch (error) {
        if (error.name !== 'TimeoutError') throw error;
        keyboardScrolled = false;
      }
      if (focused && keyboardScrolled) {
        await page.keyboard.press('End');
        await page.waitForFunction(
          () => {
            const e = document.querySelector('.slide.active');
            return e.scrollTop + e.clientHeight >= e.scrollHeight - 1;
          },
          null,
          { timeout: 3000 },
        );
      }
      const end = await page.evaluate(() => {
        const slide = document.querySelector('.slide.active');
        const last = document.querySelector('#paragraph-31').getBoundingClientRect();
        const nav = document.querySelector('.nav-controls').getBoundingClientRect();
        const rect = slide.getBoundingClientRect();
        return {
          top: slide.scrollTop,
          last_top: last.top,
          last_bottom: last.bottom,
          nav_top: nav.top,
          slide_top: rect.top,
          slide_bottom: rect.bottom,
        };
      });
      return { initial, focused, wheel_scrolled: wheelScrolled, keyboard_scrolled: keyboardScrolled, end };
    } finally {
      await page.close();
    }
  }
  try {
    const original = await probe(source);
    const repaired = await probe(candidate);
    assert(original.end.last_bottom > original.end.nav_top);
    assert.equal(original.focused, false);
    assert.equal(original.wheel_scrolled, false);
    assert.equal(original.keyboard_scrolled, false);
    assert(repaired.initial.scroll_height > repaired.initial.height);
    assert.equal(repaired.focused, true);
    assert.equal(repaired.wheel_scrolled, true);
    assert(repaired.initial.first_top >= repaired.initial.slide_top);
    assert.equal(repaired.keyboard_scrolled, true);
    assert(
      repaired.end.last_top >= repaired.end.slide_top &&
        repaired.end.last_bottom <= repaired.end.nav_top + 1 &&
        repaired.end.last_bottom <= repaired.end.slide_bottom + 1,
    );
    console.log(
      JSON.stringify(
        {
          source_sha256: digest(source),
          candidate_sha256: digest(candidate),
          node_version: process.version,
          playwright_version: require(`${process.argv[2]}/package.json`).version,
          platform: process.platform,
          architecture: process.arch,
          browser_engine: engine,
          browser_version: browser.version(),
          viewport,
          original,
          repaired,
          full_accessibility_audit: false,
          agent_performance_tested: false,
        },
        null,
        2,
      ),
    );
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
