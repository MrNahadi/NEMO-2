# User guide

NEMO walks you through three steps: describe the job, check the assumptions,
and review the designs. Every question has a **?** button that explains it.

NEMO designs three parts. This guide follows a **lifting padeye**; the other two
have their own pages for their questions and checks:
[pipe support brackets](pipe-support-brackets.md) and
[stabilizer fins](stabilizer-fins.md). Saving, the run screen, the results page,
the report and the files work the same way for all three.

## Home

- **New design** starts a design in its own new folder. A new design is always
  empty and never picks up anything from an earlier one.
- **Saved designs** lists everything you have made, newest first. Opening a saved
  design shows its last results. Nothing is recalculated until you press
  **Find designs** or **Run again**.
- The moon/sun button in the top bar switches between light and dark screens.

Your designs are stored in `Documents\NEMO Projects`. Each design has its own
folder with its answers (`project.json`) and every result (`runs`).

The **⋯** button at the right of each saved design opens a menu:

| Option | What it does |
| --- | --- |
| Open | Opens the design, the same as clicking its name |
| Rename | Changes the design's name |
| Duplicate | Makes a new design with the same answers and no results, for trying a variation |
| Open calculation report | Opens the PDF report of the latest result (only when the design has been run) |
| Open in Fusion | Builds the lightest design of the latest result in Fusion. Needs the Fusion connector; see [Using NEMO with Fusion](using-nemo-with-fusion.md) |
| Show in folder | Opens the design's folder in File Explorer |
| Delete | Asks first, then moves the design and all its results to the Windows Recycle Bin, where you can restore it |

## Step 1: Describe the lift

| Question | What to enter |
| --- | --- |
| How heavy is the load? | Everything being lifted, including any frame or spreader. Choose kg or tonnes. |
| How many lifting points? | The number of padeyes the slings attach to. |
| Sling angle from horizontal | 90° is straight up. 60° is common. Flatter angles need bigger padeyes. |
| Material | The plate the padeye is cut from. |
| Plate thicknesses | Tick only the thicknesses your workshop has. NEMO designs with these only. |
| Allow cheek plates | Lets NEMO add rings either side of the hole on heavier lifts. |

Under **Advanced settings: sling direction and load sharing** (leave these
alone for a simple lift):

- **How many points carry the load?** With four points and no spreader beam, the
  load is rarely shared evenly. Riggers often assume only two carry it.
- **Sideways pull allowance**: an extra sideways force on each padeye. 5% is a
  common allowance.
- **Angle between the sling and the padeye plate, seen from above**: the second
  angle of an oblique sling. Leave it at 0° when each padeye is turned to face
  its sling, which is the usual and best arrangement. If a padeye is fixed and
  its sling leaves at an angle to the plate, enter that angle (90° means the
  sling pulls straight across the plate). NEMO then adds the real sideways pull
  to the base and weld checks, and lowers the shackle's rating for side loading
  using the maker's table. A shackle pulled 45° to the side keeps only 70% of
  its rating, so it often has to go up a size.

The 3D view on the right is a **provisional** design. It updates a moment after
you change an answer. Drag to turn it; scroll to zoom. The chips under it show
the plate mass, plate thickness, shackle size and the check closest to its limit.

If an answer is not possible, a red message under the question tells you why.
If no padeye can do the job with your answers, a red box under the 3D view
explains what to change.

## Step 2: Check the assumptions

| Setting | Default | Meaning |
| --- | --- | --- |
| Design rules | ASME BTH-1 | The published method NEMO checks against. |
| How predictable is this lift? | Uncertain or rough (B) | Category B uses a safety factor of 3.0; A uses 2.0. Use B at sea or on deck. |
| How often will it be used at full load? | Up to 20,000 lifts | More lifts lower the allowed pin bearing stress. |
| Extra dynamic factor | 1.0 | Leave at 1.0 unless your lift plan asks for one. |
| Keep the padeye at least 60% as thick as the shackle jaw | On | Stops the shackle tilting on a thin padeye. |

Press **Find designs**. It takes one to two minutes.

## Step 3: Watching NEMO work

While NEMO works, the screen lists each step it goes through, with its numbers as
they come in. Select any step to see its details on the right. By default the
right side follows the step NEMO is working on.

