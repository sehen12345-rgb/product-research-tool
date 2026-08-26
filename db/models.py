"""
db/models.py — 상품 데이터 모델
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Product:
    """스크래핑된 상품 정보를 담는 데이터클래스."""

    # 필수 식별 정보
    url: str
    platform: str  # 쿠팡 / 스마트스토어 / 네이버쇼핑

    # 기본 상품 정보
    name: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[int] = None          # 판매가 (원)
    original_price: Optional[int] = None  # 정가 (원)

    # 영양 정보 (식품)
    calories: Optional[float] = None     # kcal
    protein: Optional[float] = None      # 단백질 (g)
    carbs: Optional[float] = None        # 탄수화물 (g)
    fat: Optional[float] = None          # 지방 (g)
    nutrition_raw: Optional[str] = None  # 원본 영양성분 텍스트

    # 제조/원산지 정보
    manufacturer: Optional[str] = None
    origin: Optional[str] = None

    # 리뷰 정보
    review_count: Optional[int] = None
    rating: Optional[float] = None       # 1.0 ~ 5.0

    # 메타
    collected_at: datetime = field(default_factory=datetime.now)
    status: str = "success"             # success / error
    error_message: Optional[str] = None

    # DB 자동 할당
    id: Optional[int] = None

    # ──────────────────────────────────────────
    def to_dict(self) -> dict:
        """테이블·내보내기용 딕셔너리 변환."""
        return {
            "id": self.id,
            "platform": self.platform,
            "name": self.name or "",
            "brand": self.brand or "",
            "price": self._fmt_price(self.price),
            "original_price": self._fmt_price(self.original_price),
            "calories": self._fmt_num(self.calories),
            "protein": self._fmt_num(self.protein),
            "carbs": self._fmt_num(self.carbs),
            "fat": self._fmt_num(self.fat),
            "nutrition_raw": self.nutrition_raw or "",
            "manufacturer": self.manufacturer or "",
            "origin": self.origin or "",
            "review_count": self.review_count if self.review_count is not None else "",
            "rating": self._fmt_num(self.rating),
            "url": self.url,
            "collected_at": self.collected_at.strftime("%Y-%m-%d %H:%M:%S"),
            "status": self.status,
            "error_message": self.error_message or "",
        }

    @staticmethod
    def _fmt_price(v: Optional[int]) -> str:
        if v is None:
            return ""
        return f"{v:,}"

    @staticmethod
    def _fmt_num(v) -> str:
        if v is None:
            return ""
        return str(v)

    # ──────────────────────────────────────────
    @classmethod
    def error_product(cls, url: str, platform: str, message: str) -> "Product":
        """스크래핑 실패 시 에러 상태로 생성."""
        return cls(
            url=url,
            platform=platform,
            status="error",
            error_message=message,
        )
