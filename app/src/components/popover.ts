import { useLayoutEffect, type RefObject } from "react";

const EDGE = 8; // clearance from the window edges and the sticky header
const GAP = 6; // between the trigger and the popover

/**
 * Keeps a popover (select list, menu) inside the window: it opens below its trigger when it fits, flips
 * above when there is more room there, caps its height to the room it has (it scrolls inside), and shifts
 * sideways so neither edge leaves the window. 8 px clearance from every edge and from the sticky header.
 * The popover stays position: absolute inside its root, so it scrolls with the page; it is re-placed on
 * scroll and resize while open. Writes styles straight onto the element (no re-render).
 */
export function usePopoverPlacement(
  open: boolean,
  anchor: RefObject<HTMLElement | null>,
  popover: RefObject<HTMLElement | null>,
  { maxHeight = 320, align = "left" }: { maxHeight?: number; align?: "left" | "right" | "stretch" } = {},
) {
  useLayoutEffect(() => {
    if (!open) return;
    const place = () => {
      const a = anchor.current?.getBoundingClientRect();
      const p = popover.current;
      if (!a || !p) return;
      // scrollHeight is the full content height whatever the current max-height, so nothing is reset (a reset
      // would lose the list's own scroll position).
      const natural = Math.min(p.scrollHeight, maxHeight);
      const header = document.querySelector(".app-header")?.getBoundingClientRect().bottom ?? 0;
      const topLimit = Math.max(0, header) + EDGE;
      const below = window.innerHeight - a.bottom - GAP - EDGE;
      const above = a.top - GAP - topLimit;
      const up = natural > below && above > below;
      const room = Math.max(96, Math.floor(up ? above : below));
      p.style.maxHeight = `${Math.min(natural, room)}px`;
      if (up) {
        p.style.top = "auto";
        p.style.bottom = `calc(100% + ${GAP}px)`;
      } else {
        p.style.top = `calc(100% + ${GAP}px)`;
        p.style.bottom = "auto";
      }
      p.dataset.side = up ? "top" : "bottom";
      if (align !== "stretch") {
        const r = p.getBoundingClientRect();
        const current = Number(p.dataset.shift ?? 0);
        const left = r.left - current;
        const right = r.right - current;
        let shift = 0;
        if (right > window.innerWidth - EDGE) shift = window.innerWidth - EDGE - right;
        if (left + shift < EDGE) shift = EDGE - left;
        p.dataset.shift = String(Math.round(shift));
        p.style.translate = shift ? `${Math.round(shift)}px 0` : "";
      }
    };
    place();
    let frame = 0;
    const schedule = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(place);
    };
    // Ignore scrolling inside the popover itself.
    const onScroll = (e: Event) => {
      if (!popover.current?.contains(e.target as Node)) schedule();
    };
    window.addEventListener("resize", schedule);
    window.addEventListener("scroll", onScroll, true);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("resize", schedule);
      window.removeEventListener("scroll", onScroll, true);
    };
  }, [open, anchor, popover, maxHeight, align]);
}

/** Typeahead for lists: the index of the next item (after `from`) whose label starts with `key`. */
export function typeahead(labels: string[], from: number, key: string, enabled?: (i: number) => boolean): number {
  if (key.length !== 1 || !/\S/.test(key)) return -1;
  const k = key.toLowerCase();
  for (let step = 1; step <= labels.length; step++) {
    const i = (from + step) % labels.length;
    if ((enabled ? enabled(i) : true) && labels[i].trim().toLowerCase().startsWith(k)) return i;
  }
  return -1;
}
