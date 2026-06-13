# pw-kit

Playwright 开发者工具套件 — Python 库 + AI Skill。

pw-kit 包含两个组件：

| 组件                         | 说明                                                                    |
| ---------------------------- | ----------------------------------------------------------------------- |
| **pw-kit Python 库**   | 本地源码安装 (`pip install -e .`)，提供 Playwright 真正缺失的工具函数 |
| **pw-automator Skill** | opencode Skill，为 AI 开发者提供浏览器自动化方法论指导                  |

核心原则：**只做 Playwright 缺失的，不做 Playwright 已有的**。Playwright 已经做得很好的（导航、点击、输入、等待、断言、截图），直接用 Playwright API。pw-kit 针对特有的工作环境添加了一些可能用得到的接口，简化自动化流程的编写。

---

## 快速开始

### 第1步：安装

```bash
pip install -e .     # Python 包（开发模式，在项目根目录下执行）
pw-kit-install       # Chromium 浏览器（约150MB，必须装）
```

> ⚠️ **Linux 用户**：还需 `playwright install-deps chromium`。漏掉浏览器安装会报 `Executable doesn't exist`。详细步骤见 [INSTALL.md](docs/INSTALL.md)。

### 第2步：录制脚本

用 Playwright codegen 打开浏览器，手动操作，自动生成 Python 代码：

```bash
python3 -m playwright codegen https://example.com
```

操作完成后，按 Inspector 窗口的 **Copy** 按钮，把代码粘贴到 `my_script.py`。

### 第3步：运行脚本

```bash
python3 my_script.py
```

如果涉及下载操作，把脚本中的 `browser.new_page()` 改成：

```python
context = browser.new_context(accept_downloads=True)
page = context.new_page()
```

### 第4步：用 pw-kit 优化

codegen 生成的脚本通常是"录像回放"，选择器脆弱、缺少容错。用 pw-kit 函数加固：

```python
"""codegen 脚本 + pw-kit 优化示例"""
from playwright.sync_api import sync_playwright, expect
from pw_kit import extract_download_urls, discover_elements, click_with_offset

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()

    page.goto("https://example.com/docs")

    # 发现稳定选择器（替代 codegen 的 nth-child）
    elements = discover_elements(page, tags=["button", "a"])
    for el in elements[:3]:
        print(f"[{el['tag']}] 推荐: {el['suggested']}")

    # 点击可能被遮挡的按钮（替代直接 click 超时崩溃）
    if not click_with_offset(page, ".download-btn"):
        page.locator(".alt-btn").click()

    # 语义提取下载链接（替代手动拼 URL）
    urls = extract_download_urls(page, strategy="auto", keywords=["PDF"])
    print(f"提取到 {len(urls)} 个下载链接")

    browser.close()
```

