# <img src="https://github.com/user-attachments/assets/cf522cbd-b589-4d3b-b683-7f9573c09efb" alt="logo" width="24"/> Thunderinex — Help Guide
![Thunderinex Banner](https://github.com/user-attachments/assets/6e808635-0ea9-40be-8202-b458cd72e00c)

**Thunderinex** is a lightweight utility designed to simplify the installation of **BepInEx** mods for **pirated games**, using mods installed via **Thunderstore Mod Manager**.  
The tool is fast, streamlined, and user-friendly, requiring minimal manual setup.

**Version:** 1.1  
**Author:** [resolutesx](https://github.com/resolutesx)  
**Built with help from:** Claude Sonnet 3.7

---

## 📚 Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Usage Guide](#usage-guide)
- [Installing BepInEx](#installing-bepinex)
- [Recent Games](#recent-games)
- [Custom Thunderstore Paths](#custom-thunderstore-paths)
- [Troubleshooting](#troubleshooting)
- [Credits & License](#credits--license)

---

## 🛠 Requirements

- Python 3.6 or higher must be installed on your system.

---

## 💾 Installation

1. Download the `thunderinex.py` script file.
2. Run the script using Python. Required libraries will be installed automatically on first launch:

```bash
python thunderinex.py
```

---

## ⚙️ Usage Guide

> **Step 1:** Install the mods you want using **Thunderstore Mod Manager**.  
> ✅ Ensure the mods are installed using **BepInEx** as the loader.

> **Step 2:** Use **Thunderinex** to install BepInEx into your pirated game by selecting the matching game and its executable.  
> 📁 This will copy the required BepInEx files from Thunderstore’s local cache into your game directory.

---

## 🔧 Installing BepInEx

1. Launch **Thunderinex**.
2. Select **Install BepInEx** from the main menu.
3. Enter the **game name** — fuzzy matching will find the closest result.
4. Choose the game’s `.exe` file when prompted.
5. Thunderinex will handle the BepInEx setup automatically.

### 🔁 Tips

- Install/remove mods in **Thunderstore Mod Manager** *before* installing BepInEx.
- To remove BepInEx: delete the `BepInEx` folder in your game directory.
- To reinstall BepInEx: rerun the installation or use **Reinstall** under **Recent Games**.

---

## 🕹 Recent Games

- View and manage previously modded games under **Recent Games**.
- Use the **Reinstall** option to quickly set up BepInEx again.

---

## 🧩 Custom Thunderstore Paths

If Thunderstore Mod Manager is not installed in the default location:

1. Open **Settings** in Thunderinex.
2. Select **Add custom Thunderstore path**.
3. Provide the full path to the `DataFolder`.

---

## 🛠 Troubleshooting

- **BepInEx folder not found**  
  → Ensure mods were installed using BepInEx via Thunderstore Mod Manager.

- **Game not found**  
  → Add a custom Thunderstore path under Settings.

- **Access is denied**  
  → Run Thunderinex with administrator privileges.

- **Installation failed**  
  → Ensure the game is closed before installation.

---

## 📝 Credits & License

> You may freely modify this project. However, do **not** claim the entire project as your own.  
> Please keep this credits section intact.
>
> Built with help from **Claude Sonnet 3.7**
