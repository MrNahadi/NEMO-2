import { useEffect, useMemo } from "react";
import * as THREE from "three";
import type { BracketDesign } from "../types";

// Viewer axes: x out from the bulkhead (centred on the seat), y up, z along the pipe. 1 unit = 1 mm.
const STEEL = new THREE.Color("#b9bec6");
const KNEE = new THREE.Color("#9aa3ad");
const PIPE = new THREE.Color("#8d949c");
const BOLT = new THREE.Color("#4a4f57");
const BULKHEAD = new THREE.Color("#a3a9b0");

export function bracketSize(d: BracketDesign): number {
  return Math.max(d.seat_length_mm * 1.8, (d.seat_thickness_mm + d.knee_depth_mm + d.pipe_od_mm) * 1.4, d.pipe_od_mm * 2.4, 160);
}

export function bracketCentreY(d: BracketDesign): number {
  return (d.knee_depth_mm + d.seat_thickness_mm + d.pipe_od_mm) / 2;
}

export function BracketModel({ design: d, showPipe = true }: { design: BracketDesign; showPipe?: boolean }) {
  const L = d.seat_length_mm;
  const ts = d.seat_thickness_mm;
  const lift = ts + d.knee_depth_mm;
  const x0 = -L / 2;

  const knee = useMemo(() => {
    const s = new THREE.Shape();
    s.moveTo(0, 0);
    s.lineTo(L, 0);
    s.lineTo(0, -d.knee_depth_mm);
    s.lineTo(0, 0);
    const g = new THREE.ExtrudeGeometry(s, { depth: d.knee_thickness_mm, bevelEnabled: false });
    g.translate(0, 0, -d.knee_thickness_mm / 2);
    return g;
  }, [L, d.knee_depth_mm, d.knee_thickness_mm]);
  useEffect(() => () => knee.dispose(), [knee]);

  const bolt = useMemo(() => {
    const r = (d.pipe_od_mm + d.ubolt_diameter_mm) / 2;
    const pts: THREE.Vector3[] = [];
    pts.push(new THREE.Vector3(-r, -d.pipe_od_mm / 2 - ts - 12, 0));
    for (let i = 0; i <= 24; i++) {
      const a = Math.PI - (Math.PI * i) / 24;
      pts.push(new THREE.Vector3(r * Math.cos(a), r * Math.sin(a), 0));
    }
    pts.push(new THREE.Vector3(r, -d.pipe_od_mm / 2 - ts - 12, 0));
    const curve = new THREE.CatmullRomCurve3(pts, false, "catmullrom", 0.05);
    return new THREE.TubeGeometry(curve, 64, d.ubolt_diameter_mm / 2, 12, false);
  }, [d.pipe_od_mm, d.ubolt_diameter_mm, ts]);
  useEffect(() => () => bolt.dispose(), [bolt]);

  const zKnee = d.seat_width_mm / 2 - d.knee_thickness_mm / 2;
  const pipeLength = Math.max(d.seat_width_mm * 4, d.pipe_od_mm * 3);
  return (
    <group>
      <mesh position={[x0 - 4, lift / 2 + d.pipe_od_mm / 2, 0]}>
        <boxGeometry args={[8, lift + d.pipe_od_mm + 60, pipeLength]} />
        <meshStandardMaterial color={BULKHEAD} roughness={0.9} />
      </mesh>
      <mesh position={[x0 + L / 2, lift - ts / 2, 0]} castShadow receiveShadow>
        <boxGeometry args={[L, ts, d.seat_width_mm]} />
        <meshStandardMaterial color={STEEL} metalness={0.55} roughness={0.42} />
      </mesh>
      {[-1, 1].map((side) => (
        <mesh key={side} geometry={knee} position={[x0, lift - ts, side * zKnee]} castShadow>
          <meshStandardMaterial color={KNEE} metalness={0.55} roughness={0.45} />
        </mesh>
      ))}
      {showPipe && (
        <group position={[x0 + d.pipe_offset_mm, lift + d.pipe_od_mm / 2, 0]}>
          <mesh rotation={[Math.PI / 2, 0, 0]}>
            <cylinderGeometry args={[d.pipe_od_mm / 2, d.pipe_od_mm / 2, pipeLength, 40, 1, true]} />
            <meshStandardMaterial color={PIPE} metalness={0.3} roughness={0.5} transparent opacity={0.55} side={THREE.DoubleSide} />
          </mesh>
          <mesh geometry={bolt}>
            <meshStandardMaterial color={BOLT} metalness={0.3} roughness={0.5} />
          </mesh>
        </group>
      )}
    </group>
  );
}
