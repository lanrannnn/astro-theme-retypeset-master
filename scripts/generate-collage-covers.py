from __future__ import annotations

import hashlib
import html
import math
import random
import re
from html.parser import HTMLParser
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE_HTML = ROOT / "dist" / "collections" / "forty-fifth-sunset" / "index.html"
OUTPUT_DIR = ROOT / "public" / "images" / "covers"
FONT_REGULAR = ROOT / "public" / "fonts" / "NotoSansSC-Regular.otf"

WIDTH = 600
HEIGHT = 900

PAPER_PALETTES = [
    ((235, 220, 184), (166, 66, 42), (42, 75, 85), (224, 164, 65)),
    ((225, 231, 225), (43, 83, 107), (173, 82, 57), (109, 145, 153)),
    ((228, 224, 190), (62, 102, 74), (148, 76, 54), (186, 170, 82)),
    ((231, 217, 197), (85, 66, 91), (190, 82, 62), (74, 104, 111)),
]

THEMES = {
    "rain": {
        "keywords": ("雨", "梅雨"),
        "palette": ((220, 226, 217), (45, 70, 75), (94, 126, 123), (177, 190, 169)),
    },
    "night": {
        "keywords": ("夜", "多梦", "梦"),
        "palette": ((218, 215, 202), (42, 45, 61), (88, 82, 105), (168, 158, 118)),
    },
    "flower": {
        "keywords": ("花", "海棠", "百合"),
        "palette": ((232, 222, 200), (74, 83, 63), (165, 98, 86), (200, 168, 112)),
    },
    "summer": {
        "keywords": ("夏", "流感", "运动会"),
        "palette": ((229, 218, 178), (55, 89, 76), (198, 112, 64), (218, 171, 71)),
    },
    "music": {
        "keywords": ("歌曲", "吉他", "夜来香", "语言"),
        "palette": ((226, 218, 200), (48, 48, 50), (75, 107, 115), (178, 72, 57)),
    },
    "journey": {
        "keywords": ("车窗", "阶梯", "错步", "散步", "转动", "延伸"),
        "palette": ((224, 225, 209), (48, 73, 69), (176, 119, 62), (107, 130, 135)),
    },
    "childhood": {
        "keywords": ("孩子", "幼稚", "朋友"),
        "palette": ((236, 223, 190), (76, 83, 70), (193, 106, 73), (116, 147, 129)),
    },
    "thought": {
        "keywords": ("查拉斯图特拉斯", "电路", "摘抄", "作文", "文字", "哑", "杂谈", "日记"),
        "palette": ((226, 221, 204), (50, 58, 61), (117, 105, 83), (151, 124, 76)),
    },
}


def theme_for(title: str) -> tuple[str, dict[str, object]]:
    for name, theme in THEMES.items():
        if any(keyword in title for keyword in theme["keywords"]):
            return name, theme
    return "memory", {
        "keywords": (),
        "palette": ((231, 217, 197), (85, 66, 91), (190, 82, 62), (74, 104, 111)),
    }


