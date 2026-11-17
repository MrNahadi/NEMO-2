# Using NEMO with Fusion

Fusion is optional. NEMO designs, checks and reports a padeye on its own. Fusion
is for when you want to look at the design in a full CAD program, change it by
hand, or repeat the stress check in a second program as an independent check.

There are two ways to use them together:

- **With the NEMO Connector** (recommended). NEMO builds the padeye in Fusion for
  you, Fusion can send edited dimensions back to NEMO to be checked, and the
  Fusion stress results go straight into the calculation report.
- **Without the connector.** You open NEMO's STEP file in Fusion yourself and copy
  the values from the report. See [Without the connector](#without-the-connector).

## Set up the connector (once)

1. In NEMO, click **Connect to Fusion** in the top bar.
2. Click **Install connector**. NEMO copies a small add-in into Fusion's add-ins
   folder and sets it to start with Fusion. You do not need to open any folders.
3. If Fusion is open, close it completely. Then start Fusion.

The light next to **Fusion** in NEMO's top bar shows the link:

| Light | Label | Meaning |
| --- | --- | --- |
| Grey | Connect to Fusion | The connector is not installed yet. |
| Orange | Fusion not running | The connector is installed, but Fusion is closed or still starting. |
| Green | Fusion connected | Fusion is open and linked to NEMO. |

The light turns green a few seconds after Fusion starts. NEMO must be running
too. If NEMO is closed, the connector waits quietly and links up when you start
NEMO again.

When NEMO has a newer connector, the dialog shows **Update connector**. Click it,
then restart Fusion.

### Nothing happens on connect

The connector never builds anything on its own when it links up. It only builds
a model when you click **Open in Fusion**. Each request is used once and is
dropped if Fusion does not pick it up within about 45 seconds, or if Fusion is
restarted, so an old design never reappears in a new session.

## Open a design in Fusion

1. In NEMO, open the design's results and pick the design you want (Lightest,
   Balanced or Extra margin).
2. Click **Open in Fusion**. You can also use **Open in Fusion** in the ⋯ menu on
   the home screen, which opens the lightest design.
3. Fusion opens a new design and builds the padeye. NEMO shows a message when it
   is done, for example: "Opened in Fusion as a parametric model. Fusion's volume
   matches NEMO's to 0.020%."

The volume match shows that Fusion built the same shape NEMO checked. Expect a
difference well under 0.1%.

### What NEMO builds in Fusion

- A **parametric** model. Every main dimension is a Fusion user parameter, so you
  can change it in **Modify > Change Parameters** and the model updates:

  | Parameter | Dimension |
  | --- | --- |
  | `nemo_t` | Main plate thickness |
  | `nemo_R` | Head radius |
  | `nemo_Dh` | Hole diameter |
  | `nemo_L` | Base length |
  | `nemo_h` | Hole height above the base |
  | `nemo_tc` | Cheek plate thickness (0 when there are no cheek plates) |
  | `nemo_Rc` | Cheek plate radius |
  | `nemo_w` | Base weld leg |
  | `nemo_wc` | Cheek weld leg |

- The plate stands in the XY plane with **Y pointing up**, the base on the
  X axis and the thickness along Z.
- The nearest material from Fusion's library (for example **Steel** for a
  shipbuilding steel). Its properties are not exactly NEMO's grade, which is why
  the cross-check sheet asks you to check the material values.
- Two faces are tagged for the stress study: the flat base face (`nemo /
  fixed_support`) and the inside of the hole (`nemo / pin_bearing`).

Welds are not modelled as solids. NEMO checks them by calculation. Changing
`nemo_w` or `nemo_wc` does not change the Fusion model, but **Check in NEMO**
uses the new weld sizes.

## Check edited dimensions in NEMO

After you change parameters in Fusion, NEMO can check the edited padeye against
the same design rules.

1. In Fusion, on the **Solid** tab, find the **NEMO** panel.
2. Click **Check in NEMO**.
3. Fusion shows the result: whether it passes every required check, the highest
   use and which check it is, the plate mass, and which dimensions you changed.

The same result appears in NEMO under **Fusion > Last check from Fusion** on the
design's results. Checks from Fusion do not change NEMO's saved design or its
report. To make an edited design the official one, enter the dimensions in a new
NEMO design and run it, so it gets its own report.

If the dimensions do not make a valid padeye (for example, cheek plates larger
than the head), Fusion lists the problems instead.

## Cross-check the stress in Fusion

NEMO runs its own stress check (finite element analysis) on every design. A
second program giving the same answer is good evidence that the result is right.
Fusion's API cannot set up or solve a study by itself, so you set the study up by
hand. The cross-check sheet lists every value, so nothing is typed from memory.

1. In Fusion, on the **Solid** tab, click **NEMO > NEMO cross-check sheet**. A
   panel opens on the right with the study set-up.
2. Switch to the **Simulation** workspace and create a **Static Stress** study.
3. Assign the material with the values on the sheet. Check the numbers, not
   only the name.
4. Add a **Fixed** constraint to the flat base face.
5. Add a **Bearing Load** to the inside face of the hole, with the total force
   and angle from the sheet. A bearing load is Fusion's load for a pin pressing in
   a hole. Enter the total force, not the force per face.
6. Add local mesh control on the hole, then mesh and solve.
7. In the sheet panel, enter the Fusion results: total reaction force, peak von
   Mises stress near the hole, largest displacement and your name. Click **Send to
   NEMO**.

NEMO compares the results and says whether they agree:

- **Reaction force** must be within **2%** of the applied load. A bigger
  difference means the load or constraint is set up wrongly.
- **Peak stress near the hole** must be within **15%** of NEMO's value. The two
  programs apply the pin load and build the mesh differently, so small
  differences are normal.
- **Displacement** is shown for information only. It depends on how each program
  models the support.

The results are saved with the design and appear on the results page under
**Fusion stress cross-check**. The calculation report is rebuilt with section 7,
"Fusion results recorded", filled in with the values, the verdict and who
checked it. You can send the results again; the latest set replaces the earlier
one.

## Without the connector

1. In NEMO, open the design's results, click **Download files** and choose
   **3D model** (a STEP file).
2. In Fusion, choose **File > Open > Open from my computer** and select the STEP
   file. Choose millimetres if asked.
3. Follow the steps in [Cross-check the stress in Fusion](#cross-check-the-stress-in-fusion)
   using section 7 of the calculation report instead of the sheet panel. The
   STEP file uses NEMO's axes (Z up), and the force components in the report
   use the same axes.
4. Write the Fusion results into the empty table in section 7 of the printed
   report and sign it.

## If something goes wrong

| What you see | What to do |
| --- | --- |
| The light stays orange with Fusion open | Fusion may still be starting. Wait 10 seconds. If it stays orange, in Fusion open **Utilities > Add-Ins**, find **NEMOConnector** and click **Run**. Tick **Run on Startup**. |
| "Fusion did not pick up the request" | Fusion was busy or closed. Check the light is green and click **Open in Fusion** again. |
| "NEMO is not running" in Fusion | Start NEMO with **Start NEMO**, then try again. |
| "This design was not opened from NEMO" | **Check in NEMO** and the sheet only work on designs NEMO built. Use **Open in Fusion** in NEMO first. |
| "Differs from NEMO" after a cross-check | Check the load total and angle, the material values and that the constraint is on the base face only. Then solve and send again. |

The **Recent activity** list in the **Connect to Fusion** dialog shows what the
connector has done, which helps when asking someone for help.
