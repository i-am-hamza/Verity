#!/usr/bin/env node
/**
 * Session 10 presentation pass: Sensitivity + Methodology pages at the
 * two required widths (390 phone, 1440 desktop) in both themes. Writes
 * to screenshots/reports/<theme>/<width>-<page>.png so these don't
 * stomp the Session 8 captures.
 */
import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = join(__dirname, "..", "screenshots", "reports");
const BASE = process.env.VERITY_BASE_URL || "http://localhost:5173";

const PAGES = [
  { name: "sensitivity", path: "/sensitivity" },
  { name: "methodology", path: "/methodology" },
];

const VIEWPORTS = [
  { label: "mobile-390", width: 390, height: 844 },
  { label: "desktop-1440", width: 1440, height: 900 },
];

const THEMES = ["dark", "light"];

async function run() {
  const browser = await chromium.launch();
  const captured = [];
  try {
    for (const theme of THEMES) {
      for (const vp of VIEWPORTS) {
        const ctx = await browser.newContext({
          viewport: { width: vp.width, height: vp.height },
          deviceScaleFactor: 1,
        });
        await ctx.addInitScript((t) => {
          try { window.localStorage.setItem("verity.theme", t); } catch (_) {}
        }, theme);
        const page = await ctx.newPage();
        const dir = join(OUT, theme);
        await mkdir(dir, { recursive: true });
        for (const p of PAGES) {
          const url = `${BASE}${p.path}`;
          try {
            await page.goto(url, { waitUntil: "networkidle", timeout: 45000 });
          } catch (_) {
            await page.goto(url, { waitUntil: "load", timeout: 45000 });
          }
          // Give Recharts a beat to paint; sensitivity has a scatter.
          await page.waitForTimeout(1200);
          const file = join(dir, `${vp.label}-${p.name}.png`);
          await page.screenshot({ path: file, fullPage: true });
          captured.push(file);
          process.stdout.write(".");
        }
        await ctx.close();
      }
    }
    process.stdout.write("\n");
    console.log(`captured ${captured.length} -> ${OUT}`);
  } finally {
    await browser.close();
  }
}

run().catch((err) => { console.error(err); process.exit(1); });
