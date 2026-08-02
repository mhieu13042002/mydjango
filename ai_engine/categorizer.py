# -*- coding: utf-8 -*-
"""Gợi ý danh mục chi tiêu từ mô tả text, dùng bộ từ khóa tiếng Việt.
Không phụ thuộc dịch vụ ngoài, chạy tức thời."""

KEYWORD_MAP = {
    "Ăn uống": ["ăn", "cơm", "trà sữa", "cafe", "cà phê", "quán", "nhà hàng",
                "ăn sáng", "ăn trưa", "ăn tối", "siêu thị", "chợ", "bún", "phở",
                "trà", "food", "milktea", "gọi món", "đồ ăn", "buffet"],
    "Di chuyển": ["xăng", "grab", "taxi", "xe bus", "vé xe", "gửi xe", "uber",
                  "đổ xăng", "sửa xe", "bến xe", "vé máy bay", "gojek", "xe ôm"],
    "Nhà ở": ["tiền nhà", "thuê nhà", "phòng trọ", "chung cư", "sửa nhà"],
    "Hóa đơn & Tiện ích": ["điện", "nước", "internet", "wifi", "hóa đơn", "cước",
                           "điện thoại", "bill"],
    "Mua sắm": ["mua", "shopee", "lazada", "tiki", "quần áo", "giày", "dép",
                "shopping", "túi xách", "mỹ phẩm"],
    "Giải trí": ["phim", "game", "netflix", "spotify", "du lịch", "vui chơi",
                 "karaoke", "concert", "vé xem", "cgv"],
    "Y tế": ["thuốc", "khám bệnh", "bệnh viện", "gym", "phòng gym",
             "bảo hiểm", "nha khoa", "bác sĩ"],
    "Giáo dục": ["học phí", "sách", "khóa học", "học", "giáo trình"],
    "Lương": ["lương", "salary"],
    "Thưởng": ["thưởng", "bonus"],
    "Thu nhập khác": ["thu nhập", "được cho", "lãi", "cổ tức"],
}


def suggest_category_from_text(description, valid_names):
    """Trả (tên_danh_mục, độ_tin_cậy) tốt nhất khớp mô tả, hoặc (None, 0)."""
    desc = (description or "").strip().lower()
    if not desc:
        return None, 0.0

    best_cat, best_score = None, 0
    for cat_name, keywords in KEYWORD_MAP.items():
        if cat_name not in valid_names:
            continue
        score = sum(1 for kw in keywords if kw in desc)
        if score > best_score:
            best_cat, best_score = cat_name, score

    if best_cat:
        return best_cat, min(0.95, 0.55 + 0.15 * best_score)
    return None, 0.0
