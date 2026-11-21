#!/usr/bin/env python3
"""
Generate minimal, high-resolution wallpapers for VyronOS (Dark and Light modes).
Resolution: 1920x1080
"""

import os
from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
BUILD_DIR = os.path.join(ROOT_DIR, "build", "wallpapers")
os.makedirs(BUILD_DIR, exist_ok=True)

DARK_PATH = os.path.join(BUILD_DIR, "vyron-dark.png")
LIGHT_PATH = os.path.join(BUILD_DIR, "vyron-light.png")

W, H = 1920, 1080

def create_dark_wallpaper():
    img = Image.new("RGB", (W, H), "#12131a")
    draw = ImageDraw.Draw(img)

    # Gradient background
    for y in range(H):
        ratio = y / H
        r = int(14 + ratio * 10)
        g = int(16 + ratio * 12)
        b = int(24 + ratio * 20)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Center emblem coordinates
    cx, cy = W // 2, H // 2 - 40
    size = 70

    # Draw geometric glowing V emblem
    # Outer glow
    for offset in range(8, 0, -1):
        alpha_color = (30 + offset * 10, 80 + offset * 15, 180 + offset * 8)
        draw.polygon([
            (cx - size - offset * 2, cy - size - offset),
            (cx, cy + size + offset * 2),
            (cx + size + offset * 2, cy - size - offset),
            (cx + size // 2, cy - size - offset),
            (cx, cy + size // 3),
            (cx - size // 2, cy - size - offset)
        ], outline=alpha_color, width=2)

    # Core emblem
    draw.polygon([
        (cx - size, cy - size),
        (cx, cy + size),
        (cx + size, cy - size),
        (cx + size // 2, cy - size),
        (cx, cy + size // 4),
        (cx - size // 2, cy - size)
    ], fill=(56, 139, 253))

    # Accent triangle in center
    draw.polygon([
        (cx - size // 4, cy - size // 2),
        (cx, cy - size // 6),
        (cx + size // 4, cy - size // 2)
    ], fill=(138, 43, 226))

    # Typography
    text = "V Y R O N   O S"
    subtext = "Desktop Edition 1.0 LTS • Linux 6.12"

    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    except Exception:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    draw.text((cx, cy + size + 50), text, fill=(240, 246, 252), font=font_large, anchor="mm")
    draw.text((cx, cy + size + 85), subtext, fill=(139, 148, 158), font=font_small, anchor="mm")

    img.save(DARK_PATH, "PNG")
    print(f"Generated Dark Wallpaper: {DARK_PATH}")

def create_light_wallpaper():
    img = Image.new("RGB", (W, H), "#f6f8fa")
    draw = ImageDraw.Draw(img)

    # Gradient background
    for y in range(H):
        ratio = y / H
        r = int(246 - ratio * 15)
        g = int(248 - ratio * 15)
        b = int(252 - ratio * 12)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Center emblem coordinates
    cx, cy = W // 2, H // 2 - 40
    size = 70

    # Draw geometric V emblem
    # Outer subtle shadow
    for offset in range(6, 0, -1):
        shadow_color = (200 - offset * 10, 205 - offset * 10, 215 - offset * 10)
        draw.polygon([
            (cx - size - offset, cy - size - offset),
            (cx, cy + size + offset),
            (cx + size + offset, cy - size - offset),
            (cx + size // 2, cy - size - offset),
            (cx, cy + size // 3),
            (cx - size // 2, cy - size - offset)
        ], outline=shadow_color, width=2)

    # Core emblem
    draw.polygon([
        (cx - size, cy - size),
        (cx, cy + size),
        (cx + size, cy - size),
        (cx + size // 2, cy - size),
        (cx, cy + size // 4),
        (cx - size // 2, cy - size)
    ], fill=(9, 105, 218))

    # Accent triangle in center
    draw.polygon([
        (cx - size // 4, cy - size // 2),
        (cx, cy - size // 6),
        (cx + size // 4, cy - size // 2)
    ], fill=(112, 87, 255))

    # Typography
    text = "V Y R O N   O S"
    subtext = "Desktop Edition 1.0 LTS • Linux 6.12"

    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    except Exception:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    draw.text((cx, cy + size + 50), text, fill=(36, 41, 47), font=font_large, anchor="mm")
    draw.text((cx, cy + size + 85), subtext, fill=(87, 96, 106), font=font_small, anchor="mm")

    img.save(LIGHT_PATH, "PNG")
    print(f"Generated Light Wallpaper: {LIGHT_PATH}")

def create_logo_icon():
    LOGO_PATH = os.path.join(BUILD_DIR, "vyron-logo.png")
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Outer circle in deep slate
    draw.ellipse([(2, 2), (size - 2, size - 2)], fill=(22, 27, 34, 255), outline=(56, 139, 253, 255), width=2)
    
    # Inner V
    cx, cy = size // 2, size // 2
    r = 16
    draw.polygon([
        (cx - r, cy - r),
        (cx, cy + r),
        (cx + r, cy - r),
        (cx + r // 2, cy - r),
        (cx, cy + r // 3),
        (cx - r // 2, cy - r)
    ], fill=(56, 139, 253, 255))
    
    img.save(LOGO_PATH, "PNG")
    print(f"Generated Logo Icon: {LOGO_PATH}")

if __name__ == "__main__":
    create_dark_wallpaper()
    create_light_wallpaper()
    create_logo_icon()
