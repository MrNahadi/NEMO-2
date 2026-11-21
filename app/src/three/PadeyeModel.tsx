import { useFrame } from "@react-three/fiber";
import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import type { PadeyeDesign } from "../types";

// World axes in the viewer: x along the base, y up, z through the plate thickness.
// Dimensions are in millimetres; 1 unit = 1 mm.

const STEEL = new THREE.Color("#b9bec6");
const CHEEK = new THREE.Color("#9aa3ad");
const WELD = new THREE.Color("#6f7680");
const SHACKLE = new THREE.Color("#4a4f57"); // galvanised hardware: neutral, so red stays a status colour
const ACCENT = new THREE.Color("#0070f7"); // Geist blue-700: the region the selected check is about
const FORCE = new THREE.Color("#8f8f8f"); // Geist gray-700: the sling pull direction

type Dims = PadeyeDesign;
const KEYS: (keyof Dims)[] = [
  "main_thickness_mm",
  "head_radius_mm",
  "hole_diameter_mm",
  "base_length_mm",
  "hole_height_mm",
  "weld_leg_mm",
  "cheek_thickness_mm",
  "cheek_radius_mm",
  "cheek_weld_leg_mm",
];

/** Eases displayed dimensions toward the target so the part visibly grows or shrinks. */
function useEasedDims(target: Dims): Dims {
  const current = useRef<Dims>({ ...target });
  const [, setTick] = useState(0);
  useFrame(() => {
    let moving = false;
    for (const key of KEYS) {
      const from = current.current[key];
      const to = target[key];
      const next = from + (to - from) * 0.18;
      if (Math.abs(to - next) > 0.02) {
        current.current[key] = next;
        moving = true;
      } else if (from !== to) {
        current.current[key] = to;
        moving = true;
      }
    }
    if (moving) setTick((t) => t + 1);
  });
  return current.current;
}

function tangentAngle(px: number, py: number, cy: number, r: number, side: 1 | -1): number {
  const dx = px;
  const dy = py - cy;
  const d = Math.max(Math.hypot(dx, dy), r + 1e-6);
  return Math.atan2(dy, dx) + side * Math.acos(r / d);
}

function outlineShape(d: Dims): THREE.Shape {
  const half = d.base_length_mm / 2;
  const h = d.hole_height_mm;
  const r = d.head_radius_mm;
  const right = tangentAngle(half, 0, h, r, 1);
  const left = tangentAngle(-half, 0, h, r, -1);
  const shape = new THREE.Shape();
  shape.moveTo(-half, 0);
  shape.lineTo(half, 0);
  shape.lineTo(r * Math.cos(right), h + r * Math.sin(right));
  shape.absarc(0, h, r, right, left, false);
  shape.lineTo(-half, 0);
  const hole = new THREE.Path();
  hole.absarc(0, h, d.hole_diameter_mm / 2, 0, Math.PI * 2, true);
  shape.holes.push(hole);
  return shape;
}

function ringShape(outer: number, inner: number): THREE.Shape {
  const shape = new THREE.Shape();
  shape.absarc(0, 0, outer, 0, Math.PI * 2, false);
  const hole = new THREE.Path();
  hole.absarc(0, 0, inner, 0, Math.PI * 2, true);
  shape.holes.push(hole);
  return shape;
}

function weldGeometry(length: number, leg: number): THREE.BufferGeometry {
  const tri = new THREE.Shape();
  tri.moveTo(0, 0);
  tri.lineTo(leg, 0);
  tri.lineTo(0, leg);
  tri.lineTo(0, 0);
  const g = new THREE.ExtrudeGeometry(tri, { depth: length, bevelEnabled: false });
  g.rotateY(-Math.PI / 2); // extrude along -x; triangle legs point up (+y) and out of the face (+z)
  g.translate(length / 2, 0, 0);
  return g;
}

