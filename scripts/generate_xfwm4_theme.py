#!/usr/bin/env python3
"""
Generate complete XFWM4 window decoration themes for Vyron-V2-Dark and Vyron-V2-Light.
Includes themerc and all XPM pixmaps (title, borders, close, hide, maximize).
"""

import os

ROOT_DIR = "/Users/sujayv/Downloads/VyronOS/build/ui_v2/themes"

def create_xpm(width, height, color_hex):
    # Generates a solid 1-color XPM
    return f"""/* XPM */
static char *pixmap[] = {{
"{width} {height} 1 1",
"c {color_hex}",
""" + ',\n'.join([f'"{("c" * width)}"' for _ in range(height)]) + "\n};\n"

def create_circle_button_xpm(size, bg_hex, circle_hex, inner_glyph=None):
    # Generates a square XPM containing a centered circular button
    lines = []
    r = size // 2 - 2
    cx, cy = size // 2, size // 2
    for y in range(size):
        row = ""
        for x in range(size):
            dist_sq = (x - cx) ** 2 + (y - cy) ** 2
            if dist_sq <= (r - 1) ** 2:
                # Inside circle
                if inner_glyph == "x" and (abs(x - cx) == abs(y - cy)) and abs(x - cx) <= 2:
                    row += "W"  # White glyph
                elif inner_glyph == "-" and y == cy and abs(x - cx) <= 3:
                    row += "W"
                elif inner_glyph == "+" and (y == cy or x == cx) and abs(x - cx) <= 3 and abs(y - cy) <= 3:
                    row += "W"
                else:
                    row += "C"  # Circle color
            elif dist_sq <= r ** 2:
                row += "C"
            else:
                row += "."  # Background
        lines.append(f'"{row}"')

    return f"""/* XPM */
static char *pixmap[] = {{
"{size} {size} 3 1",
". c {bg_hex}",
"C c {circle_hex}",
"W c #FFFFFF",
""" + ',\n'.join(lines) + "\n};\n"

def build_theme(theme_name, bg_hex, text_hex, inactive_bg_hex, inactive_text_hex):
    theme_dir = os.path.join(ROOT_DIR, theme_name, "xfwm4")
    os.makedirs(theme_dir, exist_ok=True)

    themerc = f"""# Vyron UI V2 Window Manager Theme
button_offset=6
button_spacing=6
button_layout=CHM|O
title_alignment=center
title_font=Inter,Sans 10
title_shadow_active=false
title_shadow_inactive=false
active_text_color={text_hex}
inactive_text_color={inactive_text_hex}
active_text_shadow_color={bg_hex}
inactive_text_shadow_color={inactive_bg_hex}
full_width_title=true
maximized_offset=0
"""
    with open(os.path.join(theme_dir, "themerc"), "w") as f:
        f.write(themerc)

    # Title & border slices (height 28px)
    title_act = create_xpm(8, 28, bg_hex)
    title_inact = create_xpm(8, 28, inactive_bg_hex)
    for i in range(1, 6):
        with open(os.path.join(theme_dir, f"title-{i}-active.xpm"), "w") as f:
            f.write(title_act)
        with open(os.path.join(theme_dir, f"title-{i}-inactive.xpm"), "w") as f:
            f.write(title_inact)

    # Window borders (1px)
    border_hex = "#251D42" if "Dark" in theme_name else "#E2E8F0"
    with open(os.path.join(theme_dir, "top-left-active.xpm"), "w") as f:
        f.write(create_xpm(4, 28, bg_hex))
    with open(os.path.join(theme_dir, "top-left-inactive.xpm"), "w") as f:
        f.write(create_xpm(4, 28, inactive_bg_hex))
    with open(os.path.join(theme_dir, "top-right-active.xpm"), "w") as f:
        f.write(create_xpm(4, 28, bg_hex))
    with open(os.path.join(theme_dir, "top-right-inactive.xpm"), "w") as f:
        f.write(create_xpm(4, 28, inactive_bg_hex))

    for side in ["left", "right", "bottom", "bottom-left", "bottom-right"]:
        w, h = (1, 1)
        if "left" in side or "right" in side:
            w, h = (1, 8)
        with open(os.path.join(theme_dir, f"{side}-active.xpm"), "w") as f:
            f.write(create_xpm(w, h, border_hex))
        with open(os.path.join(theme_dir, f"{side}-inactive.xpm"), "w") as f:
            f.write(create_xpm(w, h, border_hex))

    # Circular Buttons (18x18 inside 28px height)
    btn_size = 18
    # Close: Red (#EF4444)
    # Hide: Amber (#F59E0B)
    # Maximize: Emerald (#10B981)
    # Inactive: Dim charcoal / gray
    inact_btn = "#475569" if "Dark" in theme_name else "#CBD5E1"

    buttons = {
        "close": ("#EF4444", "#DC2626", "x"),
        "hide": ("#F59E0B", "#D97706", "-"),
        "maximize": ("#10B981", "#059669", "+")
    }

    for bname, (norm, hover, glyph) in buttons.items():
        with open(os.path.join(theme_dir, f"{bname}-active.xpm"), "w") as f:
            f.write(create_circle_button_xpm(btn_size, bg_hex, norm))
        with open(os.path.join(theme_dir, f"{bname}-prelight.xpm"), "w") as f:
            f.write(create_circle_button_xpm(btn_size, bg_hex, hover, glyph))
        with open(os.path.join(theme_dir, f"{bname}-pressed.xpm"), "w") as f:
            f.write(create_circle_button_xpm(btn_size, bg_hex, hover, glyph))
        with open(os.path.join(theme_dir, f"{bname}-inactive.xpm"), "w") as f:
            f.write(create_circle_button_xpm(btn_size, inactive_bg_hex, inact_btn))

    print(f"XFWM4 theme '{theme_name}' generated successfully.")

if __name__ == "__main__":
    build_theme("Vyron-V2-Dark", "#120E28", "#F8FAFC", "#0E0B1F", "#64748B")
    build_theme("Vyron-V2-Light", "#FFFFFF", "#0F172A", "#F8FAFC", "#94A3B8")
