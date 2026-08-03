# -*- coding: utf-8 -*-
"""
Nhận diện ảnh chi tiêu bằng Gemini Vision (Google AI Studio).

Khác với model offline cũ (MobileNet-SSD / PASCAL VOC — chỉ có 20 lớp vật thể
chung chung, không có "đồ ăn" hay "hoá đơn"), Gemini là mô hình đa phương thức
hiểu được cả ảnh lẫn chữ trong ảnh cùng lúc — nên có thể:
  - Đọc chữ trên hoá đơn (số tiền, tên quán...)
  - Hiểu ngữ cảnh món ăn/địa điểm Việt Nam
  - Trả thẳng gợi ý tên khoản chi + số tiền + danh mục, không chỉ 1 nhãn vật thể

Dùng gọi HTTP trực tiếp (urllib có sẵn trong Python, không cần cài thêm thư
viện ngoài) để giảm rủi ro khi deploy.

An toàn khi lỗi: mọi lỗi (thiếu key, mất mạng, quá quota, JSON không hợp lệ...)
đều trả về None thay vì raise exception — nơi gọi sẽ tự động dùng lại model
offline cũ làm phương án dự phòng.
"""
import os
import json
import base64
import urllib.request
import urllib.error

from django.conf import settings

GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

# Ngưỡng tin cậy tối thiểu để tự động điền sẵn danh mục (giống tinh thần với
# model offline cũ — thà im lặng còn hơn tự chọn liều một danh mục sai).
AUTO_SUGGEST_CONFIDENCE = 0.55

_MIME_BY_EXT = {".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


def is_configured():
    return bool(getattr(settings, "GEMINI_API_KEY", ""))


def analyze_expense_image(image_path, category_names, timeout=20):
    """Gửi ảnh lên Gemini kèm danh sách danh mục thật của người dùng, nhận về
    gợi ý phân loại + đọc số tiền/tên khoản nếu có.

    Trả về None nếu chưa cấu hình GEMINI_API_KEY hoặc có lỗi bất kỳ khi gọi API
    — để nơi gọi tự chuyển sang dùng model offline dự phòng.
    """
    api_key = getattr(settings, "GEMINI_API_KEY", "")
    if not api_key or not category_names:
        return None

    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
    except OSError:
        return None

    ext = os.path.splitext(image_path)[1].lower()
    mime_type = _MIME_BY_EXT.get(ext, "image/jpeg")
    image_b64 = base64.b64encode(image_bytes).decode("ascii")

    category_list_str = ", ".join(category_names)
    prompt = (
        "Bạn là trợ lý phân loại chi tiêu cho một ứng dụng quản lý tài chính cá "
        "nhân của người Việt Nam. Hãy quan sát kỹ bức ảnh này — có thể là hoá "
        "đơn, món ăn, biên lai, sản phẩm mua sắm, phương tiện di chuyển, hoặc "
        "bất kỳ thứ gì liên quan tới một khoản chi tiêu — rồi trả lời DUY NHẤT "
        "một đối tượng JSON theo đúng cấu trúc sau, không kèm giải thích, không "
        "kèm dấu ```:\n"
        "{\n"
        '  "label": "<mô tả ngắn gọn nội dung ảnh bằng tiếng Việt>",\n'
        '  "category": "<chọn CHÍNH XÁC một tên trong danh sách này: '
        f'{category_list_str} — hoặc null nếu không đủ chắc chắn>",\n'
        '  "confidence": <số thực 0 đến 1 — mức độ tự tin của bạn về category>,\n'
        '  "suggested_title": "<tên khoản chi ngắn gọn, vd: \'Ăn trưa - Phở bò\'>",\n'
        '  "suggested_amount": <số tiền VNĐ đọc được trên hoá đơn nếu có, chỉ '
        "là số nguyên không có chữ hay dấu phân cách, hoặc null nếu không đọc "
        'được số tiền nào>\n'
        "}\n"
        "Nếu ảnh không rõ ràng hoặc không liên quan tới chi tiêu, hãy để "
        '"category": null và "confidence" thấp thay vì đoán liều.'
    )

    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": mime_type, "data": image_b64}},
            ]
        }],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.2,
        },
    }

    req = urllib.request.Request(
        f"{GEMINI_ENDPOINT}?key={api_key}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError):
        return None

    try:
        text = raw["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(text)
    except (KeyError, IndexError, ValueError, TypeError):
        return None

    try:
        confidence = max(0.0, min(1.0, float(result.get("confidence", 0) or 0)))
    except (TypeError, ValueError):
        confidence = 0.0

    category = result.get("category")
    if category not in category_names:
        category = None

    amount = result.get("suggested_amount")
    try:
        amount = float(amount) if amount not in (None, "", "null") else None
    except (TypeError, ValueError):
        amount = None
    if amount is not None and amount <= 0:
        amount = None

    return {
        "label": (result.get("label") or "").strip(),
        "category": category,
        "confidence": confidence,
        "suggested_title": (result.get("suggested_title") or "").strip(),
        "suggested_amount": amount,
        "auto_suggest": bool(category) and confidence >= AUTO_SUGGEST_CONFIDENCE,
        "source": "gemini",
    }
