import { create } from "zustand";

export type ThemeMode = "dark" | "light";

interface ThemeState {
  theme: ThemeMode;
  setTheme: (next: ThemeMode) => void;
  toggle: () => void;
}

const STORAGE_KEY = "verity.theme";

function readInitialTheme(): ThemeMode {
  // Wrapped in try/catch because localStorage can throw in private mode or
  // sandboxed iframes; falling back to prefers-color-scheme is fine.
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored === "dark" || stored === "light") {
      return stored;
    }
  } catch {
    // ignore
  }
  if (
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    !window.matchMedia("(prefers-color-scheme: dark)").matches
  ) {
    return "light";
  }
  return "dark";
}

function persistTheme(next: ThemeMode): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, next);
  } catch {
    // ignore
  }
}

function applyThemeClass(next: ThemeMode): void {
  // Synchronously swap <html>'s class so there's zero gap between the
  // state update and the paint. Doing this inside a Zustand subscription
  // (rather than React useEffect) sidesteps StrictMode double-render +
  // effect ordering and makes the toggle testable from the console too.
  if (typeof document === "undefined") return;
  const el = document.documentElement;
  el.classList.remove("theme-dark", "theme-light");
  el.classList.add(`theme-${next}`);
}

export const useTheme = create<ThemeState>((set, get) => ({
  theme: readInitialTheme(),
  setTheme: (next) => {
    persistTheme(next);
    applyThemeClass(next);
    set({ theme: next });
  },
  toggle: () => {
    const next: ThemeMode = get().theme === "dark" ? "light" : "dark";
    console.info("[verity.theme] toggle ->", next);
    persistTheme(next);
    applyThemeClass(next);
    set({ theme: next });
  },
}));

// Ensure the class is in sync with the initial state at module load —
// paired with the pre-boot inline script in index.html as a safety net.
applyThemeClass(useTheme.getState().theme);

if (typeof window !== "undefined") {
  // Expose for one-shot console debugging: `__verityTheme.set('light')`.
  (window as unknown as { __verityTheme?: typeof useTheme }).__verityTheme =
    useTheme;
}
