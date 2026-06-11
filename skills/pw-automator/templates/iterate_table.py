"""Iterate table: traverse rows/cells with .all() + for loop.

Pattern that codegen CANNOT generate — it only records clicking one
specific cell. Use this when you need to process ALL matching elements.
"""

from playwright.sync_api import sync_playwright


def iterate_table():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto("https://example.com/data-table")

        # Pattern 1a: Iterate all rows
        rows = page.locator("table tbody tr")
        for i in range(rows.count()):
            row = rows.nth(i)

            # Pattern 1b: Within each row, click visible cells only
            # ng-hide negation strategy — skip hidden cells
            cells = row.locator("td:not(.ng-hide)")
            for j in range(cells.count()):
                cell = cells.nth(j)
                cell.click()
                page.wait_for_timeout(300)  # brief pause between clicks

                # Pattern 1c: Extract info from each clicked cell
                try:
                    detail = page.locator(".detail-panel")
                    if detail.is_visible(timeout=2000):
                        print(f"Row {i}, Cell {j}: {detail.text_content()}")
                except Exception:
                    pass  # detail panel may not appear for all cells

                # Close any popup that might appear
                try:
                    page.locator(".close-btn").click(timeout=1000)
                except Exception:
                    pass

        browser.close()


if __name__ == "__main__":
    iterate_table()