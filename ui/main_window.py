"""
ui/main_window.py — 메인 윈도우

QThread 기반 스크래핑 워커와 전체 레이아웃 조합.
"""
import traceback
from typing import List, Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QProgressBar, QStatusBar, QSplitter,
    QMessageBox, QFrame, QFileDialog,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QIcon

from db.models import Product
from db.database import init_db, save_product, delete_products, get_all_products, clear_all
from scrapers.base import detect_platform
from scrapers import get_scraper
from parser.ai_parser import AIParser
from ui.input_panel import InputPanel
from ui.result_table import ResultTable
from ui.styles import STYLESHEET, COLOR_ACCENT, COLOR_TEXT_SUB, COLOR_ERROR, COLOR_SUCCESS
from export.excel_exporter import export_excel
from export.csv_exporter import export_csv


# ════════════════════════════════════════════════
class ScraperWorker(QObject):
    """
    QThread에서 실행되는 스크래핑 워커.
    각 URL을 순서대로 처리하고 시그널로 결과를 전달한다.
    """
    product_ready = pyqtSignal(Product)   # 단건 완료
    progress = pyqtSignal(int, int, str)  # current, total, message
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, urls: List[str]):
        super().__init__()
        self.urls = urls
        self._cancelled = False
        self._ai_parser = AIParser()

    def cancel(self):
        self._cancelled = True

    def run(self):
        total = len(self.urls)
        for i, url in enumerate(self.urls, 1):
            if self._cancelled:
                break
            self.progress.emit(i - 1, total, f"수집 중... ({i}/{total}) {url[:60]}")
            try:
                platform = detect_platform(url)
                if not platform:
                    product = Product.error_product(url, "알 수 없음", "지원하지 않는 URL입니다.")
                else:
                    scraper = get_scraper(platform)
                    if scraper is None:
                        product = Product.error_product(url, platform, "스크래퍼 없음")
                    else:
                        product = scraper.scrape(url)

                        # AI 파싱으로 누락 필드 보완 (영양성분 우선)
                        if self._ai_parser.is_available() and product.status == "success":
                            raw_text = product.nutrition_raw or product.name or ""
                            product = self._ai_parser.parse(raw_text, product)

                # DB 저장
                if product.status == "success" or product.status == "error":
                    pid = save_product(product)
                    product.id = pid

                self.product_ready.emit(product)
                self.progress.emit(i, total, f"완료: {product.name or url[:40]}")

            except Exception as exc:
                tb = traceback.format_exc()
                self.error.emit(f"예외 발생: {url}\n{tb}")
                err_product = Product.error_product(url, detect_platform(url) or "알 수 없음", str(exc))
                pid = save_product(err_product)
                err_product.id = pid
                self.product_ready.emit(err_product)

        self.finished.emit()


