from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

for source in sorted(ASSETS.glob("banner-*.png")):
    target = source.with_suffix(".jpg")
    image = Image.open(source).convert("RGB")
    image.thumbnail((1600, 900), Image.Resampling.LANCZOS)
    image.save(target, format="JPEG", quality=84, optimize=True, progressive=True)
    print(f"wrote {target.name}: {image.width}x{image.height}")
