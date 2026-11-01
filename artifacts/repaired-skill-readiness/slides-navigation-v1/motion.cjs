const fs = require('node:fs');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const playwright = require(process.argv[2]);
const engine = process.argv[5];
const hash = (value) => crypto.createHash('sha256').update(value).digest('hex');
const source = fs.readFileSync(process.argv[3], 'utf8').replace(/\r\n/g, '\n');
const candidate = fs.readFileSync(process.argv[4], 'utf8').replace(/\r\n/g, '\n');
assert.equal(hash(source), 'fd5b051a37365fc6059c75bb388ec6f64daf1bd9ae938b287b6d762dc83c0c35');
assert.equal(hash(candidate), '0ed28b587e769cd036f1f1e46f31dee7f9149c263ea8be8c95d4e51f3e1d908d');
assert.equal(require(`${process.argv[2]}/package.json`).version, '1.64.1');
assert(['chromium', 'firefox', 'webkit'].includes(engine));
function fixture(text) {
  const html = text.match(/```html\n([\s\S]*?)\n```/);
  const css = text.match(/```css\n([\s\S]*?)\n```/);
  assert(html && css);
  const anchor = '<p>Subtitle or tagline</p>';
  assert.equal(html[1].split(anchor).length, 2);
  return html[1]
    .replace('</style>', `${css[1]}\n</style>`)
    .replace(anchor, `${anchor}<p id="fade" class="animate-fade-up">Fade</p><p id="scale" class="animate-scale">Scale</p><p id="count" class="animate-count">Count</p><div class="animate-stagger"><p id="stagger">Stagger</p></div>`);
}
(async () => {
  const browser = await playwright[engine].launch({ headless: true });
  async function probe(text, reducedMotion) {
    const page = await browser.newPage({ reducedMotion, viewport: { width: 1280, height: 720 } });
    let blocked = 0;
    await page.route('**/*', (route) => { blocked += 1; return route.abort(); });
    try {
      await page.setContent(fixture(text), { waitUntil: 'load', timeout: 15000 });
      assert(blocked >= 1);
      return await page.evaluate(() => {
        const style = (selector) => {
          const computed = getComputedStyle(document.querySelector(selector));
          return { transition: computed.transitionDuration, animation: computed.animationName, opacity: computed.opacity };
        };
        return { slide: style('.slide'), progress: style('.progress-bar'), fade: style('#fade'), scale: style('#scale'), count: style('#count'), stagger: style('#stagger') };
      });
    } finally { await page.close(); }
  }
  try {
    const results = {};
    for (const [name, text] of [['original', source], ['repaired', candidate]]) {
      results[name] = {};
      for (const preference of ['no-preference', 'reduce']) results[name][preference] = await probe(text, preference);
    }
    for (const name of ['original', 'repaired']) {
      for (const preference of ['no-preference', ...(name === 'original' ? ['reduce'] : [])]) {
        const r = results[name][preference];
        assert.notEqual(r.slide.transition, '0s');
        assert.notEqual(r.progress.transition, '0s');
        assert.equal(r.fade.animation, 'fadeUp');
        assert.equal(r.scale.animation, 'scaleIn');
        assert.equal(r.count.animation, 'countUp');
        assert.equal(r.stagger.animation, 'fadeUp');
      }
    }
    const reduced = results.repaired.reduce;
    assert.equal(reduced.slide.transition, '0s');
    assert.equal(reduced.progress.transition, '0s');
    for (const key of ['fade', 'scale', 'count', 'stagger']) {
      assert.equal(reduced[key].animation, 'none');
      assert.equal(reduced[key].opacity, '1');
    }
    console.log(JSON.stringify({ source_sha256: hash(source), candidate_sha256: hash(candidate), source_fixture_sha256: hash(fixture(source)), candidate_fixture_sha256: hash(fixture(candidate)), node: process.version, platform: process.platform, arch: process.arch, browser_engine: engine, browser_version: browser.version(), playwright_version: '1.64.1', full_accessibility_audit: false, agent_performance_tested: false, results }, null, 2));
  } finally { await browser.close(); }
})().catch((error) => { console.error(error); process.exitCode = 1; });
