# 🎮 Fetch Games Prices

A tool that goes to the isthereanydeal website and checks the prices of the games that you set. It checks for the discount and displays it

It is a PyQt5 desktop app to track the current prices of games on Steam and GOG, using data from [IsThereAnyDeal.com](https://isthereanydeal.com/). Originally developed for **Windows**, but works perfectly on **macOS** as well (tested on macOS Sequoia with Python 3.11).

---

## ✨ Features

- Modern PyQt5 graphical interface
- Automated price tracking with Selenium
- User-defined game list
- Background updates with visual feedback
- Fully compatible with **Windows** and **macOS**

---

## ✅ Requirements

- Python 3.11+
- Google Chrome browser installed
- ChromeDriver matching your Chrome version
- Python packages:
  - PyQt5
  - selenium

---

## ⚙️ Installation

### 1. Clone this repository or copy the files

```bash
git clone <repo-url>
cd fetch_games_prices
```

### 2. Install dependencies

```bash
pip install PyQt5 selenium
```

### 3. Install ChromeDriver

Check your Chrome version via:
```
⋮ Menu → Help → About Google Chrome
```

Download the matching ChromeDriver from:

➡️ [https://googlechromelabs.github.io/chrome-for-testing](https://googlechromelabs.github.io/chrome-for-testing)

Then:

#### On **macOS**:
```bash
chmod +x chromedriver
mv chromedriver /usr/local/bin/
```

#### On **Windows**:
Place `chromedriver.exe` in the project folder **or** add it to your system `PATH`.

---

## 🕹️ How to Use

### 1. Add the games you want to track

First, run the game editor:

```bash
python set_games_to_check_json.py
```

Inside the editor:

- Click **Add Game**
- Enter the game name
- Paste the game URL from [IsThereAnyDeal](https://isthereanydeal.com)
- Click **Save Changes**

This creates or updates the `games_to_check.json` file, which the main app will use.

---

### 2. Launch the main interface

Once your game list is set up, launch the main app:

```bash
python current_prices_ui.py
```

The app will:

- Open a GUI window with a “Refresh Prices” button
- Launch Chrome in headless mode
- Check each game’s prices
- Display current/base prices from Steam and GOG
- Calculate and show discount percentages

---

## 🧪 Quick Test

To try it out:

1. Visit [https://isthereanydeal.com](https://isthereanydeal.com)
2. Search for a game (e.g., "DOOM")
3. Copy the game page URL (e.g., `https://isthereanydeal.com/game/doomplusdoomii/info/`)
4. Paste it in the editor and save

---

## 📦 (Extra) Building Executables

- If you build it on a Mac (Intel), it will only run on other Intel Macs (or ARM, if supported).
- If you want an .exe for Windows, you'll need to run PyInstaller on Windows itself (or use a VM/advanced cross-compilation with Docker, but it's not trivial).

### 🔹 Requirements

```bash
pip install pyinstaller
```

---

### 🔹 Create executable for main app (`current_prices_ui.py`)

#### On **macOS** and  **Windows**:

```bash
python3 -m pyinstaller --onefile --windowed current_prices_ui.py
```

> Output For Mac: `dist/current_prices_ui.app`
> Output For Windows: `dist\current_prices_ui.exe`

---

### 🔹 Create executable for game editor (`set_games_to_check_json.py`)

#### On **macOS** and  **Windows**:

```bash
python3 -m pyinstaller --onefile --windowed set_games_to_check_json.py
```

> Output For Mac: `dist/set_games_to_check_json.app`
> Output For Windows: `dist\set_games_to_check_json.exe`

---

### 📝 Executable Notes

- Make sure ChromeDriver is available via system `PATH` or next to the executable.
- If distributing the app, include the `games_to_check.json` file or instruct users to create it first.

---

## 👨‍💻 Original Author

This project was created by [PedroDanadao](https://github.com/PedroDanadao), and successfully adapted/tested for macOS by [MDOBreno](https://github.com/MDOBreno).

---

## 🧠 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
