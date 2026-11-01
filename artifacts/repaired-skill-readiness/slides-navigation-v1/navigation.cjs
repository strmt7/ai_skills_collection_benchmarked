const fs = require('node:fs');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const playwright = require(process.argv[2]);
const engine = process.argv[6] || 'chromium';
const layout = process.argv[7] || 'desktop';
if (!['desktop', 'narrow'].includes(layout)) throw new Error('Unsupported viewport');
const viewport = layout === 'narrow' ? { width: 390, height: 844 } : { width: 1280, height: 720 };
assertEngine();
function assertEngine() {
  if (!['chromium', 'firefox', 'webkit'].includes(engine)) throw new Error('Unsupported browser engine');
}
const playwrightVersion = require(`${process.argv[2]}/package.json`).version;
const source = fs.readFileSync(process.argv[3], 'utf8').replace(/\r\n/g, '\n');
const candidate = fs.readFileSync(process.argv[4], 'utf8').replace(/\r\n/g, '\n');
const sha = (data) => crypto.createHash('sha256').update(data).digest('hex');
assert.equal(sha(source), 'fd5b051a37365fc6059c75bb388ec6f64daf1bd9ae938b287b6d762dc83c0c35');
assert.equal(sha(candidate), '0ed28b587e769cd036f1f1e46f31dee7f9149c263ea8be8c95d4e51f3e1d908d');
assert.equal(playwrightVersion, '1.64.1');
const placeholder = '<!-- More slides... (always wrap content in .slide-content) -->';
const second = `<div class="slide"><div class="slide-content"><h2>Second slide</h2>
  <input id="input" value="abcd"><textarea id="textarea">abcd</textarea>
  <button id="action" type="button" onclick="this.dataset.clicked='true'">Action</button>
  <a id="link" href="#local">Local link</a><div id="editable" contenteditable="true"><span id="nested">abc</span></div>
  <canvas id="canvas" width="24" height="24"></canvas>
  <div id="shadow-host"></div><div id="closed-host"></div>
  <script>
    document.querySelector('#shadow-host').attachShadow({mode:'open'}).innerHTML =
      '<input id="shadow-input" value="abcd"><button id="shadow-button" type="button" onclick="this.dataset.clicked=1">Shadow action</button>';
    const closedRoot = document.querySelector('#closed-host').attachShadow({mode:'closed'});
    closedRoot.innerHTML = '<input value="abcd"><button type="button" onclick="this.dataset.clicked=1">Closed action</button>';
    window.closedInput = closedRoot.querySelector('input');
    window.closedButton = closedRoot.querySelector('button');
  </script>
  <div id="slider" role="slider" tabindex="0" aria-valuemin="0" aria-valuemax="10" aria-valuenow="5">Slider</div>
</div></div>`;
const third =
  '<div class="slide" aria-label="Custom slide" role="group" tabindex="-1"><div class="slide-content"><h2>Third slide</h2></div></div>';
const fourth =
  '<div class="slide" aria-labelledby="custom-heading" role="group" tabindex="-1"><div class="slide-content"><h2 id="custom-heading">Fourth slide</h2></div></div>';
function fixture(text) {
  const match = text.match(/```html\n([\s\S]*?)\n```/);
  assert(match);
  assert.equal(match[1].split(placeholder).length, 2);
  return match[1].replace(placeholder, second + '\n' + third + '\n' + fourth + '\n' + placeholder);
}

