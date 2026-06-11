---
name: pw-automator
description: "Playwright 浏览器自动化脚本开发助手。核心能力: 分析 codegen 生成的线性脚本，识别可泛化的步骤，给出更健壮的替代方案。当用户提到浏览器自动化、playwright脚本、自动化下载、网页自动操作、codegen升级、iterate遍历、定时下载、branch条件分支、语义提取下载链接、pw-kit、动态元素(ng-hide/hover)时，务必使用本 Skill。即使用户只说'帮我写个自动化脚本'而没有提到 Playwright，也应触发本 Skill — 因为 Playwright 是当前最推荐的浏览器自动化方案。"
---

# pw-automator — Playwright 浏览器自动化脚本开发助手

pw-automator 帮助开发者编写、优化和升级 Playwright 浏览器自动化脚本。核心价值是**分析 codegen 生成的线性脚本，识别可泛化的步骤，给出更健壮的替代方案**。

Codegen 生成的脚本是"录像回放"式的线性代码 — 它能跑一次，但经不起页面变化。pw-automator 帮你把这类脚本改造成有模式、有分支、有容错的工程化代码。

```python
# codegen 生成的脆弱代码
page.locator("div.ng-scope:nth-child(3) > div > button").click()
page.wait_for_timeout(2000)

# pw-automator 改造后的健壮代码
page.get_by_role("button", name="提交").click()
page.get_by_text("提交成功").wait_for()
```

---

## AI 分析师工作流 (核心能力)

收到 codegen 脚本或场景描述后，按 5 步处理:

### Step 1: 接收脚本

接收用户的 codegen 脚本或纯文字场景描述。

### Step 2: 逐行分析标注风险

| 标注 | 含义 | 示例 |
|---|---|---|
| 🔴 高风险 | 硬编码选择器、nth-child、依赖时间 | `locator("div:nth-child(3) > span")` |
| 🟡 中风险 | 当前可用但页面变化可能失败 | 无 data-testid 的语义定位 |
| 🟢 低风险 | 语义定位、原生 Playwright 能力 | `get_by_role("button", name="提交")` |
| 🔵 缺失模式 | codegen 无法生成的复杂逻辑 | 遍历/分支/循环/语义提取 |

### Step 3: 询问用户

对发现的问题给出 summary，让用户选择要处理哪些:

```
⚠️ 发现以下问题:
  🔴 第12行: 硬编码 nth-child 选择器
  🔴 第23行: wait_for_timeout(3000) 硬等待
  🟡 第8-15行: 8次相似 fill+click → 适合 iterate 模式
  🔵 缺少: 下载验证逻辑

是否要逐一优化? 请选择处理项。
```

### Step 4: 给出替换方案

| 原始写法 | 替换方案 |
|---|---|
| `locator("div:nth-child(3) > button")` | `get_by_role("button", name="xx")` 或 `get_by_test_id("xx")` |
| 重复N次的fill+click | `for row in rows.all(): row.fill(...)` |
| 线性流程 | `if page.get_by_text("异常").is_visible(): ... else: ...` |
| `wait_for_timeout(2000)` | `expect(page.get_by_text("成功")).to_be_visible(timeout=5000)` |
| 下载链接提取 | `pw_kit.extract_download_urls(page)` |
| 被遮挡的元素点击 | `pw_kit.click_with_offset(page, "selector")` |

### Step 5: 用户确认 → 生成最终脚本

应用用户确认的所有替换，输出完整的 Python 脚本。

---

## 分析维度

AI 分析脚本时，按 7 个维度逐行审查:

1. **定位稳定性**: 深层路径/nth-child → 语义定位
2. **操作可靠性**: `wait_for_timeout` → expect断言
3. **模式识别**: 重复fill+click → iterate遍历
4. **分支覆盖**: 单一路径 → if/else分支
5. **容错处理**: 无try/except → 容错包裹
6. **功能缺口**: 下载提取/遮挡偏移/定时 → pw-kit函数
7. **Playwright最佳实践**: 手动scroll/sleep → PW原生API

---

## 选择器决策树

推荐定位方式时，按优先级从高到低判断:

```
1. data-testid? → page.get_by_test_id("xxx")
2. 唯一id? → page.locator("#my-id")
3. 唯一属性? → get_by_role/link/placeholder/label
4. 唯一可见文本? → page.get_by_text("xx", exact=True)
5. 稳定class? → page.locator(".user-card")
6. 只有位置? → locator(...).first / .nth(0) (最低稳定性)
7. ng-hide切换? → locator(".panel:not(.ng-hide)")
8. 多个匹配需遍历? → for item in locator(".list").all(): item.click()
```

---

## 模式库 (6种codegen无法生成的模式)

### Pattern 1: iterate — 表格/列表遍历

用 `.all()` 获取所有元素，循环处理每个。适合表格行、列表项、卡片组。

```python
rows = page.locator("table tbody tr").all()
for row in rows:
    name = row.locator("td:nth-child(1)").text_content()
    link = row.locator("td a").get_attribute("href")
    print(f"{name}: {link}")
```

完整模板: `templates/iterate_table.py`

### Pattern 2: branch — 条件分支

