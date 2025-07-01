from selenium import webdriver
from selenium.webdriver.chrome.options import Options
options = Options()
options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)
driver.get("https://www.jobkorea.co.kr/")
print(driver.title)  # Should print JOBKOREA’s page title
driver.quit()