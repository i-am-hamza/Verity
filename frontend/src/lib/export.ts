/**
 * Chart + table export helpers. Every chart/table on the dashboard binds
 * these so there's exactly one PNG and one CSV path per view.
 */
import { toPng } from "html-to-image";

export async function exportElementAsPng(
  node: HTMLElement,
  filename: string,
): Promise<void> {
  // Pin the surface colour so the PNG doesn't come out transparent on
  // dark theme (default canvas background is white).
  const bg = getComputedStyle(document.body).backgroundColor;
  const dataUrl = await toPng(node, {
    cacheBust: true,
    pixelRatio: 2,
    backgroundColor: bg,
  });
  const a = document.createElement("a");
  a.href = dataUrl;
  a.download = filename;
  a.click();
}

export function exportRowsAsCsv(
  rows: readonly Record<string, string | number | null>[],
  filename: string,
  header?: string,
): void {
  if (rows.length === 0) {
    // Still emit the file so the caller gets feedback — a 0-row CSV with
    // just the header is more useful than nothing happening.
  }
  const keys = Object.keys(rows[0] ?? {});
  const esc = (v: string | number | null): string => {
    if (v === null || v === undefined) return "";
    const s = String(v);
    if (s.includes(",") || s.includes('"') || s.includes("\n")) {
      return `"${s.replace(/"/g, '""')}"`;
    }
    return s;
  };
  const parts: string[] = [];
  if (header) parts.push(header);
  parts.push(keys.join(","));
  for (const row of rows) parts.push(keys.map((k) => esc(row[k] ?? "")).join(","));
  const blob = new Blob([parts.join("\n")], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