export function PadeyeModel({
  design,
  pinDiameter,
  jawWidth,
  slingAngleDeg,
  showShackle = true,
  highlight = null,
}: {
  design: PadeyeDesign;
  pinDiameter?: number;
  jawWidth?: number;
  slingAngleDeg: number;
  showShackle?: boolean;
  /** Id of the check whose region is marked on the model. */
  highlight?: string | null;
}) {
  const d = useEasedDims(design);
  const t = d.main_thickness_mm;
  const hasCheeks = d.cheek_thickness_mm > 0.2;

  const main = useMemo(() => {
    const g = new THREE.ExtrudeGeometry(outlineShape(d), { depth: t, bevelEnabled: false, curveSegments: 48 });
    g.translate(0, 0, -t / 2);
    return g;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [d.base_length_mm, d.head_radius_mm, d.hole_height_mm, d.hole_diameter_mm, t]);

  const cheek = useMemo(() => {
    if (!hasCheeks) return null;
    return new THREE.ExtrudeGeometry(ringShape(d.cheek_radius_mm, d.hole_diameter_mm / 2), {
      depth: d.cheek_thickness_mm,
      bevelEnabled: false,
      curveSegments: 48,
    });
  }, [hasCheeks, d.cheek_radius_mm, d.hole_diameter_mm, d.cheek_thickness_mm]);

  const weld = useMemo(() => weldGeometry(d.base_length_mm, d.weld_leg_mm), [d.base_length_mm, d.weld_leg_mm]);

  // Geometry is rebuilt while the part animates; free each old copy.
  useEffect(() => () => main.dispose(), [main]);
  useEffect(() => () => cheek?.dispose(), [cheek]);
  useEffect(() => () => weld.dispose(), [weld]);

  const angle = (slingAngleDeg * Math.PI) / 180;
  const pin = pinDiameter ?? d.hole_diameter_mm * 0.9;
  const jaw = jawWidth ?? d.main_thickness_mm + 2 * d.cheek_thickness_mm + 4;
  const bowLength = Math.max(pin * 3.2, d.head_radius_mm * 2.2);

  const bow = useMemo(() => {
    // U-shaped bow from one pin end, around the head, to the other, along the sling.
    const reach = d.head_radius_mm + pin * 0.6 + bowLength * 0.4;
    const half = jaw / 2 + pin / 2;
    const curve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(0, 0, -half),
      new THREE.Vector3(reach * 0.55, 0, -half * 1.15),
      new THREE.Vector3(reach, 0, -half * 0.6),
      new THREE.Vector3(reach * 1.08, 0, 0),
      new THREE.Vector3(reach, 0, half * 0.6),
      new THREE.Vector3(reach * 0.55, 0, half * 1.15),
      new THREE.Vector3(0, 0, half),
    ]);
    return new THREE.TubeGeometry(curve, 48, pin * 0.42, 16, false);
  }, [d.head_radius_mm, pin, jaw, bowLength]);
  useEffect(() => () => bow.dispose(), [bow]);

  const weldLit = highlight === "base_weld" || highlight === "base_weld_size";
  const shackleLit = highlight !== null && highlight.startsWith("shackle");

  return (
    <group>
      <CheckRegion design={d} pin={pin} angle={angle} check={highlight} />
      {/* Context: the deck plate the padeye is welded to, kept faint (about 0.2) so the part leads (I2). */}
      <mesh position={[0, -1.5, 0]} userData={{ excludeFit: true }}>
        <boxGeometry args={[d.base_length_mm + 40, 3, Math.max(d.main_thickness_mm * 6, 40)]} />
        <meshStandardMaterial color="#a3a9b0" roughness={0.9} transparent opacity={0.22} depthWrite={false} />
      </mesh>
      {/* Steel: metalness and roughness capped so no face blows out to white under the lights (I3). */}
      <mesh geometry={main} castShadow receiveShadow>
        <meshStandardMaterial color={STEEL} metalness={0.35} roughness={0.5} />
      </mesh>
      {cheek && (
        <>
          <mesh geometry={cheek} position={[0, d.hole_height_mm, t / 2]} castShadow>
            <meshStandardMaterial color={CHEEK} metalness={0.35} roughness={0.5} />
          </mesh>
          <mesh geometry={cheek} position={[0, d.hole_height_mm, -t / 2]} rotation={[0, Math.PI, 0]} castShadow>
            <meshStandardMaterial color={CHEEK} metalness={0.35} roughness={0.5} />
          </mesh>
        </>
      )}
      <mesh geometry={weld} position={[0, 0, t / 2]}>
        <meshStandardMaterial color={weldLit ? ACCENT : WELD} emissive={weldLit ? ACCENT : "#000000"} emissiveIntensity={weldLit ? 0.4 : 0} roughness={0.8} />
      </mesh>
      <mesh geometry={weld} position={[0, 0, -t / 2]} rotation={[0, Math.PI, 0]}>
        <meshStandardMaterial color={weldLit ? ACCENT : WELD} emissive={weldLit ? ACCENT : "#000000"} emissiveIntensity={weldLit ? 0.4 : 0} roughness={0.8} />
      </mesh>
      {showShackle && (
        <group position={[0, d.hole_height_mm, 0]} rotation={[0, 0, angle]}>
          <mesh rotation={[Math.PI / 2, 0, 0]}>
            <cylinderGeometry args={[pin / 2, pin / 2, jaw + pin * 1.6, 32]} />
            <meshStandardMaterial color={shackleLit ? ACCENT : SHACKLE} metalness={0.3} roughness={0.5} />
          </mesh>
          <mesh geometry={bow}>
            <meshStandardMaterial color={shackleLit ? ACCENT : SHACKLE} metalness={0.3} roughness={0.5} />
          </mesh>
          <mesh position={[bowLength * 1.4, 0, 0]} rotation={[0, 0, -Math.PI / 2]}>
            <cylinderGeometry args={[pin * 0.12, pin * 0.12, bowLength * 1.6, 8]} />
            <meshBasicMaterial color={FORCE} transparent opacity={0.8} />
          </mesh>
          <mesh position={[bowLength * 2.3, 0, 0]} rotation={[0, 0, -Math.PI / 2]}>
            <coneGeometry args={[pin * 0.4, pin * 1.1, 16]} />
            <meshBasicMaterial color={FORCE} />
          </mesh>
        </group>
      )}
    </group>
  );
}

