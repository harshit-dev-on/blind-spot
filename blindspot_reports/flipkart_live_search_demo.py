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
        page.wait_for_load_state("networkidle", timeout=12000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    page.screenshot(path=str(out / "01_landing.png"), full_page=True)
    print("STEP 1: Opened Flipkart visibly.", page.title(), flush=True)
    search = page.get_by_placeholder("Search for Products, Brands and More").first
    if search.count() == 0:
        print("Search field not found; stopping without interaction.", flush=True)
    else:
        search.fill("iPhone")
        search.press("Enter")
        try:
            page.wait_for_load_state("domcontentloaded", timeout=20000)
        except Exception:
            pass
        page.wait_for_timeout(4500)
        page.screenshot(path=str(out / "02_search_results.png"), full_page=True)
        body = (page.locator("body").inner_text() or "")[:25000]
        title = page.title()
        url = page.url
        links = page.locator("a[href]").evaluate_all("els => els.filter(a => {const r=a.getBoundingClientRect();return r.width&&r.height}).slice(0,100).map(a=>({text:(a.innerText||a.textContent||'').trim().replace(/\\s+/g,' ').slice(0,180),href:a.href}))")
        controls = page.locator("button,input,[role=button]").evaluate_all("els => els.filter(e=>{const r=e.getBoundingClientRect();return r.width&&r.height}).slice(0,80).map(e=>({tag:e.tagName.toLowerCase(),text:(e.innerText||e.value||e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,120),aria:e.getAttribute('aria-label')||'',placeholder:e.getAttribute('placeholder')||''}))")
        lines = ["# Flipkart: live product search context", "", f"- URL: {url}", f"- Title: {title}", "- Action: Searched for `iPhone` using the visible search field; no account data entered.", "", "## Visible page text", "", body, "", "## Visible controls", "", "| Element | Text | Accessible name | Placeholder |", "|---|---|---|---|"]
        for c in controls:
            clean=lambda s:str(s or '').replace('|','\\|').replace('\n',' ')[:180]
            lines.append(f"| {clean(c['tag'])} | {clean(c['text'])} | {clean(c['aria'])} | {clean(c['placeholder'])} |")
        lines += ["", "## Visible links", ""]
        lines.extend(f"- [{(a['text'] or 'link').replace(']', '')}]({a['href']})" for a in links[:50])
        lines += ["", "## Screenshot", "See [01_landing.png](01_landing.png) and [02_search_results.png](02_search_results.png)."]
        (out / "website_context.md").write_text("\n".join(lines), encoding="utf-8")
        print("STEP 2: Searched iPhone; current URL:", url, flush=True)
        print("PAGE TITLE:", title, flush=True)
        print("OTP/login prompt visible:", any(t in body.lower() for t in ["enter your phone number", "enter otp", "verify otp"]), flush=True)
        print("Context saved:", (out / "website_context.md").resolve(), flush=True)
    input("Live Flipkart browser is open. Press Enter in this terminal to close... ")
    context.close()
    browser.close()
