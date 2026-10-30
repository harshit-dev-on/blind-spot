from pathlib import Path
from playwright.sync_api import sync_playwright

out = Path("blindspot_reports/website-context-live-demo")
out.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=["--start-maximized"])
    context = browser.new_context(no_viewport=True)
    page = context.new_page()
    page.goto("https://example.com", wait_until="domcontentloaded", timeout=30000)
    title = page.title()
    text = (page.locator("body").inner_text() or "")[:10000]
    links = page.locator("a[href]").evaluate_all("els => els.map(a => ({text: (a.innerText || a.textContent || '').trim(), href: a.href}))")
    page.screenshot(path=str(out / "screenshot.png"), full_page=True)
    lines = [f"# Website Context: {title}", "", f"- URL: {page.url}", f"- Title: {title}", "", "## Visible page text", "", text, "", "## Links"]
    lines.extend(f"- [{link['text']}]({link['href']})" for link in links)
    lines.extend(["", "## Screenshot", "See [screenshot.png](screenshot.png)"])
    (out / "website_context.md").write_text("\n".join(lines), encoding="utf-8")
    print("LIVE_BROWSER_READY")
    print(f"Saved context to: {(out / 'website_context.md').resolve()}", flush=True)
    input("Browser is open. Press Enter in this terminal to close it... ")
    context.close()
    browser.close()
