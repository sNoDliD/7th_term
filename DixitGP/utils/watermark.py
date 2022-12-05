from pathlib import Path

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

local_path = Path(__file__).parent.resolve()

def get_circle_mark(text, size):
    mark = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(mark)
    draw.ellipse((0, 0, size, size), fill=(255, 255, 255, 55))
    font = ImageFont.truetype(str(local_path / "ArianaVioleta-dz2K.ttf"), int(size * 1.35))
    text_x, text_y, text_w, text_h = draw.multiline_textbbox((0, 0), text, font)
    draw.text(((size - text_w - text_x) // 2, (size - text_h - text_y) // 2), text, (0, 0, 0, 100), font=font)
    return mark


def get_marked_image(original, text):
    text = str(text)
    if original.mode != "RGBA":
        img = Image.new("RGBA", original.size, (0, 0, 0, 0))
        img.paste(original)
        original = img
    full_mark = Image.new("RGBA", original.size, (0, 0, 0, 0))
    mark = get_circle_mark(text, int(min(original.size) * 0.30))
    offset = int(min(original.size) * 0.05)
    full_mark.paste(mark, (offset, offset))
    return Image.alpha_composite(original, full_mark).convert("RGB")


# image = Image.open("../photos/AQADrL8xGwOnyUt-")
# get_marked_image(image, "10").show()
