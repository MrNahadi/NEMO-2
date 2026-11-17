# Engineering manual

For supervisors, checkers and surveyors. Describes every calculation NEMO makes,
its source, and how it was verified. Units: N, mm, MPa, kg.

## 1. Loads on one padeye

| Quantity | Expression |
| --- | --- |
| Vertical force | V = m g DAF / n<sub>c</sub>, g = 9.80665 m/s² |
| Sling force | F = V / sin θ |
| In-plane horizontal | H = F cos θ |
| Sideways (out of plane) | Q = k F |

m: lifted mass; DAF: user dynamic factor (default 1.0); n<sub>c</sub>: points
assumed to carry the load (default all); θ: sling angle from horizontal (15° to
90°); k: sideways allowance (default 0.05). The padeye plate is assumed to lie in
the plane of its sling.

## 2. Padeye geometry

Main plate outline: convex hull of the base line (length L) and the head circle
(radius R, centre at hole height h). Hole diameter D<sub>h</sub>. Optional cheek
plates: two rings of thickness t<sub>c</sub>, outer radius R<sub>c</sub> ≤ R.
Total thickness at the hole t = t<sub>main</sub> + 2 t<sub>c</sub>.

Area is computed exactly (polygon of base corners, tangent points and centre,
plus the head sector, minus the hole). Mass = volume × density; weld metal is
not included.

## 3. ASME BTH-1 checks

Design factor N<sub>d</sub> = 2.00 (category A) or 3.00 (category B). Pin-connected
plate strengths use 1.20 N<sub>d</sub>. F<sub>y</sub>: minimum yield for the plate
thickness; F<sub>u</sub>: minimum tensile strength; D<sub>p</sub>: shackle pin
diameter.

For the concentric round head, edge distance R and net width b<sub>e</sub> =
R − D<sub>h</sub>/2 are the same in every in-plane direction, so the head checks
use the full sling force F regardless of sling angle. With cheek plates, R is the
smaller of R and R<sub>c</sub> and the yield is the lower of the two plates.

| Check | Allowable |
| --- | --- |
| Strength reduction | C<sub>r</sub> = 1 − 0.275 √(1 − D<sub>p</sub>²/D<sub>h</sub>²) |
| Effective width | b<sub>eff</sub> = min(b<sub>e</sub>, 4t, 0.6 (F<sub>u</sub>/F<sub>y</sub>) √(D<sub>h</sub>/b<sub>e</sub>) b<sub>e</sub>) |
| Tension through pinhole | P<sub>t</sub> = C<sub>r</sub> F<sub>u</sub> 2 t b<sub>eff</sub> / (1.20 N<sub>d</sub>) |
| Fracture beyond pinhole | P<sub>b</sub> = C<sub>r</sub> F<sub>u</sub> [1.13 (R − D<sub>h</sub>/2) + 0.92 b<sub>e</sub>/(1 + b<sub>e</sub>/D<sub>h</sub>)] t / (1.20 N<sub>d</sub>) |
| Double plane shear | P<sub>v</sub> = 0.70 F<sub>u</sub> A<sub>v</sub> / (1.20 N<sub>d</sub>), A<sub>v</sub> = 2 [a + D<sub>p</sub>/2 (1 − cos φ) − Z] t, φ = 55 D<sub>p</sub>/D<sub>h</sub> degrees, Z = r − √(r² − (D<sub>p</sub>/2 · sin φ)²), a = R − D<sub>h</sub>/2, r = R |
| Pin bearing | P<sub>p</sub> = C F<sub>y</sub> D<sub>p</sub> t / N<sub>d</sub>, C = 1.25 (service class 0) or 0.63 (classes 1 to 4) |

Base section (main plate only, L × t<sub>main</sub>), cantilever of length h:

