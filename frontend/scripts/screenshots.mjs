#!/usr/bin/env node
/**
 * Session 8 verification: real Playwright screenshots of every dashboard
 * page at phone (390) and desktop (1440) widths, in both themes. Writes
 * PNGs to screenshots/<theme>/<viewport>/<page>.png. Session 7 deferred
 * this; closing it here.
 */
import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = join(__dirname, "..", "screenshots");

const BASE = process.env.VERITY_BASE_URL || "http://localhost:5173";

const PAGES = [
  { name: "overview", path: "/" },
  { name: "coverage", path: "/coverage" },
  { name: "evidence", path: "/evidence" },
  { name: "sensitivity", path: "/sensitivity" },
  { name: "benchmark", path: "/benchmark" },
  { name: "taxonomy", path: "/taxonomy" },
  { name: "methodology", path: "/methodology" },
  // Pick a known-scored institution so the detail page actually has data.
  { name: "institution", path: "/institution/qnb-qatar-national-bank" },
];

const VIEWPORTS = [
  { label: "mobile-390", width: 390, height: 844 },
  { label: "desktop-1440", width: 1440, height: 900 },
];

const THEMES = ["dark", "light"];

async function ensureDir(p) {
  await mkdir(p, { recursive: true });
}

async function run() {
  const browser = await chromium.launch();
  const captured = [];
  try {
    for (const theme of THEMES) {
      for (const vp of VIEWPORTS) {
        const context = await browser.newContext({
          viewport: { width: vp.width, height: vp.height },
          deviceScaleFactor: 2,
        });
        // Seed localStorage before any page loads so the pre-boot script
        // in index.html picks up the chosen theme.
        await context.addInitScript((t) => {
          try {
            window.localStorage.setItem("verity.theme", t);
          } catch (_) {
            // ignore
          }
        }, theme);
        const page = await context.newPage();
        const dir = join(OUT, theme, vp.label);
        await ensureDir(dir);
        for (const p of PAGES) {
          const url = `${BASE}${p.path}`;
          try {
            await page.goto(url, { waitUntil: "networkidle", timeout: 30000 });
          } catch (err) {
            // Networkidle can time out on routes with long-polling; fall
            // back to the softer "load" event so we still get a shot.
            await page.goto(url, { waitUntil: "load", timeout: 30000 });
          }
          // Give charts a beat to settle; Recharts animates on mount.
          await page.waitForTimeout(600);
          const file = join(dir, `${p.name}.png`);
          await page.screenshot({ path: file, fullPage: true });
          captured.push(file);
          process.stdout.write(`.`);
        }
        await context.close();
      }
    }
    process.stdout.write("\n");
    console.log(`captured ${captured.length} screenshots -> ${OUT}`);
  } finally {
    await browser.close();
  }
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
