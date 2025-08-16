# import necessary tools from the selenium library
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import json
from pathlib import Path

import re

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
json_path = DATA_DIR / "console_games_to_check.json"

try:
    with open(json_path, "r") as json_file:
        GAMES_TO_CHECK = json.load(json_file)
except FileNotFoundError:
    print(f"Error: The file {json_path} does not exist. Set the games to check using the ui")
    GAMES_TO_CHECK = {}

GAMES_TO_CHECK = {
    "Expedition 33": {
        "psn_site": "https://store.playstation.com/pt-br/product/EP7579-PPSA17599_00-EXP33000000PS5EU",
        "xbox_site": "https://www.xbox.com/pt-br/games/store/clair-obscur-expedition-33/9ppt8k6gqhrz"
    },
    "Jedi Survivor": {
        "psn_site": "https://store.playstation.com/pt-br/product/UP0006-PPSA07783_00-APPLEJACKGAME000",
        "xbox_site": "https://www.xbox.com/pt-br/games/store/star-wars-jedi-survivor/9pgc82v0dxfs"
    },
    "Resident Evil Village": {
        "xbox_site": "https://www.xbox.com/pt-br/games/store/resident-evil-village/9N2S04LGXXH4"
    }
}

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

    for element in elements:
        element_text = element.text

        if not (element_text.startswith("Steam\n") or element_text.startswith("GOG\n")):
            continue

        prices = re.findall(r'\d+,\d+', element_text)

        current_price = prices[1] if prices else "No price found"
        base_price = prices[2] if prices else "No price found"

        element_link = element.get_attribute("href")

        prices_data_dict["is_there_any_deal_link"] = game_site

        if "Steam" in element_text:
            prices_data_dict["Steam_current"] = current_price
            prices_data_dict["Steam_base"] = base_price
            prices_data_dict["Steam_link"] = element_link
        if "GOG" in element_text:
            prices_data_dict["GOG_current"] = current_price
            prices_data_dict["GOG_base"] = base_price
            prices_data_dict["GOG_link"] = element_link

    return prices_data_dict


def get_psn_prices(game_name, driver=None):
    """
    Fetches the current and base price of the game that matches the name in the GAMES_TO_CHECK dict
    """
    # set up chrome driver
    if not driver:
        driver = start_chrome_driver()

    game_site = GAMES_TO_CHECK.get(game_name)["psn_site"]

    # navigate to the website
    driver.get(game_site)

    # wait for the product grid to load
    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".psw-c-bg-card-1"))
    )

    price_card_element = driver.find_element(By.CSS_SELECTOR, ".psw-c-bg-card-1")
    new_price_element = price_card_element.find_element(By.CSS_SELECTOR, "span.psw-t-title-m")
    base_price_elements = price_card_element.find_elements(By.CSS_SELECTOR, "span.psw-t-title-s")

    base_price_element = base_price_elements[0] if base_price_elements else new_price_element

    new_price = re.findall(r'\d+,\d+', new_price_element.text)
    base_price = re.findall(r'\d+,\d+', base_price_element.text)

    return new_price, base_price


def get_xbox_prices(game_name, driver=None):
    """
    Fetches the current and base price of the game that matches the name in the GAMES_TO_CHECK dict
    """
    # set up chrome driver
    if not driver:
        driver = start_chrome_driver()

    game_site = GAMES_TO_CHECK.get(game_name)["xbox_site"]

    # navigate to the website
    driver.get(game_site)

    # wait for the product grid to load
    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".Price-module__boldText___1i2Li"))
    )

    new_price_element = driver.find_element(By.CSS_SELECTOR, ".Price-module__boldText___1i2Li")
    base_price_elements = driver.find_elements(By.CSS_SELECTOR, ".Price-module__brandOriginalPrice___ayJAn")

    base_price_element = base_price_elements[0] if base_price_elements else new_price_element

    new_price = re.findall(r'\d+,\d+', new_price_element.text)
    base_price = re.findall(r'\d+,\d+', base_price_element.text)

    return new_price, base_price


def get_nintendo_prices(game_name, driver=None):
    """
    Fetches the current and base price of the game that matches the name in the GAMES_TO_CHECK dict
    """
    # set up chrome driver
    if not driver:
        driver = start_chrome_driver()

    game_site = GAMES_TO_CHECK.get(game_name)["xbox_site"]

    # navigate to the website
    driver.get(game_site)

    # wait for the product grid to load
    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".W990N"))
    )

    "sc-1i9d4nw-10"

    new_price_element = price_card_element.find_element(By.CSS_SELECTOR, "span.psw-t-title-m")
    base_price_elements = price_card_element.find_elements(By.CSS_SELECTOR, "span.psw-t-title-s")

    base_price_element = base_price_elements[0] if base_price_elements else new_price_element

    new_price = re.findall(r'\d+,\d+', new_price_element.text)
    base_price = re.findall(r'\d+,\d+', base_price_element.text)


if __name__ == "__main__":
    driver = start_chrome_driver()

    # Example usage of the get_game_prices function
    # Uncomment the lines below to test with specific games or change the game names to 
    # match your JSON file

    # clair_obscur_prices = get_psn_prices("Jedi Survivor")
    # clair_obscur_prices = get_psn_prices("Expedition 33")

    # clair_obscur_prices = get_xbox_prices("Expedition 33")
    # clair_obscur_prices = get_xbox_prices("Jedi Survivor")
    # clair_obscur_prices = get_xbox_prices("Resident Evil Village")

    exit_chrome_driver(driver)
