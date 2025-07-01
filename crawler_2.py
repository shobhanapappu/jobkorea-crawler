from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException, WebDriverException, \
    NoSuchElementException
import time

import configparser
import logging
import threading
import time

from selenium.webdriver import ActionChains
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

    def _stoppable_sleep(self, seconds):
        """Sleep for the specified time, checking for stop signal."""
        start_time = time.time()
        while time.time() - start_time < seconds and not self._stop.is_set():
            time.sleep(0.1)  # Sleep in small increments to allow stop checks

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

    def scrape_job_details(driver):
        job_details = {}

        try:
            # Extract Experience Requirement
            try:
                experience = driver.find_element(By.CSS_SELECTOR, ".tbCol dl.tbList dd strong.col_1").text.strip()
                job_details["experience"] = experience
                print(experience)  # Print the extracted experience
            except NoSuchElementException:
                job_details["experience"] = "Not found"
                print("Experience requirement not found")

            # Extract Education Requirement
            try:
                education = driver.find_elements(By.CSS_SELECTOR, ".tbCol dl.tbList dd strong.col_1")[1].text.strip()
                job_details["education"] = education
                print(education)  # Print the extracted education
            except (NoSuchElementException, IndexError):
                job_details["education"] = "Not found"
                print("Education requirement not found")

            # Extract Employment Type
            try:
                employment_type = driver.find_element(By.CSS_SELECTOR,
                                                      ".tbCol dl.tbList ul.addList li strong.col_1").text.strip()
                job_details["employment_type"] = employment_type
                print(employment_type)  # Print the extracted employment type
            except NoSuchElementException:
                job_details["employment_type"] = "Not found"
                print("Employment type not found")

            # Extract Additional Employment Info
            try:
                employment_info = driver.find_element(By.CSS_SELECTOR, ".tbCol dl.tbList ul.addList li").text.strip()
                job_details["employment_info"] = employment_info
                print(employment_info)  # Print the extracted employment info
            except NoSuchElementException:
                job_details["employment_info"] = "Not found"
                print("Additional employment info not found")

            # Extract Salary
            try:
                salary = driver.find_element(By.CSS_SELECTOR, ".tbCol dl.tbList dd em.dotum").text.strip() + " " + \
                         driver.find_element(By.CSS_SELECTOR,
                                             ".tbCol dl.tbList dd .tahoma").text.strip() + " million won or more"
                job_details["salary"] = salary
                print(salary)  # Print the extracted salary
            except NoSuchElementException:
                job_details["salary"] = "Not found"
                print("Salary not found")

            # Extract Region
            try:
                region = driver.find_element(By.CSS_SELECTOR, ".tbCol dl.tbList dd a").text.strip()
                job_details["region"] = region
                print(region)  # Print the extracted region
            except NoSuchElementException:
                job_details["region"] = "Not found"
                print("Region not found")

            # Extract Working Hours
            try:
                working_hours = driver.find_element(By.CSS_SELECTOR, ".tbCol dl.tbList dd .tahoma").text.strip() + " " + \
                                driver.find_elements(By.CSS_SELECTOR, ".tbCol dl.tbList dd")[3].text.strip()
                job_details["working_hours"] = working_hours
                print(working_hours)  # Print the extracted working hours
            except (NoSuchElementException, IndexError):
                job_details["working_hours"] = "Not found"
                print("Working hours not found")

            # Extract Industry
            try:
                industry = driver.find_element(By.CSS_SELECTOR, ".tbCol.tbCoInfo dl.tbList dd text").text.strip()
                job_details["industry"] = industry
                print(industry)  # Print the extracted industry
            except NoSuchElementException:
                job_details["industry"] = "Not found"
                print("Industry not found")

            # Extract Year of Establishment
            try:
                year_established = driver.find_element(By.CSS_SELECTOR,
                                                       ".tbCol.tbCoInfo dl.tbList dd text span.tahoma").text.strip()
                job_details["year_established"] = year_established
                print(year_established)  # Print the extracted year of establishment
            except NoSuchElementException:
                job_details["year_established"] = "Not found"
                print("Year of establishment not found")

            # Extract Corporate Form
            try:
                corporate_form = driver.find_elements(By.CSS_SELECTOR, ".tbCol.tbCoInfo dl.tbList dd")[2].text.strip()
                job_details["corporate_form"] = corporate_form
                print(corporate_form)  # Print the extracted corporate form
            except (NoSuchElementException, IndexError):
                job_details["corporate_form"] = "Not found"
                print("Corporate form not found")

            return job_details

        except Exception as e:
            print(f"An error occurred during scraping: {e}")
            return job_details

    import time
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException, WebDriverException

    def _scan_posts(self, driver):
        """Scan job listings, navigate to details URL, check for contact info, and return to continue processing."""
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
                if self._stop.is_set():
                    self.logger.info("Stop signal received during post scanning")
                    return posts_data

                self._stoppable_sleep(0.5)
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

                    manager_info = "Not found"
                    try:
                        contact_section = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located(
                                (By.XPATH,
                                 '//dd[contains(@class, "devTplLyClick") and .//button[contains(@class, "devOpenCharge")]]')
                            )
                        )
                        self.logger.info(f"Post {post_id} - Contact information section found")

                        # Scroll to the contact section
                        try:
                            ActionChains(driver).move_to_element(contact_section).perform()
                            self.logger.info(f"Post {post_id} - Scrolled to contact section")
                        except:
                            self.logger.error(f"Post {post_id} - Failed to scroll to contact section")

                        # Click the "Check your contact information" button
                        try:
                            contact_button = WebDriverWait(contact_section, 10).until(
                                EC.element_to_be_clickable((By.XPATH, './/button[contains(@class, "devOpenCharge")]'))
                            )
                            ActionChains(driver).move_to_element(contact_button).click().perform()
                            self.logger.info(
                                f"Post {post_id} - Clicked 'Check your contact information' button via ActionChains")
                            # Wait for contact info to become visible
                            WebDriverWait(driver, 10).until(
                                EC.invisibility_of_element((By.XPATH, './/button[contains(@class, "devOpenCharge")]')))
                            self.logger.info(f"Post {post_id} - Contact button hidden, assuming contact info loaded")
                        except (ElementClickInterceptedException, TimeoutException, WebDriverException) as e:
                            self.logger.error(f"Post {post_id} - ActionChains click failed: {str(e)}")
                            # Fallback to JavaScript click
                            try:
                                driver.execute_script("arguments[0].click();", contact_button)
                                self.logger.info(
                                    f"Post {post_id} - Clicked 'Check your contact information' button via JavaScript")
                                WebDriverWait(driver, 10).until(
                                    EC.invisibility_of_element(
                                        (By.XPATH, './/button[contains(@class, "devOpenCharge")]')))
                                self.logger.info(
                                    f"Post {post_id} - Contact button hidden, assuming contact info loaded")
                            except:
                                self.logger.error(
                                    f"Post {post_id} - JavaScript click failed, proceeding with available data")

                        # Extract contact information after clicking
                        try:
                            phone = "Not found"
                            email = "Not found"
                            # Try to get phone number
                            try:
                                phone_element = WebDriverWait(contact_section, 5).until(
                                    EC.presence_of_element_located(
                                        (By.XPATH,
                                         './/span[contains(@class, "tahoma") and not(contains(@class, "tplHide"))]'))
                                )
                                phone = phone_element.text.strip()
                                self.logger.info(f"Post {post_id} - Extracted phone: {phone}")
                            except:
                                self.logger.warning(f"Post {post_id} - Phone number not found")

                            # Try to get email
                            try:
                                email_element = WebDriverWait(driver, 5).until(
                                    EC.presence_of_element_located(
                                        (By.XPATH,
                                         '//dd[not(contains(@class, "tplHide"))]//a[contains(@href, "mailto:")]'))
                                )
                                email = email_element.text.strip()
                                self.logger.info(f"Post {post_id} - Extracted email: {email}")
                            except:
                                self.logger.warning(f"Post {post_id} - Email not found")

                            # Check if either phone or email was found and print HELLLLOOOOOOO
                            if phone != "Not found" or email != "Not found":
                                print("HELLLLOOOOOOO")
                                # Call scrape_job_details to extract job details
                                try:
                                    job_details = scrape_job_details(driver)
                                    self.logger.info(f"Post {post_id} - Scraped job details: {job_details}")
                                except Exception as e:
                                    self.logger.error(f"Post {post_id} - Failed to scrape job details: {e}")
                                    job_details = {}

                            # Combine contact info
                            if phone != "Not found" or email != "Not found":
                                manager_info = f"Phone: {phone}, Email: {email}"

                            else:
                                manager_info = "Not found"
                                # Log DOM for debugging
                                try:
                                    dom_snippet = driver.find_element(By.XPATH,
                                                                      '//div[contains(@class, "manager")]').get_attribute(
                                        'outerHTML')
                                    self.logger.debug(f"Post {post_id} - DOM snippet of manager section: {dom_snippet}")
                                except:
                                    self.logger.debug(f"Post {post_id} - Failed to capture DOM snippet")
                            self.logger.info(f"Post {post_id} - Extracted contact info (post-click): {manager_info}")

                            # Wait for 10 seconds as per instructions
                            self._stoppable_sleep(10)
                            self.logger.info(f"Post {post_id} - Waited for 10 seconds")

                        except:
                            self.logger.error(f"Post {post_id} - Failed to extract contact info after clicking")
                            try:
                                dom_snippet = driver.find_element(By.XPATH,
                                                                  '//div[contains(@class, "manager")]').get_attribute(
                                    'outerHTML')
                                self.logger.debug(f"Post {post_id} - DOM snippet of manager section: {dom_snippet}")
                            except:
                                self.logger.debug(f"Post {post_id} - Failed to capture DOM snippet")
                            manager_info = "Not found"

                    except:
                        self.logger.info(
                            f"Post {post_id} - No contact information section found, returning to original URL")
                        try:
                            driver.get(original_url)
                            WebDriverWait(driver, 20).until(
                                EC.presence_of_all_elements_located(
                                    (By.XPATH,
                                     '//div[contains(@class, "Flex_display_flex__i0l0hl2 Flex_direction_column__i0l0hl4 h7nnv10")]')
                                )
                            )
                            self.logger.info(f"Post {post_id} - Returned to listings page after no contact section")
                        except:
                            self.logger.error(
                                f"Post {post_id} - Failed to return to listings page after no contact section")
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
                            'manager_info': manager_info,  # Updated with extracted contact info or "Not found"
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
                        if self._stop.is_set():
                            self.logger.info("Stop signal received, exiting scan loop")
                            break

                        self._stoppable_sleep(1)
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
                        self._stoppable_sleep(2)

                    if self._stop.is_set():
                        self.logger.info("Stop signal received, exiting page loop")
                        break

                    # After all pages are crawled, wait for the refresh interval
                    interval = self.config.getint('web', 'refresh_interval', fallback=300)
                    self.logger.info(f"Finished crawling all pages, waiting {interval} seconds")
                    self._stoppable_sleep(interval)

                except Exception as e:
                    self.logger.error(f"Crawler loop error: {str(e)}")
                    self._stoppable_sleep(10)  # Brief pause before retry

        except Exception as e:
            self.logger.error(f"Crawler initialization error: {str(e)}")
        finally:
            self.auth.close()
            self.logger.info("Crawler stopped")

    def stop(self):
        """Stop the crawler and close the WebDriver."""
        self._stop.set()
        self.auth.close()  # Ensure WebDriver is closed immediately
        self.logger.info("Crawler stop requested and WebDriver closed")
