"""Regenerate every raster brand asset (favicons, PWA icons, loading spinners) from scholrithm-mark.svg.

Run from the repo root: python3 branding/generate-assets.py
Needs Pillow and macOS (`sips` rasterizes the SVG).
"""

import math
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SVG = ROOT / "branding" / "scholrithm-mark.svg"
APPS = ("web", "admin", "space")


def render_mark() -> Image.Image:
    """Rasterize the SVG at 8x and crop to its visible bounds."""
    with tempfile.TemporaryDirectory() as tmp:
        big, png = Path(tmp) / "mark.svg", Path(tmp) / "mark.png"
        big.write_text(SVG.read_text().replace('width="186" height="234"', 'width="1488" height="1872"'))
        subprocess.run(["sips", "-s", "format", "png", str(big), "--out", str(png)], check=True, capture_output=True)
        img = Image.open(png).convert("RGBA")
        img.load()
    return img.crop(img.getbbox())


MARK = render_mark()


def fit(height: int) -> Image.Image:
    return MARK.resize((round(MARK.width * height / MARK.height), height), Image.LANCZOS)


def icon(size: int, fill: float, background=None) -> Image.Image:
    """Square icon with the mark centred at `fill` of the height; transparent unless `background` is set."""
    img = Image.new("RGBA", (size, size), background or (0, 0, 0, 0))
    mark = fit(round(size * fill))
    img.alpha_composite(mark, ((size - mark.width) // 2, (size - mark.height) // 2))
    return img


WHITE = (255, 255, 255, 255)


def save(img: Image.Image, path: Path, **kw):
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, **kw)


def spinner(dark: bool) -> list[Image.Image]:
    """Breathing-pulse frames, transparent background. Dark variant is lightened for contrast."""
    frames, w, h, n = [], 248, 312, 48
    for i in range(n):
        scale = 0.86 + 0.14 * (0.5 - 0.5 * math.cos(2 * math.pi * i / n))
        mark = fit(round(h * scale))
        if dark:
            alpha = mark.getchannel("A")
            mark = Image.blend(mark.convert("RGB"), Image.new("RGB", mark.size, WHITE[:3]), 0.3).convert("RGBA")
            mark.putalpha(alpha)
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        canvas.alpha_composite(mark, ((w - mark.width) // 2, (h - mark.height) // 2))
        # GIF only has 1-bit transparency: quantize colour, then punch out the transparent pixels.
        alpha = canvas.getchannel("A").point(lambda a: 255 if a >= 128 else 0)
        pal = canvas.convert("RGB").quantize(colors=255)
        pal.paste(255, mask=alpha.point(lambda a: 255 - a))
        pal.info["transparency"] = 255
        frames.append(pal)
    return frames


def main():
    for app in APPS:
        assets = ROOT / "apps" / app / "app" / "assets"
        save(icon(16, 0.96), assets / "favicon" / "favicon-16x16.png")
        save(icon(32, 0.96), assets / "favicon" / "favicon-32x32.png")
        save(icon(48, 0.96), assets / "favicon" / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
        save(icon(180, 0.66, WHITE), assets / "favicon" / "apple-touch-icon.png")
        pub = ROOT / "apps" / app / "public" / "favicon"
        save(icon(192, 0.60, WHITE), pub / "android-chrome-192x192.png")
        save(icon(512, 0.60, WHITE), pub / "android-chrome-512x512.png")
        for dark in (False, True):
            frames = spinner(dark)
            name = f"logo-spinner-{'dark' if dark else 'light'}.gif"
            save(
                frames[0], assets / "images" / name,
                save_all=True, append_images=frames[1:], duration=40, loop=0, disposal=2, transparency=255,
            )
    for size in (192, 348, 512):
        save(icon(size, 0.60, WHITE), ROOT / "apps" / "web" / "public" / "icons" / f"icon-{size}x{size}.png")


if __name__ == "__main__":
    main()
