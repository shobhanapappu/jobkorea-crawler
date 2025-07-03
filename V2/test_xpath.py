import configparser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Read config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# Get web and crawling settings
url = config.get('web', 'url')
username = config.get('web', 'username')
password = config.get('web', 'password')
xpath_title = config.get('crawling', 'xpath_post_title')
xpath_button = config.get('crawling', 'xpath_contact_button')

# Set up Selenium
options = Options()
# options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)

try:
    # Navigate to login page
    print(f"Navigating to {url}")
    driver.get(url)

    # Select Individual Member tab
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//li[@data-tab="tab1"]/a[@data-m-type="M"]'))
    ).click()
    print("Selected Individual Member tab")

    # Log in
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'M_ID'))
    )
    driver.find_element(By.ID, 'M_ID').send_keys(username)
    driver.find_element(By.ID, 'M_PWD').send_keys(password)
    driver.find_element(By.CLASS_NAME, 'login-button').click()

    # Wait for post-login page
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//a[contains(text(), "로그아웃")]'))
    )
    print("Login successful!")

    # Navigate to job listings page
    driver.get("https://www.jobkorea.co.kr/Search/")
    print("Navigating to job listings")

    # Find multiple job posts
    posts = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located(
            (By.XPATH, '//div[contains(@class, "Flex_display_flex__i0l0hl2 Flex_direction_column__i0l0hl4 h7nnv10")]'))
    )
    print(f"Found {len(posts)} job posts")

    # Test XPaths for up to 3 posts
    for i, post in enumerate(posts[:3], 1):
        try:
            # Find title within post
            title = post.find_element(By.XPATH, './/span[contains(@class, "Typography_variant_size18__344nw25")]')
            print(f"Post {i} Title: {title.text}")

            # Check for contact button
            button = post.find_element(By.XPATH, './/button[contains(@class, "SupportButton_root__1vwhuod0")]')
            print(f"Post {i} Button: {button.text}")

        except Exception as e:
            print(f"Post {i} Error: {str(e)}")

    driver.quit()

except Exception as e:
    print("Error:", str(e))
    driver.quit()
