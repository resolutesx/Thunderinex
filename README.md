# Thunderinex — Help Guide

Thunderinex is a lightweight utility that simplifies installing **BepInEx** mods from **Thunderstore Mod Manager** to pirated games.  
Designed for fast, straightforward use.

**Version:** 1.1

---

## Requirements

- Python 3.6 or higher

---

## Installation

1. Download the `thunderinex.py` file.
2. Run the file using Python. Required libraries will install automatically.

---

## Installing BepInEx

1. From the main menu, select **Install BepInEx**.
2. Enter the game name. Fuzzy matching will find the closest match.
3. Select the game’s executable (`.exe`).
4. Thunderinex will install BepInEx automatically.

**Tips:**
- Ensure mods are installed or removed in Thunderstore Mod Manager *before* installing or reinstalling BepInEx.
- To remove BepInEx, delete the `BepInEx` folder from the game directory.
- To reinstall, either install again or use the **Re-install** option under **Recent Games**.

---

## Recent Games

- Select **View Recent Games** to manage previously modded games.
- Reinstall BepInEx with a single step from this section.

---

## Custom Thunderstore Paths

If Thunderstore Mod Manager is not in its default location:

1. Open **Settings**.
2. Choose **Add custom Thunderstore path**.
3. Enter the full path to the `DataFolder`.

---

## Troubleshooting

- **BepInEx folder not found**  
  Ensure mods were installed using BepInEx via Thunderstore Mod Manager.

- **Game not found**  
  Add a custom Thunderstore path under Settings.

- **Access is denied**  
  Run Thunderinex with administrator privileges.

- **Installation failed**  
  Close the game before attempting installation.

---

> You may modify this project freely. Do not claim the entire project as your own. Please keep the credits section intact.
