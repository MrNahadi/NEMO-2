import { OrbitControls } from "@react-three/drei";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { useEffect, useRef, useState, type ReactNode } from "react";
import * as THREE from "three";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";

function useDarkTheme(): boolean {
  const read = () => document.documentElement.dataset.theme === "dark";
  const [dark, setDark] = useState(read);
  useEffect(() => {
    const mo = new MutationObserver(() => setDark(read()));
    mo.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => mo.disconnect();
  }, []);
  return dark;
}

/** True while the system asks for reduced motion; follows changes to the setting. */
function useReducedMotion(): boolean {
  const query = "(prefers-reduced-motion: reduce)";
  const [reduce, setReduce] = useState(() => window.matchMedia(query).matches);
  useEffect(() => {
    const mq = window.matchMedia(query);
    const on = () => setReduce(mq.matches);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);
  return reduce;
}

/** Moves the camera so a part of the given size (mm) fills the view, whenever the size changes: smoothly,
 *  or in one jump when the system asks for reduced motion. */
function FitCamera({ size, centreY, reduce }: { size: number; centreY: number; reduce: boolean }) {
  const { camera, size: canvas } = useThree();
  const controls = useThree((s) => s.controls) as OrbitControlsImpl | null;
  const goal = useRef(new THREE.Vector3());
  const last = useRef("");
  const frames = useRef(0);
  useFrame(() => {
    const key = `${Math.round(size)}:${Math.round(centreY)}:${Math.round(canvas.width)}:${Math.round(canvas.height)}`;
    if (key !== last.current) {
      last.current = key;
      frames.current = reduce ? 3 : 70;
    }
    const t = reduce ? 1 : 0.1;
    if (frames.current <= 0) return;
    frames.current -= 1;
    const aspect = canvas.width / Math.max(canvas.height, 1);
    const distance = size * 2.1 * Math.max(1, 0.9 / Math.max(aspect, 0.3)); // narrow views need more room across
    const target = new THREE.Vector3(0, centreY, 0);
    const direction = camera.position.clone().sub(controls?.target ?? target).normalize();
    if (direction.lengthSq() < 0.5) direction.set(0.55, 0.35, 0.75).normalize();
    goal.current.copy(target).addScaledVector(direction, distance);
    camera.position.lerp(goal.current, t);
    if (controls) {
      controls.target.lerp(target, t);
      controls.update();
    }
    const cam = camera as THREE.PerspectiveCamera;
    cam.near = size / 100;
    cam.far = size * 50;
    cam.updateProjectionMatrix();
  });
  return null;
}

/** The 3D view as one bordered panel: canvas, an optional toolbar (top left), an optional legend (top right)
 *  and an optional readout strip attached to the bottom edge. Fills its container's height. */
export function Viewer({
  size,
  centreY,
  children,
  overlay,
  top,
  toolbar,
}: {
  size: number;
  centreY: number;
  children: ReactNode;
  /** Readouts shown in a strip along the bottom edge (children are .viewer-chip cells). */
  overlay?: ReactNode;
  /** Legend or status, top right. */
  top?: ReactNode;
  /** Controls such as the Model / Mesh / Stress switch, top left. */
  toolbar?: ReactNode;
}) {
  const dark = useDarkTheme();
  const reduce = useReducedMotion();
  const grid = Math.max(50, Math.pow(10, Math.ceil(Math.log10(size))) / 10);
  // Geist background-200 behind the part; grid lines from the gray scale; the floor only catches the shadow.
  const colours = dark
    ? { bg: "#000000", major: "#2E2E2E", minor: "#1A1A1A", shadow: 0.5 }
    : { bg: "#FAFAFA", major: "#E3E3E3", minor: "#EFEFEF", shadow: 0.14 };
  return (
    <div className="viewer-panel">
      <div className="viewer" aria-label="3D view of the part. Drag to turn it, scroll to zoom.">
        <Canvas shadows dpr={[1, 2]} camera={{ fov: 35, position: [size * 1.1, size * 0.9, size * 1.5] }}>
          <color attach="background" args={[colours.bg]} />
          <hemisphereLight args={["#ffffff", dark ? "#3a3a3a" : "#d4d4d4", dark ? 0.9 : 1.1]} />
          <directionalLight position={[size, size * 2, size * 1.5]} intensity={1.6} castShadow />
          {/* Rim light from behind: gives dark hardware (shackle, stock, U-bolt) an edge against the black dark-theme background. */}
          <directionalLight position={[-size, size, -size]} intensity={dark ? 1.4 : 0.5} />
          <directionalLight position={[-size * 1.5, size * 0.4, size * 0.5]} intensity={dark ? 0.6 : 0.2} />
          {children}
          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -3.1, 0]} receiveShadow>
            <planeGeometry args={[size * 6, size * 6]} />
            <shadowMaterial transparent opacity={colours.shadow} />
          </mesh>
          <gridHelper key={dark ? "d" : "l"} args={[grid * 40, 40, colours.major, colours.minor]} position={[0, -3, 0]} />
          <OrbitControls makeDefault enablePan={false} enableDamping={!reduce} minDistance={size * 0.4} maxDistance={size * 8} />
          <FitCamera size={size} centreY={centreY} reduce={reduce} />
        </Canvas>
        {toolbar && <div className="viewer-toolbar">{toolbar}</div>}
        {top && <div className="viewer-top">{top}</div>}
      </div>
      {overlay && <div className="viewer-readouts">{overlay}</div>}
    </div>
  );
}
