#!/usr/bin/env python3
"""
==============================================================================
VYRON OS — Phase 5.1 Vyron UI V2 Squircle Icon Family Generator
Generates modern, vibrant squircle SVG and PNG icons (16, 22, 24, 32, 48, 64, 128)
matching the Vyron UI V2 design system (electric violet, soft cyan, charcoal).
==============================================================================
"""

import os
from PIL import Image, ImageDraw

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
ICONS_DIR = os.path.join(ROOT_DIR, "assets", "icons")
os.makedirs(ICONS_DIR, exist_ok=True)

# 26 Complete Vyron UI V2 SVG Definitions
V2_SVGS = {
    "vyron-logo": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#06B6D4"/>
      <stop offset="100%" stop-color="#7C3AED"/>
    </linearGradient>
  </defs>
  <rect x="4" y="4" width="56" height="56" rx="16" fill="url(#bg)"/>
  <polygon points="16,18 32,48 48,18 39,18 32,32 25,18" fill="#FFFFFF"/>
</svg>''',

    "vyron-browser": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="brw" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#F97316"/>
      <stop offset="50%" stop-color="#EC4899"/>
      <stop offset="100%" stop-color="#8B5CF6"/>
    </linearGradient>
  </defs>
  <rect x="4" y="4" width="56" height="56" rx="16" fill="url(#brw)"/>
  <circle cx="32" cy="32" r="18" fill="none" stroke="#FFFFFF" stroke-width="3"/>
  <ellipse cx="32" cy="32" rx="8" ry="18" fill="none" stroke="#FFFFFF" stroke-width="2.5"/>
  <line x1="14" y1="32" x2="50" y2="32" stroke="#FFFFFF" stroke-width="2.5"/>
</svg>''',

    "vyron-code": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="code" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0284C7"/>
      <stop offset="100%" stop-color="#06B6D4"/>
    </linearGradient>
  </defs>
  <rect x="4" y="4" width="56" height="56" rx="16" fill="url(#code)"/>
  <polyline points="24,22 14,32 24,42" fill="none" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
  <polyline points="40,22 50,32 40,42" fill="none" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
  <line x1="35" y1="18" x2="29" y2="46" stroke="#FFFFFF" stroke-width="3.5" stroke-linecap="round"/>
</svg>''',

    "vyron-files": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="files" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#F59E0B"/>
      <stop offset="100%" stop-color="#D97706"/>
    </linearGradient>
  </defs>
  <rect x="4" y="4" width="56" height="56" rx="16" fill="url(#files)"/>
  <path d="M16 22 H28 L32 26 H48 V44 H16 Z" fill="#FFFFFF" fill-opacity="0.95"/>
  <path d="M16 26 H48 V44 H16 Z" fill="#FEF3C7" fill-opacity="0.8"/>
</svg>''',

    "vyron-folder": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="fld" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#38BDF8"/>
      <stop offset="100%" stop-color="#0284C7"/>
    </linearGradient>
  </defs>
  <rect x="4" y="4" width="56" height="56" rx="16" fill="url(#fld)"/>
  <path d="M16 22 H28 L32 26 H48 V44 H16 Z" fill="#FFFFFF"/>
</svg>''',

    "vyron-home": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="hm" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#8B5CF6"/>
      <stop offset="100%" stop-color="#6D28D9"/>
    </linearGradient>
  </defs>
  <rect x="4" y="4" width="56" height="56" rx="16" fill="url(#hm)"/>
  <polygon points="32,18 16,32 22,32 22,46 42,46 42,32 48,32" fill="#FFFFFF"/>
</svg>''',

    "vyron-terminal": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="term" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1E293B"/>
      <stop offset="100%" stop-color="#0F172A"/>
    </linearGradient>
  </defs>
  <rect x="4" y="4" width="56" height="56" rx="16" fill="url(#term)" stroke="#334155" stroke-width="1.5"/>
  <polyline points="18,24 28,32 18,40" fill="none" stroke="#A855F7" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
  <line x1="32" y1="40" x2="46" y2="40" stroke="#06B6D4" stroke-width="4" stroke-linecap="round"/>
</svg>''',

    "vyron-system-monitor": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="sysmon" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#6366F1"/>
      <stop offset="100%" stop-color="#8B5CF6"/>
    </linearGradient>
  </defs>
  <rect x="4" y="4" width="56" height="56" rx="16" fill="url(#sysmon)"/>
  <polyline points="14,34 22,34 27,20 33,46 39,28 44,34 50,34" fill="none" stroke="#FFFFFF" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
</svg>''',

    "vyron-editor": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="edit" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#10B981"/>
      <stop offset="100%" stop-color="#059669"/>
    </linearGradient>
  </defs>
  <rect x="4" y="4" width="56" height="56" rx="16" fill="url(#edit)"/>
  <path d="M20 18 H40 L46 24 V46 H20 Z" fill="#FFFFFF"/>
  <line x1="26" y1="30" x2="38" y2="30" stroke="#059669" stroke-width="2.5" stroke-linecap="round"/>
  <line x1="26" y1="36" x2="38" y2="36" stroke="#059669" stroke-width="2.5" stroke-linecap="round"/>
</svg>''',

    "vyron-calc": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="calc" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#8B5CF6"/>
      <stop offset="100%" stop-color="#7C3AED"/>
    </linearGradient>
  </defs>
  <rect x="4" y="4" width="56" height="56" rx="16" fill="url(#calc)"/>
  <rect x="18" y="16" width="28" height="10" rx="2" fill="#EDE9FE"/>
  <circle cx="23" cy="34" r="3" fill="#FFFFFF"/>
  <circle cx="32" cy="34" r="3" fill="#FFFFFF"/>
  <circle cx="41" cy="34" r="3" fill="#FFFFFF"/>
  <circle cx="23" cy="44" r="3" fill="#FFFFFF"/>
  <circle cx="32" cy="44" r="3" fill="#FFFFFF"/>
  <circle cx="41" cy="44" r="3" fill="#F43F5E"/>
</svg>''',

    "vyron-settings": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="sett" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#475569"/>
      <stop offset="100%" stop-color="#334155"/>
    </linearGradient>
  </defs>
  <rect x="4" y="4" width="56" height="56" rx="16" fill="url(#sett)"/>
  <circle cx="32" cy="32" r="8" fill="none" stroke="#FFFFFF" stroke-width="4"/>
  <path d="M32 16 v4 M32 44 v4 M16 32 h4 M44 32 h4 M21 21 l3 3 M39 39 l3 3 M21 43 l3 -3 M39 25 l3 -3" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round"/>
</svg>''',

    "vyron-launcher": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="lnch" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1E1B4B"/>
      <stop offset="100%" stop-color="#0F0C2A"/>
    </linearGradient>
  </defs>
  <rect x="4" y="4" width="56" height="56" rx="16" fill="url(#lnch)" stroke="#4338CA" stroke-width="1.5"/>
  <circle cx="20" cy="20" r="4" fill="#C084FC"/>
  <circle cx="32" cy="20" r="4" fill="#38BDF8"/>
  <circle cx="44" cy="20" r="4" fill="#C084FC"/>
  <circle cx="20" cy="32" r="4" fill="#38BDF8"/>
  <circle cx="32" cy="32" r="4" fill="#FFFFFF"/>
  <circle cx="44" cy="32" r="4" fill="#38BDF8"/>
  <circle cx="20" cy="44" r="4" fill="#C084FC"/>
  <circle cx="32" cy="44" r="4" fill="#38BDF8"/>
  <circle cx="44" cy="44" r="4" fill="#C084FC"/>
</svg>''',

    "vyron-trash": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="trsh" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#64748B"/>
      <stop offset="100%" stop-color="#475569"/>
    </linearGradient>
  </defs>
  <rect x="4" y="4" width="56" height="56" rx="16" fill="url(#trsh)"/>
  <path d="M22 24 L24 46 H40 L42 24 Z" fill="#FFFFFF" fill-opacity="0.9"/>
  <line x1="18" y1="20" x2="46" y2="20" stroke="#FFFFFF" stroke-width="3.5" stroke-linecap="round"/>
</svg>''',

    "vyron-power": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="pwr" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#EF4444"/>
      <stop offset="100%" stop-color="#DC2626"/>
    </linearGradient>
  </defs>
  <rect x="4" y="4" width="56" height="56" rx="16" fill="url(#pwr)"/>
  <path d="M32 18 V30" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round"/>
  <path d="M22 23 A14 14 0 1 0 42 23" fill="none" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round"/>
</svg>''',

    "vyron-shutdown": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="sht" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#DC2626"/>
      <stop offset="100%" stop-color="#991B1B"/>
    </linearGradient>
  </defs>
  <rect x="4" y="4" width="56" height="56" rx="16" fill="url(#sht)"/>
  <path d="M32 18 V30" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round"/>
  <path d="M22 23 A14 14 0 1 0 42 23" fill="none" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round"/>
</svg>''',

    "vyron-restart": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="rst" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#F59E0B"/>
      <stop offset="100%" stop-color="#D97706"/>
    </linearGradient>
  </defs>
  <rect x="4" y="4" width="56" height="56" rx="16" fill="url(#rst)"/>
  <path d="M44 28 A16 16 0 1 0 44 36" fill="none" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round"/>
  <polyline points="44,20 44,28 36,28" fill="none" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
</svg>''',

    "vyron-lock": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="lck" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#64748B"/>
      <stop offset="100%" stop-color="#334155"/>
    </linearGradient>
  </defs>
  <rect x="4" y="4" width="56" height="56" rx="16" fill="url(#lck)"/>
  <rect x="20" y="28" width="24" height="18" rx="3" fill="#FFFFFF"/>
  <path d="M24 28 V22 A8 8 0 0 1 40 22 V28" fill="none" stroke="#FFFFFF" stroke-width="3.5" stroke-linecap="round"/>
</svg>''',

    "vyron-wifi": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <path d="M12 24 A26 26 0 0 1 52 24" fill="none" stroke="#FFFFFF" stroke-width="3.5" stroke-linecap="round"/>
  <path d="M19 32 A18 18 0 0 1 45 32" fill="none" stroke="#FFFFFF" stroke-width="3.5" stroke-linecap="round"/>
  <path d="M26 40 A10 10 0 0 1 38 40" fill="none" stroke="#FFFFFF" stroke-width="3.5" stroke-linecap="round"/>
  <circle cx="32" cy="48" r="3" fill="#FFFFFF"/>
</svg>''',

    "vyron-ethernet": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect x="18" y="16" width="28" height="24" rx="4" fill="none" stroke="#FFFFFF" stroke-width="3.5"/>
  <path d="M26 40 v8 M38 40 v8 M18 48 h28" stroke="#FFFFFF" stroke-width="3.5" stroke-linecap="round"/>
</svg>''',

    "vyron-network": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <circle cx="32" cy="32" r="22" fill="none" stroke="#FFFFFF" stroke-width="3.5"/>
  <line x1="10" y1="32" x2="54" y2="32" stroke="#FFFFFF" stroke-width="3"/>
  <ellipse cx="32" cy="32" rx="11" ry="22" fill="none" stroke="#FFFFFF" stroke-width="3"/>
</svg>''',

    "vyron-audio": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <polygon points="16,26 26,26 36,18 36,46 26,38 16,38" fill="#FFFFFF"/>
  <path d="M42 24 A10 10 0 0 1 42 40" fill="none" stroke="#FFFFFF" stroke-width="3.5" stroke-linecap="round"/>
  <path d="M48 18 A18 18 0 0 1 48 46" fill="none" stroke="#FFFFFF" stroke-width="3.5" stroke-linecap="round"/>
</svg>''',

    "vyron-display": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect x="12" y="16" width="40" height="26" rx="3" fill="none" stroke="#FFFFFF" stroke-width="3.5"/>
  <line x1="32" y1="42" x2="32" y2="50" stroke="#FFFFFF" stroke-width="3.5"/>
  <line x1="22" y1="50" x2="42" y2="50" stroke="#FFFFFF" stroke-width="3.5" stroke-linecap="round"/>
</svg>''',

    "vyron-search": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <circle cx="28" cy="28" r="14" fill="none" stroke="#FFFFFF" stroke-width="3.5"/>
  <line x1="39" y1="39" x2="52" y2="52" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round"/>
</svg>''',

    "vyron-notifications": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <path d="M32 16 A12 12 0 0 0 20 28 V38 L16 42 H48 L44 38 V28 A12 12 0 0 0 32 16 Z" fill="none" stroke="#FFFFFF" stroke-width="3.5"/>
  <path d="M28 46 A4 4 0 0 0 36 46" fill="none" stroke="#FFFFFF" stroke-width="3.5"/>
</svg>''',

    "vyron-usb": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <circle cx="32" cy="46" r="4" fill="#FFFFFF"/>
  <line x1="32" y1="42" x2="32" y2="22" stroke="#FFFFFF" stroke-width="3.5"/>
  <polygon points="32,16 26,24 38,24" fill="#FFFFFF"/>
</svg>''',

    "vyron-theme-dark": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <path d="M44 38 A18 18 0 1 1 26 20 A14 14 0 0 0 44 38 Z" fill="#8B5CF6"/>
</svg>''',

    "vyron-theme-light": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <circle cx="32" cy="32" r="12" fill="#F59E0B"/>
  <path d="M32 10 v4 M32 50 v4 M10 32 h4 M50 32 h4 M16 16 l3 3 M45 45 l3 3 M16 48 l3 -3 M45 19 l3 -3" stroke="#F59E0B" stroke-width="3.5" stroke-linecap="round"/>
</svg>'''
}

for name, svg_data in V2_SVGS.items():
    with open(os.path.join(ICONS_DIR, f"{name}.svg"), "w") as f:
        f.write(svg_data)

def rasterize_icons():
    sizes = [16, 22, 24, 32, 48, 64, 128]
    for sz in sizes:
        sz_dir = os.path.join(ICONS_DIR, f"{sz}x{sz}")
        os.makedirs(sz_dir, exist_ok=True)
        
        palette = {
            "vyron-logo": ((6, 182, 212), (124, 58, 237)),
            "vyron-browser": ((249, 115, 22), (139, 92, 246)),
            "vyron-code": ((2, 132, 199), (6, 182, 212)),
            "vyron-files": ((245, 158, 11), (217, 119, 6)),
            "vyron-folder": ((56, 189, 248), (2, 132, 199)),
            "vyron-home": ((139, 92, 246), (109, 40, 217)),
            "vyron-terminal": ((30, 41, 59), (15, 23, 42)),
            "vyron-system-monitor": ((99, 102, 241), (139, 92, 246)),
            "vyron-editor": ((16, 185, 129), (5, 150, 105)),
            "vyron-calc": ((139, 92, 246), (124, 58, 237)),
            "vyron-settings": ((71, 85, 105), (51, 65, 85)),
            "vyron-launcher": ((30, 27, 75), (15, 12, 42)),
            "vyron-trash": ((100, 116, 139), (71, 85, 105)),
            "vyron-power": ((239, 68, 68), (220, 38, 38)),
            "vyron-shutdown": ((220, 38, 38), (153, 27, 27)),
            "vyron-restart": ((245, 158, 11), (217, 119, 6)),
            "vyron-lock": ((100, 116, 139), (51, 65, 85)),
            "vyron-wifi": ((124, 58, 237), (124, 58, 237)),
            "vyron-ethernet": ((6, 182, 212), (6, 182, 212)),
            "vyron-network": ((56, 189, 248), (2, 132, 199)),
            "vyron-audio": ((139, 92, 246), (139, 92, 246)),
            "vyron-display": ((100, 116, 139), (71, 85, 105)),
            "vyron-search": ((14, 165, 233), (2, 132, 199)),
            "vyron-notifications": ((245, 158, 11), (217, 119, 6)),
            "vyron-usb": ((100, 116, 139), (71, 85, 105)),
            "vyron-theme-dark": ((139, 92, 246), (139, 92, 246)),
            "vyron-theme-light": ((245, 158, 11), (245, 158, 11)),
        }

        for name, (c1, c2) in palette.items():
            png_path = os.path.join(sz_dir, f"{name}.png")
            im = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
            draw = ImageDraw.Draw(im)
            
            rad = max(2, int(sz * 0.25))
            pad = max(1, int(sz * 0.06))
            
            draw.rounded_rectangle(
                [(pad, pad), (sz - pad - 1, sz - pad - 1)],
                radius=rad,
                fill=c1,
                outline=c2,
                width=max(1, int(sz * 0.04))
            )
            
            inner_pad = max(2, int(sz * 0.28))
            draw.rounded_rectangle(
                [(inner_pad, inner_pad), (sz - inner_pad - 1, sz - inner_pad - 1)],
                radius=max(1, rad // 2),
                fill=(255, 255, 255, 220)
            )
            im.save(png_path)

    print(f"Generated {len(V2_SVGS)} SVG icons and multi-size PNGs in {ICONS_DIR}")

if __name__ == "__main__":
    rasterize_icons()
