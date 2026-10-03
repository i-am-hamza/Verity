import { useCallback } from "react";
import { useSearchParams } from "react-router-dom";

/**
 * Lightweight URL-state helper so filter values survive refresh / back /
 * forward and views stay shareable. Zustand holds UI-only state (open menus,
 * local sorts); anything the server renders off of goes through here.
 */
export function useUrlState<T extends string>(
  key: string,
  fallback: T,
): [T, (next: T) => void] {
  const [params, setParams] = useSearchParams();
  const current = (params.get(key) ?? fallback) as T;
  const setValue = useCallback(
    (next: T) => {
      const nextParams = new URLSearchParams(params);
      if (next === fallback || next === "") {
        nextParams.delete(key);
      } else {
        nextParams.set(key, String(next));
      }
      setParams(nextParams, { replace: false });
    },
    [params, setParams, key, fallback],
  );
  return [current, setValue];
}

export function useUrlNumber(
  key: string,
  fallback: number | null,
): [number | null, (next: number | null) => void] {
  const [params, setParams] = useSearchParams();
  const raw = params.get(key);
  const current = raw === null ? fallback : Number.parseInt(raw, 10);
  const value = Number.isNaN(current) ? fallback : current;
  const setValue = useCallback(
    (next: number | null) => {
      const nextParams = new URLSearchParams(params);
      if (next === null || next === fallback) {
        nextParams.delete(key);
      } else {
        nextParams.set(key, String(next));
      }
      setParams(nextParams, { replace: false });
    },
    [params, setParams, key, fallback],
  );
  return [value, setValue];
}