完整工作流说明见下方 [Playwright codegen](#playwright-codegen) 和 [pw-kit Python 库](#pw-kit-python-库) 章节。

---

## Playwright codegen

pw-kit 的工作流起点是 Playwright **codegen**（脚本录制器）。它打开浏览器窗口，你手动操作，它自动生成 Python 代码。

```bash
# 录制指定网站（推荐起点）
python3 -m playwright codegen https://example.com

# 不指定网址，在浏览器中手动输入
python3 -m playwright codegen

# 录制时指定浏览器
python3 -m playwright codegen --browser chromium https://example.com

# 录制时指定输出文件名
python3 -m playwright codegen --target python -o my_script.py https://example.com
```

运行后会打开两个窗口：

1. **浏览器窗口** — 你在这里点击、输入、导航，跟正常上网一样
2. **Playwright Inspector 窗口** — 实时显示生成的 Python 代码

操作完成后，按 Inspector 窗口的 **Copy** 按钮，把生成的代码复制到你的编辑器。

### 保存并运行录制脚本

把复制的代码保存为 Python 文件，然后直接执行：

```bash
# 保存到文件
# 把 Inspector 中复制的代码粘贴到 my_script.py

# 运行脚本（会自动打开浏览器执行你录制的操作）
python3 my_script.py
```

如果脚本包含下载操作，运行前需要加上 `accept_downloads=True`：

```python
# 在脚本中找到 browser.new_page() 那行，改成：
context = browser.new_context(accept_downloads=True)
page = context.new_page()
```

如果想在无头模式（不显示浏览器窗口）运行，把 `headless=False` 改成 `headless=True`（或删除该参数，默认就是无头）。

更多 codegen 用法见 [Playwright Codegen 官方文档](https://playwright.dev/python/docs/codegen)。

### Playwright Python API

优化录制脚本时，参考 [Playwright Python API 文档](https://playwright.net.cn/python/docs/api/class-playwright) 查找 `get_by_role`、`get_by_text`、`expect` 等语义定位和断言方法。

---

## pw-kit Python 库

### 为什么需要 pw-kit

Playwright 核心 API 完善，但实际开发中总有"最后一公里"问题：

- 页面上有一堆下载链接，怎么批量提取？
- 元素被弹窗遮挡，Playwright `click()` 超时怎么办？
- codegen 录制的选择器里混了 `Mui-`、`ant-`、`ng-` 这种框架 class，下次构建就变了
- 想定时跑脚本，每次要手写 `cron`？

pw-kit 就是这些问题的答案。

### API 一览

| 函数                                                                       | 说明                                                                                                     |
| -------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `extract_download_urls(page, strategy, selector, expr, scope, keywords)` | 多策略下载链接提取（css/js/semantic/auto）。`auto` 策略按 css→js→semantic 级联尝试，返回首个非空结果 |
| `discover_elements(page, tags, scope)`                                   | 元素发现 + 选择器唯一性评级（★/○）                                                                     |
| `click_with_offset(page, selector, max_retries)`                         | 被遮挡时 CDP 偏移重试点击                                                                                |
| `schedule_run(script_path, time, mode, log_path)`                        | 生成 cron/daemon 定时配置                                                                                |
| `is_stable_class(class_name)`                                            | 判断 class 是否框架生成                                                                                  |
| `filter_stable_classes(class_list)`                                      | 过滤框架生成的 class                                                                                     |

函数详解、参数说明、示例代码见 [API.md](docs/API.md)。

### 使用示例

```python
"""完整工作示例：从文档站点提取下载链接"""
from playwright.sync_api import sync_playwright
from pw_kit import extract_download_urls, discover_elements, click_with_offset

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()
    page.goto("https://example.com/docs")

    # 1. 发现页面元素
    elements = discover_elements(page, tags=["button", "a"])
    for el in elements[:3]:
        print(f"[{el['tag']}] text={el['text'][:30]}, 推荐选择器: {el['suggested']}")

    # 2. 点击可能被遮挡的按钮
    if not click_with_offset(page, ".download-all-btn"):
        page.locator(".alt-download").click()

    # 3. 语义提取下载链接
    urls = extract_download_urls(page, strategy="auto", keywords=["PDF", "手册"])
    print(f"提取到 {len(urls)} 个下载链接")

    browser.close()
```

---

## pw-automator Skill

### 什么是 pw-automator

pw-automator 是 opencode 的 Skill，为 AI 开发者提供浏览器自动化方法论。它不是自动执行工具，而是 AI 分析师 — 当你描述自动化目标时，它帮你分析页面结构、选择器稳定性、边缘情况，生成完整的实现方案。

### 触发方式

在 opencode 中：

```
/pw-automator 我想自动下载 HarmonyOS 的官方文档，每天更新一次
```

### AI 分析师工作流

```
步骤 1: codegen 录制
  命令: python3 -m playwright codegen <目标网站>
  操作: 在浏览器中手动执行目标流程
  结果: 自动生成线性脚本

步骤 2: pw-automator 分析
  输入: codegen 生成的脚本 + 目标网站
  结果: AI 分析稳定性、选择器质量、边缘情况

步骤 3: 用 pw-automator 升级脚本
  替换脆弱选择器 → 用 discover_elements() 发现稳定选择器
  添加遮挡处理   → 用 click_with_offset()
  添加循环等待   → 用 while + wait_for
  添加下载提取   → 用 extract_download_urls()

步骤 4: 运行测试
  python3 script.py
```

### 安装 Skill

将 `skills/pw-automator/` 目录复制到 `~/.config/opencode/skills/`：

```bash
mkdir -p ~/.config/opencode/skills/
cp -r skills/pw-automator ~/.config/opencode/skills/
```

重启 opencode 即可自动识别，通过 `/pw-automator` 命令调用。

### Skill 目录结构

```
skills/pw-automator/
├── SKILL.md                          # Skill 定义和 AI 分析师指令
├── references/playwright-api.md      # Playwright API 快速参考
└── templates/                        # 自动化任务模板（可直接复制使用）
    ├── simple_download.py            # 单页面下载提取
    ├── iterate_table.py              # 遍历表格逐行处理
    ├── branch_download.py            # 条件分支下载
    ├── loop_progress.py              # 循环等待进度
    └── scheduled_run.py              # 定时调度配置
```

> 💡 模板文件可直接复制到你的项目中，修改 URL 和选择器即可使用。每个模板文件头部注释说明了适用场景。

---

## Playwright Actionability Checks

Playwright 内置了操作前检查机制。每次 `click`/`fill`/`check` 前，自动验证：

| 检查项          | 说明                                              |
| --------------- | ------------------------------------------------- |
| Visible         | 元素可见（非 display:none、非 visibility:hidden） |
| Stable          | 元素停止运动（位置/大小不再变化）                 |
| Receives Events | 元素没有被其他元素完全遮挡                        |
| Enabled         | 元素可用（非 disabled）                           |
| Editable        | 输入框可编辑（非 readonly、非 disabled）          |

**pw-kit 不重复封装这套机制。** 你不需要用 pw-kit 做"元素是否可见"这种检查 — Playwright 自动做了。

唯一例外是永久遮挡（`click_with_offset` 解决），详见 [API.md](docs/API.md#click_with_offset)。

---

## 项目结构

```
pw-kit/
├── README.md
├── LICENSE                          # MIT
├── pyproject.toml                   # 项目配置 + 依赖声明（唯一依赖来源）
├── docs/
│   ├── INSTALL.md                   # 安装指南（各平台）
│   ├── LOCATORS.md                  # Playwright 元素定位指南（CSS 选择器 + 语义定位）
│   └── API.md                       # 函数详解、参数说明、示例代码
├── src/pw_kit/                      # Python 库源码
│   ├── __init__.py                  # 包入口，导出所有公共函数
│   ├── extract.py                   # 语义下载提取 + 语义搜索
│   ├── discover.py                  # 元素发现 + 选择器唯一性评级
│   ├── offset.py                    # 遮挡偏移重试点击
│   ├── filters.py                   # 框架类过滤
│   ├── schedule.py                  # 定时调度（cron/daemon）
│   ├── utils.py                     # URL 检测和去重工具
│   └── _install.py                  # pw-kit-install CLI 入口
└── skills/pw-automator/             # opencode Skill
    ├── SKILL.md                     # Skill 定义
    ├── references/playwright-api.md # Playwright API 参考
    └── templates/                   # 任务模板（5个）
```

---

## FAQ

### pw-kit 和直接用 Playwright 有什么不同？

pw-kit 不是替代 Playwright 的框架，而是 Playwright 的插件包。你用 Playwright 做 90% 的工作，在 Playwright 不方便的场景调用 pw-kit：

```python
from playwright.sync_api import sync_playwright  # Playwright
from pw_kit import extract_download_urls         # pw-kit
```

### Playwright codegen 录制的脚本够用吗？

简单线性流程够用。复杂场景需要手动优化：

- 选择器稳定性（codegen 可能生成脆弱的 nth-child 选择器）
- 等待策略（codegen 用固定 timeout，应该用 wait_for_selector）
- 异常处理（codegen 不生成容错逻辑）

pw-automator Skill 帮你分析这些问题，pw-kit 工具函数帮你解决。优化时可参考 [Playwright Python API 文档](https://playwright.net.cn/python/docs/api/class-playwright) 选择更稳定的定位和等待方式

### headless 模式怎么用？

Playwright 默认 headless（不显示窗口）。调试时用 `headless=False`：

```python
browser = p.chromium.launch()               # headless（默认）
browser = p.chromium.launch(headless=False)  # 可视化（调试用）
```

### Linux 服务器部署注意什么？

1. 系统依赖：`playwright install-deps chromium`
2. 中文显示：`apt-get install fonts-noto-cjk`
3. Docker/CI：`browser = p.chromium.launch(args=["--no-sandbox"])`
4. 定时任务：`schedule_run(mode="cron")` 生成 crontab 配置

详细部署指南见 [INSTALL.md](docs/INSTALL.md)。

---

## 许可证

MIT License. See [LICENSE](LICENSE).
