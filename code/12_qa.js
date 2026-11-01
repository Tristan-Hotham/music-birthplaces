// QA: open index.html at desktop (1280) and phone (390) widths, record console errors, take screenshots to qa/.
// Run from the repo root with a static server on :8818 (python3 -m http.server 8818).
const { chromium } = require("playwright");
const path = require("path");
const OUT = path.join(__dirname, "..", "qa");
// Leaflet is served from a local npm copy (the CDN is not reachable from the build machine); tiles and fonts are skipped.
const LEAF = process.env.LEAFLET_DIST || "/tmp/claude-0/-home-claude/9791f396-0812-550b-8fd1-2ad33918f115/scratchpad/node_modules/leaflet/dist";
(async () => {
  require("fs").mkdirSync(OUT, { recursive: true });
  const b = await chromium.launch();
  for (const [name, w, h] of [["desktop", 1280, 900], ["phone", 390, 844]]) {
    const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    await p.route(/arcgisonline|googleapis|gstatic/, r => r.abort());
    await p.route(/leaflet.min.js/, r => r.fulfill({ path: LEAF + "/leaflet.js" }));
    await p.route(/leaflet.min.css/, r => r.fulfill({ path: LEAF + "/leaflet.css" }));
    const errs = [];
    p.on("console", m => { if (m.type() === "error" && !/arcgisonline|net::ERR|Failed to load resource/.test(m.text())) errs.push(m.text()); });
    p.on("pageerror", e => errs.push("pageerror " + e.message));
    await p.goto("http://localhost:" + (process.env.QA_PORT || 8818) + "/index.html", { waitUntil: "networkidle", timeout: 90000 }).catch(() => {});
    await p.waitForFunction(() => window.READY === true, null, { timeout: 60000 }).catch(() => errs.push("data did not load"));
    await p.waitForTimeout(800);
    await p.screenshot({ path: `${OUT}/${name}_top.png` });
    const at = async (sel, file) => { const e = await p.$(sel); if (e) { await e.scrollIntoViewIfNeeded(); await p.waitForTimeout(500); await e.screenshot({ path: `${OUT}/${name}_${file}.png` }); } };
    await at("#atlas", "map_all");
    await p.evaluate(() => setDec(1810)); await p.waitForTimeout(500); await at("#atlas", "map_1810");
    await p.evaluate(() => { setDec(null); setGen(4); }); await p.waitForTimeout(500); await at("#atlas", "map_eapop");
    await p.evaluate(() => { setGen(-1); setKind(1); }); await p.waitForTimeout(500); await at("#atlas", "map_bands");
    await p.evaluate(() => { setGen(2); map.fitBounds([[54.5, 4], [71, 32]]); }); await p.waitForTimeout(900); await at("#atlas", "map_metal_nordic");
    await p.evaluate(() => { setGen(-1); setKind(0); });
    // search a musician
    const o = await p.evaluate(async () => (await searchFor("Beethoven")).map(x => x.n).slice(0, 4));
    console.log(name, "search Beethoven:", JSON.stringify(o));
    await at(".searchbox", "search");
    await p.keyboard.press("Enter").catch(() => {});
    await p.focus("#q"); await p.keyboard.press("Enter"); await p.waitForTimeout(1500); await at("#atlas", "act");
    // click a hexagon at Vienna at a regional zoom
    await p.evaluate(() => { clearSel(); map.setView([48.2, 16.37], 5); }); await p.waitForTimeout(1200);
    const box = await p.$("#map"); const bb = await box.boundingBox();
    await p.mouse.click(bb.x + bb.width / 2, bb.y + bb.height / 2); await p.waitForTimeout(1500); await at("#atlas", "hex");
    const sideTxt = await p.$eval("#side", e => e.innerText.slice(0, 300)); console.log(name, "hex side:", JSON.stringify(sideTxt));
    // zoomed-in place circles at Nashville
    await p.evaluate(() => { clearSel(); map.setView([36.16, -86.78], 8); }); await p.waitForTimeout(1200); await at("#atlas", "dots");
    await p.click(".lyrBtn"); await p.waitForTimeout(300); await at("#map", "layers"); await p.click(".lyrBtn");
    await p.evaluate(() => { LY.shade = true; LY.shadeBy = "pm"; applyLayers(); map.setView([50, 10], 3); }); await p.waitForTimeout(800); await at("#atlas", "shade");
    await p.evaluate(() => { LY.shade = false; LY.shadeBy = "n"; applyLayers(); });
    for (const id of ["cityChart", "famChart", "conChart", "sigTable", "lqChart", "bpmChart", "stackChart", "riseChart", "womenChart", "wfChart", "ctyChart", "ukTable", "covChart"]) await at("#" + id, id);
    await p.click("#theme"); await p.waitForTimeout(800); await at("#atlas", "dark");
    await p.click("#theme");
    const over = await p.evaluate(() => document.documentElement.scrollWidth - innerWidth);
    console.log(name, "errors:", JSON.stringify(errs), "horizontal overflow:", over);
    await p.close();
  }
  await b.close();
})();