def draw_theme_motif(
    canvas: Image.Image,
    rng: random.Random,
    theme_name: str,
    ink: tuple[int, int, int],
    accent: tuple[int, int, int],
) -> None:
    draw = ImageDraw.Draw(canvas, "RGBA")
    if theme_name == "rain":
        for x in range(70, 555, 34):
            y = rng.randint(130, 610)
            draw.line((x, y, x - 24, y + rng.randint(90, 190)), fill=(*ink, 50), width=2)
        for radius in (24, 43, 67):
            draw.ellipse((372 - radius, 600 - radius // 3, 372 + radius, 600 + radius // 3), outline=(*accent, 58), width=2)
    elif theme_name == "night":
        draw.ellipse((390, 110, 500, 220), fill=(*accent, 70), outline=(*ink, 80), width=2)
        draw.ellipse((420, 90, 515, 205), fill=(0, 0, 0, 0), outline=(*ink, 28), width=1)
        for _ in range(18):
            x, y = rng.randint(75, 530), rng.randint(120, 690)
            draw.ellipse((x, y, x + 2, y + 2), fill=(*ink, rng.randint(35, 90)))
    elif theme_name == "flower":
        cx, cy = rng.randint(350, 455), rng.randint(205, 350)
        for angle in range(0, 360, 60):
            dx = int(math.cos(math.radians(angle)) * 38)
            dy = int(math.sin(math.radians(angle)) * 38)
            draw.ellipse((cx + dx - 25, cy + dy - 13, cx + dx + 25, cy + dy + 13), outline=(*accent, 90), width=3)
        draw.line((cx, cy + 25, cx - 40, cy + 230), fill=(*ink, 70), width=2)
    elif theme_name == "summer":
        draw.ellipse((390, 110, 505, 225), fill=(*accent, 120))
        for y in range(480, 690, 18):
            draw.line((70, y, rng.randint(260, 530), y - rng.randint(0, 24)), fill=(*ink, 34), width=1)
    elif theme_name == "music":
        for radius in range(28, 112, 17):
            draw.ellipse((420 - radius, 270 - radius, 420 + radius, 270 + radius), outline=(*ink, 50), width=2)
        draw.line((75, 620, 510, 455), fill=(*accent, 85), width=3)
        for offset in range(0, 36, 9):
            draw.line((90, 640 + offset, 515, 478 + offset), fill=(*ink, 35), width=1)
    elif theme_name == "journey":
        for step in range(6):
            left = 90 + step * 45
            top = 620 - step * 55
            draw.line((left, top, left + 130, top), fill=(*ink, 55), width=2)
            draw.line((left + 130, top, left + 130, top - 48), fill=(*accent, 50), width=2)
        draw.line((65, 690, 520, 175), fill=(*ink, 35), width=1)
    elif theme_name == "childhood":
        for x, y, radius in ((118, 520, 42), (205, 440, 25), (300, 350, 16), (385, 270, 9)):
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline=(*accent, 72), width=2)
        draw.line((84, 680, 475, 170), fill=(*ink, 32), width=1)
    elif theme_name == "thought":
        for row in range(8):
            y = 180 + row * 54
            draw.line((75, y, rng.randint(300, 520), y), fill=(*ink, 38), width=1)
        draw.rectangle((360, 250, 490, 390), outline=(*accent, 65), width=2)
        draw.line((330, 430, 520, 210), fill=(*ink, 40), width=2)
    else:
        for radius in range(24, 135, 22):
            draw.arc((300 - radius, 330 - radius // 2, 300 + radius, 330 + radius // 2), 12, 330, fill=(*ink, 42), width=2)


class ShelfParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.current_id: str | None = None
        self.in_title = False
        self.title_parts: list[str] = []
        self.posts: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        classes = set((values.get("class") or "").split())
        if tag == "a" and "shelf-book" in classes:
            match = re.search(r"/posts/([^/]+)/", values.get("href") or "")
            self.current_id = match.group(1) if match else None
            self.title_parts = []
        elif tag == "span" and self.current_id and "archive-title" in classes:
            self.in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "span" and self.in_title:
            self.in_title = False
        elif tag == "a" and self.current_id:
            title = html.unescape("".join(self.title_parts)).strip()
            if title:
                self.posts.append((self.current_id, title))
            self.current_id = None
            self.title_parts = []

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)


def torn_polygon(rng: random.Random, box: tuple[int, int, int, int], step: int = 18) -> list[tuple[int, int]]:
    left, top, right, bottom = box
    points: list[tuple[int, int]] = []
    for x in range(left, right, step):
        points.append((x, top + rng.randint(-7, 7)))
    for y in range(top, bottom, step):
        points.append((right + rng.randint(-7, 7), y))
    for x in range(right, left, -step):
        points.append((x, bottom + rng.randint(-7, 7)))
    for y in range(bottom, top, -step):
        points.append((left + rng.randint(-7, 7), y))
    return points


def add_paper_texture(image: Image.Image, rng: random.Random, strength: float = 0.18) -> None:
    noise = Image.effect_noise(image.size, rng.uniform(8, 18)).convert("L")
    fibers = Image.new("L", image.size, 128)
    draw = ImageDraw.Draw(fibers)
    for _ in range(500):
        x = rng.randrange(image.width)
        y = rng.randrange(image.height)
        length = rng.randrange(2, 16)
        shade = rng.randrange(95, 165)
        draw.line((x, y, x + length, y + rng.choice((-1, 0, 1))), fill=shade, width=1)
    texture = ImageChops.multiply(noise, fibers).filter(ImageFilter.GaussianBlur(0.25))
    texture_rgb = Image.merge("RGB", (texture, texture, texture))
    image.paste(Image.blend(image.convert("RGB"), texture_rgb, strength))


def paste_torn_layer(
    canvas: Image.Image,
    rng: random.Random,
    box: tuple[int, int, int, int],
    color: tuple[int, int, int],
    texture: bool = True,
    alpha: int = 255,
) -> None:
    polygon = torn_polygon(rng, box)
    mask = Image.new("L", canvas.size, 0)
    ImageDraw.Draw(mask).polygon(polygon, fill=alpha)
    shadow = mask.filter(ImageFilter.GaussianBlur(8))
    shadow_layer = Image.new("RGBA", canvas.size, (44, 27, 18, 0))
    shadow_layer.putalpha(shadow.point(lambda p: int(p * 0.26)))
    canvas.alpha_composite(shadow_layer, (7, 9))
    layer = Image.new("RGBA", canvas.size, (*color, 255))
    if texture:
        local_noise = Image.effect_noise(canvas.size, rng.uniform(10, 24)).convert("L")
        tint = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
        tint.putalpha(local_noise.point(lambda p: max(0, min(35, p // 7))))
        layer = Image.alpha_composite(layer, tint)
    layer.putalpha(mask)
    canvas.alpha_composite(layer)


def make_photo_fragment(rng: random.Random, size: tuple[int, int], dark: tuple[int, int, int]) -> Image.Image:
    w, h = size
    base = Image.effect_noise((w, h), rng.uniform(22, 38)).convert("L")
    base = ImageEnhance.Contrast(base).enhance(1.6).filter(ImageFilter.GaussianBlur(1.1))
    photo = Image.merge("RGB", (
        base.point(lambda p: int(p * dark[0] / 255)),
        base.point(lambda p: int(p * dark[1] / 255)),
        base.point(lambda p: int(p * dark[2] / 255)),
    )).convert("RGBA")
    draw = ImageDraw.Draw(photo, "RGBA")
    horizon = rng.randint(h // 3, h * 2 // 3)
    draw.rectangle((0, horizon, w, h), fill=(17, 25, 28, 42))
    cx = rng.randint(w // 4, w * 3 // 4)
    cy = rng.randint(h // 4, h * 3 // 4)
    draw.ellipse((cx - w // 5, cy - h // 7, cx + w // 5, cy + h // 7), outline=(245, 235, 210, 34), width=2)
    return photo


def paste_photo(canvas: Image.Image, rng: random.Random, box: tuple[int, int, int, int], dark: tuple[int, int, int]) -> None:
    left, top, right, bottom = box
    photo = make_photo_fragment(rng, (right - left, bottom - top), dark)
    local_mask = Image.new("L", photo.size, 0)
    shifted = torn_polygon(rng, (5, 5, photo.width - 5, photo.height - 5), 14)
    ImageDraw.Draw(local_mask).polygon(shifted, fill=245)
    photo.putalpha(local_mask)
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_mask = Image.new("L", canvas.size, 0)
    ImageDraw.Draw(shadow_mask).polygon([(x + left, y + top) for x, y in shifted], fill=75)
    shadow.putalpha(shadow_mask.filter(ImageFilter.GaussianBlur(7)))
    canvas.alpha_composite(shadow, (6, 8))
    canvas.alpha_composite(photo, (left, top))


def draw_tape(canvas: Image.Image, rng: random.Random, center: tuple[int, int], angle: float) -> None:
    tape = Image.new("RGBA", (150, 42), (220, 199, 150, 135))
    tape_draw = ImageDraw.Draw(tape, "RGBA")
    for x in range(6, 146, 8):
        tape_draw.line((x, 2, x + rng.randint(-2, 2), 40), fill=(255, 248, 213, 25), width=1)
    tape = tape.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    canvas.alpha_composite(tape, (center[0] - tape.width // 2, center[1] - tape.height // 2))


def draw_microtext(canvas: Image.Image, rng: random.Random, post_id: str, title: str, ink: tuple[int, int, int]) -> None:
    draw = ImageDraw.Draw(canvas, "RGBA")
    font_small = ImageFont.truetype(str(FONT_REGULAR), 13)
    font_tiny = ImageFont.truetype(str(FONT_REGULAR), 10)
    draw.text((42, 42), f"ARCHIVE / {post_id}", font=font_small, fill=(*ink, 175))
    draw.text((42, 64), "FIELD NOTES  ·  LANRAN", font=font_tiny, fill=(*ink, 120))
    for row in range(4):
        y = 764 + row * 20
        width = rng.randint(90, 270)
        draw.line((46, y, 46 + width, y), fill=(*ink, 70), width=1)
    digest = hashlib.sha1(title.encode("utf-8")).hexdigest()[:8].upper()
    draw.text((430, 840), digest, font=font_tiny, fill=(*ink, 125))


def generate_cover(post_id: str, title: str, index: int) -> Path:
    seed = int(hashlib.sha256(f"{post_id}:{title}".encode("utf-8")).hexdigest()[:16], 16)
    rng = random.Random(seed)
    theme_name, theme = theme_for(title)
    paper, ink, secondary, accent = theme["palette"]
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (*paper, 255))
    add_paper_texture(canvas, rng, 0.11)

    # One small, tactile cluster on a mostly empty sheet. The page title is
    # rendered by the site, so the bitmap stays a quiet cover image.
    layouts = [
        ((84, 238, 322, 508), (302, 405, 358, 652)),
        ((275, 172, 512, 442), (132, 340, 188, 588)),
        ((92, 360, 330, 630), (342, 224, 398, 472)),
        ((245, 258, 483, 528), (112, 178, 168, 426)),
    ]
    photo_box, strip_box = layouts[index % len(layouts)]
    paste_photo(canvas, rng, photo_box, ink)
    paste_torn_layer(
        canvas,
        rng,
        strip_box,
        accent,
        alpha=245,
    )

    draw = ImageDraw.Draw(canvas, "RGBA")
    font_small = ImageFont.truetype(str(FONT_REGULAR), 13)
    draw.text((42, 42), f"ARCHIVE / {post_id}", font=font_small, fill=(*ink, 145))
    draw.line((42, 66, 148, 66), fill=(*ink, 90), width=1)
    canvas = canvas.convert("RGB")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = OUTPUT_DIR / f"{post_id}.webp"
    canvas.save(output, "WEBP", quality=84, method=6)
    return output


def main() -> None:
    if not SOURCE_HTML.exists():
        raise SystemExit(f"Build the site first; missing {SOURCE_HTML}")
    parser = ShelfParser()
    parser.feed(SOURCE_HTML.read_text(encoding="utf-8"))
    if not parser.posts:
        raise SystemExit("No shelf books found in the built collection page")
    for index, (post_id, title) in enumerate(parser.posts):
        output = generate_cover(post_id, title, index)
        print(f"{index + 1:02d}/{len(parser.posts):02d} {post_id} {title} -> {output.name}")


if __name__ == "__main__":
    main()
