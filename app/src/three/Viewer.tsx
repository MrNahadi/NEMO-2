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

/** Moves the camera so the part + hardware in the scene fills the view, whenever the part size changes:
 *  smoothly, or in one jump when the system asks for reduced motion. The fit is measured from the scene
 *  itself (the bounding box of every mesh that is not context geometry, floor or grid), so Model, Mesh
 *  and Stress and every preview frame the same way: the whole part, sling included, centred with an 8%
 *  safe area (about 32 px on a 400 px side) on the limiting axis (I2). */
function FitCamera({ size, centreY, reduce }: { size: number; centreY: number; reduce: boolean }) {
  const { camera, size: canvas, scene } = useThree();
  const controls = useThree((s) => s.controls) as OrbitControlsImpl | null;
  const goal = useRef(new THREE.Vector3());
  const last = useRef("");
  const frames = useRef(0);
  const fit = useRef<{ target: THREE.Vector3; extents: THREE.Vector3 | null; diag: number }>({
    target: new THREE.Vector3(),
    extents: null,
    diag: size,
  });
  useFrame(() => {
    // Restart the fit when the part size, the canvas size or the geometry itself changes (a preview or a
    // stress surface can arrive after the size is known, and must be framed too).
    let meshes = 0;
    scene.traverse((o) => {
      const obj = o as THREE.Object3D & { isMesh?: boolean; isLineSegments?: boolean };
      if (!obj.userData.excludeFit && (obj.isMesh || obj.isLineSegments)) meshes += 1;
    });
    const key = `${Math.round(size)}:${Math.round(centreY)}:${Math.round(canvas.width)}:${Math.round(canvas.height)}:${meshes}`;
    if (key !== last.current) {
      last.current = key;
      frames.current = reduce ? 3 : 70;
    }
    const t = reduce ? 1 : 0.1;
    if (frames.current <= 0) return;
    frames.current -= 1;
    // Measure the part + hardware in the scene every frame while the camera eases (the geometry boxes
    // are cached, so this is cheap, and world matrices are only valid once the first frame has rendered).
    const box = new THREE.Box3();
    scene.traverse((o) => {
      const obj = o as THREE.Object3D & { isMesh?: boolean; isLineSegments?: boolean };
      if (obj.userData.excludeFit || (!obj.isMesh && !obj.isLineSegments)) return;
      box.expandByObject(obj);
    });
    if (box.isEmpty()) {
      fit.current.target.set(0, centreY, 0);
      fit.current.extents = null;
      fit.current.diag = size;
    } else {
      box.getCenter(fit.current.target);
      fit.current.extents = box.getSize(new THREE.Vector3());
      fit.current.diag = fit.current.extents.length();
    }
    const aspect = canvas.width / Math.max(canvas.height, 1);
    const halfV = (((camera as THREE.PerspectiveCamera).fov ?? 35) * Math.PI) / 360;
    const halfH = Math.atan(Math.tan(halfV) * aspect);
    const target = fit.current.target;
    const direction = camera.position.clone().sub(controls?.target ?? target).normalize();
    if (direction.lengthSq() < 0.5) direction.set(0.55, 0.35, 0.75).normalize();
    let distance: number;
    const ext = fit.current.extents;
    if (ext) {
      // Perspective-exact box fit: every one of the 8 box corners must land inside the view, 8% in from
      // the edges. Corners nearer the camera loom larger, so each corner sets its own distance floor.
      const up = new THREE.Vector3(0, 1, 0);
      const right = new THREE.Vector3().crossVectors(direction, up).normalize();
      const upv = new THREE.Vector3().crossVectors(right, direction).normalize();
      const tanW = Math.tan(halfH) * 0.84;
      const tanH = Math.tan(halfV) * 0.84;
      distance = 0;
      const corner = new THREE.Vector3();
      for (let i = 0; i < 8; i++) {
        corner.set((i & 1 ? 0.5 : -0.5) * ext.x, (i & 2 ? 0.5 : -0.5) * ext.y, (i & 4 ? 0.5 : -0.5) * ext.z);
        const depth = corner.dot(direction);
        distance = Math.max(distance, depth + Math.abs(corner.dot(right)) / tanW, depth + Math.abs(corner.dot(upv)) / tanH);
      }
    } else {
      distance = size / (2 * Math.tan(Math.min(halfV, halfH)) * 0.84);
    }
    goal.current.copy(target).addScaledVector(direction, distance);
    camera.position.lerp(goal.current, t);
    if (controls) {
      controls.target.lerp(target, t);
      controls.update();
    }
    const cam = camera as THREE.PerspectiveCamera;
    cam.near = Math.max(fit.current.diag / 100, 0.5);
    cam.far = fit.current.diag * 50 + distance * 4;
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
  status,
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
  /** Centred status overlay (loading chip or error panel) over the canvas; the panel frame stays put. */
  status?: ReactNode;
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
          {/* Key light capped at 1.35 (was 1.6): brighter light blew out to a white patch on flat steel
              faces such as the bracket seat plate (I3). */}
          <directionalLight position={[size, size * 2, size * 1.5]} intensity={1.35} castShadow />
          {/* Rim light from behind: gives dark hardware (shackle, stock, U-bolt) an edge against the black dark-theme background. */}
          <directionalLight position={[-size, size, -size]} intensity={dark ? 1.2 : 0.4} />
          <directionalLight position={[-size * 1.5, size * 0.4, size * 0.5]} intensity={dark ? 0.6 : 0.2} />
          {children}
          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -3.1, 0]} receiveShadow userData={{ excludeFit: true }}>
            <planeGeometry args={[size * 6, size * 6]} />
            <shadowMaterial transparent opacity={colours.shadow} />
          </mesh>
          <gridHelper key={dark ? "d" : "l"} args={[grid * 40, 40, colours.major, colours.minor]} position={[0, -3, 0]} userData={{ excludeFit: true }} />
          <OrbitControls makeDefault enablePan={false} enableDamping={!reduce} minDistance={size * 0.4} maxDistance={size * 8} />
          <FitCamera size={size} centreY={centreY} reduce={reduce} />
        </Canvas>
        {toolbar && <div className="viewer-toolbar">{toolbar}</div>}
        {top && <div className="viewer-top">{top}</div>}
        {status && <div className="viewer-status">{status}</div>}
      </div>
      {overlay && <div className="viewer-readouts">{overlay}</div>}
    </div>
  );
}
