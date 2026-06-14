# pw-automator 模式库

codegen 无法生成的 **5 种模式**（从脚本分析中发现）。每个模式包含适用场景、触发识别、完整代码模板和页面验证要求。

另外有 **1 个附加功能**（定时执行），不从脚本分析中发现，只在用户明确提出诉求时使用。

---

## 1. Iterate — 表格/列表遍历

### 适用场景
- codegen 脚本出现重复的 fill/click 操作，每行做的事一样
- 需要处理表格所有行、列表所有项、搜索结果所有条目

### 触发识别
```
# codegen 生成的重复代码（特征: 相似操作只换了索引）
page.locator("tr:nth-child(1) > td:nth-child(2)").click()
page.locator("tr:nth-child(2) > td:nth-child(2)").click()
page.locator("tr:nth-child(3) > td:nth-child(2)").click()
```

### 代码模板
```python
from playwright.sync_api import sync_playwright

def iterate_table():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://example.com/data-table")

        # 遍历所有行
        rows = page.locator("table tbody tr")
        for i in range(rows.count()):
            row = rows.nth(i)

            # 遍历每行中可见的单元格（跳过 ng-hide）
            cells = row.locator("td:not(.ng-hide)")
            for j in range(cells.count()):
                cell = cells.nth(j)
                cell.click()
                page.wait_for_timeout(300)

                # 提取点击后的详情（容错: 可能不是所有单元格都有详情）
                try:
                    detail = page.locator(".detail-panel")
                    if detail.is_visible(timeout=2000):
                        print(f"Row {i}, Cell {j}: {detail.text_content()}")
                except Exception:
                    pass

                # 关闭可能出现的弹窗
                try:
                    page.locator(".close-btn").click(timeout=1000)
                except Exception:
                    pass

        browser.close()
```

### 页面验证
- **必须确认**: 页面上实际有多少行/项 — 用 `discover_elements()` 确认数量
- **必须确认**: 每行操作的触发条件是否一致 — 有 ng-hide 的行需要 `.not(.ng-hide)` 过滤
- **必须确认**: 循环中是否有不同分支 — 有时前几行和后面几行行为不同

完整模板: `templates/iterate_table.py`

---

## 2. Branch — 条件分支

### 适用场景
- 同一个操作可能产生不同结果（弹窗 vs 直接下载 vs 404页面）
- 需要根据页面当前状态走不同的处理路径

### 触发识别
```
# codegen 只录制了一条路径，但实际可能出现:
#   - 路径A: 弹出下载弹窗
#   - 路径B: 直接开始下载
#   - 路径C: 无下载链接（需要语义提取）
```

### 代码模板
```python
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

            # 分支处理: 不同下载路径
            if page.locator(".download-modal").is_visible():
                # 路径A: 弹窗 → 从弹窗提取URL
                urls = extract_download_urls(page, scope=".download-modal")
                print(f"弹窗URL: {urls}")
                try:
                    page.locator(".modal .close-btn").click()
                except Exception:
                    pass

            elif page.locator(".direct-download-btn").is_visible():
                # 路径B: 直接下载 → 拦截下载事件
                with page.expect_download() as d:
                    page.locator(".direct-download-btn").click()
                download = d.value
                download.save_as(f"./downloads/{download.suggested_filename}")

            else:
                # 路径C: 无可见下载 → 语义提取
                urls = extract_download_urls(page, strategy="semantic")
                print(f"语义提取URL: {urls}")

            page.go_back()

        browser.close()
```

### 页面验证
- **必须确认**: 各分支条件确实在页面上存在 — 用 `discover_elements()` 检查 `.download-modal`、`.direct-download-btn` 等
- **必须确认**: 每个分支有对应的处理方式 — 弹窗关闭按钮存在吗? 直接下载按钮的文本是什么?

完整模板: `templates/branch_download.py`

---

## 3. Loop — 轮询等待

### 适用场景
- 进度条、加载动画、虚拟滚动 — 需要反复检查直到条件满足
- codegen 只录了一个 `wait_for_timeout`，但实际等待时间不确定

### 触发识别
```
# codegen 用固定等待 — 实际等待时间可能变化
page.wait_for_timeout(5000)  # ← 进度条可能3秒到100%，也可能10秒

# 虚拟滚动列表 — codegen 只录了点击可见的那一项
page.locator("li[data-value='openharmony']").click()  # ← 可能需要先滚动才可见
```

### 代码模板
```python
from playwright.sync_api import sync_playwright

def loop_progress():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://example.com/upload")
        page.get_by_role("button", name="上传文件").click()

        # 轮询等待: 进度条到100%
        for i in range(60):
            progress = page.locator(".progress-bar")
            if progress.is_visible() and "100%" in progress.text_content():
                print(f"上传完成，耗时 {i * 2}s")
                break
            page.wait_for_timeout(2000)

        # 轮询等待: 虚拟滚动找到目标项
        page.get_by_role("button", name="选择版本").click()
        for i in range(50):
            target = page.locator("li[data-value='openharmony']")
            if target.is_visible():
                target.click()
                print(f"找到目标，滚动 {i} 次")
                break
            page.evaluate("document.querySelector('.dropdown-menu').scrollTop += 200")
            page.wait_for_timeout(300)

        browser.close()
```