(async () => {
  const options = { headless: true };
  if (process.argv[5] !== 'playwright-default') options.executablePath = process.argv[5];
  const browser = await playwright[engine].launch(options);
  const blocked = [];
  async function open(text) {
    const page = await browser.newPage({ viewport, hasTouch: true });
    const start = blocked.length;
    await page.route('**/*', (route) => {
      blocked.push(route.request().url());
      return route.abort();
    });
    await page.setContent(fixture(text), { waitUntil: 'load', timeout: 15000 });
    const requests = blocked.slice(start);
    const chartVersion = text === source ? '4.4.1' : '4.6.1';
    const expectedUrl = `https://cdn.jsdelivr.net/npm/chart.js@${chartVersion}/dist/chart.umd.min.js`;
    assert(requests.length >= 1 && requests.every((url) => url === expectedUrl));
    return page;
  }
  async function probe(text) {
    const results = {};
    async function run(name, fn) {
      const page = await open(text);
      try {
        const get = async () => Number(await page.locator('#current').innerText());
        const prev = page.locator('.nav-controls button').first();
        const next = page.locator('.nav-controls button').last();
        await next.click();
        assert.equal(await get(), 2);
        results[name] = await fn(page, get, prev, next);
      } finally {
        await page.close();
      }
    }
    await run('previous_space', async (p, get, prev) => {
      await prev.focus();
      await p.keyboard.press('Space');
      return get();
    });
    await run('previous_enter', async (p, get, prev) => {
      await prev.focus();
      await p.keyboard.press('Enter');
      return get();
    });
    await run('previous_click', async (p, get, prev) => {
      await prev.click();
      return get();
    });
    await run('body_space', async (p, get) => {
      await p.evaluate(() => document.activeElement.blur());
      await p.keyboard.press('Space');
      return get();
    });
    await run('body_arrow_left', async (p, get) => {
      await p.evaluate(() => document.activeElement.blur());
      await p.keyboard.press('ArrowLeft');
      return get();
    });
    await run('input_arrow_right', async (p, get) => {
      const e = p.locator('#input');
      await e.focus();
      await e.evaluate((el) => el.setSelectionRange(0, 0));
      await p.keyboard.press('ArrowRight');
      return { slide: await get(), caret: await e.evaluate((el) => el.selectionStart) };
    });
    await run('input_space', async (p, get) => {
      const e = p.locator('#input');
      await e.focus();
      await e.evaluate((el) => el.setSelectionRange(0, 0));
      await p.keyboard.press('Space');
      return { slide: await get(), value: await e.inputValue() };
    });
    await run('textarea_arrow_left', async (p, get) => {
      const e = p.locator('#textarea');
      await e.focus();
      await e.evaluate((el) => el.setSelectionRange(3, 3));
      await p.keyboard.press('ArrowLeft');
      return { slide: await get(), caret: await e.evaluate((el) => el.selectionStart) };
    });
    await run('editable_space', async (p, get) => {
      const e = p.locator('#editable');
      await e.focus();
      await p.keyboard.press('Space');
      return { slide: await get(), text_length: (await e.textContent()).length };
    });
    await run('link_click', async (p, get) => {
      await p.locator('#link').click();
      return get();
    });
    await run('button_click', async (p, get) => {
      await p.locator('#action').click();
      return { slide: await get(), clicked: await p.locator('#action').getAttribute('data-clicked') };
    });
    await run('canvas_click', async (p, get) => {
      await p.locator('#canvas').click();
      return get();
    });
    await run('shadow_input_arrow', async (p, get) => {
      const e = p.locator('#shadow-host input');
      await e.focus();
      await e.evaluate((el) => el.setSelectionRange(0, 0));
      await p.keyboard.press('ArrowRight');
      return { slide: await get(), caret: await e.evaluate((el) => el.selectionStart) };
    });
    await run('shadow_button_click', async (p, get) => {
      const e = p.locator('#shadow-host button');
      await e.click();
      return { slide: await get(), clicked: await e.getAttribute('data-clicked') };
    });
    await run('shadow_button_space', async (p, get) => {
      const e = p.locator('#shadow-host button');
      await e.focus();
      await p.keyboard.press('Space');
      return { slide: await get(), clicked: await e.getAttribute('data-clicked') };
    });
    await run('closed_input_arrow', async (p, get) => {
      await p.evaluate(() => {
        window.closedInput.focus();
        window.closedInput.setSelectionRange(0, 0);
      });
      await p.keyboard.press('ArrowRight');
      return { slide: await get(), caret: await p.evaluate(() => window.closedInput.selectionStart) };
    });
    await run('closed_button_space', async (p, get) => {
      await p.evaluate(() => window.closedButton.focus());
      await p.keyboard.press('Space');
      return { slide: await get(), clicked: await p.evaluate(() => window.closedButton.getAttribute('data-clicked')) };
    });
    await run('closed_button_click', async (p, get) => {
      const point = await p.evaluate(() => {
        const r = window.closedButton.getBoundingClientRect();
        return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
      });
      await p.mouse.click(point.x, point.y);
      return { slide: await get(), clicked: await p.evaluate(() => window.closedButton.getAttribute('data-clicked')) };
    });
    await run('slider_arrow_right', async (p, get) => {
      await p.locator('#slider').focus();
      await p.keyboard.press('ArrowRight');
      return get();
    });
    await run('modified_arrow_right', async (p, get) => {
      await p.evaluate(() => document.activeElement.blur());
      await p.keyboard.press('Control+ArrowRight');
      return get();
    });
    await run('shift_space', async (p, get) => {
      await p.evaluate(() => document.activeElement.blur());
      await p.keyboard.press('Shift+Space');
      return get();
    });
    await run('content_click', async (p, get) => {
      await p.locator('.slide.active h2').click();
      return get();
    });
    await run('background_click', async (p, get) => {
      await p.locator('.slide.active').click({ position: { x: 5, y: 20 } });
      return get();
    });
    await run('background_tap', async (p, get) => {
      await p.locator('.slide.active').tap({ position: { x: 5, y: 20 } });
      return get();
    });
    await run('button_tap', async (p, get) => {
      const e = p.locator('#action');
      await e.tap();
      return { slide: await get(), clicked: await e.getAttribute('data-clicked') };
    });
    await run('prevented_key', async (p, get) => {
      await p.evaluate(() => {
        document.body.addEventListener('keydown', (e) => e.preventDefault(), { once: true });
        document.body.dispatchEvent(
          new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true, cancelable: true }),
        );
      });
      return get();
    });
    await run('composing_key', async (p, get) => {
      await p.evaluate(() =>
        document.body.dispatchEvent(
          new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true, cancelable: true, isComposing: true }),
        ),
      );
      return get();
    });
    await run('nested_editable_key', async (p, get) => {
      await p.locator('#nested').dispatchEvent('keydown', { key: 'ArrowRight', bubbles: true, cancelable: true });
      return get();
    });
    const names = await open(text);
    try {
      results.previous_label = await names.locator('.nav-controls button').first().getAttribute('aria-label');
      results.next_label = await names.locator('.nav-controls button').last().getAttribute('aria-label');
      await names.locator('.nav-controls button').last().click();
      const secondSlide = names.locator('.slide').nth(1);
      results.slide_role = await secondSlide.getAttribute('role');
      results.slide_label = await secondSlide.getAttribute('aria-label');
      results.slide_tabindex = await secondSlide.getAttribute('tabindex');
      results.named_region_count = await names
        .getByRole('region', { name: 'Slide 2: Second slide', exact: true })
        .count();
      const thirdSlide = names.locator('.slide').nth(2);
      results.custom_slide = {
        role: await thirdSlide.getAttribute('role'),
        label: await thirdSlide.getAttribute('aria-label'),
        tabindex: await thirdSlide.getAttribute('tabindex'),
      };
      const fourthSlide = names.locator('.slide').nth(3);
      results.labelled_slide = {
        role: await fourthSlide.getAttribute('role'),
        labelledby: await fourthSlide.getAttribute('aria-labelledby'),
        tabindex: await fourthSlide.getAttribute('tabindex'),
      };
      const status = names.locator('.slide-counter');
      results.status = {
        role: await status.getAttribute('role'),
        live: await status.getAttribute('aria-live'),
        atomic: await status.getAttribute('aria-atomic'),
      };
    } finally {
      await names.close();
    }
    return results;
  }
  try {
    const original = await probe(source);
    const repaired = await probe(candidate);
    const expectedOriginal = {
      previous_space: 3,
      previous_enter: 1,
      previous_click: 1,
      body_space: 3,
      body_arrow_left: 1,
      input_arrow_right: { slide: 3, caret: 0 },
      input_space: { slide: 3, value: 'abcd' },
      textarea_arrow_left: { slide: 1, caret: 3 },
      editable_space: { slide: 3, text_length: 3 },
      link_click: 3,
      button_click: { slide: 3, clicked: 'true' },
      canvas_click: 3,
      shadow_input_arrow: { slide: 3, caret: 0 },
      shadow_button_click: { slide: 3, clicked: '1' },
      shadow_button_space: { slide: 3, clicked: null },
      closed_input_arrow: { slide: 3, caret: 0 },
      closed_button_space: { slide: 3, clicked: null },
      closed_button_click: { slide: 3, clicked: '1' },
      slider_arrow_right: 3,
      modified_arrow_right: 3,
      shift_space: 3,
      content_click: 3,
      background_click: 3,
      background_tap: engine === 'webkit' ? 2 : 3,
      button_tap: { slide: 3, clicked: 'true' },
      prevented_key: 3,
      composing_key: 3,
      nested_editable_key: 3,
      previous_label: null,
      next_label: null,
      slide_role: null,
      slide_label: null,
      slide_tabindex: null,
      named_region_count: 0,
      custom_slide: { role: 'group', label: 'Custom slide', tabindex: '-1' },
      labelled_slide: { role: 'group', labelledby: 'custom-heading', tabindex: '-1' },
      status: { role: null, live: null, atomic: null },
    };
    const expectedRepaired = {
      previous_space: 1,
      previous_enter: 1,
      previous_click: 1,
      body_space: 3,
      body_arrow_left: 1,
      input_arrow_right: { slide: 2, caret: 1 },
      input_space: { slide: 2, value: ' abcd' },
      textarea_arrow_left: { slide: 2, caret: 2 },
      editable_space: { slide: 2, text_length: 4 },
      link_click: 2,
      button_click: { slide: 2, clicked: 'true' },
      canvas_click: 2,
      shadow_input_arrow: { slide: 2, caret: 1 },
      shadow_button_click: { slide: 2, clicked: '1' },
      shadow_button_space: { slide: 2, clicked: '1' },
      closed_input_arrow: { slide: 2, caret: 1 },
      closed_button_space: { slide: 2, clicked: '1' },
      closed_button_click: { slide: 2, clicked: '1' },
      slider_arrow_right: 2,
      modified_arrow_right: 2,
      shift_space: 2,
      content_click: 2,
      background_click: 3,
      background_tap: 3,
      button_tap: { slide: 2, clicked: 'true' },
      prevented_key: 2,
      composing_key: 2,
      nested_editable_key: 2,
      previous_label: 'Previous slide',
      next_label: 'Next slide',
      slide_role: 'region',
      slide_label: 'Slide 2: Second slide',
      slide_tabindex: '0',
      named_region_count: 1,
      custom_slide: { role: 'group', label: 'Custom slide', tabindex: '-1' },
      labelled_slide: { role: 'group', labelledby: 'custom-heading', tabindex: '-1' },
      status: { role: 'status', live: 'polite', atomic: 'true' },
    };
    assert.deepEqual(original, expectedOriginal);
    assert.deepEqual(repaired, expectedRepaired);
    const focusPage = await open(candidate);
    const tabOrder = [];
    try {
      for (let i = 0; i < 3; i += 1) {
        await focusPage.keyboard.press('Tab');
        tabOrder.push(await focusPage.evaluate(() => document.activeElement.getAttribute('aria-label')));
      }
    } finally {
      await focusPage.close();
    }
    assert.deepEqual(tabOrder, ['Slide 1: Title Slide', 'Previous slide', 'Next slide']);
    assert(blocked.length >= 59);
    console.log(
      JSON.stringify(
        {
          source_sha256: sha(source),
          candidate_sha256: sha(candidate),
          source_fixture_sha256: sha(fixture(source)),
          candidate_fixture_sha256: sha(fixture(candidate)),
          node_version: process.version,
          playwright_version: playwrightVersion,
          platform: process.platform,
          architecture: process.arch,
          browser_engine: engine,
          browser_version: browser.version(),
          viewport,
          touch_enabled: true,
          blocked_chart_requests: blocked.length,
          tab_order: tabOrder,
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
