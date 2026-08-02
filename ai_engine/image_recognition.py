# -*- coding: utf-8 -*-
"""
Nhận diện vật thể trong ảnh hoá đơn/chi tiêu bằng mô hình MobileNet-SSD
(Caffe, huấn luyện sẵn trên bộ dữ liệu PASCAL VOC — 20 lớp vật thể phổ biến),
chạy hoàn toàn offline qua OpenCV DNN. Đây là giải pháp mã nguồn mở miễn phí,
không gọi bất kỳ API trả phí nào.

Lưu ý trung thực: bộ 20 lớp VOC khá tổng quát (xe cộ, người, đồ nội thất,
động vật, chai lọ...) chứ không chuyên biệt cho hoá đơn/đồ ăn Việt Nam như
OpenAI Vision. Vì vậy hệ thống luôn hiển thị độ tin cậy và cho phép người
dùng đổi danh mục nếu AI đoán sai — đúng như đặc tả yêu cầu.
"""
import os
import numpy as np
import cv2
from django.conf import settings

VOC_CLASSES = [
    "background", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus",
    "car", "cat", "chair", "cow", "diningtable", "dog", "horse", "motorbike",
    "person", "pottedplant", "sheep", "sofa", "train", "tvmonitor",
]

# Ánh xạ nhãn vật thể nhận diện được -> danh mục chi tiêu gợi ý
LABEL_TO_CATEGORY = {
    "bicycle": "Di chuyển", "motorbike": "Di chuyển", "car": "Di chuyển",
    "bus": "Di chuyển", "train": "Di chuyển", "aeroplane": "Di chuyển", "boat": "Di chuyển",
    "bottle": "Ăn uống",
    "chair": "Mua sắm", "diningtable": "Mua sắm", "sofa": "Mua sắm",
    "pottedplant": "Mua sắm", "tvmonitor": "Mua sắm",
    "cat": "Khác", "dog": "Khác", "bird": "Khác", "cow": "Khác", "sheep": "Khác", "horse": "Khác",
    "person": "Khác",
}

_net = None


def _get_net():
    global _net
    if _net is None:
        prototxt = os.path.join(settings.AI_MODEL_DIR, "MobileNetSSD_deploy.prototxt")
        model = os.path.join(settings.AI_MODEL_DIR, "MobileNetSSD_deploy.caffemodel")
        _net = cv2.dnn.readNetFromCaffe(prototxt, model)
    return _net


def recognize_image(image_path, confidence_threshold=0.4):
    """Nhận diện vật thể nổi bật nhất trong ảnh.

    Trả về dict: {label, category, confidence, all_detections}
    Nếu không nhận diện được gì rõ ràng, trả confidence thấp và category=None
    để người dùng tự chọn danh mục.
    """
    net = _get_net()
    img = cv2.imread(image_path)
    if img is None:
        return {"label": None, "category": None, "confidence": 0.0, "all_detections": []}

    h, w = img.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(img, (300, 300)), 0.007843, (300, 300), 127.5)
    net.setInput(blob)
    detections = net.forward()

    results = []
    for i in range(detections.shape[2]):
        conf = float(detections[0, 0, i, 2])
        if conf < confidence_threshold:
            continue
        idx = int(detections[0, 0, i, 1])
        if idx <= 0 or idx >= len(VOC_CLASSES):
            continue
        label = VOC_CLASSES[idx]
        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
        results.append({"label": label, "confidence": conf, "box": box.tolist()})

    results.sort(key=lambda r: -r["confidence"])

    if not results:
        return {"label": None, "category": None, "confidence": 0.0, "all_detections": []}

    top = results[0]
    category = LABEL_TO_CATEGORY.get(top["label"], "Khác")
    return {
        "label": top["label"],
        "category": category,
        "confidence": top["confidence"],
        "all_detections": results[:5],
    }


LABEL_VI = {
    "bicycle": "xe đạp", "motorbike": "xe máy", "car": "ô tô", "bus": "xe buýt",
    "train": "tàu hỏa", "aeroplane": "máy bay", "boat": "thuyền",
    "bottle": "chai/đồ uống", "chair": "ghế", "diningtable": "bàn ăn",
    "sofa": "ghế sofa", "pottedplant": "cây cảnh", "tvmonitor": "tivi/màn hình",
    "cat": "mèo", "dog": "chó", "bird": "chim", "cow": "bò", "sheep": "cừu",
    "horse": "ngựa", "person": "người",
}


def label_to_vietnamese(label):
    return LABEL_VI.get(label, label or "không xác định")