| Stress | Expression | Allowable |
| --- | --- | --- |
| Axial | f<sub>a</sub> = V / (L t) | F<sub>t</sub> = F<sub>y</sub>/N<sub>d</sub> |
| In-plane bending | f<sub>bx</sub> = H h / (t L²/6) | F<sub>bx</sub> = rectangular bar, strong axis, with lateral-torsional buckling (below) |
| Sideways bending | f<sub>by</sub> = Q h / (L t²/6) | F<sub>by</sub> = 1.25 F<sub>y</sub>/N<sub>d</sub> |
| Combined | f<sub>a</sub>/F<sub>t</sub> + f<sub>bx</sub>/F<sub>bx</sub> + f<sub>by</sub>/F<sub>by</sub> ≤ 1 | |
| Shear | f<sub>v</sub> = √(H² + Q²) / (L t) | F<sub>v</sub> = F<sub>y</sub>/(√3 N<sub>d</sub>) |

F<sub>bx</sub>, with λ = L<sub>b</sub> d / t² (L<sub>b</sub> = h, d = L, C<sub>b</sub> = 1):
1.25 F<sub>y</sub>/N<sub>d</sub> for λ ≤ 0.08 E/F<sub>y</sub>;
[1.52 − 0.274 λ F<sub>y</sub>/E] F<sub>y</sub>/N<sub>d</sub> (≤ 1.25 F<sub>y</sub>/N<sub>d</sub>) up to 1.9 E/F<sub>y</sub>;
1.9 E/λ /N<sub>d</sub> beyond.

Welds: allowable shear on the throat F<sub>w</sub> = 0.60 E<sub>xx</sub>/(1.20 N<sub>d</sub>),
E<sub>xx</sub> = 482 MPa (E70XX/E7018 class) by default.

- Base weld: two fillet lines of length L, throat a = 0.707 w, centrelines
  t<sub>main</sub> + a apart. Normal stress from V, H h and Q h on the weld group
  section; shear from √(H² + Q²); combined as the vector resultant on the throat.
- Cheek welds: each cheek carries F × t<sub>c</sub>/t through one fillet around its
  circumference 2πR<sub>c</sub>.

Practice checks (marked "NEMO practice" in reports):

| Check | Rule | Severity |
| --- | --- | --- |
| Hole clearance | D<sub>h</sub> ≥ D<sub>p</sub> + 1 mm | Required |
| Shackle fit | t + 2 mm ≤ jaw width | Required |
| Shackle rating | F / g ≤ WLL | Required |
| Jaw fill | t ≥ 0.6 × jaw width | Advice (a sizing constraint by default) |
| Pin fit | D<sub>p</sub>/D<sub>h</sub> ≥ 0.90 | Advice |
| Minimum fillet | AWS D1.1 table: 3 / 5 / 6 / 8 mm for parts up to 6 / 12 / 19 / over 19 mm | Advice |

Equation numbers are not quoted because they change between BTH-1 editions.
Check the expressions against the edition named for the job.

## 4. Sizing (optimisation)

1. Shackles: the smallest Crosby G-2130 with WLL ≥ F/g, and the next two sizes.
2. Hole: D<sub>h</sub> = D<sub>p</sub> + max(1 mm, 4%), rounded up to 0.5 mm.
3. For every stock main-plate thickness and cheek thickness (0 or ≤ main) that
   fits the shackle jaw, bounded Nelder-Mead varies R, L (2R to 8R) and R<sub>c</sub>
   to minimise mass × (1 + 1000 × Σ excess²), where excess is how far each
   required check is over its target. Hole height h = max(R, 2 D<sub>p</sub>) to clear
   the shackle.
4. Welds: smallest standard leg (3 to 20 mm) that passes and is at least the AWS
   minimum; base leg ≤ 0.75 t<sub>main</sub>; cheek leg ≤ t<sub>c</sub>.
5. Rounding up: R, R<sub>c</sub>, h to 1 mm, L to 5 mm; the design is grown in small
   steps until every check passes after rounding.
6. Three targets: 100%, 85% and 70% maximum use on strength checks.

## 5. Built-in FEA

- Geometry from the same build123d (OpenCASCADE) solid as the STEP file.
- Mesh: Gmsh, linear tetrahedra, refined near the hole; three mesh sizes (factors
  1.0, 0.7, 0.5).
- Elements: quadratic (P2) displacement, scikit-fem; isotropic linear elastic.
- Support: base face fixed in all directions.
- Load: cosine pressure p ∝ max(cos α, 0) on the hole surface, α measured from
  the sling direction, scaled so its resultant equals F; sideways load spread the
  same way, scaled to Q.
