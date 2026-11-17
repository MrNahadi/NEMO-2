export interface Lift {
  lifted_mass_kg: number;
  lift_points: number;
  sling_angle_deg: number;
  dynamic_factor: number;
  points_carrying: number | null;
  side_load_fraction: number;
}

export interface PadeyeJob {
  part: "padeye";
  lift: Lift;
  material_id: string;
  plate_thicknesses_mm: number[];
  allow_cheek_plates: boolean;
  rule_set_id: string;
  design_category: "A" | "B";
  service_class: number;
  fill_shackle_jaw: boolean;
  electrode_strength_mpa: number;
}

export interface BracketJob {
  part: "pipe-bracket";
  pipe_nps: string;
  schedule: "STD" | "XS";
  pipe_material_id: string;
  fluid_id: string;
  insulation_id: string;
  insulation_thickness_mm: number;
  span_m: number;
  continuity_factor: number;
  pipe_direction: "fore_aft" | "athwartships";
  accel_vertical_g: number;
  accel_transverse_g: number;
  accel_longitudinal_g: number;
  friction: number;
  gap_mm: number;
  material_id: string;
  plate_thicknesses_mm: number[];
  ubolt_grade_id: string;
  propeller_rpm: number;
  propeller_blades: number;
  engine_rpm: number;
  engine_cylinders: number;
  engine_stroke: 2 | 4;
  frequency_margin: number;
  deflection_limit_mm: number;
  electrode_strength_mpa: number;
  rule_set_id: string;
}

export interface FinJob {
  part: "stabilizer";
  speed_kn: number;
  span_m: number;
  chord_m: number;
  thickness_ratio: number;
  max_angle_deg: number;
  stock_position: number;
  depth_m: number;
  draught_m: number;
  bearing_gap_mm: number;
  material_id: string;
  stock_material_id: string;
  plate_thicknesses_mm: number[];
  front_spar: number;
  rear_spar: number;
  deflection_limit_mm: number;
  rule_set_id: string;
}

export type Job = PadeyeJob | BracketJob | FinJob;
export type PartId = Job["part"];

export interface BracketDesign {
  seat_length_mm: number;
  seat_width_mm: number;
  seat_thickness_mm: number;
  knee_depth_mm: number;
  knee_thickness_mm: number;
  pipe_offset_mm: number;
  pipe_od_mm: number;
  ubolt_diameter_mm: number;
  root_weld_mm: number;
  knee_weld_mm: number;
}

export interface FinDesign {
  span_mm: number;
  chord_mm: number;
  thickness_ratio: number;
  stock_position: number;
  front_spar: number;
  rear_spar: number;
  skin_mm: number;
  web_mm: number;
  rib_spacing_mm: number;
  stock_diameter_mm: number;
  bearing_gap_mm: number;
}

export interface SpanInfo {
  natural_hz: number;
  excitations: { name: string; hz: number }[];
  nearest: { name: string; hz: number };
  separation: number;
  recommended_m: number;
  spans_m: { stress: number; sag: number; frequency: number };
  steps: WorkingStep[];
}

export interface Piping {
  pipes: { nps: string; dn: number; od_mm: number; wall_mm: Record<string, number> }[];
  pipe_materials: { id: string; name: string }[];
  fluids: { id: string; name: string; density_kg_m3: number }[];
  insulation: { id: string; name: string; density_kg_m3: number }[];
  ubolt_grades: { id: string; name: string }[];
}

export interface Material {
  id: string;
  name: string;
  family: string;
  source: string;
  tensile_strength_mpa: number;
  yield_bands: { max_thickness_mm: number; yield_strength_mpa: number }[];
}

export interface Reference {
  materials: Material[];
  plates: { steel_mm: number[]; aluminium_mm: number[]; default_selected_mm: number[] };
  shackles: { size_in: string; wll_t: number; jaw_width_mm: number; pin_diameter_mm: number }[];
  rule_sets: { id: string; name: string }[];
  part_rule_sets: Record<string, string[]>;
  default_job: PadeyeJob;
  parts: Record<PartId, { title: string; default_job: Job }>;
  piping: Piping;
}

export interface PadeyeDesign {
  main_thickness_mm: number;
  head_radius_mm: number;
  hole_diameter_mm: number;
  base_length_mm: number;
  hole_height_mm: number;
  weld_leg_mm: number;
  cheek_thickness_mm: number;
  cheek_radius_mm: number;
  cheek_weld_leg_mm: number;
}

export interface WorkingStep {
  label: string;
  symbol: string;
  formula: string;
  substituted: string;
  value: number;
  unit: string;
  result: string;
  note: string;
}

export interface Check {
  id: string;
  title: string;
  demand: number;
  capacity: number;
  unit: string;
  utilization: number;
  passed: boolean;
  margin_percent: number;
  source: string;
  explanation: string;
  basis: "rule" | "practice";
  severity: "required" | "advice";
  category: "strength" | "fit";
  working: WorkingStep[];
}

export interface Loads {
  sling_force_n: number;
  sling_force_t: number;
  vertical_n: number;
  horizontal_n: number;
  side_n: number;
  sling_angle_deg: number;
}

