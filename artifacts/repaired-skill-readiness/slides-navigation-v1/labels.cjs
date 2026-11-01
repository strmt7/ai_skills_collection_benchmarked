const fs = require('node:fs');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const playwright = require(process.argv[2]);
const engine = process.argv[5] || 'chromium';
const source = fs.readFileSync(process.argv[3], 'utf8').replace(/\r\n/g, '\n');
const candidate = fs.readFileSync(process.argv[4], 'utf8').replace(/\r\n/g, '\n');
const sha = (data) => crypto.createHash('sha256').update(data).digest('hex');
assert.equal(sha(source), 'fd5b051a37365fc6059c75bb388ec6f64daf1bd9ae938b287b6d762dc83c0c35');
assert.equal(sha(candidate), '0ed28b587e769cd036f1f1e46f31dee7f9149c263ea8be8c95d4e51f3e1d908d');
assert.equal(require(`${process.argv[2]}/package.json`).version, '1.64.1');
assert(['chromium', 'firefox', 'webkit'].includes(engine));
const placeholder = '<!-- More slides... (always wrap content in .slide-content) -->';
const slides = `<div class="slide" id="no-heading"><div class="slide-content"><p>Text</p></div></div>
<div class="slide" id="blank-heading"><div class="slide-content"><h2>   </h2></div></div>
<div class="slide" id="custom" role="group" aria-label="Custom label" tabindex="-1"><div class="slide-content"><h2>Custom</h2></div></div>
<div class="slide" id="referenced" role="group" aria-labelledby="custom-title" tabindex="-1"><div class="slide-content"><h2 id="custom-title">Referenced</h2></div></div>`;
function fixture(text) {
  const match = text.match(/```html\n([\s\S]*?)\n```/);
  assert(match && match[1].split(placeholder).length === 2);
  return match[1].replace(placeholder, slides + '\n' + placeholder);
}
(async () => {
  const browser = await playwright[engine].launch({ headless: true });
  async function probe(text) {
    const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
    const blocked = [];
    await page.route('**/*', (route) => {
      blocked.push(route.request().url());
      return route.abort();
    });
    try {
      await page.setContent(fixture(text), { waitUntil: 'load', timeout: 15000 });
      const version = text === source ? '4.4.1' : '4.6.1';
      assert(
        blocked.length >= 1 &&
          blocked.every((url) => url === `https://cdn.jsdelivr.net/npm/chart.js@${version}/dist/chart.umd.min.js`),
      );
      const attributes = async (selector) =>
        page
          .locator(selector)
          .evaluate((el) => ({
            role: el.getAttribute('role'),
            label: el.getAttribute('aria-label'),
            labelledby: el.getAttribute('aria-labelledby'),
            tabindex: el.getAttribute('tabindex'),
          }));
      const first = await attributes('.slide.active');
      const noHeading = await attributes('#no-heading');
      const blankHeading = await attributes('#blank-heading');
      const custom = await attributes('#custom');
      const referenced = await attributes('#referenced');
      await page.locator('.nav-controls button').last().click();
      const namedRegion = await page.getByRole('region', { name: 'Slide 2 of 5', exact: true }).count();
      return {
        first,
        no_heading: noHeading,
        blank_heading: blankHeading,
        custom,
        referenced,
        named_region_count: namedRegion,
      };
    } finally {
      await page.close();
    }
  }
  try {
    const original = await probe(source);
    const repaired = await probe(candidate);
    const empty = { role: null, label: null, labelledby: null, tabindex: null };
    const custom = { role: 'group', label: 'Custom label', labelledby: null, tabindex: '-1' };
    const referenced = { role: 'group', label: null, labelledby: 'custom-title', tabindex: '-1' };
    assert.deepEqual(original, {
      first: empty,
      no_heading: empty,
      blank_heading: empty,
      custom,
      referenced,
      named_region_count: 0,
    });
    assert.deepEqual(repaired, {
      first: { role: 'region', label: 'Slide 1: Title Slide', labelledby: null, tabindex: '0' },
      no_heading: { role: 'region', label: 'Slide 2 of 5', labelledby: null, tabindex: '0' },
      blank_heading: { role: 'region', label: 'Slide 3 of 5', labelledby: null, tabindex: '0' },
      custom,
      referenced,
      named_region_count: 1,
    });
    console.log(
      JSON.stringify(
        {
          source_sha256: sha(source),
          candidate_sha256: sha(candidate),
          source_fixture_sha256: sha(fixture(source)),
          candidate_fixture_sha256: sha(fixture(candidate)),
          node_version: process.version,
          playwright_version: '1.64.1',
          platform: process.platform,
          architecture: process.arch,
          browser_engine: engine,
          browser_version: browser.version(),
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
