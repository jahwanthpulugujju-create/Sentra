import { useCallback, useEffect, useRef, useState } from "react";

// Poll an async function every `interval` ms; expose {data, error, refresh}.
// Cleans up on unmount. (BUILD_PLAN.md §9 — roster/ledger poll every 2s.)
export function usePolling(fn, interval = 2000) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const savedFn = useRef(fn);
  savedFn.current = fn;

  const refresh = useCallback(async () => {
    try {
      const d = await savedFn.current();
      setData(d);
      setError(null);
    } catch (e) {
      setError(e);
    }
  }, []);

  useEffect(() => {
    let active = true;
    refresh();
    const id = setInterval(() => {
      if (active) refresh();
    }, interval);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [interval, refresh]);

  return { data, error, refresh };
}
