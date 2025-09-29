from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time

# Parole chiave tipiche da ignorare (menu, footer, cookie, ecc.)
IGNORE_KEYWORDS = [
    "cookie", "privacy", "powered by", "accept all", "decline all", 
    "view website", "help", "all jobs", "accessibility", "svg"
]

def fetch_job_description(url: str, timeout: int = 60000) -> dict:
    """
    Fetch job posting from any URL using Playwright.
    Handles iframes, JS-rendered content, removes duplicates and irrelevant text.
    Returns a dict with title, description, and url.
    """
    result = {
        "title": "No title found",
        "description": "No description found",
        "url": url
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=timeout)

        # fallback: aspetta che il body esista
        page.locator("body").wait_for(timeout=timeout)
        time.sleep(2)  # attesa JS extra per pagine lente

        # Tentativo di leggere iframe se presente
        frames = page.frames
        content_frame = page.main_frame
        max_text_len = 0

        for f in frames:
            try:
                text = f.locator("body").inner_text()
                if len(text) > max_text_len:
                    max_text_len = len(text)
                    content_frame = f
            except:
                continue

        html = content_frame.locator("body").inner_html()
        soup = BeautifulSoup(html, "html.parser")

        # Titolo: h1, h2, h3
        title_tag = soup.find(["h1", "h2", "h3"])
        if title_tag:
            result["title"] = title_tag.get_text(strip=True)

        # Estrazione testo completo
        texts = soup.find_all(["p", "li", "div", "span", "section", "article"])
        lines = []
        seen = set()
        for t in texts:
            text = t.get_text(strip=True)
            if len(text) < 20:
                continue
            if any(k.lower() in text.lower() for k in IGNORE_KEYWORDS):
                continue
            if text in seen:
                continue
            seen.add(text)
            lines.append(text)

        if lines:
            result["description"] = "\n".join(lines)

        browser.close()

    return result