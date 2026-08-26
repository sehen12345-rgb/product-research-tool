"""
export/csv_exporter.py — CSV 내보내기
"""
import csv
from typing import List

from db.models import Product


HEADERS = [
    "플랫폼", "상품명", "브랜드", "판매가", "정가",
    "칼로리(kcal)", "단백질(g)", "탄수화물(g)", "지방(g)",
    "영양성분(원문)", "제조사", "원산지",
    "리뷰수", "평점", "수집일시", "상태", "오류메시지", "URL",
]

KEYS = [
    "platform", "name", "brand", "price", "original_price",
    "calories", "protein", "carbs", "fat",
    "nutrition_raw", "manufacturer", "origin",
    "review_count", "rating", "collected_at", "status", "error_message", "url",
]


def export_csv(products: List[Product], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        for product in products:
            data = product.to_dict()
            row = {header: data.get(key, "") for header, key in zip(HEADERS, KEYS)}
            writer.writerow(row)
