from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://www.jobkorea.co.kr")
    print("Playwright browser launched successfully!")
    browser.close()