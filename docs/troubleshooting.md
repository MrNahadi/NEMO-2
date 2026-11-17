# Troubleshooting

Find what you see, then follow the steps in order.

## Installing

**"Windows protected your PC" appears.**
Click **More info**, then **Run anyway**. Windows shows this for files downloaded
from the internet.

**The installer says uv or Python could not be downloaded.**
1. Check the laptop is online (open any website).
2. If you are on a company or university network, it may block downloads. Try a
   different network, such as a phone hotspot.
3. Run **Install NEMO.bat** again. It carries on from where it stopped.

**The installer says the app files are missing.**
Your copy of NEMO is incomplete. Get a fresh copy of the `NEMO2` folder that
includes `app\dist`, or ask whoever gave you NEMO.

## Starting

**Double-clicking the NEMO shortcut does nothing, or the window closes at once.**
1. Open the `NEMO2` folder and double-click **Start NEMO.bat** instead. Read the
   message in the window.
2. If it says NEMO is not installed, run **Install NEMO.bat**.

**The browser does not open.**
Open your browser yourself and go to `http://127.0.0.1:8765`.

**The browser says the page cannot be reached.**
The black NEMO window must stay open. Start NEMO again and wait a few seconds.

**The window says NEMO stopped with an error, and another NEMO might be open.**
Only one NEMO can run at a time. Look for another black NEMO window on the taskbar
and use that one, or close it and start NEMO again.

## Using NEMO

**A red message says "We couldn't reach the NEMO engine".**
The black NEMO window was closed. Start NEMO again. Your answers are saved each
time you move to the next step.

**The 3D view is blank or grey.**
Your browser may have 3D graphics switched off. Try a different browser (Edge or
Chrome), or update your graphics driver.

**"No padeye passed every check" or a similar message.**
See [If NEMO cannot find a design](understanding-results.md#if-nemo-cannot-find-a-design).

**Finding designs takes longer than five minutes.**
Large padeyes take longer to simulate. Leave it running. If nothing changes for
ten minutes, close the black window, start NEMO again, and press **Run again**.

**The report does not open.**
Choose **Download files > Calculation report** instead and open the file from your
Downloads folder.

## Fusion

**The Fusion light stays orange while Fusion is open.**
Wait 10 seconds. If it is still orange, in Fusion open **Utilities > Add-Ins**,
select **NEMOConnector**, click **Run** and tick **Run on Startup**.

**"Open in Fusion" shows the connector dialog instead of opening Fusion.**
Fusion is not linked yet. Follow the steps in the dialog, then try again.

More in [Using NEMO with Fusion](using-nemo-with-fusion.md#if-something-goes-wrong).

## Files

**Where are my designs?**
In `Documents\NEMO Projects`. Each design has its own folder.

**The STEP file opens at the wrong size.**
STEP files from NEMO are in millimetres. If your CAD program asks, choose
millimetres.
