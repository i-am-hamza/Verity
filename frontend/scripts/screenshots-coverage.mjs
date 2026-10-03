#!/usr/bin/env node
/**
 * Coverage-page-only screenshots for the Session 10 above-breakpoint
 * fix. Captures the Coverage page at 390 px (phone), 790 px (just
 * below the 800 px breakpoint — scroll + sticky column must still be
 * there), 810 px (just above — table should start filling), and
 * 1440 px (desktop — table should span the full width with no gap),
 * in both dark and light themes.
 *
 * Writes PNGs to screenshots/coverage-fix/<theme>/<width>.png so the
 * existing Session 8 captures aren't overwritten.
 */
import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = join(__dirname, "..", "screenshots", "coverage-fix");
const BASE = process.env.VERITY_BASE_URL || "http://localhost:5173";

const VIEWPORTS = [
  { width: 390, height: 844 },   // phone — must not regress
  { width: 790, height: 900 },   // just below breakpoint — scroll + sticky still active
  { width: 810, height: 900 },   // just above breakpoint — fill mode kicks in
  { width: 1024, height: 900 },  // lg sanity
  { width: 1440, height: 900 },  // desktop — the "no empty gap" test
];

const THEMES = ["dark", "light"];

async function run() {
  const browser = await chromium.launch();
  const captured = [];
  try {
    for (const theme of THEMES) {
      for (const vp of VIEWPORTS) {
        const context = await browser.newContext({
          viewport: { width: vp.width, height: vp.height },
          deviceScaleFactor: 1,
        });
        await context.addInitScript((t) => {
          try { window.localStorage.setItem("verity.theme", t); } catch (_) {}
        }, theme);
        const page = await context.newPage();
        const dir = join(OUT, theme);
        await mkdir(dir, { recursive: true });
        const url = `${BASE}/coverage`;
        try {
          await page.goto(url, { waitUntil: "networkidle", timeout: 30000 });
        } catch (_) {
          await page.goto(url, { waitUntil: "load", timeout: 30000 });
        }
        // The coverage table lazy-fetches; give the network a moment.
        await page.waitForTimeout(1200);
        const file = join(dir, `${vp.width}.png`);
        // fullPage so the whole matrix is captured. We care about the
        // table width filling the container above the breakpoint and
        // the horizontal scroll + sticky column below it.
        await page.screenshot({ path: file, fullPage: true });
        captured.push(file);
        process.stdout.write(".");
        await context.close();
      }
    }
    process.stdout.write("\n");
    console.log(`captured ${captured.length} coverage screenshots -> ${OUT}`);
  } finally {
    await browser.close();
  }
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