/** Frame for the padeye with its shackle and sling: the sling rises at about 60 degrees from the hole,
 *  so the frame reaches the end of the sling arrow and the sling never leaves the view abruptly (I2). */
export function padeyeFrame(design: PadeyeDesign): { size: number; centreY: number } {
  const pin = design.hole_diameter_mm * 0.9;
  const bowLength = Math.max(pin * 3.2, design.head_radius_mm * 2.2);
  const sling = bowLength * 2.3 + pin; // sling line and arrow past the bow (see the shackle group below)
  const top = design.hole_height_mm + sling * Math.sin(Math.PI / 3);
  const across = Math.max(design.base_length_mm, 2 * sling * Math.cos(Math.PI / 3) + pin);
  const height = Math.max(top, design.hole_height_mm + design.head_radius_mm);
  return { size: Math.max(across, height, 60), centreY: height / 2 };
}

// ------------------------------------------------------------ check regions
/** Slab through the plate thickness between two points in the plate plane. */
function slab(x1: number, y1: number, x2: number, y2: number, width: number): THREE.Shape {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const len = Math.hypot(dx, dy) || 1;
  const nx = (-dy / len) * (width / 2);
  const ny = (dx / len) * (width / 2);
  const s = new THREE.Shape();
  s.moveTo(x1 + nx, y1 + ny);
  s.lineTo(x2 + nx, y2 + ny);
  s.lineTo(x2 - nx, y2 - ny);
  s.lineTo(x1 - nx, y1 - ny);
  s.lineTo(x1 + nx, y1 + ny);
  return s;
}

