import os
import asyncio
import yfinance as yf
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options

# ========================================================================================================================================================================
# Constants
# ========================================================================================================================================================================

# Selenium Constants
geckodriver_path = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "geckodriver.exe")
firefox_options = Options()
firefox_options.add_argument("--headless")

# ========================================================================================================================================================================
# Functions
# ========================================================================================================================================================================

# This function is used to get the stock data from the ticker
async def generateStockFromTicker(ticker, period='1d') -> tuple:
    stock_panda = yf.download(ticker, period=period, prepost=True)
    stock_info = yf.Ticker(ticker)

    return stock_panda, stock_info
    

# This function is used to get the Fear and Greed Index
async def getFearGreedIndex() -> BytesIO | None:
    # Initialize WebDriver
    try:
        service = Service(geckodriver_path)
        driver = webdriver.Firefox(service=service, options=firefox_options)
        driver.maximize_window()

        # Get webpage
        driver.get(f'https://money.cnn.com/data/fear-and-greed/')
        await asyncio.sleep(1)

        # Get Fear and Greed Index
        element = driver.find_element(By.NAME, 'fng-index').find_element(By.XPATH, '..')
        screenshot = element.screenshot_as_png
        image = BytesIO(screenshot)

        # Close WebDriver
        driver.quit()

        return image
    except:
        return None