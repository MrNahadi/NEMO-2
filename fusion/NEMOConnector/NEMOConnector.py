"""NEMO Connector for Autodesk Fusion.

Runs inside Fusion. It talks to NEMO on this computer (127.0.0.1) and:

* builds NEMO designs as parametric Fusion models when NEMO asks;
* adds "Check in NEMO" to Fusion, which sends edited dimensions back to NEMO
  to be checked against the design rules;
* shows NEMO's Static Stress cross-check sheet in a panel.

Uses only Python's standard library, which Fusion's own Python includes.
Fusion work is always done on Fusion's main thread through a custom event.
"""

import json
import math
import os
import threading
import time
import traceback
import urllib.error
import urllib.request
import uuid

import adsk.core
import adsk.fusion

VERSION = "1.1.0"
HERE = os.path.dirname(os.path.abspath(__file__))
EVENT_ID = "nemo_connector_job"
PANEL_ID = "NEMOConnectorPanel"
PALETTE_ID = "NEMOConnectorSheet"
CMD_CHECK = "NEMOConnectorCheck"
CMD_SHEET = "NEMOConnectorSheetCmd"
ATTR_GROUP = "nemo"
POLL_SECONDS = 1.5

APP = None
UI = None
HANDLERS = []
STOP = threading.Event()
SESSION = uuid.uuid4().hex


# ------------------------------------------------------------------ helpers
def _log(message):
    try:
        with open(os.path.join(HERE, "NEMOConnector.log"), "a", encoding="utf-8") as handle:
            handle.write(time.strftime("%Y-%m-%d %H:%M:%S ") + message + "\n")
    except OSError:
        pass


def _server():
    try:
        with open(os.path.join(HERE, "config.json"), encoding="utf-8") as handle:
            return json.load(handle).get("server", "http://127.0.0.1:8765").rstrip("/")
    except (OSError, ValueError):
        return "http://127.0.0.1:8765"


