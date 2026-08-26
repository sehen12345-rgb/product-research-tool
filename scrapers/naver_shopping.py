"""
scrapers/naver_shopping.py — 네이버쇼핑 스크래퍼

네이버쇼핑(shopping.naver.com) 상품 상세페이지 파싱.
쇼핑 집계 페이지는 최저가 정보 + 여러 판매처 정보를 제공한다.
"""
import re
from typing import Optional

from bs4 import BeautifulSoup
from playwright.sync_api import Page

from db.models import Product
from scrapers.base import BaseScraper, clean_price, clean_float, random_delay


class NaverShoppingScraper(BaseScraper):
    PLATFORM = "네이버쇼핑"

    def scrape_page(self, page: Page, url: str) -> Product:
        try:
            page.wait_for_load_state("networkidle", timeout=20_000)
        except Exception:
            pass
        try:
            page.wait_for_selector("h1, .prod_name, .tit_inner", timeout=12_000)
        except Exception:
            pass

        random_delay(1.0, 2.0)
        html = page.content()
        soup = BeautifulSoup(html, "lxml")

        product = Product(url=url, platform=self.PLATFORM)
        product.name = self._parse_name(soup)
        product.brand = self._parse_brand(soup)
        product.price = self._parse_price(soup)
        product.original_price = self._parse_original_price(soup)
        product.review_count, product.rating = self._parse_review(soup)
        self._parse_detail_info(soup, product)

        return product

    # ────────────────────────────────────────
    def _parse_name(self, soup: BeautifulSoup) -> Optional[str]:
        for sel in [
            ".prod_name",
            "h1.tit_inner",
            ".title_area h1",
            "h1[class*='prod_name']",
            ".product_title",
            "h1",
        ]:
            el = soup.select_one(sel)
            if el:
                name = el.get_text(strip=True)
                if name:
                    return name

        og = soup.find("meta", property="og:title")
        if og and og.get("content"):
            return og["content"].strip()
        return None

    def _parse_brand(self, soup: BeautifulSoup) -> Optional[str]:
        for sel in [
            ".brand_name",
            "a[class*='brand']",
            ".prod_brand",
            "[class*='maker'] a",
        ]:
            el = soup.select_one(sel)
            if el:
                return el.get_text(strip=True)

        # 상품 스펙 테이블
        for row in soup.select("table tr, dl.spec_list dt"):
            th = row.select_one("th, dt")
            td = row.select_one("td, dd")
            if th and td and "브랜드" in th.get_text():
                return td.get_text(strip=True)
        return None

    def _parse_price(self, soup: BeautifulSoup) -> Optional[int]:
        # 최저가
        for sel in [
            ".price_num",
            "strong.num",
            ".prc_num",
            "em[class*='price']",
            ".price_main em",
        ]:
            el = soup.select_one(sel)
            if el:
                price = clean_price(el.get_text())
                if price:
                    return price
        return None

    def _parse_original_price(self, soup: BeautifulSoup) -> Optional[int]:
        for sel in [
            ".price_org",
            "del[class*='price']",
            "s.price",
        ]:
            el = soup.select_one(sel)
            if el:
                return clean_price(el.get_text())
        return None

    def _parse_review(self, soup: BeautifulSoup):
        count = None
        rating = None

        for sel in [
            ".graph_desc em",
            "em[class*='rating']",
            ".star_score em",
            ".review_score em",
        ]:
            el = soup.select_one(sel)
            if el:
                rating = clean_float(el.get_text())
                if rating:
                    break

        for sel in [
            ".count_num",
            "span[class*='review_cnt']",
            ".review_count",
            ".txt_num",
        ]:
            el = soup.select_one(sel)
            if el:
                txt = re.sub(r"[^\d]", "", el.get_text())
                if txt:
                    count = int(txt)
                    break

        return count, rating

    def _parse_detail_info(self, soup: BeautifulSoup, product: Product) -> None:
        info_map: dict[str, str] = {}

        # 상품 스펙 테이블
        for row in soup.select("table tr"):
            th = row.select_one("th")
            td = row.select_one("td")
            if th and td:
                info_map[th.get_text(strip=True)] = td.get_text(" ", strip=True)

        # 정의 목록 형태
        dts = soup.select("dl dt")
        dds = soup.select("dl dd")
        for dt, dd in zip(dts, dds):
            info_map[dt.get_text(strip=True)] = dd.get_text(" ", strip=True)

        product.manufacturer = self._find_in_map(
            info_map, ["제조사", "제조업체", "브랜드", "수입원", "수입자"]
        )
        product.origin = self._find_in_map(
            info_map, ["원산지", "제조국", "생산국"]
        )

        # 상세 설명 영역 텍스트
        detail_text = ""
        for sel in [".detail_cont", ".product_detail", ".goods_desc", ".se-main-container"]:
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
