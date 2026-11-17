import { useEffect, useMemo } from "react";
import * as THREE from "three";
import type { SurfaceMesh } from "../types";
import { frameOf, toViewer } from "./frame";

/** The FEA mesh drawn as a wireframe over a faint solid. Engine axes are swapped to the viewer's y-up. */
export function MeshModel({ mesh }: { mesh: SurfaceMesh }) {
  const { geometry, edges } = useMemo(() => {
    const positions = toViewer(mesh.positions, frameOf(mesh.positions));
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    g.setIndex(mesh.triangles);
    g.computeVertexNormals();
    return { geometry: g, edges: new THREE.WireframeGeometry(g) };
  }, [mesh]);
  useEffect(() => () => {
    geometry.dispose();
    edges.dispose();
  }, [geometry, edges]);
  return (
    <group>
      <mesh geometry={geometry}>
        <meshStandardMaterial color="#d6dbe1" roughness={0.9} polygonOffset polygonOffsetFactor={1} polygonOffsetUnits={1} />
      </mesh>
      <lineSegments geometry={edges}>
        <lineBasicMaterial color="#2a3340" transparent opacity={0.55} />
      </lineSegments>
    </group>
  );
}
