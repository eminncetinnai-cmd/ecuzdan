"""
Generate Apple Touch Icons and PWA PNG Icons for E-Cuzdan.
Uses headless Microsoft Edge to rasterize SVG at 1024x1024,
then uses Pillow with Lanczos resampling to produce crisp icons.
"""

import os
import subprocess
import sys
from PIL import Image

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(REPO_ROOT, "static")
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# 1024x1024 Master Icon SVG with Full Bleed Background and Safe Area Emblem
MASTER_ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" width="1024" height="1024">
  <defs>
    <!-- Background Gradient: Obsidian & Royal Indigo -->
    <linearGradient id="bg-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1e1b4b" />
      <stop offset="45%" stop-color="#0f172a" />
      <stop offset="100%" stop-color="#020617" />
    </linearGradient>

    <!-- Radial Ambient Glow -->
    <radialGradient id="halo-glow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#4f46e5" stop-opacity="0.35" />
      <stop offset="70%" stop-color="#38bdf8" stop-opacity="0.1" />
      <stop offset="100%" stop-color="#020617" stop-opacity="0" />
    </radialGradient>

    <!-- Top Wing Gradient (Growth & Alpha) -->
    <linearGradient id="top-wing-grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#06b6d4" />
      <stop offset="45%" stop-color="#3b82f6" />
      <stop offset="100%" stop-color="#6366f1" />
    </linearGradient>

    <!-- 24K Gold Clasp & Reserve Core Gradient -->
    <linearGradient id="gold-core-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#fffbeb" />
      <stop offset="25%" stop-color="#fcd34d" />
      <stop offset="65%" stop-color="#f59e0b" />
      <stop offset="100%" stop-color="#b45309" />
    </linearGradient>

    <!-- Bottom Wing Gradient (Ledger Balance) -->
    <linearGradient id="bottom-wing-grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#34d399" />
      <stop offset="55%" stop-color="#10b981" />
      <stop offset="100%" stop-color="#047857" />
    </linearGradient>

    <!-- Titanium Spine Pillar Gradient -->
    <linearGradient id="spine-grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#ffffff" />
      <stop offset="40%" stop-color="#f8fafc" />
      <stop offset="75%" stop-color="#e2e8f0" />
      <stop offset="100%" stop-color="#94a3b8" />
    </linearGradient>

    <!-- Subtle Rim Light Gradient -->
    <linearGradient id="rim-light" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#818cf8" stop-opacity="0.6" />
      <stop offset="40%" stop-color="#38bdf8" stop-opacity="0.3" />
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0.05" />
    </linearGradient>

    <!-- Wallet Silhouette Ribbon -->
    <linearGradient id="wallet-ribbon" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#6366f1" stop-opacity="0.4" />
      <stop offset="50%" stop-color="#38bdf8" stop-opacity="0.2" />
      <stop offset="100%" stop-color="#10b981" stop-opacity="0.05" />
    </linearGradient>

    <!-- Drop Shadow for Sovereign Emblem -->
    <filter id="emblem-shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="24" stdDeviation="32" flood-color="#010409" flood-opacity="0.9" />
    </filter>
  </defs>

  <!-- Full-bleed background for Apple squircle / adaptive canvas -->
  <rect width="1024" height="1024" fill="url(#bg-grad)" />
  <rect width="1024" height="1024" fill="url(#halo-glow)" />

  <!-- Inner Master Squircle Container (Scaled & Centered in safe zone) -->
  <!-- Center: 512, 512. Width: 760, Height: 760 (132 to 892) -->
  <rect x="132" y="132" width="760" height="760" rx="196" fill="#0f172a" fill-opacity="0.5" stroke="url(#rim-light)" stroke-width="6" />

  <!-- Emblem Group transformed to center (scale factor: 6.8x, original center ~64,64) -->
  <!-- Original coords: x: 31..98 (width 67), y: 28..100 (height 72). Center: (64.5, 64) -->
  <!-- Scaled by 6.8: width ~455, height ~490. Centered at 512, 512 -> translation: (512 - 64.5*6.8 = 73.4, 512 - 64*6.8 = 76.8) -->
  <g transform="translate(73, 77) scale(6.8)" filter="url(#emblem-shadow)">
    
    <!-- Outer Wallet Perimeter Arc (Isometric Flow) -->
    <path d="M 46 28 C 76 28 98 42 98 64 C 98 86 76 100 46 100" 
          fill="none" stroke="url(#wallet-ribbon)" stroke-width="3.5" stroke-linecap="round" />

    <!-- 1. TOP WING: ASCENDING FINANCIAL GROWTH VECTOR -->
    <path d="M 44 28 
             L 80 28 
             C 83.5 28 86.5 29.5 88.5 32 
             L 94 39
             C 95.5 41 94.5 44 92 44 
             L 44 44 
             Z" 
          fill="url(#top-wing-grad)" />
    <!-- Vector Specular Edge -->
    <path d="M 45 29.5 L 79.5 29.5 C 82 29.5 84.5 30.8 86 32.8 L 91.5 39.5" fill="none" stroke="rgba(255,255,255,0.7)" stroke-width="1.2" stroke-linecap="round" />

    <!-- 2. BOTTOM WING: GENERAL LEDGER FOUNDATION -->
    <path d="M 44 84 
             L 80 84 
             C 84 84 87 86 89 89 
             L 94 95
             C 95 96.5 94 99 92 100 
             L 44 100 
             Z" 
          fill="url(#bottom-wing-grad)" />
    <!-- Ledger Specular Edge -->
    <path d="M 45 85.5 L 79.5 85.5 C 82.5 85.5 85 87 86.5 89.5 L 91 95" fill="none" stroke="rgba(255,255,255,0.5)" stroke-width="1.2" stroke-linecap="round" />

    <!-- 3. CENTRAL CLASP: 24K GOLD VAULT LOCK -->
    <path d="M 44 58 
             L 64 58 
             L 70 54 
             L 80 54 
             L 86 64 
             L 80 74 
             L 70 74 
             L 64 70 
             L 44 70 
             Z" 
          fill="url(#gold-core-grad)" />
    <!-- Faceted Diamond Bevel in Clasp -->
    <polygon points="75,57 82,64 75,71 68,64" fill="#fffbeb" opacity="0.9" />
    <circle cx="75" cy="64" r="2.5" fill="#78350f" />

    <!-- 4. TITANIUM MASTER SPINE: THE VAULT PILLAR -->
    <path d="M 37 28 
             L 46 28 
             L 46 100 
             L 37 100 
             C 33.7 100 31 97.3 31 94 
             L 31 34 
             C 31 30.7 33.7 28 37 28 
             Z" 
          fill="url(#spine-grad)" />

    <!-- Spine Polished Bevel Lines -->
    <line x1="33" y1="33" x2="33" y2="95" stroke="#ffffff" stroke-width="1.4" stroke-linecap="round" opacity="0.95" />
    <line x1="44.5" y1="29" x2="44.5" y2="99" stroke="#94a3b8" stroke-width="1" opacity="0.6" />

    <!-- Quantum Ledger Triple Micro-Nodes -->
    <circle cx="34" cy="36" r="1.6" fill="#38bdf8" />
    <circle cx="34" cy="64" r="1.6" fill="#f59e0b" />
    <circle cx="34" cy="92" r="1.6" fill="#10b981" />
  </g>
