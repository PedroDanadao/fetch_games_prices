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
        self.showing_only_discounted = False
        self.games_data = {}  # Store game data: {game_name: {psn_data, xbox_data, nintendo_data, links}}
        self.games_order = []  # Store original order of game names
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
        
        self.show_discounted_button = QtWidgets.QPushButton("Show Only Discounted")
        self.show_discounted_button.setEnabled(False)
        self.show_discounted_button.clicked.connect(self.toggle_discount_filter)
        button_layout.addWidget(self.show_discounted_button)
        
        # Add sort combo box
        sort_label = QtWidgets.QLabel("Sort by:")
        button_layout.addWidget(sort_label)
        
        self.sort_combo = QtWidgets.QComboBox()
        self.sort_combo.addItems(["Saved Order", "Current Price Ascending", "Discount Percentage (Highest to Lowest)"])
        self.sort_combo.setEnabled(False)
        self.sort_combo.currentTextChanged.connect(self.sort_games)
        button_layout.addWidget(self.sort_combo)
        
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
        self.show_discounted_button.setEnabled(False)
        self.sort_combo.setEnabled(False)
        self.games_data.clear()
        self.games_order.clear()
        self.status_label.setText("Initializing...")
        self.worker = ConsolePriceWorker()
        self.worker.set_games(current_prices_consoles.update_games_to_check())
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
        # Store game data in dictionary
        self.games_data[game_name] = price_info
        self.games_order.append(game_name)
        
        # Create and add item to tree
        self.create_and_add_item(game_name, price_info)

    def create_and_add_item(self, game_name, price_info):
        """Create a tree widget item from game data and add it to the tree."""
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
        self.show_discounted_button.setEnabled(True)
        self.sort_combo.setEnabled(True)
        self.sort_combo.setCurrentIndex(0)  # Reset to "Saved Order"
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

    def apply_discount_filter(self):
        """Apply the discount filter to currently visible items."""
        for i in range(self.prices_tree_widget.topLevelItemCount()):
            item = self.prices_tree_widget.topLevelItem(i)
            psn_current = self._parse_price(item.text(2))
            psn_base = self._parse_price(item.text(3))
            xbox_current = self._parse_price(item.text(6))
            xbox_base = self._parse_price(item.text(7))
            nintendo_current = self._parse_price(item.text(10))
            nintendo_base = self._parse_price(item.text(11))
            has_discount = ((psn_base > 0 and psn_current < psn_base) or 
                           (xbox_base > 0 and xbox_current < xbox_base) or 
                           (nintendo_base > 0 and nintendo_current < nintendo_base))
            item.setHidden(not has_discount)

    def show_only_discounted(self):
        """Show only games with discounts applied."""
        self.apply_discount_filter()

    def show_all_games(self):
        """Show all games (both discounted and undiscounted)."""
        for i in range(self.prices_tree_widget.topLevelItemCount()):
            item = self.prices_tree_widget.topLevelItem(i)
            item.setHidden(False)

    def toggle_discount_filter(self):
        """Toggle between showing only discounted games and showing all games."""
        if self.showing_only_discounted:
            self.show_all_games()
            self.show_discounted_button.setText("Show Only Discounted")
            self.showing_only_discounted = False
        else:
            self.show_only_discounted()
            self.show_discounted_button.setText("Show Undiscounted")
            self.showing_only_discounted = True

    def sort_games(self, sort_type):
        """Sort games based on the selected sort type."""
        if sort_type == "Saved Order":
            self.sort_by_saved_order()
        elif sort_type == "Current Price Ascending":
            self.sort_by_current_price()
        elif sort_type == "Discount Percentage (Highest to Lowest)":
            self.sort_by_discount_value()

    def sort_by_saved_order(self):
        """Restore original order of items."""
        self.prices_tree_widget.clear()
        for game_name in self.games_order:
            if game_name in self.games_data:
                self.create_and_add_item(game_name, self.games_data[game_name])
        
        # Apply discount filter if active
        if self.showing_only_discounted:
            self.apply_discount_filter()

    def sort_by_current_price(self):
        """Sort by current price (lowest price between PSN, Xbox, and Nintendo)."""
        # Create list of (min_price, game_name) tuples
        price_items = []
        for game_name, price_info in self.games_data.items():
            psn_current = price_info.get("psn", {}).get("current", 0.0)
            xbox_current = price_info.get("xbox", {}).get("current", 0.0)
            nintendo_current = price_info.get("nintendo", {}).get("current", 0.0)
            # Get the lowest current price (excluding 0)
            prices = [p for p in [psn_current, xbox_current, nintendo_current] if p > 0]
            min_price = min(prices) if prices else float('inf')
            price_items.append((min_price, game_name))
        
        # Sort by price (ascending)
        price_items.sort(key=lambda x: x[0])
        
        # Clear and rebuild tree
        self.prices_tree_widget.clear()
        for _, game_name in price_items:
            self.create_and_add_item(game_name, self.games_data[game_name])
        
        # Apply discount filter if active
        if self.showing_only_discounted:
            self.apply_discount_filter()

    def sort_by_discount_value(self):
        """Sort by discount percentage (highest percentage first)."""
        # Create list of (max_discount_percentage, game_name) tuples
        discount_items = []
        for game_name, price_info in self.games_data.items():
            psn_current = price_info.get("psn", {}).get("current", 0.0)
            psn_base = price_info.get("psn", {}).get("base", 0.0)
            xbox_current = price_info.get("xbox", {}).get("current", 0.0)
            xbox_base = price_info.get("xbox", {}).get("base", 0.0)
            nintendo_current = price_info.get("nintendo", {}).get("current", 0.0)
            nintendo_base = price_info.get("nintendo", {}).get("base", 0.0)
            
            # Calculate discount percentages - only if there's actually a discount
            psn_discount_percentage = 0
            if psn_base > 0 and psn_current > 0 and psn_current < psn_base:
                psn_discount_percentage = ((psn_base - psn_current) / psn_base) * 100
            
            xbox_discount_percentage = 0
            if xbox_base > 0 and xbox_current > 0 and xbox_current < xbox_base:
                xbox_discount_percentage = ((xbox_base - xbox_current) / xbox_base) * 100
            
            nintendo_discount_percentage = 0
            if nintendo_base > 0 and nintendo_current > 0 and nintendo_current < nintendo_base:
                nintendo_discount_percentage = ((nintendo_base - nintendo_current) / nintendo_base) * 100
            
            # Get the highest discount percentage between PSN, Xbox, and Nintendo
            max_discount_percentage = max(psn_discount_percentage, xbox_discount_percentage, nintendo_discount_percentage)
            
            # If no discount, put at the end
            if max_discount_percentage == 0:
                max_discount_percentage = -1  # This will sort to the end
            
            discount_items.append((max_discount_percentage, game_name))
        
        # Sort by discount percentage (descending - highest first)
        discount_items.sort(key=lambda x: x[0], reverse=True)
        
        # Clear and rebuild tree
        self.prices_tree_widget.clear()
        for _, game_name in discount_items:
            self.create_and_add_item(game_name, self.games_data[game_name])
        
        # Apply discount filter if active
        if self.showing_only_discounted:
            self.apply_discount_filter()

    def _parse_price(self, price_str):
        """Parse price string to float, handling spaces and commas."""
        price_str = price_str.strip().replace(' ', '').replace(',', '.')
        try:
            return float(price_str)
        except Exception:
            return 0.0

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
