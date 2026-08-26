from scrapers.base import detect_platform
from scrapers.coupang import CoupangScraper
from scrapers.smartstore import SmartStoreScraper
from scrapers.naver_shopping import NaverShoppingScraper


def get_scraper(platform: str):
    """플랫폼명으로 스크래퍼 인스턴스를 반환한다."""
    mapping = {
        "쿠팡": CoupangScraper,
        "스마트스토어": SmartStoreScraper,
        "네이버쇼핑": NaverShoppingScraper,
    }
    cls = mapping.get(platform)
    return cls() if cls else None