- Solver: direct (small models) or smoothed-aggregation AMG with conjugate
  gradients and rigid-body near-null space.
- Output: vertex-averaged von Mises stress. Reported peak is the maximum within
  R + 1 mm of the hole axis. Convergence = change between the two finest meshes
  (target ≤ 5%). Force balance = |applied + reaction| / |applied|.
- Acceptance: peak von Mises < F<sub>y</sub> and converged. The base edge where the
  fixed face meets the free faces is a known singularity and is not used.

## 6. Verification

Automated tests (`engine/tests`, 100+ tests) run on every change.

| Test | Expected | NEMO | Difference |
| --- | --- | --- | --- |
| Padeye hand calculation, all BTH-1 checks (4 t on 2 points, 60°, S355, t = 20) | See `test_padeye_hand_calc.py` | Matches | < 0.1% |
| CAD volume vs exact formula, 50 random designs | Formula | build123d solid | < 1e-9 |
| STEP export and re-import volume | Original solid | Re-imported | < 0.5% |
| Cantilever 200×20×20 mm, 1 kN: tip deflection (Timoshenko) | 0.9598 mm | 0.9522 mm | −0.8% |
| Same: bending stress at mid-span | 75.0 MPa | 77.0 MPa | +2.6% |
| Plate 200 mm wide, 20 mm hole, tension: K<sub>t</sub> (Heywood, gross) | 3.032 | 3.060 | +0.9% |
| Fast stiffness assembly vs scikit-fem reference | Reference | Matches | < 1e-12 |
| Padeye FEA force balance | 0 | < 1e-12 | |
| Padeye FEA mesh convergence (example: 89.31 / 89.22 / 89.26 MPa) | ≤ 5% | 0.05% | |

Still to do: compare with a published BTH-1 worked padeye example.

**Fusion cross-check.** A Fusion Static Stress study of the same design is an
independent check of the built-in FEA. The study is set up by hand (Fusion's API
cannot create or solve studies), using the values on the cross-check sheet. The
results are entered on the sheet inside Fusion or in report section 7. NEMO
counts the two as agreeing when the total reaction is within 2% of the applied
load and the peak von Mises stress near the hole is within 15% of NEMO's value.
Displacement is reported but not used, because it depends on how the support and
the weld are modelled.

## 7. Traceability

Every number NEMO reports can be traced to its inputs.

- **Fusion records.** When a design is built in Fusion, `fusion-model.json`
  stores Fusion's volume against NEMO's CAD volume, the Fusion version and the
  material assigned. **Check in NEMO** appends each edited-dimension check to
  `fusion-checks.json` (the latest 50) with the dimensions changed and every check result. A
  cross-check writes `fusion-crosscheck.json` with Fusion's and NEMO's values,
  the differences, the verdict and who checked it. The PDF is rebuilt after a
  new model record or cross-check so section 7 shows them.
- **Calculation working.** Each check carries its working: quantity, formula,
  formula with values substituted, result (`nemo.parts.padeye.working`). The
  same steps appear in the app and in the PDF report. A test confirms the
  working's results equal the values the checks use.
- **Engineering log.** Each run writes `engineering-log.json`: an ordered,
  time-stamped list of events (forces, shackle choice, every search combination,
  thinned samples of designs tried, CAD volumes, mesh statistics, solver residual
  history, force balance, mesh convergence). The app's live run screen is drawn
  from these events.
- **Every design tried.** `designs-evaluated.csv` lists every design the
  optimizer evaluated: target, shackle, plate and cheek thickness, head radius,
  cheek radius, base length, hole height, weld sizes, mass, highest check use,
  and whether it met the target.
- **Report checksums.** The PDF's audit trail lists the SHA-256 of each run file.
- **Verification on demand.** `nemo.verification` runs the benchmarks in
  section 6; the app's Verification page runs them on the user's computer and
  shows reference, NEMO value, difference and tolerance for each quantity.

## 8. Reference data

| Data | Source |
| --- | --- |
| S235, S275, S355 | EN 10025-2:2019, minimum yield by thickness band, minimum tensile |
| Grade A, AH36 | IACS UR W11 |
| 316L | EN 10088-2, hot-rolled plate |
| 5083-H111 | EN 485-2 (welded strength equals parent in this temper) |
| Shackles | Crosby G-2130 / S-2130 catalogue, 2019: dimension A (jaw width) and B (pin diameter) |

