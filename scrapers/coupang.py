"""
scrapers/coupang.py — 쿠팡 스크래퍼

쿠팡은 봇 탐지가 강하므로 딜레이와 헤더 설정에 주의한다.
HTML 구조 기준: 2024-2026년 기준 쿠팡 PC 상품 상세페이지.
"""
import re
import time
from typing import Optional

from bs4 import BeautifulSoup
from playwright.sync_api import Page

from db.models import Product
from scrapers.base import BaseScraper, clean_price, clean_float, random_delay


class CoupangScraper(BaseScraper):
    PLATFORM = "쿠팡"

    def scrape_page(self, page: Page, url: str) -> Product:
        # 쿠팡은 JS 렌더링이 완료될 때까지 추가 대기
        try:
            page.wait_for_selector(".prod-title", timeout=15_000)
        except Exception:
            pass

        random_delay(0.8, 1.5)
        html = page.content()
        soup = BeautifulSoup(html, "lxml")

        product = Product(url=url, platform=self.PLATFORM)

        # ── 상품명
        product.name = self._parse_name(soup)

        # ── 브랜드
        product.brand = self._parse_brand(soup)

        # ── 판매가
        product.price = self._parse_price(soup)

        # ── 정가
        product.original_price = self._parse_original_price(soup)

        # ── 리뷰수 / 평점
        product.review_count, product.rating = self._parse_review(soup)

        # ── 영양정보 / 제조사 등 (상세설명 영역)
        self._parse_detail_info(soup, product)

        return product

    # ────────────────────────────────────────
    def _parse_name(self, soup: BeautifulSoup) -> Optional[str]:
        # 1순위: .prod-title h1
        for sel in [
            "h1.prod-title",
            ".prod-buy-header h1",
            "h1[data-buybox-name='title']",
            ".prod-buy-header__title",
        ]:
            el = soup.select_one(sel)
            if el:
                return el.get_text(strip=True)
        return None

    def _parse_brand(self, soup: BeautifulSoup) -> Optional[str]:
        # 상품 상세 테이블에서 브랜드/제조사 추출
        for row in soup.select(".prod-attr-list li, .prod-information tr"):
            text = row.get_text(" ", strip=True)
            if "브랜드" in text or "제조사" in text or "브랜드명" in text:
                # 콜론 뒤 값 추출
                parts = re.split(r"[:\s]{1,3}", text, maxsplit=1)
                if len(parts) > 1:
                    return parts[-1].strip()
        # 대안: 링크 텍스트
        el = soup.select_one("a.prod-brand-name, span.prod-brand-name")
        if el:
            return el.get_text(strip=True)
        return None

    def _parse_price(self, soup: BeautifulSoup) -> Optional[int]:
        # 할인가 (최종 판매가)
        for sel in [
            ".prod-price .total-price strong",
            ".prod-sale-price .total-price strong",
            "strong.total-price",
            ".price-info .final-price",
        ]:
            el = soup.select_one(sel)
            if el:
                return clean_price(el.get_text())
        return None

    def _parse_original_price(self, soup: BeautifulSoup) -> Optional[int]:
        for sel in [
            ".base-price",
            ".prod-origin-price",
            "del.base-price",
        ]:
            el = soup.select_one(sel)
            if el:
                return clean_price(el.get_text())
        return None

    def _parse_review(self, soup: BeautifulSoup):
        count = None
        rating = None

        # 평점
        for sel in [
            ".rating-star-num",
            ".prod-rating .rating",
            "[class*='rating-total-star-num']",
        ]:
            el = soup.select_one(sel)
            if el:
                rating = clean_float(el.get_text())
                break

        # 리뷰수
        for sel in [
            ".count.notranslate",
            ".prod-review .count",
            "[class*='review-count']",
            "span.count",
        ]:
            el = soup.select_one(sel)
            if el:
                txt = re.sub(r"[^\d]", "", el.get_text())
                if txt:
                    count = int(txt)
                    break

        return count, rating

    def _parse_detail_info(self, soup: BeautifulSoup, product: Product) -> None:
        """상세 스펙 테이블에서 영양정보·제조사·원산지 파싱."""
        # 상품 정보 테이블 (dt/dd 또는 th/td)
        info_map: dict[str, str] = {}

        for row in soup.select(".product-information__table tr"):
            th = row.select_one("th")
            td = row.select_one("td")
            if th and td:
                info_map[th.get_text(strip=True)] = td.get_text(" ", strip=True)

        for dt, dd in zip(
            soup.select(".prod-attr-list dt"),
            soup.select(".prod-attr-list dd"),
        ):
            info_map[dt.get_text(strip=True)] = dd.get_text(" ", strip=True)

        product.manufacturer = self._find_in_map(
            info_map, ["제조사", "제조업체", "브랜드", "브랜드명"]
        )
        product.origin = self._find_in_map(
            info_map, ["원산지", "제조국", "생산국"]
        )

        # 영양성분: 상세 설명 내 텍스트 전체에서 정규식으로 추출
        detail_text = ""
        for sel in [".prod-description", "#detailed-images", ".product-detail"]:
            el = soup.select_one(sel)
            if el:
                detail_text += el.get_text(" ", strip=True)

        if detail_text:
            product.nutrition_raw = detail_text[:500]  # 원본 저장 (AI 파싱용)
            product.calories = self._extract_kcal(detail_text)
            product.protein = self._extract_nutrient(detail_text, "단백질")
            product.carbs = self._extract_nutrient(detail_text, "탄수화물")
            product.fat = self._extract_nutrient(detail_text, "지방")

    @staticmethod
    def _find_in_map(info_map: dict, keys: list) -> Optional[str]:
        for k in keys:
            for mk, mv in info_map.items():
                if k in mk:
                    return mv
        return None

    @staticmethod
    def _extract_kcal(text: str) -> Optional[float]:
        m = re.search(r"(\d[\d,.]*)\s*(?:kcal|칼로리|Kcal|KCAL)", text, re.IGNORECASE)
        if m:
            return clean_float(m.group(1))
        return None

    @staticmethod
    def _extract_nutrient(text: str, name: str) -> Optional[float]:
        pattern = rf"{name}[^\d]{{0,10}}(\d[\d.,]*)\s*g"
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return clean_float(m.group(1))
        return None
