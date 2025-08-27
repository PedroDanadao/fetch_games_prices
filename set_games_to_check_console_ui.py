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


X_STRING = 8 * " " + "X"


class ConsoleGameManagerUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setup_main_window()
        self.setup_tree_widget()
        self.setup_input_group()
        self.setup_buttons()
        self.load_games()

    def setup_main_window(self):
        """Set up main window properties and layout."""
        self.setWindowTitle("Console Game Manager - Edit Console Games to Check")
        self.setGeometry(100, 100, 900, 600)
        if os.path.exists(ICON_PATH):
            window_icon = QtGui.QIcon(ICON_PATH)
            self.setWindowIcon(window_icon)
        self.main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.main_layout)
        title_label = QtWidgets.QLabel("Console Games to Check Configuration")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        self.main_layout.addWidget(title_label)

    def setup_tree_widget(self):
        """Set up the tree widget for displaying games."""
        self.games_tree = QtWidgets.QTreeWidget()
        self.games_tree.setHeaderLabels(["Game Name", "PSN", "Xbox", "Nintendo"])
        self.games_tree.setAlternatingRowColors(True)
        self.games_tree.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.main_layout.addWidget(self.games_tree)
        self.games_tree.setColumnWidth(0, 300)
        self.games_tree.setColumnWidth(1, 100)
        self.games_tree.setColumnWidth(2, 100)
        self.games_tree.setColumnWidth(3, 100)
        # Prevent Nintendo column from stretching
        header = self.games_tree.header()
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.Fixed)
        self.games_tree.itemSelectionChanged.connect(self.on_selection_changed)
        self.games_tree.itemDoubleClicked.connect(self.on_item_double_clicked)

    def setup_input_group(self):
        """Set up the input fields for adding/editing games."""
        input_group = QtWidgets.QGroupBox("Add/Edit Console Game")
        input_layout = QtWidgets.QFormLayout()
        input_group.setLayout(input_layout)
        # Game name input
        self.game_name_input = QtWidgets.QLineEdit()
        self.game_name_input.setPlaceholderText("Enter game name...")
        input_layout.addRow("Game Name:", self.game_name_input)
        # PSN site input
        self.psn_input = QtWidgets.QLineEdit()
        self.psn_input.setPlaceholderText("Enter PSN URL (optional)...")
        self.psn_input.setToolTip("Right click to copy the PSN store link (or your custom link if filled)")
        self.psn_input.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.psn_input.customContextMenuRequested.connect(lambda point: self.open_site_context_menu(self.psn_input, "https://store.playstation.com", point))
        input_layout.addRow("PSN Site:", self.psn_input)
        # Xbox site input
        self.xbox_input = QtWidgets.QLineEdit()
        self.xbox_input.setPlaceholderText("Enter Xbox URL (optional)...")
        self.xbox_input.setToolTip("Right click to copy the Xbox store link (or your custom link if filled)")
        self.xbox_input.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.xbox_input.customContextMenuRequested.connect(lambda point: self.open_site_context_menu(self.xbox_input, "https://www.xbox.com", point))
        input_layout.addRow("Xbox Site:", self.xbox_input)
        # Nintendo site input
        self.nintendo_input = QtWidgets.QLineEdit()
        self.nintendo_input.setPlaceholderText("Enter Nintendo URL (optional)...")
        self.nintendo_input.setToolTip("Right click to copy the Nintendo store link (or your custom link if filled)")
        self.nintendo_input.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.nintendo_input.customContextMenuRequested.connect(lambda point: self.open_site_context_menu(self.nintendo_input, "https://www.nintendo.com", point))
        input_layout.addRow("Nintendo Site:", self.nintendo_input)
        self.main_layout.addWidget(input_group)

    def setup_buttons(self):
        """Set up the action buttons for the UI."""
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
        self.main_layout.addLayout(buttons_layout)

    def open_site_context_menu(self, line_edit, default_url, point):
        """Show context menu for copying site link from a line edit."""
        menu = QtWidgets.QMenu(self)
        copy_action = menu.addAction("Copy site link")
        def copy_link():
            link = line_edit.text().strip() or default_url
            QtWidgets.QApplication.clipboard().setText(link)
        copy_action.triggered.connect(copy_link)
        menu.exec_(line_edit.mapToGlobal(point))

    def load_games(self):
        """Load games from the JSON file into the tree widget."""
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
                        X_STRING if psn else "",
                        X_STRING if xbox else "",
                        X_STRING if nintendo else ""
                    ])
                    item.setData(0, QtCore.Qt.UserRole, sites)
                    self.games_tree.addTopLevelItem(item)
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"Failed to load games: {str(e)}")

    def add_game(self):
        """Add a new game to the tree widget."""
        game_name = self.game_name_input.text().strip()
        psn = self.psn_input.text().strip()
        xbox = self.xbox_input.text().strip()
        nintendo = self.nintendo_input.text().strip()
        if not game_name:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please enter a game name.")
            return
        # Check for duplicate game name
        for i in range(self.games_tree.topLevelItemCount()):
            item = self.games_tree.topLevelItem(i)
            if item.text(0) == game_name:
                QtWidgets.QMessageBox.warning(self, "Warning", "A game with this name already exists.")
                return
        # Build sites dictionary
        sites = {}
        if psn:
            sites["psn_site"] = psn
        if xbox:
            sites["xbox_site"] = xbox
        if nintendo:
            sites["nintendo_site"] = nintendo
        # Add item to tree
        item = QtWidgets.QTreeWidgetItem([
            game_name,
            X_STRING if psn else "",
            X_STRING if xbox else "",
            X_STRING if nintendo else ""
        ])
        item.setData(0, QtCore.Qt.UserRole, sites)
        self.games_tree.addTopLevelItem(item)
        # Clear inputs
        self.game_name_input.clear()
        self.psn_input.clear()
        self.xbox_input.clear()
        self.nintendo_input.clear()
        self.games_tree.setCurrentItem(item)
        QtWidgets.QMessageBox.information(self, "Success", f"Game '{game_name}' added successfully.")

    def update_game(self):
        """Update the selected game in the tree widget."""
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
        # Check for duplicate game name (except current)
        for i in range(self.games_tree.topLevelItemCount()):
            item = self.games_tree.topLevelItem(i)
            if item != current_item and item.text(0) == game_name:
                QtWidgets.QMessageBox.warning(self, "Warning", "A game with this name already exists.")
                return
        # Build sites dictionary
        sites = {}
        if psn:
            sites["psn_site"] = psn
        if xbox:
            sites["xbox_site"] = xbox
        if nintendo:
            sites["nintendo_site"] = nintendo
        # Update item in tree
        current_item.setText(0, game_name)
        current_item.setText(1, X_STRING if psn else "")
        current_item.setText(2, X_STRING if xbox else "")
        current_item.setText(3, X_STRING if nintendo else "")
        current_item.setData(0, QtCore.Qt.UserRole, sites)
        # Clear inputs
        self.game_name_input.clear()
        self.psn_input.clear()
        self.xbox_input.clear()
        self.nintendo_input.clear()
        QtWidgets.QMessageBox.information(self, "Success", f"Game updated successfully.")

    def remove_game(self):
        """Remove the selected game from the tree widget."""
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
        """Open the folder containing the JSON data file."""
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
        """Save all games from the tree widget to the JSON file."""
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
        """Handle tree selection changes."""
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
        """Handle double-click on tree items to populate input fields."""
        self.game_name_input.setText(item.text(0))
        sites = item.data(0, QtCore.Qt.UserRole) or {}
        self.psn_input.setText(sites.get("psn_site", ""))
        self.xbox_input.setText(sites.get("xbox_site", ""))
        self.nintendo_input.setText(sites.get("nintendo_site", ""))

    def closeEvent(self, event):
        """Handle window close event, prompting to save changes."""
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
