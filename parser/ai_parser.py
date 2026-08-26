"""
parser/ai_parser.py — Claude API로 비정형 상품 정보 파싱

BeautifulSoup으로 추출하지 못한 칼로리·영양성분·제조사 등을
Claude API의 JSON 응답으로 보완한다.
Prompt caching 적용으로 시스템 프롬프트 캐싱.
"""
import json
import os
import re
from typing import Optional

import anthropic
from dotenv import load_dotenv

from db.models import Product

load_dotenv()

_SYSTEM_PROMPT = """당신은 상품 상세페이지 HTML 텍스트에서 구조화된 정보를 추출하는 전문가입니다.

주어진 텍스트에서 아래 필드를 최대한 정확하게 추출하고 JSON으로 반환하세요.
추출할 수 없는 필드는 null로 반환하세요.

반환 형식 (JSON only, 코드블록 없이):
{
  "name": "상품명",
  "brand": "브랜드/제조사명",
  "price": 15900,
  "original_price": 19900,
  "calories": 250.0,
  "protein": 25.5,
  "carbs": 10.2,
  "fat": 8.3,
  "manufacturer": "제조사",
  "origin": "원산지"
}

규칙:
- price, original_price: 숫자만 (콤마 제거, 원 단위 정수)
- calories, protein, carbs, fat: 숫자만 (float)
- 영양성분이 없는 상품(전자제품, 의류 등)은 해당 필드 null
- 추측하지 말 것. 텍스트에서 명확히 확인되는 값만 반환"""


class AIParser:
    """Claude API를 이용한 상품 정보 보조 파싱."""

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else None
        self.model = "claude-sonnet-4-6"

    def is_available(self) -> bool:
        return self.client is not None

    def parse(self, html_text: str, product: Product) -> Product:
        """
        HTML 텍스트를 Claude에 전달해 누락된 필드를 보완한다.
        API 실패 시 원본 product를 그대로 반환한다.
        """
        if not self.client:
            return product

        # 텍스트 길이 제한 (비용 절약)
        text = html_text[:4000] if len(html_text) > 4000 else html_text

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=[
                    {
                        "type": "text",
                        "text": _SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},  # prompt caching
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": f"다음 상품 페이지 텍스트에서 정보를 추출해주세요:\n\n{text}",
                    }
                ],
            )

            raw = response.content[0].text.strip()
            data = self._safe_parse_json(raw)
            if data:
                product = self._merge(product, data)

        except Exception as exc:
            # AI 파싱 실패는 무시하고 기존 데이터 사용
            print(f"[AIParser] 파싱 실패: {exc}")

        return product

    # ────────────────────────────────────────
    @staticmethod
    def _safe_parse_json(text: str) -> Optional[dict]:
        """코드블록 제거 후 JSON 파싱."""
        text = re.sub(r"```(?:json)?", "", text).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 부분 매칭 시도
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group())
                except Exception:
                    pass
        return None

    @staticmethod
    def _merge(product: Product, data: dict) -> Product:
        """AI 결과로 누락된 필드만 채운다. 기존 값 우선."""

        def _set_if_missing(attr, val, cast=None):
            if getattr(product, attr) is None and val is not None:
                try:
                    setattr(product, attr, cast(val) if cast else val)
                except (ValueError, TypeError):
                    pass

        _set_if_missing("name", data.get("name"))
        _set_if_missing("brand", data.get("brand"))
        _set_if_missing("price", data.get("price"), int)
        _set_if_missing("original_price", data.get("original_price"), int)
        _set_if_missing("calories", data.get("calories"), float)
        _set_if_missing("protein", data.get("protein"), float)
        _set_if_missing("carbs", data.get("carbs"), float)
        _set_if_missing("fat", data.get("fat"), float)
        _set_if_missing("manufacturer", data.get("manufacturer"))
        _set_if_missing("origin", data.get("origin"))

        return product
