"""
scrapers/base.py — 스크래퍼 추상 기본 클래스
"""
import re
import time
import random
from abc import ABC, abstractmethod
from typing import Optional

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

from db.models import Product


# 공통 User-Agent 목록
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


def detect_platform(url: str) -> Optional[str]:
    """URL 패턴으로 플랫폼을 감지한다."""
    url = url.strip()
    if "coupang.com" in url:
        return "쿠팡"
    if "smartstore.naver.com" in url:
        return "스마트스토어"
    if "shopping.naver.com" in url:
        return "네이버쇼핑"
    return None


def random_delay(min_sec: float = 1.0, max_sec: float = 3.0) -> None:
    time.sleep(random.uniform(min_sec, max_sec))


def clean_price(text: str) -> Optional[int]:
    """'15,900원' → 15900"""
    if not text:
        return None
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else None


def clean_float(text: str) -> Optional[float]:
    """'4.8점' → 4.8"""
    if not text:
        return None
    m = re.search(r"[\d]+\.?[\d]*", text)
    return float(m.group()) if m else None


class BaseScraper(ABC):
    """플랫폼 스크래퍼의 공통 인터페이스."""

    PLATFORM: str = ""

    def scrape(self, url: str) -> Product:
        """
        Playwright로 페이지를 열고 scrape_page()를 호출한다.
        예외 발생 시 에러 Product를 반환한다.
        """
        try:
            with sync_playwright() as pw:
                browser = self._launch_browser(pw)
                context = self._create_context(browser)
                page = context.new_page()
                self._set_stealth(page)
                page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                random_delay(1.5, 2.5)
                product = self.scrape_page(page, url)
                browser.close()
                return product
        except Exception as exc:
            return Product.error_product(url, self.PLATFORM, str(exc))

    # ────────────────────────────────────────────────
    @abstractmethod
    def scrape_page(self, page: Page, url: str) -> Product:
        """실제 파싱 로직. 서브클래스에서 구현."""
        ...

    # ────────────────────────────────────────────────
    def _launch_browser(self, pw) -> Browser:
        return pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ],
        )

    def _create_context(self, browser: Browser) -> BrowserContext:
        return browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1280, "height": 900},
            locale="ko-KR",
            timezone_id="Asia/Seoul",
            extra_http_headers={
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            },
        )

    def _set_stealth(self, page: Page) -> None:
        """자동화 감지 우회."""
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3]});
            window.chrome = {runtime: {}};
        """)

    # ────────────────────────────────────────────────
    @staticmethod
    def _text(page: Page, selector: str, default: str = "") -> str:
        try:
            el = page.query_selector(selector)
            return el.inner_text().strip() if el else default
        except Exception:
            return default

    @staticmethod
    def _attr(page: Page, selector: str, attr: str, default: str = "") -> str:
        try:
            el = page.query_selector(selector)
            return (el.get_attribute(attr) or default).strip() if el else default
        except Exception:
            return default
