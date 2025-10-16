## AfricaEnergy/extract

This file/module is used to extract data using Selenium + BeautifulSoup4 for African energy data from the AEP Database webpage

### 1. `driver.py`
This module contains the Selenium web driver configurations together with BeautifulSoup's `soup`.
This allows for easier configuration of Selenium and bs4 anywhere in this project.

### 2. `scrape.py`
Scrapes data from AEP Database webpage using Selenium and bs4 and gets data into a structured format.
After scraping, data is stored into `staging_data/{sector_name}.csv`