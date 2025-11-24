# import necessary tools from the selenium library
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# set up chrome driver
service = Service()
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
driver = webdriver.Chrome(service=service, options=options)

import re

# ...

games_to_check = {
    "Outlaws": "https://isthereanydeal.com/game/outlaws-and-handful-of-missions-remaster/info",
    "Kingdom Hearts": "https://isthereanydeal.com/game/kingdom-hearts-hd-1-5-and-2-5-remix/info",
    "Beyond Good and Evil": "https://isthereanydeal.com/game/beyond-good-and-evil/info"
}

def get_store_links(game_name):
    game_site = games_to_check.get(game_name)

    # navigate to the target webpage
    driver.get(game_site)

    # wait for the product grid to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".cell"))
    )

    elements = driver.find_elements(By.CSS_SELECTOR, ".row")

    for element in elements:
        element_text = element.text

        if not (element_text.startswith("Steam\n") or element_text.startswith("GOG\n")):
            continue

        link = element.get_attribute("href")

        if "Steam" in element_text:
            get_steam_link(link)
        if "GOG" in element_text:
            get_gog_link(link)


def get_store_link(store_link, css_selector, price_label, price_fetch_function):
    store_driver = webdriver.Chrome(service=service, options=options)
    store_driver.get(store_link)

    # wait for the product grid to load
    WebDriverWait(store_driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector))
    )

    print(f"{price_label} Page URL:")
    print(store_driver.current_url)

    current_price, base_price = price_fetch_function(store_driver)

    print(f"{price_label} current price for game:", current_price if current_price else "No price found")
    print(f"{price_label} base price for game:", base_price if base_price else "No price found")

    store_driver.quit()


def get_steam_link(store_link):
    get_store_link(store_link, ".btn_green_steamui", "Steam", 
                   get_steam_current_and_base_prices)
    

def get_steam_current_and_base_prices(store_driver):
    """
    Returns the current and base prices from a Steam store page.
    """
    try:
        current_price_element = store_driver.find_element(By.CSS_SELECTOR, ".discount_final_price")
        base_price_element = store_driver.find_element(By.CSS_SELECTOR, ".discount_original_price")
    except:
        current_price_element = store_driver.find_element(By.CSS_SELECTOR, ".game_purchase_price")
        base_price_element = current_price_element

    current_price = current_price_element.text
    base_price = base_price_element.text

    current_price_value = re.findall(r'\d+,\d+', current_price)[0].replace(',', '.').strip()
    base_price_value = re.findall(r'\d+,\d+', base_price)[0].replace(',', '.').strip()

    return current_price_value, base_price_value


def get_gog_link(store_link):
    get_store_link(store_link, ".product-actions-price__final-amount", "GOG", 
                   get_gog_current_and_base_prices)


def get_gog_current_and_base_prices(store_driver):
    """
    Returns the current and base prices from a GOG store page.
    """
    try:
        current_price_element = store_driver.find_element(By.CSS_SELECTOR, ".product-actions-price__final-amount")
        base_price_element = store_driver.find_element(By.CSS_SELECTOR, ".product-actions-price__base-amount")
    except:
        current_price_element = store_driver.find_element(By.CSS_SELECTOR, ".product-actions-price__final-amount")
        base_price_element = current_price_element

    current_price = current_price_element.text
    base_price = base_price_element.text

    current_price_value = re.findall(r'\d+\.\d+', current_price)[0].strip()
    base_price_value = re.findall(r'\d+\.\d+', base_price)[0].strip()

    return current_price_value, base_price_value


get_store_links("Beyond Good and Evil")
get_store_links("Kingdom Hearts")

# close the browser
driver.quit()
