"""
db/database.py — SQLite 초기화 및 CRUD
"""
import sqlite3
import os
from datetime import datetime
from typing import List, Optional

from db.models import Product

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "research.db")

DDL = """
CREATE TABLE IF NOT EXISTS products (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    url             TEXT NOT NULL,
    platform        TEXT NOT NULL,
    name            TEXT,
    brand           TEXT,
    price           INTEGER,
    original_price  INTEGER,
    calories        REAL,
    protein         REAL,
    carbs           REAL,
    fat             REAL,
    nutrition_raw   TEXT,
    manufacturer    TEXT,
    origin          TEXT,
    review_count    INTEGER,
    rating          REAL,
    collected_at    TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'success',
    error_message   TEXT
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """DB 파일과 테이블을 초기화한다."""
    with get_connection() as conn:
        conn.executescript(DDL)


def save_product(product: Product) -> int:
    """상품 저장 후 삽입된 row id 반환."""
    sql = """
    INSERT INTO products
        (url, platform, name, brand, price, original_price,
         calories, protein, carbs, fat, nutrition_raw,
         manufacturer, origin, review_count, rating,
         collected_at, status, error_message)
    VALUES
        (:url, :platform, :name, :brand, :price, :original_price,
         :calories, :protein, :carbs, :fat, :nutrition_raw,
         :manufacturer, :origin, :review_count, :rating,
         :collected_at, :status, :error_message)
    """
    params = {
        "url": product.url,
        "platform": product.platform,
        "name": product.name,
        "brand": product.brand,
        "price": product.price,
        "original_price": product.original_price,
        "calories": product.calories,
        "protein": product.protein,
        "carbs": product.carbs,
        "fat": product.fat,
        "nutrition_raw": product.nutrition_raw,
        "manufacturer": product.manufacturer,
        "origin": product.origin,
        "review_count": product.review_count,
        "rating": product.rating,
        "collected_at": product.collected_at.strftime("%Y-%m-%d %H:%M:%S"),
        "status": product.status,
        "error_message": product.error_message,
    }
    with get_connection() as conn:
        cur = conn.execute(sql, params)
        return cur.lastrowid


def delete_products(ids: List[int]) -> None:
    """id 목록의 상품을 삭제한다."""
    if not ids:
        return
    placeholders = ",".join("?" * len(ids))
    with get_connection() as conn:
        conn.execute(f"DELETE FROM products WHERE id IN ({placeholders})", ids)


def get_all_products(platform: Optional[str] = None) -> List[Product]:
    """저장된 상품 전체 조회. platform 지정 시 필터링."""
    if platform:
        sql = "SELECT * FROM products WHERE platform = ? ORDER BY id DESC"
        args = (platform,)
    else:
        sql = "SELECT * FROM products ORDER BY id DESC"
        args = ()

    with get_connection() as conn:
        rows = conn.execute(sql, args).fetchall()

    products = []
    for row in rows:
        p = Product(
            id=row["id"],
            url=row["url"],
            platform=row["platform"],
            name=row["name"],
            brand=row["brand"],
            price=row["price"],
            original_price=row["original_price"],
            calories=row["calories"],
            protein=row["protein"],
            carbs=row["carbs"],
            fat=row["fat"],
            nutrition_raw=row["nutrition_raw"],
            manufacturer=row["manufacturer"],
            origin=row["origin"],
            review_count=row["review_count"],
            rating=row["rating"],
            collected_at=datetime.strptime(row["collected_at"], "%Y-%m-%d %H:%M:%S"),
            status=row["status"],
            error_message=row["error_message"],
        )
        products.append(p)
    return products


def clear_all() -> None:
    """테이블 전체 비우기."""
    with get_connection() as conn:
        conn.execute("DELETE FROM products")
