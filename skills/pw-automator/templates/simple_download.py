"""Simple download: navigate → fill → click → expect_download.

Basic workflow that Playwright codegen can handle, with minimal
pw-automator upgrades (semantic locators instead of fragile selectors).
"""

from playwright.sync_api import sync_playwright, expect


def simple_download(query="OpenHarmony"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # 1. Navigate
        page.goto("https://example.com/search")

        # 2. Fill search (semantic locator, not fragile selector)
        page.get_by_placeholder("搜索项目").fill(query)

        # 3. Click search button
        page.get_by_role("button", name="搜索").click()

        # 4. Wait for results (expect assertion, not hard wait)
        expect(page.get_by_text("搜索结果")).to_be_visible(timeout=15000)

        # 5. Click first result
        page.locator(".result-item").first.click()

        # 6. Intercept download (Playwright built-in, better than href extraction)
        with page.expect_download() as download_info:
            page.get_by_text("下载").click()
        download = download_info.value
        download.save_as(f"./downloads/{download.suggested_filename}")
        print(f"Downloaded: {download.suggested_filename}")

        browser.close()


if __name__ == "__main__":
    simple_download()