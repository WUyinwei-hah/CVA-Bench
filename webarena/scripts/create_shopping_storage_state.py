from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_BASE_URL = "http://localhost:7770"
DEFAULT_OUTPUT = "webarena/auth/shopping_state.json"
DEFAULT_EMAIL = "emma.lopez@gmail.com"
DEFAULT_PASSWORD = "Password.123"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a Playwright storage state for WebArena shopping.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Shopping site base URL.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Path to write the storage-state JSON.")
    parser.add_argument("--email", default=DEFAULT_EMAIL, help="Shopping account email.")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Shopping account password.")
    parser.add_argument("--headed", action="store_true", help="Run Chromium with a visible window.")
    args = parser.parse_args()

    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError:
        raise SystemExit(
            "Playwright is not installed. Install repository requirements and run "
            "`playwright install chromium` first."
        )

    base_url = args.base_url.rstrip("/")
    login_url = f"{base_url}/customer/account/login/"
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not args.headed)
        context = browser.new_context(viewport={"width": 1440, "height": 1024})
        page = context.new_page()

        try:
            page.goto(login_url, wait_until="domcontentloaded")

            email_locator = page.get_by_label("Email", exact=True)
            if email_locator.count() == 0:
                email_locator = page.locator("#email, input[type='email']").first
            email_locator.fill(args.email)

            password_locator = page.get_by_label("Password", exact=True)
            if password_locator.count() == 0:
                password_locator = page.locator("#pass, input[type='password']").first
            password_locator.fill(args.password)

            page.get_by_role("button", name="Sign In").click()

            try:
                page.wait_for_url("**/customer/account/**", timeout=15000)
            except PlaywrightTimeoutError:
                page.wait_for_load_state("networkidle")

            if "/customer/account/login" in page.url:
                raise SystemExit(f"Login did not leave the login page: {page.url}")

            context.storage_state(path=str(output_path))
            print(
                json.dumps(
                    {
                        "storage_state": str(output_path),
                        "final_url": page.url,
                    },
                    indent=2,
                )
            )
            return 0
        finally:
            browser.close()


if __name__ == "__main__":
    raise SystemExit(main())
