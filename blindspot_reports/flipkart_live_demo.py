from pathlib import Path
from playwright.sync_api import sync_playwright

out = Path("blindspot_reports/flipkart-live-context")
out.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=["--start-maximized"])
    context = browser.new_context(no_viewport=True)
    page = context.new_page()
    page.goto("https://www.flipkart.com", wait_until="domcontentloaded", timeout=45000)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    page.wait_for_timeout(2500)
    print("LIVE_BROWSER_OPEN", flush=True)
    print("URL:", page.url, "TITLE:", page.title(), flush=True)
    print("Visible login dialog:", page.get_by_text("Enter your phone number to continue", exact=False).count() > 0, flush=True)
    print("Visible search field:", page.get_by_placeholder("Search for Products, Brands and More").count() > 0, flush=True)
    print("Visible phone field:", page.locator("input").count(), flush=True)
    page.screenshot(path=str(out / "flipkart_initial.png"), full_page=True)
    body = (page.locator("body").inner_text() or "")[:18000]
    elements = page.locator("a[href], button, input, select, textarea, [role=button], [role=link]").evaluate_all("els => els.filter(e => {const r=e.getBoundingClientRect(); return r.width && r.height}).slice(0,150).map(e => ({tag:e.tagName.toLowerCase(), text:(e.innerText||e.value||e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,120), aria:e.getAttribute('aria-label')||'', placeholder:e.getAttribute('placeholder')||'', href:e.href||''}))")
    report = ["# Flipkart live page context", "", f"- URL: {page.url}", f"- Title: {page.title()}", "- Capture: headed Chromium; user-visible session", "", "## Visible page text", "", body, "", "## Visible controls", "", "| Element | Text | Accessible name | Placeholder | Link |", "|---|---|---|---|---|"]
    for e in elements:
        clean = lambda s: str(s or '').replace('|','\\|').replace('\n',' ')[:200]
        report.append(f"| {clean(e['tag'])} | {clean(e['text'])} | {clean(e['aria'])} | {clean(e['placeholder'])} | {clean(e['href'])} |")
    report += ["", "## Screenshot", "See [flipkart_initial.png](flipkart_initial.png)"]
    (out / "website_context.md").write_text("\n".join(report), encoding="utf-8")
    print("CONTEXT_SAVED", (out / "website_context.md").resolve(), flush=True)
    input("Flipkart is open in Chromium. Press Enter in this terminal when you want to close the live browser... ")
    context.close()
    browser.close()
