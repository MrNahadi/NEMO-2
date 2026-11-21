import { MoreHorizontal, X } from "lucide-react";
import { useEffect, useId, useRef, useState, type KeyboardEvent, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { typeahead, usePopoverPlacement } from "./popover";

export interface MenuItem {
  label: string;
  icon?: ReactNode;
  /** Short note at the right, such as a file type. */
  hint?: string;
  onSelect: () => void;
  danger?: boolean;
  disabled?: boolean;
  /** Draw a divider above this item. */
  separated?: boolean;
}

/** "More options" button with a pop-up list of actions. Arrow keys move, Enter chooses, Escape closes. */
export function MoreMenu({
  label,
  items,
  trigger,
  triggerClassName = "icon-btn",
  align = "right",
}: {
  label: string;
  items: MenuItem[];
  /** Button content. Defaults to the three-dots icon. */
  trigger?: ReactNode;
  triggerClassName?: string;
  align?: "left" | "right";
}) {
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const root = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const list = useRef<HTMLDivElement>(null);
  const id = useId();
  const enabled = items.map((it, i) => (it.disabled ? -1 : i)).filter((i) => i >= 0);
  usePopoverPlacement(open, triggerRef, list, { maxHeight: 480, align, onLost: () => setOpen(false) });

  useEffect(() => {
    if (!open) return;
    setActive(enabled[0] ?? 0);
    const close = (e: MouseEvent) => {
      if (!root.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  useEffect(() => {
    if (open) (list.current?.children[active] as HTMLElement | undefined)?.focus();
  }, [open, active]);

  function choose(i: number) {
    const item = items[i];
    if (!item || item.disabled) return;
    setOpen(false);
    triggerRef.current?.focus();
    item.onSelect();
  }

  function step(dir: 1 | -1) {
    const pos = enabled.indexOf(active);
    setActive(enabled[(pos + dir + enabled.length) % enabled.length]);
  }

  function onKey(e: KeyboardEvent) {
    if (e.key === "ArrowDown") step(1);
    else if (e.key === "ArrowUp") step(-1);
    else if (e.key === "Home") setActive(enabled[0]);
    else if (e.key === "End") setActive(enabled[enabled.length - 1]);
    else if (e.key === "Escape" || e.key === "Tab") {
      setOpen(false);
      triggerRef.current?.focus();
      if (e.key === "Tab") return;
    } else {
      // Typeahead: a letter moves to the next item that starts with it.
      const next = typeahead(items.map((it) => it.label), active, e.key, (i) => !items[i].disabled);
      if (next < 0) return;
      setActive(next);
    }
    e.preventDefault();
  }

  return (
    <div className="menu-root" ref={root}>
      <button
        ref={triggerRef}
        type="button"
        className={triggerClassName}
        aria-label={trigger ? undefined : label}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={open ? id : undefined}
        onClick={(e) => {
          e.stopPropagation();
          setOpen((o) => !o);
        }}
        onKeyDown={(e) => {
          if (e.key === "ArrowDown" && !open) {
            e.preventDefault();
            setOpen(true);
          }
        }}
      >
        {trigger ?? <MoreHorizontal aria-hidden />}
      </button>
      {open && (
        <div className={align === "left" ? "menu menu-left" : "menu"} role="menu" id={id} ref={list} aria-label={label} onKeyDown={onKey}>
          {items.map((item, i) => (
            <button
              key={item.label}
              type="button"
              role="menuitem"
              tabIndex={i === active ? 0 : -1}
              className={`menu-item${item.danger ? " danger" : ""}${item.separated ? " separated" : ""}`}
              disabled={item.disabled}
              onMouseEnter={() => !item.disabled && setActive(i)}
              onClick={(e) => {
                e.stopPropagation();
                choose(i);
              }}
            >
              {item.icon}
              <span>{item.label}</span>
              {item.hint && <span className="menu-hint">{item.hint}</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

const FOCUSABLE =
  'a[href]:not([tabindex="-1"]), button:not([disabled]):not([tabindex="-1"]), input:not([disabled]):not([type="hidden"]):not([tabindex="-1"]), select:not([disabled]), textarea:not([disabled]), iframe:not([tabindex="-1"]), summary, [tabindex]:not([tabindex="-1"])';

let openModals = 0;

/**
 * Shared modal behaviour for every dialog (Geist Modal, the report viewer): the rest of the app becomes
 * inert (not focusable, not clickable, hidden from assistive technology), page scrolling is locked, focus
 * moves in and cycles inside with Tab and Shift+Tab, Escape closes, and focus returns to the trigger.
 * Render the dialog through createPortal(..., document.body) so it sits outside the inert #root.
 */
export function useModal(box: React.RefObject<HTMLElement | null>, onClose: () => void, initialFocus?: () => HTMLElement | null | undefined) {
  const close = useRef(onClose);
  close.current = onClose;
  // The trigger is read during the first render, before the commit: an autoFocus input inside the dialog
  // takes focus during the commit, so reading it in the effect would return the dialog's own input.
  const [trigger] = useState(() => (typeof document === "undefined" ? null : (document.activeElement as HTMLElement | null)));
  useEffect(() => {
    const previous = trigger && trigger !== document.body ? trigger : null;
    const root = document.getElementById("root");
    openModals += 1;
    if (root) root.inert = true;
    const overflow = document.documentElement.style.overflow;
    document.documentElement.style.overflow = "hidden";
    (initialFocus?.() ?? box.current?.querySelector<HTMLElement>(FOCUSABLE))?.focus();

    const focusables = () =>
      [...(box.current?.querySelectorAll<HTMLElement>(FOCUSABLE) ?? [])].filter(
        (el) => el.getClientRects().length > 0 && !(el instanceof HTMLInputElement && el.type === "radio" && !el.checked),
      );
    const onKey = (e: globalThis.KeyboardEvent) => {
      if (e.key === "Escape") {
        // An open select or menu inside the dialog closes first.
        if ((document.activeElement as HTMLElement | null)?.getAttribute("aria-expanded") === "true") return;
        if (box.current?.querySelector('[role="menu"], [role="listbox"]')) return;
        e.stopPropagation();
        close.current();
        return;
      }
      if (e.key !== "Tab" || !box.current) return;
      const list = focusables();
      if (!list.length) return;
      const first = list[0];
      const last = list[list.length - 1];
      const inside = box.current.contains(document.activeElement);
      if (e.shiftKey && (document.activeElement === first || !inside)) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && (document.activeElement === last || !inside)) {
        e.preventDefault();
        first.focus();
      }
    };
    // If focus ever lands outside (the browser chrome hands it back to the document), bring it back in.
    const onFocusIn = (e: FocusEvent) => {
      if (box.current && !box.current.contains(e.target as Node)) focusables()[0]?.focus();
    };
    document.addEventListener("keydown", onKey, true);
    document.addEventListener("focusin", onFocusIn);
    return () => {
      document.removeEventListener("keydown", onKey, true);
      document.removeEventListener("focusin", onFocusIn);
      openModals -= 1;
      if (root && openModals === 0) root.inert = false;
      document.documentElement.style.overflow = overflow;
      // Return focus to the control that opened the dialog (after the app stops being inert).
      if (previous?.isConnected) previous.focus();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
}

/** Geist Modal (560 px, 640 wide). Rendered over a dimmed, inert app; focus stays inside until it closes. */
export function Dialog({
  title,
  description,
  children,
  actions,
  onClose,
  wide,
  initialFocus,
}: {
  title: string;
  description?: ReactNode;
  children: ReactNode;
  actions: ReactNode;
  onClose: () => void;
  /** 640 px instead of 560 px. */
  wide?: boolean;
  /** CSS selector of the element to focus first (default: the first input, else the primary button). */
  initialFocus?: string;
}) {
  const box = useRef<HTMLDivElement>(null);
  const titleId = useId();
  const descId = useId();
  useModal(box, onClose, () =>
    (initialFocus ? box.current?.querySelector<HTMLElement>(initialFocus) : null) ??
    box.current?.querySelector<HTMLElement>(
      ".dialog-body input:not([type=radio]), .dialog-body input:checked, .dialog-actions button.btn-primary, .dialog-actions button.btn-danger, .dialog-actions button",
    ),
  );
  return createPortal(
    <div className="overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div
        className={`dialog${wide ? " wide" : ""}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={description ? descId : undefined}
        ref={box}
      >
        <div className="dialog-head">
          <h2 id={titleId} className="dialog-title">
            {title}
          </h2>
          {description && (
            <p id={descId} className="dialog-description">
              {description}
            </p>
          )}
          <button type="button" className="icon-btn dialog-close" aria-label="Close" onClick={onClose}>
            <X aria-hidden />
          </button>
        </div>
        <div className="dialog-body">{children}</div>
        <div className="dialog-actions">{actions}</div>
      </div>
    </div>,
    document.body,
  );
}
