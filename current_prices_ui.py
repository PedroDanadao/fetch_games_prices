import os
from pathlib import Path
import platform
import subprocess
from PyQt5 import QtWidgets, QtGui, QtCore

import current_prices

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(THIS_FOLDER, "icons", "window_icon.png")


class PriceWorker(QtCore.QThread):
    """Worker thread for fetching game prices without blocking the UI."""
    
    # Signals
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
            driver = current_prices.start_chrome_driver()
            
            total_games = len(self.games_to_check)
            
            for i, (game_name, game_url) in enumerate(self.games_to_check.items(), 1):
                self.progress_updated.emit(f"Fetching prices for {game_name} ({i}/{total_games})...")
                
                try:
                    current_prices_dict = current_prices.get_game_prices(game_name, driver)
                    
                    game_data = {
                        "steam": {
                            "current": self.convert_to_float(current_prices_dict.get("Steam_current", "0,0")),
                            "base": self.convert_to_float(current_prices_dict.get("Steam_base", "0,0")),
                            "link": current_prices_dict.get("Steam_link")
                        },
                        "gog": {
                            "current": self.convert_to_float(current_prices_dict.get("GOG_current", "0,0")),
                            "base": self.convert_to_float(current_prices_dict.get("GOG_base", "0,0")),
                            "link": current_prices_dict.get("GOG_link")
                        },
                        "is_there_any_deal_link": current_prices_dict.get("is_there_any_deal_link")
                    }
                    
                    self.price_updated.emit(game_name, game_data)
                    
                except Exception as e:
                    self.error_occurred.emit(f"Error fetching prices for {game_name}: {str(e)}")
                    
            self.progress_updated.emit("Closing Chrome driver...")
            current_prices.exit_chrome_driver(driver)
            
            self.progress_updated.emit("All prices updated!")
            self.finished_all.emit()
            
        except Exception as e:
            self.error_occurred.emit(f"Critical error: {str(e)}")
    
    def convert_to_float(self, price_str):
        """Convert price string to float."""
        try:
            float_value = float(price_str.replace(',', '.')) if price_str else 0.0
        except ValueError:
            float_value = 0.0

        return float_value

class CurrentPricesUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()
        self.update_prices()

    def init_ui(self):
        self.setWindowTitle("Current Prices")
        self.setGeometry(100, 100, 1200, 800)

        window_icon = QtGui.QIcon(ICON_PATH)
        self.setWindowIcon(window_icon)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        # Add status label
        self.status_label = QtWidgets.QLabel("Ready")
        self.status_label.setStyleSheet("padding: 5px; background-color: #f0f0f0; border: 1px solid #ccc;")
        layout.addWidget(self.status_label)

        # Add refresh button
        button_layout = QtWidgets.QHBoxLayout()
        self.refresh_button = QtWidgets.QPushButton("Refresh Prices")
        self.refresh_button.clicked.connect(self.update_prices)
        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Add open json folder
        self.open_data_folder_button = QtWidgets.QPushButton("Open Json Folder")
        self.open_data_folder_button.clicked.connect(self.open_data_folder)
        button_layout.addWidget(self.open_data_folder_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.prices_tree_widget = QtWidgets.QTreeWidget()
        self.prices_tree_widget.setHeaderLabels(["Game", "Steam Current", "Steam Base", "Steam Discount", "GOG Current", "GOG Base", "GOG Discount"])
        
        # Set dark theme for tree widget
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

        # Context menu for copying links
        self.prices_tree_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.prices_tree_widget.customContextMenuRequested.connect(self.open_context_menu)

        layout.addWidget(self.prices_tree_widget)

    def update_prices(self):
        """Start the price update process in a worker thread."""
        if self.worker and self.worker.isRunning():
            return
            
        self.prices_tree_widget.clear()
        self.refresh_button.setEnabled(False)
        self.status_label.setText("Initializing...")
        
        self.worker = PriceWorker()
        self.worker.set_games(current_prices.GAMES_TO_CHECK)
        
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
        """Handle when a single game's price is updated."""
        item = QtWidgets.QTreeWidgetItem([game_name])

        number_of_items = len(self.prices_tree_widget.children())
        if number_of_items % 2 == 0:
            bg_color = QtGui.QColor("#ffffff")
        else:
            bg_color = QtGui.QColor("#ffffff")

        steam_base = self.convert_to_str(price_info["steam"]["base"])
        gog_base = self.convert_to_str(price_info["gog"]["base"])
        steam_base = steam_base if steam_base != "0,00    " else ""
        gog_base = gog_base if gog_base != "0,00    " else ""

        steam_current = self.convert_to_str(price_info["steam"]["current"])
        gog_current = self.convert_to_str(price_info["gog"]["current"])
        steam_current = steam_current if steam_current != "0,00    " else ""
        gog_current = gog_current if gog_current != "0,00    " else ""

        steam_discount = self.get_discount_string(price_info["steam"]["current"],
                                                   price_info["steam"]["base"])
        gog_discount = self.get_discount_string(price_info["gog"]["current"],
                                                   price_info["gog"]["base"])

        item.setText(1, steam_current)
        item.setText(2, steam_base)
        item.setText(3, steam_discount)
        item.setText(4, gog_current)
        item.setText(5, gog_base)
        item.setText(6, gog_discount)

        item.setForeground(3, QtGui.QBrush(QtGui.QColor("#30fc4b")))
        item.setForeground(6, QtGui.QBrush(QtGui.QColor("#30fc4b")))

        if price_info["steam"]["current"] < price_info["steam"]["base"]:
            item.setForeground(1, QtGui.QBrush(QtGui.QColor("#5186f8")))
        if price_info["gog"]["current"] < price_info["gog"]["base"]:
            item.setForeground(4, QtGui.QBrush(QtGui.QColor("#5186f8")))

        self.prices_tree_widget.setColumnWidth(0, 300)

        for i in range(1, 7):
            item.setTextAlignment(i, QtCore.Qt.AlignRight)

        # Store links for context menu
        item.setData(0, QtCore.Qt.UserRole, {
            "steam_link": price_info["steam"].get("link"),
            "gog_link": price_info["gog"].get("link"),
            "itad_link": price_info.get("is_there_any_deal_link")
        })

        self.prices_tree_widget.addTopLevelItem(item)

    def open_context_menu(self, point):
        item = self.prices_tree_widget.itemAt(point)
        if not item:
            return
        links = item.data(0, QtCore.Qt.UserRole) or {}
        steam_link = links.get("steam_link")
        gog_link = links.get("gog_link")
        itad_link = links.get("itad_link")

        menu = QtWidgets.QMenu(self)

        if steam_link:
            act_steam = menu.addAction("Copy Steam link")
            act_steam.triggered.connect(lambda: self.copy_link(steam_link))
        if gog_link:
            act_gog = menu.addAction("Copy GOG link")
            act_gog.triggered.connect(lambda: self.copy_link(gog_link))

        if any([steam_link, gog_link]):
            menu.addSeparator()
        
        if itad_link:
            act_itad = menu.addAction("Copy IsThereAnyDeal link")
            act_itad.triggered.connect(lambda: self.copy_link(itad_link))

        if not any([steam_link, gog_link, itad_link]):
            disabled = menu.addAction("No links available")
            disabled.setEnabled(False)

        menu.exec_(self.prices_tree_widget.viewport().mapToGlobal(point))

    def copy_link(self, link_text):
        if not link_text:
            return
        QtWidgets.QApplication.clipboard().setText(link_text)
        self.status_label.setText("Link copied to clipboard")

    def get_discount_string(self, current_price, base_price):
        """Calculate and return the discount string."""
        if base_price > 0 and current_price < base_price:
            discount_value = round(base_price - current_price, 2)
            discount_percentage = round(discount_value / base_price * 100)
            return f"{discount_value:.2f} ({discount_percentage}%)   ".replace('.', ',')
        
        return ""

    def on_progress_updated(self, message):
        """Handle progress updates from the worker thread."""
        self.status_label.setText(message)

    def on_finished_all(self):
        """Handle when all prices have been fetched."""
        self.refresh_button.setEnabled(True)
        self.status_label.setText("All prices updated successfully!")

    def on_error_occurred(self, error_message):
        """Handle errors from the worker thread."""
        self.status_label.setText(f"Error: {error_message}")
        self.refresh_button.setEnabled(True)
        QtWidgets.QMessageBox.warning(self, "Error", error_message)

    def closeEvent(self, event):
        """Handle window close event - ensure worker thread is properly terminated."""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        event.accept()

    def convert_to_float(self, price_str):
        """Convert price string to float."""
        return float(price_str.replace(',', '.')) if price_str else 0.0
    
    def convert_to_str(self, price_float):
        """Convert float to price string with comma as decimal separator."""
        if price_float:
            formatted = f"{price_float:.2f}".replace('.', ',')
            return formatted + "    "
        return "0,00    "


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = CurrentPricesUI()
    window.show()
    sys.exit(app.exec_())
