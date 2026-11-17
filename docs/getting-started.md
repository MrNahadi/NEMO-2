# Getting started

This guide takes you from a new Windows laptop to your first padeye design. You
do not need any coding or command-line experience.

## What you need

- A Windows 10 or 11 laptop.
- About 2 GB of free disk space.
- An internet connection for the first installation only. After that NEMO works
  offline.
- A web browser (Edge, Chrome or Firefox). NEMO runs inside your browser but
  everything stays on your laptop.

You do **not** need Python, Autodesk Fusion or any other engineering software to
use NEMO. Fusion is optional; see [Using NEMO with Fusion](using-nemo-with-fusion.md).

## 1. Put the NEMO folder somewhere permanent

1. Copy the `NEMO2` folder to a place you will keep it, for example
   `Documents\NEMO2` or your Desktop.
2. Do not move it after installing. If you do, run the installer again.

## 2. Install NEMO

1. Open the `NEMO2` folder in File Explorer.
2. Double-click **Install NEMO.bat**.
3. A black window opens and shows each step. The first installation downloads
   about 300 MB and takes 3 to 10 minutes, depending on your connection.
4. When you see **NEMO is installed**, press any key to close the window.

The installer:

- downloads a private copy of Python just for NEMO (it does not change any other
  program on your laptop);
- installs NEMO's calculation engine;
- puts a **NEMO** shortcut on your desktop.

If Windows shows a blue "Windows protected your PC" box, click **More info**, then
**Run anyway**. This appears because the file was downloaded, not because anything
is wrong. If you are unsure, ask whoever gave you NEMO.

## 3. Start NEMO

1. Double-click the **NEMO** shortcut on your desktop.
2. A small black window opens. Leave it open: it is NEMO's engine.
3. Your browser opens NEMO after a few seconds. If it does not, open your browser
   and go to `http://127.0.0.1:8765`.

To stop NEMO, close the black window.

## 4. Your first padeye in 10 minutes

Example: lifting a 5-tonne generator with two padeyes.

1. Click **New design**.
2. Type a name, for example `Generator lift`, keep **Lifting padeye** selected,
   and click **Create design**.
3. On **Describe the lift**:
   - How heavy is the load: type `5` and choose **tonnes**.
   - How many lifting points: **2**.
   - Sling angle: leave **60°**.
   - Material: **S355 structural steel**.
   - Plate thicknesses: leave the ticked sizes, or tick only the ones your
     workshop has.

   Watch the padeye on the right change as you type.
4. Click **Next: check the assumptions**. Leave the defaults and click
   **Find designs**.
5. Wait one to two minutes. The screen shows each step NEMO works through: the
   forces, the shackle, a chart of every design it tries, the mesh and the stress
   solve. Select any step to see its numbers.
6. On the results page, pick **Lightest**, **Balanced** or **Extra margin** to
   compare them.
7. Select a check, for example **Shearing out above the hole**, to see its full
   calculation and where it acts on the 3D padeye.
8. Click **View calculation report** to read the full engineering report. Use
   **Download** at the top of the viewer to save it.
9. Open **Download files** for the 3D model (STEP), the cutting profile (DXF), or
   **Everything** as one ZIP file.

Your design is saved. Next time you start NEMO it appears under **Saved designs**.

## Next

- [User guide](user-guide.md): every screen explained.
- [Understanding your results](understanding-results.md): what the checks mean.
- [Limits and safety](limits-and-safety.md): what NEMO does not check.
- [Troubleshooting](troubleshooting.md): if something does not work.
