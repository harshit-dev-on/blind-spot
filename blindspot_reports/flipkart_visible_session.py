import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=["--start-maximized"])
    context = browser.new_context(no_viewport=True)
    page = context.new_page()
    page.goto("https://www.flipkart.com/search?q=iPhone", wait_until="domcontentloaded", timeout=45000)
    try:
        page.wait_for_load_state("networkidle", timeout=12000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    print("Flipkart iPhone search results are open in visible Chromium.", flush=True)
    print("Current URL:", page.url, flush=True)
    print("Visible browser will stay open for 10 minutes.", flush=True)
    time.sleep(600)
    context.close()
    browser.close()
