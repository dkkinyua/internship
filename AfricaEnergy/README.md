# AfricaEnergy

This project shows the extraction, transformation and loading of African energy data between 2000 and 2022. Data is extracted through Selenium and BeautifulSoup, which runs in headless mode in production and visual mode in testing, transformed using pandas and loaded into MongoDB collections categorized by sectors i.e Electricity, Supply and Social & Economic sectors.

## Project Setup.
### 1. Clone this project
```bash
git clone https://github.com/dkkinyua/internship.git
cd AfricaEnergy
```

### 2. Set virtual environment and install project dependencies
#### a. Set up virtual environment
```bash
python3 -m venv myenv
source myenv/bin/activate # MacOS / Linux
./myenv/Scripts/activate # Windows
```
#### b. Install project dependencies

**NOTE: Ensure that virtual environment has been activated**

```bash
pip install -r requirements.txt
```

#### 3. Running the scraper

```bash
python3 extract/scrape.py
```

