import configparser
import json
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


class AuthManager:
    """Handles JOBKOREA login with session caching."""

    def __init__(self, config_path='config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        self.session_file = Path('session.json')
        self.driver = None
        self.logger = logging.getLogger(__name__)

    def _init_driver(self, headless=True):
        """Initialize Selenium WebDriver."""
        options = Options()
        # if headless:
            # options.add_argument("--headless=new")
        self.driver = webdriver.Chrome(options=options)
        self.logger.info("WebDriver initialized")

    def _save_session(self):
        """Save session cookies to file."""
        if self.driver:
            cookies = self.driver.get_cookies()
            with open(self.session_file, 'w') as f:
                json.dump(cookies, f)
            self.logger.info("Session cookies saved to session.json")

    def _load_session(self):
        """Load session cookies from file."""
        if self.session_file.exists():
            try:
                self._init_driver(headless=True)
                self.driver.get("https://www.jobkorea.co.kr/")  # Navigate to base URL to set cookies
                with open(self.session_file, 'r') as f:
                    cookies = json.load(f)
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
                self.driver.refresh()
                self.logger.info("Session cookies loaded")
                # Check if still logged in
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, '//a[contains(text(), "로그아웃")]'))
                    )
                    self.logger.info("Session restored successfully")
                    return True
                except:
                    self.logger.info("Session expired, need to re-login")
                    return False
            except Exception as e:
                self.logger.error(f"Failed to load session: {e}")
                return False
        return False

    def login(self):
        """Log into JOBKOREA with credentials from config.ini."""
        try:
            # Try loading session first
            if self._load_session():
                return self.driver

            # Initialize driver if session loading fails
            self._init_driver(headless=self.config.getboolean('crawling', 'headless'))

            # Navigate to login page
            url = self.config.get('web', 'url')
            self.logger.info(f"Navigating to login page: {url}")
            self.driver.get(url)

            # Select Individual Member tab
            self.logger.info("Selecting Individual Member tab")
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//li[@data-tab="tab1"]/a[@data-m-type="M"]'))
            ).click()

            # Enter credentials
            username = self.config.get('web', 'username')
            password = self.config.get('web', 'password')
            self.logger.info("Entering login credentials")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'M_ID'))
            )
            self.driver.find_element(By.ID, 'M_ID').send_keys(username)
            self.driver.find_element(By.ID, 'M_PWD').send_keys(password)
            self.driver.find_element(By.CLASS_NAME, 'login-button').click()

            # Wait for post-login page
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//a[contains(text(), "로그아웃")]'))
            )
            self.logger.info("Login successful")

            # Save session cookies
            self._save_session()

            return self.driver

        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            if self.driver:
                self.driver.quit()
            raise

    def close(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            self.logger.info("WebDriver closed")
