import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QIcon, QPalette, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSystemTrayIcon,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from booking_config import load_schedule, save_schedule
from booking_scheduler import BookingScheduler


ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
SCHEDULE_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("USC Padel Booking")
        self.setMinimumSize(860, 540)

        self.scheduler = BookingScheduler()

        self._init_ui()
        self._init_tray()
        self._update_ui()

    def _init_ui(self) -> None:
        central = QWidget()
        central.setObjectName("central")
        central.setAutoFillBackground(True)
        palette = central.palette()
        palette.setColor(QPalette.Window, QColor("#0b1221"))
        central.setPalette(palette)
        self.setCentralWidget(central)

        self.background_label = QLabel(central)
        self.background_label.setAlignment(Qt.AlignCenter)
        self.background_label.setAttribute(Qt.WA_TransparentForMouseEvents)

        self._background_pixmap = QPixmap()
        background_path = self._asset_path("background_usc.svg")
        if os.path.exists(background_path):
            self._background_pixmap.load(background_path)

        title = QLabel("USC Padel Booking Controller")
        title.setStyleSheet("color: #ffffff; font-size: 22px; font-weight: 700;")
        title.setAlignment(Qt.AlignCenter)

        robot_label = QLabel()
        robot_path = self._asset_path("robot_racket.svg")
        robot_pixmap = QPixmap()
        if os.path.exists(robot_path):
            robot_pixmap.load(robot_path)
        if robot_pixmap.isNull():
            robot_label.setText("USC Padel Booking")
            robot_label.setStyleSheet("color: #ffffff; font-size: 16px;")
        else:
            robot_label.setPixmap(
                robot_pixmap.scaled(220, 260, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        robot_label.setAlignment(Qt.AlignCenter)

        self.run_background_checkbox = QCheckBox("Run in background")
        self.run_background_checkbox.setStyleSheet("color: #ffffff; font-size: 16px;")

        self.start_stop_button = QPushButton("Start booking")
        self.start_stop_button.setFixedWidth(200)
        self.start_stop_button.setStyleSheet(
            "QPushButton { background-color: #f2c94c; font-size: 16px; font-weight: 600; padding: 10px; }"
        )
        self.start_stop_button.clicked.connect(self._toggle_booking)

        self.status_label = QLabel("Scheduler stopped")
        self.status_label.setStyleSheet("color: #ffffff; font-size: 14px;")
        self.status_label.setAlignment(Qt.AlignCenter)

        schedule_group = QGroupBox("Booking schedule")
        schedule_group.setStyleSheet(
            "QGroupBox { color: #ffffff; font-size: 16px; font-weight: 600; }"
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; }"
        )
        schedule_layout = QVBoxLayout(schedule_group)

        self.schedule_table = QTableWidget(0, 3)
        self.schedule_table.setHorizontalHeaderLabels(["Day", "Check time", "Book time"])
        self.schedule_table.verticalHeader().setVisible(False)
        self.schedule_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.schedule_table.setStyleSheet(
            "QTableWidget { background-color: #ffffff; color: #111827; }"
            "QHeaderView::section { background-color: #f2c94c; color: #111827; font-weight: 600; }"
        )

        schedule_button_row = QHBoxLayout()
        self.add_schedule_button = QPushButton("Add slot")
        self.remove_schedule_button = QPushButton("Remove selected")
        self.save_schedule_button = QPushButton("Save schedule")
        self.add_schedule_button.clicked.connect(self._add_schedule_row)
        self.remove_schedule_button.clicked.connect(self._remove_schedule_rows)
        self.save_schedule_button.clicked.connect(self._save_schedule)
        schedule_button_row.addWidget(self.add_schedule_button)
        schedule_button_row.addWidget(self.remove_schedule_button)
        schedule_button_row.addWidget(self.save_schedule_button)

        schedule_layout.addWidget(self.schedule_table)
        schedule_layout.addLayout(schedule_button_row)

        controls_layout = QVBoxLayout()
        controls_layout.addWidget(self.run_background_checkbox, alignment=Qt.AlignCenter)
        controls_layout.addWidget(self.start_stop_button, alignment=Qt.AlignCenter)
        controls_layout.addWidget(self.status_label, alignment=Qt.AlignCenter)
        controls_layout.setSpacing(12)

        content_layout = QHBoxLayout()
        content_layout.addWidget(robot_label, stretch=1)
        content_layout.addLayout(controls_layout, stretch=1)
        content_layout.setContentsMargins(40, 20, 40, 40)

        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        main_layout.addWidget(title)
        main_layout.addLayout(content_layout)
        main_layout.addWidget(schedule_group)

        overlay_layout = QGridLayout(central)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.addWidget(self.background_label, 0, 0)
        overlay_layout.addWidget(content_widget, 0, 0)

        self._update_background_pixmap()
        self._load_schedule()

    def _init_tray(self) -> None:
        icon_path = self._asset_path("racket.svg")
        if not os.path.exists(icon_path):
            icon_path = self._asset_path("racket.png")
        if not os.path.exists(icon_path):
            icon_path = self._asset_path("robot_racket.svg")
        tray_icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
        self.tray_icon = QSystemTrayIcon(tray_icon, self)
        self.tray_icon.setToolTip("USC Padel Booking")

        self.tray_menu = QMenu()
        self.show_action = QAction("Show window")
        self.show_action.triggered.connect(self._show_window)
        self.start_stop_action = QAction("Start booking")
        self.start_stop_action.triggered.connect(self._toggle_booking)
        self.quit_action = QAction("Quit")
        self.quit_action.triggered.connect(self._quit_app)

        self.tray_menu.addAction(self.show_action)
        self.tray_menu.addAction(self.start_stop_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.quit_action)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)

        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon.show()

    def _update_ui(self) -> None:
        if self.scheduler.is_running():
            self.start_stop_button.setText("Stop booking")
            self.start_stop_action.setText("Stop booking")
            self.status_label.setText("Scheduler running")
        else:
            self.start_stop_button.setText("Start booking")
            self.start_stop_action.setText("Start booking")
            self.status_label.setText("Scheduler stopped")

    def _toggle_booking(self) -> None:
        if self.scheduler.is_running():
            self.scheduler.stop()
        else:
            try:
                self.scheduler.start()
            except ValueError as exc:
                QMessageBox.warning(self, "Missing credentials", str(exc))
        self._update_ui()

    def _load_schedule(self) -> None:
        self.schedule_table.setRowCount(0)
        for slot in load_schedule():
            self._add_schedule_row(slot)

    def _add_schedule_row(self, slot: dict | None = None) -> None:
        row = self.schedule_table.rowCount()
        self.schedule_table.insertRow(row)

        day_combo = QComboBox()
        day_combo.addItems(SCHEDULE_DAYS)
        day_value = slot.get("day") if slot else SCHEDULE_DAYS[0]
        if day_value in SCHEDULE_DAYS:
            day_combo.setCurrentText(day_value)
        self.schedule_table.setCellWidget(row, 0, day_combo)

        check_time_edit = QLineEdit()
        check_time_edit.setPlaceholderText("19:59:00")
        check_time_edit.setText(slot.get("check_time") if slot else "")
        self.schedule_table.setCellWidget(row, 1, check_time_edit)

        book_time_edit = QLineEdit()
        book_time_edit.setPlaceholderText("20:00:00")
        book_time_edit.setText(slot.get("book_time") if slot else "")
        self.schedule_table.setCellWidget(row, 2, book_time_edit)

    def _remove_schedule_rows(self) -> None:
        selected_rows = {index.row() for index in self.schedule_table.selectionModel().selectedRows()}
        for row in sorted(selected_rows, reverse=True):
            self.schedule_table.removeRow(row)

    def _save_schedule(self) -> None:
        slots: list[dict[str, str]] = []
        for row in range(self.schedule_table.rowCount()):
            day_combo = self.schedule_table.cellWidget(row, 0)
            check_time_edit = self.schedule_table.cellWidget(row, 1)
            book_time_edit = self.schedule_table.cellWidget(row, 2)
            if not isinstance(day_combo, QComboBox):
                continue
            if not isinstance(check_time_edit, QLineEdit) or not isinstance(book_time_edit, QLineEdit):
                continue
            day = day_combo.currentText().strip()
            check_time = check_time_edit.text().strip()
            book_time = book_time_edit.text().strip()
            if not day or not check_time or not book_time:
                continue
            slots.append({"day": day, "check_time": check_time, "book_time": book_time})
        if not slots:
            slots = load_schedule()
        save_schedule(slots)

    def _show_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _quit_app(self) -> None:
        self.scheduler.stop()
        QApplication.quit()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self._show_window()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_background_pixmap()

    def _asset_path(self, filename: str) -> str:
        return os.path.abspath(os.path.join(ASSETS_DIR, filename))

    def _update_background_pixmap(self) -> None:
        if self._background_pixmap.isNull():
            self.background_label.clear()
            return
        target_size = self.centralWidget().size()
        scaled = self._background_pixmap.scaled(
            target_size,
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation,
        )
        self.background_label.setPixmap(scaled)
        self.background_label.setMinimumSize(target_size)

    def closeEvent(self, event) -> None:
        if self.run_background_checkbox.isChecked() and QSystemTrayIcon.isSystemTrayAvailable():
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "USC Padel Booking",
                "App is still running in the background.",
                QSystemTrayIcon.Information,
                2000,
            )
            return
        self.scheduler.stop()
        event.accept()


def main() -> None:
    app = QApplication(sys.argv)  # CHANGED
    app.setQuitOnLastWindowClosed(True)  # CHANGED
    window = MainWindow()  # CHANGED
    window.show()  # CHANGED
    window.raise_()  # CHANGED
    window.activateWindow()  # CHANGED
    sys.exit(app.exec())  # CHANGED


if __name__ == "__main__":
    main()
