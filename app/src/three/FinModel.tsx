import { useEffect, useMemo } from "react";
import * as THREE from "three";
import type { FinDesign } from "../types";

// Viewer axes: x along the chord (stock at x = 0), y up the span from the hull, z across the foil.
const SKIN = new THREE.Color("#b9bec6");
const INNER = new THREE.Color("#7f8894");
const STOCK = new THREE.Color("#4a4f57");
const HULL = new THREE.Color("#a3a9b0");

function halfThickness(x: number, t: number): number {
  return 5 * t * (0.2969 * Math.sqrt(x) - 0.126 * x - 0.3516 * x * x + 0.2843 * x ** 3 - 0.1036 * x ** 4);
}

function foilShape(d: FinDesign, inset = 0): THREE.Shape {
  const c = d.chord_mm;
  const xs = d.stock_position * c;
  const s = new THREE.Shape();
  const n = 60;
  const pts: [number, number][] = [];
  for (let i = 0; i <= n; i++) {
    const x = 0.5 * (1 - Math.cos((Math.PI * i) / n));
    pts.push([x * c - xs, Math.max(halfThickness(x, d.thickness_ratio) * c - inset, 0)]);
  }
  s.moveTo(pts[0][0], pts[0][1]);
  for (const [x, y] of pts) s.lineTo(x, y);
  for (const [x, y] of [...pts].reverse()) s.lineTo(x, -y);
  return s;
}

export function finSize(d: FinDesign): number {
  return Math.max(d.chord_mm * 1.2, d.span_mm + d.bearing_gap_mm, 300);
}

export function finCentreY(d: FinDesign): number {
  return (d.span_mm + d.bearing_gap_mm) / 2;
}

export function FinModel({ design: d }: { design: FinDesign }) {
  const lift = d.bearing_gap_mm;
  const outer = useMemo(() => {
    const g = new THREE.ExtrudeGeometry(foilShape(d), { depth: d.span_mm, bevelEnabled: false, curveSegments: 4 });
    g.rotateX(-Math.PI / 2);
    return g;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [d.chord_mm, d.span_mm, d.thickness_ratio, d.stock_position]);
  const rib = useMemo(() => {
    const g = new THREE.ExtrudeGeometry(foilShape(d, d.skin_mm), { depth: d.web_mm, bevelEnabled: false });
    g.rotateX(-Math.PI / 2);
    return g;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [d.chord_mm, d.thickness_ratio, d.stock_position, d.skin_mm, d.web_mm]);
  useEffect(() => () => outer.dispose(), [outer]);
  useEffect(() => () => rib.dispose(), [rib]);

  const count = Math.max(Math.ceil(d.span_mm / d.rib_spacing_mm - 1e-9), 1);
  const pitch = d.span_mm / count;
  const c = d.chord_mm;
  const xs = d.stock_position * c;
  const spars = [d.front_spar, d.rear_spar].map((f) => ({ x: f * c - xs, h: 2 * (halfThickness(f, d.thickness_ratio) * c - d.skin_mm) }));
  const stockLength = d.bearing_gap_mm + d.span_mm / 2;
  return (
    <group>
      <mesh position={[0, lift, 0]}>
        <boxGeometry args={[c * 1.6, 6, Math.max(c * 0.6, 200)]} />
        <meshStandardMaterial color={HULL} roughness={0.9} transparent opacity={0.6} />
      </mesh>
      <mesh geometry={outer} position={[0, lift, 0]}>
        <meshStandardMaterial color={SKIN} metalness={0.4} roughness={0.45} transparent opacity={0.35} side={THREE.DoubleSide} depthWrite={false} />
      </mesh>
      {Array.from({ length: count + 1 }, (_, i) => (
        <mesh key={i} geometry={rib} position={[0, lift + Math.min(Math.max(i * pitch - d.web_mm / 2, 0), d.span_mm - d.web_mm), 0]}>
          <meshStandardMaterial color={INNER} metalness={0.4} roughness={0.5} />
        </mesh>
      ))}
      {spars.map((s, i) => (
        <mesh key={i} position={[s.x, lift + d.span_mm / 2, 0]}>
          <boxGeometry args={[d.web_mm, d.span_mm, s.h]} />
          <meshStandardMaterial color={INNER} metalness={0.4} roughness={0.5} />
        </mesh>
      ))}
      <mesh position={[0, lift - d.bearing_gap_mm + stockLength / 2, 0]}>
        <cylinderGeometry args={[d.stock_diameter_mm / 2, d.stock_diameter_mm / 2, stockLength, 40]} />
        <meshStandardMaterial color={STOCK} metalness={0.4} roughness={0.45} />
      </mesh>
    </group>
  );
}
