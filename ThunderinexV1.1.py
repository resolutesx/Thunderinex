import os
import sys
import shutil
import difflib
import platform
import tkinter as tk
from tkinter import filedialog
import argparse
import logging
import time
import threading
import datetime
import json
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import logging
import ctypes


def run_as_admin():
    if ctypes.windll.shell32.IsUserAnAdmin():
        return  # Already running as admin
    else:
        # Re-run the program with admin rights
        script = os.path.abspath(sys.argv[0])
        params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}" {params}', None, 1
        )
        sys.exit()


Logger = logging.getLogger("ThunderModInstaller")

# External libraries for beautiful UI

REQUIRED_PACKAGES = ["rich", "questionary", "yaspin", "pyfiglet"]

missing_packages = []

for pkg in REQUIRED_PACKAGES:
    try:
        __import__(pkg)
    except ImportError:
        missing_packages.append(pkg)

if missing_packages:
    print(f"Missing packages detected: {', '.join(missing_packages)}. Installing...")
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_packages])
    print("Successfully installed missing packages. Restarting application...")
    os.execv(sys.executable, [sys.executable] + sys.argv)

import rich
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import (
    Progress,
    TaskID,
    TextColumn,
    BarColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.style import Style
from rich.theme import Theme
from rich import box
from rich.layout import Layout
from rich.live import Live
from rich.columns import Columns
from rich.syntax import Syntax
from rich.markdown import Markdown

import questionary
from questionary import Style as QuestionaryStyle
from yaspin import yaspin
from yaspin.spinners import Spinners
from pyfiglet import Figlet

console = Console()

questionary_style = QuestionaryStyle(
    [
        ("qmark", "fg:#00ffff bold"),  # ?
        ("question", "bold"),  # the question text
        ("answer", "fg:#00ff00 bold"),  # the selected answer
        ("pointer", "fg:#00ffff bold"),  # the arrow pointer
        ("highlighted", "fg:#00b2ff bold"),  # when an option is highlighted
        ("selected", "fg:#ff0000"),  # when an option is selected
    ]
)


def show_rendered_text():
    console = Console()
    f = Figlet(font="small")
    logo = f.renderText("Thunderinex V1.1").strip()
    logo_colored = Text(logo, style="bold blue")

    console.print(logo_colored)


def display_credits():
    console.print("\n")
    console.print(
        "[bold]Made by Tex at[/bold] "
        "[link=https://github.com/resolutesx]github.com/resolutesx[/link]"
    )

    input("Press Enter to continue...")


def clear_console():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

    show_rendered_text()


class ThunderModInstaller:
    def __init__(self, debug=False):
        """Initialize the ThunderMod Installer."""
        self.debug = debug
        if debug:
            Logger.setLevel(logging.DEBUG)

        # Config file path
        self.config_path = os.path.join(
            os.path.expanduser("~"), ".thundermod_config.json"
        )

        # Load config if exists
        self.config = self._load_config()

        # Common base paths for Thunderstore Mod Manager DataFolder
        self.base_paths = [
            os.path.expanduser("~/AppData/Roaming/Thunderstore Mod Manager/DataFolder"),
            os.path.expanduser(
                "~/AppData/Roaming/r2modman/Thunderstore Mod Manager/DataFolder"
            ),
            os.path.expanduser(
                "~/.config/r2modmanPlus-local/Thunderstore Mod Manager/DataFolder"
            ),
            os.path.expanduser(
                "~/Library/Application Support/r2modmanPlus-local/Thunderstore Mod Manager/DataFolder"
            ),
        ]

        # Add custom paths from config
        if self.config.get("custom_paths"):
            self.base_paths.extend(self.config.get("custom_paths"))

        # Automatically detect which path exists
        self.thunderstore_path = self._find_thunderstore_path()

        # Default search depth for finding BepInEx folders
        self.search_depth = self.config.get("search_depth", 5)

        # Default recent games list
        self.recent_games = self.config.get("recent_games", [])

        # Theme setting
        self.theme = self.config.get("theme", "default")

        Logger.debug(f"Thunderstore path: {self.thunderstore_path}")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        default_config = {
            "search_depth": 5,
            "recent_games": [],
            "custom_paths": [],
            "theme": "default",
            "auto_backup": True,
            "max_recent_games": 10,
        }

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                return {**default_config, **config}  # Merge with defaults
            except Exception as e:
                Logger.error(f"Error loading config: {e}")

        return default_config

    def _save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            Logger.error(f"Error saving config: {e}")

    def _add_recent_game(self, game_name: str, game_path: str, exe_path: str):
        """Add a game to recent games list."""
        # Remove if already exists
        self.recent_games = [g for g in self.recent_games if g.get("name") != game_name]

        # Add to the beginning of the list
        self.recent_games.insert(
            0,
            {
                "name": game_name,
                "path": game_path,
                "exe": exe_path,
                "timestamp": datetime.datetime.now().isoformat(),
            },
        )

        # Limit to max_recent_games
        max_games = self.config.get("max_recent_games", 10)
        self.recent_games = self.recent_games[:max_games]

        # Update config
        self.config["recent_games"] = self.recent_games
        self._save_config()

    def _find_thunderstore_path(self) -> Optional[str]:
        """Find the Thunderstore Mod Manager data folder path."""
        for path in self.base_paths:
            if os.path.exists(path):
                return path

        # If no predefined paths work, try to search for it
        if platform.system() == "Windows":
            appdata = os.path.expanduser("~/AppData/Roaming")
            for root, dirs, _ in os.walk(appdata):
                for dir_name in dirs:
                    if "thunderstore" in dir_name.lower():
                        possible_path = os.path.join(root, dir_name, "DataFolder")
                        if os.path.exists(possible_path):
                            return possible_path

        return None

    def add_custom_path(self, path: str) -> bool:
        """Add a custom Thunderstore path to configuration."""
        if not os.path.exists(path):
            return False

        custom_paths = self.config.get("custom_paths", [])
        if path not in custom_paths:
            custom_paths.append(path)
            self.config["custom_paths"] = custom_paths
            self._save_config()

            # Update base paths and try to find Thunderstore again
            self.base_paths.append(path)
            if not self.thunderstore_path:
                self.thunderstore_path = self._find_thunderstore_path()

            return True
        return False

    def find_game_directory(self, game_name: str) -> List[Tuple[str, float]]:
        """
        Find potential game directories in Thunderstore Mod Manager.
        Returns a list of tuples (directory_path, similarity_score)
        """
        if not self.thunderstore_path:
            Logger.error("Thunderstore Mod Manager data folder not found.")
            return []

        # List all game directories in Thunderstore path
        game_dirs = []
        try:
            with yaspin(
                Spinners.dots, text=f"Searching for game '{game_name}'..."
            ) as sp:
                entries = os.listdir(self.thunderstore_path)
                for entry in entries:
                    full_path = os.path.join(self.thunderstore_path, entry)
                    if os.path.isdir(full_path):
                        game_dirs.append((entry, full_path))
                sp.ok("✓")
        except Exception as e:
            Logger.error(f"Error listing Thunderstore directories: {e}")
            return []

        # Calculate similarity scores with the provided game name
        matches = []
        for dir_name, dir_path in game_dirs:
            similarity = difflib.SequenceMatcher(
                None, dir_name.lower(), game_name.lower()
            ).ratio()
            Logger.debug(f"Directory: {dir_name}, Similarity: {similarity}")
            matches.append((dir_path, similarity))

        # Sort by similarity score, highest first
        return sorted(matches, key=lambda x: x[1], reverse=True)

    def find_bepinex_folder(self, game_dir: str) -> Optional[str]:
        """Find BepInEx folder within the game directory structure."""
        bepinex_paths = []

        with yaspin(Spinners.bouncingBar, text="Searching for BepInEx folder...") as sp:
            # Expected path pattern: <game_dir>/profiles/Default/BepInEx
            default_path = os.path.join(game_dir, "profiles", "Default", "BepInEx")
            if os.path.exists(default_path) and os.path.isdir(default_path):
                Logger.debug(f"Found BepInEx at expected path: {default_path}")
                sp.ok("✓")
                return default_path

            # If not in the expected location, search within the game_dir
            Logger.debug(
                f"BepInEx not found at expected path, searching recursively..."
            )

            for root, dirs, _ in os.walk(game_dir):
                # Limit search depth to avoid excessive searching
                rel_path = os.path.relpath(root, game_dir)
                if rel_path.count(os.sep) > self.search_depth:
                    continue

                for dir_name in dirs:
                    if (
                        difflib.SequenceMatcher(
                            None, dir_name.lower(), "bepinex"
                        ).ratio()
                        > 0.8
                    ):
                        bepinex_path = os.path.join(root, dir_name)
                        Logger.debug(f"Found potential BepInEx folder: {bepinex_path}")
                        bepinex_paths.append(bepinex_path)

            if bepinex_paths:
                sp.ok("✓")
            else:
                sp.fail("✗")

        # Return the first match if any were found
        if bepinex_paths:
            return bepinex_paths[0]
        return None

    def install_bepinex(
        self, bepinex_source: str, game_exe_path: str, game_name: str
    ) -> bool:
        """Copy BepInEx folder to the game directory."""
        # Get the game directory from the exe path
        game_dir = os.path.dirname(game_exe_path)
        target_bepinex = os.path.join(game_dir, "BepInEx")

        console.print(
            f"Installing BepInEx from [path]{bepinex_source}[/path] to [path]{game_dir}[/path]"
        )

        try:
            # Check if BepInEx already exists in the target directory
            if os.path.exists(target_bepinex):
                console.print(
                    "[warning]BepInEx folder already exists in the target directory.[/warning]"
                )

                if not self.config.get("auto_backup", True):
                    overwrite = Confirm.ask("Overwrite existing BepInEx folder?")
                    if not overwrite:
                        console.print("[info]Installation canceled.[/info]")
                        return False

                # Backup the existing BepInEx folder
                backup_path = f"{target_bepinex}_backup_{int(time.time())}"
                with yaspin(
                    Spinners.bouncingBall,
                    text="Creating backup of existing BepInEx folder...",
                ) as sp:
                    shutil.copytree(target_bepinex, backup_path)
                    sp.ok("✓")
                console.print(f"Created backup at [path]{backup_path}[/path]")

                # Remove the existing folder
                with yaspin(
                    Spinners.clock, text="Removing old BepInEx folder..."
                ) as sp:
                    shutil.rmtree(target_bepinex)
                    sp.ok("✓")

            # Copy BepInEx folder to game directory with progress bar
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                console=console,
            ) as progress:
                task1 = progress.add_task("[cyan]Copying BepInEx folder...", total=100)

                # Count files for progress calculation
                total_files = sum(
                    [len(files) for _, _, files in os.walk(bepinex_source)]
                )
                copied_files = 0

                # Define a callback for updating progress
                def copy_with_progress(src, dst):
                    nonlocal copied_files
                    shutil.copy2(src, dst)
                    copied_files += 1
                    progress.update(
                        task1, completed=int(copied_files / total_files * 100)
                    )

                # Custom copytree with progress
                def custom_copytree(src, dst):
                    os.makedirs(dst, exist_ok=True)
                    for item in os.listdir(src):
                        s = os.path.join(src, item)
                        d = os.path.join(dst, item)
                        if os.path.isdir(s):
                            custom_copytree(s, d)
                        else:
                            copy_with_progress(s, d)

                custom_copytree(bepinex_source, target_bepinex)

            # Copy doorstop files to game directory if they exist
            doorstop_files = ["winhttp.dll", "doorstop_config.ini"]
            doorstop_copied = False

            with yaspin(
                Spinners.simpleDotsScrolling, text="Copying doorstop files..."
            ) as sp:
                for doorstop_file in doorstop_files:
                    doorstop_source = os.path.join(
                        os.path.dirname(bepinex_source), doorstop_file
                    )
                    if os.path.exists(doorstop_source):
                        shutil.copy2(
                            doorstop_source, os.path.join(game_dir, doorstop_file)
                        )
                        doorstop_copied = True
                        Logger.debug(f"Copied doorstop file: {doorstop_file}")

                if doorstop_copied:
                    sp.ok("✓")
                else:
                    sp.text = "No doorstop files found"
                    sp.ok("!")

            console.print("\n[success]BepInEx installed successfully![/success]")
            return True

        except Exception as e:
            Logger.error(f"Error installing BepInEx: {e}")
            console.print(f"[error]Error during installation: {e}[/error]")
            return False

    def select_exe_file(self, initial_dir=None) -> Optional[str]:
        """Open a file dialog to select the game executable."""
        # Create and hide the root window
        root = tk.Tk()
        root.withdraw()

        # Set initial directory to desktop if none provided
        if not initial_dir:
            initial_dir = os.path.join(os.path.expanduser("~"), "Desktop")

        console.print("\n[info]Opening file dialog to select game executable...[/info]")

        # Show the file dialog
        exe_path = filedialog.askopenfilename(
            title="Select Game Executable",
            initialdir=initial_dir,
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")],
        )

        root.destroy()

        if not exe_path:
            return None

        # Validate it's an executable
        if not exe_path.lower().endswith(".exe") and platform.system() == "Windows":
            console.print("[error]Selected file is not an executable.[/error]")
            return None

        return exe_path

    def _create_shortcut(self, exe_path):
        """Create a Windows shortcut to launch the game with BepInEx."""
        if platform.system() != "Windows":
            Logger.error("Shortcut creation is only supported on Windows.")
            return

        try:
            import win32com.client

            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            game_name = os.path.splitext(os.path.basename(exe_path))[0]
            shortcut_path = os.path.join(desktop, f"{game_name} (Modded).lnk")

            with yaspin(Spinners.pulse, text="Creating shortcut...") as sp:
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.Targetpath = exe_path
                shortcut.WorkingDirectory = os.path.dirname(exe_path)
                shortcut.IconLocation = exe_path
                shortcut.save()
                sp.ok("✓")

            console.print(f"Created shortcut: [path]{shortcut_path}[/path]")
            return True
        except ImportError:
            console.print(
                "[warning]win32com module not found. Install with: pip install pywin32[/warning]"
            )
            return False
        except Exception as e:
            Logger.error(f"Error creating shortcut: {e}")
            console.print(f"[error]Error creating shortcut: {e}[/error]")
            return False

    def display_recent_games(self):
        """Display recent games in a rich table."""
        if not self.recent_games:
            console.print("[info]No recent games.[/info]")
            return

        table = Table(title="Recent Games", box=box.ROUNDED)
        table.add_column("#", style="dim")
        table.add_column("Game", style="cyan")
        table.add_column("Last Used", style="green")
        table.add_column("Path", style="blue")

        for i, game in enumerate(self.recent_games, 1):
            # Parse the timestamp and format it
            try:
                timestamp = datetime.datetime.fromisoformat(game.get("timestamp", ""))
                time_str = timestamp.strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                time_str = "Unknown"

            # Truncate path if too long
            path = game.get("exe", "")
            if len(path) > 50:
                path = "..." + path[-47:]

            table.add_row(str(i), game.get("name", "Unknown"), time_str, path)

        console.print(table)

    def settings_menu(self):
        """Display and modify settings."""
        while True:
            console.print(
                Panel.fit(
                    "[title]ThunderMod Installer Settings[/title]", border_style="blue"
                )
            )

            options = [
                f"Search depth: {self.config.get('search_depth', 5)}",
                f"Auto backup: {'Enabled' if self.config.get('auto_backup', True) else 'Disabled'}",
                f"Maximum recent games: {self.config.get('max_recent_games', 10)}",
                "Add custom Thunderstore path",
                "View custom paths",
                "Back to main menu",
            ]

            choice = questionary.select(
                "Select an option:", choices=options, style=questionary_style
            ).ask()

            if not choice:
                return

            if "Search depth" in choice:
                depth = questionary.text(
                    "Enter new search depth (1-10):",
                    default=str(self.config.get("search_depth", 5)),
                    validate=lambda x: x.isdigit() and 1 <= int(x) <= 10,
                    style=questionary_style,
                ).ask()

                if depth:
                    self.config["search_depth"] = int(depth)
                    self.search_depth = int(depth)
                    self._save_config()
                    console.print("[success]Search depth updated.[/success]")

            elif "Auto backup" in choice:
                auto_backup = questionary.confirm(
                    "Enable automatic backup of existing BepInEx folders?",
                    default=self.config.get("auto_backup", True),
                    style=questionary_style,
                ).ask()

                if auto_backup is not None:
                    self.config["auto_backup"] = auto_backup
                    self._save_config()
                    console.print("[success]Auto backup setting updated.[/success]")

            elif "Maximum recent games" in choice:
                max_games = questionary.text(
                    "Enter maximum number of recent games to remember (1-50):",
                    default=str(self.config.get("max_recent_games", 10)),
                    validate=lambda x: x.isdigit() and 1 <= int(x) <= 50,
                    style=questionary_style,
                ).ask()

                if max_games:
                    self.config["max_recent_games"] = int(max_games)
                    self._save_config()
                    console.print("[success]Maximum recent games updated.[/success]")

            elif "Theme" in choice:
                theme = questionary.select(
                    "Select theme:",
                    choices=["default", "dark", "light", "colorful", "minimal"],
                    default=self.config.get("theme", "default"),
                    style=questionary_style,
                ).ask()

                if theme:
                    self.config["theme"] = theme
                    self.theme = theme
                    self._save_config()
                    console.print(
                        "[success]Theme updated. Restart for full effect.[/success]"
                    )

            elif "Add custom" in choice:
                path = questionary.text(
                    "Enter custom Thunderstore path:", style=questionary_style
                ).ask()

                if path:
                    if self.add_custom_path(path):
                        console.print(f"[success]Added custom path: {path}[/success]")
                    else:
                        console.print(f"[error]Invalid path: {path}[/error]")

            elif "View custom paths" in choice:
                custom_paths = self.config.get("custom_paths", [])
                if not custom_paths:
                    console.print("[info]No custom paths added.[/info]")
                else:
                    table = Table(title="Custom Thunderstore Paths", box=box.ROUNDED)
                    table.add_column("Path", style="green")
                    table.add_column("Status", style="cyan")

                    for path in custom_paths:
                        status = "✓ Exists" if os.path.exists(path) else "✗ Not found"
                        style = "green" if os.path.exists(path) else "red"
                        table.add_row(path, f"[{style}]{status}[/{style}]")

                    console.print(table)

                    if questionary.confirm(
                        "Would you like to remove any custom paths?",
                        default=False,
                        style=questionary_style,
                    ).ask():
                        to_remove = questionary.select(
                            "Select path to remove:",
                            choices=custom_paths + ["Cancel"],
                            style=questionary_style,
                        ).ask()

                        if to_remove and to_remove != "Cancel":
                            self.config["custom_paths"].remove(to_remove)
                            self._save_config()
                            console.print(f"[success]Removed: {to_remove}[/success]")

            elif "Back" in choice:
                return

    def display_help(self):
        """Display help information."""
        console.print(Panel.fit("ThunderMod Installer Help", style="bold cyan"))

        console.print("[bold underline]Overview[/bold underline]")
        console.print(
            "ThunderMod Installer helps you install BepInEx mods from Thunderstore Mod Manager to your pirated games.\n"
        )

        console.print("[bold underline]Common Tasks[/bold underline]")

        console.print("[bold]Installing BepInEx[/bold]")
        console.print("1. Select [cyan]Install BepInEx[/cyan] from the main menu")
        console.print(
            "2. Enter the game name - fuzzy matching will find the closest match"
        )
        console.print("3. Select the game's executable ([magenta].exe[/magenta]) file")
        console.print("4. BepInEx will be copied and installed\n")
        console.print(
            "- Before installing or re-installing, make sure you installed/removed all the mods you want to from the Thunderstore Mod Manager software."
        )
        console.print(
            "- If you would like to delete BepInEx, go into the game's directory, and delete the folder."
        )
        console.print(
            '- If you would like to reinstall BepInEx, you can install it again, or use the re-install option from the "Recent Games" section.\n'
        )

        console.print("[bold]Using Recent Games[/bold]")
        console.print(
            "- Select [cyan]View Recent Games[/cyan] to see recently modded games"
        )
        console.print("- You can quickly reinstall BepInEx for these games\n")

        console.print("[bold]Adding Custom Paths[/bold]")
        console.print("If your Thunderstore Mod Manager is in a non-standard location:")
        console.print("1. Go to [cyan]Settings[/cyan]")
        console.print("2. Select [cyan]Add custom Thunderstore path[/cyan]")
        console.print("3. Enter the path to the DataFolder\n")

        console.print("[bold underline]Troubleshooting[/bold underline]")
        console.print(
            "- [yellow]BepInEx folder not found[/yellow]: Make sure you've installed mods with BepInEx for your game in Thunderstore Mod Manager"
        )
        console.print(
            "- [yellow]Game not found[/yellow]: Try adding a custom path in Settings if your Thunderstore installation is in a non-standard location"
        )
        console.print(
            "- [yellow]Access is denied[/yellow]: Run the python file with administrative permissions from the main menu."
        )
        console.print(
            "- [yellow]Installation failed[/yellow]: Check if the game is running and close it before installing mods\n"
        )

        console.print("[bold underline]Command Line Usage[/bold underline]")
        console.print(
            '[green]python thundermod_installer.py --game "Game Name" --exe-path "C:/path/to/game.exe"[/green]\n'
        )

        console.print("[bold underline]Additional Options[/bold underline]")
        console.print("Use the [cyan]--debug[/cyan] flag for verbose logging.")
        console.print(
            "The keybind [cyan]Ctrl + C[/cyan] will return you to the main menu.\n"
        )

        input("\nPress Enter to return to main menu...")

    def show_welcome_screen(self):
        """Display welcome screen with ASCII art logo."""

        console = Console()

        os.system("cls" if platform.system() == "Windows" else "clear")

        f = Figlet(font="coinstak")
        logo = f.renderText(
            "ThunderMod Installer"
        ).strip()  # strip blank lines around ASCII art
        logo_colored = Text(logo, style="blue")

        layout = Layout()
        layout.split(
            Layout(name="logo"),
            Layout(name="subtitle"),
            Layout(name="info"),
        )

        layout["logo"].update(Panel(logo_colored, border_style="blue", padding=(0, 0)))
        layout["subtitle"].update(
            Text(
                "Easily install mods from Thunderstore to your games",
                style="italic cyan",
                justify="center",
            )
        )

        status_text = Text.from_markup(
            f"[bold]Status:[/bold] {'[green]Connected[/green]' if self.thunderstore_path else '[red]Not connected[/red]'}\n"
            f"[bold]Thunderstore Path:[/bold] {self.thunderstore_path or 'Not found'}\n"
            f"[bold]Version:[/bold] 1.0.0"
        )
        layout["info"].update(
            Panel(
                status_text,
                title="System Information",
                border_style="cyan",
                padding=(0, 0),
            )
        )
        console.print(layout)

        input("")  # no extra newlines here

    def run(self):
        """Run the installer command line interface."""
        # Show welcome screen

        while True:
            clear_console()
            console.print("\n")  # Add some spacing

            # Create menu
            menu_options = [
                "Install BepInEx",
                "View Recent Games",
                "Settings",
                "Run As Administrator",
                "Help",
                "Credits",
                "Exit",
            ]

            # Disable certain options if Thunderstore is not found
            if not self.thunderstore_path:
                menu_options[0] = {
                    "name": "Install BepInEx (Unavailable)",
                    "disabled": True,
                }

            choice = questionary.select(
                "What would you like to do?",
                choices=menu_options,
                style=questionary_style,
                qmark="⚝",
            ).ask()

            if not choice or "Exit" in choice:
                console.print("[info]Thank you for using ThunderMod Installer![/info]")
                return True

            if "Install BepInEx" in choice and not "Unavailable" in choice:
                self._install_workflow()

            if "Run As Administrator" in choice and not "Unavailable" in choice:
                run_as_admin()

            elif "View Recent Games" in choice:
                self._recent_games_workflow()

            elif "Settings" in choice:
                self.settings_menu()

            elif "Help" in choice:
                self.display_help()

            elif "Credits" in choice:
                display_credits()

    def _install_workflow(self):
        """Run the BepInEx installation workflow."""
        if not self.thunderstore_path:
            console.print("[error]Thunderstore Mod Manager not found![/error]")
            console.print("\nCouldn't locate Thunderstore Mod Manager data folder.")
            console.print("Please ensure Thunderstore Mod Manager is installed.")
            console.print("You can add a custom path in Settings.")
            return False

        # Get game name from user
        game_name = questionary.text("Enter game name:", style=questionary_style).ask()

        if not game_name:
            console.print("[error]No game name provided.[/error]")
            return False

        # Find potential game directories with spinner
        console.print(
            f"\n[info]Searching for game '{game_name}' in Thunderstore Mod Manager...[/info]"
        )
        game_matches = self.find_game_directory(game_name)

        if not game_matches:
            console.print(f"[error]No games found matching '{game_name}'.[/error]")
            time.sleep(2)
            return False

        # Display matches with threshold of at least 0.3 similarity
        valid_matches = [(path, score) for path, score in game_matches if score > 0.3]

        if not valid_matches:
            console.print(
                f"[error]No similar games found. Please check the game name.[/error]"
            )
            time.sleep(2)
            return False

        # If multiple matches, let user choose
        selected_game_dir = None
        game_folder_name = ""

        if len(valid_matches) == 1:
            selected_game_dir = valid_matches[0][0]
            game_folder_name = os.path.basename(selected_game_dir)
            console.print(f"Found game: [highlight]{game_folder_name}[/highlight]")
        else:
            # Create choices for questionary
            choices = []
            for i, (path, score) in enumerate(
                valid_matches[:10]
            ):  # Show top 10 matches
                folder_name = os.path.basename(path)
                choices.append(
                    {
                        "name": f"{folder_name} (similarity: {score:.2f})",
                        "value": (path, folder_name),
                    }
                )

            selection = questionary.select(
                "Multiple potential matches found. Please select one:",
                choices=choices,
                style=questionary_style,
            ).ask()

            if not selection:
                return False

            selected_game_dir, game_folder_name = selection

        # Find BepInEx folder
        console.print("\n[info]Searching for BepInEx folder...[/info]")
        bepinex_path = self.find_bepinex_folder(selected_game_dir)

        if not bepinex_path:
            console.print(
                "[error]BepInEx folder not found for the selected game.[/error]"
            )
            console.print(
                "Make sure you've installed mods with BepInEx for this game in Thunderstore Mod Manager."
            )
            time.sleep(2)
            return False

        console.print(f"Found BepInEx folder: [path]{bepinex_path}[/path]")

        # Prompt user to select game executable
        console.print(
            "\n[info]Please select the game's executable (.exe) file...[/info]"
        )
        exe_path = self.select_exe_file()

        if not exe_path:
            console.print("[error]No executable selected.[/error]")
            time.sleep(2)
            return False

        console.print(f"Selected game executable: [path]{exe_path}[/path]")

        # Install BepInEx
        console.print("\n[title]Installing BepInEx...[/title]")
        success = self.install_bepinex(bepinex_path, exe_path, game_folder_name)

        if success:
            # Add to recent games
            self._add_recent_game(game_folder_name, selected_game_dir, exe_path)

            console.print(
                "\n[success]✅ Installation successful! You can now launch the game and enjoy your mods.[/success]"
            )

            # Create a shortcut to launch the game with BepInEx
            if platform.system() == "Windows":
                create_shortcut = questionary.confirm(
                    "Would you like to create a shortcut to launch the game with BepInEx?",
                    default=True,
                    style=questionary_style,
                ).ask()

                if create_shortcut:
                    self._create_shortcut(exe_path)
        else:
            console.print("\n[error]❌ Installation failed. Please try again.[/error]")
            time.sleep(2)

        return success

    def _recent_games_workflow(self):
        if not self.recent_games:
            console.print("[info]No recent games found.[/info]")
            return

        self.display_recent_games()

        # Create choices for questionary
        choices = []
        for i, game in enumerate(self.recent_games):
            choices.append({"name": f"{game.get('name', 'Unknown')}", "value": i})
        choices.append({"name": "Back to main menu", "value": "back"})

        selection = questionary.select(
            "Select a game to reinstall BepInEx:",
            choices=choices,
            style=questionary_style,
        ).ask()

        if selection is None or selection == "back":
            return

        # Get the selected game
        game = self.recent_games[selection]
        game_dir = game.get("path")
        exe_path = game.get("exe")
        game_name = game.get("name")

        if not os.path.exists(game_dir) or not os.path.exists(exe_path):
            console.print(
                "[error]Game directory or executable no longer exists.[/error]"
            )

            # Ask if they want to remove it from recent games
            remove = questionary.confirm(
                "Would you like to remove this entry from recent games?",
                default=True,
                style=questionary_style,
            ).ask()

            if remove:
                self.recent_games.pop(selection)
                self.config["recent_games"] = self.recent_games
                self._save_config()
                console.print("[info]Entry removed from recent games.[/info]")

            return

        # Find BepInEx folder
        console.print("\n[info]Searching for BepInEx folder...[/info]")
        bepinex_path = self.find_bepinex_folder(game_dir)

        if not bepinex_path:
            console.print(
                "[error]BepInEx folder not found for the selected game.[/error]"
            )
            return

        console.print(f"Found BepInEx folder: [path]{bepinex_path}[/path]")

        # Confirm reinstallation
        install = questionary.confirm(
            f"Reinstall BepInEx for {game_name}?", default=True, style=questionary_style
        ).ask()

        if install:
            # Install BepInEx
            console.print("\n[title]Installing BepInEx...[/title]")
            success = self.install_bepinex(bepinex_path, exe_path, game_name)

            if success:
                # Update recent games (move to top)
                self._add_recent_game(game_name, game_dir, exe_path)
                console.print("\n[success]✅ Installation successful![/success]")
            else:
                console.print("\n[error]❌ Installation failed.[/error]")


