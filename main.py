"""
main.py — 앱 진입점

경쟁사 상품 리서치 도구 (PyQt6 데스크탑 앱)
"""
import sys
import os

# Windows DPI 스케일링 설정 (PyQt6)
os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("경쟁사 상품 리서치 도구")
    app.setOrganizationName("ProductResearch")

    # 고DPI 지원
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    # 기본 폰트
    font = QFont("Pretendard", 13)
    font.setFallbackFamilies(["Malgun Gothic", "Segoe UI"])
    app.setFont(font)

    # 메인 윈도우 지연 임포트 (DB 초기화 포함)
    from ui.main_window import MainWindow

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
