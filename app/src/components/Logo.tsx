/** NEMO mark: a padeye (lifting lug) seen side-on: a flared plate rising to a round head with the pin hole,
 *  welded to a base plate. The sides are tangent to the head, so it reads as a lug, not a padlock or a
 *  tombstone. Drawn in currentColor on a 24-unit grid; the hole is a cut-out. Same path as public/favicon.svg. */
export const LOGO_PATH =
  "M2 17.5L6.97 6.28A5.5 5.5 0 0 1 17.03 6.28L22 17.5ZM15 8.5a3 3 0 1 0 -6 0a3 3 0 1 0 6 0ZM0.5 17.5h23v2.75h-23z";

export function Logo({ size = 20 }: { size?: number }) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} aria-hidden focusable="false">
      <path fill="currentColor" fillRule="evenodd" d={LOGO_PATH} />
    </svg>
  );
}
