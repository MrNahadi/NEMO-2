import { Check, ChevronDown } from "lucide-react";
import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react";
import { typeahead, usePopoverPlacement } from "./popover";
import { useControlA11y } from "./ui";

export interface Option<T extends string | number> {
  value: T;
  label: string;
  hint?: string;
}

/** Listbox drop-down drawn with the design system, so it matches light and dark themes. */
export function Select<T extends string | number>({
  value,
  options,
  onChange,
  label,
  width = 420,
}: {
  value: T;
  options: Option<T>[];
  onChange: (value: T) => void;
  label: string;
  width?: number;
}) {
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const root = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const list = useRef<HTMLUListElement>(null);
  const id = useId();
  const selected = options.find((o) => o.value === value);
  const a11y = useControlA11y(label);
  usePopoverPlacement(open, trigger, list, { align: "stretch" });

  useEffect(() => {
    if (!open) return;
    setActive(Math.max(0, options.findIndex((o) => o.value === value)));
    const close = (e: MouseEvent) => {
      if (!root.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open, options, value]);

  useEffect(() => {
    if (open) list.current?.children[active]?.scrollIntoView({ block: "nearest" });
  }, [active, open]);

  function choose(index: number) {
    const option = options[index];
    if (option) onChange(option.value);
    setOpen(false);
  }

  function onKey(e: KeyboardEvent) {
    if (!open && ["ArrowDown", "ArrowUp", "Enter", " "].includes(e.key)) {
      e.preventDefault();
      setOpen(true);
      return;
    }
    if (!open) return;
    if (e.key === "ArrowDown") setActive((a) => Math.min(a + 1, options.length - 1));
    else if (e.key === "ArrowUp") setActive((a) => Math.max(a - 1, 0));
    else if (e.key === "Home") setActive(0);
    else if (e.key === "End") setActive(options.length - 1);
    else if (e.key === "Enter" || e.key === " ") choose(active);
    else if (e.key === "Escape" || e.key === "Tab") {
      setOpen(false);
      return;
    } else {
      const next = typeahead(options.map((o) => o.label), active, e.key);
      if (next < 0) return;
      setActive(next);
    }
    e.preventDefault();
  }

  return (
    <div className="select-root" ref={root} style={{ maxWidth: width }}>
      <button
        ref={trigger}
        type="button"
        className="select-trigger"
        aria-haspopup="listbox"
        aria-expanded={open}
        {...a11y.props}
        aria-controls={id}
        aria-activedescendant={open ? `${id}-${active}` : undefined}
        onClick={() => setOpen((o) => !o)}
        onKeyDown={onKey}
      >
        <span className="select-value">{selected?.label ?? "Choose"}</span>
        <ChevronDown aria-hidden className={open ? "select-chevron open" : "select-chevron"} />
      </button>
      {a11y.own}
      {open && (
        <ul className="select-menu" role="listbox" id={id} ref={list} aria-label={label}>
          {options.map((o, i) => (
            <li
              key={String(o.value)}
              id={`${id}-${i}`}
              role="option"
              aria-selected={o.value === value}
              className={i === active ? "select-option active" : "select-option"}
              onMouseEnter={() => setActive(i)}
              onMouseDown={(e) => {
                e.preventDefault();
                choose(i);
              }}
            >
              <span className="stack">
                <span>{o.label}</span>
                {o.hint && <span className="caption">{o.hint}</span>}
              </span>
              {o.value === value && <Check aria-hidden className="select-tick" />}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
