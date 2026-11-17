import { useEffect, useMemo } from "react";
import * as THREE from "three";
import type { StressSurface } from "../types";
import { frameOf, toViewer } from "./frame";

// Blue (low) to red (high), similar to most FEA viewers.
const RAMP = ["#1f4fbf", "#2bb3c0", "#8ad15c", "#f2c94c", "#e5484d"].map((c) => new THREE.Color(c));

export function rampColor(fraction: number, out = new THREE.Color()): THREE.Color {
  const f = Math.min(Math.max(fraction, 0), 1) * (RAMP.length - 1);
  const i = Math.min(Math.floor(f), RAMP.length - 2);
  return out.copy(RAMP[i]).lerp(RAMP[i + 1], f - i);
}

/** Engine coordinates are x along the base, y through the plate, z up. The viewer uses y up. */
export function StressModel({ surface, scaleMax }: { surface: StressSurface; scaleMax: number }) {
  const geometry = useMemo(() => {
    const g = new THREE.BufferGeometry();
    const p = surface.positions;
    const positions = toViewer(p, frameOf(p));
    const colors = new Float32Array(p.length);
    const c = new THREE.Color();
    surface.von_mises.forEach((value, i) => {
      rampColor(value / scaleMax, c);
      colors[3 * i] = c.r;
      colors[3 * i + 1] = c.g;
      colors[3 * i + 2] = c.b;
    });
    g.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    g.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    g.setIndex(surface.triangles);
    g.computeVertexNormals();
    return g;
  }, [surface, scaleMax]);
  useEffect(() => () => geometry.dispose(), [geometry]);

  return (
    <mesh geometry={geometry}>
      <meshStandardMaterial vertexColors side={THREE.DoubleSide} roughness={0.7} metalness={0.05} flatShading />
    </mesh>
  );
}
