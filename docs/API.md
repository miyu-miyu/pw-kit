# API 参考

pw-kit 的 6 个公共函数。所有函数接受 Playwright `Page` 对象，返回结果，无副作用。

---

## extract_download_urls(page, strategy, selector, expr, scope, keywords) → list[str]

多策略下载链接提取。4 种策略按优先级尝试，返回第一个非空结果。

```python
from pw_kit import extract_download_urls

# css: 用 CSS 选择器提取 <a> 链接
urls = extract_download_urls(page, strategy="css", selector=".download-panel")
# 结果: ['https://example.com/file.pdf', 'https://example.com/doc.zip']

# js: 执行 JS 表达式提取 URL
urls = extract_download_urls(page, strategy="js", expr="window.downloadUrls")
# 结果: ['https://example.com/pkg/1.0.0.tar.gz']

# semantic: Accessibility Tree + JS 关键词扫描
urls = extract_download_urls(page, strategy="semantic", keywords=["下载", "PDF"])
# 结果: 包含关键词的下载链接

# auto: 自动尝试 css → js → semantic，返回第一个非空结果
urls = extract_download_urls(page, strategy="auto", selector=".results", keywords=["PDF"])
# 结果: 先试 css，找到就返回，没有则试 js，最后试 semantic

# 带 scope 限定搜索范围
urls = extract_download_urls(page, strategy="css", selector="a", scope=".main-content")
# 只在 .main-content 内搜索 <a> 元素
```

**参数：**

| 参数 | 类型 | 说明 |
|---|---|---|
| `page` | `Page` | Playwright Page 对象 |
| `strategy` | `str` | `"css"` / `"js"` / `"semantic"` / `"auto"` |
| `selector` | `str` | CSS 选择器（css/auto 策略使用） |
| `expr` | `str` | JS 表达式（js 策略使用） |
| `scope` | `str` | 搜索范围限定器 |
| `keywords` | `list[str]` | 语义关键词（semantic 策略使用） |

**策略选择指南：**

| 策略 | 适用场景 | 优先级 |
|---|---|---|
| `css` | 下载链接是静态 `<a>` 标签，有明确容器选择器 | 高 |
| `js` | 下载地址在 JS 变量中、动态生成、非 href 属性 | 高 |
| `semantic` | 不确定结构、页面无规律、想盲搜 | 中 |
| `auto` | 快速测试，懒得选策略 | 兜底 |

---

## discover_elements(page, tags, scope) → list[dict]

扫描页面可交互元素，为每个元素生成优先级排序的 CSS 选择器候选列表，标注唯一性（★ 唯一 / ○ 可能重复）。

```python
from pw_kit import discover_elements

# 发现页面上所有可交互元素
elements = discover_elements(page)

# 限定标签类型
elements = discover_elements(page, tags=["button", "a"])

# 限定搜索范围
elements = discover_elements(page, tags=["input"], scope=".search-area")

# 分析结果
for el in elements:
    print(f"[{el['tag']}] id={el['id']}, text={el['text'][:40]}")
    print(f"  推荐选择器: {el['suggested']}")
    for c in el['selectors']:
        mark = "★" if c['unique'] else "○"
        print(f"  {mark} {c['selector']} ({c['type']})")
```

输出示例：

```
[input] id=None, text=""
  推荐选择器: [name='query']
  ○ #search-box (id)             ← id 匹配了多个元素
  ★ [name='query'] (name)       ← name 唯一
  ○ input.search-input (class-single)

[button] id=None, text="搜索"
  推荐选择器: [aria-label='搜索']
  ★ [aria-label='搜索'] (aria-label)
  ○ button.search-btn (class-single)
```

**选择器优先级（从高到低）：**

| 优先级 | 类型 | 示例 | 唯一性 |
|---|---|---|---|
| 1 | id | `#globalSearch` | 通常唯一 |
| 2 | href | `a[href='/download']` | 通常唯一 |
| 3 | aria-label | `[aria-label='搜索']` | 通常唯一 |
| 4 | name | `[name='query']` | 通常唯一 |
| 5 | placeholder | `[placeholder='搜索']` | 通常唯一 |
| 6 | 组合 class | `.btn.primary.large` | 可能唯一 |
| 7 | 单 class | `.search-btn` | 可能重复 |
| 8 | nth-child | `div > button:nth-of-type(2)` | 唯一但脆弱 |

