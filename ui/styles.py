"""
ui/styles.py — 다크 테마 QSS 스타일시트
"""

# 색상 팔레트
COLOR_BG = "#1e1e2e"
COLOR_SUB_BG = "#2a2a3d"
COLOR_SURFACE = "#313150"
COLOR_ACCENT = "#7c6af7"
COLOR_ACCENT_HOVER = "#9488ff"
COLOR_SUCCESS = "#4ade80"
COLOR_ERROR = "#f87171"
COLOR_WARNING = "#fbbf24"
COLOR_TEXT = "#e2e8f0"
COLOR_TEXT_SUB = "#94a3b8"
COLOR_BORDER = "#3d3d5c"
COLOR_TABLE_ROW_ALT = "#252538"
COLOR_TABLE_HEADER = "#2a2a3d"
COLOR_SELECTION = "#7c6af755"


STYLESHEET = f"""
/* ── 전체 배경 ── */
QWidget {{
    background-color: {COLOR_BG};
    color: {COLOR_TEXT};
    font-family: 'Pretendard', 'Segoe UI', sans-serif;
    font-size: 13px;
}}

/* ── 메인 윈도우 ── */
QMainWindow {{
    background-color: {COLOR_BG};
}}

/* ── 그룹박스 ── */
QGroupBox {{
    background-color: {COLOR_SUB_BG};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    margin-top: 8px;
    padding: 12px;
    font-size: 13px;
    font-weight: 600;
    color: {COLOR_TEXT};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {COLOR_ACCENT};
}}

/* ── 텍스트 입력 ── */
QTextEdit, QLineEdit, QPlainTextEdit {{
    background-color: {COLOR_SURFACE};
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 8px 10px;
    selection-background-color: {COLOR_ACCENT};
    font-size: 13px;
}}
QTextEdit:focus, QLineEdit:focus, QPlainTextEdit:focus {{
    border: 1px solid {COLOR_ACCENT};
}}
QTextEdit::placeholder, QLineEdit::placeholder {{
    color: {COLOR_TEXT_SUB};
}}

/* ── 버튼 — 기본 ── */
QPushButton {{
    background-color: {COLOR_SURFACE};
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 7px 18px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {COLOR_BORDER};
    border-color: {COLOR_ACCENT};
}}
QPushButton:pressed {{
    background-color: {COLOR_ACCENT};
    color: #fff;
}}
QPushButton:disabled {{
    color: {COLOR_TEXT_SUB};
    border-color: {COLOR_BORDER};
    background-color: {COLOR_SUB_BG};
}}

/* ── 버튼 — 강조(수집 시작) ── */
QPushButton#btn_collect {{
    background-color: {COLOR_ACCENT};
    color: #fff;
    font-weight: 700;
    border: none;
    padding: 8px 24px;
}}
QPushButton#btn_collect:hover {{
    background-color: {COLOR_ACCENT_HOVER};
}}
QPushButton#btn_collect:disabled {{
    background-color: {COLOR_SURFACE};
    color: {COLOR_TEXT_SUB};
}}

/* ── 버튼 — 위험(삭제) ── */
QPushButton#btn_delete {{
    color: {COLOR_ERROR};
    border-color: {COLOR_ERROR}44;
}}
QPushButton#btn_delete:hover {{
    background-color: {COLOR_ERROR}22;
    border-color: {COLOR_ERROR};
}}

/* ── 탭 버튼 (필터 바) ── */
QPushButton[tab_btn="true"] {{
    background-color: transparent;
    border: 1px solid {COLOR_BORDER};
    border-radius: 20px;
    padding: 5px 16px;
    font-size: 12px;
    color: {COLOR_TEXT_SUB};
}}
QPushButton[tab_btn="true"]:hover {{
    border-color: {COLOR_ACCENT};
    color: {COLOR_TEXT};
}}
QPushButton[tab_btn="true"][active="true"] {{
    background-color: {COLOR_ACCENT};
    border-color: {COLOR_ACCENT};
    color: #fff;
    font-weight: 600;
}}

/* ── 테이블 ── */
QTableWidget {{
    background-color: {COLOR_SUB_BG};
    alternate-background-color: {COLOR_TABLE_ROW_ALT};
    gridline-color: {COLOR_BORDER};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    font-family: 'Consolas', 'Pretendard', monospace;
    font-size: 12px;
    selection-background-color: {COLOR_SELECTION};
    selection-color: {COLOR_TEXT};
}}
QTableWidget::item {{
    padding: 6px 8px;
    border-bottom: 1px solid {COLOR_BORDER};
}}
QTableWidget::item:selected {{
    background-color: {COLOR_SELECTION};
    color: {COLOR_TEXT};
}}
QHeaderView::section {{
    background-color: {COLOR_TABLE_HEADER};
    color: {COLOR_TEXT_SUB};
    font-size: 12px;
    font-weight: 600;
    border: none;
    border-right: 1px solid {COLOR_BORDER};
    border-bottom: 1px solid {COLOR_BORDER};
    padding: 6px 8px;
}}
QHeaderView::section:checked {{
    background-color: {COLOR_SURFACE};
}}

/* ── 스크롤바 ── */
QScrollBar:vertical {{
    background: {COLOR_SUB_BG};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {COLOR_BORDER};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLOR_ACCENT};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background: {COLOR_SUB_BG};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {COLOR_BORDER};
    border-radius: 4px;
    min-width: 20px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {COLOR_ACCENT};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ── 프로그레스바 ── */
QProgressBar {{
    background-color: {COLOR_SURFACE};
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background-color: {COLOR_ACCENT};
    border-radius: 4px;
}}

/* ── 상태바 ── */
QStatusBar {{
    background-color: {COLOR_SUB_BG};
    color: {COLOR_TEXT_SUB};
    border-top: 1px solid {COLOR_BORDER};
    font-size: 12px;
}}

/* ── 라벨 ── */
QLabel {{
    color: {COLOR_TEXT};
    background: transparent;
}}
QLabel#label_title {{
    font-size: 18px;
    font-weight: 700;
    color: {COLOR_TEXT};
}}
QLabel#label_sub {{
    font-size: 12px;
    color: {COLOR_TEXT_SUB};
}}

/* ── 콤보박스 ── */
QComboBox {{
    background-color: {COLOR_SURFACE};
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 5px 10px;
}}
QComboBox:hover {{
    border-color: {COLOR_ACCENT};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background-color: {COLOR_SURFACE};
    color: {COLOR_TEXT};
    selection-background-color: {COLOR_ACCENT};
    border: 1px solid {COLOR_BORDER};
}}

/* ── 체크박스 ── */
QCheckBox {{
    color: {COLOR_TEXT};
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {COLOR_BORDER};
    border-radius: 3px;
    background: {COLOR_SURFACE};
}}
QCheckBox::indicator:checked {{
    background: {COLOR_ACCENT};
    border-color: {COLOR_ACCENT};
}}

/* ── 구분선 ── */
QFrame[frameShape="4"], QFrame[frameShape="HLine"] {{
    color: {COLOR_BORDER};
}}

/* ── 툴팁 ── */
QToolTip {{
    background-color: {COLOR_SURFACE};
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    padding: 4px 8px;
}}
"""


def get_platform_badge_color(platform: str) -> str:
    """플랫폼별 배지 색상 반환."""
    return {
        "쿠팡": "#e63312",
        "스마트스토어": "#03c75a",
        "네이버쇼핑": "#1ec800",
    }.get(platform, COLOR_ACCENT)
