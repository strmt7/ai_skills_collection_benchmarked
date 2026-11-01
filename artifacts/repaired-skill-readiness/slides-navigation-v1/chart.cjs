const fs = require('node:fs');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const playwright = require(process.argv[2]);
const version = process.argv[4];
const engine = process.argv[7] || 'chromium';
const layout = process.argv[9] || 'desktop';
if (!['desktop', 'narrow', 'landscape'].includes(layout)) throw new Error('Unsupported viewport');
const viewport =
  layout === 'narrow'
    ? { width: 390, height: 844 }
    : layout === 'landscape'
      ? { width: 844, height: 390 }
      : { width: 1280, height: 720 };
const reference = fs.readFileSync(process.argv[3], 'utf8').replace(/\r\n/g, '\n');
const bundle = fs.readFileSync(process.argv[5]);
const digest = (data) => crypto.createHash('sha256').update(data).digest('hex');
const expected = {
  '4.4.1': 'd2af8974e95271638772e9e9524db5b9a6f58d6ec2d5d781400447b4a31c681e',
  '4.6.1': '87364cc2b2a76a6684929e7d6b80b18a897794db38400caff1fcf1791c6925d2',
};
assert(
  [
    'fd5b051a37365fc6059c75bb388ec6f64daf1bd9ae938b287b6d762dc83c0c35',
    '0ed28b587e769cd036f1f1e46f31dee7f9149c263ea8be8c95d4e51f3e1d908d',
  ].includes(digest(reference)),
);
assert(expected[version]);
assert.equal(digest(bundle), expected[version]);
assert.equal(require(`${process.argv[2]}/package.json`).version, '1.64.1');
const blocks = [...reference.matchAll(/```html\n([\s\S]*?)\n```/g)].map((match) => match[1]);
assert(blocks.length >= 2);
const url = `https://cdn.jsdelivr.net/npm/chart.js@${version}/dist/chart.umd.min.js`;
let html = blocks[0];
if (html.includes('chart.js@4.4.1/')) {
  assert.equal(html.split('chart.js@4.4.1/').length, 2);
  html = html.replace('chart.js@4.4.1/', `chart.js@${version}/`);
} else {
  assert.equal(version, '4.6.1');
  assert.equal(html.split('chart.js@4.6.1/').length, 2);
}
const anchor = '<p>Subtitle or tagline</p>';
assert.equal(html.split(anchor).length, 2);
html = html.replace(anchor, `${anchor}\n${blocks[1]}`);
(async () => {
  const options = { headless: true };
  if (process.argv[6] !== 'playwright-default') options.executablePath = process.argv[6];
  const browser = await playwright[engine].launch(options);
  try {
    const page = await browser.newPage({ viewport });
    let served = 0;
    const unexpected = [];
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await page.route('**/*', (route) => {
      if (route.request().url() === url) {
        served += 1;
        return route.fulfill({ status: 200, contentType: 'application/javascript', body: bundle });
      }
      unexpected.push(route.request().url());
      return route.abort();
    });
    await page.setContent(html, { waitUntil: 'load', timeout: 15000 });
    await page.waitForFunction(
      () => {
        const chart = window.Chart && Chart.getChart('revenueChart');
        if (!chart || !chart.canvas.width || !chart.canvas.height) return false;
        const points = chart.getDatasetMeta(0).data;
        const values = chart.data.datasets[0].data;
        if (
          points.length !== values.length ||
          !points.every((point, i) => Math.abs(point.y - chart.scales.y.getPixelForValue(values[i])) < 0.5)
        )
          return false;
        const pixels = chart.canvas.getContext('2d').getImageData(0, 0, chart.canvas.width, chart.canvas.height).data;
        for (let i = 3; i < pixels.length; i += 4) if (pixels[i]) return true;
        return false;
      },
      null,
      { timeout: 8000 },
    );
    const result = await page.evaluate(() => {
      const chart = Chart.getChart('revenueChart');
      if (!chart) throw new Error('Chart was not created');
      const canvas = chart.canvas;
      const pixels = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height).data;
      let nontransparent = 0;
      for (let i = 3; i < pixels.length; i += 4) if (pixels[i]) nontransparent += 1;
      const values = chart.data.datasets[0].data;
      const maxPixelError = Math.max(
        ...chart
          .getDatasetMeta(0)
          .data.map((point, i) => Math.abs(point.y - chart.scales.y.getPixelForValue(values[i]))),
      );
      const bounds = (element) => {
        const r = element.getBoundingClientRect();
        return { left: r.left, top: r.top, right: r.right, bottom: r.bottom };
      };
      const chartBounds = bounds(canvas);
      const navBounds = bounds(document.querySelector('.nav-controls'));
      const contentBounds = bounds(document.querySelector('.slide.active .slide-content'));
      const slideBounds = bounds(document.querySelector('.slide.active'));
      const overlap =
        Math.max(0, Math.min(chartBounds.right, navBounds.right) - Math.max(chartBounds.left, navBounds.left)) *
        Math.max(0, Math.min(chartBounds.bottom, navBounds.bottom) - Math.max(chartBounds.top, navBounds.top));
      return {
        version: Chart.version,
        type: chart.config.type,
        labels: chart.data.labels,
        values,
        width: canvas.width,
        height: canvas.height,
        nontransparent,
        max_pixel_error: maxPixelError,
        chart_bounds: chartBounds,
        navigation_bounds: navBounds,
        content_bounds: contentBounds,
        slide_bounds: slideBounds,
        chart_navigation_overlap_area: overlap,
      };
    });
    assert.equal(result.version, version);
    assert.equal(result.type, 'line');
    assert.deepEqual(result.labels, ['Sep', 'Oct', 'Nov', 'Dec']);
    assert.deepEqual(result.values, [5, 12, 28, 45]);
    assert(result.width > 0 && result.height > 0 && result.nontransparent > 0 && result.max_pixel_error < 0.5);
    assert(served >= 1);
    assert.deepEqual(unexpected, []);
    assert.deepEqual(errors, []);
    if (layout !== 'landscape') {
      assert.equal(result.chart_navigation_overlap_area, 0, 'Chart overlaps navigation in a normal viewport');
    }
    if (layout === 'landscape') {
      const before = await page
        .locator('.slide.active')
        .evaluate((el) => ({ client: el.clientHeight, scroll: el.scrollHeight, top: el.scrollTop }));
      assert(before.scroll > before.client, 'The short slide should be scrollable');
      await page.locator('.slide.active').focus();
      await page.keyboard.press('ArrowDown');
      await page.waitForFunction(() => document.querySelector('.slide.active').scrollTop > 0, null, { timeout: 3000 });
      await page.locator('.slide.active').evaluate((el) => {
        el.scrollTop = el.scrollHeight;
      });
      const visible = await page.evaluate(() => {
        const chart = document.querySelector('#revenueChart').getBoundingClientRect();
        const nav = document.querySelector('.nav-controls').getBoundingClientRect();
        const slide = document.querySelector('.slide.active').getBoundingClientRect();
        return {
          chart_bottom: chart.bottom,
          navigation_top: nav.top,
          slide_bottom: slide.bottom,
          scroll_top: document.querySelector('.slide.active').scrollTop,
        };
      });
      assert(
        visible.chart_bottom <= visible.navigation_top + 1 && visible.chart_bottom <= visible.slide_bottom + 1,
        `Chart remains obscured after scrolling: ${JSON.stringify(visible)}`,
      );
      result.scroll_control = { before, visible };
    }
    if (process.argv[8] && process.argv[8] !== '-') await page.screenshot({ path: process.argv[8] });
    console.log(
      JSON.stringify(
        {
          source_sha256: digest(reference),
          fixture_sha256: digest(html),
          bundle_sha256: digest(bundle),
          node_version: process.version,
          playwright_version: '1.64.1',
          platform: process.platform,
          architecture: process.arch,
          browser_engine: engine,
          browser_version: browser.version(),
          viewport,
          served_requests: served,
          unexpected_requests: unexpected,
          page_errors: errors,
          chart: result,
          interactive_chart_behavior_tested: false,
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