export interface CheckReport {
  passed: boolean;
  governing: string;
  mass_kg: number;
  design: PadeyeDesign;
  material: string;
  shackle: { label: string; wll_t: number; jaw_width_mm: number; pin_diameter_mm: number };
  loads: Loads;
  checks: Check[];
  values?: Record<string, number>;
  // Bracket
  pipe?: { label: string; od_mm: number; wall_mm: number; material: string };
  ubolt?: { label: string; thread: string; diameter_mm: number };
  span?: SpanInfo;
  // Fin
  masses_kg?: Record<string, number>;
  stock_material?: { id: string; name: string };
  ribs?: number;
  rib_pitch_mm?: number;
}

/** The design dimensions of any part. Read them with the part's own type. */
export type AnyDesign = PadeyeDesign | BracketDesign | FinDesign;

export type Preview =
  | (CheckReport & { feasible: true; outline: [number, number][]; load_steps: WorkingStep[] })
  | { feasible: false; reason: string; loads: Loads };

export interface FeaLevel {
  level: number;
  elements: number;
  head_von_mises_mpa: number;
  max_displacement_mm: number;
  reaction_balance_error: number;
  global_size_mm: number;
  local_size_mm: number;
}

export interface FeaSummary {
  head_von_mises_mpa: number;
  factor_of_safety_on_yield: number;
  yield_strength_mpa: number;
  convergence_change: number;
  converged: boolean;
  levels: FeaLevel[];
  region?: string;
  hand_stress_mpa?: number | null;
  hand_label?: string;
}

export interface DesignResult {
  key: "lightest" | "balanced" | "robust";
  label: string;
  target_utilization: number;
  check_report: CheckReport;
  cad_volume_mm3: number;
  fea: FeaSummary | null;
  files: { step: string; stl: string; dxf: string; stress_surface: string | null };
}

export interface Results {
  part?: PartId;
  job: Job;
  loads: Loads;
  load_steps?: WorkingStep[];
  material: { id: string; name: string };
  search: { combinations: number; evaluations: number; skipped: number };
  designs: DesignResult[];
  files?: { engineering_log: string; designs_evaluated: string };
  seconds: number;
}

export interface Project {
  id: string;
  name: string;
  part: string;
  created_at: string;
  updated_at: string | null;
  inputs: Job | null;
  runs: string[];
  results?: Results | null;
  latest_run?: string | null;
}

export interface RunStatus {
  id: string;
  project_id: string;
  state: "queued" | "running" | "done" | "failed";
  message: string;
  fraction: number;
  run_name: string | null;
  error: string | null;
  events: EngEvent[];
  next: number;
  result?: VerificationResult;
}

/** One engineering event from the engine. Fields depend on `kind`. */
export interface EngEvent {
  seq: number;
  t: number;
  kind: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [key: string]: any;
}

export interface SurfaceMesh {
  positions: number[];
  triangles: number[];
}

export interface Comparison {
  quantity: string;
  reference: number;
  nemo: number;
  unit: string;
  error_percent: number;
  tolerance_percent: number;
  passed: boolean;
}

export interface Benchmark {
  id: string;
  title: string;
  description: string;
  source: string;
  setup: WorkingStep[];
  comparisons: Comparison[];
  mesh: { elements: number; equations: number } | null;
  passed: boolean;
  error: string | null;
  seconds: number;
}

export interface VerificationResult {
  nemo_version: string;
  ran_at: string;
  passed: boolean;
  benchmarks: Benchmark[];
}

export interface StressSurface {
  positions: number[];
  triangles: number[];
  von_mises: number[];
  max_von_mises: number;
}

export interface FusionStatus {
  installed: boolean;
  installed_version: string | null;
  current_version: string;
  update_available: boolean;
  connected: boolean;
  seconds_since_seen: number | null;
  fusion_version: string | null;
  connector_version: string | null;
  addins_folder: string;
  activity: { kind: string; message: string; at: string; passed?: boolean; project_id?: string }[];
}

export interface FusionJob {
  id: string;
  kind: string;
  state: "waiting" | "sent" | "done" | "failed" | "expired";
  result: FusionModel | null;
  error: string | null;
}

export interface FusionModel {
  volume_mm3: number;
  nemo_volume_mm3: number;
  volume_difference: number | null;
  fusion_mass_kg: number;
  nemo_mass_kg: number;
  fusion_material: string | null;
  fusion_yield_mpa?: number | null;
  material_matches?: boolean;
  material_warnings?: string[];
  parametric: boolean;
  warnings?: string[];
  fusion_version: string;
  recorded_at: string;
}

export interface FusionCheckResult {
  ok: boolean;
  passed: boolean;
  mass_kg: number;
  nemo_mass_kg: number;
  governing: { title: string; use: number };
  changed: Record<string, { from: number; to: number }>;
  checks: { id: string; title: string; use: number; passed: boolean; severity: string }[];
  checked_at: string;
}

export interface FusionCrossCheck {
  reaction_n: number | null;
  peak_stress_mpa: number | null;
  max_displacement_mm: number | null;
  checked_by: string;
  nemo_reaction_n: number | null;
  nemo_peak_stress_mpa: number | null;
  nemo_max_displacement_mm: number | null;
  reaction_difference: number | null;
  stress_difference: number | null;
  displacement_difference: number | null;
  agrees: boolean;
  recorded_at: string;
}

export interface FusionRecords {
  model: FusionModel | null;
  checks: FusionCheckResult[];
  crosscheck: FusionCrossCheck | null;
}
