# Installing NEMO from GitHub

This guide is for someone who has never installed NEMO, Python or any
programming tool. You only need to download, unzip and double-click. You will
not type any commands.

Allow about **20 minutes** the first time. Most of it is waiting while NEMO
downloads what it needs.

## Before you start

You need:

- **A Windows 10 or Windows 11 computer.** NEMO's installer does not work on Mac
  or Linux.
- **About 2 GB of free disk space.** NEMO itself takes about 0.8 GB once
  installed. The rest is room for your designs.
- **An internet connection** for the installation. After that NEMO works without
  internet.
- **A web browser**: Microsoft Edge, Google Chrome or Firefox. NEMO opens inside
  your browser, but it runs only on your own computer. Your designs are not sent
  anywhere.

You do **not** need to install Python, Git, Autodesk Fusion or anything else
first. The installer gets what NEMO needs.

If you use a work or university computer, the IT department may block
downloaded programs. If one of the steps below is blocked, show this guide to
your IT department.

## Step 1: Download NEMO

1. Open this page in your browser: <https://github.com/MrNahadi/NEMO-2>
2. Click the green **Code** button near the top right of the list of files.
3. In the menu that opens, click **Download ZIP**.
4. Your browser saves a file called **NEMO-2-main.zip** (about 20 MB) in your
   **Downloads** folder.

You do not need a GitHub account to download it.

## Step 2: Unblock the download

Windows marks files downloaded from the internet and asks about them later.
Unblocking the ZIP file now saves you from several warnings later.

1. Open your **Downloads** folder.
2. Right-click **NEMO-2-main.zip** and choose **Properties**.
3. At the bottom of the **General** tab, if there is a box called **Unblock**,
   tick it.
4. Click **OK**.

If there is no **Unblock** box, carry on. It just means Windows has not marked
the file.

## Step 3: Unzip NEMO into a permanent place

NEMO must live in a folder you will keep. Do not run it from inside the ZIP file
or from the Downloads folder.

We recommend **C:\NEMO**, because:

- a short folder path avoids Windows errors about file names being too long;
- it keeps NEMO out of OneDrive, which would otherwise try to upload all of
  NEMO's files.

