import os
import platform
import subprocess
import sys
from pathlib import Path
import json
from PyQt5 import QtWidgets, QtGui, QtCore
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



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


class StoreLinkWorker(QtCore.QThread):
    """Worker thread for fetching store links without blocking the UI."""
    progress_updated = QtCore.pyqtSignal(str)  # status message
    link_updated = QtCore.pyqtSignal(str, dict)  # game_name, links_dict
    finished_all = QtCore.pyqtSignal()
    error_occurred = QtCore.pyqtSignal(str)

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
            service = Service()
            options = webdriver.ChromeOptions()
            options.add_argument("--headless=new")
            driver = webdriver.Chrome(service=service, options=options)

            total_games = len(self.games_to_check)
            processed = 0

            for game_name, game_data in self.games_to_check.items():
                processed += 1

                try:
                    # Get the IsThereAnyDeal URL
                    itad_url = game_data if isinstance(game_data, str) else game_data.get("isthereanydeal_link", "")
                    
                    if not itad_url:
                        self.error_occurred.emit(f"No IsThereAnyDeal link for {game_name}")
                        continue

                    # Check what links are already saved
                    existing_steam = game_data.get("steam_link") if isinstance(game_data, dict) else None
                    existing_gog = game_data.get("gog_link") if isinstance(game_data, dict) else None

                    # Check if both links are already resolved (either fetched or marked as non-existent)
                    steam_resolved = existing_steam and existing_steam != "link_not_fetched"
                    gog_resolved = existing_gog and existing_gog != "link_not_fetched"
                    
                    if steam_resolved and gog_resolved:
                        self.progress_updated.emit(f"Skipping {game_name} ({processed}/{total_games}) - both links already resolved")
                        continue

                    self.progress_updated.emit(f"Fetching store links for {game_name} ({processed}/{total_games})...")

                    # Navigate to IsThereAnyDeal page to see what's available
                    driver.get(itad_url)
                    WebDriverWait(driver, 60).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".cell"))
                    )

                    # Get fresh elements each time to avoid stale reference
                    elements = driver.find_elements(By.CSS_SELECTOR, ".row")
                    
                    links_dict = {"isthereanydeal_link": itad_url}
                    
                    # Store element data before interacting with them
                    steam_href = None
                    gog_href = None
                    
                    for element in elements:
                        try:
                            text = element.text
                            if not text:
                                continue
                            
                            href = element.get_attribute("href")
                            if not href:
                                continue
                            
                            if text.startswith("Steam\n"):
                                steam_href = href
                                self.progress_updated.emit(f"Found Steam link for {game_name}")
                            elif text.startswith("GOG\n"):
                                gog_href = href
                                self.progress_updated.emit(f"Found GOG link for {game_name}")
                        except:
                            continue
                    
                    # Handle Steam link
                    if steam_href:
                        if existing_steam and existing_steam not in ["non_existent", "link_not_fetched"]:
                            links_dict["steam_link"] = existing_steam
                            self.progress_updated.emit(f"Using existing Steam link for {game_name}")
                        else:
                            steam_link = self.get_steam_link(driver, steam_href)
                            if steam_link:
                                links_dict["steam_link"] = steam_link
                                self.progress_updated.emit(f"Steam link fetched for {game_name}")
                            else:
                                links_dict["steam_link"] = "link_not_fetched"
                                self.progress_updated.emit(f"Failed to fetch Steam link for {game_name}")
                    else:
                        links_dict["steam_link"] = "non_existent"
                    
                    # Handle GOG link
                    if gog_href:
                        if existing_gog and existing_gog not in ["non_existent", "link_not_fetched"]:
                            links_dict["gog_link"] = existing_gog
                            self.progress_updated.emit(f"Using existing GOG link for {game_name}")
                        else:
                            gog_link = self.get_gog_link(driver, gog_href)
                            if gog_link:
                                links_dict["gog_link"] = gog_link
                                self.progress_updated.emit(f"GOG link fetched for {game_name}")
                            else:
                                links_dict["gog_link"] = "link_not_fetched"
                                self.progress_updated.emit(f"Failed to fetch GOG link for {game_name}")
                    else:
                        links_dict["gog_link"] = "non_existent"

                    # Always emit to save the current iteration
                    self.link_updated.emit(game_name, links_dict)

                except Exception as e:
                    self.error_occurred.emit(f"Error fetching links for {game_name}: {str(e)}")

            self.progress_updated.emit("Closing Chrome driver...")
            driver.quit()
            self.progress_updated.emit("All store links updated!")
            self.finished_all.emit()

        except Exception as e:
            self.error_occurred.emit(f"Critical error: {str(e)}")

    def get_steam_link(self, driver: webdriver.Chrome, itad_link: str) -> str:
        """Navigate to Steam through IsThereAnyDeal and get the actual store link."""
        try:
            driver.get(itad_link)
            # Try multiple selectors and wait longer
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".apphub_AppName"))
                )
            except:
                # Try alternative selector
                try:
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".game_area_purchase_game"))
                    )
                except:
                    # Last resort - check if we're on Steam domain
                    if "steampowered.com" in driver.current_url:
                        return driver.current_url
                    return None
            return driver.current_url
        except Exception as e:
            print(f"Steam link error: {str(e)}")
            return None

    def get_gog_link(self, driver: webdriver.Chrome, itad_link: str) -> str:
        """Navigate to GOG through IsThereAnyDeal and get the actual store link."""
        try:
            driver.get(itad_link)
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-actions-price__final-amount"))
            )
            return driver.current_url
        except:
            return None


