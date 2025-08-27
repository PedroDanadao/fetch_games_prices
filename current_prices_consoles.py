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

# DEBUG
# GAMES_TO_CHECK = {
#     "Expedition 33": {
#         "psn_site": "https://store.playstation.com/pt-br/product/EP7579-PPSA17599_00-EXP33000000PS5EU",
#         "xbox_site": "https://www.xbox.com/pt-br/games/store/clair-obscur-expedition-33/9ppt8k6gqhrz"
#     },
#     "Jedi Survivor": {
#         "psn_site": "https://store.playstation.com/pt-br/product/UP0006-PPSA07783_00-APPLEJACKGAME000",
#         "xbox_site": "https://www.xbox.com/pt-br/games/store/star-wars-jedi-survivor/9pgc82v0dxfs"
#     },
#     "Resident Evil Village": {
#         "xbox_site": "https://www.xbox.com/pt-br/games/store/resident-evil-village/9N2S04LGXXH4"
#     },
#     "Donkey Kong": {
#         "nintendo_site":"https://www.nintendo.com/pt-br/store/products/donkey-kong-bananza-switch-2"
#     },
#     "Spiritfarer": {
#         "nintendo_site": "https://www.nintendo.com/pt-br/store/products/spiritfarer-switch"
#     }
# }


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
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.psw-fill-x"))
    )

    price_card_element = driver.find_element(By.CSS_SELECTOR, ".psw-c-bg-card-1")
    new_price_elements = price_card_element.find_elements(By.CSS_SELECTOR, "span.psw-t-title-m")
    
    for element in new_price_elements:
        new_price_element = element
        if re.findall(r'\d+,\d+', element.text):
            break

    base_price_elements = price_card_element.find_elements(By.CSS_SELECTOR, "span.psw-t-title-s")

    base_price_element = base_price_elements[0] if base_price_elements else new_price_element

    new_price = re.findall(r'\d+,\d+', new_price_element.text)
    base_price = re.findall(r'\d+,\d+', base_price_element.text)

    return base_price, new_price


def get_xbox_prices(game_name, driver=None):
    """
    Fetches the current and base price of the game that matches the name in the GAMES_TO_CHECK dict
    """
    new_price, base_price = get_site_price(game_name, driver, site_key="xbox_site",
                                           waiter_selector=".CommonButtonStyles-module__variableLineDesktopButton___cxDyV",
                                           new_price_selector=".Price-module__boldText___1i2Li",
                                           base_price_selector=".Price-module__brandOriginalPrice___ayJAn")
    
    return base_price[0], new_price[0]


def get_nintendo_prices(game_name, driver=None):
    """
    Fetches the current and base price of the game that matches the name in the GAMES_TO_CHECK dict
    """
    base_price, new_price = get_site_price(game_name, driver, site_key="nintendo_site", waiter_selector=".W990N", 
                                           new_price_selector=".W990N",base_price_selector=".o2BsP")
    
    return base_price[0], new_price[0]


def get_site_price(game_name, driver=None, site_key="psn_site", waiter_selector='', new_price_selector='', 
                   base_price_selector='', price_card_selector=''):
    """
    Fetches the current and base price of the game that matches the name in the GAMES_TO_CHECK dict
    """
    # set up chrome driver
    if not driver:
        driver = start_chrome_driver()

    game_site = GAMES_TO_CHECK.get(game_name)[site_key]

    # navigate to the website
    driver.get(game_site)

    # wait for the product grid to load
    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, waiter_selector))
    )

    parent_element = driver

    if price_card_selector:
        price_card_element = driver.find_element(By.CSS_SELECTOR, price_card_selector)
        parent_element = price_card_element

    new_price_element = parent_element.find_element(By.CSS_SELECTOR, new_price_selector)
    base_price_elements = parent_element.find_elements(By.CSS_SELECTOR, base_price_selector)

    base_price_element = base_price_elements[0] if base_price_elements else new_price_element

    new_price = re.findall(r'\d+,\d+', new_price_element.text)
    base_price = re.findall(r'\d+,\d+', base_price_element.text)

    return new_price, base_price


if __name__ == "__main__":
    driver = start_chrome_driver()

    # Example usage of the get_game_prices function
    # Uncomment the lines below to test with specific games or change the game names to 
    # match your JSON file

    # get_psn_prices("Jedi Survivor")
    get_psn_prices("Expedition 33")

    # get_xbox_prices("Expedition 33")
    # get_xbox_prices("Jedi Survivor")
    # get_xbox_prices("Resident Evil Village")

    # get_nintendo_prices("Donkey Kong")
    # get_nintendo_prices("Spiritfarer")

    exit_chrome_driver(driver)