function arcBand(cx: number, cy: number, inner: number, outer: number, from: number, to: number): THREE.Shape {
  const s = new THREE.Shape();
  s.absarc(cx, cy, outer, from, to, false);
  s.absarc(cx, cy, inner, to, from, true);
  return s;
}

/**
 * Marks the material each check is about: the two net sections beside the hole for tension,
 * the line above the hole for splitting, the two shear planes, the pin contact arc, the base
 * section, or the cheek welds. Drawn in the accent colour, slightly proud of the plate.
 */
function CheckRegion({ design: d, pin, angle, check }: { design: PadeyeDesign; pin: number; angle: number; check: string | null }) {
  const geometry = useMemo(() => {
    if (!check) return null;
    const h = d.hole_height_mm;
    const rh = d.hole_diameter_mm / 2;
    const head = d.cheek_thickness_mm > 0.2 ? Math.min(d.head_radius_mm, d.cheek_radius_mm) : d.head_radius_mm;
    const ux = Math.cos(angle);
    const uy = Math.sin(angle);
    const nx = -uy;
    const ny = ux;
    const band = Math.max(2.4, head * 0.09);
    const shapes: THREE.Shape[] = [];
    if (check === "head_tension") {
      for (const sgn of [1, -1]) shapes.push(slab(sgn * nx * rh, h + sgn * ny * rh, sgn * nx * head, h + sgn * ny * head, band));
    } else if (check === "head_fracture") {
      shapes.push(slab(ux * rh, h + uy * rh, ux * head, h + uy * head, band));
    } else if (check === "head_shear_out") {
      const phi = ((55 * pin) / d.hole_diameter_mm) * (Math.PI / 180);
      for (const sgn of [1, -1]) {
        const a = angle + sgn * phi;
        const sx = (pin / 2) * Math.cos(a);
        const sy = (pin / 2) * Math.sin(a);
        const lateral = (sx * nx + sy * ny);
        const along = Math.sqrt(Math.max(head * head - lateral * lateral, 0));
        shapes.push(slab(sx, h + sy, nx * lateral + ux * along, h + ny * lateral + uy * along, band * 0.8));
      }
    } else if (check === "head_bearing") {
      shapes.push(arcBand(0, h, rh - 0.4, rh + band, angle - Math.PI / 2, angle + Math.PI / 2));
    } else if (["pin_hole_fit", "hole_clearance", "hole_fits_pin"].includes(check)) {
      shapes.push(arcBand(0, h, rh - 0.4, rh + band, 0, Math.PI * 2));
    } else if (check === "base_combined" || check === "base_shear") {
      const strip = Math.max(2.5, d.hole_height_mm * 0.05);
      shapes.push(slab(-d.base_length_mm / 2, strip / 2, d.base_length_mm / 2, strip / 2, strip));
    } else if ((check === "cheek_weld" || check === "cheek_weld_size") && d.cheek_thickness_mm > 0.2) {
      shapes.push(arcBand(0, h, d.cheek_radius_mm - 0.6, d.cheek_radius_mm + band, 0, Math.PI * 2));
    }
    if (!shapes.length) return null;
    const depth = d.main_thickness_mm + 2 * d.cheek_thickness_mm + 1.2;
    const g = new THREE.ExtrudeGeometry(shapes, { depth, bevelEnabled: false, curveSegments: 48 });
    g.translate(0, 0, -depth / 2);
    return g;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [d.hole_height_mm, d.hole_diameter_mm, d.head_radius_mm, d.cheek_radius_mm, d.cheek_thickness_mm, d.main_thickness_mm, d.base_length_mm, pin, angle, check]);
  useEffect(() => () => geometry?.dispose(), [geometry]);
  if (!geometry) return null;
  return (
    <mesh geometry={geometry} renderOrder={2}>
      <meshStandardMaterial color={ACCENT} emissive={ACCENT} emissiveIntensity={0.55} roughness={0.5} transparent opacity={0.9} />
    </mesh>
  );
}
