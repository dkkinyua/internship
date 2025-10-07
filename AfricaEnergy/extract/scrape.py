import re
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

"""
initialize Driver class to setup, close driver and set up soup efficiently. this is very efficient as i can use the Driver methods wherever i want to use them instead of setting up and closing driver each time I use it. I can also import it to other modules if need be.

setup_driver(headless=False) sets up the chrome driver for scraping, the headless param helps in switching between headless and visible scraping for testing, default=False for visible scraping.
close_driver() closes driver when scraping is complete
get_soup() sets up soup for scraping html content from page content extracted from selenium's driver
wait() allows the driver to wait before sending any more requests to the browser, this allows for respectful scraping
"""

class Driver:
    def __init__(self):
        self.driver = None

    def setup_driver(self, headless=False):
        options = Options()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox") 
        options.add_argument("--disable-dev-shm-usage") 
        options.add_argument("--disable-gpu") 
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled") 
        options.add_argument("--disable-infobars") 
        options.add_argument("--start-maximized")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--log-level=3")

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        print("Driver is set up successfully!")

    def close_driver(self):
        if self.driver:
            self.driver.quit()
            print("Driver has been closed successfully!")
        else:
            print("Driver is not set up or not available")

    def get_soup(self):
        if not self.driver:
            raise Exception("Driver not set up first, run setup_driver() first for soup to work")
        return BeautifulSoup(self.driver.page_source, 'html.parser')
    
    def wait(self, secs=3):
        time.sleep(secs)