### 页面验证
- **必须确认**: 等待目标确实会变化 — 进度条文本会更新吗? 虚拟滚动会加载更多项吗?
- **必须确认**: 循环终止条件可靠 — "100%" 是实际出现的文本吗? 不是猜测

⚠️ **不知道等待什么时，不能猜测条件。问用户或列出页面实际变化选项。**

完整模板: `templates/loop_progress.py`

---

## 4. 语义提取 — 下载链接提取

### 适用场景
- 页面上有多个下载链接，需要批量提取
- 链接不在明显的按钮上，可能是文字链接、图标链接、隐藏链接

### 触发识别
```
# codegen 只录了点一个下载按钮，但页面上可能有多个下载链接
page.get_by_text("下载PDF").click()  # ← 只处理了一个，遗漏了其他格式

# 或链接隐藏在深层DOM中
page.locator("div.hidden-links > a:nth-child(1)").click()  # ← 选择器脆弱
```

### 代码模板
```python
from playwright.sync_api import sync_playwright, expect
from pw_kit import extract_download_urls

def simple_download(query="OpenHarmony"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://example.com/search")

        page.get_by_placeholder("搜索项目").fill(query)
        page.get_by_role("button", name="搜索").click()
        expect(page.get_by_text("搜索结果")).to_be_visible(timeout=15000)

        # 方法1: intercept download (适合直接点击下载)
        with page.expect_download() as download_info:
            page.get_by_text("下载").click()
        download = download_info.value
        download.save_as(f"./downloads/{download.suggested_filename}")

        # 方法2: pw_kit 语义提取 (适合批量提取所有下载链接)
        urls = extract_download_urls(page, strategy="auto", keywords=["PDF"])
        for url in urls:
            print(f"下载链接: {url}")

        browser.close()
```

### 页面验证
- **必须确认**: 页面有下载链接 — 用 `extract_download_urls()` 先扫描，确认非空再优化
- **必须确认**: 链接的关键词/文件扩展名 — keywords 参数应基于页面实际出现的文本

完整模板: `templates/simple_download.py`

---

## 5. 动态元素 — ng-hide/hover/遮挡

### 适用场景
- 元素受 `ng-hide`、`ng-show` 控制 — 有时可见有时不可见
- 元素需要 hover 才出现（下拉菜单、tooltip）
- 元素被其他元素遮挡，Playwright `click()` 报错

### 触发识别
```
# ng-hide 切换 — codegen 不知道什么时候隐藏
page.locator(".panel").click()  # ← .panel 可能被 ng-hide 控制

# hover 才出现 — codegen 没录 hover 动作
page.locator(".menu-item").click()  # ← 需要 hover 父元素才出现

# 遮挡报错 — codegen 录了 click 但运行时报错
page.locator(".btn").click()  # ← TimeoutError: 元素被弹窗遮挡
```

### 代码模板
```python
from playwright.sync_api import sync_playwright
from pw_kit import click_with_offset

def dynamic_elements():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://example.com")

        # ng-hide 处理: 只点击可见的元素
        visible_panels = page.locator(".panel:not(.ng-hide)")
        if visible_panels.count() > 0:
            visible_panels.first.click()

        # hover 处理: 先 hover 再 click 子元素
        parent = page.locator(".menu-container")
        parent.hover()
        page.wait_for_timeout(300)  # hover 后等子元素出现
        page.locator(".menu-container .submenu-item").click()

        # 遮挡处理: 用 pw_kit 偏移点击
        if not click_with_offset(page, ".download-btn"):
            # 偏移点击失败，关闭遮挡元素再试
            try:
                page.locator(".overlay").click()  # 关闭遮挡
            except Exception:
                pass
            page.locator(".download-btn").click()

        browser.close()
```

### 页面验证
- **必须确认**: ng-hide 条件确实存在 — 页面分析对比不同阶段，确认哪些元素会隐藏/显示
- **必须确认**: hover 触发条件和出现条件 — hover 后子元素是否真的出现? 文本是什么?
- **必须确认**: 遮挡确实存在 — 歁骤 2 执行验证时报 TimeoutError 才使用 `click_with_offset`

---

## 附加功能: 定时执行 — cron/daemon

⚠️ **这不是从codegen脚本中能分析出的模式** — codegen只记录浏览器操作，不会产生任何"定时运行"的线索。只有当用户明确提出"每天自动运行"或"定时执行"等诉求时才使用 `schedule_run`。

### 适用场景
- 用户明确提出: "每天自动运行"、"定时下载"、"每天更新一次"等定时诉求
- 不需要页面验证 — 只生成调度配置

### 代码模板
```python
from pw_kit import schedule_run

# cron 模式: 生成 crontab 配置（服务器推荐）
cron_config = schedule_run(
    script_path="my_download_script.py",
    time="09:00",
    mode="cron",
)
print(cron_config)
# 输出:
# Crontab entry:
# 0 9 * * * cd /path && python my_download_script.py >> ~/logs/pw-kit.log 2>&1

# daemon 模式: 生成 Python daemon 脚本
daemon_config = schedule_run(
    script_path="my_download_script.py",
    time="09:00",
    mode="daemon",  # ← 需要额外安装: pip install -e ".[schedule]"
)
print(daemon_config)
```

### 注意
- `schedule_run` 只生成配置文本，**不执行调度本身**
- daemon 模式需要 `pip install -e ".[schedule]"` 安装 schedule 包

完整模板: `templates/scheduled_run.py`