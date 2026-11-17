import { MoreHorizontal, X } from "lucide-react";
import { useEffect, useId, useRef, useState, type KeyboardEvent, type ReactNode } from "react";

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
    } else return;
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

/** Geist Modal. Focus moves into it; Escape, the close button or the overlay closes it. */
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
  /** 640 px instead of 540 px. */
  wide?: boolean;
  /** CSS selector of the element to focus first (default: the first input, else the primary button). */
  initialFocus?: string;
}) {
  const box = useRef<HTMLDivElement>(null);
  const titleId = useId();
  const descId = useId();
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const first =
      (initialFocus ? box.current?.querySelector<HTMLElement>(initialFocus) : null) ??
      box.current?.querySelector<HTMLElement>(".dialog-body input, .dialog-actions button.btn-primary, .dialog-actions button.btn-danger, .dialog-actions button");
    first?.focus();
    const onKey = (e: globalThis.KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "Tab" && box.current) {
        const focusable = [...box.current.querySelectorAll<HTMLElement>("input:not([disabled]), button:not([disabled]), a[href], summary")].filter(
          (el) => !(el instanceof HTMLInputElement && el.type === "radio" && !el.checked),
        );
        const firstEl = focusable[0];
        const lastEl = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === firstEl) {
          e.preventDefault();
          lastEl.focus();
        } else if (!e.shiftKey && document.activeElement === lastEl) {
          e.preventDefault();
          firstEl.focus();
        }
      }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      previous?.focus();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [onClose]);
  return (
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
    </div>
  );
}