| Step | What you see |
| --- | --- |
| 1 Forces on each padeye | A diagram of the sling force and its parts, and the calculation from the load to the force on one padeye |
| 2 Shackle | The shackles that can carry the load and why the smallest was picked |
| 3 Design search | A chart that fills in with every design tried: plate mass across, highest check use up. Dots below the red line pass. The circle is the design chosen |
| 4 3D models | The volume of each 3D model next to the formula volume, to show they match |
| 5 Mesh | The padeye split into small elements, drawn in 3D, with the element counts |
| 6 Stress solve | The solver's error shrinking to almost zero, and the number of equations solved |
| 7 Checks on the result | Whether the stress changes as the mesh gets finer, and whether the support forces balance the load |

## Results

NEMO shows up to three designs:

- **Lightest**: least steel that passes every required check.
- **Balanced**: every check at 85% of its limit or less.
- **Extra margin**: every check at 70% of its limit or less.

If two targets give the same design, NEMO shows it once.

For the selected design you see:

- **Summary**: plate mass, sling force and the highest use.
- **Dimensions**: everything needed to mark out and cut the padeye.
- **Design checks**: each check with a bar showing how much of its limit is used.
  Select a check to open its calculation: each line shows the quantity, the
  formula, the same formula with the numbers put in, and the result, so you can
  repeat it with a calculator. The 3D view marks the part of the padeye the check
  is about in blue (for example the two shear planes above the hole).
- **Stress check**: the result of NEMO's built-in simulation.
- **3D view**: switch between **Model**, **Mesh** and **Stress**. The stress view
  colours the padeye from blue (low) to red (at yield).
- **How NEMO got here**: the record of the run, with the same seven steps as the
  run screen, for the design you selected.

### Report and files

**View calculation report** opens the PDF report inside NEMO. The report has a
cover sheet, design basis, dimensioned fabrication drawing with parts list,
design search, a calculation sheet for every check, stress results with figures,
a Fusion cross-check sheet and an audit trail. Use **Download** in the viewer's
top bar to save it, or **Open in new tab** to print it. Press Escape or the X to
close the viewer.

**Download files** opens a menu:

| Option | File | Use it for |
| --- | --- | --- |
| Everything | `.zip` | The report, 3D model, cutting profile and the run's records in one file, ready to send to a supervisor, checker or workshop |
| Calculation report | `.pdf` | Records, approval, the job file |
| 3D model | `.step` | Fusion, SolidWorks, Inventor, Rhino, ShipConstructor |
| Cutting profile | `.dxf` | Plasma, laser or oxy-fuel cutting tables. Full size, in mm. Cut lines on layer CUT |
| Engineering log | `.json` | Every step of the run with its time and numbers |
| Every design tried | `.csv` | Opens in Excel. One row per design the search tried, so anyone can check the choice |

### Fusion

**Open in Fusion** builds the selected design in Autodesk Fusion as a model you
can edit. The light in the top bar shows whether Fusion is linked: grey means the
connector is not installed, orange means Fusion is not running, green means
Fusion is connected. Click the light to install the connector.

Once you have used Fusion with a design, a **Fusion** section appears on its
results with the model Fusion built, the last **Check in NEMO** sent from Fusion
and any Fusion stress cross-check. See
[Using NEMO with Fusion](using-nemo-with-fusion.md) for the full steps.

### Changing or repeating a design

**Change the answers** takes you back to step 1 with your answers filled in.
**Run again** repeats the calculation with the same answers and keeps the old
results too.

## Verification

Select **Verification** in the top bar. It lists the problems NEMO is checked
against: a padeye worked out by hand, the 3D model volumes (padeye and pipe
bracket), a cantilever beam, a plate with a hole, the foil pressure solver used for
stabilizer fins, and a fin stock against beam theory. **Run verification now** runs
them on your laptop in about a minute and shows NEMO's answer next to the known answer for each one. Select
**Show how the reference is worked out** to see the reference calculation itself.
Use it to show a supervisor, examiner or checker that the engine works.

## Worked examples

### 5 t engine lift, two padeyes

Load 5 t, 2 points, slings at 60°, S355, default plates. Each padeye takes about
28.3 kN (2.89 t), so NEMO picks a 3.25 t shackle.

### 20 t module lift, four padeyes, no spreader

Load 20 t, 4 points, slings at 60°. Under **Advanced settings**, set **How
many points carry the load?** to **2**. Each padeye is then designed for half the
load, about 113 kN (11.5 t), instead of a quarter.
