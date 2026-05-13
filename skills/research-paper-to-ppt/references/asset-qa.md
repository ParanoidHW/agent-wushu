# Asset Extraction and QA Reference

## Trim White Margins

Use this after converting paper figure PDFs to PNG. It preserves aspect ratio and only removes blank margins.

```python
from PIL import Image, ImageChops
from pathlib import Path

src = Path("deep_research_<slug>/assets/paper_figures")
out = Path("deep_research_<slug>/assets/paper_figures_trimmed")
out.mkdir(parents=True, exist_ok=True)

for p in src.glob("*.png"):
    im = Image.open(p).convert("RGB")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    bbox = ImageChops.difference(im, bg).getbbox()
    if bbox:
        pad = 24
        l = max(0, bbox[0] - pad)
        t = max(0, bbox[1] - pad)
        r = min(im.size[0], bbox[2] + pad)
        b = min(im.size[1], bbox[3] + pad)
        im = im.crop((l, t, r, b))
    im.save(out / p.name)
```

## Aspect-Ratio Fit for PptxGenJS

Do not rely on PowerPoint or LibreOffice to preserve aspect ratio. Compute it before insertion.

```javascript
const sizeOf = require("image-size");

function addFitImage(slide, imgPath, x, y, w, h) {
  const dim = sizeOf(imgPath);
  const boxRatio = w / h;
  const imgRatio = dim.width / dim.height;
  let iw = w, ih = h, ix = x, iy = y;

  if (imgRatio > boxRatio) {
    ih = w / imgRatio;
    iy = y + (h - ih) / 2;
  } else {
    iw = h * imgRatio;
    ix = x + (w - iw) / 2;
  }

  slide.addImage({ path: imgPath, x: ix, y: iy, w: iw, h: ih });
}
```

Use the same function for SVG formulas and extracted PNG figures.

## LibreOffice Conversion Notes

In WSL or sandboxed environments, run LibreOffice with a writable profile:

```bash
mkdir -p /tmp/codex-lo-out /tmp/codex-lo-home /tmp/codex-lo-cache /tmp/codex-lo-profile
HOME=/tmp/codex-lo-home XDG_CACHE_HOME=/tmp/codex-lo-cache \
libreoffice --headless --nologo \
  -env:UserInstallation=file:///tmp/codex-lo-profile \
  --convert-to pdf --outdir /tmp/codex-lo-out deck.pptx
```

Then render images:

```bash
pdftoppm -jpeg -r 150 /tmp/codex-lo-out/deck.pdf qa_render/slide
```

## Contact Sheet

```python
from PIL import Image, ImageDraw
from pathlib import Path

imgs = []
for p in sorted(Path("qa_render").glob("slide-*.jpg")):
    img = Image.open(p).convert("RGB")
    img.thumbnail((480, 270))
    canvas = Image.new("RGB", (500, 310), "white")
    canvas.paste(img, (10, 10))
    ImageDraw.Draw(canvas).text((10, 285), p.stem, fill=(0, 0, 0))
    imgs.append(canvas)

rows = (len(imgs) + 1) // 2
out = Image.new("RGB", (1000, rows * 310), "white")
for idx, img in enumerate(imgs):
    out.paste(img, ((idx % 2) * 500, (idx // 2) * 310))
out.save("qa_render/contact_sheet.jpg", quality=92)
```
