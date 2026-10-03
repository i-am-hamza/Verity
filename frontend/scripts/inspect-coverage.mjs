#!/usr/bin/env node
/**
 * Spot-check: at each viewport, measure the actual rendered pixel width
 * of the table, the overflow-x container, and the first few th cells.
 * Confirms whether horizontal scroll is active below 800 and whether
 * the table fills the container above it.
 */
import { chromium } from "playwright";

const BASE = process.env.VERITY_BASE_URL || "http://localhost:5173";
const WIDTHS = [390, 640, 760, 790, 810, 1024, 1440];

const browser = await chromium.launch();
try {
  for (const w of WIDTHS) {
    const ctx = await browser.newContext({ viewport: { width: w, height: 900 } });
    const page = await ctx.newPage();
    try {
      await page.goto(`${BASE}/coverage`, { waitUntil: "networkidle", timeout: 30000 });
    } catch (_) {
      await page.goto(`${BASE}/coverage`, { waitUntil: "load", timeout: 30000 });
    }
    await page.waitForTimeout(800);
    const data = await page.evaluate(() => {
      const main = document.querySelector("main");
      const container = document.querySelector("main .relative.rounded-md");
      const scroller = container?.querySelector(".overflow-x-auto, .min-\\[800px\\]\\:overflow-visible");
      const table = scroller?.querySelector("table");
      const headRow = table?.querySelector("thead tr");
      const ths = headRow ? [...headRow.querySelectorAll("th")] : [];
      return {
        viewport: window.innerWidth,
        mainW: main?.getBoundingClientRect().width ?? null,
        containerW: container?.getBoundingClientRect().width ?? null,
        scrollerClientW: scroller?.clientWidth ?? null,
        scrollerScrollW: scroller?.scrollWidth ?? null,
        tableW: table?.getBoundingClientRect().width ?? null,
        thWidths: ths.map((e) => Math.round(e.getBoundingClientRect().width)),
      };
    });
    const overflows = data.scrollerScrollW != null && data.scrollerClientW != null
      && data.scrollerScrollW > data.scrollerClientW + 1;
    const slack = data.containerW != null && data.tableW != null
      ? Math.round(data.containerW - data.tableW)
      : null;
    console.log(
      `w=${w}  main=${Math.round(data.mainW ?? 0)}  cont=${Math.round(data.containerW ?? 0)}  ` +
      `tbl=${Math.round(data.tableW ?? 0)}  slack=${slack}  ` +
      `scroll=${overflows ? "YES" : "no"} (${data.scrollerClientW}/${data.scrollerScrollW})  ` +
      `ths=${JSON.stringify(data.thWidths)}`,
    );
    await ctx.close();
  }
} finally {
  await browser.close();
}
