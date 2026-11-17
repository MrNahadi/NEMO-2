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
    page.wait_for_timeout(600)
    page.screenshot(path=str(IMG / f"app-{name}.png"), full_page=full)
    print("wrote", name, flush=True)


def home(page) -> None:
    page.goto(URL)
    page.wait_for_selector(".project-row")
    page.locator(".brand").click()


def open_project(page, name: str) -> None:
    home(page)
    page.locator(".project-row", has_text=name).click()
    page.wait_for_selector("h1")
    page.wait_for_timeout(2500)


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True, args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1.5)

        home(page)
        shot(page, "home")

        page.get_by_role("button", name="New design").click()
        page.locator(".choice-card", has_text="Pipe support").click()
        page.get_by_label("Design name").fill("Engine room seawater line")
        shot(page, "new-design")

        open_project(page, "Engine room lift")
        page.get_by_role("button", name="Change the answers").click()
        page.wait_for_selector(".viewer-chip", timeout=20000)
        page.wait_for_timeout(2500)
        shot(page, "padeye-describe")

        open_project(page, "Engine room seawater line")
        page.get_by_role("button", name="Change the answers").click()
        page.wait_for_selector(".viewer-chip", timeout=20000)
        page.get_by_role("button", name="Next: ship motion and vibration").click()
        page.wait_for_selector(".viewer-chip", timeout=20000)
        page.wait_for_timeout(2500)
        shot(page, "bracket-motion")

        open_project(page, "Engine room lift")
        shot(page, "padeye-results")
        page.locator(".check-row", has_text="Shearing out above the hole").click()
        page.wait_for_timeout(1500)
        page.locator(".check.open").scroll_into_view_if_needed()
        page.evaluate("window.scrollBy(0, -120)")
        page.wait_for_timeout(1500)
        shot(page, "padeye-check-working")

        open_project(page, "Patrol boat stabilizer")
        page.locator(".segmented button", has_text="Stress").click()
        page.wait_for_timeout(3500)
        shot(page, "fin-results-stress")

        open_project(page, "Engine room seawater line")
        page.locator("section h2", has_text="How NEMO got here").scroll_into_view_if_needed()
        page.locator(".stage", has_text="Pipe span and vibration").click()
        page.wait_for_timeout(1200)
        page.locator("section h2", has_text="How NEMO got here").scroll_into_view_if_needed()
        shot(page, "bracket-record")

        page.locator(".brand").click()
        page.get_by_role("button", name="Verification").click()
        page.wait_for_timeout(2000)
        shot(page, "verification")

        open_project(page, "Patrol boat stabilizer")
        page.get_by_role("button", name="Change the answers").click()
        page.wait_for_selector(".viewer-chip", timeout=20000)
        page.get_by_role("button", name="Next: check the assumptions").click()
        page.wait_for_timeout(1500)
        page.get_by_role("button", name="Find designs").click()
        t0 = time.time()
        while time.time() - t0 < 120:
            page.wait_for_timeout(1000)
            stage = page.locator(".stage-active .stage-title").all_inner_texts()
            if any("Stress solve" in s or "Mesh" in s for s in stage):
                break
        page.wait_for_timeout(1500)
        shot(page, "running")
        browser.close()


if __name__ == "__main__":
    main()