---

## click_with_offset(page, selector, max_retries) → bool

当 Playwright 原生 `locator.click()` 因元素被永久遮挡而超时时，通过 CDP 协议计算偏移量点击。

Playwright 内置 Actionability Checks，自动等待元素可见/稳定/可交互。唯一例外是**永久遮挡**（弹窗、广告条、Cookie 同意横幅不会自动消失），会导致超时。`click_with_offset` 通过 CDP 协议绕过 Playwright 的事件层，直接向浏览器发送鼠标事件。

```python
from pw_kit import click_with_offset

# 推荐做法：先用 Playwright 原生 click
try:
    page.locator("#download-btn").click(timeout=3000)
except:
    # 被永久遮挡 → 用偏移重试
    click_with_offset(page, "#download-btn", max_retries=5)

# 更简洁：直接尝试偏移点击
if click_with_offset(page, ".modal .confirm-btn"):
    print("确认按钮已点击")
```

**工作原理：**

1. 先用 Playwright 原生 `click()` 尝试（超时 5 秒）
2. 超时后，用 `elementFromPoint()` 检测实际命中的元素
3. 如果命中元素不是目标元素 → 判断为遮挡
4. 计算遮挡元素高度，在遮挡物上方点击
5. 每次重试增加 2px 的随机微调

**什么时候用 Playwright 原生 click vs click_with_offset：**

| 场景 | 用什么 |
|---|---|
| 元素正常可见 | `page.click()` |
| 元素被永久遮挡（弹窗/广告/Cookie横幅） | `click_with_offset()` |
| 元素不在 DOM 里 | `wait_for_selector()` |
| 元素在 iframe 里 | `frame_locator()` |
| 元素是 Shadow DOM | 穿透 shadow 定位 |

---

## schedule_run(script_path, time, mode, log_path) → str

生成定时任务配置字符串。不直接调度，输出配置供你安装。

```python
from pw_kit import schedule_run

# cron 模式：生成 crontab 条目
config = schedule_run(
    script_path="/home/user/fetch_docs.py",
    time="09:30",
    mode="cron",
)
print(config)
# 输出:
# Crontab entry:
# 30 9 * * * cd /home/user && python /home/user/fetch_docs.py >> ~/logs/pw-kit-fetch_docs.log 2>&1
# To install, run: crontab -e

# daemon 模式：生成 Python daemon 脚本
config = schedule_run(
    script_path="~/my_project/auto_fetch.py",
    time="18:00",
    mode="daemon",
)
print(config)
# 输出 Python 脚本内容，保存后用 nohup 运行
```

**两种模式的选择：**

| 模式 | 工作原理 | 适用场景 |
|---|---|---|
| `cron` | 生成 crontab 条目 | 系统级调度，长期运行 |
| `daemon` | 生成 Python daemon 脚本（用 `schedule` 库轮询） | 开发测试，不想碰 cron 配置 |

> `daemon` 模式需要额外安装：`pip install -e ".[schedule]"`

---

## is_stable_class(class_name) → bool

判断 class 名称是否由前端框架生成。框架生成的 class（如 `MuiButton-root`、`ant-btn`、`ng-binding`）在每次构建时可能变化，不适合做 CSS 选择器。

```python
from pw_kit import is_stable_class

is_stable_class("MuiButton-root")   # False — Material UI 生成
is_stable_class("ant-btn-primary")   # False — Ant Design 生成
is_stable_class("ng-binding")       # False — Angular 生成
is_stable_class("search-btn")       # True — 应用自定义 class
is_stable_class("my-header-title")  # True — 应用自定义 class
```

**已知的框架前缀：**

| 框架 | 前缀 |
|---|---|
| Material UI | `Mui-` |
| Ant Design | `ant-` |
| Angular | `ng-` |
| Angular CDK | `cdk-` |
| Element UI | `el-` |
| Vue | `v-` |
| DevUI | `devui` |

---

## filter_stable_classes(class_list) → list[str]

批量过滤框架生成的 class，只保留应用自定义的稳定 class。

```python
from pw_kit import filter_stable_classes

classes = ["btn", "MuiButton-root", "primary", "ng-scope", "search-btn"]
filter_stable_classes(classes)
# 结果: ["btn", "primary", "search-btn"]
```