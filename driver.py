from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Driver initialization.
# chrome_driver_binary = "./chromedriver"
service = Service(executable_path=r'./chromedriver')

options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
# options.headless = True
# options.binary_location = "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe"
prefs = {"profile.managed_default_content_settings.images": 2}
options.add_experimental_option("prefs", prefs)
driver = webdriver.Chrome(service=service, options=options)
