"""
ui/input_panel.py — URL 입력 패널
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from ui.styles import COLOR_TEXT_SUB, COLOR_BORDER


class InputPanel(QWidget):
    """
    URL 입력 패널.
    수집 시작 / 초기화 버튼과 URL 입력 TextEdit으로 구성.
    """

    # 신호: 수집 시작 요청 (URL 목록 전달)
    collect_requested = pyqtSignal(list)
    # 신호: 초기화 요청
    clear_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # ────────────────────────────────────────
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 헤더
        header_row = QHBoxLayout()
        lbl = QLabel("URL 입력")
        lbl.setFont(QFont("Pretendard", 13, QFont.Weight.Bold))
        header_row.addWidget(lbl)
        header_row.addStretch()

        hint = QLabel("줄바꿈으로 여러 URL 입력 가능 | 쿠팡·스마트스토어·네이버쇼핑 지원")
        hint.setObjectName("label_sub")
        hint.setStyleSheet(f"color: {COLOR_TEXT_SUB}; font-size: 12px;")
        header_row.addWidget(hint)

        layout.addLayout(header_row)

        # URL 입력창
        self.txt_url = QTextEdit()
        self.txt_url.setPlaceholderText(
            "https://www.coupang.com/vp/products/...\n"
            "https://smartstore.naver.com/...\n"
            "https://shopping.naver.com/...\n"
        )
        self.txt_url.setMinimumHeight(120)
        self.txt_url.setMaximumHeight(180)
        layout.addWidget(self.txt_url)

        # 버튼 행
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.lbl_count = QLabel("0개 URL")
        self.lbl_count.setStyleSheet(f"color: {COLOR_TEXT_SUB}; font-size: 12px;")
        btn_row.addWidget(self.lbl_count)
        btn_row.addStretch()

        self.btn_clear = QPushButton("초기화")
        self.btn_clear.setFixedWidth(80)
        self.btn_clear.clicked.connect(self._on_clear)
        btn_row.addWidget(self.btn_clear)

        self.btn_collect = QPushButton("수집 시작")
        self.btn_collect.setObjectName("btn_collect")
        self.btn_collect.setFixedWidth(110)
        self.btn_collect.clicked.connect(self._on_collect)
        btn_row.addWidget(self.btn_collect)

        layout.addLayout(btn_row)

        # URL 변경 시 카운터 업데이트
        self.txt_url.textChanged.connect(self._update_count)

    # ────────────────────────────────────────
    def _on_collect(self):
        urls = self._get_urls()
        if urls:
            self.collect_requested.emit(urls)

    def _on_clear(self):
        self.txt_url.clear()
        self.clear_requested.emit()

    def _get_urls(self) -> list:
        """입력창에서 유효한 URL 목록 추출."""
        text = self.txt_url.toPlainText()
        urls = []
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("http"):
                urls.append(line)
        return urls

    def _update_count(self):
        urls = self._get_urls()
        self.lbl_count.setText(f"{len(urls)}개 URL")

    # ────────────────────────────────────────
    def set_collecting(self, active: bool):
        """수집 중 상태로 UI 잠금/해제."""
        self.btn_collect.setEnabled(not active)
        self.btn_clear.setEnabled(not active)
        self.txt_url.setReadOnly(active)
        if active:
            self.btn_collect.setText("수집 중...")
        else:
            self.btn_collect.setText("수집 시작")
