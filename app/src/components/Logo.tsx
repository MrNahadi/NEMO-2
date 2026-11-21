/** NEMO mark: a padeye (lifting lug) seen side-on: a round head with the pin hole, near-vertical sides
 *  tangent to the head, welded to a base plate. The head dominates and the hole is about a third of the
 *  head, so at 20 px it reads as a lug with a hole (round 3's flared version read as a tent). Drawn in
 *  currentColor on a 24-unit grid; the hole is a cut-out. Same path as public/favicon.svg. */
export const LOGO_PATH = "M4.5 19L5.01 8.66A7 7 0 1 1 18.99 8.66L19.5 19ZM15.2 9a3.2 3.2 0 1 0 -6.4 0a3.2 3.2 0 1 0 6.4 0ZM1 19h22v2.5h-22z";

export function Logo({ size = 20 }: { size?: number }) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} aria-hidden focusable="false">
      <path fill="currentColor" fillRule="evenodd" d={LOGO_PATH} />
    </svg>
  );
}