def _call(method, path, body=None, timeout=6):
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(_server() + path, data=data, method=method,
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _cm(mm):
    return mm / 10.0


# ------------------------------------------------------------------ start / stop
def run(context):
    global APP, UI
    try:
        APP = adsk.core.Application.get()
        UI = APP.userInterface
        STOP.clear()

        event = APP.registerCustomEvent(EVENT_ID)
        handler = _JobHandler()
        event.add(handler)
        HANDLERS.append(handler)

        _add_commands()
        threading.Thread(target=_poll_loop, daemon=True).start()
        _log("NEMO Connector %s started in Fusion %s" % (VERSION, APP.version))
    except Exception:
        _log(traceback.format_exc())
        if UI:
            UI.messageBox("NEMO Connector could not start:\n" + traceback.format_exc())


def stop(context):
    STOP.set()
    try:
        APP.unregisterCustomEvent(EVENT_ID)
    except Exception:
        pass
    try:
        _remove_commands()
    except Exception:
        _log(traceback.format_exc())
    _log("NEMO Connector stopped")


# ------------------------------------------------------------------ polling
def _poll_loop():
    connected = False
    while not STOP.is_set():
        try:
            if not connected:
                _call("POST", "/api/fusion/hello",
                      {"session": SESSION, "connector_version": VERSION, "fusion_version": APP.version})
                connected = True
                _log("Connected to NEMO at " + _server())
            reply = _call("GET", "/api/fusion/poll?session=" + SESSION)
            job = reply.get("job")
            if job and job.get("kind") == "hello_again":
                connected = False
            elif job:
                APP.fireCustomEvent(EVENT_ID, json.dumps(job))
            STOP.wait(POLL_SECONDS)
        except (urllib.error.URLError, OSError, ValueError):
            if connected:
                _log("Lost NEMO; will keep trying")
            connected = False
            STOP.wait(5.0)  # NEMO is not running. Try again quietly.
        except Exception:
            _log(traceback.format_exc())
            STOP.wait(5.0)


class _JobHandler(adsk.core.CustomEventHandler):
    def notify(self, args):
        job = json.loads(args.additionalInfo)
        try:
            if job["kind"] == "open_design":
                result = _build_padeye(job["payload"])
                _call("POST", "/api/fusion/jobs/%s/result" % job["id"], {"ok": True, "result": result})
                _show_sheet(job["payload"]["sheet_url"])
            else:
                raise ValueError("Unknown request: %s" % job["kind"])
        except Exception as exc:
            _log(traceback.format_exc())
            try:
                _call("POST", "/api/fusion/jobs/%s/result" % job["id"], {"ok": False, "error": "Fusion: %s" % exc})
            except Exception:
                pass
            UI.messageBox("NEMO could not build the model in Fusion:\n%s" % exc, "NEMO Connector")


# ------------------------------------------------------------------ building the padeye
def _tangent_angle(px, py, cy, radius, side):
    dx, dy = px, py - cy
    distance = math.hypot(dx, dy)
    return math.atan2(dy, dx) + side * math.acos(radius / distance)


def _build_padeye(payload):
    values = {p["name"]: p["value_mm"] for p in payload["parameters"]}
    doc = APP.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(APP.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    try:
        design.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
    except Exception:
        pass

    for p in payload["parameters"]:
        design.userParameters.add(p["name"], adsk.core.ValueInput.createByString("%r mm" % p["value_mm"]), "mm", p["label"])

    root = design.rootComponent
    warnings = []

    def attempt(label, action):
        try:
            return action()
        except Exception as exc:
            warnings.append("%s: %s" % (label, exc))
            return None

    t, R, Dh, L, h = (values[k] for k in ("nemo_t", "nemo_R", "nemo_Dh", "nemo_L", "nemo_h"))
    tc, Rc = values.get("nemo_tc", 0.0), values.get("nemo_Rc", 0.0)
    P = adsk.core.Point3D.create
    a_right = _tangent_angle(L / 2, 0.0, h, R, +1)
    a_left = _tangent_angle(-L / 2, 0.0, h, R, -1)
    sweep = (a_left - a_right) % (2 * math.pi)

    # Outline sketch: base line, two flanks, the head arc and the hole.
    sketch = root.sketches.add(root.xYConstructionPlane)
    sketch.name = "NEMO padeye outline"
    lines = sketch.sketchCurves.sketchLines
    base = lines.addByTwoPoints(P(_cm(-L / 2), 0, 0), P(_cm(L / 2), 0, 0))
    right = lines.addByTwoPoints(base.endSketchPoint, P(_cm(R * math.cos(a_right)), _cm(h + R * math.sin(a_right)), 0))
    arc = sketch.sketchCurves.sketchArcs.addByCenterStartSweep(P(0, _cm(h), 0), right.endSketchPoint, sweep)
    left = lines.addByTwoPoints(arc.endSketchPoint, base.startSketchPoint)
    hole = sketch.sketchCurves.sketchCircles.addByCenterRadius(arc.centerSketchPoint, _cm(Dh / 2))

    gc, dims = sketch.geometricConstraints, sketch.sketchDimensions
    attempt("base horizontal", lambda: gc.addHorizontal(base))
    attempt("base centred", lambda: gc.addMidPoint(sketch.originPoint, base))
    attempt("right flank tangent", lambda: gc.addTangent(right, arc))
    attempt("left flank tangent", lambda: gc.addTangent(left, arc))
    attempt("hole on centre line", lambda: gc.addVerticalPoints(sketch.originPoint, arc.centerSketchPoint))
    H, V = adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, adsk.fusion.DimensionOrientations.VerticalDimensionOrientation

    def bind(dimension, expression):
        dimension.parameter.expression = expression

    attempt("base length", lambda: bind(dims.addDistanceDimension(base.startSketchPoint, base.endSketchPoint, H,
                                                                     P(0, _cm(-12), 0)), "nemo_L"))
    attempt("hole height", lambda: bind(dims.addDistanceDimension(sketch.originPoint, arc.centerSketchPoint, V,
                                                                     P(_cm(-L / 2 - 15), _cm(h / 2), 0)), "nemo_h"))
    attempt("head radius", lambda: bind(dims.addRadialDimension(arc, P(_cm(-R * 0.7), _cm(h + R * 1.2), 0)), "nemo_R"))
    attempt("hole diameter", lambda: bind(dims.addDiameterDimension(hole, P(_cm(Dh), _cm(h + Dh), 0)), "nemo_Dh"))

    profile = _profile_with_hole(sketch)
    extrudes = root.features.extrudeFeatures
    plate_input = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    plate_input.setSymmetricExtent(adsk.core.ValueInput.createByString("nemo_t"), True)
    plate = extrudes.add(plate_input)
    plate.name = "NEMO main plate"
    body = plate.bodies.item(0)
    body.name = "Padeye"

    if tc > 0.05 and Rc > Dh / 2:
        ring = root.sketches.add(root.xYConstructionPlane)
        ring.name = "NEMO cheek plates"
        centre = ring.project(arc.centerSketchPoint).item(0)
        outer = ring.sketchCurves.sketchCircles.addByCenterRadius(centre, _cm(Rc))
        inner = ring.sketchCurves.sketchCircles.addByCenterRadius(centre, _cm(Dh / 2))
        attempt("cheek radius", lambda: bind(ring.sketchDimensions.addRadialDimension(outer, P(_cm(Rc), _cm(h + Rc), 0)), "nemo_Rc"))
        attempt("cheek hole", lambda: bind(ring.sketchDimensions.addDiameterDimension(inner, P(_cm(-Dh), _cm(h - Dh), 0)), "nemo_Dh"))
        cheek_input = extrudes.createInput(_profile_with_hole(ring), adsk.fusion.FeatureOperations.JoinFeatureOperation)
        cheek_input.setSymmetricExtent(adsk.core.ValueInput.createByString("nemo_t + 2 * nemo_tc"), True)
        cheek_input.participantBodies = [body]
        extrudes.add(cheek_input).name = "NEMO cheek plates"

    material_warnings = []
    material_info = attempt("material", lambda: _assign_material(design, body, payload["material"], material_warnings)) or {}
    if material_warnings:
        _log("Material: " + "; ".join(material_warnings))
    _tag_faces(body, Dh)
    design.attributes.add(ATTR_GROUP, "link", json.dumps({
        "project_id": payload["project_id"], "run": payload["run"], "design_key": payload["design_key"],
        "project_name": payload["project_name"], "design_label": payload["design_label"], "sheet_url": payload["sheet_url"],
    }))
    try:
        APP.activeViewport.fit()
    except Exception:
        pass

    props = body.physicalProperties
    volume_mm3 = props.volume * 1000.0  # cm^3 to mm^3
    if warnings:
        _log("Built with warnings: " + "; ".join(warnings))
    return {
        "volume_mm3": volume_mm3,
        "fusion_mass_kg": props.mass,
        "mass_at_nemo_density_kg": volume_mm3 * 1e-9 * payload["material"]["density_kg_m3"],
        "fusion_material": material_info.get("fusion_material"),
        **{k: v for k, v in material_info.items() if k != "fusion_material"},
        "material_warnings": material_warnings,
        "parametric": not warnings,
        "warnings": warnings,
        "fusion_version": APP.version,
        "faces": body.faces.count,
    }


def _profile_with_hole(sketch):
    best = None
    for i in range(sketch.profiles.count):
        profile = sketch.profiles.item(i)
        if profile.profileLoops.count == 2:
            if best is None or profile.areaProperties().area > best.areaProperties().area:
                best = profile
    if best is None:
        raise RuntimeError("the outline did not close into a plate with a hole")
    return best


def _library_material(material):
    family = material["id"].upper()
    wanted = ["Aluminum 5083", "Aluminum"] if family.startswith("AL") else (["Stainless Steel", "Steel"] if "316" in family else ["Steel"])
    libraries = APP.materialLibraries
    for name in wanted:
        for li in range(libraries.count):
            found = libraries.item(li).materials.itemByName(name)
            if found:
                return found
    return None


# (NEMO value, its unit and its size in SI units, words that identify the Fusion property, words it must not contain)
_PROPERTIES = (
    ("yield_strength_mpa", "MPa", 1e6, "kg / (m s^2)", ("yield",), ()),
    ("tensile_strength_mpa", "MPa", 1e6, "kg / (m s^2)", ("tensile",), ("yield",)),
    ("elastic_modulus_gpa", "GPa", 1e9, "kg / (m s^2)", ("young",), ()),
    ("poisson_ratio", "", 1.0, "", ("poisson",), ()),
    ("density_kg_m3", "kg / m^3", 1.0, "kg / m^3", ("density",), ()),
)
_READBACK = {"yield_strength_mpa": "fusion_yield_mpa", "tensile_strength_mpa": "fusion_tensile_mpa",
             "elastic_modulus_gpa": "fusion_modulus_gpa", "poisson_ratio": "fusion_poisson_ratio",
             "density_kg_m3": "fusion_density_kg_m3"}


def _find_property(properties, words, avoid):
    for i in range(properties.count):
        prop = properties.item(i)
        text = ("%s %s" % (getattr(prop, "name", ""), getattr(prop, "id", ""))).lower()
        if all(w in text for w in words) and not any(a in text for a in avoid) and hasattr(prop, "value"):
            return prop
    return None


def _to_fusion(units_manager, value, nemo_units, prop_units, si_scale, si_units):
    """A NEMO value in the Fusion property's own units. Tries the plain unit name, then SI base units."""
    if not prop_units or not nemo_units:
        return value
    try:
        return units_manager.convert(value, nemo_units, prop_units)
    except Exception:
        return units_manager.convert(value * si_scale, si_units, prop_units)


def _from_fusion(units_manager, value, nemo_units, prop_units, si_scale, si_units):
    """A Fusion property value back in NEMO's units, for the read-back check."""
    if not prop_units or not nemo_units:
        return value
    try:
        return units_manager.convert(value, prop_units, nemo_units)
    except Exception:
        return units_manager.convert(value, prop_units, si_units) / si_scale


def _assign_material(design, body, material, warnings):
    """Give the body a copy of a library material carrying NEMO's own values.

    Fusion's library has no EN or IACS grades (no S355, no AH36), and its
    generic "Steel" has a 207 MPa yield, so Fusion's safety factor would be
    wrong. The copy lives only in this design. Every value is read back after
    it is set, and NEMO compares the read-back values with its own.
    """
    info = {"fusion_material": None}
    base = _library_material(material)
    if base is None:
        warnings.append("no suitable Fusion library material was found to copy")
        return info
    name = material.get("fusion_name") or material["name"]
    try:
        copy = design.materials.itemByName(name) or design.materials.addByCopy(base, name)
    except Exception as exc:
        body.material = base
        info["fusion_material"] = base.name
        warnings.append("could not copy %s into the design (%s); set the material by hand" % (base.name, exc))
        return info

    units = design.unitsManager
    for key, nemo_units, si_scale, si_units, words, avoid in _PROPERTIES:
        if key not in material:
            continue
        prop = _find_property(copy.materialProperties, words, avoid)
        if prop is None:
            warnings.append("Fusion material has no %s property" % key.split("_")[0])
            continue
        prop_units = getattr(prop, "units", "") or ""
        try:
            if getattr(prop, "isReadOnly", False):
                raise ValueError("it is read-only")
            prop.value = _to_fusion(units, float(material[key]), nemo_units, prop_units, si_scale, si_units)
        except Exception as exc:
            warnings.append("could not set %s (%s)" % (prop.name, exc))
        try:
            info[_READBACK[key]] = _from_fusion(units, float(prop.value), nemo_units, prop_units, si_scale, si_units)
        except Exception as exc:
            warnings.append("could not read back %s (%s)" % (prop.name, exc))
    body.material = copy
    info["fusion_material"] = copy.name
    return info


def _tag_faces(body, hole_diameter_mm):
    radius_cm = _cm(hole_diameter_mm / 2)
    for i in range(body.faces.count):
        face = body.faces.item(i)
        geometry = face.geometry
        role = None
        if isinstance(geometry, adsk.core.Plane):
            normal = geometry.normal
            if abs(normal.y + 1) < 1e-6 and abs(face.centroid.y) < 1e-6:
                role = "fixed_support"
        elif isinstance(geometry, adsk.core.Cylinder) and abs(geometry.radius - radius_cm) < 1e-4:
            role = "pin_bearing"
        if role:
            face.attributes.add(ATTR_GROUP, "role", role)


# ------------------------------------------------------------------ commands in Fusion's toolbar
def _link():
    design = adsk.fusion.Design.cast(APP.activeProduct)
    if not design:
        return None, None
    attribute = design.attributes.itemByName(ATTR_GROUP, "link")
    return design, (json.loads(attribute.value) if attribute else None)


class _CheckCreated(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        handler = _CheckExecute()
        args.command.execute.add(handler)
        HANDLERS.append(handler)


class _CheckExecute(adsk.core.CommandEventHandler):
    def notify(self, args):
        design, link = _link()
        if not link:
            UI.messageBox("This design was not opened from NEMO. Use \"Open in Fusion\" in NEMO first.", "NEMO Connector")
            return
        values = {}
        for i in range(design.userParameters.count):
            param = design.userParameters.item(i)
            if param.name.startswith("nemo_"):
                values[param.name] = param.value * 10.0  # cm to mm
        try:
            result = _call("POST", "/api/fusion/check", {"project_id": link["project_id"], "run": link["run"],
                                                         "design": link["design_key"], "parameters": values}, timeout=20)
        except urllib.error.HTTPError as exc:
            UI.messageBox("NEMO could not check this design: %s" % exc.read().decode("utf-8", "replace"), "NEMO Connector")
            return
        except (urllib.error.URLError, OSError):
            UI.messageBox("NEMO is not running. Start NEMO, then try again.", "NEMO Connector")
            return
        if not result.get("ok"):
            UI.messageBox("These dimensions do not make a valid padeye:\n- " + "\n- ".join(result.get("problems", [])), "NEMO Connector")
            return
        failing = [c for c in result["checks"] if not c["passed"] and c["severity"] == "required"]
        advice = [c for c in result["checks"] if not c["passed"] and c["severity"] == "advice"]
        lines = [
            "Passes every required check." if result["passed"] else "Does NOT pass every required check.",
            "",
            "Highest use: %s, %.0f%%" % (result["governing"]["title"], result["governing"]["use"] * 100),
            "Plate mass: %.2f kg (NEMO design: %.2f kg)" % (result["mass_kg"], result["nemo_mass_kg"]),
        ]
        if result["changed"]:
            lines += ["", "Changed from the NEMO design:"]
            lines += ["  %s: %g to %g mm" % (k.replace("_mm", "").replace("_", " "), v["from"], v["to"]) for k, v in result["changed"].items()]
        if failing:
            lines += ["", "Failing:"] + ["  %s (%.0f%%)" % (c["title"], c["use"] * 100) for c in failing]
        if advice:
            lines += ["", "Advice:"] + ["  %s" % c["title"] for c in advice]
        lines += ["", "The result is also shown in NEMO."]
        UI.messageBox("\n".join(lines), "Checked in NEMO")


class _SheetCreated(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        handler = _SheetExecute()
        args.command.execute.add(handler)
        HANDLERS.append(handler)


class _SheetExecute(adsk.core.CommandEventHandler):
    def notify(self, args):
        _, link = _link()
        if not link:
            UI.messageBox("This design was not opened from NEMO. Use \"Open in Fusion\" in NEMO first.", "NEMO Connector")
            return
        _show_sheet(link["sheet_url"])


def _show_sheet(url):
    palette = UI.palettes.itemById(PALETTE_ID)
    if palette:
        palette.htmlFileURL = url
        palette.isVisible = True
        return
    palette = UI.palettes.add(PALETTE_ID, "NEMO cross-check", url, True, True, True, 380, 720)
    try:
        palette.dockingState = adsk.core.PaletteDockingStates.PaletteDockStateRight
    except Exception:
        pass


def _add_commands():
    definitions = UI.commandDefinitions
    for cmd_id, name, tip, created in (
        (CMD_CHECK, "Check in NEMO", "Send this padeye's dimensions to NEMO and check them against the design rules.", _CheckCreated()),
        (CMD_SHEET, "NEMO cross-check sheet", "Show the values for setting up the Static Stress cross-check study.", _SheetCreated()),
    ):
        existing = definitions.itemById(cmd_id)
        if existing:
            existing.deleteMe()
        definition = definitions.addButtonDefinition(cmd_id, name, tip, os.path.join(HERE, "resources", cmd_id))
        definition.commandCreated.add(created)
        HANDLERS.append(created)
    workspace = UI.workspaces.itemById("FusionSolidEnvironment")
    tab = workspace.toolbarTabs.itemById("SolidTab")
    panel = tab.toolbarPanels.itemById(PANEL_ID) or tab.toolbarPanels.add(PANEL_ID, "NEMO")
    for cmd_id in (CMD_CHECK, CMD_SHEET):
        if not panel.controls.itemById(cmd_id):
            control = panel.controls.addCommand(definitions.itemById(cmd_id))
            control.isPromoted = cmd_id == CMD_CHECK


def _remove_commands():
    workspace = UI.workspaces.itemById("FusionSolidEnvironment")
    panel = workspace.toolbarTabs.itemById("SolidTab").toolbarPanels.itemById(PANEL_ID)
    if panel:
        panel.deleteMe()
    for cmd_id in (CMD_CHECK, CMD_SHEET):
        definition = UI.commandDefinitions.itemById(cmd_id)
        if definition:
            definition.deleteMe()
    palette = UI.palettes.itemById(PALETTE_ID)
    if palette:
        palette.deleteMe()
