import { useLayoutEffect, useRef, type RefObject } from "react";

const EDGE = 8; // clearance from the window edges, the sticky header and the sticky footer bar
const GAP = 6; // between the trigger and the popover

/** The part of the window a popover may use: below the sticky header, above the sticky footer bar and 8 px
 *  inside every window edge. Inside a modal the page chrome does not count. */
function corridor(anchor: HTMLElement) {
  const inModal = !!anchor.closest(".overlay, .report-overlay");
  let top = 0;
  let bottom = window.innerHeight;
  if (!inModal) {
    top = Math.max(0, document.querySelector(".app-header")?.getBoundingClientRect().bottom ?? 0);
    const footer = document.querySelector(".footer-bar")?.getBoundingClientRect();
    // The sticky footer bar covers everything under its top edge (content sits above it in the DOM), so it
    // bounds every popover outside it, including one whose trigger has scrolled under it.
    if (footer && !anchor.closest(".footer-bar") && footer.top < window.innerHeight) bottom = Math.min(bottom, footer.top);
  }
  return { top: top + EDGE, bottom: bottom - EDGE, rawTop: top, rawBottom: bottom };
}

/**
 * Keeps a popover (select list, menu) inside the visible corridor: it opens below its trigger when it fits,
 * flips above when there is more room there, caps its height to the room it has (it scrolls inside), and
 * shifts sideways so neither edge leaves the window. 8 px clearance from every window edge, from the sticky
 * header and from the sticky footer bar. When the trigger scrolls out of the corridor (under the header or
 * the footer bar, or off screen) `onLost` is called so the popover closes instead of floating detached.
 * The popover stays position: absolute inside its root, so it scrolls with the page; it is re-placed on
 * scroll and resize while open. Writes styles straight onto the element (no re-render).
 */
export function usePopoverPlacement(
  open: boolean,
  anchor: RefObject<HTMLElement | null>,
  popover: RefObject<HTMLElement | null>,
  {
    maxHeight = 320,
    align = "left",
    onLost,
  }: { maxHeight?: number; align?: "left" | "right" | "stretch"; onLost?: () => void } = {},
) {
  const lost = useRef(onLost);
  lost.current = onLost;
  useLayoutEffect(() => {
    if (!open) return;
    const place = () => {
      const el = anchor.current;
      const p = popover.current;
      if (!el || !p) return;
      const a = el.getBoundingClientRect();
      const room = corridor(el);
      // The trigger has left the part of the window the user can see: close rather than float.
      if (a.bottom <= room.rawTop + 4 || a.top >= room.rawBottom - 4) {
        lost.current?.();
        return;
      }
      // scrollHeight is the full content height whatever the current max-height, so nothing is reset (a reset
      // would lose the list's own scroll position).
      const natural = Math.min(p.scrollHeight, maxHeight);
      const below = room.bottom - a.bottom - GAP;
      const above = a.top - GAP - room.top;
      const up = natural > below && above > below;
      const space = Math.max(96, Math.floor(up ? above : below));
      p.style.maxHeight = `${Math.min(natural, space)}px`;
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