def main():
    """Main entry point for the ThunderMod Installer."""
    parser = argparse.ArgumentParser(
        description="Install BepInEx for games from Thunderstore Mod Manager"
    )
    parser.add_argument("--game", type=str, help="Game name to search for")
    parser.add_argument(
        "--thunderstore-path",
        type=str,
        help="Custom path to Thunderstore Mod Manager DataFolder",
    )
    parser.add_argument("--exe-path", type=str, help="Path to game executable")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip backup of existing BepInEx folder",
    )
    parser.add_argument("--version", action="store_true", help="Show version and exit")

    args = parser.parse_args()

    # Show version if requested
    if args.version:
        console.print("[title]ThunderMod Installer[/title] v1.0.0")
        return 0

    # Create installer
    installer = ThunderModInstaller(debug=args.debug)

    # Override Thunderstore path if specified
    if args.thunderstore_path:
        if os.path.exists(args.thunderstore_path):
            installer.thunderstore_path = args.thunderstore_path
        else:
            Logger.error(
                f"Custom Thunderstore path not found: {args.thunderstore_path}"
            )
            console.print(
                f"[error]Custom Thunderstore path not found: {args.thunderstore_path}[/error]"
            )
            return 1

    # Set quiet mode in config if requested
    if args.quiet:
        installer.config["quiet"] = True

    # Set backup option if requested
    if args.no_backup:
        installer.config["auto_backup"] = False

    # If arguments are provided, use them
    if args.game and args.exe_path:
        # Non-interactive mode with arguments
        if not installer.thunderstore_path:
            Logger.error("Thunderstore Mod Manager not found!")
            console.print("[error]Thunderstore Mod Manager not found![/error]")
            return 1

        with yaspin(Spinners.dots, text=f"Searching for game '{args.game}'...") as sp:
            game_matches = installer.find_game_directory(args.game)
            valid_matches = [
                (path, score) for path, score in game_matches if score > 0.3
            ]

            if not valid_matches:
                sp.fail("✗")
                Logger.error(f"No games found matching '{args.game}'.")
                console.print(f"[error]No games found matching '{args.game}'.[/error]")
                return 1

            sp.ok("✓")

        selected_game_dir = valid_matches[0][0]
        game_name = os.path.basename(selected_game_dir)

        with yaspin(Spinners.dots, text="Searching for BepInEx folder...") as sp:
            bepinex_path = installer.find_bepinex_folder(selected_game_dir)

            if not bepinex_path:
                sp.fail("✗")
                Logger.error("BepInEx folder not found for the selected game.")
                console.print(
                    "[error]BepInEx folder not found for the selected game.[/error]"
                )
                return 1

            sp.ok("✓")

        if not os.path.exists(args.exe_path):
            Logger.error(f"Game executable not found: {args.exe_path}")
            console.print(f"[error]Game executable not found: {args.exe_path}[/error]")
            return 1

        success = installer.install_bepinex(bepinex_path, args.exe_path, game_name)
        return 0 if success else 1

    else:
        # Interactive mode
        try:
            success = installer.run()
            return 0 if success else 1
        except KeyboardInterrupt:
            console.print("\n[info]Operation canceled by user.[/info]")
            return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        console.print("\n[info]Operation canceled by user.[/info]")
        sys.exit(1)
    except Exception as e:
        Logger.error(f"Unexpected error: {e}")
        console.print(f"[error]Unexpected error: {e}[/error]")
        console.print_exception(show_locals=True)
        sys.exit(1)  #!/usr/bin/env python3
