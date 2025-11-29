# import necessary tools from the selenium library
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import json
from pathlib import Path
from typing import Optional

# ...


DEBUG = False


def start_chrome_driver():
    """Initialize and return a Chrome WebDriver instance."""
    service = Service()
    options = webdriver.ChromeOptions()

    if not DEBUG:
        options.add_argument("--headless=new")
    
    return webdriver.Chrome(service=service, options=options)

def exit_chrome_driver(driver: webdriver.Chrome):
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

def update_games_to_check():
    """Update the games to check from the JSON file."""
    global GAMES_TO_CHECK
    try:
        with open(json_path, "r") as json_file:
            GAMES_TO_CHECK = json.load(json_file)
    except FileNotFoundError:
        print(f"Error: The file {json_path} does not exist. Set the games to check using the ui")
        GAMES_TO_CHECK = {}

    return GAMES_TO_CHECK


def check_steam_comming_soon(store_driver: webdriver.Chrome) -> bool:
    """
    Checks if the Steam store page indicates a "Coming Soon" status.
    """
    try:
        coming_soon_element = store_driver.find_element(By.CSS_SELECTOR, ".game_area_comingsoon")
        if coming_soon_element:
            return True
    except:
        return False
    return False


def get_valid_purchase_action_bg(store_driver: webdriver.Chrome) -> Optional[webdriver.remote.webelement.WebElement]:
    """
    Returns the first valid purchase action background element that contains price information.
    """
    purchase_area_elements = store_driver.find_elements(By.CSS_SELECTOR, ".game_purchase_action_bg")
    
    for element in purchase_area_elements:
        try:
            # Check if the element contains price information
            element.find_element(By.CSS_SELECTOR, ".discount_final_price")
            return element
        except:
            try:
                element.find_element(By.CSS_SELECTOR, ".game_purchase_price")
                return element
            except:
                continue
    return None


def get_steam_original_price(purchase_area_element: webdriver.remote.webelement.WebElement) -> webdriver.remote.webelement.WebElement:
    """
    Returns the original price from a Steam store page. In some cases it only has the final price 
    element and it throws an error, this function handles that.
    """
    try:
        base_price_element = purchase_area_element.find_element(By.CSS_SELECTOR, ".discount_original_price")
    except:
        base_price_element = purchase_area_element.find_element(By.CSS_SELECTOR, ".discount_final_price")

    return base_price_element


def get_steam_prices_direct(driver: webdriver.Chrome, steam_link: str) -> tuple[str, str]:
    """Get Steam prices directly from Steam store page."""
    import re
    import time
    try:
        driver.get(steam_link)
        
        # Check if we hit an age verification page
        if "agecheck" in driver.current_url:
            try:
                # Wait for age gate elements to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "main_content_ctn"))
                )
                
                # Check if year input exists
                try:
                    year_select = driver.find_element(By.ID, "ageYear")
                    # Year input exists, select 1990
                    year_select.click()
                    year_option = driver.find_element(By.CSS_SELECTOR, "option[value='1990']")
                    year_option.click()
                    time.sleep(0.5)  # Wait for button to update
                    
                    # Click the "View Page" button
                    view_page_button = driver.find_element(By.ID, "view_product_page_btn")
                    view_page_button.click()
                except:
                    # Year input not present, remove agecheck from URL and navigate
                    current_url = driver.current_url
                    # Remove agecheck part from URL
                    clean_url = current_url.replace("/agecheck", "").split("?")[0]
                    driver.get(clean_url)
                
                # Wait a bit for the page to load
                time.sleep(2)
            except Exception as e:
                print(f"Error fetching Steam link: {steam_link}")
                print(f"Age verification handling error: {str(e)}")
                return "0,0", "0,0"
        
        # wait for the steam game page to load(.breadcrumbs element loaded)
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".breadcrumbs"))
        )

        # this is here in case a game is marked as coming soon(does not have prices)
        if check_steam_comming_soon(driver):
            return "0,0", "0,0"

        # we get the prices from the first purchase area of the page to avoid DLCs or bundles
        purchase_area_element = get_valid_purchase_action_bg(driver)
        if not purchase_area_element:
            return "0,0", "0,0"
        
        try:
            current_price_element = purchase_area_element.find_element(By.CSS_SELECTOR, ".discount_final_price")
            base_price_element = get_steam_original_price(purchase_area_element)
        except:
            current_price_element = purchase_area_element.find_element(By.CSS_SELECTOR, ".game_purchase_price")
            base_price_element = current_price_element
        
        current_price = current_price_element.text
        base_price = base_price_element.text
        
        current_price_value = re.findall(r'\d+,\d+', current_price)
        base_price_value = re.findall(r'\d+,\d+', base_price)
        
        return (
            current_price_value[0] if current_price_value else "0,0",
            base_price_value[0] if base_price_value else "0,0"
        )
    except Exception as e:
        print(f"Error fetching Steam prices: {e}")
        return "0,0", "0,0"


