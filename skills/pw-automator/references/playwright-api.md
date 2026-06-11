# Playwright 常用 API 速查

本文件是 pw-automator Skill 的参考文件，当需要查 Playwright API 时读取。

## Page 常用操作

```python
# 导航
page.goto("https://example.com", wait_until="networkidle")

# 语义定位 (推荐)
page.get_by_role("button", name="提交").click()
page.get_by_placeholder("输入密码").fill("secret")
page.get_by_test_id("user-name").text_content()
page.get_by_label("电子邮件").click()
page.get_by_text("确认删除", exact=True).click()

# 等待
page.wait_for_load_state("networkidle")
page.wait_for_url("**/success")
page.wait_for_function("window.loaded === true")

# 状态获取
title = page.title()
url = page.url()
content = page.content()
```

## Locator 操作

```python
# 创建
btn = page.get_by_role("button", name="下载")
row = page.locator("table tbody tr")

# 操作 (自动 actionability 检查)
btn.click()
btn.dblclick()
btn.hover()
btn.fill("text")
btn.select_option("value1")

# 链式定位
cell = page.locator("table").locator("tr").locator("td").first
btn = page.locator(".panel:not(.ng-hide)").get_by_role("button")

# 信息获取
count = row.count()
text = row.text_content()
html = row.inner_html()
attr = row.get_attribute("href")

# 过滤
visible_btn = page.locator("button").filter(has_text="确认")
btn_with_icon = page.locator("button").filter(has=page.locator(".icon"))
```

## expect 断言

```python
from playwright.sync_api import expect

expect(page).to_have_title("文件管理")
expect(page).to_have_url("**/success")
expect(page.locator("button")).to_be_enabled()
expect(page.get_by_text("加载完成")).to_be_visible()
expect(page.locator("input")).to_have_value("test")

# 多数断言支持 timeout
expect(page.get_by_text("成功")).to_be_visible(timeout=10000)
```

## Actionability Checks

Playwright 在执行操作前自动检查元素是否可交互:

| 检查项 | 说明 |
|---|---|
| Visible | 元素在视口中可见 |
| Stable | 元素停止动画/过渡 |
| Receives Events | 没有被遮挡 |
| Enabled | 未被禁用 |
| Editable | 表单项可编辑 |

不需要手动验证这些条件 — Playwright 自动处理。唯一例外: 永久性遮挡 → 用 pw-kit `click_with_offset()`。