1. Right-click **NEMO-2-main.zip** and choose **Extract All...**
2. In the box that shows the destination, delete what is there and type
   `C:\`
3. Click **Extract**. Windows creates a folder called **C:\NEMO-2-main**.
4. If Windows asks for permission to write to C:\, click **Continue**. If you
   are not allowed, extract to your user folder instead. That is the folder
   with your name, the one that holds Documents and Downloads. Then use that
   location wherever this guide says C:\NEMO.
5. Open **This PC > Local Disk (C:)**, right-click **NEMO-2-main**, choose
   **Rename** and call it `NEMO`.

You should now have a folder **C:\NEMO** that contains, among others, folders
called `app`, `docs` and `engine`, and two files called **Install NEMO** and
**Start NEMO**.

If you see a folder called **NEMO-2-main** inside another **NEMO-2-main**,
open it until you see **Install NEMO** and **Start NEMO**. That inner folder is
the one to use.

**Do not move or rename the NEMO folder after installing it.** If you do, run
the installer again (Step 4).

## Step 4: Install NEMO

1. Open the **C:\NEMO** folder.
2. Double-click **Install NEMO**. Windows may show it as **Install NEMO.bat**.
   Its type is "Windows Batch File".
3. If a blue box says **Windows protected your PC**, click **More info**, then
   **Run anyway**. Windows shows this for any program downloaded from the
   internet that it does not recognise.
4. A black window opens and lists each step as it goes:
   - **Checking for uv.** uv is a small tool that downloads Python for NEMO.
   - **Getting Python 3.12.** This is a private copy for NEMO. It does not
     change any other program on your computer.
   - **Installing the NEMO engine.** This is the longest step. It downloads
     about 300 MB and can take 5 to 15 minutes. The window may look busy or
     quiet for a while. Leave it alone.
   - **Testing the installation.** You should see **NEMO engine ... is ready**.
   - **Adding a NEMO shortcut to the desktop.**
5. When the window says **NEMO is installed** in green, press any key to close
   it.

If the window shows a red message instead, read it, then see
[If something goes wrong](#if-something-goes-wrong) below. It is safe to run
**Install NEMO** again. It carries on from where it stopped.

## Step 5: Start NEMO

1. Double-click the **NEMO** shortcut on your desktop.
2. A black window opens with the title **NEMO - close this window to stop
   NEMO**. Leave it open while you work. It is NEMO's engine.
3. After a few seconds your browser opens NEMO. If it does not, open your
   browser and go to <http://127.0.0.1:8765>
4. If Windows asks whether to allow NEMO through the firewall, you can click
   **Cancel**. NEMO only talks to your own computer and does not need network
   access.

To stop NEMO, close the black window. Closing the browser tab does not stop it.

## Step 6: Check that it works

1. In NEMO, click **Verification** at the top right.
2. Click **Run verification now**. NEMO solves a set of test problems with
   known answers and compares its results with them. This takes about half a
   minute.
3. The page should say **every benchmark passed**, and every row should show
   **Pass**.

You are ready. For your first design, follow
[Your first padeye in 10 minutes](getting-started.md#4-your-first-padeye-in-10-minutes).

## Everyday use

- **Start NEMO:** double-click the **NEMO** shortcut on the desktop.
- **Stop NEMO:** close the black NEMO window.
- **Your designs** are saved in **Documents\NEMO Projects**, one folder per
  design. They are not inside C:\NEMO.
- **Autodesk Fusion** is optional. To connect it, see
  [Using NEMO with Fusion](using-nemo-with-fusion.md).

## Getting a newer version

Your designs are kept in Documents\NEMO Projects, so replacing NEMO does not
touch them.

1. Close the black NEMO window if it is open.
2. Delete the **C:\NEMO** folder.
3. Repeat Steps 1 to 4: download the new ZIP, unblock it, unzip it, rename the
   folder to **C:\NEMO** and run **Install NEMO**.

The second installation is quicker, because some downloads are kept from the
first time.

## Removing NEMO

1. Close the black NEMO window if it is open.
2. Delete the **C:\NEMO** folder and the **NEMO** shortcut on your desktop.
3. If you no longer want your designs, delete **Documents\NEMO Projects**.

The installer also left two small tools in your user folder, which you can
delete if nothing else uses them:

- uv, in `.local\bin` inside your user folder;
- NEMO's copy of Python and a download cache, in the `uv` folders inside
  `AppData\Roaming` and `AppData\Local`.

## If something goes wrong

| What you see | What to do |
| --- | --- |
| **Windows protected your PC** | Click **More info**, then **Run anyway**. To avoid this, unblock the ZIP file before unzipping it (Step 2). |
| The installer says **uv** or **Python could not be downloaded** | Check the computer is online by opening any website. Company and university networks sometimes block these downloads, so try another network, such as a phone hotspot. Then run **Install NEMO** again. |
| The installer stops with a red message during **Installing the NEMO engine** | Run **Install NEMO** again. Most failures are a dropped connection, and it carries on from where it stopped. |
| The installer says **the app files are missing** | The download is incomplete. Download the ZIP again from Step 1. |
| Unzipping fails, or Windows says a **file name is too long** | Unzip to `C:\` as in Step 3, not to Downloads or the Desktop. |
| Double-clicking **Install NEMO** opens it in Notepad | You opened it with the wrong program. Right-click it and choose **Open**. |
| Your antivirus deletes or blocks a file | Ask whoever manages your computer to allow the C:\NEMO folder, then download and unzip again. |
| The **NEMO** shortcut does nothing, or the window closes at once | Open C:\NEMO and double-click **Start NEMO**, then read the message in the window. If it says NEMO is not installed, run **Install NEMO**. |
| The browser does not open | Open your browser and go to <http://127.0.0.1:8765> |
| The browser says the page **cannot be reached** | The black NEMO window must stay open. Start NEMO again and wait a few seconds. |
| **NEMO stopped with an error** and another NEMO might be open | Only one NEMO can run at a time. Look for another black NEMO window on the taskbar and use it, or close it and start again. |
| The 3D view is blank or grey | Try another browser (Edge or Chrome), or update your graphics driver. |

For problems once NEMO is running, see [Troubleshooting](troubleshooting.md).
