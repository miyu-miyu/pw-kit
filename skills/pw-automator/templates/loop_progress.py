"""Loop progress: poll a condition until satisfied, with sub-operations.

Pattern that codegen CANNOT generate — it records only a single wait.
Use this for progress bars, virtual scrolling, or any polling scenario.
"""

from playwright.sync_api import sync_playwright


def loop_progress():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto("https://example.com/upload")
        page.get_by_role("button", name="上传文件").click()

        # Pattern 3a: Wait for progress completion (loop check)
        for i in range(60):
            progress = page.locator(".progress-bar")
            if progress.is_visible() and "100%" in progress.text_content():
                print(f"Upload complete after {i * 2}s")
                break
            page.wait_for_timeout(2000)

        # Pattern 3b: Virtual scrolling dropdown (scroll + check each round)
        page.get_by_role("button", name="选择版本").click()

        for i in range(50):
            target = page.locator("li[data-value='openharmony']")
            if target.is_visible():
                target.click()
                print(f"Found target after {i} scrolls")
                break
            # Scroll the dropdown list down
            page.evaluate(
                "document.querySelector('.dropdown-menu').scrollTop += 200"
            )
            page.wait_for_timeout(300)

        browser.close()


if __name__ == "__main__":
    loop_progress()