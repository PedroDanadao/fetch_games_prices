import os
import platform
import subprocess
import sys
from pathlib import Path
import json
from PyQt5 import QtWidgets, QtGui, QtCore

# User data folder path
DATA_DIR = Path.home() / ".current_prices_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

JSON_PATH = DATA_DIR / "console_games_to_check.json"

if getattr(sys, 'frozen', False):
    THIS_FOLDER = os.path.dirname(sys.executable)
else:
    THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(THIS_FOLDER, "icons", "window_icon.png")

class ConsoleGameManagerUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_games()

    def init_ui(self):
        self.setWindowTitle("Console Game Manager - Edit Console Games to Check")
        self.setGeometry(100, 100, 900, 600)
        if os.path.exists(ICON_PATH):
            window_icon = QtGui.QIcon(ICON_PATH)
            self.setWindowIcon(window_icon)
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)
        title_label = QtWidgets.QLabel("Console Games to Check Configuration")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(title_label)
        self.games_tree = QtWidgets.QTreeWidget()
        self.games_tree.setHeaderLabels(["Game Name", "PSN", "Xbox", "Nintendo"])
        self.games_tree.setAlternatingRowColors(True)
        self.games_tree.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        main_layout.addWidget(self.games_tree)
        input_group = QtWidgets.QGroupBox("Add/Edit Console Game")
        input_layout = QtWidgets.QFormLayout()
        input_group.setLayout(input_layout)
        self.game_name_input = QtWidgets.QLineEdit()
        self.game_name_input.setPlaceholderText("Enter game name...")
        input_layout.addRow("Game Name:", self.game_name_input)
        self.psn_input = QtWidgets.QLineEdit()
        self.psn_input.setPlaceholderText("Enter PSN URL (optional)...")
        input_layout.addRow("PSN Site:", self.psn_input)
        self.xbox_input = QtWidgets.QLineEdit()
        self.xbox_input.setPlaceholderText("Enter Xbox URL (optional)...")
        input_layout.addRow("Xbox Site:", self.xbox_input)
        self.nintendo_input = QtWidgets.QLineEdit()
        self.nintendo_input.setPlaceholderText("Enter Nintendo URL (optional)...")
        input_layout.addRow("Nintendo Site:", self.nintendo_input)
        main_layout.addWidget(input_group)
        buttons_layout = QtWidgets.QHBoxLayout()
        self.add_button = QtWidgets.QPushButton("Add Game")
        self.add_button.clicked.connect(self.add_game)
        buttons_layout.addWidget(self.add_button)
        self.update_button = QtWidgets.QPushButton("Update Selected")
        self.update_button.clicked.connect(self.update_game)
        self.update_button.setEnabled(False)
        buttons_layout.addWidget(self.update_button)
        self.remove_button = QtWidgets.QPushButton("Remove Selected")
        self.remove_button.clicked.connect(self.remove_game)
        self.remove_button.setEnabled(False)
        buttons_layout.addWidget(self.remove_button)
        self.open_json_button = QtWidgets.QPushButton("Open Json Folder")
        self.open_json_button.clicked.connect(self.open_data_folder)
        buttons_layout.addWidget(self.open_json_button)
        buttons_layout.addStretch()
        self.save_button = QtWidgets.QPushButton("Save Changes")
        self.save_button.clicked.connect(self.save_games)
        self.save_button.setStyleSheet("font-weight: bold; padding: 8px;")
        buttons_layout.addWidget(self.save_button)
        main_layout.addLayout(buttons_layout)
        self.games_tree.itemSelectionChanged.connect(self.on_selection_changed)
        self.games_tree.itemDoubleClicked.connect(self.on_item_double_clicked)

        self.games_tree.setColumnWidth(0, 300)
        self.games_tree.setColumnWidth(1, 100)
        self.games_tree.setColumnWidth(2, 100)
        self.games_tree.setColumnWidth(3, 100)

    def load_games(self):
        self.games_tree.clear()
        if os.path.exists(JSON_PATH):
            try:
                with open(JSON_PATH, 'r', encoding='utf-8') as f:
                    games_data = json.load(f)
                for game_name, sites in games_data.items():
                    psn = sites.get("psn_site", "")
                    xbox = sites.get("xbox_site", "")
                    nintendo = sites.get("nintendo_site", "")
                    item = QtWidgets.QTreeWidgetItem([
                        game_name,
                        "X" if psn else "",
                        "X" if xbox else "",
                        "X" if nintendo else ""
                    ])
                    item.setData(0, QtCore.Qt.UserRole, sites)
                    self.games_tree.addTopLevelItem(item)
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"Failed to load games: {str(e)}")

    def add_game(self):
        game_name = self.game_name_input.text().strip()
        psn = self.psn_input.text().strip()
        xbox = self.xbox_input.text().strip()
        nintendo = self.nintendo_input.text().strip()
        if not game_name:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please enter a game name.")
            return
        for i in range(self.games_tree.topLevelItemCount()):
            item = self.games_tree.topLevelItem(i)
            if item.text(0) == game_name:
                QtWidgets.QMessageBox.warning(self, "Warning", "A game with this name already exists.")
                return
        sites = {}
        if psn:
            sites["psn_site"] = psn
        if xbox:
            sites["xbox_site"] = xbox
        if nintendo:
            sites["nintendo_site"] = nintendo
        item = QtWidgets.QTreeWidgetItem([
            game_name,
            "X" if psn else "",
            "X" if xbox else "",
            "X" if nintendo else ""
        ])
        item.setData(0, QtCore.Qt.UserRole, sites)
        self.games_tree.addTopLevelItem(item)
        self.game_name_input.clear()
        self.psn_input.clear()
        self.xbox_input.clear()
        self.nintendo_input.clear()
        self.games_tree.setCurrentItem(item)
        QtWidgets.QMessageBox.information(self, "Success", f"Game '{game_name}' added successfully.")

    def update_game(self):
        current_item = self.games_tree.currentItem()
        if not current_item:
            return
        game_name = self.game_name_input.text().strip()
        psn = self.psn_input.text().strip()
        xbox = self.xbox_input.text().strip()
        nintendo = self.nintendo_input.text().strip()
        if not game_name:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please enter a game name.")
            return
        for i in range(self.games_tree.topLevelItemCount()):
            item = self.games_tree.topLevelItem(i)
            if item != current_item and item.text(0) == game_name:
                QtWidgets.QMessageBox.warning(self, "Warning", "A game with this name already exists.")
                return
        sites = {}
        if psn:
            sites["psn_site"] = psn
        if xbox:
            sites["xbox_site"] = xbox
        if nintendo:
            sites["nintendo_site"] = nintendo
        current_item.setText(0, game_name)
        current_item.setText(1, "X" if psn else "")
        current_item.setText(2, "X" if xbox else "")
        current_item.setText(3, "X" if nintendo else "")
        current_item.setData(0, QtCore.Qt.UserRole, sites)
        self.game_name_input.clear()
        self.psn_input.clear()
        self.xbox_input.clear()
        self.nintendo_input.clear()
        QtWidgets.QMessageBox.information(self, "Success", f"Game updated successfully.")

    def remove_game(self):
        current_item = self.games_tree.currentItem()
        if not current_item:
            return
        game_name = current_item.text(0)
        reply = QtWidgets.QMessageBox.question(
            self, "Confirm Removal", 
            f"Are you sure you want to remove '{game_name}'?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            index = self.games_tree.indexOfTopLevelItem(current_item)
            self.games_tree.takeTopLevelItem(index)
            self.game_name_input.clear()
            self.psn_input.clear()
            self.xbox_input.clear()
            self.nintendo_input.clear()
            QtWidgets.QMessageBox.information(self, "Success", f"Game '{game_name}' removed successfully.")

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

    def save_games(self):
        games_data = {}
        for i in range(self.games_tree.topLevelItemCount()):
            item = self.games_tree.topLevelItem(i)
            game_name = item.text(0)
            sites = item.data(0, QtCore.Qt.UserRole) or {}
            games_data[game_name] = sites
        try:
            with open(JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(games_data, f, indent=4, ensure_ascii=False)
            QtWidgets.QMessageBox.information(self, "Success", "Games saved successfully!")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save games: {str(e)}")

    def on_selection_changed(self):
        has_selection = bool(self.games_tree.currentItem())
        self.update_button.setEnabled(has_selection)
        self.remove_button.setEnabled(has_selection)
        if has_selection:
            current_item = self.games_tree.currentItem()
            self.game_name_input.setText(current_item.text(0))
            sites = current_item.data(0, QtCore.Qt.UserRole) or {}
            self.psn_input.setText(sites.get("psn_site", ""))
            self.xbox_input.setText(sites.get("xbox_site", ""))
            self.nintendo_input.setText(sites.get("nintendo_site", ""))

    def on_item_double_clicked(self, item, column):
        self.game_name_input.setText(item.text(0))
        sites = item.data(0, QtCore.Qt.UserRole) or {}
        self.psn_input.setText(sites.get("psn_site", ""))
        self.xbox_input.setText(sites.get("xbox_site", ""))
        self.nintendo_input.setText(sites.get("nintendo_site", ""))

    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(
            self, "Exit", 
            "Do you want to save changes before closing?",
            QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel
        )
        if reply == QtWidgets.QMessageBox.Save:
            self.save_games()
            event.accept()
        elif reply == QtWidgets.QMessageBox.Discard:
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = ConsoleGameManagerUI()
    window.show()
    sys.exit(app.exec_())
