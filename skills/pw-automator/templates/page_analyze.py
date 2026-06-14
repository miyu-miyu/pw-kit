"""Page analysis: discover real elements and download links at each stage.

This is Step 3 of the pw-automator workflow. codegen scripts often involve
multiple page navigations and DOM changes (clicks, fills, AJAX updates).
This template scans the page at each stage so optimizations are grounded
in reality rather than guesswork.

Usage:
    1. Copy the scan() function into your analysis script
    2. For each page.goto() in your codegen script, add a scan stage
    3. For each click/fill that changes the page, add a scan sub-stage
    4. For each wait operation, add a scan sub-stage (DOM may change after wait)
    5. Run: python3 page_analyze.py
    6. Share ALL stage outputs with pw-automator

Three types of page changes:
    - URL change (page.goto, link click) → new scan stage (A/B/C)
    - DOM change (click/fill triggers AJAX) → scan sub-stage (A+1/A+2)
    - Wait completion (wait_for_timeout/load_state/url) → scan sub-stage (A+3/A+4)

⚠️ wait operations are important triggers! DOM may only change after a wait
   completes. Always scan after wait_for_timeout, wait_for_load_state, etc.
"""

from playwright.sync_api import sync_playwright
from pw_kit import discover_elements, extract_download_urls


def scan(page, stage_name):
    """Scan current page state and print results."""
    print(f"\n{'='*60}")
    print(f"阶段: {stage_name}")
    print(f"URL: {page.url}")
    print(f"标题: {page.title()}")
    print(f"{'='*60}")

    elements = discover_elements(page, tags=["button", "a", "input", "select"])
    print(f"可交互元素 ({len(elements)}个):")
    for el in elements[:15]:  # 只显示前15个，避免过多
        suggested = el.get("suggested") or "无唯一选择器"
        text = el.get("text", "")[:30]
        print(f"  [{el['tag']}] text={text}, suggested={suggested}")

    urls = extract_download_urls(page, strategy="auto")
    print(f"下载链接: {len(urls)}个")
    for u in urls[:5]:
        print(f"  {u}")


def page_analyze():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        # ── 阶段A: 第一个页面（从 codegen 脚本的第一个 page.goto） ──
        page.goto("https://example.com/login")
        page.wait_for_load_state("networkidle")
        scan(page, "A: 登录页")

        # ── 阶段A+1: 点击登录后（DOM变化） ──
        # ← 复制 codegen 脚本中的登录操作
        # page.get_by_placeholder("用户名").fill("test")
        # page.get_by_role("button", name="登录").click()
        # page.wait_for_load_state("networkidle")
        # scan(page, "A+1: 登录后")

        # ── 阶段A+2: wait_for_timeout 后（DOM可能在等待期间变化） ──
        # ← codegen 脚本中如果有 wait_for_timeout，等待结束后也扫描
        # page.wait_for_timeout(3000)
        # scan(page, "A+2: 等待3秒后（DOM可能已变化）")

        # ── 阶段B: 第二个页面（URL变化） ──
        # page.goto("https://example.com/search")
        # page.wait_for_load_state("networkidle")
        # scan(page, "B: 搜索页")

        # ── 阶段B+1: 搜索后（DOM变化） ──
        # page.get_by_placeholder("搜索").fill("关键字")
        # page.get_by_role("button", name="搜索").click()
        # page.wait_for_load_state("networkidle")
        # scan(page, "B+1: 搜索结果")

        # ── 阶段B+2: wait_for_timeout 后（搜索结果可能需要等待加载） ──
        # ← 重要: wait_for_timeout 后 DOM 可能已变化，应该扫描
        # page.wait_for_timeout(2000)
        # scan(page, "B+2: 等待后（搜索结果可能已加载完成）")

        # ── 阶段B+3: 点击筛选后（局部DOM变化） ──
        # page.get_by_role("button", name="筛选").click()
        # page.wait_for_timeout(500)  # 等下拉菜单展开
        # scan(page, "B+3: 筛选展开后")

        # ── 阶段C: 详情页（URL变化） ──
        # page.locator(".result-item").first.click()
        # page.wait_for_load_state("networkidle")
        # scan(page, "C: 详情页")

        # ── 阶段C+1: wait_for_load_state 后（页面完全加载） ──
        # ← wait_for_load_state 完成后也扫描，对比加载前后的变化
        # page.wait_for_load_state("networkidle")
        # scan(page, "C+1: 页面完全加载后")

        # ── 阶段C+2: 下载操作后 ──
        # page.get_by_role("button", name="下载").click()
        # page.wait_for_timeout(3000)  # ← wait 后扫描
        # scan(page, "C+2: 下载后（等待3秒后DOM可能变化）")

        browser.close()


if __name__ == "__main__":
    page_analyze()
