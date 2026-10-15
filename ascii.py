"""One-off: convert avatar.png into ascii.txt (dark pixels -> dense chars, background masked out)."""
import sys
from PIL import Image, ImageOps, ImageFilter, ImageDraw
W, H = 50, 29                      # chars; monospace cells are ~2x taller than wide
RAMP = " .:-=+*#%@"
img = Image.open(sys.argv[1]).convert("L").crop((70, 10, 340, 330))
img = ImageOps.autocontrast(img, cutoff=2).filter(ImageFilter.SHARPEN)
mask = Image.new("L", img.size, 0)
ImageDraw.Draw(mask).ellipse((25, 0, img.size[0]-25, img.size[1]+60), fill=255)
img = Image.composite(img, Image.new("L", img.size, 255), mask.filter(ImageFilter.GaussianBlur(12)))
img = img.resize((W, H))
rows = []
for y in range(H):
    rows.append("".join(RAMP[(255 - img.getpixel((x, y))) * (len(RAMP) - 1) // 255] for x in range(W)).rstrip())
open(sys.argv[2], "w").write("\n".join(rows) + "\n")
print("\n".join(rows))
