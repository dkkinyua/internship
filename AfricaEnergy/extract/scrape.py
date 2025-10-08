import re
import time
import pandas as pd
from driver import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://africa-energy-portal.org/database"


def scrape_sector_data(driver, sector_name):
    """Scrape all data for a specific sector"""
    all_data = []

    print(f"\n{'='*60}")
    print(f"Starting to scrape sector: {sector_name.upper()}")
    print(f"{'='*60}\n")

    try:
        # Select the sector from dropdown
        print(f"Selecting sector: {sector_name}")
        
        select2_selection = WebDriverWait(driver.driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".maingrouping-select + .select2 .select2-selection__rendered"))
        )
        
        current_sector = select2_selection.text.strip()
        print(f"  Current sector: {current_sector}")
        
        if current_sector != sector_name:
            select2_parent = driver.driver.find_element(By.CSS_SELECTOR, ".maingrouping-select + .select2")
            driver.driver.execute_script("arguments[0].scrollIntoView(true);", select2_parent)
            driver.wait(1)
            
            driver.driver.execute_script("arguments[0].click();", select2_parent)
            driver.wait(2)
            
            try:
                options = WebDriverWait(driver.driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".select2-results__option"))
                )
            except:
                print("  Retrying dropdown open...")
                driver.driver.execute_script("arguments[0].click();", select2_parent)
                driver.wait(2)
                options = WebDriverWait(driver.driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".select2-results__option"))
                )
            
            sector_found = False
            for opt in options:
                if opt.text.strip() == sector_name:
                    driver.driver.execute_script("arguments[0].click();", opt)
                    driver.wait(3)
                    print(f"✓ Sector '{sector_name}' selected")
                    sector_found = True
                    break
            
            if not sector_found:
                print(f"✗ Sector '{sector_name}' not found")
                return all_data
        else:
            print(f"✓ Sector '{sector_name}' already selected")

        # Click "SELECT ALL THEMES" checkbox
        print("Selecting all themes...")
        select_all_checkbox = WebDriverWait(driver.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f"//input[@class='select-all-themes' and @name='{sector_name}']"))
        )
        driver.driver.execute_script("arguments[0].scrollIntoView(true);", select_all_checkbox)
        
        if select_all_checkbox.is_selected():
            driver.driver.execute_script("arguments[0].click();", select_all_checkbox)
            driver.wait(1)
        
        driver.driver.execute_script("arguments[0].click();", select_all_checkbox)
        driver.wait(2)
        print("✓ All themes selected")

        # Select ALL years before clicking APPLY
        print("Selecting all years (2000-2024)...")
        try:
            # Find and click the year filter label to open dropdown
            year_filter_label = WebDriverWait(driver.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'year-filter-field')]//a[contains(@class, 'filter-field-label')]"))
            )
            driver.driver.execute_script("arguments[0].scrollIntoView(true);", year_filter_label)
            driver.driver.execute_script("arguments[0].click();", year_filter_label)
            driver.wait(2)
            
            # Find and click "All" checkbox for years
            year_all_checkbox = driver.driver.find_element(By.XPATH, 
                "//div[contains(@class, 'year-filter-field')]//span[@class='checkbox-label' and text()='All']/preceding-sibling::input"
            )
            
            # First uncheck if already checked (to ensure clean state)
            if year_all_checkbox.is_selected():
                driver.driver.execute_script("arguments[0].click();", year_all_checkbox)
                driver.wait(1)
            
            # Then check it to select all years
            driver.driver.execute_script("arguments[0].click();", year_all_checkbox)
            driver.wait(2)
            print("✓ All years selected")
            
            # Close the year dropdown
            driver.driver.execute_script("arguments[0].click();", year_filter_label)
            driver.wait(1)
        except Exception as e:
            print(f"⚠ Could not select all years: {e}")
            print("  Continuing anyway...")

        # Click APPLY button
        print("Clicking APPLY button...")
        apply_button = WebDriverWait(driver.driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "apply-btn"))
        )
        driver.driver.execute_script("arguments[0].scrollIntoView(true);", apply_button)
        driver.driver.execute_script("arguments[0].click();", apply_button)
        driver.wait(8)  # Increased wait time for all years to load
        print("✓ APPLY button clicked, waiting for data to load...")

        # Wait for chart to appear
        try:
            WebDriverWait(driver.driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "highcharts-container"))
            )
            print("✓ Charts loaded successfully")
        except Exception as e:
            print(f"✗ Charts did not load: {e}")
            return all_data

        # Extract data from charts
        print("\nExtracting data from charts...")
        chart_data = extract_chart_data(driver, sector_name)
        
        all_data.extend(chart_data)

        print(f"\n✓ Completed scraping {sector_name}: {len(all_data)} rows extracted")

    except Exception as e:
        print(f"✗ Error scraping sector {sector_name}: {e}")
        import traceback
        traceback.print_exc()

    return all_data


