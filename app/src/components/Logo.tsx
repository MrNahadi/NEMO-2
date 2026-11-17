/** NEMO mark: a padeye (lifting lug) welded to a deck plate, with its pin hole.
 *  Drawn in currentColor on a 24-unit grid; the pin hole is a cut-out, so the
 *  background behind the mark shows through. */
export function Logo({ size = 20 }: { size?: number }) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} aria-hidden focusable="false">
      <path
        fill="currentColor"
        fillRule="evenodd"
        d="M4.5 19L5.53 7.9A6.5 6.5 0 1 1 18.47 7.9L19.5 19ZM15 8.5a3 3 0 1 0 -6 0a3 3 0 1 0 6 0ZM2.5 19h19v2.5h-19z"
      />
    </svg>
  );
}
