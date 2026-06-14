# Playwright 元素定位指南

面向不熟悉前端的开发者，介绍如何用 Playwright 定位网页元素和编写 CSS 选择器。

完整 API 参考: [Playwright Python API 文档](https://playwright.net.cn/python/docs/api/class-playwright)

定位器详解: [Playwright 定位器指南](https://playwright.net.cn/python/docs/locators)

其他定位器（CSS/XPath/文本）: [Playwright 其他定位器](https://playwright.net.cn/python/docs/other-locators)

---

## 核心原则

**优先用语义定位，CSS 选择器作为兜底。**

语义定位（`get_by_role`、`get_by_text` 等）模拟用户感知页面的方式，自带自动等待和重试。CSS 选择器与 DOM 结构绑定，页面变化就失效。

```
优先级: get_by_test_id > get_by_role > get_by_label > get_by_text > CSS 选择器 > nth/first
```

---

## 一、语义定位器（推荐）

### 1.1 按角色定位 `page.get_by_role()`

**首选方法。** 模拟用户和辅助技术感知页面的方式。角色是元素的 ARIA 角色（button、checkbox、heading、link、textbox 等），HTML 元素有隐式角色映射。

```python
page.get_by_role("button", name="登录").click()
page.get_by_role("checkbox", name="订阅").check()
page.get_by_role("heading", name="注册").text_content()
page.get_by_role("link", name="首页").click()
page.get_by_role("textbox", name="邮箱").fill("test@example.com")
page.get_by_role("listitem").filter(has_text="产品2").click()
```

`name` 参数支持正则表达式:

```python
import re
page.get_by_role("button", name=re.compile("submit", re.IGNORECASE)).click()
```

常见角色对照:

| HTML 元素                 | 隐式角色                    | 例子                                     |
| ------------------------- | --------------------------- | ---------------------------------------- |
| `<button>`              | button                      | `get_by_role("button", name="提交")`   |
| `<a href>`              | link                        | `get_by_role("link", name="首页")`     |
| `<input type=text>`     | textbox                     | `get_by_role("textbox", name="搜索")`  |
| `<input type=checkbox>` | checkbox                    | `get_by_role("checkbox", name="同意")` |
| `<h1>`~`<h6>`         | heading                     | `get_by_role("heading", name="标题")`  |
| `<input type=radio>`    | radio                       | `get_by_role("radio", name="选项A")`   |
| `<select>`              | combobox/listbox            | `get_by_role("combobox", name="城市")` |
| `<ul>/<ol>`             | list                        | `get_by_role("list")`                  |
| `<li>`                  | listitem                    | `get_by_role("listitem")`              |
| `<table>`               | table                       | `get_by_role("table")`                 |
| `<tr>`                  | row                         | `get_by_role("row")`                   |
| `<td>/<th>`             | cell/columnheader/rowheader | `get_by_role("cell")`                  |
| `<nav>`                 | navigation                  | `get_by_role("navigation")`            |
| `<dialog>`              | dialog                      | `get_by_role("dialog")`                |
| `<img alt>`             | img                         | `get_by_role("img", name="logo")`      |

### 1.2 按标签文本定位 `page.get_by_label()`

**表单控件首选。** 通过关联的 `<label>` 文本定位表单输入框。

```html
<label>用户名 <input type="text" /></label>
<label for="email">邮箱</label>
<input id="email" type="email" />
```

```python
page.get_by_label("用户名").fill("admin")
page.get_by_label("邮箱").fill("test@example.com")
```

### 1.3 按占位符定位 `page.get_by_placeholder()`

适用于没有 label 但有 placeholder 的输入框:

```html
<input placeholder="请输入搜索关键词" />
```

```python
page.get_by_placeholder("请输入搜索关键词").fill("Playwright")
```

### 1.4 按文本内容定位 `page.get_by_text()`

**定位非交互元素**（div、span、p 等）。交互元素（按钮、链接、输入框）应优先用 `get_by_role()`。

```python
# 子串匹配（默认，不区分大小写）
page.get_by_text("欢迎回来").click()

# 精确匹配（区分大小写）
page.get_by_text("欢迎回来", exact=True).click()

# 正则匹配
import re
page.get_by_text(re.compile("欢迎", re.IGNORECASE)).click()
```

注意: 文本匹配始终规范化空白（多空格→1个，换行→空格，忽略首尾空白）。

### 1.5 按 alt 文本定位 `page.get_by_alt_text()`

用于图片元素的 `alt` 属性:

```html
<img alt="公司logo" src="/logo.png" />
```

```python
page.get_by_alt_text("公司logo").click()
```

### 1.6 按 title 属性定位 `page.get_by_title()`

用于有 `title` 属性的任意元素:

```html
<span title="问题数量">25 个问题</span>
```

```python
page.get_by_title("问题数量").text_content()
```

### 1.7 按 test id 定位 `page.get_by_test_id()`

**最稳健**，不受文本和角色变化影响。默认匹配 `data-testid` 属性。

```html
<button data-testid="submit-btn">提交</button>
```

```python
page.get_by_test_id("submit-btn").click()
```

自定义 test id 属性名:

```python
playwright.selectors.set_test_id_attribute("data-pw")  # 改为匹配 data-pw
```

---

## 二、CSS 选择器

### 2.1 基础用法

```python
page.locator("css=button").click()     # 显式 css= 前缀
page.locator("button").click()          # 自动识别为 CSS
```

Playwright CSS 选择器**默认穿透 Shadow DOM**（XPath 不支持）。

### 2.2 标准 CSS 选择器语法

这是你需要掌握的基础 CSS 选择器，按使用频率排列:

#### 按标签名

```python
page.locator("button")       # 所有 <button>
page.locator("a")            # 所有 <a>
page.locator("input")        # 所有 <input>
```

#### 按 ID

```python
page.locator("#search-box")  # id="search-box" 的元素
```

#### 按 class

```python
page.locator(".btn-primary")         # class 含 btn-primary
page.locator(".card.title")          # class 同时含 card 和 title
page.locator("button.download")     # <button> 且 class 含 download
```

#### 按属性

```python
page.locator("[name='query']")               # name 属性值为 "query"
page.locator("[type='submit']")              # type 属性值为 "submit"
page.locator("[href='/download']")           # href 属性值为 "/download"
page.locator("[aria-label='搜索']")          # aria-label 属性
page.locator("[placeholder='请输入']")        # placeholder 属性
page.locator("[data-testid='submit']")       # data-testid 属性
page.locator("input[type='checkbox']")       # <input type=checkbox>
page.locator("a[href^='https://']")          # href 以 https:// 开头
page.locator("a[href$='.pdf']")              # href 以 .pdf 结尾
page.locator("a[href*='download']")          # href 包含 download
```

#### 后代与子元素

```python
page.locator("nav a")                     # nav 内的所有 <a>（任意深度后代）
page.locator("ul > li")                   # ul 的直接子 <li>
page.locator("table tbody tr td")         # 多级后代
page.locator(".modal .btn-primary")        # modal 内的主要按钮
```

#### 组合选择器

```python
page.locator("button, a")                 # 所有 button 或 a（逗号=任一匹配）
page.locator("input:focus")               # 当前聚焦的 input
page.locator("input:enabled")             # 未禁用的 input
page.locator("input:disabled")            # 已禁用的 input
page.locator("input:checked")             # 已选中的 checkbox/radio
```

#### 否定伪类

```python
page.locator("button:not(.hidden)")       # 不含 hidden class 的 button
page.locator("tr:not(.ng-hide)")          # 不含 ng-hide 的 tr（Angular 场景）
```

### 2.3 Playwright 扩展的 CSS 伪类

Playwright 在标准 CSS 基础上添加了以下**自定义伪类**，标准 CSS 不支持这些写法:

#### 按文本匹配

| 伪类                              | 匹配规则                                     | 示例                                |
| --------------------------------- | -------------------------------------------- | ----------------------------------- |
| `:has-text("文本")`             | 包含指定文本（子串、不区分大小写、穿透后代） | `article:has-text("Playwright")`  |
| `:text("文本")`                 | 包含文本的最小元素（子串、不区分大小写）     | `#nav :text("Home")`              |
| `:text-is("文本")`              | 精确文本（区分大小写、完整字符串）           | `#nav :text-is("Home")`           |
| `:text-matches("正则", "标志")` | 正则匹配                                     | `:text-matches("Log\\s*in", "i")` |

**重要**: `:has-text()` 必须配合其他选择器，单独用会匹配 `<body>` 等大量元素:

```python
# ❌ 错误: 匹配太多
page.locator(':has-text("下载")').click()

# ✅ 正确: 限定范围
page.locator('button:has-text("下载")').click()
page.locator('article:has-text("所有产品")').click()
```

#### 仅匹配可见元素

```python
page.locator("button:visible").click()   # 只匹配可见按钮，跳过 display:none
```

#### 包含其他元素

```python
page.locator("article:has(div.promo)")    # 包含 div.promo 的 article
page.locator("li:has(a[href*='.pdf']))")  # 包含 PDF 链接的 li
```

#### 选择第 n 个匹配项

`:nth-match()` 从所有匹配结果中取第 n 个，索引从 1 开始。不要求元素是兄弟节点:

```python
page.locator(":nth-match(:text('Buy'), 3)").click()    # 第3个含"Buy"的元素
page.locator(":nth-match(:text('Buy'), 3)").wait_for()  # 等待第3个元素出现
```

**与标准 CSS `:nth-child()` 的区别**: `:nth-child()` 只在兄弟节点中计数，`:nth-match()` 在整个页面匹配结果中计数。

#### 匹配任一条件

```python
# 逗号分隔: 匹配含"登录"或"注册"的按钮
page.locator('button:has-text("登录"), button:has-text("注册")').click()
```

### 2.4 属性简写选择器

Playwright 对常用属性有简写（注意: 这些不是完整 CSS 选择器，不支持 CSS 伪类）:

```python
page.locator('id=username').fill('value')         # 按 id
page.locator('data-testid=submit').click()        # 按 data-testid
page.locator('data-test-id=submit').click()       # 按 data-test-id
page.locator('data-test=submit').click()          # 按 data-test

# 需要CSS功能时用 css= 前缀
page.locator('css=[data-test="login"]:enabled').click()
```

### 2.5 链式选择器（`>>` 连接）

用 `>>` 将多个选择器串联，后一个在前一个的结果范围内查找:

```python
# 等价于: article → .bar > .baz → span[attr=value]
page.locator("css=article >> css=.bar > .baz >> css=span[attr=value]")
```

`*` 前缀捕获中间匹配项:

```python
# css=article >> text=Hello → 匹配含"Hello"的元素本身
# *css=article >> text=Hello → 匹配包含"Hello"元素的 article（* 前缀）
```

---

## 三、XPath 选择器（不推荐）

XPath 与 DOM 结构强绑定，不如语义定位器稳定，且**不穿透 Shadow DOM**:

```python
page.locator("xpath=//button").click()      # 显式 xpath= 前缀
page.locator("//button").click()             # // 开头自动识别为 XPath
page.locator("..")                           # .. 开头识别为 XPath（父元素）
```

XPath 联合（`|` 管道运算符）匹配任一条件:

```python
page.locator("//span[contains(@class, 'spinner')]|//div[@id='confirmation']").wait_for()
```

---

## 四、定位器组合与过滤⭐️

### 4.1 链式定位（缩小范围）

```python
# 在 iframe 内定位
page.frame_locator("#my-frame").get_by_role("button", name="登录").click()

# 在特定区域内定位
dialog = page.get_by_test_id("settings-dialog")
dialog.get_by_role("button", name="保存").click()
```

### 4.2 按文本过滤

```python
page.get_by_role("listitem").filter(has_text="产品2").click()
page.get_by_role("listitem").filter(has_not_text="缺货").count()
```

### 4.3 按后代元素过滤

```python
# 包含特定后代
page.get_by_role("listitem").filter(
    has=page.get_by_role("heading", name="产品2")
).click()

# 不包含特定后代
page.get_by_role("listitem").filter(
    has_not=page.get_by_role("heading", name="产品2")
).count()
```

### 4.4 逻辑组合

```python
# 同时匹配两个定位器
button = page.get_by_role("button").and_(page.get_by_title("订阅"))

# 匹配任一定位器
new_email = page.get_by_role("button", name="新建")
dialog = page.get_by_text("确认安全设置")
expect(new_email.or_(dialog).first).to_be_visible()
```

### 4.5 位置选择

```python
page.get_by_role("listitem").first    # 第1个
page.get_by_role("listitem").last     # 最后1个
page.get_by_role("listitem").nth(1)   # 第2个（从0开始）
```

⚠️ `.first`/`.nth()` 是最后手段，页面变化时可能指向错误元素。优先用语义定位+过滤。

### 4.6 遍历所有元素

```python
for row in page.get_by_role("listitem").all():
    print(row.text_content())
```

`.all()` 不会等待元素，立即返回当前 DOM 中的匹配。动态列表请先等待加载完成。

---

## 五、实用场景对照

| 场景         | 推荐写法                                                          | 不推荐写法                                          |
| ------------ | ----------------------------------------------------------------- | --------------------------------------------------- |
| 点击按钮     | `page.get_by_role("button", name="提交")`                       | `page.locator("div:nth-child(3) > button")`       |
| 填写输入框   | `page.get_by_label("邮箱").fill("...")`                         | `page.locator("#tsf > div:nth-child(2) > input")` |
| 勾选复选框   | `page.get_by_role("checkbox", name="同意").check()`             | `page.locator("//input[@type='checkbox'][2]")`    |
| 查找文本     | `page.get_by_text("欢迎回来")`                                  | `page.locator("text=欢迎回来")`（遗留语法）       |
| 等待加载完成 | `expect(page.get_by_text("加载完成")).to_be_visible()`          | `page.wait_for_timeout(3000)`（硬等待）           |
| 表格遍历     | `for row in page.get_by_role("row").all():`                     | `page.locator("table > tbody > tr:nth-child(1)")` |
| ng-hide 元素 | `page.locator("tr:not(.ng-hide)")`                              | —                                                  |
| 被遮挡点击   | `pw_kit.click_with_offset(page, "#btn")`                        | 强制 `force=True`（不推荐）                       |
| 弹窗拦截     | `page.add_locator_handler(...)` 或 `pw_kit.click_with_offset` | `page.wait_for_timeout(5000)`                     |

---

## 六、pw-kit 选择器辅助工具

pw-kit 的选择器辅助工具**不是日常定位用的**，而是在 **codegen 脚本优化阶段** 用的。定位元素本身直接用 Playwright 的 `get_by_role`/`get_by_text`/`locator` 等。辅助工具帮你判断选择器是否可靠、帮你发现更好的替代选择器。

### 使用时机

| 时机                                                                          | 用什么工具                  | 为什么                                                             |
| ----------------------------------------------------------------------------- | --------------------------- | ------------------------------------------------------------------ |
| codegen 生成了 `div:nth-child(3) > button` 这种深层路径选择器，想找替代方案 | `discover_elements()`     | 扫描页面，看该元素是否有 id、aria-label、稳定 class 等更好的选择器 |
| codegen 选择器包含 `MuiButton-root`、`ant-btn` 等框架 class，想判断能否用 | `is_stable_class()`       | 判断这个 class 下次构建是否可能变化                                |
| 拿到一组 class 名，想过滤掉框架生成的，只保留可靠的                           | `filter_stable_classes()` | 批量过滤，快速得到可用 class                                       |
| 页面有多个相似按钮，不确定哪个选择器唯一                                      | `discover_elements()`     | 返回每个元素的唯一性评级（★ 唯一 / ○ 重复）                      |

### `discover_elements(page, tags, scope)` — 发现稳定选择器

**什么时候调**: 你拿到了 codegen 脚本，发现其中的 CSS 选择器是深层路径（如 `div:nth-child(3) > div > button`），想确认页面上有没有更稳定的定位方式。

**怎么调**: 在浏览器打开目标页面后调用，传入你想关注的标签类型：

```python
from pw_kit import discover_elements

# 场景: codegen 生成了 page.locator("div.ng-scope:nth-child(3) > div > button").click()
# 你不确定有没有更好的选择器

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://example.com/docs")

    # 1. 扫描页面上所有按钮和链接
    elements = discover_elements(page, tags=["button", "a"])
    for el in elements:
        print(f"[{el['tag']}] text={el['text'][:30]}, 推荐: {el['suggested']}")
        for c in el['selectors']:
            mark = "★" if c['unique'] else "○"
            print(f"  {mark} {c['selector']} ({c['type']})")

    # 2. 只扫描某个区域内的元素
    elements = discover_elements(page, tags=["button"], scope=".download-panel")
    for el in elements:
        if "下载" in el["text"]:
            print(f"下载按钮推荐选择器: {el['suggested']}")
            # 替换 codegen 的脆弱选择器:
            # page.locator("div:nth-child(3) > button") → page.get_by_role("button", name="下载")

    browser.close()
```

**输出示例**:

```
[button] text=搜索, 推荐: [aria-label='搜索']
  ★ [aria-label='搜索'] (aria-label)
  ○ button.search-btn (class-single)

[button] text=下载, 推荐: #download-btn
  ★ #download-btn (id)
  ○ button.btn-primary (class-single)
```

**返回字段说明**:

| 字段          | 类型       | 说明                                                             |
| ------------- | ---------- | ---------------------------------------------------------------- |
| `tag`       | str        | 元素标签名                                                       |
| `text`      | str        | 元素文本内容（截取前80字）                                       |
| `id`        | str\| None | 元素 id                                                          |
| `classes`   | list[str]  | 元素所有 class（已过滤掉框架 class）                             |
| `suggested` | str\| None | 推荐的唯一选择器（优先级最高的那个）                             |
| `selectors` | list[dict] | 所有候选选择器，每个含 `selector`、`unique`(★/○)、`type` |

选择器优先级: id → href → aria-label → name → placeholder → 组合class → 单class → nth-child

### `is_stable_class(class_name)` — 判断单个 class 是否稳定

**什么时候调**: 你看到 codegen 生成的选择器里某个 class 名，想快速判断它能否信赖。

**怎么调**: 传入单个 class 名字符串：

```python
from pw_kit import is_stable_class

# codegen 生成了: page.locator(".MuiButton-root.ant-btn-primary.download-btn")
# 你想判断每个 class 是否可靠

is_stable_class("MuiButton-root")     # False — Material UI 生成，下次构建可能变
is_stable_class("ant-btn-primary")     # False — Ant Design 生成，下次构建可能变
is_stable_class("download-btn")        # True  — 应用自定义，稳定可用
```

**判断依据**: 匹配 `FRAMEWORK_CLASS_PATTERN` 正则（前缀: `devui|ng-|cdk|mat-|Mui|ant-|el-|v-|cdk`）。

### `filter_stable_classes(class_list)` — 批量过滤框架 class

**什么时候调**: 你拿到了一个元素的所有 class 列表，想一次性去掉框架生成的，只保留能做选择器的。

**怎么调**: 传入 class 列表：

```python
from pw_kit import filter_stable_classes

# 从 codegen 选择器中提取的 class 列表
classes = ["btn", "MuiButton-root", "primary", "ng-scope", "download-btn"]
stable = filter_stable_classes(classes)
print(stable)  # ["btn", "primary", "download-btn"]

# 用过滤后的稳定 class 组合选择器
selector = "." + ".".join(stable)  # ".btn.primary.download-btn"
page.locator(selector).click()
```

### `FRAMEWORK_CLASS_PATTERN` — 框架 class 正则（可直接用）

```python
from pw_kit import FRAMEWORK_CLASS_PATTERN

# 匹配框架生成的 class 名
FRAMEWORK_CLASS_PATTERN.match("MuiButton-root")   # 有匹配 → 框架生成
FRAMEWORK_CLASS_PATTERN.match("btn-primary")       # 无匹配 → 应用自定义
```

### 典型工作流: codegen → 扫描 → 替换

```python
"""完整示例: 用 pw-kit 辅助工具优化 codegen 选择器"""
from playwright.sync_api import sync_playwright, expect
from pw_kit import discover_elements, is_stable_class

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://example.com/docs")

    # 歁骤 1: codegen 生成的脆弱脚本
    # page.locator("div.ng-scope:nth-child(3) > div > button.download-btn").click()

    # 歁骤 2: 扫描页面，找更好的选择器
    elements = discover_elements(page, tags=["button"])
    target = None
    for el in elements:
        if "下载" in el.get("text", ""):
            target = el
            break

    if target and target["suggested"]:
        print(f"发现稳定选择器: {target['suggested']}")
        # 歁骤 3: 替换脆弱选择器
        # page.locator("div:nth-child(3) > button") → 用 suggested
        page.locator(target["suggested"]).click()
    else:
        # 兜底: 原始 codegen 选择器
        page.locator("div:nth-child(3) > button").click()

    browser.close()
```

已知框架前缀: `Mui`、`ant-`、`ng-`、`cdk`、`mat-`、`el-`、`v-`、`devui`

---

## 七、定位器决策树

当不确定用哪种定位方式时，按以下顺序判断:

```
1. 元素有 data-testid?      → page.get_by_test_id("xxx")
2. 元素有唯一 id?            → page.locator("#my-id")
3. 元素有 ARIA 角色+名称?    → page.get_by_role("button", name="提交")
4. 表单控件有关联 label?     → page.get_by_label("密码")
5. 输入框有 placeholder?     → page.get_by_placeholder("搜索")
6. 有唯一可见文本?           → page.get_by_text("xx", exact=True)
7. 图片有 alt?               → page.get_by_alt_text("logo")
8. 元素有 title 属性?        → page.get_by_title("提示")
9. 有稳定 class?             → page.locator(".user-card")
10. 只能靠位置?              → locator.first / .nth(0) ← 最后手段，尽量避免
11. ng-hide 动态切换?        → page.locator(".panel:not(.ng-hide)")
12. 需遍历多个同类元素?       → for item in locator.all(): item.click()
```

---
