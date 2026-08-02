# -*- coding: utf-8 -*-
"""Ghi đè số tiền + ngày lên góc dưới ảnh chi tiêu bằng Pillow."""
import os
from PIL import Image, ImageDraw, ImageFont


def _load_font(size):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def annotate_expense_image(input_path, output_path, amount_text, date_text):
    """Mở ảnh gốc, vẽ một dải nền mờ ở góc dưới và ghi số tiền + ngày lên đó,
    lưu thành ảnh mới (không ghi đè ảnh gốc)."""
    img = Image.open(input_path).convert("RGB")
    w, h = img.size

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    band_height = max(int(h * 0.14), 64)
    draw.rectangle([0, h - band_height, w, h], fill=(10, 14, 25, 190))

    font_size = max(int(band_height * 0.34), 16)
    font_amount = _load_font(font_size)
    font_date = _load_font(int(font_size * 0.62))

    padding = int(band_height * 0.18)
    draw.text((padding, h - band_height + padding), amount_text,
              font=font_amount, fill=(255, 255, 255, 255))
    draw.text((padding, h - band_height + padding + font_size + 4), date_text,
              font=font_date, fill=(203, 213, 225, 255))

    combined = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    combined.save(output_path, quality=90)
    return output_path