根据页面状态走不同路径。

```python
if page.locator(".download-modal").is_visible():
    urls = pw_kit.extract_download_urls(page, scope=".download-modal")
elif page.locator(".direct-download-btn").is_visible():
    with page.expect_download() as d:
        page.locator(".direct-download-btn").click()
else:
    urls = pw_kit.extract_download_urls(page, strategy="semantic")
```

完整模板: `templates/branch_download.py`

### Pattern 3: loop — 轮询 + 子操作

等待条件满足后执行操作，循环直到超时。

```python
for i in range(60):
    if "100%" in page.locator(".progress-bar").text_content():
        break
    page.wait_for_timeout(2000)
```

完整模板: `templates/loop_progress.py`

### Pattern 4: 语义提取下载链接

多策略级联提取下载链接 (css → js → semantic)。

```python
from pw_kit import extract_download_urls

urls = extract_download_urls(page, strategy="auto", scope=".download-panel")
urls = extract_download_urls(page, strategy="semantic", keywords=["下载", "PDF"])
```

完整模板: `templates/simple_download.py`

### Pattern 5: 动态元素处理

处理 ng-hide 切换、hover后显示、被遮挡等场景。

```python
# ng-hide 否定策略
page.locator("tr:not(.ng-hide)").click()

# hover 后点击
item.hover()
item.locator(".delete-btn").wait_for(state="visible")
item.locator(".delete-btn").click()

# 遏挡偏移
pw_kit.click_with_offset(page, "#real-button")
```

### Pattern 6: 定时执行

```python
from pw_kit import schedule_run

schedule_run(script_path="./download.py", time="09:00", mode="cron")
```

完整模板: `templates/scheduled_run.py`

---

## pw-kit API 参考

pw-kit 是 pw-automator 配套的工具库，只封装 Playwright 真正缺失的功能。安装: `pip install -e .`（在项目根目录下执行）

### 真实API (仅以下6个函数)

| 函数 | 签名 | 返回值 | 说明 |
|---|---|---|---|
| `extract_download_urls` | `(page, strategy="auto", selector=None, expr=None, scope=None, keywords=None)` | `list[str]` | 多策略下载链接提取 (css/js/semantic/auto) |
| `discover_elements` | `(page, tags=None, scope=None)` | `list[dict]` | 元素发现+选择器唯一性评级 |
| `click_with_offset` | `(page, selector, max_retries=3)` | `bool` | 被遮挡时CDP偏移重试点击 |
| `schedule_run` | `(script_path, time="09:00", mode="cron", log_path=None)` | `str` | 生成定时配置 (cron/daemon) |
| `is_stable_class` | `(class_name)` | `bool` | 判断class是否非框架生成 |
| `filter_stable_classes` | `(class_list)` | `list[str]` | 过滤框架生成的class |

⚠️ **只使用以上函数** — 不要调用 pw-kit 中不存在的函数。

---

## Actionability Checks 说明

Playwright 在执行操作前自动检查元素是否可交互 (Visible/Stable/Receives Events/Enabled/Editable)。pw-kit 不重复封装这套机制 — 直接用 Playwright 的 `click()`、`fill()` 即可。

唯一例外: **永久性遮挡** (cookie栏、浮窗永远挡住按钮) → 用 `pw_kit.click_with_offset()`。

详细的 Playwright API 参考: 读取 `references/playwright-api.md`

---

## codegen 升级完整示例

```python
"""codegen 脚本升级为工程化代码的完整示例"""

from playwright.sync_api import sync_playwright, expect
from pw_kit import extract_download_urls, click_with_offset

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        try:
            page.goto("https://reports.example.com")

            # branch: 已登录则跳过
            if not page.get_by_text("欢迎回来").is_visible():
                page.get_by_placeholder("用户名").fill("admin")
                page.get_by_placeholder("密码").fill("pass")
                page.get_by_role("button", name="登录").click()
                expect(page.get_by_text("登录成功")).to_be_visible(timeout=5000)

            # iterate: 遍历表格找可下载的报表
            for row in page.locator("table tbody tr").all():
                if "已完成" in row.locator(".status").text_content():
                    row.get_by_role("button", name="下载").click()
                    break

            # 语义提取下载链接
            urls = extract_download_urls(page, scope=".download-panel")
            print(f"找到 {len(urls)} 个下载链接")

        except Exception as e:
            page.screenshot(path="failure.png")
            raise
        finally:
            browser.close()

if __name__ == "__main__":
    main()
```

---

## 规则速查

| 场景 | 推荐做法 |
|---|---|
| 定位元素 | 按决策树选最高优先级 |
| 等待条件 | `expect(...).to_be_visible(timeout=...)` |
| 遍历元素 | `.all()` + for 循环 |
| 条件分支 | if/else |
| 下载链接 | `pw_kit.extract_download_urls()` |
| 遮挡点击 | `pw_kit.click_with_offset()` |
| 轮询等待 | while + `wait_for_timeout()` |
| 定时执行 | `pw_kit.schedule_run()` |
| 容错 | try/except + `page.screenshot()` |
| 框架class | `pw_kit.is_stable_class()` / `filter_stable_classes()` |