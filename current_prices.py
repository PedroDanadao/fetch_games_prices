# import necessary tools from the selenium library
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import json
from pathlib import Path

# ...

def start_chrome_driver():
    """Initialize and return a Chrome WebDriver instance."""
    service = Service()
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    return webdriver.Chrome(service=service, options=options)

def exit_chrome_driver(driver):
    """Close the Chrome WebDriver instance."""
    if driver:
        driver.quit()

# User data folder path
DATA_DIR = Path.home() / ".current_prices_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Get the actual directory of the Python executable or script
json_path = DATA_DIR / "games_to_check.json"

try:
    with open(json_path, "r") as json_file:
        GAMES_TO_CHECK = json.load(json_file)
except FileNotFoundError:
    print(f"Error: The file {json_path} does not exist. Set the games to check using the ui")
    GAMES_TO_CHECK = {}

def get_game_prices(game_name, driver=None):
    """Check the prices of a game on Steam and GOG."""
    # set up chrome driver
    if not driver:
        driver = start_chrome_driver()
    
    prices_data_dict = {}

    game_site = GAMES_TO_CHECK.get(game_name)

    # navigate to the target webpage
    driver.get(game_site)

    # wait for the product grid to load
    WebDriverWait(driver, 60).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".svelte-1l4u06e"))
    )

    elements = driver.find_elements(By.CSS_SELECTOR, ".row")

    import re

    for element in elements:
        element_text = element.text

        if not (element_text.startswith("Steam\n") or element_text.startswith("GOG\n")):
            continue

        prices = re.findall(r'\d+,\d+', element_text)

        current_price = prices[1] if prices else "No price found"
        base_price = prices[2] if prices else "No price found"

        if "Steam" in element_text:
            prices_data_dict["Steam_current"] = current_price
            prices_data_dict["Steam_base"] = base_price
        if "GOG" in element_text:
            prices_data_dict["GOG_current"] = current_price
            prices_data_dict["GOG_base"] = base_price

    return prices_data_dict


if __name__ == "__main__":
    driver = start_chrome_driver()

    # Example usage of the get_game_prices function
    # Uncomment the lines below to test with specific games or change the game names to 
    # match your JSON file

    # doom_prices = get_game_prices("DOOM + DOOM II", driver)

    # print("DOOM + DOOM II Prices:", doom_prices)

    exit_chrome_driver(driver)
