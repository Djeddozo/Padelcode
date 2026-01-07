import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from booking_scheduler import BookingScheduler


ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")


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
        self.setCentralWidget(central)

        background_path = os.path.join(ASSETS_DIR, "background_usc.svg")
        central.setStyleSheet(
            f"""
            QWidget#central {{
                background-image: url("{background_path}");
                background-position: center;
                background-repeat: no-repeat;
                background-color: #0b1221;
            }}
            """
        )

        title = QLabel("USC Padel Booking Controller")
        title.setStyleSheet("color: #ffffff; font-size: 22px; font-weight: 700;")
        title.setAlignment(Qt.AlignCenter)

        robot_label = QLabel()
        robot_pixmap = QPixmap(os.path.join(ASSETS_DIR, "robot_racket.svg"))
        robot_label.setPixmap(robot_pixmap.scaled(220, 260, Qt.KeepAspectRatio, Qt.SmoothTransformation))
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

        controls_layout = QVBoxLayout()
        controls_layout.addWidget(self.run_background_checkbox, alignment=Qt.AlignCenter)
        controls_layout.addWidget(self.start_stop_button, alignment=Qt.AlignCenter)
        controls_layout.addWidget(self.status_label, alignment=Qt.AlignCenter)
        controls_layout.setSpacing(12)

        content_layout = QHBoxLayout()
        content_layout.addWidget(robot_label, stretch=1)
        content_layout.addLayout(controls_layout, stretch=1)
        content_layout.setContentsMargins(40, 20, 40, 40)

        main_layout = QVBoxLayout(central)
        main_layout.addWidget(title)
        main_layout.addLayout(content_layout)

    def _init_tray(self) -> None:
        icon_path = os.path.join(ASSETS_DIR, "robot_racket.svg")
        self.tray_icon = QSystemTrayIcon(QIcon(icon_path), self)
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
            self.scheduler.start()
        self._update_ui()

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
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
