"""
scrapers/smartstore.py — 네이버 스마트스토어 스크래퍼

스마트스토어는 React/Next.js 기반 SPA이므로
network idle 상태까지 기다린 후 파싱한다.
"""
import re
from typing import Optional

from bs4 import BeautifulSoup
from playwright.sync_api import Page

from db.models import Product
from scrapers.base import BaseScraper, clean_price, clean_float, random_delay


class SmartStoreScraper(BaseScraper):
    PLATFORM = "스마트스토어"

    def scrape_page(self, page: Page, url: str) -> Product:
        # 핵심 요소 대기
        try:
            page.wait_for_load_state("networkidle", timeout=20_000)
        except Exception:
            pass
        try:
            page.wait_for_selector("._1eddO7u4UC", timeout=10_000)
        except Exception:
            pass

        random_delay(1.0, 2.0)
        html = page.content()
        soup = BeautifulSoup(html, "lxml")

        product = Product(url=url, platform=self.PLATFORM)
        product.name = self._parse_name(soup)
        product.brand = self._parse_brand(soup, page)
        product.price = self._parse_price(soup)
        product.original_price = self._parse_original_price(soup)
        product.review_count, product.rating = self._parse_review(soup)
        self._parse_detail_info(soup, product)

        return product

    # ────────────────────────────────────────
    def _parse_name(self, soup: BeautifulSoup) -> Optional[str]:
        # 스마트스토어 상품명 셀렉터 (2024+ 기준)
        for sel in [
            "._1eddO7u4UC",           # 상품명 클래스
            "h3._2dABiTwFG-",         # 상품 타이틀
            "div[class*='_3XamX']",   # 상품 헤더
            "h2.se-heading",
            ".ProductName_product_name__s1o0v",
            "[class*='product_name']",
            ".product_detail .name",
        ]:
            el = soup.select_one(sel)
            if el:
                return el.get_text(strip=True)

        # fallback: og:title
        og = soup.find("meta", property="og:title")
        if og and og.get("content"):
            return og["content"].strip()
        return None

    def _parse_brand(self, soup: BeautifulSoup, page: Page) -> Optional[str]:
        # 판매자명 (브랜드 역할)
        for sel in [
            "._1QRiCIVi6J",           # 스토어명
            ".StoreName_store_name__1aECR",
            "a[class*='store_name']",
            "[class*='StoreInfo'] a",
            ".brand_name",
        ]:
            el = soup.select_one(sel)
            if el:
                return el.get_text(strip=True)

        # 상품 상세 정보 테이블에서 브랜드 추출
        for row in soup.select("table tr"):
            th = row.select_one("th")
            td = row.select_one("td")
            if th and td and "브랜드" in th.get_text():
                return td.get_text(strip=True)
        return None

    def _parse_price(self, soup: BeautifulSoup) -> Optional[int]:
        for sel in [
            "._1LY7DqCnwR",           # 판매가
            "strong[class*='_1LY7']",
            ".[class*='price_sale'] strong",
            ".price_list ._2wX0OL8nMY",
            "span[class*='salePrice'] strong",
            "[class*='price_sale']",
        ]:
            el = soup.select_one(sel)
            if el:
                price = clean_price(el.get_text())
                if price:
                    return price
        return None

    def _parse_original_price(self, soup: BeautifulSoup) -> Optional[int]:
        for sel in [
            "._2FZbikSV2P",
            "del[class*='origin']",
            "span[class*='originalPrice']",
            ".[class*='price_origin']",
        ]:
            el = soup.select_one(sel)
            if el:
                return clean_price(el.get_text())
        return None

    def _parse_review(self, soup: BeautifulSoup):
        count = None
        rating = None

        for sel in [
            "._3oj-d2JKQ_",           # 평점
            "span[class*='avg']",
            "em[class*='rating']",
            "[class*='ReviewSummary'] em",
        ]:
            el = soup.select_one(sel)
            if el:
                rating = clean_float(el.get_text())
                if rating:
                    break

        for sel in [
            "._2L3vDiadT9",           # 리뷰수
            "span[class*='review_count']",
            "[class*='ReviewSummary'] span._2pgHN-ntx6",
        ]:
            el = soup.select_one(sel)
            if el:
                txt = re.sub(r"[^\d]", "", el.get_text())
                if txt:
                    count = int(txt)
                    break

        return count, rating

    def _parse_detail_info(self, soup: BeautifulSoup, product: Product) -> None:
        """상품정보제공고시 테이블 + 상세설명 파싱."""
        # 상품정보제공고시
        info_map: dict[str, str] = {}
        for row in soup.select("table tr"):
            th = row.select_one("th")
            td = row.select_one("td")
            if th and td:
                info_map[th.get_text(strip=True)] = td.get_text(" ", strip=True)

        if not product.manufacturer:
            product.manufacturer = self._find_in_map(
                info_map, ["제조사", "제조업체", "브랜드", "수입자"]
            )
        product.origin = self._find_in_map(
            info_map, ["원산지", "제조국", "생산국"]
        )

        # 상세 설명에서 영양 정보 추출
        detail_text = ""
        for sel in [
            ".se-main-container",
            "#INTRODUCE",
            "[class*='detail_contents']",
            ".product_detail_area",
        ]:
            el = soup.select_one(sel)
            if el:
                detail_text += el.get_text(" ", strip=True)
                break

        if detail_text:
            product.nutrition_raw = detail_text[:500]
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
