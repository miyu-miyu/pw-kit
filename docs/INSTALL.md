# 安装指南

pw-kit 安装分两步：先装 Python 包，再装 Playwright 浏览器二进制。第二步不能漏。

pw-kit 未发布到 PyPI，需从项目源码本地安装：

```bash
# 在 pw-kit 项目根目录下执行
pip install -e .             ← 第1步：Python 包（开发模式，可编辑）
pw-kit-install               ← 第2步：Chromium 浏览器（约150MB，必须装）
```

第1步 `pip install -e .` 以可编辑模式安装 Python 代码（修改源码后无需重新安装），第2步 `pw-kit-install` 装浏览器才能跑脚本。漏掉第2步会报 `Executable doesn't exist` 或 `Browser closed unexpectedly`。

如果只想安装不可编辑的正式版本：

```bash
pip install .
```

---

## 各平台安装

### macOS

```bash
cd pw-kit项目根目录
pip3 install -e .
pw-kit-install
```

如果 macOS Gatekeeper 阻止浏览器运行：

```bash
xattr -d com.apple.quarantine ~/Library/Caches/ms-playwright/chromium-*/chrome-mac/Chromium.app
```

### Linux

```bash
cd pw-kit项目根目录
pip3 install -e .
pw-kit-install
playwright install-deps chromium    # 系统依赖（仅 Linux 需要）
```

`playwright install-deps` 会自动识别你的发行版（Ubuntu/Debian/Fedora/RHEL/Arch/Alpine）并安装所需系统库。不需要手动 `apt install libnss3 ...`。

### Windows

```powershell
cd pw-kit项目根目录
pip install -e .
pw-kit-install
```

Windows 上 Python 命令是 `python` 和 `pip`（不是 `python3` 和 `pip3`）。如果 `playwright` 命令找不到，用 `python -m playwright` 替代。

---

## 验证

```bash
python3 -c "
from playwright.sync_api import sync_playwright
from pw_kit import discover_elements

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('https://example.com')
    els = discover_elements(page)
    print(f'OK — found {len(els)} elements')
    browser.close()
"
```

Windows 用 `python` 替代 `python3`。

---

## pw-kit-install 是什么

`pw-kit-install` 是 pw-kit 提供的一键安装命令，等价于 `playwright install chromium`。安装 pw-kit 后自动可用，不需要额外安装任何东西。

手动安装浏览器也可以：

```bash
playwright install chromium
```

安装其他浏览器（一般不需要，pw-kit 默认用 Chromium）：

```bash
playwright install            # chromium + firefox + webkit（约500MB）
playwright install firefox    # 只装 firefox
```

---

## 可选：schedule 模块

pw-kit 的 `schedule_run()` 依赖 `schedule` 库，不装不影响核心功能：

```bash
# 在项目根目录下，安装带 schedule 依赖的可编辑模式
pip install -e ".[schedule]"
```

---

## 常见问题

### 浏览器下载慢（中国大陆）

```bash
# 设置镜像源后重装
export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright
pw-kit-install
```

### Linux 缺共享库

报 `OSError: libnss3.so` 之类错误：

```bash
playwright install-deps chromium
```

### pip 权限错误

不要 `sudo pip`，用虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
cd pw-kit项目根目录
pip install -e .
pw-kit-install
```

---

[← 返回主文档](../README.md)