## 9. Pipe support bracket

Code: `engine/src/nemo/parts/bracket/`. Units mm, N, MPa.

**Geometry.** Seat plate L × b × t_s with its top at z = 0; two right-triangle
knees of thickness t_k flush with the seat edges, h_k deep at the bulkhead
(x = 0) and running to the seat tip. The pipe centre is e = gap + insulation +
D/2 from the bulkhead. U-bolt legs at x = e ± (D + d)/2 on the centre line,
holes d + 2 mm. Seat length L = e + (D + d)/2 + 1.5 d_hole, rounded up to 5 mm.

**Loads.** Weight per metre q = g (m_pipe + m_contents + m_insulation). On one
bracket W = k_c q S, with S the support spacing and k_c the continuity factor
(default 1.25, the middle support of a two-span continuous beam). Design forces
at the pipe: F_z = W (1 + a_v) down, F_u = W (a_v − 1) up when a_v > 1,
F_x = W a_h across the pipe (a_h is the athwartships acceleration for a
fore-and-aft pipe, and the fore-and-aft one otherwise), F_y = μ F_z along it.
The accelerations are user inputs; NEMO does not yet compute them from a class
method.

**Rule set.** AISC 360-16 ASD (`rules/aisc360.py`): Ω = 1.67 for tension,
flexure and shear yield; 2.00 for fillet welds (0.60 F_EXX on the throat) and
bolts (0.75 F_u tension, 0.45 F_u shear, on the threaded tensile area).

**Checks.**

| Check | Method |
| --- | --- |
| Arm bending | Section at x: seat flange plus two webs of depth h_k (1 − x/L). U(x) = F_x/(A F_t) + M_y/(S_min F_b) + M_z/(S_z F_b), with M_y = F_z (e − x) + F_x (D/2 − z̄) and M_z = F_y (e − x). Maximum over 61 stations from 0 to e. F_b at first yield (Z/S = 1), because the knees are not compact. |
| Arm shear | V / (2 t_k h(x) + b t_s), maximum over the stations, against 0.6 F_y / Ω. |
| Welds to the bulkhead | Line-weld group: two lines across the seat (top and bottom) and two per knee. f_n = N/A_w + M_y c/I_w + M_z (b/2)/I_wz; f_s = √(V² + F_y²)/A_w; resultant on the throat. |
| Knee-to-seat welds | Shear flow V Q / I_y at the root over four fillets. |
| Seat between the knees | Strip of width min(L, b − t_k) spanning b − t_k: M = max(F_z l/8, T l/4). F_b = 1.5 F_y / Ω (AISC F11, plates bent flat). |
| U-bolt | T = F_u/2 + F_x (D/2)/s per leg, V = F_x/2; (f_t/F_t)² + (f_v/F_v)² ≤ 1. Smallest size from the table that passes, but at least M10 below 60 mm OD, M12 below 170, M16 below 280, M20 above (NEMO practice). |
| Deflection | δ = ∫ F_z (e − x)²/(E I(x)) dx + ∫ F_z/(G A_v(x)) dx by Simpson's rule. Limit set per job (1 mm default). |
| Knee free edge (advice) | l_e ≤ 50 t_k √(235/F_y), NEMO practice after ship-structure bracket rules. |
| Pipe vibration | f_n = (π/2) √(EI/(m S⁴)) (simply supported span). Excitations: shaft rate, blade rate, twice blade rate, engine rate, firing rate (cylinders × rpm/60, halved for 4-stroke). Required separation from each: the frequency margin (20% default). |
| Pipe bending | σ = q_d S²/(10 Z) with q_d = q √((1 + a_v)² + a_h²), against F_y,pipe / 1.67. |
| Pipe sag (advice) | 5 q S⁴/(384 E I) ≤ 2.5 mm (MSS SP-58/69 style). |
| Recommended spacing (advice) | Smallest of the spans meeting the stress, the sag and f_n ≥ (1 + margin) × the highest excitation. |

Span checks have category `span`: the sizing search ignores them, because the
bracket's size cannot change them, but a failing one still fails the design.

