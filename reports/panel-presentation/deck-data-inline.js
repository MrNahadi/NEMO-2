window.NEMO_DATA = {
  "provenance": {
    "cases": "reports/project-report/data/cases.json",
    "verification": "reports/project-report/data/verification.json",
    "sweeps": "reports/project-report/data/sweeps.json",
    "advanced": "reports/project-report/data/advanced.json",
    "runs": {
      "padeye": "reports/project-report/data/runs/padeye/20270115-090000-000000/results.json",
      "pipe-bracket": "reports/project-report/data/runs/pipe-bracket/20270115-090000-000000/results.json",
      "stabilizer": "reports/project-report/data/runs/stabilizer/20270115-090000-000000/results.json"
    }
  },
  "summary": {
    "benchmarks_passed": 6,
    "benchmarks_total": 6,
    "verification_seconds": 60.016754900000024,
    "max_vv_fea_error_pct": 2.626636756778055,
    "max_vv_hand_error_pct": 0.0015675140091190886,
    "max_vv_cad_error_pct": 3.520556530084743e-14,
    "total_evaluations": 23469,
    "total_fea_designs": 7,
    "total_fea_solves": 21,
    "all_fea_converged": true,
    "max_fea_convergence_change_pct": 0.704279930954617,
    "worst_reaction_balance_error": 9.89048964198333e-12,
    "fin_lift_excess_over_urs10_pct": 20.597329011608906,
    "fin_18kn_cavitation_margin_pct": 1.4525180706490142
  },
  "verification": {
    "nemo_version": "0.1.0",
    "passed": true,
    "seconds_total": 60.016754900000024,
    "benchmarks": [
      {
        "id": "padeye-hand-calc",
        "title": "Padeye checks against a hand calculation",
        "source": "Hand calculation in the engineering manual",
        "passed": true,
        "seconds": 0.0006703000001380133,
        "mesh": null,
        "comparisons": [
          {
            "quantity": "Sling force F",
            "reference": 22647.6,
            "nemo": 22647.488069393774,
            "unit": "N",
            "error_percent": -0.0004942272303671575,
            "tolerance_percent": 0.1,
            "passed": true
          },
          {
            "quantity": "Strength reduction C_r",
            "reference": 0.885696,
            "nemo": 0.8856957480312277,
            "unit": "",
            "error_percent": -2.844867452165052e-05,
            "tolerance_percent": 0.1,
            "passed": true
          },
          {
            "quantity": "Effective width b_{eff}",
            "reference": 22.0013,
            "nemo": 22.00134383247493,
            "unit": "mm",
            "error_percent": 0.00019922674991783475,
            "tolerance_percent": 0.1,
            "passed": true
          },
          {
            "quantity": "Tension through pinhole P_t",
            "reference": 101763,
            "nemo": 101762.81601329088,
            "unit": "N",
            "error_percent": -0.00018079921888945047,
            "tolerance_percent": 0.1,
            "passed": true
          },
          {
            "quantity": "Fracture beyond pinhole P_b",
            "reference": 117933,
            "nemo": 117932.96215557186,
            "unit": "N",
            "error_percent": -3.2089769731762674e-05,
            "tolerance_percent": 0.1,
            "passed": true
          },
          {
            "quantity": "Shear plane area A_v",
            "reference": 1492.61,
            "nemo": 1492.614079263358,
            "unit": "mm\u00b2",
            "error_percent": 0.000273297335412982,
            "tolerance_percent": 0.1,
            "passed": true
          },
          {
            "quantity": "Double plane shear P_v",
            "reference": 136408,
            "nemo": 136408.34224379022,
            "unit": "N",
            "error_percent": 0.0002508971542864585,
            "tolerance_percent": 0.1,
            "passed": true
          },
          {
            "quantity": "Pin bearing P_p",
            "reference": 54912.5,
            "nemo": 54912.5,
            "unit": "N",
            "error_percent": 0.0,
            "tolerance_percent": 0.1,
            "passed": true
          },
          {
            "quantity": "Base combined use",
            "reference": 0.14898,
            "nemo": 0.1489823352823708,
            "unit": "",
            "error_percent": 0.0015675140091190886,
            "tolerance_percent": 0.1,
            "passed": true
          },
          {
            "quantity": "Base weld stress",
            "reference": 26.179,
            "nemo": 26.178778899547435,
            "unit": "MPa",
            "error_percent": -0.0008445718039780177,
            "tolerance_percent": 0.1,
            "passed": true
          },
          {
            "quantity": "Plate mass",
            "reference": 2.5958,
            "nemo": 2.5957835601618386,
            "unit": "kg",
            "error_percent": -0.0006333245304516481,
            "tolerance_percent": 0.1,
            "passed": true
          }
        ]
      },
      {
        "id": "cad-volume",
        "title": "3D model volume against the exact formula",
        "source": "Exact geometry",
        "passed": true,
        "seconds": 0.16601550000018506,
        "mesh": null,
        "comparisons": [
          {
            "quantity": "Plain padeye volume",
            "reference": 330673.06498876924,
            "nemo": 330673.06498876936,
            "unit": "mm\u00b3",
            "error_percent": 3.520556530084743e-14,
            "tolerance_percent": 0.01,
            "passed": true
          },
          {
            "quantity": "Padeye with cheek plates",
            "reference": 424000.0720740801,
            "nemo": 424000.07207408006,
            "unit": "mm\u00b3",
            "error_percent": -1.372821957994798e-14,
            "tolerance_percent": 0.01,
            "passed": true
          },
          {
            "quantity": "Pipe support bracket",
            "reference": 324921.239199482,
            "nemo": 324921.239199482,
            "unit": "mm\u00b3",
            "error_percent": 0.0,
            "tolerance_percent": 0.01,
            "passed": true
          }
        ]
      },
      {
        "id": "cantilever",
        "title": "Cantilever beam",
        "source": "Timoshenko beam theory",
        "passed": true,
        "seconds": 2.0879273000000467,
        "mesh": {
          "elements": 3487,
          "equations": 19479
        },
        "comparisons": [
          {
            "quantity": "Tip deflection",
            "reference": 0.9598095238095238,
            "nemo": 0.9521628123881029,
            "unit": "mm",
            "error_percent": -0.7966905132458794,
            "tolerance_percent": 3.0,
            "passed": true
          },
          {
            "quantity": "Bending stress at mid-span",
            "reference": 75.0,
            "nemo": 76.96997756758354,
            "unit": "MPa",
            "error_percent": 2.626636756778055,
            "tolerance_percent": 4.0,
            "passed": true
          },
          {
            "quantity": "Support reaction",
            "reference": 1000.0,
            "nemo": 999.9999999693123,
            "unit": "N",
            "error_percent": -3.068771547987126e-09,
            "tolerance_percent": 1e-06,
            "passed": true
          }
        ]
      },
      {
        "id": "plate-hole",
        "title": "Plate with a hole",
        "source": "Heywood (1952), as given in Peterson's Stress Concentration Factors",
        "passed": true,
        "seconds": 46.731266199999936,
        "mesh": {
          "elements": 16749,
          "equations": 96000
        },
        "comparisons": [
          {
            "quantity": "Stress concentration factor",
            "reference": 3.0322222222222224,
            "nemo": 3.0596966142807505,
            "unit": "",
            "error_percent": 0.9060810865765949,
            "tolerance_percent": 5.0,
            "passed": true
          },
          {
            "quantity": "Support reaction",
            "reference": 200000.0,
            "nemo": 199999.99999990186,
            "unit": "N",
            "error_percent": -4.906905815005302e-11,
            "tolerance_percent": 1e-06,
            "passed": true
          }
        ]
      },
      {
        "id": "panel-method",
        "title": "Foil pressure solver",
        "source": "Potential flow theory; Abbott and von Doenhoff, Theory of Wing Sections",
        "passed": true,
        "seconds": 0.20427479999989373,
        "mesh": null,
        "comparisons": [
          {
            "quantity": "Lowest pressure on a circle",
            "reference": -3.0,
            "nemo": -2.9984580724814474,
            "unit": "",
            "error_percent": -0.05139758395175479,
            "tolerance_percent": 0.5,
            "passed": true
          },
          {
            "quantity": "NACA 0012 lift slope",
            "reference": 6.86375162956298,
            "nemo": 6.938689529922449,
            "unit": "per rad",
            "error_percent": 1.091792133571715,
            "tolerance_percent": 3.0,
            "passed": true
          },
          {
            "quantity": "NACA 0020 lift slope",
            "reference": 7.250795844485242,
            "nemo": 7.370365025972965,
            "unit": "per rad",
            "error_percent": 1.6490490706432448,
            "tolerance_percent": 3.0,
            "passed": true
          }
        ]
      },
      {
        "id": "stock-beam",
        "title": "Fin stock against beam theory",
        "source": "Beam and torsion theory, as used in IACS UR S10.4",
        "passed": true,
        "seconds": 10.82653879999998,
        "mesh": {
          "elements": 6160,
          "equations": 31584
        },
        "comparisons": [
          {
            "quantity": "Equivalent stress near the bearing",
            "reference": 165.66998500379137,
            "nemo": 165.45539572066397,
            "unit": "MPa",
            "error_percent": -0.12952815992739092,
            "tolerance_percent": 4.0,
            "passed": true
          },
          {
            "quantity": "Support reaction",
            "reference": 80487.73021618668,
            "nemo": 80487.73021599163,
            "unit": "N",
            "error_percent": -2.4233988360352905e-10,
            "tolerance_percent": 1e-06,
            "passed": true
          }
        ]
      }
    ]
  },
  "runs": {
    "padeye": {
      "source_path": "reports/project-report/data/runs/padeye/20270115-090000-000000/results.json",
      "csv_path": "reports/project-report/data/runs/padeye/20270115-090000-000000/designs-evaluated.csv",
      "csv_rows": 14199,
      "seconds": 291.9596815,
      "rule_set": {
        "id": "asme-bth-1",
        "name": "ASME BTH-1, Design of Below-the-Hook Lifting Devices",
        "design_category": "B",
        "service_class": 0,
        "design_factor": 3.0,
        "pin_connection_design_factor": 3.5999999999999996
      },
      "job": {
        "part": "padeye",
        "lift": {
          "lifted_mass_kg": 5000.0,
          "lift_points": 2,
          "sling_angle_deg": 60.0,
          "dynamic_factor": 1.0,
          "points_carrying": null,
          "side_load_fraction": 0.05,
          "out_of_plane_angle_deg": 0.0
        },
        "material_id": "S355",
        "plate_thicknesses_mm": [
          6.0,
          8.0,
          10.0,
          12.0,
          15.0,
          20.0,
          25.0,
          30.0,
          40.0,
          50.0
        ],
        "allow_cheek_plates": true,
        "rule_set_id": "asme-bth-1",
        "design_category": "B",
        "service_class": 0,
        "fill_shackle_jaw": true,
        "electrode_strength_mpa": 482.0
      },
      "loads": {
        "sling_force_n": 28309.360086742217,
        "sling_force_t": 2.8867513459481287,
        "vertical_n": 24516.625,
        "horizontal_n": 14154.680043371112,
        "side_n": 1415.4680043371109,
        "sling_angle_deg": 60.0,
        "static_sling_force_n": 28309.360086742217,
        "out_of_plane_angle_deg": 0.0,
        "side_angle_deg": 0.0,
        "side_from_angle_n": 0.0
      },
      "material": {
        "id": "S355",
        "name": "S355 structural steel",
        "source": "EN 10025-2:2019, plate 3-100 mm",
        "tensile_strength_mpa": 470.0,
        "elastic_modulus_gpa": 210.0,
        "density_kg_m3": 7850.0
      },
      "stock_material": null,
      "search": {
        "combinations": 36,
        "evaluations": 19389,
        "skipped": 0
      },
      "designs": {
        "lightest": {
          "label": "Lightest",
          "target_utilization": 1.0,
          "mass_kg": 0.30500722463627267,
          "governing_id": "base_weld",
          "governing_title": "Base weld strength",
          "governing_utilization": 0.9796597125107048,
          "governing_source": "ASME BTH-1, welded connections: fillet weld allowable shear",
          "passed": true,
          "design": {
            "main_thickness_mm": 6.0,
            "head_radius_mm": 21.0,
            "hole_diameter_mm": 20.5,
            "base_length_mm": 140.0,
            "hole_height_mm": 39.0,
            "weld_leg_mm": 4.0,
            "cheek_thickness_mm": 6.0,
            "cheek_radius_mm": 21.0,
            "cheek_weld_leg_mm": 3.0
          },
          "shackle": {
            "label": "3.25 t (5/8 in) Crosby G-2130",
            "wll_t": 3.25,
            "jaw_width_mm": 26.9,
            "pin_diameter_mm": 19.1
          },
          "span": null,
          "checks": [
            {
              "id": "head_tension",
              "title": "Tearing across the sides of the hole",
              "demand": 28309.360086742217,
              "capacity": 45478.42460687764,
              "unit": "N",
              "utilization": 0.6224789079976405,
              "passed": true,
              "severity": "required",
              "source": "ASME BTH-1, pin-connected plates: tensile strength through the pinhole"
            },
            {
              "id": "head_fracture",
              "title": "Splitting above the hole",
              "demand": 28309.360086742217,
              "capacity": 39418.87931225725,
              "unit": "N",
              "utilization": 0.7181675527223691,
              "passed": true,
              "severity": "required",
              "source": "ASME BTH-1, pin-connected plates: fracture strength beyond the pinhole"
            },
            {
              "id": "head_shear_out",
              "title": "Shearing out above the hole",
              "demand": 28309.360086742217,
              "capacity": 42627.765792605984,
              "unit": "N",
              "utilization": 0.6641061186381161,
              "passed": true,
              "severity": "required",
              "source": "ASME BTH-1, pin-connected plates: double plane shear strength"
            },
            {
              "id": "head_bearing",
              "title": "Crushing under the shackle pin",
              "demand": 28309.360086742217,
              "capacity": 50853.75,
              "unit": "N",
              "utilization": 0.5566818589925466,
              "passed": true,
              "severity": "required",
              "source": "ASME BTH-1, pin-connected plates: bearing strength"
            },
            {
              "id": "pin_hole_fit",
              "title": "Pin fits the hole closely",
              "demand": 0.9,
              "capacity": 0.9317073170731708,
              "unit": "ratio",
              "utilization": 0.9659685863874345,
              "passed": true,
              "severity": "advice",
              "source": "ASME BTH-1 commentary on pin-to-hole clearance"
            },
            {
              "id": "hole_clearance",
              "title": "Hole is big enough for the pin",
              "demand": 20.1,
              "capacity": 20.5,
              "unit": "mm",
              "utilization": 0.9804878048780489,
              "passed": true,
              "severity": "required",
              "source": "NEMO practice"
            },
            {
              "id": "cheek_weld",
              "title": "Cheek plate welds",
              "demand": 33.71378731949658,
              "capacity": 80.33333333333334,
              "unit": "MPa",
              "utilization": 0.4196737010725715,
              "passed": true,
              "severity": "required",
              "source": "ASME BTH-1, welded connections: fillet weld allowable shear"
            },
            {
              "id": "cheek_weld_size",
              "title": "Cheek weld size",
              "demand": 3.0,
              "capacity": 3.0,
              "unit": "mm",
              "utilization": 1.0,
              "passed": true,
              "severity": "advice",
              "source": "AWS D1.1 minimum fillet weld size"
            },
            {
              "id": "base_combined",
              "title": "Pulling and bending at the base",
              "demand": 0.8813486524190552,
              "capacity": 1.0,
              "unit": "ratio",
              "utilization": 0.8813486524190552,
              "passed": true,
              "severity": "required",
              "source": "ASME BTH-1, members: combined axial tension and bending"
            },
            {
              "id": "base_shear",
              "title": "Shear at the base",
              "demand": 16.9348540348383,
              "capacity": 68.31978185410571,
              "unit": "MPa",
              "utilization": 0.24787628963748792,
              "passed": true,
              "severity": "required",
              "source": "ASME BTH-1, members: allowable shear stress"
            },
            {
              "id": "base_weld",
              "title": "Base weld strength",
              "demand": 78.69933023835996,
              "capacity": 80.33333333333334,
              "unit": "MPa",
              "utilization": 0.9796597125107048,
              "passed": true,
              "severity": "required",
              "source": "ASME BTH-1, welded connections: fillet weld allowable shear"
            },
            {
              "id": "base_weld_size",
              "title": "Base weld size",
              "demand": 3.0,
              "capacity": 4.0,
              "unit": "mm",
              "utilization": 0.75,
              "passed": true,
              "severity": "advice",
              "source": "AWS D1.1 minimum fillet weld size"
            },
            {
              "id": "shackle_rating",
              "title": "Shackle is rated for the load",
              "demand": 2.8867513459481287,
              "capacity": 3.25,
              "unit": "t",
              "utilization": 0.8882311833686549,
              "passed": true,
              "severity": "required",
              "source": "Crosby G-2130 working load limit"
            },
            {
              "id": "shackle_fit",
              "title": "Padeye fits inside the shackle",
              "demand": 20.0,
              "capacity": 26.9,
              "unit": "mm",
              "utilization": 0.7434944237918216,
              "passed": true,
              "severity": "required",
              "source": "NEMO practice"
            },
            {
              "id": "shackle_fill",
              "title": "Padeye fills the shackle jaw",
              "demand": 16.139999999999997,
              "capacity": 18.0,
              "unit": "mm",
              "utilization": 0.8966666666666665,
              "passed": true,
              "severity": "advice",
              "source": "NEMO practice (rigging guidance)"
            }
          ],
          "fea": {
            "model": null,
            "region": null,
            "head_von_mises_mpa": 222.69345774437102,
            "yield_strength_mpa": 355.0,
            "factor_of_safety_on_yield": 1.5941195740357275,
            "convergence_change": 0.004407192050041557,
            "convergence_change_pct": 0.4407192050041557,
            "converged": true,
            "hand_stress_mpa": null,
            "hand_label": null,
            "max_reaction_balance_error": 9.727028543087758e-13,
            "levels": [
              {
                "level": 1,
                "elements": 6487,
                "dofs": 34986,
                "head_von_mises_mpa": 222.9235604273291,
                "max_von_mises_mpa": 222.9235604273291,
                "max_displacement_mm": 0.13209284923972578,
                "reaction_balance_error": 9.727028543087758e-13,
                "solve_seconds": 10.035012199999983
              },
              {
                "level": 2,
                "elements": 17200,
                "dofs": 86325,
                "head_von_mises_mpa": 223.67491058093827,
                "max_von_mises_mpa": 223.67491058093827,
                "max_displacement_mm": 0.13327094454221813,
                "reaction_balance_error": 3.517271063912662e-13,
                "solve_seconds": 32.81801949999999
              },
              {
                "level": 3,
                "elements": 44271,
                "dofs": 209763,
                "head_von_mises_mpa": 222.69345774437102,
                "max_von_mises_mpa": 222.69345774437102,
                "max_displacement_mm": 0.13389928127100992,
                "reaction_balance_error": 1.7826771376137018e-13,
                "solve_seconds": 56.32535760000019
              }
            ]
          }
        },
        "balanced": {
          "label": "Balanced (at least 15% spare)",
          "target_utilization": 0.85,
          "mass_kg": 0.4319738202833279,
          "governing_id": "base_weld",
          "governing_title": "Base weld strength",
          "governing_utilization": 0.8104094940664458,
          "governing_source": "ASME BTH-1, welded connections: fillet weld allowable shear",
          "passed": true,
          "design": {
            "main_thickness_mm": 8.0,
            "head_radius_mm": 25.0,
            "hole_diameter_mm": 23.5,
            "base_length_mm": 140.0,
            "hole_height_mm": 45.0,
            "weld_leg_mm": 5.0,
            "cheek_thickness_mm": 6.0,
            "cheek_radius_mm": 22.0,
            "cheek_weld_leg_mm": 5.0
          },
          "shackle": {
            "label": "4.75 t (3/4 in) Crosby G-2130",
            "wll_t": 4.75,
            "jaw_width_mm": 31.8,
            "pin_diameter_mm": 22.4
          },
          "span": null,
          "checks": [
            {
              "id": "head_tension",
              "title": "Tearing across the sides of the hole",
              "demand": 28309.360086742217,
              "capacity": 49076.88911416988,
              "unit": "N",
              "utilization": 0.5768368899847099,
              "passed": true,
              "severity": "required",
              "source": "ASME BTH-1, pin-connected plates: tensile strength through the pinhole"
            },
            {
              "id": "head_fracture",
              "title": "Splitting above the hole",
              "demand": 28309.360086742217,
              "capacity": 43447.58816651861,
              "unit": "N",
              "utilization": 0.6515749499890042,
              "passed": true,
              "severity": "required",
              "source": "ASME BTH-1, pin-connected plates: fracture strength beyond the pinhole"
            },
            {
              "id": "head_shear_out",
              "title": "Shearing out above the hole",
              "demand": 28309.360086742217,
              "capacity": 46608.401754328355,
              "unit": "N",
              "utilization": 0.6073874885468097,
              "passed": true,
              "severity": "required",
              "source": "ASME BTH-1, pin-connected plates: double plane shear strength"
            },
            {
              "id": "head_bearing",
              "title": "Crushing under the shackle pin",
              "demand": 28309.360086742217,
              "capacity": 66266.66666666667,
              "unit": "N",
              "utilization": 0.42720362303936943,
              "passed": true,
              "severity": "required",
              "source": "ASME BTH-1, pin-connected plates: bearing strength"
            },
            {
              "id": "pin_hole_fit",
              "title": "Pin fits the hole closely",
              "demand": 0.9,
              "capacity": 0.9531914893617021,
              "unit": "ratio",
              "utilization": 0.9441964285714287,
              "passed": true,
              "severity": "advice",
              "source": "ASME BTH-1 commentary on pin-to-hole clearance"
            },
            {
              "id": "hole_clearance",
              "title": "Hole is big enough for the pin",
              "demand": 23.4,
              "capacity": 23.5,
              "unit": "mm",
              "utilization": 0.9957446808510638,
              "passed": true,
              "severity": "required",
              "source": "NEMO practice"
            },
            {
              "id": "cheek_weld",
              "title": "Cheek plate welds",
              "demand": 17.377924918322332,
              "capacity": 80.33333333333334,
              "unit": "MPa",
              "utilization": 0.21632271682558918,
              "passed": true,
              "severity": "required",
              "source": "ASME BTH-1, welded connections: fillet weld allowable shear"
            },
            {
              "id": "cheek_weld_size",
              "title": "Cheek weld size",
              "demand": 5.0,
              "capacity": 5.0,
              "unit": "mm",
              "utilization": 1.0,
              "passed": true,
              "severity": "advice",
              "source": "AWS D1.1 minimum fillet weld size"
            },
            {
              "id": "base_combined",
              "title": "Pulling and bending at the base",
              "demand": 0.6381255809371824,
              "capacity": 1.0,
              "unit": "ratio",
              "utilization": 0.6381255809371824,
              "passed": true,
              "severity": "required",
              "source": "ASME BTH-1, members: combined axial tension and bending"
            },
            {
              "id": "base_shear",
              "title": "Shear at the base",
              "demand": 12.701140526128725,
              "capacity": 68.31978185410571,
              "unit": "MPa",
              "utilization": 0.18590721722811596,
              "passed": true,
              "severity": "required",
              "source": "ASME BTH-1, members: allowable shear stress"
            },
            {
              "id": "base_weld",
              "title": "Base weld strength",
              "demand": 65.10289602333782,
              "capacity": 80.33333333333334,
              "unit": "MPa",
              "utilization": 0.8104094940664458,
              "passed": true,
              "severity": "required",
              "source": "ASME BTH-1, welded connections: fillet weld allowable shear"
            },
            {
              "id": "base_weld_size",
              "title": "Base weld size",
              "demand": 5.0,
              "capacity": 5.0,
              "unit": "mm",
              "utilization": 1.0,
              "passed": true,
              "severity": "advice",
              "source": "AWS D1.1 minimum fillet weld size"
            },
            {
              "id": "shackle_rating",
              "title": "Shackle is rated for the load",
              "demand": 2.8867513459481287,
              "capacity": 4.75,
              "unit": "t",
              "utilization": 0.6077371254627639,
              "passed": true,
              "severity": "required",
              "source": "Crosby G-2130 working load limit"
            },
            {
              "id": "shackle_fit",
              "title": "Padeye fits inside the shackle",
              "demand": 22.0,
              "capacity": 31.8,
              "unit": "mm",
              "utilization": 0.6918238993710691,
              "passed": true,
              "severity": "required",
              "source": "NEMO practice"
            },
            {
              "id": "shackle_fill",
              "title": "Padeye fills the shackle jaw",
              "demand": 19.08,
              "capacity": 20.0,
              "unit": "mm",
              "utilization": 0.954,
              "passed": true,
              "severity": "advice",
              "source": "NEMO practice (rigging guidance)"
            }
          ],
          "fea": {
            "model": null,
            "region": null,
            "head_von_mises_mpa": 188.51394662774598,
            "yield_strength_mpa": 355.0,
            "factor_of_safety_on_yield": 1.8831497952828395,
            "convergence_change": 0.003827443297801341,
            "convergence_change_pct": 0.3827443297801341,
            "converged": true,
            "hand_stress_mpa": null,
            "hand_label": null,
            "max_reaction_balance_error": 5.782693174724256e-13,
            "levels": [
              {
                "level": 1,
                "elements": 5530,
                "dofs": 30201,
                "head_von_mises_mpa": 188.40451496794506,
                "max_von_mises_mpa": 188.40451496794506,
                "max_displacement_mm": 0.08665881799203225,
                "reaction_balance_error": 5.01960290239656e-13,
                "solve_seconds": 7.583672699999852
              },
              {
                "level": 2,
                "elements": 13982,
                "dofs": 71370,
                "head_von_mises_mpa": 189.23547306930843,
                "max_von_mises_mpa": 189.23547306930843,
                "max_displacement_mm": 0.08703073292351314,
                "reaction_balance_error": 5.782693174724256e-13,
                "solve_seconds": 23.82213230000002
              },
              {
                "level": 3,
                "elements": 35940,
                "dofs": 172938,
                "head_von_mises_mpa": 188.51394662774598,
                "max_von_mises_mpa": 188.51394662774598,
                "max_displacement_mm": 0.08743036196101305,
                "reaction_balance_error": 3.032995442770273e-13,
                "solve_seconds": 39.08262139999988
              }
            ]
          }
        },
        "robust": {
          "label": "Extra margin (at least 30% spare)",
          "target_utilization": 0.7,
          "mass_kg": 0.44726599252408344,
          "governing_id": "base_weld",
          "governing_title": "Base weld strength",
          "governing_utilization": 0.6725406189524116,
          "governing_source": "ASME BTH-1, welded connections: fillet weld allowable shear",
          "passed": true,
          "design": {
            "main_thickness_mm": 8.0,
            "head_radius_mm": 22.0,
            "hole_diameter_mm": 23.5,
            "base_length_mm": 160.0,
            "hole_height_mm": 45.0,
            "weld_leg_mm": 5.0,
            "cheek_thickness_mm": 6.0,
            "cheek_radius_mm": 22.0,
            "cheek_weld_leg_mm": 5.0
          },
          "shackle": {
            "label": "4.75 t (3/4 in) Crosby G-2130",
            "wll_t": 4.75,
            "jaw_width_mm": 31.8,
            "pin_diameter_mm": 22.4
          },
          "span": null,
          "checks": [
            {
              "id": "head_tension",
              "title": "Tearing across the sides of the hole",
              "demand": 28309.360086742217,
              "capacity": 49076.88911416988,
              "unit": "N",
              "utilization": 0.5768368899847099,
              "passed": true,
              "severity": "required",
              "source": "ASME BTH-1, pin-connected plates: tensile strength through the pinhole"
            },
            {
              "id": "head_fracture",
              "title": "Splitting above the hole",
              "demand": 28309.360086742217,
              "capacity": 43447.58816651861,
              "unit": "N",
              "utilization": 0.6515749499890042,
              "passed": true,
              "severity": "required",
              "source": "ASME BTH-1, pin-connected plates: fracture strength beyond the pinhole"
            },
            {
              "id": "head_shear_out",
              "title": "Shearing out above the hole",
              "demand": 28309.360086742217,
              "capacity": 46608.401754328355,
              "unit": "N",
              "utilization": 0.6073874885468097,
              "passed": true,
              "severity": "required",
              "source": "ASME BTH-1, pin-connected plates: double plane shear strength"
            },
            {
              "id": "head_bearing",
              "title": "Crushing under the shackle pin",
              "demand": 28309.360086742217,
              "capacity": 66266.66666666667,
              "unit": "N",
              "utilization": 0.42720362303936943,
              "passed": true,
              "severity": "required",
              "source": "ASME BTH-1, pin-connected plates: bearing strength"
            },
            {
              "id": "pin_hole_fit",
              "title": "Pin fits the hole closely",
              "demand": 0.9,
              "capacity": 0.9531914893617021,
              "unit": "ratio",
              "utilization": 0.9441964285714287,
              "passed": true,
              "severity": "advice",
              "source": "ASME BTH-1 commentary on pin-to-hole clearance"
            },
            {
              "id": "hole_clearance",
              "title": "Hole is big enough for the pin",
              "demand": 23.4,
              "capacity": 23.5,
              "unit": "mm",
              "utilization": 0.9957446808510638,
              "passed": true,
              "severity": "required",
              "source": "NEMO practice"
            },
            {
              "id": "cheek_weld",
              "title": "Cheek plate welds",
              "demand": 17.377924918322332,
              "capacity": 80.33333333333334,
              "unit": "MPa",
              "utilization": 0.21632271682558918,
              "passed": true,
              "severity": "required",
              "source": "ASME BTH-1, welded connections: fillet weld allowable shear"
            },
            {
              "id": "cheek_weld_size",
              "title": "Cheek weld size",
              "demand": 5.0,
              "capacity": 5.0,
              "unit": "mm",
              "utilization": 1.0,
              "passed": true,
              "severity": "advice",
              "source": "AWS D1.1 minimum fillet weld size"
            },
            {
              "id": "base_combined",
              "title": "Pulling and bending at the base",
              "demand": 0.5403372304730611,
              "capacity": 1.0,
              "unit": "ratio",
              "utilization": 0.5403372304730611,
              "passed": true,
              "severity": "required",
              "source": "ASME BTH-1, members: combined axial tension and bending"
            },
            {
              "id": "base_shear",
              "title": "Shear at the base",
              "demand": 11.113497960362634,
              "capacity": 68.31978185410571,
              "unit": "MPa",
              "utilization": 0.16266881507460146,
              "passed": true,
              "severity": "required",
              "source": "ASME BTH-1, members: allowable shear stress"
            },
            {
              "id": "base_weld",
              "title": "Base weld strength",
              "demand": 54.027429722510405,
              "capacity": 80.33333333333334,
              "unit": "MPa",
              "utilization": 0.6725406189524116,
              "passed": true,
              "severity": "required",
              "source": "ASME BTH-1, welded connections: fillet weld allowable shear"
            },
            {
              "id": "base_weld_size",
              "title": "Base weld size",
              "demand": 5.0,
              "capacity": 5.0,
              "unit": "mm",
              "utilization": 1.0,
              "passed": true,
              "severity": "advice",
              "source": "AWS D1.1 minimum fillet weld size"
            },
            {
              "id": "shackle_rating",
              "title": "Shackle is rated for the load",
              "demand": 2.8867513459481287,
              "capacity": 4.75,
              "unit": "t",
              "utilization": 0.6077371254627639,
              "passed": true,
              "severity": "required",
              "source": "Crosby G-2130 working load limit"
            },
            {
              "id": "shackle_fit",
              "title": "Padeye fits inside the shackle",
              "demand": 22.0,
              "capacity": 31.8,
              "unit": "mm",
              "utilization": 0.6918238993710691,
              "passed": true,
              "severity": "required",
              "source": "NEMO practice"
            },
            {
              "id": "shackle_fill",
              "title": "Padeye fills the shackle jaw",
              "demand": 19.08,
              "capacity": 20.0,
              "unit": "mm",
              "utilization": 0.954,
              "passed": true,
              "severity": "advice",
              "source": "NEMO practice (rigging guidance)"
            }
          ],
          "fea": {
            "model": null,
            "region": null,
            "head_von_mises_mpa": 201.28758115310586,
            "yield_strength_mpa": 355.0,
            "factor_of_safety_on_yield": 1.7636458144428468,
            "convergence_change": 0.006644170301354264,
            "convergence_change_pct": 0.6644170301354264,
            "converged": true,
            "hand_stress_mpa": null,
            "hand_label": null,
            "max_reaction_balance_error": 6.984659557218613e-13,
            "levels": [
              {
                "level": 1,
                "elements": 5011,
                "dofs": 27867,
                "head_von_mises_mpa": 198.325008265487,
                "max_von_mises_mpa": 198.325008265487,
                "max_displacement_mm": 0.08407644811246795,
                "reaction_balance_error": 6.984659557218613e-13,
                "solve_seconds": 6.69712770000001
              },
              {
                "level": 2,
                "elements": 12648,
                "dofs": 65556,
                "head_von_mises_mpa": 199.95019218437696,
                "max_von_mises_mpa": 199.95019218437696,
                "max_displacement_mm": 0.08496790736183539,
                "reaction_balance_error": 6.910361452695274e-13,
                "solve_seconds": 21.537560400000075
              },
              {
                "level": 3,
                "elements": 32096,
                "dofs": 155709,
                "head_von_mises_mpa": 201.28758115310586,
                "max_von_mises_mpa": 201.28758115310586,
                "max_displacement_mm": 0.0852617808946921,
                "reaction_balance_error": 2.378499437467677e-13,
                "solve_seconds": 38.562379800000144
              }
            ]
          }
        }
      }
    },
    "pipe-bracket": {
      "source_path": "reports/project-report/data/runs/pipe-bracket/20270115-090000-000000/results.json",
      "csv_path": "reports/project-report/data/runs/pipe-bracket/20270115-090000-000000/designs-evaluated.csv",
      "csv_rows": 300,
      "seconds": 67.69998680000003,
      "rule_set": {
        "id": "aisc-360-asd",
        "name": "AISC 360-16, Specification for Structural Steel Buildings, allowable strength design",
        "design_factor": 1.67,
        "omega_tension": 1.67,
        "omega_flexure": 1.67,
        "omega_shear": 1.67,
        "omega_weld": 2.0,
        "omega_bolt": 2.0
      },
      "job": {
        "pipe_nps": "4",
        "schedule": "STD",
        "pipe_material_id": "CS",
        "fluid_id": "sea_water",
        "insulation_id": "none",
        "insulation_thickness_mm": 0.0,
        "span_m": 3.0,
        "continuity_factor": 1.25,
        "pipe_direction": "fore_aft",
        "accel_vertical_g": 1.0,
        "accel_transverse_g": 0.8,
        "accel_longitudinal_g": 0.5,
        "friction": 0.3,
        "gap_mm": 50.0,
        "material_id": "GRADE_A",
        "plate_thicknesses_mm": [
          6.0,
          8.0,
          10.0,
          12.0,
          15.0,
          20.0
        ],
        "ubolt_grade_id": "4.6",
        "propeller_rpm": 120.0,
        "propeller_blades": 4,
        "engine_rpm": 750.0,
        "engine_cylinders": 6,
        "engine_stroke": 4,
        "frequency_margin": 0.2,
        "deflection_limit_mm": 1.0,
        "electrode_strength_mpa": 482.0,
        "rule_set_id": "aisc-360-asd",
        "include_bracket_flexibility": true,
        "part": "pipe-bracket"
      },
      "loads": {
        "mass_per_m": {
          "pipe": 16.075491783643436,
          "contents": 8.418317931076734,
          "insulation": 0.0,
          "total": 24.49380971472017
        },
        "weight_per_m_n": 240.20221903886056,
        "static_n": 900.7583213957272,
        "down_n": 1801.5166427914544,
        "up_n": 0.0,
        "across_n": 720.6066571165818,
        "along_n": 540.4549928374363,
        "accel": {
          "vertical_g": 1.0,
          "across_g": 0.8,
          "direction": "fore_aft"
        },
        "sling_force_n": 1801.5166427914544,
        "sling_force_t": 0.1837035728604013
      },
      "material": {
        "id": "GRADE_A",
        "name": "Shipbuilding steel grade A (normal strength)",
        "source": "IACS UR W11, normal strength hull structural steel",
        "tensile_strength_mpa": 400.0,
        "elastic_modulus_gpa": 206.0,
        "density_kg_m3": 7850.0
      },
      "stock_material": null,
      "search": {
        "combinations": 63,
        "evaluations": 300,
        "skipped": 60
      },
      "designs": {
        "lightest": {
          "label": "Lightest",
          "target_utilization": 1.0,
          "mass_kg": 0.9957940366295602,
          "governing_id": "root_weld",
          "governing_title": "Welds to the bulkhead",
          "governing_utilization": 0.2539839513591594,
          "governing_source": "AISC 360-16 (ASD): fillet welds, J2.4 (elastic method)",
          "passed": true,
          "design": {
            "seat_length_mm": 195.0,
            "seat_width_mm": 50.0,
            "seat_thickness_mm": 6.0,
            "knee_depth_mm": 60.0,
            "knee_thickness_mm": 6.0,
            "pipe_offset_mm": 107.15,
            "pipe_od_mm": 114.3,
            "ubolt_diameter_mm": 12,
            "root_weld_mm": 3.0,
            "knee_weld_mm": 3.0
          },
          "shackle": null,
          "span": {
            "natural_hz": 27.5688048323118,
            "excitations": [
              {
                "name": "Propeller shaft rotation",
                "hz": 2.0
              },
              {
                "name": "Propeller blade rate",
                "hz": 8.0
              },
              {
                "name": "Blade rate, second harmonic",
                "hz": 16.0
              },
              {
                "name": "Engine rotation",
                "hz": 12.5
              },
              {
                "name": "Engine firing",
                "hz": 37.5
              }
            ],
            "nearest": {
              "name": "Engine firing",
              "hz": 37.5
            },
            "separation": 0.26483187113835205,
            "pipe_stress_mpa": 8.84002117520464,
            "pipe_allow_mpa": 143.7125748502994,
            "sag_mm": 0.4145370302636079,
            "spans_m": {
              "stress": 12.0960058263021,
              "sag": 4.701272489127292,
              "frequency": 2.348139894993984
            },
            "recommended_m": 2.3,
            "steps": [
              {
                "label": "Pipe bending stiffness",
                "symbol": "EI",
                "formula": "EI = E \u03c0/64 (D^4 \u2212 d^4)",
                "substituted": "EI = 203\u2009000 MPa \u00d7 3\u2009010\u2009519 mm\u2074",
                "value": 611135.4581072,
                "unit": "N\u00b7m\u00b2",
                "result": "611\u2009135 N\u00b7m\u00b2",
                "note": ""
              },
              {
                "label": "Natural frequency of one span",
                "symbol": "f_n",
                "formula": "f_n = (\u03c0/2) \u221a(EI / (m S^4))",
                "substituted": "f_n = (\u03c0/2) \u00d7 \u221a(611\u2009135 / (24.49 \u00d7 3.00\u2074))",
                "value": 27.5688048323118,
                "unit": "Hz",
                "result": "27.57 Hz",
                "note": "Simply supported span: the lowest, safest estimate."
              },
              {
                "label": "Nearest excitation",
                "symbol": "f_e",
                "formula": "Engine firing",
                "substituted": "f_e = 37.50 Hz",
                "value": 37.5,
                "unit": "Hz",
                "result": "37.50 Hz",
                "note": ""
              },
              {
                "label": "Separation",
                "symbol": "\u0394",
                "formula": "\u0394 = |f_n \u2212 f_e| / f_e",
                "substituted": "\u0394 = |27.57 \u2212 37.50| / 37.50",
                "value": 26.483187113835204,
                "unit": "%",
                "result": "26.48 %",
                "note": "Must be at least 20%."
              },
              {
                "label": "Pipe bending between supports",
                "symbol": "\u03c3_p",
                "formula": "\u03c3_p = q_d S^2 / (10 Z)",
                "substituted": "\u03c3_p = 0.5174 N/mm \u00d7 3\u2009000\u00b2 / (10 \u00d7 52\u2009678)",
                "value": 8.84002117520464,
                "unit": "MPa",
                "result": "8.840 MPa",
                "note": "q_d is the pipe weight with the vertical and horizontal accelerations combined; S\u00b2/10 for a continuous pipe."
              },
              {
                "label": "Sag under its own weight",
                "symbol": "\u03b4_p",
                "formula": "\u03b4_p = 5 q S^4 / (384 E I)",
                "substituted": "\u03b4_p = 5 \u00d7 0.2402 \u00d7 3\u2009000\u2074 / (384 \u00d7 203\u2009000 \u00d7 3\u2009010\u2009519)",
                "value": 0.4145370302636079,
                "unit": "mm",
                "result": "0.4145 mm",
                "note": ""
              },
              {
                "label": "Longest spacing",
                "symbol": "S_{max}",
                "formula": "smallest of the stress, sag and frequency limits",
                "substituted": "stress 12.10 m, sag 4.70 m, frequency 2.35 m",
                "value": 2.3,
                "unit": "m",
                "result": "2.300 m",
                "note": "The frequency limit keeps f_n 20% above the highest excitation (37.50 Hz)."
              }
            ]
          },
          "checks": [
            {
              "id": "arm_bending",
              "title": "Bending along the bracket arm",
              "demand": 0.19114034248074413,
              "capacity": 1.0,
              "unit": "ratio",
              "utilization": 0.19114034248074413,
              "passed": true,
              "severity": "required",
              "source": "AISC 360-16 (ASD): combined axial force and flexure (Chapter H)"
            },
            {
              "id": "arm_shear",
              "title": "Shear in the arm",
              "demand": 2.885338600962067,
              "capacity": 84.43113772455091,
              "unit": "MPa",
              "utilization": 0.034173868536217386,
              "passed": true,
              "severity": "required",
              "source": "AISC 360-16 (ASD): shear yield of plate webs (Chapter G)"
            },
            {
              "id": "root_weld",
              "title": "Welds to the bulkhead",
              "demand": 36.72607936653445,
              "capacity": 144.6,
              "unit": "MPa",
              "utilization": 0.2539839513591594,
              "passed": true,
              "severity": "required",
              "source": "AISC 360-16 (ASD): fillet welds, J2.4 (elastic method)"
            },
            {
              "id": "knee_weld",
              "title": "Knee-to-seat welds",
              "demand": 3.3154253784063057,
              "capacity": 144.6,
              "unit": "MPa",
              "utilization": 0.02292825296269921,
              "passed": true,
              "severity": "required",
              "source": "AISC 360-16 (ASD): fillet welds, J2.4 (shear flow VQ/I)"
            },
            {
              "id": "seat_bending",
              "title": "Seat plate between the knees",
              "demand": 37.531596724821966,
              "capacity": 211.07784431137725,
              "unit": "MPa",
              "utilization": 0.17780926675305725,
              "passed": true,
              "severity": "required",
              "source": "AISC 360-16 (ASD): flexure of plates about their weak axis (F11)"
            },
            {
              "id": "ubolt",
              "title": "U-bolt legs",
              "demand": 0.00292020211058713,
              "capacity": 1.0,
              "unit": "ratio",
              "utilization": 0.00292020211058713,
              "passed": true,
              "severity": "required",
              "source": "AISC 360-16 (ASD): bolts in tension and shear, J3.6 and J3.7 (elliptical interaction)"
            },
            {
              "id": "deflection",
              "title": "Bracket deflection under the pipe",
              "demand": 0.015640856964106636,
              "capacity": 1.0,
              "unit": "mm",
              "utilization": 0.015640856964106636,
              "passed": true,
              "severity": "required",
              "source": "Design limit set for this job"
            },
            {
              "id": "knee_edge",
              "title": "Knee free edge",
              "demand": 204.02205763103166,
              "capacity": 300.0,
              "unit": "mm",
              "utilization": 0.6800735254367722,
              "passed": true,
              "severity": "advice",
              "source": "NEMO practice, after ship-structure bracket rules (unflanged free edge up to 50 t \u221a(235/F_y))"
            },
            {
              "id": "root_weld_size",
              "title": "Bulkhead weld size",
              "demand": 3.0,
              "capacity": 3.0,
              "unit": "mm",
              "utilization": 1.0,
              "passed": true,
              "severity": "advice",
              "source": "AWS D1.1 minimum fillet weld size"
            },
            {
              "id": "knee_weld_size",
              "title": "Knee weld size",
              "demand": 3.0,
              "capacity": 3.0,
              "unit": "mm",
              "utilization": 1.0,
              "passed": true,
              "severity": "advice",
              "source": "AWS D1.1 minimum fillet weld size"
            },
            {
              "id": "pipe_vibration",
              "title": "Pipe span clear of vibration",
              "demand": 0.2,
              "capacity": 0.26483187113835205,
              "unit": "ratio",
              "utilization": 0.7551961142000053,
              "passed": true,
              "severity": "required",
              "source": "NEMO practice: natural frequency at least 20% from every excitation"
            },
            {
              "id": "pipe_stress",
              "title": "Pipe bending between supports",
              "demand": 8.84002117520464,
              "capacity": 143.7125748502994,
              "unit": "MPa",
              "utilization": 0.06151181401079896,
              "passed": true,
              "severity": "required",
              "source": "AISC 360-16 (ASD): flexure, applied to the pipe as a continuous beam"
            },
            {
              "id": "pipe_sag",
              "title": "Pipe sag between supports",
              "demand": 0.4145370302636079,
              "capacity": 2.5,
              "unit": "mm",
              "utilization": 0.16581481210544316,
              "passed": true,
              "severity": "advice",
              "source": "MSS SP-58 / SP-69 style span guidance (2.5 mm sag)"
            },
            {
              "id": "span_limit",
              "title": "Support spacing within NEMO's recommended maximum",
              "demand": 3.0,
              "capacity": 2.3,
              "unit": "m",
              "utilization": 1.3043478260869565,
              "passed": false,
              "severity": "advice",
              "source": "NEMO: smallest of the stress, sag and frequency limits"
            },
            {
              "id": "support_vibration",
              "title": "Pipe on its brackets clear of vibration",
              "demand": 0.2,
              "capacity": 0.27347264275149663,
              "unit": "ratio",
              "utilization": 0.7313345788000415,
              "passed": true,
              "severity": "required",
              "source": "NEMO practice: Dunkerley's combination of the pipe span and bracket frequencies, at least 20% from every excitation"
            }
          ],
          "fea": {
            "model": null,
            "region": "away from the bulkhead face (x \u2265 9 mm)",
            "head_von_mises_mpa": 34.39479697821678,
            "yield_strength_mpa": 235.0,
            "factor_of_safety_on_yield": 6.8324287580133785,
            "convergence_change": 0.007042799309546171,
            "convergence_change_pct": 0.704279930954617,
            "converged": true,
            "hand_stress_mpa": 37.531596724821966,
            "hand_label": "seat plate between the knees",
            "max_reaction_balance_error": 5.672629380710076e-13,
            "levels": [
              {
                "level": 1,
                "elements": 4033,
                "dofs": 25266,
                "head_von_mises_mpa": 34.71138387760574,
                "max_von_mises_mpa": 35.59462226825658,
                "max_displacement_mm": 0.05366406104599715,
                "reaction_balance_error": 5.34184433347865e-13,
                "solve_seconds": 5.712031899999829
              },
              {
                "level": 2,
                "elements": 7698,
                "dofs": 47280,
                "head_von_mises_mpa": 34.63703263062695,
                "max_von_mises_mpa": 40.85817727693119,
                "max_displacement_mm": 0.053103486783787436,
                "reaction_balance_error": 5.672629380710076e-13,
                "solve_seconds": 13.825604800000065
              },
              {
                "level": 3,
                "elements": 16536,
                "dofs": 97380,
                "head_von_mises_mpa": 34.39479697821678,
                "max_von_mises_mpa": 46.8276375863004,
                "max_displacement_mm": 0.053378844504036765,
                "reaction_balance_error": 2.932761930961353e-13,
                "solve_seconds": 39.07646829999999
              }
            ]
          }
        }
      }
    },
    "stabilizer": {
      "source_path": "reports/project-report/data/runs/stabilizer/20270115-090000-000000/results.json",
      "csv_path": "reports/project-report/data/runs/stabilizer/20270115-090000-000000/designs-evaluated.csv",
      "csv_rows": 3780,
      "seconds": 162.91520650000007,
      "rule_set": {
        "id": "iacs-ur-s10",
        "name": "IACS UR S10, Rudders, sole pieces and rudder horns (Rev.8, 2025), applied to a stabilizer fin",
        "design_factor": 2.1363636363636362
      },
      "job": {
        "speed_kn": 18.0,
        "span_m": 1.4,
        "chord_m": 1.2,
        "thickness_ratio": 0.2,
        "max_angle_deg": 22.0,
        "stock_position": 0.35,
        "depth_m": 3.0,
        "draught_m": 5.0,
        "bearing_gap_mm": 200.0,
        "material_id": "AH36",
        "stock_material_id": "42CRMO4_QT",
        "plate_thicknesses_mm": [
          8.0,
          10.0,
          12.0,
          15.0,
          20.0,
          25.0
        ],
        "front_spar": 0.15,
        "rear_spar": 0.65,
        "deflection_limit_mm": 10.0,
        "rule_set_id": "iacs-ur-s10",
        "include_astern": true,
        "astern_speed_kn": 0.0,
        "check_bearings": false,
        "bearing_spacing_mm": 800.0,
        "bearing_material": "synthetic",
        "part": "stabilizer"
      },
      "loads": {
        "speed_ms": 9.259992,
        "lift_coefficient": 1.0901978115188686,
        "lift_slope_per_rad": 2.707612918505479,
        "nemo_lift_n": 80487.73021618668,
        "ur_s10_force_n": 66740.88960000001,
        "design_force_n": 80487.73021618668,
        "lever_m": 0.12,
        "torque_nm": 9658.5276259424,
        "root_moment_nm": 56341.41115133068,
        "stock_moment_nm": 72438.957194568,
        "section_angle_deg": 8.474985053563763,
        "cp_min": -2.910313075744681,
        "cavitation_number": 2.953208969693507,
        "astern_speed_kn": 9.0,
        "astern_force_n": 12134.7072,
        "astern_lever_m": 0.37200000000000005,
        "astern_torque_nm": 4514.111078400001,
        "astern_stock_moment_nm": 10921.23648,
        "outer_bearing_n": 0.0,
        "inner_bearing_n": 0.0,
        "area_m2": 1.68,
        "effective_aspect_ratio": 2.3333333333333335,
        "span_arm_m": 0.7,
        "sling_force_n": 80487.73021618668,
        "sling_force_t": 8.207464344723904
      },
      "material": {
        "id": "AH36",
        "name": "Shipbuilding steel AH36 (higher strength)",
        "source": "IACS UR W11, higher strength hull structural steel, grade AH36",
        "tensile_strength_mpa": 490.0,
        "elastic_modulus_gpa": 206.0,
        "density_kg_m3": 7850.0
      },
      "stock_material": {
        "id": "42CRMO4_QT",
        "name": "Forged steel 42CrMo4, quenched and tempered (stocks)",
        "source": "EN 10083-3, 42CrMo4 (1.7225) +QT. Tensile strength is the minimum for the largest size band; check the mill certificate.",
        "tensile_strength_mpa": 750.0,
        "elastic_modulus_gpa": 210.0,
        "density_kg_m3": 7850.0
      },
      "search": {
        "combinations": 108,
        "evaluations": 3780,
        "skipped": 0
      },
      "designs": {
        "lightest": {
          "label": "Lightest",
          "target_utilization": 1.0,
          "mass_kg": 457.45129812815543,
          "governing_id": "stock_combined",
          "governing_title": "Stock bending and twisting at the outer bearing",
          "governing_utilization": 0.9453618709860613,
          "governing_source": "IACS UR S10.4.2: equivalent stress in the stock, ahead and astern",
          "passed": true,
          "design": {
            "span_mm": 1400.0,
            "chord_mm": 1200.0,
            "thickness_ratio": 0.2,
            "stock_position": 0.35,
            "front_spar": 0.15,
            "rear_spar": 0.65,
            "skin_mm": 8.0,
            "web_mm": 8.0,
            "rib_spacing_mm": 350.0,
            "stock_diameter_mm": 160.0,
            "bearing_gap_mm": 200.0
          },
          "shackle": null,
          "span": null,
          "checks": [
            {
              "id": "stock_torsion",
              "title": "Stock twisting",
              "demand": 12.025998753004453,
              "capacity": 110.69229742177005,
              "unit": "MPa",
              "utilization": 0.10864350124726274,
              "passed": true,
              "severity": "required",
              "source": "IACS UR S10.4.1: torsional stress in the stock, ahead and astern"
            },
            {
              "id": "stock_combined",
              "title": "Stock bending and twisting at the outer bearing",
              "demand": 181.58859900791225,
              "capacity": 192.08369258483629,
              "unit": "MPa",
              "utilization": 0.9453618709860613,
              "passed": true,
              "severity": "required",
              "source": "IACS UR S10.4.2: equivalent stress in the stock, ahead and astern"
            },
            {
              "id": "stock_fit",
              "title": "Stock fits inside the foil",
              "demand": 160.0,
              "capacity": 214.08218732209156,
              "unit": "mm",
              "utilization": 0.7473765192770397,
              "passed": true,
              "severity": "required",
              "source": "NEMO practice"
            },
            {
              "id": "fin_bending",
              "title": "Fin body bending at the root",
              "demand": 55.69279051765012,
              "capacity": 146.0704537957944,
              "unit": "MPa",
              "utilization": 0.3812734818740845,
              "passed": true,
              "severity": "required",
              "source": "IACS UR S10.5.1: bending stress in the rudder blade"
            },
            {
              "id": "fin_shear",
              "title": "Spar web shear at the root",
              "demand": 31.210080194143643,
              "capacity": 66.39566081627018,
              "unit": "MPa",
              "utilization": 0.47006204638143534,
              "passed": true,
              "severity": "required",
              "source": "IACS UR S10.5.1: shear stress in the rudder blade"
            },
            {
              "id": "fin_equivalent",
              "title": "Fin skin combined stress",
              "demand": 56.261811155444256,
              "capacity": 159.34958595904843,
              "unit": "MPa",
              "utilization": 0.3530715867056165,
              "passed": true,
              "severity": "required",
              "source": "IACS UR S10.5.1: equivalent stress in the rudder blade"
            },
            {
              "id": "skin_thickness",
              "title": "Skin plate thickness",
              "demand": 7.540423673479692,
              "capacity": 8.0,
              "unit": "mm",
              "utilization": 0.9425529591849615,
              "passed": true,
              "severity": "required",
              "source": "IACS UR S10.5.2: rudder plating"
            },
            {
              "id": "web_thickness",
              "title": "Spar and rib web thickness",
              "demand": 8.0,
              "capacity": 8.0,
              "unit": "mm",
              "utilization": 1.0,
              "passed": true,
              "severity": "required",
              "source": "IACS UR S10.5.2: web plates at least 70% of the side plating and 8 mm"
            },
            {
              "id": "skin_buckling",
              "title": "Skin panel buckling",
              "demand": 55.69279051765012,
              "capacity": 116.48944803492725,
              "unit": "MPa",
              "utilization": 0.47809300719625386,
              "passed": true,
              "severity": "required",
              "source": "NEMO practice: plate buckling (Timoshenko) with Johnson-Ostenfeld correction, factor 1.5"
            },
            {
              "id": "tip_deflection",
              "title": "Fin tip deflection",
              "demand": 0.8901751244922316,
              "capacity": 10.0,
              "unit": "mm",
              "utilization": 0.08901751244922315,
              "passed": true,
              "severity": "required",
              "source": "Design limit set for this job"
            },
            {
              "id": "cavitation",
              "title": "Cavitation at the largest fin angle",
              "demand": 2.910313075744681,
              "capacity": 2.953208969693507,
              "unit": "ratio",
              "utilization": 0.9854748192935099,
              "passed": true,
              "severity": "advice",
              "source": "Panel method pressure against the cavitation number"
            }
          ],
          "fea": {
            "model": "stock",
            "region": "stock from 80 mm outboard of the bearing to the loaded length",
            "head_von_mises_mpa": 165.26262078584597,
            "yield_strength_mpa": 550.0,
            "factor_of_safety_on_yield": 3.3280362938980157,
            "convergence_change": 0.001166476326596623,
            "convergence_change_pct": 0.11664763265966231,
            "converged": true,
            "hand_stress_mpa": 165.66998500379137,
            "hand_label": "stock, beam theory with bending and twist",
            "max_reaction_balance_error": 9.89048964198333e-12,
            "levels": [
              {
                "level": 1,
                "elements": 2232,
                "dofs": 12354,
                "head_von_mises_mpa": 168.7203000078561,
                "max_von_mises_mpa": 188.44691817747207,
                "max_displacement_mm": 3.902701044756821,
                "reaction_balance_error": 7.681960478525146e-12,
                "solve_seconds": 2.5239004000000023
              },
              {
                "level": 2,
                "elements": 6160,
                "dofs": 31584,
                "head_von_mises_mpa": 165.45539572066397,
                "max_von_mises_mpa": 184.6475088767516,
                "max_displacement_mm": 3.8170320848009065,
                "reaction_balance_error": 2.434766438898042e-12,
                "solve_seconds": 7.803573700000015
              },
              {
                "level": 3,
                "elements": 15758,
                "dofs": 75831,
                "head_von_mises_mpa": 165.26262078584597,
                "max_von_mises_mpa": 190.03704473920558,
                "max_displacement_mm": 3.7735740330626215,
                "reaction_balance_error": 9.89048964198333e-12,
                "solve_seconds": 24.312752300000056
              }
            ]
          }
        },
        "balanced": {
          "label": "Balanced (at least 15% spare)",
          "target_utilization": 0.85,
          "mass_kg": 475.7624636086852,
          "governing_id": "stock_combined",
          "governing_title": "Stock bending and twisting at the outer bearing",
          "governing_utilization": 0.7881543300547338,
          "governing_source": "IACS UR S10.4.2: equivalent stress in the stock, ahead and astern",
          "passed": true,
          "design": {
            "span_mm": 1400.0,
            "chord_mm": 1200.0,
            "thickness_ratio": 0.2,
            "stock_position": 0.35,
            "front_spar": 0.15,
            "rear_spar": 0.65,
            "skin_mm": 8.0,
            "web_mm": 8.0,
            "rib_spacing_mm": 350.0,
            "stock_diameter_mm": 170.0,
            "bearing_gap_mm": 200.0
          },
          "shackle": null,
          "span": null,
          "checks": [
            {
              "id": "stock_torsion",
              "title": "Stock twisting",
              "demand": 10.026153244922906,
              "capacity": 110.69229742177005,
              "unit": "MPa",
              "utilization": 0.09057679240968618,
              "passed": true,
              "severity": "required",
              "source": "IACS UR S10.4.1: torsional stress in the stock, ahead and astern"
            },
            {
              "id": "stock_combined",
              "title": "Stock bending and twisting at the outer bearing",
              "demand": 151.39159404364108,
              "capacity": 192.08369258483629,
              "unit": "MPa",
              "utilization": 0.7881543300547338,
              "passed": true,
              "severity": "required",
              "source": "IACS UR S10.4.2: equivalent stress in the stock, ahead and astern"
            },
            {
              "id": "stock_fit",
              "title": "Stock fits inside the foil",
              "demand": 170.0,
              "capacity": 214.08218732209156,
              "unit": "mm",
              "utilization": 0.7940875517318547,
              "passed": true,
              "severity": "required",
              "source": "NEMO practice"
            },
            {
              "id": "fin_bending",
              "title": "Fin body bending at the root",
              "demand": 55.69279051765012,
              "capacity": 146.0704537957944,
              "unit": "MPa",
              "utilization": 0.3812734818740845,
              "passed": true,
              "severity": "required",
              "source": "IACS UR S10.5.1: bending stress in the rudder blade"
            },
            {
              "id": "fin_shear",
              "title": "Spar web shear at the root",
              "demand": 31.210080194143643,
              "capacity": 66.39566081627018,
              "unit": "MPa",
              "utilization": 0.47006204638143534,
              "passed": true,
              "severity": "required",
              "source": "IACS UR S10.5.1: shear stress in the rudder blade"
            },
            {
              "id": "fin_equivalent",
              "title": "Fin skin combined stress",
              "demand": 56.261811155444256,
              "capacity": 159.34958595904843,
              "unit": "MPa",
              "utilization": 0.3530715867056165,
              "passed": true,
              "severity": "required",
              "source": "IACS UR S10.5.1: equivalent stress in the rudder blade"
            },
            {
              "id": "skin_thickness",
              "title": "Skin plate thickness",
              "demand": 7.540423673479692,
              "capacity": 8.0,
              "unit": "mm",
              "utilization": 0.9425529591849615,
              "passed": true,
              "severity": "required",
              "source": "IACS UR S10.5.2: rudder plating"
            },
            {
              "id": "web_thickness",
              "title": "Spar and rib web thickness",
              "demand": 8.0,
              "capacity": 8.0,
              "unit": "mm",
              "utilization": 1.0,
              "passed": true,
              "severity": "required",
              "source": "IACS UR S10.5.2: web plates at least 70% of the side plating and 8 mm"
            },
            {
              "id": "skin_buckling",
              "title": "Skin panel buckling",
              "demand": 55.69279051765012,
              "capacity": 116.48944803492725,
              "unit": "MPa",
              "utilization": 0.47809300719625386,
              "passed": true,
              "severity": "required",
              "source": "NEMO practice: plate buckling (Timoshenko) with Johnson-Ostenfeld correction, factor 1.5"
            },
            {
              "id": "tip_deflection",
              "title": "Fin tip deflection",
              "demand": 0.8901751244922316,
              "capacity": 10.0,
              "unit": "mm",
              "utilization": 0.08901751244922315,
              "passed": true,
              "severity": "required",
              "source": "Design limit set for this job"
            },
            {
              "id": "cavitation",
              "title": "Cavitation at the largest fin angle",
              "demand": 2.910313075744681,
              "capacity": 2.953208969693507,
              "unit": "ratio",
              "utilization": 0.9854748192935099,
              "passed": true,
              "severity": "advice",
              "source": "Panel method pressure against the cavitation number"
            }
          ],
          "fea": {
            "model": "stock",
            "region": "stock from 85 mm outboard of the bearing to the loaded length",
            "head_von_mises_mpa": 136.8595443875623,
            "yield_strength_mpa": 500.0,
            "factor_of_safety_on_yield": 3.6533805679206957,
            "convergence_change": 0.0038688721660991125,
            "convergence_change_pct": 0.38688721660991127,
            "converged": true,
            "hand_stress_mpa": 137.2912997920541,
            "hand_label": "stock, beam theory with bending and twist",
            "max_reaction_balance_error": 5.234483411916635e-12,
            "levels": [
              {
                "level": 1,
                "elements": 2131,
                "dofs": 11715,
                "head_von_mises_mpa": 140.44606093323964,
                "max_von_mises_mpa": 153.41277665782562,
                "max_displacement_mm": 3.057168619499709,
                "reaction_balance_error": 2.5753768703687366e-12,
                "solve_seconds": 2.3391211999999086
              },
              {
                "level": 2,
                "elements": 5644,
                "dofs": 28935,
                "head_von_mises_mpa": 137.38903646950834,
                "max_von_mises_mpa": 152.57006142673515,
                "max_displacement_mm": 3.0038040498008862,
                "reaction_balance_error": 5.234483411916635e-12,
                "solve_seconds": 6.8115060000000085
              },
              {
                "level": 3,
                "elements": 15030,
                "dofs": 72174,
                "head_von_mises_mpa": 136.8595443875623,
                "max_von_mises_mpa": 158.97027024368128,
                "max_displacement_mm": 2.9708615219472616,
                "reaction_balance_error": 3.45511710268997e-12,
                "solve_seconds": 21.696576899999855
              }
            ]
          }
        },
        "robust": {
          "label": "Extra margin (at least 30% spare)",
          "target_utilization": 0.7,
          "mass_kg": 495.1833966940956,
          "governing_id": "stock_combined",
          "governing_title": "Stock bending and twisting at the outer bearing",
          "governing_utilization": 0.6639578572631869,
          "governing_source": "IACS UR S10.4.2: equivalent stress in the stock, ahead and astern",
          "passed": true,
          "design": {
            "span_mm": 1400.0,
            "chord_mm": 1200.0,
            "thickness_ratio": 0.2,
            "stock_position": 0.35,
            "front_spar": 0.15,
            "rear_spar": 0.65,
            "skin_mm": 8.0,
            "web_mm": 8.0,
            "rib_spacing_mm": 350.0,
            "stock_diameter_mm": 180.0,
            "bearing_gap_mm": 200.0
          },
          "shackle": null,
          "span": null,
          "checks": [
            {
              "id": "stock_torsion",
              "title": "Stock twisting",
              "demand": 8.446243294291193,
              "capacity": 110.69229742177005,
              "unit": "MPa",
              "utilization": 0.07630380334512829,
              "passed": true,
              "severity": "required",
              "source": "IACS UR S10.4.1: torsional stress in the stock, ahead and astern"
            },
            {
              "id": "stock_combined",
              "title": "Stock bending and twisting at the outer bearing",
              "demand": 127.53547694382861,
              "capacity": 192.08369258483629,
              "unit": "MPa",
              "utilization": 0.6639578572631869,
              "passed": true,
              "severity": "required",
              "source": "IACS UR S10.4.2: equivalent stress in the stock, ahead and astern"
            },
            {
              "id": "stock_fit",
              "title": "Stock fits inside the foil",
              "demand": 180.0,
              "capacity": 214.08218732209156,
              "unit": "mm",
              "utilization": 0.8407985841866698,
              "passed": true,
              "severity": "required",
              "source": "NEMO practice"
            },
            {
              "id": "fin_bending",
              "title": "Fin body bending at the root",
              "demand": 55.69279051765012,
              "capacity": 146.0704537957944,
              "unit": "MPa",
              "utilization": 0.3812734818740845,
              "passed": true,
              "severity": "required",
              "source": "IACS UR S10.5.1: bending stress in the rudder blade"
            },
            {
              "id": "fin_shear",
              "title": "Spar web shear at the root",
              "demand": 31.210080194143643,
              "capacity": 66.39566081627018,
              "unit": "MPa",
              "utilization": 0.47006204638143534,
              "passed": true,
              "severity": "required",
              "source": "IACS UR S10.5.1: shear stress in the rudder blade"
            },
            {
              "id": "fin_equivalent",
              "title": "Fin skin combined stress",
              "demand": 56.261811155444256,
              "capacity": 159.34958595904843,
              "unit": "MPa",
              "utilization": 0.3530715867056165,
              "passed": true,
              "severity": "required",
              "source": "IACS UR S10.5.1: equivalent stress in the rudder blade"
            },
            {
              "id": "skin_thickness",
              "title": "Skin plate thickness",
              "demand": 7.540423673479692,
              "capacity": 8.0,
              "unit": "mm",
              "utilization": 0.9425529591849615,
              "passed": true,
              "severity": "required",
              "source": "IACS UR S10.5.2: rudder plating"
            },
            {
              "id": "web_thickness",
              "title": "Spar and rib web thickness",
              "demand": 8.0,
              "capacity": 8.0,
              "unit": "mm",
              "utilization": 1.0,
              "passed": true,
              "severity": "required",
              "source": "IACS UR S10.5.2: web plates at least 70% of the side plating and 8 mm"
            },
            {
              "id": "skin_buckling",
              "title": "Skin panel buckling",
              "demand": 55.69279051765012,
              "capacity": 116.48944803492725,
              "unit": "MPa",
              "utilization": 0.47809300719625386,
              "passed": true,
              "severity": "required",
              "source": "NEMO practice: plate buckling (Timoshenko) with Johnson-Ostenfeld correction, factor 1.5"
            },
            {
              "id": "tip_deflection",
              "title": "Fin tip deflection",
              "demand": 0.8901751244922316,
              "capacity": 10.0,
              "unit": "mm",
              "utilization": 0.08901751244922315,
              "passed": true,
              "severity": "required",
              "source": "Design limit set for this job"
            },
            {
              "id": "cavitation",
              "title": "Cavitation at the largest fin angle",
              "demand": 2.910313075744681,
              "capacity": 2.953208969693507,
              "unit": "ratio",
              "utilization": 0.9854748192935099,
              "passed": true,
              "severity": "advice",
              "source": "Panel method pressure against the cavitation number"
            }
          ],
          "fea": {
            "model": "stock",
            "region": "stock from 90 mm outboard of the bearing to the loaded length",
            "head_von_mises_mpa": 114.23182886567585,
            "yield_strength_mpa": 500.0,
            "factor_of_safety_on_yield": 4.377063774300115,
            "convergence_change": 0.00698316505206829,
            "convergence_change_pct": 0.698316505206829,
            "converged": true,
            "hand_stress_mpa": 114.95892539043238,
            "hand_label": "stock, beam theory with bending and twist",
            "max_reaction_balance_error": 5.037684497889455e-12,
            "levels": [
              {
                "level": 1,
                "elements": 1991,
                "dofs": 10989,
                "head_von_mises_mpa": 115.98898775283253,
                "max_von_mises_mpa": 132.24285123716578,
                "max_displacement_mm": 2.436292866975789,
                "reaction_balance_error": 5.037684497889455e-12,
                "solve_seconds": 2.2535903000000417
              },
              {
                "level": 2,
                "elements": 5391,
                "dofs": 27612,
                "head_von_mises_mpa": 115.02952858084448,
                "max_von_mises_mpa": 128.46930799985913,
                "max_displacement_mm": 2.3973566031681406,
                "reaction_balance_error": 2.583853494270265e-12,
                "solve_seconds": 6.551681299999927
              },
              {
                "level": 3,
                "elements": 14153,
                "dofs": 68112,
                "head_von_mises_mpa": 114.23182886567585,
                "max_von_mises_mpa": 134.80977298552577,
                "max_displacement_mm": 2.369128581318476,
                "reaction_balance_error": 4.475729474568303e-12,
                "solve_seconds": 21.209896299999855
              }
            ]
          }
        }
      }
    }
  },
  "sweeps": {
    "padeye": [
      {
        "angle": 45,
        "load_t": 1,
        "mass_kg": 0.053050551791734735,
        "sling_t": 0.7071067811865476,
        "shackle_t": 0.75,
        "governing": "Base weld strength",
        "use": 0.9730610798695127,
        "plate_mm": 10.0,
        "cheeks": false
      },
      {
        "angle": 45,
        "load_t": 2,
        "mass_kg": 0.10661631207388013,
        "sling_t": 1.4142135623730951,
        "shackle_t": 1.5,
        "governing": "Base weld strength",
        "use": 0.9587678661794332,
        "plate_mm": 12.0,
        "cheeks": false
      },
      {
        "angle": 45,
        "load_t": 5,
        "mass_kg": 0.39999427819143923,
        "sling_t": 3.5355339059327373,
        "shackle_t": 4.75,
        "governing": "Base weld strength",
        "use": 0.9750490506499965,
        "plate_mm": 8.0,
        "cheeks": true
      },
      {
        "angle": 45,
        "load_t": 10,
        "mass_kg": 0.9898889490379804,
        "sling_t": 7.071067811865475,
        "shackle_t": 8.5,
        "governing": "Base weld strength",
        "use": 0.9782635510706156,
        "plate_mm": 12.0,
        "cheeks": true
      },
      {
        "angle": 45,
        "load_t": 20,
        "mass_kg": 2.7717671499937793,
        "sling_t": 14.14213562373095,
        "shackle_t": 17.0,
        "governing": "Splitting above the hole",
        "use": 0.9924977339846054,
        "plate_mm": 15.0,
        "cheeks": true
      },
      {
        "angle": 45,
        "load_t": 30,
        "mass_kg": 5.084681951520677,
        "sling_t": 21.213203435596423,
        "shackle_t": 25.0,
        "governing": "Splitting above the hole",
        "use": 0.970964827393523,
        "plate_mm": 20.0,
        "cheeks": true
      },
      {
        "angle": 45,
        "load_t": 40,
        "mass_kg": 7.501900866826891,
        "sling_t": 28.2842712474619,
        "shackle_t": 35.0,
        "governing": "Splitting above the hole",
        "use": 0.993758237365122,
        "plate_mm": 20.0,
        "cheeks": true
      },
      {
        "angle": 60,
        "load_t": 1,
        "mass_kg": 0.04861084009328367,
        "sling_t": 0.5773502691896258,
        "shackle_t": 0.75,
        "governing": "Base weld strength",
        "use": 0.8439518839052557,
        "plate_mm": 10.0,
        "cheeks": false
      },
      {
        "angle": 60,
        "load_t": 2,
        "mass_kg": 0.08648610671755647,
        "sling_t": 1.1547005383792517,
        "shackle_t": 1.5,
        "governing": "Base weld strength",
        "use": 0.936185236770914,
        "plate_mm": 12.0,
        "cheeks": false
      },
      {
        "angle": 60,
        "load_t": 5,
        "mass_kg": 0.30500722463627267,
        "sling_t": 2.8867513459481287,
        "shackle_t": 3.25,
        "governing": "Base weld strength",
        "use": 0.9796597125107048,
        "plate_mm": 6.0,
        "cheeks": true
      },
      {
        "angle": 60,
        "load_t": 10,
        "mass_kg": 0.629242756929721,
        "sling_t": 5.773502691896257,
        "shackle_t": 6.5,
        "governing": "Pulling and bending at the base",
        "use": 0.9885043470922313,
        "plate_mm": 8.0,
        "cheeks": true
      },
      {
        "angle": 60,
        "load_t": 20,
        "mass_kg": 1.83670240600381,
        "sling_t": 11.547005383792515,
        "shackle_t": 12.0,
        "governing": "Base weld strength",
        "use": 0.9771369381125834,
        "plate_mm": 12.0,
        "cheeks": true
      },
      {
        "angle": 60,
        "load_t": 30,
        "mass_kg": 3.973464222717597,
        "sling_t": 17.320508075688778,
        "shackle_t": 25.0,
        "governing": "Splitting above the hole",
        "use": 0.9557757931759943,
        "plate_mm": 20.0,
        "cheeks": true
      },
      {
        "angle": 60,
        "load_t": 40,
        "mass_kg": 5.255519433982303,
        "sling_t": 23.09401076758503,
        "shackle_t": 25.0,
        "governing": "Splitting above the hole",
        "use": 0.9956017494225348,
        "plate_mm": 20.0,
        "cheeks": true
      },
      {
        "angle": 90,
        "load_t": 1,
        "mass_kg": 0.025965437554701817,
        "sling_t": 0.5,
        "shackle_t": 0.5,
        "governing": "Shackle is rated for the load",
        "use": 1.0,
        "plate_mm": 8.0,
        "cheeks": false
      },
      {
        "angle": 90,
        "load_t": 2,
        "mass_kg": 0.06283527852874252,
        "sling_t": 1.0,
        "shackle_t": 1.0,
        "governing": "Shackle is rated for the load",
        "use": 1.0,
        "plate_mm": 12.0,
        "cheeks": false
      },
      {
        "angle": 90,
        "load_t": 5,
        "mass_kg": 0.21650602284738832,
        "sling_t": 2.5,
        "shackle_t": 3.25,
        "governing": "Splitting above the hole",
        "use": 0.9814191678711714,
        "plate_mm": 20.0,
        "cheeks": false
      },
      {
        "angle": 90,
        "load_t": 10,
        "mass_kg": 0.43779771821835956,
        "sling_t": 5.0,
        "shackle_t": 6.5,
        "governing": "Pulling and bending at the base",
        "use": 0.9964503521126762,
        "plate_mm": 12.0,
        "cheeks": true
      },
      {
        "angle": 90,
        "load_t": 20,
        "mass_kg": 1.1067167666659996,
        "sling_t": 10.0,
        "shackle_t": 12.0,
        "governing": "Pulling and bending at the base",
        "use": 0.987060641304348,
        "plate_mm": 20.0,
        "cheeks": true
      },
      {
        "angle": 90,
        "load_t": 30,
        "mass_kg": 1.9921590909209563,
        "sling_t": 15.0,
        "shackle_t": 17.0,
        "governing": "Splitting above the hole",
        "use": 0.9884434438209033,
        "plate_mm": 25.0,
        "cheeks": true
      },
      {
        "angle": 90,
        "load_t": 40,
        "mass_kg": 3.3356423324735696,
        "sling_t": 20.0,
        "shackle_t": 25.0,
        "governing": "Splitting above the hole",
        "use": 0.9887301455432805,
        "plate_mm": 30.0,
        "cheeks": true
      }
    ],
    "bracket": [
      {
        "nps": "2",
        "od_mm": 60.3,
        "down_kn": 0.5630001068191381,
        "mass_kg": 0.6119290366295602,
        "governing": "Welds to the bulkhead",
        "use": 0.09051597412226031,
        "natural_hz": 14.949445584417841,
        "recommended_m": 1.7,
        "spans_m": {
          "stress": 9.030537372411047,
          "sag": 3.4619357044481043,
          "frequency": 1.7291295836008267
        }
      },
      {
        "nps": "3",
        "od_mm": 88.9,
        "down_kn": 1.190095609127762,
        "mass_kg": 0.8262340366295603,
        "governing": "Welds to the bulkhead",
        "use": 0.1681561514954659,
        "natural_hz": 21.913281603081394,
        "recommended_m": 2.0,
        "spans_m": {
          "stress": 10.901937877295463,
          "sag": 4.191410185036489,
          "frequency": 2.093479476999065
        }
      },
      {
        "nps": "4",
        "od_mm": 114.3,
        "down_kn": 1.8015166427914544,
        "mass_kg": 0.9957940366295602,
        "governing": "Welds to the bulkhead",
        "use": 0.2539839513591594,
        "natural_hz": 27.5688048323118,
        "recommended_m": 2.3,
        "spans_m": {
          "stress": 12.0960058263021,
          "sag": 4.701272489127292,
          "frequency": 2.348139894993984
        }
      },
      {
        "nps": "6",
        "od_mm": 168.3,
        "down_kn": 3.4844687327665933,
        "mass_kg": 1.4573740366295602,
        "governing": "Welds to the bulkhead",
        "use": 0.43770653555825845,
        "natural_hz": 39.1058776047935,
        "recommended_m": 2.7,
        "spans_m": {
          "stress": 14.139926185301398,
          "sag": 5.599219239894011,
          "frequency": 2.796636465642022
        }
      },
      {
        "nps": "8",
        "od_mm": 219.1,
        "down_kn": 5.563224738825523,
        "mass_kg": 2.2026815197345795,
        "governing": "Seat plate between the knees",
        "use": 0.5490889665389258,
        "natural_hz": 49.67783423278696,
        "recommended_m": 3.1,
        "spans_m": {
          "stress": 15.74304108462145,
          "sag": 6.310848891863907,
          "frequency": 3.15207342023586
        }
      },
      {
        "nps": "10",
        "od_mm": 273.0,
        "down_kn": 8.268306550167884,
        "mass_kg": 2.773769019734579,
        "governing": "Seat plate between the knees",
        "use": 0.8160799018191706,
        "natural_hz": 60.64364566700957,
        "recommended_m": 3.4,
        "spans_m": {
          "stress": 17.21674874879629,
          "sag": 6.97266989890768,
          "frequency": 3.482632500480336
        }
      },
      {
        "nps": "12",
        "od_mm": 323.8,
        "down_kn": 10.931100928825911,
        "mass_kg": 4.238355331487805,
        "governing": "Seat plate between the knees",
        "use": 0.6068796060884066,
        "natural_hz": 69.55282487923314,
        "recommended_m": 3.7,
        "spans_m": {
          "stress": 18.131073352974635,
          "sag": 7.467304155925497,
          "frequency": 3.729686980947145
        }
      }
    ],
    "fin": [
      {
        "speed_kn": 10,
        "nemo_lift_kn": 24.84189204203293,
        "ur_s10_kn": 20.599040000000002,
        "design_kn": 24.84189204203293,
        "torque_knm": 2.9810270450439518,
        "cp_min": -2.910313075744681,
        "sigma": 9.568397061806962,
        "mass_kg": 370.22731676671526,
        "stock_mm": 110.0,
        "governing": "Stock bending and twisting at the outer bearing"
      },
      {
        "speed_kn": 12,
        "nemo_lift_kn": 35.77232454052741,
        "ur_s10_kn": 29.662617600000004,
        "design_kn": 35.77232454052741,
        "torque_knm": 4.292678944863289,
        "cp_min": -2.910313075744681,
        "sigma": 6.644720181810393,
        "mass_kg": 382.9896442228421,
        "stock_mm": 120.0,
        "governing": "Stock bending and twisting at the outer bearing"
      },
      {
        "speed_kn": 14,
        "nemo_lift_kn": 48.69010840238454,
        "ur_s10_kn": 40.37411840000001,
        "design_kn": 48.69010840238454,
        "torque_knm": 5.842813008286145,
        "cp_min": -2.910313075744681,
        "sigma": 4.881835235615798,
        "mass_kg": 416.5286176981835,
        "stock_mm": 135.0,
        "governing": "Stock bending and twisting at the outer bearing"
      },
      {
        "speed_kn": 16,
        "nemo_lift_kn": 63.59524362760428,
        "ur_s10_kn": 52.733542400000005,
        "design_kn": 63.59524362760428,
        "torque_knm": 7.631429235312514,
        "cp_min": -2.910313075744681,
        "sigma": 3.737655102268345,
        "mass_kg": 440.2499002525062,
        "stock_mm": 150.0,
        "governing": "Stock bending and twisting at the outer bearing"
      },
      {
        "speed_kn": 18,
        "nemo_lift_kn": 80.48773021618668,
        "ur_s10_kn": 66.7408896,
        "design_kn": 80.48773021618668,
        "torque_knm": 9.658527625942401,
        "cp_min": -2.910313075744681,
        "sigma": 2.953208969693507,
        "mass_kg": 457.45129812815543,
        "stock_mm": 160.0,
        "governing": "Stock bending and twisting at the outer bearing"
      },
      {
        "speed_kn": 20,
        "nemo_lift_kn": 99.36756816813173,
        "ur_s10_kn": 82.39616000000001,
        "design_kn": 99.36756816813173,
        "torque_knm": 11.924108180175807,
        "cp_min": -2.910313075744681,
        "sigma": 2.3920992654517406,
        "mass_kg": 475.7624636086852,
        "stock_mm": 170.0,
        "governing": "Stock bending and twisting at the outer bearing"
      },
      {
        "speed_kn": 22,
        "nemo_lift_kn": 120.2347574834394,
        "ur_s10_kn": 99.69935360000002,
        "design_kn": 120.2347574834394,
        "torque_knm": 14.428170898012725,
        "cp_min": -2.910313075744681,
        "sigma": 1.9769415416956535,
        "mass_kg": 507.4980647260956,
        "stock_mm": 180.0,
        "governing": "Stock bending and twisting at the outer bearing"
      },
      {
        "speed_kn": 24,
        "nemo_lift_kn": 143.08929816210963,
        "ur_s10_kn": 118.65047040000002,
        "design_kn": 143.08929816210963,
        "torque_knm": 17.170715779453158,
        "cp_min": -2.910313075744681,
        "sigma": 1.6611800454525982,
        "mass_kg": 538.7102786133623,
        "stock_mm": 195.0,
        "governing": "Stock bending and twisting at the outer bearing"
      }
    ],
    "bracket_span": [
      {
        "span_m": 1.5,
        "natural_hz": 110.2752193292472,
        "separation": 1.9406725154465918,
        "nearest": "Engine firing",
        "pipe_stress_mpa": 2.21000529380116
      },
      {
        "span_m": 2.0,
        "natural_hz": 62.02981087270154,
        "separation": 0.6541282899387078,
        "nearest": "Engine firing",
        "pipe_stress_mpa": 3.928898300090951
      },
      {
        "span_m": 2.5,
        "natural_hz": 39.699078958528986,
        "separation": 0.05864210556077296,
        "nearest": "Engine firing",
        "pipe_stress_mpa": 6.1389035938921115
      },
      {
        "span_m": 3.0,
        "natural_hz": 27.5688048323118,
        "separation": 0.26483187113835205,
        "nearest": "Engine firing",
        "pipe_stress_mpa": 8.84002117520464
      },
      {
        "span_m": 3.5,
        "natural_hz": 20.25463212169846,
        "separation": 0.26591450760615376,
        "nearest": "Blade rate, second harmonic",
        "pipe_stress_mpa": 12.03225104402854
      },
      {
        "span_m": 4.0,
        "natural_hz": 15.507452718175385,
        "separation": 0.030784205114038454,
        "nearest": "Blade rate, second harmonic",
        "pipe_stress_mpa": 15.715593200363804
      },
      {
        "span_m": 5.0,
        "natural_hz": 9.924769739632247,
        "separation": 0.2060184208294203,
        "nearest": "Engine rotation",
        "pipe_stress_mpa": 24.555614375568446
      },
      {
        "span_m": 6.0,
        "natural_hz": 6.89220120807795,
        "separation": 0.1384748489902563,
        "nearest": "Propeller blade rate",
        "pipe_stress_mpa": 35.36008470081856
      }
    ]
  },
  "advanced": {
    "padeye": [
      {
        "beta_deg": 0.0,
        "side_angle_deg": 0.0,
        "horizontal_n": 14154.680043371112,
        "side_n": 1415.4680043371109,
        "shackle": "3.25 t (5/8 in) Crosby G-2130",
        "shackle_wll_t": 3.25,
        "side_factor": 1.0,
        "rated_t": 3.25,
        "shackle_use": 0.8882311833686549,
        "main_plate_mm": 6,
        "cheek_mm": 6,
        "mass_kg": 0.30500722463627267,
        "governing": "Base weld strength",
        "governing_use": 0.9796597125107048
      },
      {
        "beta_deg": 20.0,
        "side_angle_deg": 9.846551939834079,
        "horizontal_n": 13301.048386341397,
        "side_n": 4841.18569716277,
        "shackle": "3.25 t (5/8 in) Crosby G-2130",
        "shackle_wll_t": 3.25,
        "side_factor": 1.0,
        "rated_t": 3.25,
        "shackle_use": 0.8882311833686549,
        "main_plate_mm": 20,
        "cheek_mm": 0.0,
        "mass_kg": 0.3126346190056362,
        "governing": "Splitting above the hole",
        "governing_use": 0.979325862002565
      },
      {
        "beta_deg": 45.0,
        "side_angle_deg": 20.704811054635435,
        "horizontal_n": 10008.87024419361,
        "side_n": 10008.870244193608,
        "shackle": "4.75 t (3/4 in) Crosby G-2130",
        "shackle_wll_t": 4.75,
        "side_factor": 0.75,
        "rated_t": 3.5625,
        "shackle_use": 0.8103161672836853,
        "main_plate_mm": 20,
        "cheek_mm": 0.0,
        "mass_kg": 0.4305032180831073,
        "governing": "Pulling and bending at the base",
        "governing_use": 0.9358722895105424
      },
      {
        "beta_deg": 90.0,
        "side_angle_deg": 30.000000000000004,
        "horizontal_n": 8.667241804034675e-13,
        "side_n": 14154.680043371112,
        "shackle": "4.75 t (3/4 in) Crosby G-2130",
        "shackle_wll_t": 4.75,
        "side_factor": 0.75,
        "rated_t": 3.5625,
        "shackle_use": 0.8103161672836853,
        "main_plate_mm": 25,
        "cheek_mm": 0.0,
        "mass_kg": 0.4199940648715086,
        "governing": "Pulling and bending at the base",
        "governing_use": 0.9284620431603251
      }
    ],
    "bracket": [
      {
        "nps": "2",
        "span_hz": 14.949445584417841,
        "bracket_hz": 340.430881546006,
        "combined_hz": 14.935052303325145,
        "separation": 0.06655923104217842,
        "use": 3.004842406806961,
        "passed": false,
        "category": "span",
        "mass_kg": 0.6119290366295602,
        "rigid_separation": 0.06565965097388493
      },
      {
        "nps": "3",
        "span_hz": 21.913281603081394,
        "bracket_hz": 234.9669927345262,
        "combined_hz": 21.81860192398572,
        "separation": 0.36366262024910756,
        "use": 0.5499602897405313,
        "passed": true,
        "category": "stiffness",
        "mass_kg": 0.8262340366295603,
        "rigid_separation": 0.36958010019258714
      },
      {
        "nps": "4",
        "span_hz": 27.5688048323118,
        "bracket_hz": 178.2235930938585,
        "combined_hz": 27.244775896818876,
        "separation": 0.27347264275149663,
        "use": 0.7313345788000415,
        "passed": true,
        "category": "stiffness",
        "mass_kg": 0.9957940366295602,
        "rigid_separation": 0.26483187113835205
      },
      {
        "nps": "6",
        "span_hz": 39.1058776047935,
        "bracket_hz": 122.31804598730427,
        "combined_hz": 37.24855394765356,
        "separation": 0.006705228062571678,
        "use": 29.827471658479784,
        "passed": false,
        "category": "span",
        "mass_kg": 1.4573740366295602,
        "rigid_separation": 0.04282340279449329
      },
      {
        "nps": "8",
        "span_hz": 49.67783423278696,
        "bracket_hz": 108.31597176861861,
        "combined_hz": 45.1551572146778,
        "separation": 0.20413752572474134,
        "use": 0.9797316749575952,
        "passed": true,
        "category": "stiffness",
        "mass_kg": 2.2026815197345795,
        "rigid_separation": 0.3247422462076522
      },
      {
        "nps": "10",
        "span_hz": 60.64364566700957,
        "bracket_hz": 80.90194014165402,
        "combined_hz": 48.524360746375,
        "separation": 0.29398295323666673,
        "use": 0.680311554796148,
        "passed": true,
        "category": "stiffness",
        "mass_kg": 2.773769019734579,
        "rigid_separation": 0.6171638844535886
      },
      {
        "nps": "12",
        "span_hz": 69.55282487923314,
        "bracket_hz": 78.46101074009437,
        "combined_hz": 52.04706263679802,
        "separation": 0.3879216703146138,
        "use": 0.5155680007198237,
        "passed": true,
        "category": "stiffness",
        "mass_kg": 4.238355331487805,
        "rigid_separation": 0.8547419967795504
      }
    ],
    "fin": {
      "default": {
        "astern_speed_kn": 9.0,
        "astern_force_n": 12134.7072,
        "astern_torque_nm": 4514.111078400001,
        "astern_moment_nm": 10921.23648,
        "ahead_torque_nm": 9658.5276259424,
        "stock_mm": 160.0,
        "mass_kg": 457.45129812815543,
        "torsion_condition": "ahead",
        "torsion_use": 0.10864350124726274,
        "combined_condition": "ahead",
        "combined_use": 0.9453618709860613
      },
      "stock_forward": {
        "astern_speed_kn": 12.0,
        "astern_force_n": 21572.812800000003,
        "astern_torque_nm": 11908.192665600003,
        "astern_moment_nm": 19415.53152,
        "ahead_torque_nm": 5580.482628322276,
        "stock_mm": 125.0,
        "mass_kg": 387.4576583822179,
        "torsion_condition": "astern",
        "torsion_use": 0.2809108981624523,
        "combined_condition": "ahead",
        "combined_use": 0.8851320073904785
      },
      "bearings_800": {
        "astern_speed_kn": 9.0,
        "astern_force_n": 12134.7072,
        "astern_torque_nm": 4514.111078400001,
        "astern_moment_nm": 10921.23648,
        "ahead_torque_nm": 9658.5276259424,
        "stock_mm": 160.0,
        "mass_kg": 457.45129812815543,
        "torsion_condition": "ahead",
        "torsion_use": 0.10864350124726274,
        "combined_condition": "ahead",
        "combined_use": 0.9453618709860613,
        "outer": {
          "reaction_n": 171036.42670939668,
          "diameter_mm": 176.0,
          "length_mm": 176.69052346012054,
          "longest_mm": 211.2,
          "use": 0.8366028572922375,
          "clearance_mm": 1.5
        },
        "inner": {
          "reaction_n": 90548.69649321001,
          "diameter_mm": 176.0,
          "length_mm": 93.54204183182853,
          "longest_mm": 211.2,
          "use": 0.4429073950370669,
          "clearance_mm": 1.5
        }
      },
      "bearings_400": {
        "astern_speed_kn": 9.0,
        "astern_force_n": 12134.7072,
        "astern_torque_nm": 4514.111078400001,
        "astern_moment_nm": 10921.23648,
        "ahead_torque_nm": 9658.5276259424,
        "stock_mm": 185.0,
        "mass_kg": 505.31002608863105,
        "torsion_condition": "ahead",
        "torsion_use": 0.07028271274890541,
        "combined_condition": "ahead",
        "combined_use": 0.61156531278446,
        "outer": {
          "reaction_n": 261585.1232026067,
          "diameter_mm": 201.0,
          "length_mm": 236.6215497083733,
          "longest_mm": 241.2,
          "use": 0.9810180336168047,
          "clearance_mm": 1.5
        },
        "inner": {
          "reaction_n": 181097.39298642002,
          "diameter_mm": 201.0,
          "length_mm": 163.81491902887382,
          "longest_mm": 241.2,
          "use": 0.6791663309654802,
          "clearance_mm": 1.5
        }
      }
    }
  }
};
