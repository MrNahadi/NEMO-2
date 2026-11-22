"""Screenshots of the NEMO app for the project report.

Needs a running NEMO server (default http://127.0.0.1:8768) loaded with the three case studies, and
Playwright (uses the installed Microsoft Edge):  python screenshots.py [url]
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8768/"
IMG = Path(__file__).resolve().parent.parent / "images"


def shot(page, name: str, full: bool = False) -> None:
    page.wait_for_timeout(800)
    page.screenshot(path=str(IMG / f"app-{name}.png"), full_page=full)
    print("wrote", name, flush=True)


def home(page) -> None:
    page.goto(URL)
    page.wait_for_selector("tr.row-link", timeout=20000)


def open_project(page, name: str) -> None:
    home(page)
    page.locator("button.design-name", has_text=name).click()
    page.wait_for_selector("h1", timeout=20000)
    page.wait_for_timeout(2500)


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="msedge",
            headless=True,
            args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
        )
        page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1.5)

        # 1. Home screen
        home(page)
        shot(page, "home")

        # 2. New design dialog
        page.get_by_role("button", name="New design").first.click()
        dialog = page.get_by_role("dialog")
        dialog.wait_for(timeout=10000)
        dialog.get_by_text("Pipe support bracket", exact=True).click()
        dialog.get_by_label("Design name").fill("Engine room seawater line")
        shot(page, "new-design")

        # 3. Padeye describe screen
        open_project(page, "Engine room lift")
        page.locator("#tab-describe").click()
        page.wait_for_selector(".viewer-chip", timeout=20000)
        page.wait_for_timeout(2500)
        shot(page, "padeye-describe")

        # 4. Bracket ship motion & vibration assumptions screen
        open_project(page, "Engine room seawater line")
        page.locator("#tab-assumptions").click()
        page.wait_for_selector(".viewer-chip", timeout=20000)
        page.wait_for_timeout(2500)
        shot(page, "bracket-motion")

        # 5 & 6. Padeye results + expanded check working
        open_project(page, "Engine room lift")
        shot(page, "padeye-results")
        page.locator(".check-row", has_text="Shearing out above the hole").click()
        page.wait_for_timeout(1500)
        page.locator(".check.open, .check-row[aria-expanded='true']").first.scroll_into_view_if_needed()
        page.evaluate("window.scrollBy(0, -120)")
        page.wait_for_timeout(1200)
        shot(page, "padeye-check-working")

        # 7. Fin results stress view
        open_project(page, "Patrol boat stabilizer")
        page.locator(".segmented button", has_text="Stress").click()
        page.wait_for_timeout(3500)
        shot(page, "fin-results-stress")

        # 8. Bracket engineering run log ("How NEMO got here" tab)
        open_project(page, "Engine room seawater line")
        page.locator("#tab-runlog").click()
        page.wait_for_selector(".stage-row", timeout=20000)
        page.locator(".stage-row", has_text="Pipe span").first.click()
        page.wait_for_timeout(1500)
        shot(page, "bracket-record")

        # 9. Verification screen (run verification so passed benchmark results are shown)
        page.locator(".brand").click()
        page.get_by_role("button", name="Verification").click()
        page.wait_for_selector("h1", timeout=15000)
        run_btn = page.get_by_role("button", name="Run verification")
        if run_btn.is_visible():
            run_btn.click()
            t0 = time.time()
            while time.time() - t0 < 150:
                page.wait_for_timeout(1500)
                if page.get_by_role("button", name="Run verification").is_visible() and page.get_by_role("button", name="Run verification").is_enabled():
                    break
        page.wait_for_timeout(1500)
        shot(page, "verification")

        # 10. Live running screen
        open_project(page, "Patrol boat stabilizer")
        page.locator("#tab-assumptions").click()
        page.wait_for_timeout(1500)
        page.get_by_role("button", name="Find designs").click()
        page.wait_for_selector(".stage-row", timeout=20000)
        t0 = time.time()
        while time.time() - t0 < 120:
            page.wait_for_timeout(1000)
            active = page.locator(".stage-row:has(.stage-icon.active) .stage-title").all_inner_texts()
            if any("Stress solve" in s or "Mesh" in s for s in active):
                break
        page.wait_for_timeout(1500)
        shot(page, "running")
        browser.close()


if __name__ == "__main__":
    main()
