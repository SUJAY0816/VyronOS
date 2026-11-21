#!/usr/bin/env python3
"""
==============================================================================
VYRON OS — Phase 5.1 Dynamic Dual-Theme Switching Engine (Vyron UI V2)
Location: /usr/local/bin/vyron-theme
Commands:
  vyron-theme dark      - Switch to Vyron UI V2 Dark Mode
  vyron-theme light     - Switch to Vyron UI V2 Light Mode
  vyron-theme switch    - Toggle between Dark and Light mode
  vyron-theme status    - Display current active theme
  vyron-theme --json    - Output JSON theme status
==============================================================================
"""

import os
import sys
import json
import subprocess

CONFIG_DIR = os.path.expanduser("~/.config/vyron")
STATE_FILE = os.path.join(CONFIG_DIR, "theme.state")
DARK_WALLPAPER = "/usr/share/backgrounds/vyron-dark.png"
LIGHT_WALLPAPER = "/usr/share/backgrounds/vyron-light.png"

def run_cmd(args):
    try:
        res = subprocess.run(args, capture_output=True, text=True, timeout=5)
        return res.returncode == 0
    except Exception:
        return False

def run_cmd_out(args):
    try:
        res = subprocess.run(args, capture_output=True, text=True, timeout=5)
        return res.stdout.strip()
    except Exception:
        return ""

def get_current_theme():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                theme = f.read().strip().lower()
                if theme in ["dark", "light"]:
                    return theme
        except Exception:
            pass
    gtk_theme = run_cmd_out(["xfconf-query", "-c", "xsettings", "-p", "/Net/ThemeName"])
    if "light" in gtk_theme.lower():
        return "light"
    return "dark"

def set_xfconf_property(channel, prop, value, prop_type="string"):
    run_cmd(["xfconf-query", "-c", channel, "-p", prop, "-s", str(value)])
    if not run_cmd(["xfconf-query", "-c", channel, "-p", prop]):
        run_cmd(["xfconf-query", "-c", channel, "-p", prop, "-n", "-t", prop_type, "-s", str(value)])

def set_wallpapers(wallpaper_path):
    if not os.path.exists(wallpaper_path):
        return
    out = run_cmd_out(["xfconf-query", "-c", "xfce4-desktop", "-l"])
    if out:
        for line in out.splitlines():
            line = line.strip()
            if "last-image" in line or "image-path" in line:
                run_cmd(["xfconf-query", "-c", "xfce4-desktop", "-p", line, "-s", wallpaper_path])
    set_xfconf_property("xfce4-desktop", "/backdrop/screen0/monitor0/workspace0/last-image", wallpaper_path, "string")
    set_xfconf_property("xfce4-desktop", "/backdrop/screen0/monitor0/workspace0/image-style", 5, "int")

def apply_theme(theme):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    theme = theme.lower()
    
    if theme == "dark":
        gtk_theme = "Vyron-V2-Dark"
        wm_theme = "Vyron-V2-Dark"
        icon_theme = "Vyron-V2-Icons"
        wallpaper = DARK_WALLPAPER
    else:
        gtk_theme = "Vyron-V2-Light"
        wm_theme = "Vyron-V2-Light"
        icon_theme = "Vyron-V2-Icons"
        wallpaper = LIGHT_WALLPAPER

    set_xfconf_property("xsettings", "/Net/ThemeName", gtk_theme)
    set_xfconf_property("xfwm4", "/general/theme", wm_theme)
    set_xfconf_property("xsettings", "/Net/IconThemeName", icon_theme)
    set_wallpapers(wallpaper)

    try:
        with open(STATE_FILE, "w") as f:
            f.write(theme)
    except Exception:
        pass

    if os.environ.get("DISPLAY"):
        run_cmd(["notify-send", "-a", "Vyron UI V2", f"Vyron Theme: {theme.capitalize()} Active", f"Applied {gtk_theme} theme."])

    print(f"Applied Vyron UI V2 {theme.capitalize()} Mode: GTK={gtk_theme}, WM={wm_theme}, Wallpaper={wallpaper}")

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["status", "--status"]:
        current = get_current_theme()
        if "--json" in sys.argv:
            print(json.dumps({"theme": current, "status": "active", "version": "2.0.0"}))
        else:
            print(f"Vyron UI V2 Theme Status: {current.upper()} MODE")
        return

    cmd = sys.argv[1].lower()
    if cmd == "dark":
        apply_theme("dark")
    elif cmd == "light":
        apply_theme("light")
    elif cmd in ["switch", "toggle"]:
        current = get_current_theme()
        next_theme = "light" if current == "dark" else "dark"
        apply_theme(next_theme)
    elif cmd == "--json":
        print(json.dumps({"theme": get_current_theme(), "status": "active", "version": "2.0.0"}))
    else:
        print(f"Usage: vyron-theme [dark|light|switch|status|--json]")
        sys.exit(1)

if __name__ == "__main__":
    main()
