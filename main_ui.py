import os
import sys
from PyQt5 import QtWidgets, QtGui, QtCore

# Import all the UI modules
import current_prices_ui
import set_games_to_check_json
import current_console_prices_ui
import set_games_to_check_console_ui

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(THIS_FOLDER, "icons", "window_icon.png")


class MainUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.child_windows = {}  # Store references to child windows
        self.init_ui()

    def init_ui(self):
        """Initialize the main UI."""
        self.setWindowTitle("Game Price Tracker - Main Menu")
        self.setGeometry(100, 100, 450, 500)
        self.setFixedSize(450, 500)  # Fixed size for clean layout
        
        # Set window icon
        if os.path.exists(ICON_PATH):
            window_icon = QtGui.QIcon(ICON_PATH)
            self.setWindowIcon(window_icon)

        # Main layout
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

        # Title
        title_label = QtWidgets.QLabel("Game Price Tracker")
        title_label.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            margin: 25px 20px 20px 20px;
            color: #ffffff;
            text-align: center;
        """)
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # PC Games Section
        pc_label = QtWidgets.QLabel("PC Games")
        pc_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff; margin: 15px 0px 10px 0px;")
        pc_label.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(pc_label)

        # PC Games buttons
        self.pc_prices_button = QtWidgets.QPushButton("View PC Game Prices")
        self.pc_prices_button.setStyleSheet(self.get_button_style())
        self.pc_prices_button.clicked.connect(self.open_pc_prices)
        main_layout.addWidget(self.pc_prices_button)

        self.pc_config_button = QtWidgets.QPushButton("Set PC Games")
        self.pc_config_button.setStyleSheet(self.get_button_style())
        self.pc_config_button.clicked.connect(self.open_pc_config)
        main_layout.addWidget(self.pc_config_button)

        # Horizontal separator
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        separator.setStyleSheet("color: #555555; background-color: #555555; margin: 20px 30px;")
        main_layout.addWidget(separator)

        # Console Games Section
        console_label = QtWidgets.QLabel("Console Games")
        console_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff; margin: 10px 0px 15px 0px;")
        console_label.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(console_label)

        # Console Games buttons
        self.console_prices_button = QtWidgets.QPushButton("View Console Game Prices")
        self.console_prices_button.setStyleSheet(self.get_button_style())
        self.console_prices_button.clicked.connect(self.open_console_prices)
        main_layout.addWidget(self.console_prices_button)

        self.console_config_button = QtWidgets.QPushButton("Set Console Games")
        self.console_config_button.setStyleSheet(self.get_button_style())
        self.console_config_button.clicked.connect(self.open_console_config)
        main_layout.addWidget(self.console_config_button)

        # Add stretch to center everything
        main_layout.addStretch()

        # Apply main window styling
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)

    def get_button_style(self):
        """Return consistent button styling."""
        return """
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 2px solid #404040;
                padding: 15px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
                margin: 8px;
                min-height: 20px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #404040;
                border-color: #555555;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #505050;
                border-color: #666666;
                color: #ffffff;
            }
            QPushButton:disabled {
                background-color: #1f1f1f;
                border-color: #333333;
                color: #666666;
            }
        """

    def open_pc_prices(self):
        """Open the PC prices UI."""
        if 'pc_prices' not in self.child_windows or self.child_windows['pc_prices'] is None:
            self.child_windows['pc_prices'] = current_prices_ui.CurrentPricesUI()
            self.child_windows['pc_prices'].closeEvent = lambda event: self.on_child_closed('pc_prices', event)
        
        self.child_windows['pc_prices'].show()
        self.hide()

    def open_pc_config(self):
        """Open the PC configuration UI."""
        if 'pc_config' not in self.child_windows or self.child_windows['pc_config'] is None:
            self.child_windows['pc_config'] = set_games_to_check_json.GameManagerUI()
            self.child_windows['pc_config'].closeEvent = lambda event: self.on_child_closed('pc_config', event)
        
        self.child_windows['pc_config'].show()
        self.hide()

    def open_console_prices(self):
        """Open the console prices UI."""
        if 'console_prices' not in self.child_windows or self.child_windows['console_prices'] is None:
            self.child_windows['console_prices'] = current_console_prices_ui.CurrentConsolePricesUI()
            self.child_windows['console_prices'].closeEvent = lambda event: self.on_child_closed('console_prices', event)
        
        self.child_windows['console_prices'].showMaximized()
        self.hide()

    def open_console_config(self):
        """Open the console configuration UI."""
        if 'console_config' not in self.child_windows or self.child_windows['console_config'] is None:
            self.child_windows['console_config'] = set_games_to_check_console_ui.ConsoleGameManagerUI()
            self.child_windows['console_config'].closeEvent = lambda event: self.on_child_closed('console_config', event)
        
        self.child_windows['console_config'].show()
        self.hide()

    def on_child_closed(self, window_key, event):
        """Handle when a child window is closed."""
        # Store the original closeEvent if it exists
        original_close_event = getattr(self.child_windows[window_key], '_original_close_event', None)
        
        # Call the original closeEvent if it exists
        if original_close_event:
            original_close_event(event)
        else:
            event.accept()
        
        # Clean up the reference
        if event.isAccepted():
            self.child_windows[window_key] = None
            self.show()  # Show main window when child closes

    def closeEvent(self, event):
        """Handle main window close event."""
        # Close all child windows
        for window_key, window in self.child_windows.items():
            if window is not None:
                window.close()
        
        # Accept the close event to exit the application
        event.accept()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Game Price Tracker")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Game Price Tracker")
    
    # Create and show main window
    main_window = MainUI()
    main_window.show()
    
    sys.exit(app.exec_())
