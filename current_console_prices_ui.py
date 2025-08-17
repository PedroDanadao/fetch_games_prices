import os
from pathlib import Path
import platform
import subprocess
from PyQt5 import QtWidgets, QtGui, QtCore

import current_prices_consoles

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(THIS_FOLDER, "icons", "window_icon.png")

# Global variable for price padding
PRICE_PADDING = " " * 3

class ConsolePriceWorker(QtCore.QThread):
    """Worker thread for fetching console game prices without blocking the UI."""
    price_updated = QtCore.pyqtSignal(str, dict)  # game_name, price_data
    progress_updated = QtCore.pyqtSignal(str)  # status message
    finished_all = QtCore.pyqtSignal()  # all prices fetched
    error_occurred = QtCore.pyqtSignal(str)  # error message

    def __init__(self):
        super().__init__()
        self.games_to_check = {}
    
    def set_games(self, games_dict):
        """Set the games dictionary to check."""
        self.games_to_check = games_dict
    
    def run(self):
        """Main worker thread function."""
        try:
            self.progress_updated.emit("Starting Chrome driver...")
            driver = current_prices_consoles.start_chrome_driver()
            total_games = len(self.games_to_check)
            for i, (game_name, sites) in enumerate(self.games_to_check.items(), 1):
                self.progress_updated.emit(f"Fetching prices for {game_name} ({i}/{total_games})...")
                try:
                    price_data = {}
                    # PSN
                    if sites.get("psn_site"):
                        try:
                            base, current = current_prices_consoles.get_psn_prices(game_name, driver)
                            price_data["psn"] = {
                                "current": self.convert_to_float(current[0]) if current else 0.0,
                                "base": self.convert_to_float(base[0]) if base else 0.0,
                                "link": sites.get("psn_site")
                            }
                        except Exception as e:
                            price_data["psn"] = {"current": 0.0, "base": 0.0, "link": sites.get("psn_site"), "error": str(e)}
                    # Xbox
                    if sites.get("xbox_site"):
                        try:
                            base, current = current_prices_consoles.get_xbox_prices(game_name, driver)
                            price_data["xbox"] = {
                                "current": self.convert_to_float(current) if current else 0.0,
                                "base": self.convert_to_float(base) if base else 0.0,
                                "link": sites.get("xbox_site")
                            }
                        except Exception as e:
                            price_data["xbox"] = {"current": 0.0, "base": 0.0, "link": sites.get("xbox_site"), "error": str(e)}
                    # Nintendo
                    if sites.get("nintendo_site"):
                        try:
                            base, current = current_prices_consoles.get_nintendo_prices(game_name, driver)
                            price_data["nintendo"] = {
                                "current": self.convert_to_float(current) if current else 0.0,
                                "base": self.convert_to_float(base) if base else 0.0,
                                "link": sites.get("nintendo_site")
                            }
                        except Exception as e:
                            price_data["nintendo"] = {"current": 0.0, "base": 0.0, "link": sites.get("nintendo_site"), "error": str(e)}
                    self.price_updated.emit(game_name, price_data)
                except Exception as e:
                    self.error_occurred.emit(f"Error fetching prices for {game_name}: {str(e)}")
            self.progress_updated.emit("Closing Chrome driver...")
            current_prices_consoles.exit_chrome_driver(driver)
            self.progress_updated.emit("All prices updated!")
            self.finished_all.emit()
        except Exception as e:
            self.error_occurred.emit(f"Critical error: {str(e)}")
    def convert_to_float(self, price_str):
        try:
            return float(price_str.replace(',', '.')) if price_str else 0.0
        except Exception:
            return 0.0

class CurrentConsolePricesUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()
        self.update_prices()

    def init_ui(self):
        self.setWindowTitle("Current Console Prices")
        self.setGeometry(100, 100, 1300, 800)
        window_icon = QtGui.QIcon(ICON_PATH)
        self.setWindowIcon(window_icon)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        self.status_label = QtWidgets.QLabel("Ready")
        self.status_label.setStyleSheet("padding: 5px; background-color: #f0f0f0; border: 1px solid #ccc;")
        layout.addWidget(self.status_label)
        button_layout = QtWidgets.QHBoxLayout()
        self.refresh_button = QtWidgets.QPushButton("Refresh Prices")
        self.refresh_button.clicked.connect(self.update_prices)
        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()
        self.open_data_folder_button = QtWidgets.QPushButton("Open Json Folder")
        self.open_data_folder_button.clicked.connect(self.open_data_folder)
        button_layout.addWidget(self.open_data_folder_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        self.prices_tree_widget = QtWidgets.QTreeWidget()
        self.prices_tree_widget.setHeaderLabels([
            "Game", "|",
            "PSN Current", "PSN Base", "PSN Discount", "|",
            "Xbox Current", "Xbox Base", "Xbox Discount", "|",
            "Nintendo Current", "Nintendo Base", "Nintendo Discount"
        ])
        # Dark theme styling (copied from current_prices_ui.py)
        self.prices_tree_widget.setStyleSheet("""
            QTreeWidget {
                background-color: #1a1a1a;
                alternate-background-color: #292928;
                color: white;
                gridline-color: #333333;
                outline: 0;
                border: 1px solid #333333;
            }
            QTreeWidget::item {
                height: 25px;
                border: none;
            }
            QTreeWidget::item:selected {
                background-color: #404040;
            }
            QTreeWidget::item:hover {
                background-color: #2d2d2d;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: white;
                padding: 5px;
                border: 1px solid #333333;
                font-weight: bold;
            }
        """)
        self.prices_tree_widget.setAlternatingRowColors(True)
        self.prices_tree_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.prices_tree_widget.customContextMenuRequested.connect(self.open_context_menu)
        
        layout.addWidget(self.prices_tree_widget)
        # Set column widths for separators to 2px (after widget is added)
        self.prices_tree_widget.setColumnWidth(1, 2)   # Separator after Game
        self.prices_tree_widget.setColumnWidth(5, 2)   # Separator after PSN
        self.prices_tree_widget.setColumnWidth(9, 2)   # Separator after Xbox

    def update_prices(self):
        if self.worker and self.worker.isRunning():
            return
        self.prices_tree_widget.clear()
        self.refresh_button.setEnabled(False)
        self.status_label.setText("Initializing...")
        self.worker = ConsolePriceWorker()
        self.worker.set_games(current_prices_consoles.GAMES_TO_CHECK)
        self.worker.price_updated.connect(self.on_price_updated)
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.finished_all.connect(self.on_finished_all)
        self.worker.error_occurred.connect(self.on_error_occurred)
        self.worker.start()

    def open_data_folder(self):
        folder = Path.home() / ".current_prices_data"
        folder.mkdir(parents=True, exist_ok=True)
        system = platform.system()
        if system == "Darwin":
            subprocess.run(["open", folder])
        elif system == "Windows":
            os.startfile(folder)
        else:
            subprocess.run(["xdg-open", folder])

    def on_price_updated(self, game_name, price_info):
        item = QtWidgets.QTreeWidgetItem([
            game_name, "|",
            self.convert_to_str(price_info.get("psn", {}).get("current", 0.0)),
            self.convert_to_str(price_info.get("psn", {}).get("base", 0.0)),
            self.get_discount_string(price_info.get("psn", {}).get("current", 0.0), price_info.get("psn", {}).get("base", 0.0)), "|",
            self.convert_to_str(price_info.get("xbox", {}).get("current", 0.0)),
            self.convert_to_str(price_info.get("xbox", {}).get("base", 0.0)),
            self.get_discount_string(price_info.get("xbox", {}).get("current", 0.0), price_info.get("xbox", {}).get("base", 0.0)), "|",
            self.convert_to_str(price_info.get("nintendo", {}).get("current", 0.0)),
            self.convert_to_str(price_info.get("nintendo", {}).get("base", 0.0)),
            self.get_discount_string(price_info.get("nintendo", {}).get("current", 0.0), price_info.get("nintendo", {}).get("base", 0.0))
        ])

        # Set colors: blue for current price if discount, green for discount columns
        blue = QtGui.QBrush(QtGui.QColor("#5186f8"))
        green = QtGui.QBrush(QtGui.QColor("#30fc4b"))
        # PSN
        psn_current_val = price_info.get("psn", {}).get("current", 0.0)
        psn_base_val = price_info.get("psn", {}).get("base", 0.0)
        if psn_current_val < psn_base_val:
            item.setForeground(2, blue)
        item.setForeground(4, green)
        # Xbox
        xbox_current_val = price_info.get("xbox", {}).get("current", 0.0)
        xbox_base_val = price_info.get("xbox", {}).get("base", 0.0)
        if xbox_current_val < xbox_base_val:
            item.setForeground(6, blue)
        item.setForeground(8, green)
        # Nintendo
        nintendo_current_val = price_info.get("nintendo", {}).get("current", 0.0)
        nintendo_base_val = price_info.get("nintendo", {}).get("base", 0.0)
        if nintendo_current_val < nintendo_base_val:
            item.setForeground(10, blue)
        item.setForeground(12, green)

        # Store links for context menu
        item.setData(0, QtCore.Qt.UserRole, {
            "psn_link": price_info.get("psn", {}).get("link"),
            "xbox_link": price_info.get("xbox", {}).get("link"),
            "nintendo_link": price_info.get("nintendo", {}).get("link")
        })
        self.prices_tree_widget.addTopLevelItem(item)

    def open_context_menu(self, point):
        item = self.prices_tree_widget.itemAt(point)
        if not item:
            return
        links = item.data(0, QtCore.Qt.UserRole) or {}
        psn_link = links.get("psn_link")
        xbox_link = links.get("xbox_link")
        nintendo_link = links.get("nintendo_link")
        menu = QtWidgets.QMenu(self)
        if psn_link:
            act_psn = menu.addAction("Copy PSN link")
            act_psn.triggered.connect(lambda: self.copy_link(psn_link))
        if xbox_link:
            act_xbox = menu.addAction("Copy Xbox link")
            act_xbox.triggered.connect(lambda: self.copy_link(xbox_link))
        if nintendo_link:
            act_nintendo = menu.addAction("Copy Nintendo link")
            act_nintendo.triggered.connect(lambda: self.copy_link(nintendo_link))
        if not any([psn_link, xbox_link, nintendo_link]):
            disabled = menu.addAction("No links available")
            disabled.setEnabled(False)
        menu.exec_(self.prices_tree_widget.viewport().mapToGlobal(point))

    def copy_link(self, link_text):
        if not link_text:
            return
        QtWidgets.QApplication.clipboard().setText(link_text)
        self.status_label.setText("Link copied to clipboard")

    def get_discount_string(self, current_price, base_price):
        if base_price > 0 and current_price < base_price:
            discount_value = round(base_price - current_price, 2)
            discount_percentage = round(discount_value / base_price * 100)
            return f"{discount_value:.2f} ({discount_percentage}%)   ".replace('.', ',')
        return ""

    def on_progress_updated(self, message):
        self.status_label.setText(message)

    def on_finished_all(self):
        self.refresh_button.setEnabled(True)
        self.status_label.setText("All prices updated successfully!")

    def on_error_occurred(self, error_message):
        self.status_label.setText(f"Error: {error_message}")
        self.refresh_button.setEnabled(True)
        QtWidgets.QMessageBox.warning(self, "Error", error_message)

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        event.accept()

    def convert_to_str(self, price_float):
        if price_float:
            formatted = f"{price_float:.2f}".replace('.', ',')
            return PRICE_PADDING + formatted
        return PRICE_PADDING

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = CurrentConsolePricesUI()
    window.showMaximized()
    sys.exit(app.exec_())
