(function () {
  "use strict";

  var React = window.React;
  var ReactDOM = window.ReactDOM;
  var h = React.createElement;
  var B = window.Bitfield;
  var DATA = window.NEMO_DATA;
  var PLOTS = window.NEMO_PLOTS;

  function fmt(n, digits) {
    return Number(n).toFixed(digits);
  }

  function fmtInt(n) {
    return Math.round(Number(n)).toLocaleString("en-US");
  }

  function fmtSci(n) {
    return Number(n).toExponential(2).replace("e-0", "e-");
  }

  function SvgPlot(name) {
    return h("div", { className: "nemo-vis-wrap" },
      h("div", {
        className: "nemo-svg-box",
        dangerouslySetInnerHTML: { __html: PLOTS[name] || "" }
      })
    );
  }

  function buildSlides() {
    var S = DATA.summary;
    var pad = DATA.runs["padeye"];
    var brk = DATA.runs["pipe-bracket"];
    var fin = DATA.runs["stabilizer"];

    var padLight = pad.designs.lightest;
    var padBal = pad.designs.balanced;
    var padExt = pad.designs.robust;
    var brkLight = brk.designs.lightest;
    var finLight = fin.designs.lightest;
    var finBal = fin.designs.balanced;
    var finExt = fin.designs.robust;

    var brkChecks = {};
    brkLight.checks.forEach(function (c) { brkChecks[c.id] = c; });
    var finChecks = {};
    finLight.checks.forEach(function (c) { finChecks[c.id] = c; });
    var padBalChecks = {};
    padBal.checks.forEach(function (c) { padBalChecks[c.id] = c; });

    var vvById = {};
    DATA.verification.benchmarks.forEach(function (b) { vvById[b.id] = b; });
    function vvErr(id, substr) {
      var comp = vvById[id].comparisons.find(function (c) {
        return c.quantity.toLowerCase().indexOf(substr.toLowerCase()) !== -1;
      });
      return Math.abs(comp.error_percent);
    }

    var padAdv = DATA.advanced.padeye;
    var brkAdv = DATA.advanced.bracket;
    var finAdv = DATA.advanced.fin;
    var brkNps6 = brkAdv.find(function (r) { return r.nps === "6"; });
    var brkNps12 = brkAdv.find(function (r) { return r.nps === "12"; });

    var fin20 = DATA.sweeps.fin.find(function (r) { return r.speed_kn === 20; });

    /* Slide 13 visual: Checked by NEMO vs Engineer / Class Sign-Off */
    var boundaryVisual = h("div", { className: "nemo-vis-wrap" },
      h("div", { className: "nemo-table-panel" },
        h("div", { className: "nemo-table-panel__head" },
          h("span", null, "ENGINEERING SCOPE AND SIGN-OFF BOUNDARY"),
          h("span", { className: "nemo-table-panel__sub" }, "DOCS/LIMITS-AND-SAFETY.MD")
        ),
        h(B.Table, {
          dense: true,
          columns: [
            { key: "scope", label: "Domain" },
            { key: "status", label: "Owner", render: function (v, r) { return h(B.Tag, { tone: r.tone }, v); } },
            { key: "detail", label: "Basis and requirement" }
          ],
          rows: [
            { id: "c1", scope: "Part code checks", status: "NEMO", tone: "green", detail: "ASME BTH-1, AISC 360-16 ASD, IACS UR S10 with worked formulas" },
            { id: "c2", scope: "Stock sizing and CAD", status: "NEMO", tone: "green", detail: "Shipyard plate thicknesses, Crosby shackles, STEP, STL, DXF" },
            { id: "c3", scope: "3D linear-elastic FEA", status: "NEMO", tone: "green", detail: "3-level TET10 convergence (<= 5%), reaction balance (< 1e-11)" },
            { id: "c4", scope: "Foil loads and vibration", status: "NEMO", tone: "green", detail: "Whicker-Fehlner, Hess-Smith cavitation, Dunkerley pipe span" },
            { id: "o1", scope: "Supporting hull structure", status: "ENGINEER", tone: "orange", detail: "Deck, bulkhead, stiffeners and through-thickness lamellar tearing" },
            { id: "o2", scope: "Corrosion and fatigue", status: "ENGINEER", tone: "orange", detail: "No corrosion wastage added; fatigue limited to chosen service class" },
            { id: "o3", scope: "Welding and proof test", status: "CLASS", tone: "blue", detail: "Qualified WPS, NDT inspection, proof-load testing and class approval" }
          ]
        })
      )
    );

    /* Backup B3 visual: Astern torque & hull bearing spacing table */
    var b3Visual = h("div", { className: "nemo-vis-wrap" },
      h("div", { className: "nemo-table-panel" },
        h("div", { className: "nemo-table-panel__head" },
          h("span", null, "FIN STOCK · ASTERN TORQUE AND BEARING SPACING"),
          h("span", { className: "nemo-table-panel__sub" }, "IACS UR S10.8 · SYNTHETIC 5.5 MPA")
        ),
        h(B.Table, {
          dense: true,
          columns: [
            { key: "caseName", label: "Configuration" },
            { key: "stock", label: "Stock", mono: true, align: "right" },
            { key: "mass", label: "Mass", mono: true, align: "right" },
            { key: "torque", label: "Gov. Torque", mono: true, align: "right" },
            { key: "bearing", label: "Outer Bearing", mono: true, align: "right" }
          ],
          rows: [
            {
              id: "def",
              caseName: "Baseline (35% chord, 9 kn astern)",
              stock: fmt(finAdv["default"].stock_mm, 0) + " mm",
              mass: fmt(finAdv["default"].mass_kg, 1) + " kg",
              torque: fmt(finAdv["default"].ahead_torque_nm / 1000, 2) + " kN·m (AHEAD)",
              bearing: "NOT CHECKED"
            },
            {
              id: "fwd",
              caseName: "Stock forward (12 kn astern)",
              stock: fmt(finAdv.stock_forward.stock_mm, 0) + " mm",
              mass: fmt(finAdv.stock_forward.mass_kg, 1) + " kg",
              torque: fmt(finAdv.stock_forward.astern_torque_nm / 1000, 2) + " kN·m (ASTERN)",
              bearing: "AHEAD " + fmt(finAdv.stock_forward.ahead_torque_nm / 1000, 2) + " kN·m"
            },
            {
              id: "b800",
              caseName: "Bearings at 800 mm spacing",
              stock: fmt(finAdv.bearings_800.stock_mm, 0) + " mm",
              mass: fmt(finAdv.bearings_800.mass_kg, 1) + " kg",
              torque: fmt(finAdv.bearings_800.ahead_torque_nm / 1000, 2) + " kN·m (AHEAD)",
              bearing: fmt(finAdv.bearings_800.outer.reaction_n / 1000, 1) + " kN (" + fmt(finAdv.bearings_800.outer.use * 100, 1) + "%)"
            },
            {
              id: "b400",
              caseName: "Bearings at 400 mm spacing",
              stock: fmt(finAdv.bearings_400.stock_mm, 0) + " mm",
              mass: fmt(finAdv.bearings_400.mass_kg, 1) + " kg",
              torque: fmt(finAdv.bearings_400.ahead_torque_nm / 1000, 2) + " kN·m (AHEAD)",
              bearing: fmt(finAdv.bearings_400.outer.reaction_n / 1000, 1) + " kN (" + fmt(finAdv.bearings_400.outer.use * 100, 1) + "%)"
            }
          ]
        }),
        h("div", {
          style: {
            marginTop: "auto",
            paddingTop: "0.7cqw",
            borderTop: "1px solid var(--line)",
            fontFamily: "var(--font-mono)",
            fontSize: "0.82cqw",
            color: "var(--ink-muted)",
            textTransform: "uppercase",
            letterSpacing: "0.05em"
          }
        }, "L/D <= 1.2 (UR S10.8.3) · CLEARANCE 1.5 MM (S10.8.4) · SOURCE: ADVANCED.JSON#FIN")
      )
    );

    /* Backup B4 visual: 3D FEA stress renders framed cleanly on opaque Bitfield panels */
    var padLv3 = padBal.fea.levels[2];
    var brkLv3 = brkLight.fea.levels[2];
    var finLv3 = finLight.fea.levels[2];

    var b4Visual = h("div", { className: "nemo-vis-wrap" },
      h("div", { className: "nemo-fea-grid" },
        h("div", { className: "nemo-fea-card" },
          h("div", { className: "nemo-fea-card__imgbox" },
            h("img", { src: "../project-report/images/padeye-stress-head.png", alt: "Padeye balanced head von Mises stress field" })
          ),
          h("div", { className: "nemo-fea-card__info" },
            h("div", { className: "nemo-fea-card__head" },
              h("span", null, "01 · PADEYE"),
              h("span", null, "BALANCED L3")
            ),
            h("div", { className: "nemo-fea-card__foot" },
              h("span", { className: "nemo-fea-card__metric" }, fmt(padBal.fea.head_von_mises_mpa, 1) + " MPA · FOS " + fmt(padBal.fea.factor_of_safety_on_yield, 2)),
              h("span", null, fmtInt(padLv3.elements) + " TET10 · " + fmtInt(padLv3.dofs) + " DOF"),
              h("span", null, "L2 TO L3 DELTA " + fmt(padBal.fea.convergence_change_pct, 2) + "%"),
              h("span", null, "BALANCE ERR " + fmtSci(padLv3.reaction_balance_error))
            )
          )
        ),
        h("div", { className: "nemo-fea-card" },
          h("div", { className: "nemo-fea-card__imgbox" },
            h("img", { src: "../project-report/images/bracket-stress.png", alt: "Pipe bracket von Mises stress field" })
          ),
          h("div", { className: "nemo-fea-card__info" },
            h("div", { className: "nemo-fea-card__head" },
              h("span", null, "02 · BRACKET"),
              h("span", null, "LIGHTEST L3")
            ),
            h("div", { className: "nemo-fea-card__foot" },
              h("span", { className: "nemo-fea-card__metric" }, fmt(brkLight.fea.head_von_mises_mpa, 1) + " MPA · HAND " + fmt(brkLight.fea.hand_stress_mpa, 1) + " MPA"),
              h("span", null, fmtInt(brkLv3.elements) + " TET10 · X >= 9 MM MASK"),
              h("span", null, "L2 TO L3 DELTA " + fmt(brkLight.fea.convergence_change_pct, 2) + "%"),
              h("span", null, "RAW CORNER PEAK " + fmt(brkLv3.max_von_mises_mpa, 1) + " MPA")
            )
          )
        ),
        h("div", { className: "nemo-fea-card" },
          h("div", { className: "nemo-fea-card__imgbox" },
            h("img", { src: "../project-report/images/fin-stock-stress.png", alt: "Stabilizer fin stock von Mises stress field" })
          ),
          h("div", { className: "nemo-fea-card__info" },
            h("div", { className: "nemo-fea-card__head" },
              h("span", null, "03 · FIN STOCK"),
              h("span", null, "LIGHTEST L3")
            ),
            h("div", { className: "nemo-fea-card__foot" },
              h("span", { className: "nemo-fea-card__metric" }, fmt(finLight.fea.head_von_mises_mpa, 1) + " MPA · BEAM " + fmt(finLight.fea.hand_stress_mpa, 1) + " MPA"),
              h("span", null, fmtInt(finLv3.elements) + " TET10 · >= 80 MM OUTBOARD"),
              h("span", null, "L2 TO L3 DELTA " + fmt(finLight.fea.convergence_change_pct, 2) + "%"),
              h("span", null, "FOS " + fmt(finLight.fea.factor_of_safety_on_yield, 2) + " · BAL " + fmtSci(finLv3.reaction_balance_error))
            )
          )
        )
      )
    );

    /* Backup B5 visual: Shipyard stock quantization table + L3 equilibrium telemetry */
    var b5Code = [
      "{",
      '  "part": "stabilizer_stock_lightest",',
      '  "elements_tet10": ' + finLv3.elements + ",",
      '  "dofs": ' + finLv3.dofs + ",",
      '  "assessed_von_mises_mpa": ' + fmt(finLight.fea.head_von_mises_mpa, 2) + ",",
      '  "beam_theory_mpa": ' + fmt(finLight.fea.hand_stress_mpa, 2) + ",",
      '  "convergence_change_pct": ' + fmt(finLight.fea.convergence_change_pct, 3) + ",",
      '  "reaction_balance_err": "' + fmtSci(finLv3.reaction_balance_error) + '"',
      "}"
    ].join("\n");

    var b5Visual = h("div", { className: "nemo-vis-wrap" },
      h("div", { className: "nemo-b5-stack" },
        h("div", { className: "nemo-table-panel" },
          h("div", { className: "nemo-table-panel__head" },
            h("span", null, "SHIPYARD PLATE-STOCK QUANTIZATION STEP"),
            h("span", { className: "nemo-table-panel__sub" }, "DISCRETE PLATE CANDIDATES")
          ),
          h(B.Table, {
            dense: true,
            columns: [
              { key: "part", label: "Part" },
              { key: "light", label: "Lightest (100%)", mono: true, align: "right" },
              { key: "bal", label: "Balanced (85%)", mono: true, align: "right" },
              { key: "ext", label: "Extra margin (70%)", mono: true, align: "right" }
            ],
            rows: [
              {
                id: "p",
                part: "Padeye (S355)",
                light: fmt(padLight.mass_kg, 3) + " kg (6+6 mm)",
                bal: fmt(padBal.mass_kg, 3) + " kg (8+6 mm)",
                ext: fmt(padExt.mass_kg, 3) + " kg (8+6 mm)"
              },
              {
                id: "b",
                part: "Pipe bracket (Grade A)",
                light: fmt(brkLight.mass_kg, 3) + " kg (6 mm)",
                bal: "SAME (25.4% USE)",
                ext: "SAME (25.4% USE)"
              },
              {
                id: "f",
                part: "Stabilizer (AH36 / 42CrMo4)",
                light: fmt(finLight.mass_kg, 1) + " kg (160 mm)",
                bal: fmt(finBal.mass_kg, 1) + " kg (170 mm)",
                ext: fmt(finExt.mass_kg, 1) + " kg (180 mm)"
              }
            ]
          })
        ),
        h(B.CodeBlock, {
          lang: "RUNS/STABILIZER/RESULTS.JSON · L3",
          code: b5Code,
          mark: [5, 6, 8],
          className: "nemo-b5-code"
        })
      )
    );

    var sectionCodeMethod = [
      '{ "solver": "SCIKIT-FEM + PYAMG",',
      '  "element": "TET10 QUADRATIC",',
      '  "mesh_levels": [1.0, 0.7, 0.5],',
      '  "convergence_gate": 0.05,',
      '  "benchmarks_passed": "6 / 6" }'
    ].join("\n");

    var sectionCodeResults = [
      '{ "padeye_evaluations": ' + pad.search.evaluations + ",",
      '  "bracket_evaluations": ' + brk.search.evaluations + ",",
      '  "fin_evaluations": ' + fin.search.evaluations + ",",
      '  "fea_solves_3d": ' + S.total_fea_solves + ",",
      '  "max_conv_delta_pct": ' + fmt(S.max_fea_convergence_change_pct, 2) + " }"
    ].join("\n");

    return [
      /* 01 */ {
        id: "01", group: "main", time: "0:30",
        cue: "Introduce NEMO as an independent rule-based marine structural design tool for three shipboard details. State the panel scope: code sizing from shipyard stock, automated 3D FEA confirmation, and fabrication output.",
        provenance: "WRITING-BRIEF.md · General Objective",
        props: {
          layout: "title",
          tone: "orange",
          seed: 11,
          kicker: "JKUAT · BSc Marine Engineering · Final Panel Defense",
          title: "NEMO: Verified design for marine steelwork.",
          body: "Rule-based sizing and automated 3D FEA for lifting padeyes, pipe support brackets and roll-stabilizer fins.",
          meta: ["Amina A. Bwana (ENM241-0087/2022)", "Mboje Abdullah (ENM241-0088/2022)", "March 2027"],
          page: "01 / 15"
        }
      },
      /* 02 */ {
        id: "02", group: "main", time: "1:00",
        cue: "Contrast disconnected shipyard spreadsheets and unverified CAD against NEMO's closed loop. Emphasize RQ1: unifying three distinct marine codes over discrete shipyard plate stock without hiding any calculation step.",
        provenance: "WRITING-BRIEF.md · General Objective & RQ1; engine/src/nemo/rules/*.py",
        props: {
          layout: "split",
          seed: 5,
          left: {
            glyph: "target",
            title: "The gap",
            body: "Shipboard steel details rely on ad-hoc spreadsheets and disconnected CAD. Code assumptions hide in cells, plate thicknesses ignore yard stock, and simulation loops stay open."
          },
          right: {
            glyph: "gate",
            title: "NEMO",
            body: "One local tool unifies ASME BTH-1, AISC 360-16 and IACS UR S10 over shipyard stock, confirms every buildable solid by 3-level 3D FEA, and issues worked PDF, STEP and DXF files."
          }
        }
      },
      /* 03 */ {
        id: "03", group: "main", time: "0:15",
        cue: "Transition into Section 01: how the pipeline executes deterministically and how we verified every solver before running vessel cases.",
        provenance: "SO1, SO2 · engine/src/nemo/",
        props: {
          layout: "section",
          index: "01",
          kicker: "Section",
          title: "Method and verification",
          glyph: "core",
          tone: "green",
          seed: 4,
          code: sectionCodeMethod
        }
      },
      /* 04 */ {
        id: "04", group: "main", time: "1:00",
        cue: "Walk through the three deterministic stages. Stage 1 searches discrete shipyard stock across 23,469 candidates. Stage 2 builds OpenCASCADE solids, meshes in Gmsh, and solves 3 quadratic TET10 levels with PyAMG. Stage 3 issues signed calculation PDFs and STEP/DXF files.",
        provenance: "deck-data.json#summary; engine/src/nemo/fea_study.py",
        props: {
          layout: "process",
          glyph: "flow",
          seed: 6,
          title: "From vessel inputs to verified steel.",
          items: [
            {
              tab: "01 · Code",
              title: "Stock-aware sizing",
              body: fmtInt(S.total_evaluations) + " plate-stock checks."
            },
            {
              tab: "02 · Solve",
              title: "3-level 3D FEA",
              body: "Gmsh TET10 on 3 meshes."
            },
            {
              tab: "03 · Issue",
              title: "Traceable package",
              body: "Worked PDF, STEP and DXF."
            }
          ]
        }
      },
      /* 05 */ {
        id: "05", group: "main", time: "1:00",
        cue: "Address RQ2 directly: before trusting any vessel case, we ran six independent benchmarks in 60.0 s. Hand calculations match to 0.0016%, CAD volumes to machine precision, Heywood hole SCF within 0.91%, Timoshenko beam within 2.63%, and Hess-Smith foil within 1.65%.",
        provenance: "reports/project-report/data/verification.json",
        props: {
          layout: "content",
          kicker: "01 · Verification · RQ2",
          title: "Six independent benchmarks pass in " + fmt(S.verification_seconds, 1) + " s.",
          body: "Every structural, geometric and hydrodynamic solver is checked against closed-form theory and published reference data.",
          items: [
            "ASME BTH-1 hand checks: max error " + fmt(S.max_vv_hand_error_pct, 4) + "% across 11 equations",
            "OpenCASCADE solid volume: exact to < 1e-13% across 3 parts",
            "Timoshenko cantilever & Heywood hole SCF: " + fmt(vvErr("cantilever", "deflection"), 2) + "% and " + fmt(vvErr("plate-hole", "concentration"), 2) + "%",
            "Hess-Smith panel solver: " + fmt(vvErr("panel-method", "circle"), 2) + "% on circle Cp,min; " + fmt(vvErr("panel-method", "0020"), 2) + "% on NACA 0020"
          ],
          visual: SvgPlot("vv-benchmarks"),
          meta: ["SOURCE: VERIFICATION.JSON", "ALL 6 BENCHMARKS PASS"],
          page: "05 / 15"
        }
      },
      /* 06 */ {
        id: "06", group: "main", time: "1:00",
        cue: "Pre-empt the FEA singularity question: on the pipe bracket, raw peak nodal stress climbs 31.6% at the rigid bulkhead corner as the mesh refines, while assessed stress away from the fixed face (x >= 9 mm) converges to 0.70%. Across all 21 solves, worst change is 0.70% and force balance stays below 1e-11.",
        provenance: "runs/*/20270115-090000-000000/results.json; engine/src/nemo/fea_study.py",
        props: {
          layout: "content",
          kicker: "01 · Mesh Convergence · RQ2",
          title: "All " + S.total_fea_solves + " 3D solves converge below " + fmt(S.max_fea_convergence_change_pct, 2) + "%.",
          body: "Assessed stress is sampled away from fixed-boundary singularities and checked against a 5.0% refinement gate.",
          items: [
            "Padeye balanced: " + fmt(padBal.fea.head_von_mises_mpa, 1) + " MPa at L3 (" + fmt(padBal.fea.convergence_change_pct, 2) + "% change, FoS " + fmt(padBal.fea.factor_of_safety_on_yield, 2) + ")",
            "Bracket seat (x >= 9 mm): " + fmt(brkLight.fea.head_von_mises_mpa, 1) + " MPa vs " + fmt(brkLight.fea.hand_stress_mpa, 1) + " MPa hand (" + fmt(brkLight.fea.convergence_change_pct, 2) + "%)",
            "Fin stock (>= 80 mm outboard): " + fmt(finLight.fea.head_von_mises_mpa, 1) + " MPa vs " + fmt(finLight.fea.hand_stress_mpa, 1) + " MPa beam (" + fmt(finLight.fea.convergence_change_pct, 2) + "%)",
            "Force equilibrium across all " + S.total_fea_solves + " solves: worst error " + fmtSci(S.worst_reaction_balance_error)
          ],
          visual: SvgPlot("fea-convergence"),
          meta: ["SOURCE: DATA/RUNS/*/RESULTS.JSON", "CONVERGED: 7 / 7 DESIGNS"],
          page: "06 / 15"
        }
      },
      /* 07 */ {
        id: "07", group: "main", time: "0:15",
        cue: "Transition into Section 02: applying the verified engine across three shipboard case studies and operating-envelope sweeps to answer RQ3.",
        provenance: "SO3, RQ3 · sweeps.json & runs/*",
        props: {
          layout: "section",
          index: "02",
          kicker: "Section",
          title: "Case studies and governing limits",
          glyph: "target",
          tone: "blue",
          seed: 7,
          code: sectionCodeResults
        }
      },
      /* 08 */ {
        id: "08", group: "main", time: "1:15",
        cue: "Case 1: 5 t engine-room lift, 2 points at 60 deg (28.31 kN sling) under ASME BTH-1 Category B (Nd = 3.0, 1.20 Nd = 3.60 for pin plates). Lightest is 0.305 kg, Balanced is 0.432 kg (8 mm main + 6 mm cheeks, 4.75 t Crosby shackle). Across 1 to 40 t sweeps, base welds govern light oblique lifts while head fracture takes over above 20 t.",
        provenance: "runs/padeye/results.json; sweeps.json#padeye; rules/asme_bth1.py",
        props: {
          layout: "content",
          kicker: "02 · Case 1 · Lifting Padeye · ASME BTH-1",
          title: "Welds govern light lifts; head fracture above 20 t.",
          body: "5.0 t engine-room lift at 60 deg (" + fmt(pad.loads.sling_force_n / 1000, 2) + " kN sling, S355, Nd = " + fmt(pad.rule_set.design_factor, 1) + ") searched " + fmtInt(pad.search.evaluations) + " candidates.",
          items: [
            "Balanced option: " + fmt(padBal.mass_kg, 3) + " kg (8 mm plate, 6 mm cheeks, 4.75 t Crosby G-2130)",
            "Governing check: base fillet weld at " + fmt(padBal.governing_utilization * 100, 1) + "% allowable shear",
            "3D FEA confirms " + fmt(padBal.fea.head_von_mises_mpa, 1) + " MPa peak head stress (FoS " + fmt(padBal.fea.factor_of_safety_on_yield, 2) + " on 355 MPa yield)",
            "At 90 deg vertical, shackle rating governs at 1 to 2 t; head splitting dominates at 30 to 40 t"
          ],
          visual: SvgPlot("padeye-sweep"),
          meta: ["SOURCE: RUNS/PADEYE/RESULTS.JSON & SWEEPS.JSON#PADEYE"],
          page: "08 / 15"
        }
      },
      /* 09 */ {
        id: "09", group: "main", time: "1:15",
        cue: "Case 2: DN100 (NPS 4) seawater line on a 3.0 m span under 1.0g vertical and 0.8g transverse ship motion (1.80 kN down). Minimum 6 mm Grade A plate uses only 25.4% weld capacity (0.996 kg, FEA 34.4 MPa vs 37.5 MPa hand). Yet the critical finding is vibration: frequency limits spacing to 2.35 m versus 4.70 m for sag and 12.10 m for pipe stress.",
        provenance: "runs/pipe-bracket/results.json; sweeps.json#bracket_span; rules/aisc360.py",
        props: {
          layout: "content",
          kicker: "02 · Case 2 · Pipe Support Bracket · AISC 360-16",
          title: "Machinery vibration bounds spacing long before steel strength.",
          body: "DN100 seawater line at 3.0 m span (" + fmt(brk.loads.down_n / 1000, 2) + " kN down, Grade A steel) passes steel checks on minimum 6 mm plate.",
          items: [
            "Bracket mass " + fmt(brkLight.mass_kg, 3) + " kg: root weld at " + fmt(brkLight.governing_utilization * 100, 1) + "% use, seat FEA " + fmt(brkLight.fea.head_von_mises_mpa, 1) + " MPa",
            "Pipe span limits: stress " + fmt(brkLight.span.spans_m.stress, 1) + " m, sag " + fmt(brkLight.span.spans_m.sag, 2) + " m, frequency " + fmt(brkLight.span.spans_m.frequency, 2) + " m",
            "At 3.0 m, f_n = " + fmt(brkLight.span.natural_hz, 2) + " Hz clears 37.5 Hz engine firing by " + fmt(brkLight.span.separation * 100, 1) + "% (Dunkerley " + fmt(brkChecks.support_vibration.capacity * 100, 1) + "%)",
            "Spans of 2.5 m, 4.0 m and 6.0 m fall inside the +-20% excitation bands"
          ],
          visual: SvgPlot("bracket-vibration"),
          meta: ["SOURCE: RUNS/PIPE-BRACKET/RESULTS.JSON & SWEEPS.JSON#BRACKET_SPAN"],
          page: "09 / 15"
        }
      },
      /* 10 */ {
        id: "10", group: "main", time: "1:15",
        cue: "Case 3: 1.4 m by 1.2 m NACA 0020 patrol-boat stabilizer fin at 18 kn and 22 deg. Whicker-Fehlner predicts 80.49 kN normal force, 20.6% above IACS UR S10's empirical 66.74 kN; NEMO takes the larger load. Combined bending and torsion governs the 160 mm 42CrMo4+QT stock (FEA 165.3 MPa vs 165.7 MPa beam theory). Crucially, Hess-Smith suction peak |Cp,min| = 2.91 leaves only 1.5% cavitation margin at 18 kn and cavitates at 20 kn.",
        provenance: "runs/stabilizer/results.json; sweeps.json#fin; hydro.py & rules/iacs_s10.py",
        props: {
          layout: "content",
          kicker: "02 · Case 3 · Stabilizer Fin · IACS UR S10",
          title: "Foil lift exceeds UR S10 by " + fmt(S.fin_lift_excess_over_urs10_pct, 1) + "%; cavitation caps speed.",
          body: "1.4 m by 1.2 m NACA 0020 fin at 18 kn, 22 deg (" + fmt(fin.loads.design_force_n / 1000, 2) + " kN vs " + fmt(fin.loads.ur_s10_force_n / 1000, 2) + " kN UR S10).",
          items: [
            "Lightest fin: " + fmt(finLight.mass_kg, 1) + " kg (8 mm AH36 box, 160 mm 42CrMo4+QT stock at " + fmt(finLight.governing_utilization * 100, 1) + "%)",
            "Stock FEA matches beam theory within 0.25%: " + fmt(finLight.fea.head_von_mises_mpa, 1) + " MPa vs " + fmt(finLight.fea.hand_stress_mpa, 1) + " MPa",
            "At 18 kn, |Cp,min| = " + fmt(Math.abs(fin.loads.cp_min), 2) + " sits " + fmt(S.fin_18kn_cavitation_margin_pct, 1) + "% below sigma = " + fmt(fin.loads.cavitation_number, 2),
            "At 20 kn, sigma falls to " + fmt(fin20.sigma, 2) + ", triggering cavitation before blade yield"
          ],
          visual: SvgPlot("fin-sweep"),
          meta: ["SOURCE: RUNS/STABILIZER/RESULTS.JSON & SWEEPS.JSON#FIN"],
          page: "10 / 15"
        }
      },
      /* 11 */ {
        id: "11", group: "main", time: "0:45",
        cue: "Pause here for the core engineering takeaway answering RQ3: across all three marine details, non-structural or non-yielding limits dictate the practical design envelope before parent plate yield.",
        provenance: "sweeps.json#{padeye,bracket,bracket_span,fin}",
        props: {
          layout: "statement",
          seed: 3,
          title: "Non-structural limits govern before steel yield.",
          body: "Welds and shackles bound padeyes, excitation frequencies bound pipe spans, and cavitation bounds stabilizer speed."
        }
      },
      /* 12 */ {
        id: "12", group: "main", time: "1:00",
        cue: "Present the three headline verification metrics across the entire codebase and committed run artifacts. Every number is traceable directly to JSON outputs and passing automated tests.",
        provenance: "verification.json & runs/*/20270115-090000-000000/results.json",
        props: {
          layout: "data",
          kicker: "02 · Quantitative Evidence · RQ2",
          title: "End-to-end verified results across three shipboard details.",
          body: "Every displayed metric comes directly from committed solver runs and automated regression benchmarks.",
          items: [
            {
              value: S.benchmarks_passed + " / " + S.benchmarks_total,
              unit: "PASS",
              label: "Independent V&V benchmarks",
              meter: 100,
              tone: "green",
              note: "Completed in " + fmt(S.verification_seconds, 1) + " s; worst FEA error " + fmt(S.max_vv_fea_error_pct, 2) + "%."
            },
            {
              value: fmt(S.max_fea_convergence_change_pct, 2),
              unit: "%",
              label: "Max L2 to L3 FEA change",
              meter: Math.round((1 - S.max_fea_convergence_change_pct / 5.0) * 100),
              tone: "blue",
              note: "Across all " + S.total_fea_solves + " TET10 solves (5.0% gate, equilibrium < 1e-11)."
            },
            {
              value: fmtInt(S.total_evaluations),
              unit: "",
              label: "Stock candidates evaluated",
              meter: 94,
              tone: "orange",
              note: "Padeye " + fmtInt(pad.search.evaluations) + ", bracket " + fmtInt(brk.search.evaluations) + ", fin " + fmtInt(fin.search.evaluations) + "."
            }
          ],
          source: "SOURCE: VERIFICATION.JSON & DATA/RUNS/*/20270115-090000-000000/RESULTS.JSON",
          page: "12 / 15"
        }
      },
      /* 13 */ {
        id: "13", group: "main", time: "1:00",
        cue: "Demonstrate engineering maturity by stating exact tool boundaries. NEMO is a traceable design aid, never a replacement for a reviewing engineer, hull backup check, Z-grade lamellar tearing review, corrosion allowance, or class approval.",
        provenance: "docs/limits-and-safety.md; engine/src/nemo/rules/*.py",
        props: {
          layout: "content",
          kicker: "03 · Engineering Boundaries · RQ1",
          title: "Explicit scope boundaries keep sign-off with the engineer.",
          body: "NEMO automates repeatable sizing and 3D checks while flagging every shipboard requirement that remains outside the isolated part.",
          items: [
            "Supporting deck, bulkhead or hull girder backup structure must be checked separately",
            "Lamellar tearing (Z-grade steel) and corrosion wastage are not added automatically",
            "FEA is linear-elastic without nonlinear pin contact or post-yield plasticity",
            "Qualified weld procedures, NDT, proof load testing and class rules govern fabrication"
          ],
          visual: boundaryVisual,
          meta: ["SOURCE: DOCS/LIMITS-AND-SAFETY.MD", "NEMO IS A VERIFIED DESIGN AID"],
          page: "13 / 15"
        }
      },
      /* 14 */ {
        id: "14", group: "main", time: "0:45",
        cue: "Sum up the four delivered pillars closing all three specific objectives: transparent code rules, stock-aware sizing, verified 3D quadratic FEA, and reviewable fabrication packages.",
        provenance: "WRITING-BRIEF.md · Specific Objectives 1–3",
        props: {
          layout: "pillars",
          kicker: "03 · Conclusions",
          title: "Four verified capabilities close the marine steelwork loop.",
          items: [
            { glyph: "core", label: "Code rules", tone: "orange", filled: false },
            { glyph: "stack", label: "Stock sizing", tone: "green", filled: true },
            { glyph: "target", label: "3D FEA V&V", tone: "blue", filled: false },
            { glyph: "flow", label: "PDF & CAD", tone: "yellow", filled: true }
          ],
          meta: ["OBJECTIVES 1 TO 3 MET", "ALL TESTS AND BENCHMARKS PASSING"],
          page: "14 / 15"
        }
      },
      /* 15 */ {
        id: "15", group: "main", time: "0:15",
        cue: "Thank the panel and open for technical questions. Note that indexed backup slides B1 to B5 are ready for obliquity, Dunkerley vibration, astern/bearing spacing, 3D FEA contours, and stock quantization.",
        provenance: "WRITING-BRIEF.md · Authors & Department",
        props: {
          layout: "closing",
          glyph: "spark",
          tone: "green",
          kicker: "Final Panel Defense · March 2027",
          title: "Questions and technical review.",
          meta: [
            "Amina Ahmed Bwana · ENM241-0087/2022",
            "Mboje Abdullah · ENM241-0088/2022",
            "Dept. of Marine Engineering & Maritime Operations · JKUAT",
            "Backup: B1 Obliquity · B2 Dunkerley · B3 Bearings · B4 FEA · B5 Stock"
          ]
        }
      },

      /* ───────────── INDEXED Q&A BACKUP SLIDES (B1–B5) ───────────── */
      /* B1 */ {
        id: "B1", group: "backup", time: "Q&A",
        cue: "If asked about out-of-plane deck lifts: obliquity beta from 0 to 90 deg multiplies side force 10x (1.42 to 14.15 kN), triggers Crosby's 0.75 shackle derating above 15 deg, and forces a solid 25 mm plate without cheek plates.",
        provenance: "reports/project-report/data/advanced.json#padeye",
        props: {
          layout: "content",
          kicker: "Backup B1 · Padeye Out-of-Plane Obliquity",
          title: "Obliquity multiplies side load 10x and derates the shackle.",
          body: "5.0 t lift at 60 deg sling inclination as out-of-plane angle beta rises from 0 deg to 90 deg.",
          items: [
            "Side load grows from " + fmt(padAdv[0].side_n / 1000, 2) + " kN (5% nominal) to " + fmt(padAdv[3].side_n / 1000, 2) + " kN at 90 deg",
            "Above 15 deg side angle, Crosby G-2130 derates to " + fmt(padAdv[2].side_factor, 2) + ", stepping 3.25 t to 4.75 t",
            "Main plate jumps from 6 mm + 6 mm cheeks (" + fmt(padAdv[0].mass_kg, 3) + " kg) to 25 mm solid (" + fmt(padAdv[3].mass_kg, 3) + " kg)",
            "Governing mode shifts from base fillet weld to combined base bending"
          ],
          visual: SvgPlot("padeye-obliquity"),
          meta: ["SOURCE: ADVANCED.JSON#PADEYE", "Q&A BACKUP"],
          page: "B1 / B5"
        }
      },
      /* B2 */ {
        id: "B2", group: "backup", time: "Q&A",
        cue: "If asked whether bracket flexibility matters for pipe vibration: rigid-support screening puts NPS 6 at 39.11 Hz (4.3% above 37.5 Hz), whereas Dunkerley combination drops it to 37.25 Hz (0.67% separation, direct resonance). On NPS 12, compliance cuts frequency from 69.55 Hz to 52.05 Hz.",
        provenance: "reports/project-report/data/advanced.json#bracket",
        props: {
          layout: "content",
          kicker: "Backup B2 · Bracket Flexibility & Dunkerley Coupling",
          title: "Rigid screening misses NPS 6 resonance.",
          body: "Dunkerley combination (1/f_c^2 = 1/f_span^2 + 1/f_bracket^2) on a 3.0 m seawater span across NPS 2 to 12.",
          items: [
            "NPS 6 rigid span is " + fmt(brkNps6.span_hz, 2) + " Hz; " + fmt(brkNps6.bracket_hz, 1) + " Hz bracket pulls it to " + fmt(brkNps6.combined_hz, 2) + " Hz",
            "NPS 6 separation from 37.5 Hz engine firing collapses to " + fmt(brkNps6.separation * 100, 2) + "% (fail)",
            "NPS 12 frequency drops from " + fmt(brkNps12.span_hz, 2) + " Hz rigid to " + fmt(brkNps12.combined_hz, 2) + " Hz combined (-25.2%)",
            "Rigid checks underestimate vibration risk on stiff, large-bore engine-room lines"
          ],
          visual: SvgPlot("bracket-dunkerley"),
          meta: ["SOURCE: ADVANCED.JSON#BRACKET", "Q&A BACKUP"],
          page: "B2 / B5"
        }
      },
      /* B3 */ {
        id: "B3", group: "backup", time: "Q&A",
        cue: "If asked about astern operation and hull stock bearings (IACS UR S10.8): moving the stock forward makes astern torque (11.91 kN·m) more than double ahead torque (5.58 kN·m). Halving bearing spacing from 800 to 400 mm drives outer bearing reaction from 171.0 to 261.6 kN, forcing stock diameter from 160 to 185 mm (+47.9 kg).",
        provenance: "reports/project-report/data/advanced.json#fin; rules/iacs_s10.py",
        props: {
          layout: "content",
          kicker: "Backup B3 · Astern Torque & Hull Bearing Spacing",
          title: "Short bearing spacing forces a 185 mm stock and +47.9 kg.",
          body: "IACS UR S10.2 astern loading and S10.8 synthetic bearing pressure (5.5 MPa, L/D <= 1.2) reshape stock sizing.",
          items: [
            "Stock moved forward at 12 kn astern: astern torque " + fmt(finAdv.stock_forward.astern_torque_nm / 1000, 2) + " kN·m beats ahead " + fmt(finAdv.stock_forward.ahead_torque_nm / 1000, 2) + " kN·m",
            "At 800 mm bearing spacing: outer reaction " + fmt(finAdv.bearings_800.outer.reaction_n / 1000, 1) + " kN fits 160 mm stock (" + fmt(finAdv.bearings_800.outer.use * 100, 1) + "%)",
            "At 400 mm spacing: reaction climbs to " + fmt(finAdv.bearings_400.outer.reaction_n / 1000, 1) + " kN, hitting bearing L/D limit",
            "NEMO upsizes stock to 185 mm (" + fmt(finAdv.bearings_400.mass_kg, 1) + " kg) to satisfy S10.8.2 and S10.8.3"
          ],
          visual: b3Visual,
          meta: ["SOURCE: ADVANCED.JSON#FIN", "Q&A BACKUP"],
          page: "B3 / B5"
        }
      },
      /* B4 */ {
        id: "B4", group: "backup", time: "Q&A",
        cue: "If asked to show the actual 3D FEA contours and explain how singularities are excluded: walk through each assessed zone (padeye head, bracket seat x >= 9 mm, fin stock >= 80 mm outboard of bearing) alongside the exact L3 mesh counts and hand-calc comparison.",
        provenance: "runs/*/results.json; reports/project-report/images/*-stress*.png",
        props: {
          layout: "content",
          kicker: "Backup B4 · 3D FEA Stress Fields & Singularity Zones",
          title: "Assessed stress isolates fixed-face singularities.",
          body: "Each Level 3 quadratic tetrahedral mesh reports structural stress away from artificial rigid constraints.",
          items: [
            "Padeye head: " + fmt(padBal.fea.head_von_mises_mpa, 1) + " MPa around pinhole; " + fmt(padBal.fea.convergence_change_pct, 2) + "% L2 to L3 delta",
            "Bracket seat: x >= 9 mm excludes bulkhead-corner singularity (raw " + fmt(brkLv3.max_von_mises_mpa, 1) + " vs " + fmt(brkLight.fea.head_von_mises_mpa, 1) + " MPa)",
            "Fin stock: >= 80 mm outboard of bearing matches beam theory (" + fmt(finLight.fea.head_von_mises_mpa, 1) + " vs " + fmt(finLight.fea.hand_stress_mpa, 1) + " MPa)",
            "All three solids exported as STEP, STL and cutting DXF from build123d"
          ],
          visual: b4Visual,
          meta: ["SOURCE: DATA/RUNS/*/RESULTS.JSON", "Q&A BACKUP"],
          page: "B4 / B5"
        }
      },
      /* B5 */ {
        id: "B5", group: "backup", time: "Q&A",
        cue: "If asked why open-source build123d/Gmsh/scikit-fem was chosen over commercial CAD/FEA, or what plate-stock quantization costs: closed CAD Python APIs cannot trigger simulation solves automatically; our open-source stack closes the loop in pure Python with 1e-12 equilibrium, while discrete stock steps show exact mass trade-offs.",
        provenance: "runs/*/results.json; engine/src/nemo/fea/solver.py",
        props: {
          layout: "content",
          kicker: "Backup B5 · Open-Source Stack & Stock Quantization",
          title: "Open-source solvers close the loop with zero manual handoffs.",
          body: "Automated CAD, Gmsh TET10 meshing and PyAMG solves verify discrete shipyard-stock steps directly.",
          items: [
            "Closed CAD APIs cannot launch or extract FEA programmatically; build123d + scikit-fem closes the loop",
            "Optional Fusion connector re-checks edited padeye dimensions and records external cross-checks",
            "Padeye 15% and 30% spare steps add +0.127 kg and +0.142 kg over discrete plate stock",
            "Fin stock steps 160 -> 170 -> 180 mm (+18.3 kg / +37.7 kg); bracket stays on 6 mm minimum stock"
          ],
          visual: b5Visual,
          meta: ["SOURCE: DATA/RUNS/*/RESULTS.JSON", "Q&A BACKUP"],
          page: "B5 / B5"
        }
      }
    ];
  }

  function App() {
    var params = new URLSearchParams(window.location.search);
    var printMode = params.get("print");
    var initialTheme = params.get("theme") === "paper" ? "paper" : "ink";
    var initialSlideParam = params.get("slide");

    var slides = React.useMemo(buildSlides, []);
    var initialIndex = 0;
    if (initialSlideParam) {
      var found = slides.findIndex(function (s, i) {
        return s.id.toLowerCase() === initialSlideParam.toLowerCase() || String(i + 1) === initialSlideParam;
      });
      if (found >= 0) initialIndex = found;
    }

    var stateIdx = React.useState(initialIndex);
    var idx = stateIdx[0], setIdx = stateIdx[1];
    var stateTheme = React.useState(initialTheme);
    var theme = stateTheme[0], setTheme = stateTheme[1];
    var stateNotes = React.useState(false);
    var showNotes = stateNotes[0], setShowNotes = stateNotes[1];
    var stateGrid = React.useState(false);
    var showGrid = stateGrid[0], setShowGrid = stateGrid[1];

    React.useEffect(function () {
      document.documentElement.setAttribute("data-theme", theme);
    }, [theme]);

    React.useEffect(function () {
      if (printMode) return;
      function onKey(e) {
        if (e.key === "ArrowRight" || e.key === " " || e.key === "PageDown") {
          e.preventDefault();
          setIdx(function (i) { return Math.min(slides.length - 1, i + 1); });
        } else if (e.key === "ArrowLeft" || e.key === "PageUp") {
          e.preventDefault();
          setIdx(function (i) { return Math.max(0, i - 1); });
        } else if (e.key === "Home") {
          setIdx(0);
        } else if (e.key === "End") {
          setIdx(slides.length - 1);
        } else if (e.key === "t" || e.key === "T") {
          setTheme(function (t) { return t === "ink" ? "paper" : "ink"; });
        } else if (e.key === "n" || e.key === "N") {
          setShowNotes(function (v) { return !v; });
        } else if (e.key === "g" || e.key === "G" || e.key === "Escape") {
          setShowGrid(function (v) { return e.key === "Escape" ? false : !v; });
        }
      }
      window.addEventListener("keydown", onKey);
      return function () { window.removeEventListener("keydown", onKey); };
    }, [printMode, slides.length]);

    if (printMode) {
      var list = printMode === "main" ? slides.filter(function (s) { return s.group === "main"; }) : slides;
      return h("div", { className: "deck-print-root", "data-theme": theme },
        list.map(function (s) {
          var p = Object.assign({}, s.props, { theme: theme });
          return h("div", { key: s.id, className: "deck-print-page", "data-slide-id": s.id, "data-layout": p.layout, "data-tone": p.tone || "" },
            h(B.Slide, p)
          );
        })
      );
    }

    if (showGrid) {
      return h("div", { className: "deck-shell", "data-theme": theme },
        h("div", { className: "deck-overview" },
          slides.map(function (s, i) {
            var p = Object.assign({}, s.props, { theme: theme });
            return h("button", {
              key: s.id,
              type: "button",
              className: "deck-thumb",
              onClick: function () { setIdx(i); setShowGrid(false); }
            },
              h(B.Slide, p),
              h("div", { className: "deck-thumb__cap" },
                h("span", null, s.id + " · " + p.layout),
                h("span", null, s.time)
              )
            );
          })
        ),
        h("div", { className: "deck-hud" },
          h("div", { className: "deck-hud__group" },
            h("span", null, "OVERVIEW · " + slides.length + " SLIDES (15 MAIN + 5 BACKUP)")
          ),
          h("div", { className: "deck-hud__group" },
            h(B.Button, { variant: "ghost", size: "sm", onClick: function () { setTheme(theme === "ink" ? "paper" : "ink"); } }, "THEME: " + theme.toUpperCase()),
            h(B.Button, { variant: "primary", size: "sm", onClick: function () { setShowGrid(false); } }, "CLOSE GRID")
          )
        )
      );
    }

    var cur = slides[idx];
    var slideProps = Object.assign({}, cur.props, { theme: theme });
    var backups = slides.map(function (s, i) { return { id: s.id, idx: i, group: s.group }; }).filter(function (x) { return x.group === "backup"; });

    return h("div", { className: "deck-shell", "data-theme": theme },
      h("div", { className: "deck-stage" },
        h("div", {
          className: "deck-canvas" + (showNotes ? " with-notes" : ""),
          "data-slide-id": cur.id,
          "data-layout": slideProps.layout,
          "data-tone": slideProps.tone || ""
        }, h(B.Slide, slideProps))
      ),
      h("div", null,
        showNotes && h("div", { className: "deck-notes" },
          h("div", null,
            h("div", { className: "deck-notes__label" }, "SLIDE " + cur.id + " · " + cur.time),
            h("div", { className: "deck-notes__label", style: { marginTop: "6px" } }, "LAYOUT: " + slideProps.layout)
          ),
          h("p", { className: "deck-notes__cue" }, cur.cue),
          h("div", { className: "deck-notes__prov" },
            h("div", { className: "deck-notes__label" }, "PROVENANCE"),
            h("div", { style: { marginTop: "4px" } }, cur.provenance)
          )
        ),
        h("div", { className: "deck-hud" },
          h("div", { className: "deck-hud__group" },
            h(B.Button, { variant: "ghost", size: "sm", disabled: idx === 0, onClick: function () { setIdx(idx - 1); } }, "PREV"),
            h(B.Button, { variant: "ghost", size: "sm", disabled: idx === slides.length - 1, onClick: function () { setIdx(idx + 1); } }, "NEXT"),
            h("span", { style: { marginLeft: "8px" } }, "SLIDE " + cur.id + " (" + (idx + 1) + "/" + slides.length + ") · " + cur.time)
          ),
          h("div", { className: "deck-hud__group" },
            h("span", null, "Q&A:"),
            backups.map(function (bk) {
              return h(B.Button, {
                key: bk.id,
                variant: idx === bk.idx ? "primary" : "quiet",
                size: "sm",
                onClick: function () { setIdx(bk.idx); }
              }, bk.id);
            }),
            h(B.Button, { variant: "ghost", size: "sm", onClick: function () { setShowNotes(!showNotes); } }, showNotes ? "HIDE NOTES (N)" : "NOTES (N)"),
            h(B.Button, { variant: "ghost", size: "sm", onClick: function () { setShowGrid(true); } }, "GRID (G)"),
            h(B.Button, { variant: "signal", size: "sm", onClick: function () { setTheme(theme === "ink" ? "paper" : "ink"); } }, "THEME: " + theme.toUpperCase() + " (T)")
          )
        )
      )
    );
  }

  ReactDOM.createRoot(document.getElementById("root")).render(h(App));
})();
