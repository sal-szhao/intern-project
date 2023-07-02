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
# options.add_argument("--disable-dev-shm-usage")
# options.page_load_strategy = "eager"
prefs = {"profile.managed_default_content_settings.images": 2}
options.add_experimental_option("prefs", prefs)
driver = webdriver.Chrome(service=service, options=options)

# Will be refreshing the page ???
# driver.implicitly_wait(0.5)
