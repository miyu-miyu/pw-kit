"""Branch download: conditional paths based on page state.

Pattern that codegen CANNOT generate — it records only one linear path.
Use this when different outcomes may occur after a click.
"""

from playwright.sync_api import sync_playwright
from pw_kit import extract_download_urls


def branch_download(query="OpenHarmony"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto("https://example.com/search")
        page.get_by_placeholder("搜索项目").fill(query)
        page.get_by_role("button", name="搜索").click()

        page.get_by_text("搜索结果").wait_for(timeout=15000)

        for result in page.locator(".result-item").all():
            result.click()

            # Branch: different download paths
            if page.locator(".download-modal").is_visible():
                # Path A: modal popup → extract URLs from modal
                urls = extract_download_urls(page, scope=".download-modal")
                print(f"Modal URLs: {urls}")

                # Close modal (may not exist, tolerate)
                try:
                    page.locator(".modal .close-btn").click()
                except Exception:
                    pass

            elif page.locator(".direct-download-btn").is_visible():
                # Path B: direct download → intercept download event
                with page.expect_download() as d:
                    page.locator(".direct-download-btn").click()
                download = d.value
                download.save_as(f"./downloads/{download.suggested_filename}")
                print(f"Direct download: {download.suggested_filename}")

            else:
                # Path C: no visible download → semantic search fallback
                urls = extract_download_urls(page, strategy="semantic")
                print(f"Semantic fallback URLs: {urls}")

            page.go_back()

        browser.close()


if __name__ == "__main__":
    branch_download()