**FEA.** The STEP solid; faces at x = 0 fixed; F_z, F_x and F_y as uniform
tractions on a strip of the seat top under the pipe (width the larger of D/4,
2.5 t_s and 1.5 element sizes). Mesh size 1.2 × the thinner plate (4 to 20 mm),
refined near the bulkhead. Peak von Mises read where x ≥ 1.5 × the thicker
plate, clear of the fixed-edge singularity. The report compares it with the
larger of the arm-bending and seat-bending hand stresses.

## 10. Stabilizer fin

Code: `engine/src/nemo/parts/stabilizer/` and `engine/src/nemo/hydro.py`.

**Loads.** Effective aspect ratio A_e = 2 b / c (the hull is a mirror plane).
Whicker and Fehlner (1958) lift: dC_L/dα = 0.9 · 2π A_e / (√(A_e² + 4) + 1.8)
per radian, C_L = (dC_L/dα) α + (C_Dc/A_e) α² with C_Dc = 0.8 (square tip).
L = ½ ρ V² A C_L with ρ = 1025 kg/m³. UR S10.2.1.1: C_R = K1 K2 K3 132 A V²
with K1 = (λ + 2)/3, λ = b²/A ≤ 2, K2 = 1.10 (NACA), K3 = 0.8 (outside the
propeller jet). Design force F = max(L, C_R). Torque Q = F c |0.33 − x_s/c|,
at least 0.1 F c (UR S10.2.1.2). Root moment F × 0.5 b; stock moment at the
outer bearing F (0.5 b + l_g).

**Panel method.** Hess-Smith: constant-strength sources on each of 160 panels
(cosine spacing) plus one vortex strength, Kutta condition at the trailing
edge. Verified against the exact flow round a circle (C_p,min = −3) and the
thick-foil lift slope 2π (1 + 0.77 t/c), within 1.1% for NACA 0012 and 1.6%
for NACA 0020 (Verification page). The section angle giving the fin's C_L sets
the pressure distribution; cavitation is flagged when −C_p,min exceeds
σ = (p_a + ρ g h − p_v)/(½ ρ V²).

**Rule set.** IACS UR S10 Rev.8 (2025) (`rules/iacs_s10.py`), material factor
k = (235/R_eH)^0.75 with R_eH ≤ min(0.7 σ_T, 450 MPa).

| Check | Method |
| --- | --- |
| Stock torsion | τ_t = 5.1 Q / D³ × 10³ ≤ 68/k (S10.4.1) |
| Stock combined | σ_b = 10.2 M / D³ × 10³, σ_e = √(σ_b² + 3 τ_t²) ≤ 118/k (S10.4.2) |
| Fin body | Box girder between the spars: I = 2 ∫ t y² ds + t_w (h_f³ + h_r³)/12; σ_b ≤ 110/k, web shear F/(t_w Σh) + q_t/t_w ≤ 50/k with Bredt shear flow q_t = Q/(2 A_box), skin σ_e ≤ 120/k (S10.5.1) |
| Plating | t ≥ 5.5 s β √((T + C_R 10⁻⁴/A) k) + 2.5 (S10.5.2); webs ≥ max(0.7 t, 8 mm) |
| Skin buckling | σ_cr = k_b π² E/(12(1 − ν²)) (t/b)², Johnson-Ostenfeld above F_y/2, factor 1.5 (NEMO practice) |
| Tip deflection | Point load at mid-span on a cantilever of the box I |
| Cavitation (advice) | −C_p,min ≤ σ |

**Sizing.** Stock: smallest 5 mm step meeting both stock checks at the
target use. Structure: every (skin, web) pair from stock with webs ≥ 8 mm, and
every rib spacing from 150 to 1000 mm in 25 mm steps; the lightest passing fin
is kept. The mass uses a thin-wall formula; the STEP solid's volume is within
about 4% of it.

**FEA.** The stock alone (a solid shaft from the outer bearing to 0.6 b),
fixed at the bearing face. The fin force and the twist are tractions on the
stock surface between 0.4 b and 0.6 b; the twist is scaled to the target
moment and the force load takes up any small net force it adds, so the
applied total is exact. The peak is read from half a diameter outboard of the
bearing to the loaded length and compared with beam theory at that section
(within 0.2% in the benchmark).
