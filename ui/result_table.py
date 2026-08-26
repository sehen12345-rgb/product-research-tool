"""
ui/result_table.py — 결과 테이블 위젯
"""
import webbrowser
from typing import List, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QLabel, QAbstractItemView,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QBrush

from db.models import Product
from ui.styles import (
    COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING,
    COLOR_TEXT_SUB, COLOR_ACCENT, COLOR_BG,
    get_platform_badge_color,
)


# 테이블 컬럼 정의: (헤더 이름, product.to_dict() 키, 너비)
COLUMNS = [
    ("플랫폼",    "platform",       90),
    ("상품명",    "name",           280),
    ("브랜드",    "brand",          110),
    ("판매가",    "price",           90),
    ("정가",      "original_price",  80),
    ("칼로리",   "calories",         75),
    ("단백질",   "protein",          70),
    ("탄수화물", "carbs",            75),
    ("지방",     "fat",              65),
    ("제조사",   "manufacturer",    110),
    ("원산지",   "origin",           90),
    ("리뷰수",   "review_count",     75),
    ("평점",     "rating",           60),
    ("수집일시", "collected_at",    130),
    ("상태",     "status",           60),
]


class ResultTable(QWidget):
    """
    필터 탭 + 테이블 + 버튼바로 구성된 결과 표시 위젯.
    더블클릭 시 브라우저에서 원본 URL 열기.
    """

    # 선택 삭제 요청 시그널 (id 목록)
    delete_requested = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._products: List[Product] = []
        self._current_filter: Optional[str] = None
        self._build_ui()

    # ────────────────────────────────────────
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # ── 필터 탭 + 버튼 바
        top_bar = QHBoxLayout()
        top_bar.setSpacing(6)

        self._tab_btns: dict[Optional[str], QPushButton] = {}
        for label, platform in [
            ("전체", None),
            ("쿠팡", "쿠팡"),
            ("스마트스토어", "스마트스토어"),
            ("네이버쇼핑", "네이버쇼핑"),
        ]:
            btn = QPushButton(label)
            btn.setProperty("tab_btn", "true")
            btn.setProperty("active", "false")
            btn.clicked.connect(lambda _, p=platform: self._filter(p))
            self._tab_btns[platform] = btn
            top_bar.addWidget(btn)

        top_bar.addSpacing(16)

        self.btn_excel = QPushButton("Excel 내보내기")
        self.btn_excel.setFixedWidth(120)
        top_bar.addWidget(self.btn_excel)

        self.btn_csv = QPushButton("CSV 내보내기")
        self.btn_csv.setFixedWidth(100)
        top_bar.addWidget(self.btn_csv)

        top_bar.addStretch()

        self.btn_delete = QPushButton("선택 삭제")
        self.btn_delete.setObjectName("btn_delete")
        self.btn_delete.setFixedWidth(90)
        self.btn_delete.clicked.connect(self._on_delete)
        top_bar.addWidget(self.btn_delete)

        layout.addLayout(top_bar)

        # ── 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(len(COLUMNS))
        self.table.setHorizontalHeaderLabels([c[0] for c in COLUMNS])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.setShowGrid(True)

        # 컬럼 너비 설정
        for i, (_, _, width) in enumerate(COLUMNS):
            self.table.setColumnWidth(i, width)

        # 상품명 컬럼은 늘어나게
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )

        self.table.cellDoubleClicked.connect(self._on_double_click)

        layout.addWidget(self.table)

        # 초기 탭 활성화
        self._filter(None)

    # ────────────────────────────────────────
    def set_products(self, products: List[Product]):
        """전체 데이터를 교체하고 현재 필터로 렌더링."""
        self._products = products
        self._render(products)
        self._update_tab_labels()

    def add_product(self, product: Product):
        """단건 추가 (수집 중 실시간 업데이트용)."""
        self._products.append(product)
        if self._current_filter is None or product.platform == self._current_filter:
            self._append_row(product)
        self._update_tab_labels()

    def clear(self):
        self._products.clear()
        self.table.setRowCount(0)
        self._update_tab_labels()

    # ────────────────────────────────────────
    def _filter(self, platform: Optional[str]):
        self._current_filter = platform

        # 탭 버튼 active 상태 갱신
        for p, btn in self._tab_btns.items():
            active = p == platform
            btn.setProperty("active", "true" if active else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        filtered = [
            p for p in self._products
            if platform is None or p.platform == platform
        ]
        self._render(filtered)

    def _render(self, products: List[Product]):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        for p in products:
            self._append_row(p)
        self.table.setSortingEnabled(True)

    def _append_row(self, product: Product):
        row = self.table.rowCount()
        self.table.insertRow(row)
        data = product.to_dict()

        for col, (_, key, _) in enumerate(COLUMNS):
            val = str(data.get(key, ""))
            item = QTableWidgetItem(val)
            item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

            # URL은 userData로 저장 (더블클릭용)
            if col == 0:
                item.setData(Qt.ItemDataRole.UserRole, product.url)
                item.setData(Qt.ItemDataRole.UserRole + 1, product.id)
                # 플랫폼 배지 색상
                color = get_platform_badge_color(product.platform)
                item.setForeground(QBrush(QColor(color)))
                item.setFont(QFont("Pretendard", 12, QFont.Weight.Bold))

            # 에러 행 강조
            if product.status == "error":
                item.setForeground(QBrush(QColor(COLOR_ERROR)))

            # 수치 컬럼 오른쪽 정렬
            if key in ("price", "original_price", "calories", "protein",
                       "carbs", "fat", "review_count", "rating"):
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

            # 상태 컬럼 색상
            if key == "status":
                if val == "success":
                    item.setForeground(QBrush(QColor(COLOR_SUCCESS)))
                    item.setText("✓")
                else:
                    item.setForeground(QBrush(QColor(COLOR_ERROR)))
                    item.setText("✗")

            self.table.setItem(row, col, item)

        self.table.setRowHeight(row, 36)

    def _update_tab_labels(self):
        """탭 버튼 카운터 업데이트."""
        counts = {"쿠팡": 0, "스마트스토어": 0, "네이버쇼핑": 0}
        for p in self._products:
            if p.platform in counts:
                counts[p.platform] += 1
        total = len(self._products)

        self._tab_btns[None].setText(f"전체 {total}")
        self._tab_btns["쿠팡"].setText(f"쿠팡 {counts['쿠팡']}")
        self._tab_btns["스마트스토어"].setText(f"스마트스토어 {counts['스마트스토어']}")
        self._tab_btns["네이버쇼핑"].setText(f"네이버쇼핑 {counts['네이버쇼핑']}")

    # ────────────────────────────────────────
    def _on_double_click(self, row: int, col: int):
        """더블클릭 → 브라우저에서 원본 URL 열기."""
        item = self.table.item(row, 0)
        if item:
            url = item.data(Qt.ItemDataRole.UserRole)
            if url:
                webbrowser.open(url)

    def _on_delete(self):
        """선택된 행의 상품 ID를 상위에 전달."""
        selected_rows = set(idx.row() for idx in self.table.selectedIndexes())
        ids = []
        for row in selected_rows:
            item = self.table.item(row, 0)
            if item:
                pid = item.data(Qt.ItemDataRole.UserRole + 1)
                if pid is not None:
                    ids.append(pid)
        if ids:
            self.delete_requested.emit(ids)

    # ────────────────────────────────────────
    def get_visible_products(self) -> List[Product]:
        """현재 필터된(표시 중인) 상품 목록 반환."""
        if self._current_filter is None:
            return list(self._products)
        return [p for p in self._products if p.platform == self._current_filter]