</svg>
"""

def generate_icons():
    temp_html = os.path.join(STATIC_DIR, "icon_render_temp.html")
    temp_master_png = os.path.join(STATIC_DIR, "master_icon_1024.png")

    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  html, body {{
    margin: 0;
    padding: 0;
    width: 1024px;
    height: 1024px;
    overflow: hidden;
    background: transparent;
  }}
  svg {{
    display: block;
    width: 1024px;
    height: 1024px;
  }}
</style>
</head>
<body>
{MASTER_ICON_SVG}
</body>
</html>"""

    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    print("Rasterizing SVG to 1024x1024 PNG with Headless Edge...")
    cmd = [
        EDGE_PATH,
        "--headless",
        "--disable-gpu",
        "--hide-scrollbars",
        "--window-size=1024,1024",
        f"--screenshot={temp_master_png}",
        temp_html
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0 or not os.path.exists(temp_master_png):
        print(f"Edge rasterization failed: {res.stderr}")
        return False

    print("Master 1024x1024 PNG rendered successfully.")

    master_img = Image.open(temp_master_png).convert("RGBA")
    # Crop to exactly 1024x1024 in case viewport included decoration
    master_img = master_img.crop((0, 0, 1024, 1024))

    targets = {
        # Apple iOS Touch Icons
        "apple-touch-icon.png": 180,
        "apple-touch-icon-180x180.png": 180,
        "apple-touch-icon-167x167.png": 167,
        "apple-touch-icon-152x152.png": 152,
        "apple-touch-icon-120x120.png": 120,
        # PWA & Android Icons
        "pwa-icon-192.png": 192,
        "pwa-icon-512.png": 512,
        "pwa-icon-maskable.png": 512,
        # Favicon png
        "favicon-32x32.png": 32,
    }

    for filename, size in targets.items():
        out_path = os.path.join(STATIC_DIR, filename)
        resized = master_img.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(out_path, format="PNG", optimize=True)
        print(f"  Generated: {filename} ({size}x{size})")

    # Clean up temp files
    if os.path.exists(temp_html):
        os.remove(temp_html)
    if os.path.exists(temp_master_png):
        os.remove(temp_master_png)
    test_png = os.path.join(STATIC_DIR, "test_icon.png")
    if os.path.exists(test_png):
        os.remove(test_png)

    print("All PWA & Apple Touch Icons successfully generated!")
    return True

if __name__ == "__main__":
    if not generate_icons():
        sys.exit(1)