def extract_chart_data(driver, sector_name):
    """Extract data from all Highcharts on the page"""
    all_rows = []
    
    # Get all selected indicators with their metadata
    indicators_metadata = []
    try:
        selected_indicators = driver.driver.find_elements(By.CSS_SELECTOR, ".indicator-select:checked")
        for ind in selected_indicators:
            indicator_label = ind.get_attribute("value") or ""
            unit = ind.get_attribute("data-unit") or ""
            theme = ind.get_attribute("data-theme") or ""
            
            # Extract metric from label (text before parenthesis)
            if "(" in indicator_label:
                metric = indicator_label.split("(")[0].strip()
                # Remove trailing dashes
                metric = metric.rstrip(" -")
            else:
                metric = indicator_label
            
            indicators_metadata.append({
                "label": indicator_label,
                "metric": metric,
                "unit": unit,
                "theme": theme
            })
        print(f"  Found {len(indicators_metadata)} selected indicators")
    except Exception as e:
        print(f"  Warning: Could not extract indicator metadata: {e}")
    
    # Enhanced JavaScript to extract chart data - gets ALL years
    extract_script = """
    var allData = [];
    if (Highcharts && Highcharts.charts) {
        Highcharts.charts.forEach(function(chart, chartIndex) {
            if (!chart || !chart.series || chart.series.length === 0) return;
            
            var chartTitle = chart.title ? chart.title.textStr : '';
            var yAxisTitle = chart.yAxis && chart.yAxis[0] && chart.yAxis[0].axisTitle 
                ? chart.yAxis[0].axisTitle.textStr 
                : '';
            
            var hasCategories = chart.xAxis && chart.xAxis[0] && chart.xAxis[0].categories && chart.xAxis[0].categories.length > 0;
            var categories = hasCategories ? chart.xAxis[0].categories : [];
            
            // Countries on X-axis (categories), Years as series
            if (hasCategories && categories.length > 0) {
                categories.forEach(function(country, countryIndex) {
                    var yearData = {};
                    
                    // Iterate through ALL series (each series is a year)
                    chart.series.forEach(function(series) {
                        if (series.data && series.data[countryIndex]) {
                            var point = series.data[countryIndex];
                            if (point && point.y !== null && point.y !== undefined) {
                                var year = series.name;
                                yearData[year] = point.y;
                            }
                        }
                    });
                    
                    // Only add if we have data for this country
                    if (Object.keys(yearData).length > 0) {
                        allData.push({
                            chartIndex: chartIndex,
                            chartTitle: chartTitle,
                            yAxisTitle: yAxisTitle,
                            country: country,
                            yearData: yearData
                        });
                    }
                });
            }
        });
    }
    return allData;
    """
    
    try:
        chart_data_list = driver.driver.execute_script(extract_script)
        
        if not chart_data_list:
            print("  ✗ No chart data found")
            return all_rows
        
        print(f"  Found {len(chart_data_list)} country-indicator combinations")
        
        # Group data by chart index
        charts_by_index = {}
        for data in chart_data_list:
            chart_idx = data.get("chartIndex", 0)
            if chart_idx not in charts_by_index:
                charts_by_index[chart_idx] = []
            charts_by_index[chart_idx].append(data)
        
        # Create country serial mapping that resets for each indicator
        country_serial_map = {}
        
        # Process each chart
        for chart_idx, chart_countries_list in sorted(charts_by_index.items()):
            # Get indicator metadata for this chart
            if chart_idx < len(indicators_metadata):
                indicator = indicators_metadata[chart_idx]
                sub_sector = indicator["theme"]
                sub_sub_sector = indicator["label"]
                metric = indicator["metric"]
                unit = indicator["unit"]
            else:
                # Fallback to chart title
                sample_data = chart_countries_list[0]
                chart_title = sample_data.get("chartTitle")
                unit = sample_data.get("yAxisTitle", "")
                
                # Handle None chart_title
                if chart_title and "(" in chart_title:
                    metric = chart_title.split("(")[0].strip().rstrip(" -")
                    sub_sub_sector = chart_title
                elif chart_title:
                    metric = chart_title
                    sub_sub_sector = chart_title
                else:
                    metric = "Unknown"
                    sub_sub_sector = "Unknown"
                
                sub_sector = "Unknown"
            
            print(f"    Processing Chart {chart_idx + 1}: {sub_sub_sector}")
            
            # Reset country serial for each indicator
            indicator_key = f"{sub_sector}_{metric}_{unit}"
            if indicator_key not in country_serial_map:
                country_serial_map[indicator_key] = {}
            
            country_counter = 1
            
            # Process each country in this chart
            for data in chart_countries_list:
                country = data.get("country", "Unknown")
                year_data = data.get("yearData", {})
                
                # Assign country serial (resets after 55 countries)
                if country not in country_serial_map[indicator_key]:
                    country_serial_map[indicator_key][country] = country_counter
                    country_counter += 1
                    if country_counter > 55:
                        country_counter = 1
                
                country_serial = country_serial_map[indicator_key][country]
                
                # Initialize row
                row_dict = {
                    "country": country,
                    "country_serial": country_serial,
                    "metric": metric,
                    "unit": unit,
                    "sector": sector_name,
                    "sub_sector": sub_sector,
                    "sub_sub_sector": sub_sub_sector,
                    "source_link": BASE_URL,
                    "source": "Africa Energy Portal"
                }
                
                # Initialize all year columns with empty values
                for year in range(2000, 2025):
                    row_dict[str(year)] = ""
                
                # Populate year data
                for year_str, value in year_data.items():
                    # Clean year string (remove any extra text)
                    year_clean = re.search(r'(20\d{2})', str(year_str))
                    if year_clean:
                        year_key = year_clean.group(1)
                        if year_key in row_dict:
                            row_dict[year_key] = value
                
                all_rows.append(row_dict)
                
                # Log with year info
                years_with_data = [y for y in year_data.keys()]
                if years_with_data:
                    print(f"      ✓ {country} (serial: {country_serial}): {len(years_with_data)} years")
    
    except Exception as e:
        print(f"  ✗ Error extracting chart data: {e}")
        import traceback
        traceback.print_exc()
    
    return all_rows


