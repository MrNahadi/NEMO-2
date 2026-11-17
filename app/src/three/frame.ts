/**
 * Placing an engine model (x, y, z with z up) in the viewer (y up): centred across, resting on the floor.
 * The padeye already sits that way, so it moves by nothing; the bracket and the fin stock get shifted.
 */
export interface Frame {
  dx: number;
  dz: number;
  lift: number;
  size: number;
  centreY: number;
}

export function frameOf(positions: number[]): Frame {
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity, minZ = Infinity, maxZ = -Infinity;
  for (let i = 0; i < positions.length; i += 3) {
    const x = positions[i], y = positions[i + 1], z = positions[i + 2];
    if (x < minX) minX = x;
    if (x > maxX) maxX = x;
    if (y < minY) minY = y;
    if (y > maxY) maxY = y;
    if (z < minZ) minZ = z;
    if (z > maxZ) maxZ = z;
  }
  if (!Number.isFinite(minX)) return { dx: 0, dz: 0, lift: 0, size: 100, centreY: 50 };
  const height = maxZ - minZ;
  return {
    dx: -(minX + maxX) / 2,
    dz: -(minY + maxY) / 2,
    lift: -minZ,
    size: Math.max(maxX - minX, maxY - minY, height, 60),
    centreY: height / 2,
  };
}

/** Engine positions to viewer positions using a frame. */
export function toViewer(p: number[], f: Frame): Float32Array {
  const out = new Float32Array(p.length);
  for (let i = 0; i < p.length; i += 3) {
    out[i] = p[i] + f.dx;
    out[i + 1] = p[i + 2] + f.lift;
    out[i + 2] = p[i + 1] + f.dz;
  }
  return out;
}
