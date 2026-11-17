import type { PadeyeJob } from "./types";

export type Problems = Partial<Record<"mass" | "points" | "carrying" | "angle" | "plates" | "dynamic" | "side" | "oblique", string>>;

/** Same rules as the engine, checked as you type so mistakes are explained next to the question. */
export function problems(job: PadeyeJob): Problems {
  const p: Problems = {};
  const l = job.lift;
  if (!(l.lifted_mass_kg > 0)) p.mass = "Enter the weight of the load. It must be more than 0.";
  else if (l.lifted_mass_kg > 2_000_000) p.mass = "That is more than 2,000 t. Check the number and the unit.";
  if (!(l.lift_points >= 1)) p.points = "There must be at least 1 lifting point.";
  if (l.points_carrying !== null && (l.points_carrying < 1 || l.points_carrying > l.lift_points))
    p.carrying = `Choose between 1 and ${l.lift_points}.`;
  if (!(l.sling_angle_deg >= 15 && l.sling_angle_deg <= 90)) p.angle = "Use an angle between 15° and 90° from horizontal.";
  if (job.plate_thicknesses_mm.length === 0) p.plates = "Tick at least one plate thickness.";
  if (!(l.dynamic_factor >= 1)) p.dynamic = "The dynamic factor cannot be less than 1.0.";
  if (!(l.side_load_fraction >= 0 && l.side_load_fraction <= 0.5)) p.side = "Use between 0% and 50%.";
  const beta = l.out_of_plane_angle_deg ?? 0;
  if (!(beta >= 0 && beta <= 90)) p.oblique = "Use an angle between 0° and 90°.";
  return p;
}

export function isValid(job: PadeyeJob): boolean {
  return Object.keys(problems(job)).length === 0;
}