# ════════════════════════════════════════════════
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("경쟁사 상품 리서치 도구")
        self.setMinimumSize(1280, 760)
        self.resize(1440, 860)

        # 다크 테마
        self.setStyleSheet(STYLESHEET)

        # DB 초기화
        init_db()

        self._thread: Optional[QThread] = None
        self._worker: Optional[ScraperWorker] = None
        self._all_products: List[Product] = []

        self._build_ui()
        self._load_from_db()

    # ────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 12, 16, 8)
        root.setSpacing(10)

        # ── 타이틀 바
        title_row = QHBoxLayout()
        icon_lbl = QLabel("🔍")
        icon_lbl.setFont(QFont("Segoe UI Emoji", 22))
        title_row.addWidget(icon_lbl)

        title = QLabel("경쟁사 상품 리서치 도구")
        title.setObjectName("label_title")
        title.setFont(QFont("Pretendard", 18, QFont.Weight.Bold))
        title_row.addWidget(title)

        sub = QLabel("쿠팡 · 스마트스토어 · 네이버쇼핑")
        sub.setObjectName("label_sub")
        sub.setFont(QFont("Pretendard", 12))
        sub.setStyleSheet(f"color: {COLOR_TEXT_SUB}; margin-left: 8px;")
        title_row.addWidget(sub)
        title_row.addStretch()

        self.lbl_ai_status = QLabel()
        self._update_ai_label()
        title_row.addWidget(self.lbl_ai_status)

        root.addLayout(title_row)

        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(line)

        # ── 입력 패널
        self.input_panel = InputPanel()
        self.input_panel.collect_requested.connect(self._start_collecting)
        self.input_panel.clear_requested.connect(self._on_clear_input)
        root.addWidget(self.input_panel)

        # ── 결과 테이블
        self.result_table = ResultTable()
        self.result_table.btn_excel.clicked.connect(self._export_excel)
        self.result_table.btn_csv.clicked.connect(self._export_csv)
        self.result_table.delete_requested.connect(self._on_delete)
        root.addWidget(self.result_table, stretch=1)

        # ── 프로그레스 바 + 상태
        bottom = QHBoxLayout()
        bottom.setSpacing(10)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        bottom.addWidget(self.progress_bar, stretch=1)

        self.lbl_status = QLabel("준비")
        self.lbl_status.setStyleSheet(f"color: {COLOR_TEXT_SUB}; font-size: 12px;")
        bottom.addWidget(self.lbl_status)

        self.btn_cancel = QPushButton("중단")  # type: ignore
        from PyQt6.QtWidgets import QPushButton as _QB
        self.btn_cancel = _QB("중단")
        self.btn_cancel.setFixedWidth(60)
        self.btn_cancel.setVisible(False)
        self.btn_cancel.clicked.connect(self._cancel_collecting)
        bottom.addWidget(self.btn_cancel)

        root.addLayout(bottom)

    # ────────────────────────────────────────
    def _update_ai_label(self):
        import os
        from dotenv import load_dotenv
        load_dotenv()
        key = os.getenv("ANTHROPIC_API_KEY", "")
        if key:
            self.lbl_ai_status.setText("AI 파싱 ● 활성")
            self.lbl_ai_status.setStyleSheet(f"color: {COLOR_SUCCESS}; font-size: 12px;")
        else:
            self.lbl_ai_status.setText("AI 파싱 ○ 비활성")
            self.lbl_ai_status.setStyleSheet(f"color: {COLOR_TEXT_SUB}; font-size: 12px;")

    def _load_from_db(self):
        """앱 시작 시 저장된 상품 로드."""
        try:
            products = get_all_products()
            self._all_products = products
            self.result_table.set_products(products)
            self._set_status(f"DB에서 {len(products)}개 상품 로드됨")
        except Exception as exc:
            self._set_status(f"DB 로드 실패: {exc}", error=True)

    # ────────────────────────────────────────
    def _start_collecting(self, urls: List[str]):
        if self._thread and self._thread.isRunning():
            return

        self.input_panel.set_collecting(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(urls))
        self.progress_bar.setValue(0)
        self.btn_cancel.setVisible(True)
        self._set_status(f"수집 시작 ({len(urls)}개 URL)")

        self._worker = ScraperWorker(urls)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.product_ready.connect(self._on_product_ready)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def _cancel_collecting(self):
        if self._worker:
            self._worker.cancel()
        self._set_status("수집 중단 요청됨", error=True)

    # ────────────────────────────────────────
    def _on_product_ready(self, product: Product):
        self._all_products.append(product)
        self.result_table.add_product(product)

    def _on_progress(self, current: int, total: int, message: str):
        self.progress_bar.setValue(current)
        self._set_status(message)

    def _on_finished(self):
        self.input_panel.set_collecting(False)
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.btn_cancel.setVisible(False)
        success = sum(1 for p in self._all_products if p.status == "success")
        errors = sum(1 for p in self._all_products if p.status == "error")
        self._set_status(
            f"수집 완료 — 성공 {success}개  실패 {errors}개",
            success=(errors == 0),
        )
        # 잠시 후 프로그레스바 숨기기
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(3000, lambda: self.progress_bar.setVisible(False))

    def _on_error(self, msg: str):
        self._set_status(f"오류: {msg[:80]}", error=True)

    def _on_clear_input(self):
        pass

    # ────────────────────────────────────────
    def _on_delete(self, ids: List[int]):
        reply = QMessageBox.question(
            self,
            "삭제 확인",
            f"{len(ids)}개 상품을 삭제할까요?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        delete_products(ids)
        self._all_products = [p for p in self._all_products if p.id not in ids]
        self.result_table.set_products(self._all_products)
        self._set_status(f"{len(ids)}개 상품 삭제됨")

    # ────────────────────────────────────────
    def _export_excel(self):
        products = self.result_table.get_visible_products()
        if not products:
            QMessageBox.information(self, "알림", "내보낼 데이터가 없습니다.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Excel 저장", "상품리서치.xlsx", "Excel (*.xlsx)"
        )
        if path:
            try:
                export_excel(products, path)
                self._set_status(f"Excel 저장 완료: {path}", success=True)
            except Exception as exc:
                QMessageBox.critical(self, "오류", str(exc))

    def _export_csv(self):
        products = self.result_table.get_visible_products()
        if not products:
            QMessageBox.information(self, "알림", "내보낼 데이터가 없습니다.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "CSV 저장", "상품리서치.csv", "CSV (*.csv)"
        )
        if path:
            try:
                export_csv(products, path)
                self._set_status(f"CSV 저장 완료: {path}", success=True)
            except Exception as exc:
                QMessageBox.critical(self, "오류", str(exc))

    # ────────────────────────────────────────
    def _set_status(self, msg: str, error: bool = False, success: bool = False):
        if error:
            color = COLOR_ERROR
        elif success:
            color = COLOR_SUCCESS
        else:
            color = COLOR_TEXT_SUB
        self.lbl_status.setText(msg)
        self.lbl_status.setStyleSheet(f"color: {color}; font-size: 12px;")

    def closeEvent(self, event):
        if self._thread and self._thread.isRunning():
            if self._worker:
                self._worker.cancel()
            self._thread.quit()
            self._thread.wait(3000)
        event.accept()