def scrape_all_sectors():
    """Main function to scrape all sectors"""
    sectors = ["Electricity", "Energy", "Social and Economic"]
    
    driver = Driver()
    driver.setup_driver(headless=False)
    
    try:
        # Navigate to the database page
        print(f"Navigating to {BASE_URL}")
        driver.driver.get(BASE_URL)
        driver.wait(3)
        
        # Handle cookie banner
        try:
            cookie_button = WebDriverWait(driver.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, 
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept') or "
                    "contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree') or "
                    "contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ok')]"
                ))
            )
            driver.driver.execute_script("arguments[0].click();", cookie_button)
            print("✓ Cookie banner closed")
            driver.wait(2)
        except:
            print("No cookie banner found")
        
        # Scrape each sector
        for sector in sectors:
            sector_data = scrape_sector_data(driver, sector)
            
            if sector_data:
                # Convert to DataFrame
                df = pd.DataFrame(sector_data)
                
                # Ensure all year columns exist
                for year in range(2000, 2025):
                    if str(year) not in df.columns:
                        df[str(year)] = ""
                
                # Reorder columns
                columns = [
                    "country", "country_serial", "metric", "unit", "sector",
                    "sub_sector", "sub_sub_sector", "source_link", "source"
                ] + [str(year) for year in range(2000, 2025)]
                df = df[columns]
                
                # Save to CSV
                filename = f"africa_energy_{sector.lower().replace(' ', '_')}_data.csv"
                df.to_csv(filename, index=False)
                print(f"\n✓ Saved {sector} data to {filename} ({len(df)} rows)\n")
                
                # Print summary
                print(f"Summary for {sector}:")
                print(f"  - Unique countries: {df['country'].nunique()}")
                print(f"  - Unique metrics: {df['metric'].nunique()}")
                print(f"  - Sub-sectors: {df['sub_sector'].unique().tolist()}")
            else:
                print(f"\n✗ No data collected for {sector}\n")
            
            # Navigate back to base page for next sector
            if sector != sectors[-1]:
                print(f"\nNavigating back to base page for next sector...")
                driver.driver.get(BASE_URL)
                driver.wait(5)
    
    finally:
        driver.close_driver()
        print("\n" + "="*60)
        print("Scraping completed!")
        print("="*60)


if __name__ == "__main__":
    scrape_all_sectors()