def get_gog_prices_direct(driver: webdriver.Chrome, gog_link: str) -> tuple[str, str]:
    """Get GOG prices directly from GOG store page."""
    try:
        driver.get(gog_link)
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-actions-price__final-amount"))
        )
        
        try:
            current_price_element = driver.find_element(By.CSS_SELECTOR, ".product-actions-price__final-amount")
            base_price_element = driver.find_element(By.CSS_SELECTOR, ".product-actions-price__base-amount")
        except:
            current_price_element = driver.find_element(By.CSS_SELECTOR, ".product-actions-price__final-amount")
            base_price_element = current_price_element
        
        current_price = current_price_element.text
        base_price = base_price_element.text
        
        # GOG uses . as decimal separator, convert to ,
        current_price_value = current_price.replace('.', ',') if current_price else "0,0"
        base_price_value = base_price.replace('.', ',') if base_price else "0,0"
        
        return current_price_value, base_price_value
    except Exception as e:
        print(f"Error fetching GOG prices: {e}")
        return "0,0", "0,0"


def get_game_prices(game_name: str, driver: webdriver.Chrome = None) -> dict:
    """Check the prices of a game on Steam and GOG."""
    # set up chrome driver
    if not driver:
        driver = start_chrome_driver()
    
    prices_data_dict = {}

    game_data = GAMES_TO_CHECK.get(game_name)
    
    # Check if game_data is a dict with direct store links
    if isinstance(game_data, dict):
        steam_link = game_data.get("steam_link")
        gog_link = game_data.get("gog_link")
        itad_link = game_data.get("isthereanydeal_link", "")
        
        prices_data_dict["is_there_any_deal_link"] = itad_link
        
        # Fetch from direct Steam link if available and valid
        if steam_link and steam_link not in ["non_existent", "link_not_fetched"]:
            steam_current, steam_base = get_steam_prices_direct(driver, steam_link)
            prices_data_dict["Steam_current"] = steam_current
            prices_data_dict["Steam_base"] = steam_base
            prices_data_dict["Steam_link"] = steam_link
        
        # Fetch from direct GOG link if available and valid
        if gog_link and gog_link not in ["non_existent", "link_not_fetched"]:
            gog_current, gog_base = get_gog_prices_direct(driver, gog_link)
            prices_data_dict["GOG_current"] = gog_current
            prices_data_dict["GOG_base"] = gog_base
            prices_data_dict["GOG_link"] = gog_link
    else:
        # Old format - use IsThereAnyDeal (string URL)
        game_site = game_data if game_data else ""
        
        if not game_site:
            return prices_data_dict
        
        # navigate to the target webpage
        driver.get(game_site)

        # wait for the product grid to load
        WebDriverWait(driver, 60).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".cell"))
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


if __name__ == "__main__":
    driver = start_chrome_driver()

    # Example usage of the get_game_prices function
    # Uncomment the lines below to test with specific games or change the game names to 
    # match your JSON file

    boltgun_prices = get_game_prices("Boltgun", driver)
    space_marine_prices = get_game_prices("Space Marine", driver)

    print("Boltgun Prices:", boltgun_prices)
    print("Space Marine Prices:", space_marine_prices)

    exit_chrome_driver(driver)
