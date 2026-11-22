// Rendu PNG fidèle (filtres SVG compris) via Chromium.
// Usage : node render_svg.js <width> <in.svg> <out.png> [<in.svg> <out.png> ...]
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [width, ...pairs] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: 1 });
  for (let i = 0; i < pairs.length; i += 2) {
    const svg = fs.readFileSync(pairs[i], 'utf8');
    const m = svg.match(/viewBox="([\d.\s-]+)"/);
    const [, , vw, vh] = m[1].trim().split(/\s+/).map(Number);
    const w = Number(width), h = Math.round(w * vh / vw);
    await page.setViewportSize({ width: w, height: h });
    const sized = svg.replace(/<svg([^>]*?) width="[^"]*" height="[^"]*"/, `<svg$1 width="${w}" height="${h}"`);
    await page.setContent(`<html><body style="margin:0;background:transparent">${sized}</body></html>`);
    await page.screenshot({ path: pairs[i + 1], omitBackground: true, clip: { x: 0, y: 0, width: w, height: h } });
  }
  await browser.close();
})();
