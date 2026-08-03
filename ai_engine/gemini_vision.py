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

LƯU Ý QUAN TRỌNG VỀ VÒNG ĐỜI MODEL: Google khai tử model Gemini theo tên cụ
thể khá thường xuyên — hệ thống này đã 2 lần bị ảnh hưởng (gemini-2.0-flash
shutdown 01/06/2026, rồi gemini-2.5-flash cũng bị chặn với user mới) chỉ trong
vài tháng. Vì vậy thay vì hardcode một model duy nhất, danh sách GEMINI_MODELS
bên dưới liệt kê VÀI model theo thứ tự ưu tiên — hễ model nào báo lỗi 404 (
không tồn tại/không còn hỗ trợ), code tự động thử model kế tiếp trong danh
sách trước khi bỏ cuộc. Nếu tương lai TẤT CẢ model trong danh sách đều bị lỗi
404, vào https://ai.google.dev/gemini-api/docs/pricing xem model mới nhất
đang "Free with rate limits" và thêm vào đầu danh sách.
"""
import os
import json
import base64
import logging
import urllib.request
import urllib.error

from django.conf import settings

logger = logging.getLogger(__name__)

GEMINI_MODELS = [
    "gemini-3.6-flash",       # GA ổn định mới nhất (21/07/2026)
    "gemini-2.5-flash-lite",  # dự phòng — vẫn free tính đến 08/2026
    "gemini-3.5-flash-lite",  # dự phòng — vẫn free tính đến 08/2026
]
_ENDPOINT_TPL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# Ngưỡng tin cậy tối thiểu để tự động điền sẵn danh mục (giống tinh thần với
# model offline cũ — thà im lặng còn hơn tự chọn liều một danh mục sai).
AUTO_SUGGEST_CONFIDENCE = 0.55

_MIME_BY_EXT = {".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


def is_configured():
    return bool(getattr(settings, "GEMINI_API_KEY", ""))


def _call_gemini(model, api_key, payload, timeout):
    """Gọi 1 model cụ thể. Trả (raw_json, None) nếu thành công,
    hoặc (None, "retry") nếu nên thử model kế tiếp (404 - model không tồn
    tại/hết hỗ trợ), hoặc (None, "stop") nếu là lỗi khác không đáng thử lại
    (sai key, hết quota, mất mạng...)."""
    req = urllib.request.Request(
        f"{_ENDPOINT_TPL.format(model=model)}?key={api_key}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")[:500]
        logger.error("Gemini API (model=%s) lỗi HTTP %s: %s", model, e.code, body)
        return None, ("retry" if e.code == 404 else "stop")
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as e:
        logger.error("Gemini API (model=%s) lỗi kết nối/parse: %s", model, e)
        return None, "stop"


def analyze_expense_image(image_path, category_names, timeout=20):
    """Gửi ảnh lên Gemini kèm danh sách danh mục thật của người dùng, nhận về
    gợi ý phân loại + đọc số tiền/tên khoản nếu có.

    Trả về None nếu chưa cấu hình GEMINI_API_KEY hoặc mọi model đều lỗi — để
    nơi gọi tự chuyển sang dùng model offline dự phòng.
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
            "role": "user",
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

    raw = None
    for model in GEMINI_MODELS:
        raw, action = _call_gemini(model, api_key, payload, timeout)
        if raw is not None:
            break
        if action == "stop":
            return None
        # action == "retry" -> thử model kế tiếp trong danh sách
    else:
        logger.error("Tất cả model trong GEMINI_MODELS đều lỗi 404 — cần cập nhật danh sách model.")
        return None

    if not raw.get("candidates"):
        block_reason = raw.get("promptFeedback", {}).get("blockReason", "không rõ")
        logger.error("Gemini không trả về candidates nào (có thể bị chặn bởi bộ lọc an toàn) — blockReason=%s | raw=%s", block_reason, raw)
        return None

    try:
        text = raw["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(text)
    except (KeyError, IndexError, ValueError, TypeError) as e:
        logger.error("Gemini API trả về JSON không đúng cấu trúc mong đợi: %s | raw=%s", e, raw)
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
