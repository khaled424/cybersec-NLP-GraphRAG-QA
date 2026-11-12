"""Render the Vigie logo variants of ``logo.html`` to high-resolution PNG files (media/brand/).

    python media/brand/render_logo.py
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
VARIANTS = {  # name: (variant, css width, css height, scale, transparent)
    "vigie_logo.png": ("lockup", 1900, 640, 2, True),          # 3800 × 1280, transparent
    "vigie_logo_dark.png": ("lockup-dark", 1900, 640, 2, False),  # 3800 × 1280, on #0C111C
    "vigie_icon.png": ("icon", 1024, 1024, 1, True),          # 1024 × 1024 app icon
    "vigie_mark.png": ("mark", 1024, 1024, 2, True),          # 2048 × 2048 mark only, transparent
}

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--force-color-profile=srgb"])
    for filename, (variant, width, height, scale, transparent) in VARIANTS.items():
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=scale)
        page.goto(f"{(HERE / 'logo.html').as_uri()}?v={variant}")
        page.evaluate("document.fonts.ready")
        page.screenshot(path=str(HERE / filename), omit_background=transparent,
                        clip={"x": 0, "y": 0, "width": width, "height": height})
        page.close()
        print(HERE / filename)
    browser.close()
