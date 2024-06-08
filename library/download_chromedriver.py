import requests
import zipfile
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

def get_chromedriver_download_url():
    url = "https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Failed to fetch the versions JSON.")
    
    versions = response.json()
    for milestone_key, milestone_value in versions["milestones"].items():
        if milestone_value["milestone"] == 125:  # Adjust the milestone as needed
            for download in milestone_value["downloads"]["chromedriver"]:
                if download["platform"] == "win64":
                    return download["url"]
    raise Exception("No matching version found.")

def download_and_extract_chromedriver(url, extract_to="."):
    response = requests.get(url)
    zip_path = "chromedriver.zip"
    with open(zip_path, "wb") as file:
        file.write(response.content)

    if zipfile.is_zipfile(zip_path):
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_to)
        print("Extraction completed successfully.")
    else:
        print("Downloaded file is not a valid zip file.")
    os.remove(zip_path)

def setup_selenium_driver(chrome_driver_path):
    service = Service(chrome_driver_path)
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--ignore-certificate-errors')  # Ignore SSL certificate errors

    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def main():
    try:
        chromedriver_url = get_chromedriver_download_url()
        download_and_extract_chromedriver(chromedriver_url, "C:/DaDudeKC/selenium-4.21.0/selenium-4.21.0/chromedriver-win64")

        # Set up Selenium WebDriver
        chrome_driver_path = "C:/DaDudeKC/selenium-4.21.0/selenium-4.21.0/chromedriver-win64/chromedriver.exe"
        driver = setup_selenium_driver(chrome_driver_path)

        # Example Selenium usage
        driver.get("https://www.google.com")

        # Add a delay to ensure the page loads completely
        time.sleep(5)

        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys("Selenium testing" + Keys.RETURN)
        print(driver.title)

        driver.quit()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
