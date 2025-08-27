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

# Get the actual directory of the Python executable or script
JSON_PATH = DATA_DIR / "games_to_check.json"



# Pega o diretório real do executável ou script Python
if getattr(sys, 'frozen', False):
    THIS_FOLDER = os.path.dirname(sys.executable)  # se for executável
else:
    THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))  # se for script
print(f"This app is running from this folder:\n{THIS_FOLDER}")

ICON_PATH = os.path.join(THIS_FOLDER, "icons", "window_icon.png")

class CustomTreeWidget(QtWidgets.QTreeWidget):
    """Custom tree widget that prevents nesting during drag and drop."""
    
    def dropEvent(self, event):
        # Only allow drops at the root level
        item = self.itemAt(event.pos())
        if item is None:
            # Dropping in empty space - allow
            super().dropEvent(event)
        else:
            # Get the drop indicator position
            drop_indicator = self.dropIndicatorPosition()
            if drop_indicator == QtWidgets.QAbstractItemView.OnItem:
                # Trying to drop on an item (would create nesting) - don't allow
                event.ignore()
                return
            else:
                # Dropping above or below an item - allow
                super().dropEvent(event)

class GameManagerUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_games()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Game Manager - Edit Games to Check")
        self.setGeometry(100, 100, 800, 600)
        
        # Set window icon if it exists
        if os.path.exists(ICON_PATH):
            window_icon = QtGui.QIcon(ICON_PATH)
            self.setWindowIcon(window_icon)

        # Main layout
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

        # Title label
        title_label = QtWidgets.QLabel("Games to Check Configuration")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Tree widget for games
        self.games_tree = CustomTreeWidget()
        self.games_tree.setHeaderLabels(["Game Name", "URL"])
        self.games_tree.setAlternatingRowColors(True)
        self.games_tree.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        
        # Enable drag and drop for reordering but prevent nesting
        self.games_tree.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.games_tree.setRootIsDecorated(False)  # Remove expand/collapse indicators
        
        # Set column widths
        self.games_tree.setColumnWidth(0, 300)
        self.games_tree.setColumnWidth(1, 450)
        
        main_layout.addWidget(self.games_tree)

        # Input section
        input_group = QtWidgets.QGroupBox("Add/Edit Game")
        input_layout = QtWidgets.QFormLayout()
        input_group.setLayout(input_layout)

        self.game_name_input = QtWidgets.QLineEdit()
        self.game_name_input.setPlaceholderText("Enter game name...")
        input_layout.addRow("Game Name:", self.game_name_input)

        self.game_url_input = QtWidgets.QLineEdit()
        self.game_url_input.setPlaceholderText("Enter IsThereAnyDeal URL...")
        input_layout.addRow("URL:", self.game_url_input)

        main_layout.addWidget(input_group)

        # Buttons section
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

        # Connect tree selection change
        self.games_tree.itemSelectionChanged.connect(self.on_selection_changed)
        self.games_tree.itemDoubleClicked.connect(self.on_item_double_clicked)

    def load_games(self):
        """Load games from the JSON file into the tree widget."""
        self.games_tree.clear()
        
        if os.path.exists(JSON_PATH):
            try:
                with open(JSON_PATH, 'r', encoding='utf-8') as f:
                    games_data = json.load(f)
                
                for game_name, game_url in games_data.items():
                    item = QtWidgets.QTreeWidgetItem([game_name, game_url])
                    self.games_tree.addTopLevelItem(item)
                    
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"Failed to load games: {str(e)}")
        
        # Resize columns to content
        self.games_tree.resizeColumnToContents(0)
        self.games_tree.resizeColumnToContents(1)

    def add_game(self):
        """Add a new game to the tree widget."""
        game_name = self.game_name_input.text().strip()
        game_url = self.game_url_input.text().strip()
        
        if not game_name:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please enter a game name.")
            return
            
        if not game_url:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please enter a game URL.")
            return
            
        # Check if game already exists
        for i in range(self.games_tree.topLevelItemCount()):
            item = self.games_tree.topLevelItem(i)
            if item.text(0) == game_name:
                QtWidgets.QMessageBox.warning(self, "Warning", "A game with this name already exists.")
                return
        
        # Add new item
        item = QtWidgets.QTreeWidgetItem([game_name, game_url])
        self.games_tree.addTopLevelItem(item)
        
        # Clear inputs
        self.game_name_input.clear()
        self.game_url_input.clear()
        
        # Select the new item
        self.games_tree.setCurrentItem(item)
        
        QtWidgets.QMessageBox.information(self, "Success", f"Game '{game_name}' added successfully.")

    def update_game(self):
        """Update the selected game."""
        current_item = self.games_tree.currentItem()
        if not current_item:
            return
            
        game_name = self.game_name_input.text().strip()
        game_url = self.game_url_input.text().strip()
        
        if not game_name:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please enter a game name.")
            return
            
        if not game_url:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please enter a game URL.")
            return
        
        # Check if the new name conflicts with another game (except the current one)
        for i in range(self.games_tree.topLevelItemCount()):
            item = self.games_tree.topLevelItem(i)
            if item != current_item and item.text(0) == game_name:
                QtWidgets.QMessageBox.warning(self, "Warning", "A game with this name already exists.")
                return
        
        # Update the item
        current_item.setText(0, game_name)
        current_item.setText(1, game_url)
        
        # Clear inputs
        self.game_name_input.clear()
        self.game_url_input.clear()
        
        QtWidgets.QMessageBox.information(self, "Success", f"Game updated successfully.")

    def remove_game(self):
        """Remove the selected game."""
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
            
            # Clear inputs
            self.game_name_input.clear()
            self.game_url_input.clear()
            
            QtWidgets.QMessageBox.information(self, "Success", f"Game '{game_name}' removed successfully.")

    def open_data_folder(self):
        folder = Path.home() / ".current_prices_data"
        folder.mkdir(parents=True, exist_ok=True)  # Garante que existe

        system = platform.system()

        if system == "Darwin":  # macOS
            subprocess.run(["open", folder])
        elif system == "Windows":
            os.startfile(folder)
        else:  # Linux ou outros Unix-like
            subprocess.run(["xdg-open", folder])

    def save_games(self):
        """Save all games from the tree widget to the JSON file."""
        games_data = {}
        
        for i in range(self.games_tree.topLevelItemCount()):
            item = self.games_tree.topLevelItem(i)
            game_name = item.text(0)
            game_url = item.text(1)
            games_data[game_name] = game_url
        
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
            self.game_url_input.setText(current_item.text(1))

    def on_item_double_clicked(self, item, column):
        """Handle double-click on tree items."""
        self.game_name_input.setText(item.text(0))
        self.game_url_input.setText(item.text(1))

    def closeEvent(self, event):
        """Handle window close event."""
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
    window = GameManagerUI()
    window.show()
    sys.exit(app.exec_())