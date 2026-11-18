import { useLayoutEffect, useRef, type ReactNode } from "react";

/** The page header used on every screen: heading-24 title, one line of copy-14, actions on the right
 *  (primary action last). */
export function PageHeader({ title, description, actions }: { title: ReactNode; description?: ReactNode; actions?: ReactNode }) {
  return (
    <header className="page-header">
      <div className="page-header-text">
        <h1 className="page-title">{title}</h1>
        {description && <p className="page-description">{description}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </header>
  );
}

/** Template A (list page) and any page that is not a workspace: the shared frame, max 1248 px. */
export function Page({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={`page${className ? ` ${className}` : ""}`}>{children}</div>;
}

/** Template B (workspace): left panel 520 px with the page header, the form and a sticky footer bar;
 *  right panel sticky, filling the window. Used by Describe, Assumptions and Running. */
export function Workspace({
  header,
  children,
  footer,
  aside,
  asideLabel,
}: {
  header: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  aside: ReactNode;
  asideLabel?: string;
}) {
  return (
    <div className="page workspace">
      <div className="workspace-main">
        {header}
        <div className="workspace-body">{children}</div>
        {footer && <div className="footer-bar">{footer}</div>}
      </div>
      <StickyAside label={asideLabel}>{aside}</StickyAside>
    </div>
  );
}

/** A section inside a page: heading-16 title, optional copy-13 description and actions, then content. */
export function Section({
  title,
  description,
  actions,
  children,
  className,
  id,
}: {
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <section className={`section${className ? ` ${className}` : ""}`} id={id}>
      <div className="section-head">
        <div>
          <h2 className="section-title">{title}</h2>
          {description && <p className="section-description">{description}</p>}
        </div>
        {actions}
      </div>
      {children}
    </section>
  );
}

/** The workspace's right panel: sticky below the header, and sized from where it actually is on screen,
 *  so it never runs past the window bottom (24 px clearance). On Results it starts lower down (below the
 *  design choices) and grows to the full height once it sticks. Sets --aside-h on the element; CSS uses it
 *  as the height (or as a max-height for panels that fit their content, such as Running). */
export function StickyAside({
  children,
  label,
  className,
  live,
}: {
  children: ReactNode;
  label?: string;
  className?: string;
  /** aria-live for panels whose content updates on its own (Running). */
  live?: "polite";
}) {
  const ref = useRef<HTMLElement>(null);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    let frame = 0;
    let last = "";
    const fit = () => {
      const top = el.getBoundingClientRect().top;
      const stickyTop = parseFloat(getComputedStyle(el).top) || 0;
      const h = `${Math.max(280, Math.floor(window.innerHeight - Math.max(top, stickyTop) - 24))}px`;
      if (h !== last) {
        last = h;
        el.style.setProperty("--aside-h", h);
      }
    };
    const schedule = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(fit);
    };
    fit();
    const ro = new ResizeObserver(schedule);
    ro.observe(document.body);
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    return () => {
      cancelAnimationFrame(frame);
      ro.disconnect();
      window.removeEventListener("scroll", schedule);
      window.removeEventListener("resize", schedule);
    };
  }, []);
  return (
    <aside ref={ref} className={`workspace-aside${className ? ` ${className}` : ""}`} aria-label={label} aria-live={live}>
      {children}
    </aside>
  );
}