class CustomTreeWidget(QtWidgets.QTreeWidget):
    """Custom tree widget that prevents nesting during drag and drop."""
    
    def dropEvent(self, event: QtGui.QDropEvent):
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
        self.worker = None
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
        input_layout.addRow("IsThereAnyDeal URL:", self.game_url_input)

        self.steam_link_input = QtWidgets.QLineEdit()
        self.steam_link_input.setPlaceholderText("Enter Steam store URL (optional)...")
        input_layout.addRow("Steam Link:", self.steam_link_input)

        self.gog_link_input = QtWidgets.QLineEdit()
        self.gog_link_input.setPlaceholderText("Enter GOG store URL (optional)...")
        input_layout.addRow("GOG Link:", self.gog_link_input)

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

        self.update_links_button = QtWidgets.QPushButton("Update Store Links")
        self.update_links_button.clicked.connect(self.update_store_links)
        self.update_links_button.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; padding: 8px;")
        buttons_layout.addWidget(self.update_links_button)

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
                
                for game_name, game_data in games_data.items():
                    # Handle both old format (string) and new format (dict)
                    if isinstance(game_data, str):
                        game_url = game_data
                    else:
                        game_url = game_data.get("isthereanydeal_link", "")
                    
                    item = QtWidgets.QTreeWidgetItem([game_name, game_url])
                    # Store full data in item
                    item.setData(0, QtCore.Qt.UserRole + 1, game_data)
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
        steam_link = self.steam_link_input.text().strip()
        gog_link = self.gog_link_input.text().strip()
        
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
        
        # Create game data dictionary
        game_data = {"isthereanydeal_link": game_url}
        if steam_link:
            game_data["steam_link"] = steam_link
        if gog_link:
            game_data["gog_link"] = gog_link
        
        # Add new item
        item = QtWidgets.QTreeWidgetItem([game_name, game_url])
        item.setData(0, QtCore.Qt.UserRole + 1, game_data)
        self.games_tree.addTopLevelItem(item)
        
        # Clear inputs
        self.game_name_input.clear()
        self.game_url_input.clear()
        self.steam_link_input.clear()
        self.gog_link_input.clear()
        
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
        steam_link = self.steam_link_input.text().strip()
        gog_link = self.gog_link_input.text().strip()
        
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
        
        # Create game data dictionary
        game_data = {"isthereanydeal_link": game_url}
        if steam_link:
            game_data["steam_link"] = steam_link
        if gog_link:
            game_data["gog_link"] = gog_link
        
        # Update the item
        current_item.setText(0, game_name)
        current_item.setText(1, game_url)
        current_item.setData(0, QtCore.Qt.UserRole + 1, game_data)
        
        # Clear inputs
        self.game_name_input.clear()
        self.game_url_input.clear()
        self.steam_link_input.clear()
        self.gog_link_input.clear()
        
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
            self.steam_link_input.clear()
            self.gog_link_input.clear()
            
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
            
            # Check if item has stored data (with links)
            stored_data = item.data(0, QtCore.Qt.UserRole + 1)
            if isinstance(stored_data, dict):
                # Update the isthereanydeal_link if it changed
                stored_data["isthereanydeal_link"] = game_url
                games_data[game_name] = stored_data
            else:
                # Create new dict structure
                games_data[game_name] = {"isthereanydeal_link": game_url}
        
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
            
            # Get stored data for Steam and GOG links
            stored_data = current_item.data(0, QtCore.Qt.UserRole + 1)
            if isinstance(stored_data, dict):
                self.steam_link_input.setText(stored_data.get("steam_link", ""))
                self.gog_link_input.setText(stored_data.get("gog_link", ""))
            else:
                self.steam_link_input.clear()
                self.gog_link_input.clear()

    def on_item_double_clicked(self, item: QtWidgets.QTreeWidgetItem, column: int):
        """Handle double-click on tree items."""
        self.game_name_input.setText(item.text(0))
        self.game_url_input.setText(item.text(1))
        
        # Get stored data for Steam and GOG links
        stored_data = item.data(0, QtCore.Qt.UserRole + 1)
        if isinstance(stored_data, dict):
            self.steam_link_input.setText(stored_data.get("steam_link", ""))
            self.gog_link_input.setText(stored_data.get("gog_link", ""))
        else:
            self.steam_link_input.clear()
            self.gog_link_input.clear()

    def update_store_links(self):
        """Update store links for all games."""
        if self.worker and self.worker.isRunning():
            return

        # Disable buttons during update
        self.update_links_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.add_button.setEnabled(False)
        self.update_button.setEnabled(False)
        self.remove_button.setEnabled(False)

        # Collect all games data
        games_to_check = {}
        for i in range(self.games_tree.topLevelItemCount()):
            item = self.games_tree.topLevelItem(i)
            game_name = item.text(0)
            stored_data = item.data(0, QtCore.Qt.UserRole + 1)
            
            if isinstance(stored_data, dict):
                games_to_check[game_name] = stored_data
            else:
                games_to_check[game_name] = {"isthereanydeal_link": item.text(1)}

        # Create and start worker
        self.worker = StoreLinkWorker()
        self.worker.set_games(games_to_check)
        self.worker.progress_updated.connect(self.on_link_progress)
        self.worker.link_updated.connect(self.on_link_updated)
        self.worker.finished_all.connect(self.on_links_finished)
        self.worker.error_occurred.connect(self.on_link_error)
        self.worker.start()

    def on_link_progress(self, message: str):
        """Handle progress updates."""
        print(message)

    def on_link_updated(self, game_name: str, links_dict: dict):
        """Handle when store links are updated for a game."""
        print(f"[DEBUG] on_link_updated called for: {game_name}")
        # Find the item in the tree
        for i in range(self.games_tree.topLevelItemCount()):
            item = self.games_tree.topLevelItem(i)
            if item.text(0) == game_name:
                # Update stored data
                item.setData(0, QtCore.Qt.UserRole + 1, links_dict)
                print(f"Updated links for {game_name}: Steam={links_dict.get('steam_link', 'N/A')[:50]}..., GOG={links_dict.get('gog_link', 'N/A')[:50]}...")
                
                # Save JSON immediately after fetching each link
                print(f"[DEBUG] Calling save_games_silent for {game_name}")
                self.save_games_silent()
                print(f"[DEBUG] save_games_silent completed for {game_name}")
                break

    def save_games_silent(self):
        """Save games without showing a success message."""
        games_data = {}
        
        for i in range(self.games_tree.topLevelItemCount()):
            item = self.games_tree.topLevelItem(i)
            game_name = item.text(0)
            game_url = item.text(1)
            
            # Check if item has stored data (with links)
            stored_data = item.data(0, QtCore.Qt.UserRole + 1)
            if isinstance(stored_data, dict):
                # Update the isthereanydeal_link if it changed
                stored_data["isthereanydeal_link"] = game_url
                games_data[game_name] = stored_data
            else:
                # Create new dict structure
                games_data[game_name] = {"isthereanydeal_link": game_url}
        
        try:
            with open(JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(games_data, f, indent=4, ensure_ascii=False)
            print(f"JSON saved successfully with {len(games_data)} games")
        except Exception as e:
            print(f"Failed to save games: {str(e)}")

    def on_links_finished(self):
        """Handle when all links are updated."""
        # Re-enable buttons
        self.update_links_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.add_button.setEnabled(True)
        self.update_button.setEnabled(True)
        self.remove_button.setEnabled(True)
        
        QtWidgets.QMessageBox.information(self, "Success", "Store links updated and saved!")

    def on_link_error(self, error_message: str):
        """Handle errors."""
        print(f"Error: {error_message}")

    def closeEvent(self, event: QtGui.QCloseEvent):
        """Handle window close event."""
        # Stop worker if running
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        
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

    def _original_close_event(self, event: QtGui.QCloseEvent):
        """Placeholder for storing original closeEvent if needed."""
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