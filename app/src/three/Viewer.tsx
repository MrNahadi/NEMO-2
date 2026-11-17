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

/** Moves the camera smoothly so a part of the given size (mm) fills the view, whenever the size changes. */
function FitCamera({ size, centreY }: { size: number; centreY: number }) {
  const { camera, size: canvas } = useThree();
  const controls = useThree((s) => s.controls) as OrbitControlsImpl | null;
  const goal = useRef(new THREE.Vector3());
  const last = useRef("");
  const frames = useRef(0);
  useFrame(() => {
    const key = `${Math.round(size)}:${Math.round(centreY)}:${Math.round(canvas.width)}:${Math.round(canvas.height)}`;
    if (key !== last.current) {
      last.current = key;
      frames.current = 70;
    }
    if (frames.current <= 0) return;
    frames.current -= 1;
    const aspect = canvas.width / Math.max(canvas.height, 1);
    const distance = size * 2.1 * Math.max(1, 0.9 / Math.max(aspect, 0.3)); // narrow views need more room across
    const target = new THREE.Vector3(0, centreY, 0);
    const direction = camera.position.clone().sub(controls?.target ?? target).normalize();
    if (direction.lengthSq() < 0.5) direction.set(0.55, 0.35, 0.75).normalize();
    goal.current.copy(target).addScaledVector(direction, distance);
    camera.position.lerp(goal.current, 0.1);
    if (controls) {
      controls.target.lerp(target, 0.1);
      controls.update();
    }
    const cam = camera as THREE.PerspectiveCamera;
    cam.near = size / 100;
    cam.far = size * 50;
    cam.updateProjectionMatrix();
  });
  return null;
}

export function Viewer({
  size,
  centreY,
  children,
  overlay,
  top,
}: {
  size: number;
  centreY: number;
  children: ReactNode;
  overlay?: ReactNode;
  top?: ReactNode;
}) {
  const dark = useDarkTheme();
  const grid = Math.max(50, Math.pow(10, Math.ceil(Math.log10(size))) / 10);
  const colours = dark
    ? { bg: "#16181b", floor: "#1d2024", major: "#30353b", minor: "#25292e" }
    : { bg: "#f4f5f7", floor: "#e3e6ea", major: "#c6ccd4", minor: "#d6dbe1" };
  return (
    <div className="viewer" aria-label="3D view of the part. Drag to turn it, scroll to zoom.">
      <Canvas shadows dpr={[1, 2]} camera={{ fov: 35, position: [size * 1.1, size * 0.9, size * 1.5] }}>
        <color attach="background" args={[colours.bg]} />
        <hemisphereLight args={["#ffffff", dark ? "#3a4048" : "#c9ced6", dark ? 0.9 : 1.1]} />
        <directionalLight position={[size, size * 2, size * 1.5]} intensity={1.6} castShadow />
        <directionalLight position={[-size, size, -size]} intensity={0.5} />
        {children}
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -3.1, 0]} receiveShadow>
          <planeGeometry args={[size * 6, size * 6]} />
          <meshStandardMaterial color={colours.floor} roughness={0.95} />
        </mesh>
        <gridHelper key={dark ? "d" : "l"} args={[grid * 40, 40, colours.major, colours.minor]} position={[0, -3, 0]} />
        <OrbitControls makeDefault enablePan={false} minDistance={size * 0.4} maxDistance={size * 8} />
        <FitCamera size={size} centreY={centreY} />
      </Canvas>
      {top && <div className="viewer-top">{top}</div>}
      {overlay && <div className="viewer-overlay">{overlay}</div>}
    </div>
  );
}
