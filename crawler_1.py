import configparser
import logging
import threading
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from auth import AuthManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class SiteCrawler(threading.Thread):
    """Background crawler for JOBKOREA job listings."""

    def __init__(self, config_path='config.ini', on_new_callback=None, on_status_callback=None):
        super().__init__(daemon=True)
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        self.on_new_callback = on_new_callback
        self.on_status_callback = on_status_callback
        self._stop = threading.Event()
        self.known_post_ids = set()  # Track processed post IDs
        self.auth = AuthManager(config_path)
        self.logger = logging.getLogger(__name__)
        self.start()

    def _apply_filters(self, driver):
        """Apply search filters: sort by posting date."""
        try:
            self.logger.info("Applying filter: sort by posting date")
            sort_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//select[@id="sorder"]/option[@value="reg_dt"]'))
            )
            sort_button.click()
            self.logger.info("Filter applied: sorted by registration date")
        except:
            self.logger.error("Failed to apply filters")

    def _scan_posts(self, driver):
        """Scan job listings, navigate to details URL, and return to continue processing."""
        posts_data = []
        original_url = ""

        try:
            # Store the original page URL
            try:
                original_url = driver.current_url
                self.logger.info("Stored original URL")
            except:
                self.logger.error("Failed to store original URL")
                return []

            # Wait for job listing elements to load
            try:
                posts = WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH,
                         '//div[contains(@class, "Flex_display_flex__i0l0hl2 Flex_direction_column__i0l0hl4 h7nnv10")]')
                    )
                )
                self.logger.info(f"Found {len(posts)} job posts")
            except:
                self.logger.error("Failed to load job posts")
                driver.get(original_url)
                return []

            for i, post in enumerate(posts, 1):  # Process all posts
                time.sleep(0.5)
                try:
                    # Re-fetch post to avoid stale element references
                    try:
                        posts = WebDriverWait(driver, 20).until(
                            EC.presence_of_all_elements_located(
                                (By.XPATH,
                                 '//div[contains(@class, "Flex_display_flex__i0l0hl2 Flex_direction_column__i0l0hl4 h7nnv10")]')
                            )
                        )
                        post = posts[i - 1]
                        self.logger.info(f"Re-fetched post {i}")
                    except:
                        self.logger.error(f"Post {i} - Failed to re-fetch post")
                        continue

                    # Extract post ID and details URL from the job link
                    post_id = ""
                    details_url = ""
                    try:
                        job_link = WebDriverWait(post, 15).until(
                            EC.presence_of_element_located((By.XPATH, './/a[contains(@href, "GI_Read")]'))
                        )
                        href = job_link.get_attribute('href')
                        post_id = href.split('GI_Read/')[1].split('?')[0]
                        details_url = href
                        self.logger.info(f"Extracted post ID: {post_id}, Details URL: {details_url}")
                    except:
                        self.logger.error(f"Post {i} - No job link found")
                        continue

                    # Check if post ID is already processed
                    try:
                        if post_id in self.known_post_ids:
                            self.logger.info(f"Post {post_id} already processed, skipping")
                            continue
                    except:
                        self.logger.error(f"Post {i} - Failed to check processed posts")
                        continue

                    # Check for contact button
                    try:
                        contact_button = post.find_elements(By.XPATH,
                                                            './/button[contains(@class, "SupportButton_root__1vwhuod0")]')
                        if not contact_button:
                            self.logger.info(f"Post {post_id}: No contact button, skipping")
                            continue
                    except:
                        self.logger.error(f"Post {i} - No contact button found")
                        continue

                    # Extract title
                    title = ""
                    try:
                        title_element = WebDriverWait(post, 15).until(
                            EC.presence_of_element_located(
                                (By.XPATH, './/span[contains(@class, "Typography_variant_size18__344nw25")]')
                            )
                        )
                        title = title_element.text.strip()
                        self.logger.info(f"Post {i} - Extracted title: {title}")
                    except:
                        self.logger.error(f"Post {i} - No title found")
                        continue

                    # Extract company name
                    company = ""
                    try:
                        company_element = WebDriverWait(post, 15).until(
                            EC.presence_of_element_located(
                                (By.XPATH, './/span[contains(@class, "Typography_variant_size16__344nw26")]')
                            )
                        )
                        company = company_element.text.strip()
                        self.logger.info(f"Post {i} - Extracted company: {company}")
                    except:
                        self.logger.error(f"Post {i} - No company name found")
                        continue

                    # Extract additional details
                    details = []
                    try:
                        details_elements = post.find_elements(By.XPATH,
                                                              './/span[contains(@class, "Typography_variant_size14__344nw27")]')
                        details = [elem.text.strip() for elem in details_elements]
                        self.logger.info(f"Post {i} - Extracted details: {details}")
                    except:
                        self.logger.error(f"Post {i} - No additional details found")

                    # Navigate to details URL
                    try:
                        self.logger.info(f"Post {post_id} - Navigating to details URL: {details_url}")
                        driver.get(details_url)
                        WebDriverWait(driver, 20).until(
                            EC.presence_of_element_located((By.XPATH, '//body'))  # Simple check to ensure page loads
                        )
                        self.logger.info(f"Post {post_id} - Successfully navigated to details page")
                    except:
                        self.logger.error(f"Post {post_id} - Failed to navigate to details page")
                        # Attempt to return to original page and continue
                        try:
                            driver.get(original_url)
                            WebDriverWait(driver, 20).until(
                                EC.presence_of_all_elements_located(
                                    (By.XPATH,
                                     '//div[contains(@class, "Flex_display_flex__i0l0hl2 Flex_direction_column__i0l0hl4 h7nnv10")]')
                                )
                            )
                            self.logger.info(
                                f"Post {post_id} - Recovered to listings page after failed details navigation")
                        except:
                            self.logger.error(
                                f"Post {post_id} - Failed to recover to listings page after details navigation")
                            continue

                    # Return to the original listings page
                    try:
                        driver.get(original_url)
                        WebDriverWait(driver, 20).until(
                            EC.presence_of_all_elements_located(
                                (By.XPATH,
                                 '//div[contains(@class, "Flex_display_flex__i0l0hl2 Flex_direction_column__i0l0hl4 h7nnv10")]')
                            )
                        )
                        self.logger.info(f"Post {post_id} - Returned to listings page")
                    except:
                        self.logger.error(f"Post {post_id} - Failed to return to listings page")
                        continue




                    # Append data to posts_data
                    try:
                        posts_data.append({
                            'id': post_id,
                            'title': title,
                            'company': company,
                            'details': details,
                            'details_url': details_url,
                            'manager_info': "Not found",  # Hard-coded as per user acceptance
                            'recruitment_details': ""  # Hard-coded as per user acceptance
                        })
                        self.known_post_ids.add(post_id)
                        self.logger.info(f"Post {post_id} extracted successfully")
                    except:
                        self.logger.error(f"Post {i} - Failed to append post data")

                except:
                    self.logger.error(f"Post {i} - General processing error")
                    try:
                        driver.get(original_url)
                        WebDriverWait(driver, 20).until(
                            EC.presence_of_all_elements_located(
                                (By.XPATH,
                                 '//div[contains(@class, "Flex_display_flex__i0l0hl2 Flex_direction_column__i0l0hl4 h7nnv10")]')
                            )
                        )
                        self.logger.info(f"Post {i} - Recovered to listings page")
                    except:
                        self.logger.error(f"Post {i} - Failed to recover to listings page")
                    continue

            return posts_data

        except:
            self.logger.error("General error in scanning posts")
            try:
                driver.get(original_url)
                self.logger.info("Returned to original URL after general error")
            except:
                self.logger.error("Failed to return to original URL")
            return []
    def run(self):
        """Main crawling loop with pagination."""
        try:
            driver = self.auth.login()
            self.logger.info("Starting crawler")
            if self.on_status_callback:
                self.on_status_callback("Crawler started")

            while not self._stop.is_set():
                try:
                    driver.get("https://www.jobkorea.co.kr/Search/")
                    self._apply_filters(driver)  # Apply sorting filter
                    current_page = 1
                    total_pages = None

                    while not self._stop.is_set():
                        # Scan posts on the current page
                        new_posts = self._scan_posts(driver)
                        time.sleep(1)
                        if new_posts and self.on_new_callback:
                            self.on_new_callback(new_posts)
                            self.logger.info(f"Found {len(new_posts)} new posts on page {current_page}")

                        # Find the next page link
                        try:
                            # Get all pagination links to determine total pages
                            if total_pages is None:
                                pagination_links = WebDriverWait(driver, 10).until(
                                    EC.presence_of_all_elements_located(
                                        (By.XPATH, '//nav[@aria-label="pagination"]//a[contains(@href, "Page_No")]')
                                    )
                                )
                                page_numbers = []
                                for link in pagination_links:
                                    href = link.get_attribute('href')
                                    if 'Page_No=' in href:
                                        try:
                                            page_num = int(href.split('Page_No=')[1].split('&')[0])
                                            page_numbers.append(page_num)
                                        except ValueError:
                                            continue
                                total_pages = max(page_numbers) if page_numbers else current_page
                                self.logger.info(f"Total pages detected: {total_pages}")

                            # Check if there's a next page
                            next_button = driver.find_elements(By.XPATH,
                                                               '//nav[@aria-label="pagination"]//a[contains(., "Next")]')
                            if not next_button or current_page >= total_pages:
                                self.logger.info("No more pages to crawl or reached last page")
                                break

                            # Navigate to the next page
                            current_page += 1
                            next_page_url = f"https://www.jobkorea.co.kr/Search?Page_No={current_page}"
                            self.logger.info(f"Navigating to page {current_page}: {next_page_url}")
                            driver.get(next_page_url)
                            WebDriverWait(driver, 20).until(
                                EC.presence_of_all_elements_located(
                                    (By.XPATH,
                                     '//div[contains(@class, "Flex_display_flex__i0l0hl2 Flex_direction_column__i0l0hl4 h7nnv10")]')
                                )
                            )

                        except Exception as e:
                            self.logger.error(f"Failed to navigate to next page: {str(e)}")
                            break

                        # Brief pause to avoid overwhelming the server
                        time.sleep(2)

                    # After all pages are crawled, wait for the refresh interval
                    interval = self.config.getint('web', 'refresh_interval')
                    self.logger.info(f"Finished crawling all pages, waiting {interval} seconds")
                    time.sleep(interval)

                except Exception as e:
                    self.logger.error(f"Crawler loop error: {str(e)}")
                    time.sleep(10)  # Brief pause before retry

        except Exception as e:
            self.logger.error(f"Crawler initialization error: {str(e)}")
        finally:
            self.auth.close()
            self.logger.info("Crawler stopped")

    def stop(self):
        """Stop the crawler."""
        self._stop.set()
        self.logger.info("Crawler stop requested")