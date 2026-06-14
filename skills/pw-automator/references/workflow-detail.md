# pw-automator 工作流详细说明

本文件包含 SKILL.md 中步骤 2-6 的完整操作指南。遇到这些步骤时，SKILL.md 会指引你读取本文件。

---

## Step 2: 执行验证

**先跑一遍，看脚本本身能不能正常执行。** 不验证就优化 = 盲修代码。

### 操作方式

1. 让用户运行原始 codegen 脚本: `python3 my_script.py`
2. 如果成功 → 记录，继续步骤 3
3. 如果报错 → **先分析报错原因再继续**

### 常见执行失败原因

| 报错 | 原因 | 处理方式 |
|---|---|---|
| `TimeoutError` | 选择器失效或页面加载慢 | 记录哪个选择器超时，步骤 3 重点分析 |
| `strict mode violation` | 选择器匹配多个元素 | 歁骤 3 用 discover_elements 确认实际数量 |
| `Executable doesn't exist` | 没装浏览器 | 让用户执行 `pw-kit-install` |
| `Browser closed unexpectedly` | 系统依赖缺失 | Linux: `playwright install-deps chromium` |
| 脚本卡住不动 | 元素被遮挡或页面变化 | 记录卡在哪一步 |

### 汇报模板

```
✅ 原始脚本执行成功 — 所有步骤正常完成
   继续步骤 3: 分析页面内容

❌ 原始脚本执行失败:
   第5行 page.locator("...").click()
   → TimeoutError: 选择器找不到元素
   需先分析页面实际结构再优化
```

如果用户无法运行脚本:

```
⚠️ 未验证原始脚本执行情况。以下分析基于代码层面，可能遗漏运行时问题。
   建议你在本地运行一次 python3 my_script.py 确认。
```

---

## Step 3: 网页分析（分阶段扫描）

**按脚本的实际执行流程，逐阶段分析每个页面的真实结构。** 不是一次性扫描，而是分阶段扫描。

### 两种页面变化类型

| 变化类型 | 触发条件 | 分析方式 | 示例 |
|---|---|---|---|
| **URL 变化（导航）** | `page.goto()`、点击链接跳转 | 新 URL → 新扫描阶段 | 登录页 → 搜索页 → 详情页 |
| **DOM 变化（同 URL）** | `click()`、`fill()` 触发 AJAX/SPA 更新 | 同 URL → 操作后再扫描子阶段 | 搜索按钮 → 结果出现；筛选按钮 → 下拉展开 |

### 触发页面分析的操作类型

以下操作都可能改变页面结构，需要在操作后新增一个扫描阶段:

| 操作类型 | 是否改变页面 | 何时扫描 | 示例 |
|---|---|---|---|
| `page.goto()` | ✅ URL 变化 | goto + wait_load 后扫描 | 导航到新页面 |
| `page.click()` | 可能 | 点击后等 DOM 稳定再扫描 | 点击搜索 → 结果列表出现 |
| `page.fill()` | 可能 | 填写后等 DOM 稳定再扫描 | 输入关键字 → 自动补全出现 |
| `page.wait_for_timeout()` | 不直接改变 | 但等待结束后 DOM 可能已变化，**应扫描** | 等待3秒后 → 进度条到100% |
| `page.wait_for_load_state()` | ✅ 网络请求完成 | 等待完成后扫描 | 等待 networkidle → 页面加载完成 |
| `page.wait_for_url()` | ✅ URL 变化 | URL 变化后扫描 | 等待跳转到结果页 |
| `page.wait_for_selector()` | DOM 变化 | 选择器出现后扫描 | 等待某个元素出现 |
| `page.wait_for_function()` | 可能 | 函数条件满足后扫描 | 等待 window.loaded === true |

**关键新增: wait 操作** — codegen 脚本中的 `wait_for_timeout`、`wait_for_load_state`、`wait_for_url`、`wait_for_selector`、`wait_for_function` 都意味着页面正在变化。等待结束后，DOM 可能已经更新，**应该在等待结束后也扫描一次页面**:

```
脚本: page.click(搜索按钮) → page.wait_for_timeout(3000) → page.locator(结果).click()

分析阶段:
  阶段B:   点击搜索按钮前 → scan(page, "B: 搜索页")
  阶段B+1: 点击搜索按钮后 → scan(page, "B+1: 点击搜索后（DOM可能开始变化）")
  阶段B+2: wait_for_timeout 结束后 → scan(page, "B+2: 等待3秒后（搜索结果应该出现了）")
  
  → 对比 B+1 和 B+2，确认等待3秒后确实出现了搜索结果
  → 优化: wait_for_timeout → expect(page.get_by_text("搜索结果")).to_be_visible()
```

### 分阶段分析策略

每个 `page.goto()` 是一个新的主阶段（字母 A/B/C），同 URL 内的变化是子阶段（A+1/A+2）:

```
脚本步骤                       →  分析阶段
──────────────────────────────────────────────────
page.goto(URL1)                →  阶段A: URL1 初始页面
page.click(按钮)                →  阶段A+1: 点击后 DOM 变化
page.wait_for_timeout(3000)    →  阶段A+2: 等待结束后 DOM 变化
page.goto(URL2)                →  阶段B: URL2 页面
page.fill(输入框)               →  阶段B+1: 填写后 DOM 变化
page.click(搜索)                →  阶段B+2: 搜索结果
page.wait_for_load_state()     →  阶段B+3: 网络请求完成后
```

### 操作方式

**方式 A: 生成分阶段分析脚本（推荐）**

使用 `templates/page_analyze.py` 中的 `scan()` 函数，按脚本步骤生成分阶段脚本让用户运行。每个关键操作后调用 `scan()`，所有 wait 操作结束后也调用 `scan()`。

**方式 B: AI 用 pw-kit CLI 逐步分析**

AI 逐步生成 pw-kit Python 脚本片段，通过 bash 执行并读取输出。每段脚本使用 `discover_elements()` 和 `extract_download_urls()` 扫描页面，输出元素和下载链接数据。AI 读取输出后决定下一步操作，再生成下一段脚本。

操作流程:
1. AI 生成阶段1脚本（goto + scan）→ bash 执行 → 读取输出
2. AI 根据输出决定下一步 → 生成阶段2脚本（click/fill + scan）→ bash 执行 → 读取输出
3. 重复直到所有阶段分析完成

⚠️ 每段脚本需要启动浏览器，效率低于方式 A（一次性运行）。但优势是 AI 可以根据每步的输出实时调整分析策略。

如果环境配置了 Playwright MCP（opencode 的 `/playwright` skill），也可以用 MCP 逐步操控浏览器。但 MCP 无法调用 pw-kit 函数（`discover_elements`、`extract_download_urls`），只能用 `browser_snapshot` 获取 accessibility tree — 分析深度不如 pw-kit CLI 方式。

**方式 C: 用户截图**

按脚本步骤手动操作，每个关键步骤后截图贴回来。

如果所有方式都不行:

```
⚠️ 未分析目标网页内容。优化建议基于代码模式推断，未验证页面实际结构。
   建议你在本地用 discover_elements() 扫描页面确认。
```

### 页面变化对比规则

扫描完每个阶段后，对比相邻阶段:

| 对比项 | 用途 |
|---|---|
| 新增元素 → 确定 expect / wait_for 的等待目标 |
| 消失元素 → 标记选择器在操作后失效 |
| 选择器唯一性变化 → 操作后可能更稳定 |
| 下载链接变化 → 确定提取最佳时机 |

**对比示例 — URL 变化（导航）**:

```
阶段A: 登录页
  [input] suggested=[name='username']    ← 唯一
  [input] suggested=[name='password']    ← 唯一
  [button] text="登录", suggested=[aria-label='登录']

阶段A+1: 登录成功后
  新增: [text] "欢迎回来" ← expect 的等待目标！
  新增: [link] text="搜索"
  消失: [input] name='username' ← 登录页选择器失效

  → expect(page.get_by_text("欢迎回来")).to_be_visible() 替代 wait_for_timeout
```

**对比示例 — DOM 变化（同 URL）**:

```
阶段B: 搜索页
  [input] suggested=[placeholder='搜索']
  [button] text="搜索", suggested=[aria-label='搜索']

阶段B+1: 点击搜索后
  新增: [button] text="筛选" ← 搜索后才出现
  新增: [text] "搜索结果" ← 可作为 expect 等待目标

  → expect(page.get_by_text("搜索结果")).to_be_visible() 替代 wait_for_timeout
```

**对比示例 — wait 结束后 DOM 变化**:

```
阶段B+2: wait_for_timeout(3000) 结束后
  新增: [text] "100%" ← 进度条完成
  新增: [button] text="下载报告" ← 进度完成后出现

  → for i in range(60):
      if "100%" in page.locator(".progress").text_content(): break
      page.wait_for_timeout(2000)
    替代硬等待
```

---

## Step 4: 逐行标注风险

结合步骤 2 和 3 的实际数据标注风险，附上页面证据:

| 标注 | 含义 | 页面验证 |
|---|---|---|
| 🔴 高风险 | 选择器已失效 | 页面分析确认匹配 0 个或多个 |
| 🟡 中风险 | 当前可用但不稳健 | 页面分析确认有更好替代 |
| 🟢 低风险 | 语义定位，稳健 | 页面分析确认元素确实存在 |
| 🔵 缺失模式 | 需要的逻辑 codegen 没生成 | 页面分析确认模式适用 |
| 🟣 事实不符 | 建议与页面实际不符 | 页面上没有建议的元素 |

标注示例:

```
🔴 第12行: page.locator("div:nth-child(3) > button")
   → 页面分析: 匹配0个元素（结构已变化）
   → discover_elements 发现: [button] text="下载", suggested=#download-btn

🟡 第23行: page.wait_for_timeout(3000)
   → 页面分析: 等待3秒后出现文本 "操作成功"（已确认）
   → 替换: expect(page.get_by_text("操作成功")).to_be_visible(timeout=5000)

🟡 第30行: page.wait_for_timeout(2000)
   → 页面分析: 等待后出现进度条100%（已确认）
   → 替换: for i in range(60): if "100%" in progress.text_content(): break
```

---

## Step 5: 询问用户

附上页面实际数据，让用户基于真实信息做决策:

```
⚠️ 发现以下问题（基于页面分析）:

  🔴 第12行: 选择器失效 → 页面实际有 #download-btn
     替换: page.locator("#download-btn") 或 page.get_by_role("button", name="下载文件")

  🟡 第23行: wait_for_timeout(3000)
     页面分析确认: 点击后出现 "操作成功"
     替换: expect(page.get_by_text("操作成功")).to_be_visible()
     如果你等待的不是这个文本，请告诉我实际等待什么

  🟡 第30行: wait_for_timeout(2000)
     页面分析确认: 进度条到100%
     替换: for loop 等待进度完成

  🔵 缺少: 下载链接提取（页面有3个下载链接）

  是否要逐一优化? 不确定的地方请告诉我。
```

当无法确认页面状态时，**必须向用户提问，不能猜测**:

| 场景 | 问用户 |
|---|---|
| wait_for_timeout 后应等待什么 | "点击后页面会出现什么? 文本/URL变化/元素消失?" |
| 重复操作应遍历多少项 | "处理所有行还是只前N行?" |
| 选择器有多个候选 | "页面上有3个按钮，你要点哪个?" |
| 条件分支的触发条件 | "什么情况下出现弹窗?" |

---

## Step 6: 给出替换方案

每个替换方案标注依据来源:

| 原始写法 | 替换方案 | 依据 |
|---|---|---|
| `locator("div:nth-child(3) > button")` | `get_by_role("button", name="下载")` | 页面分析确认 |
| 重复 fill+click | `for row in rows.all()` | 页面分析确认数量 |
| `wait_for_timeout(2000)` | `expect(...).to_be_visible()` | 页面分析确认等待目标 |
| `wait_for_timeout(2000)` | `for loop 等待进度` | 页面分析确认有进度条 |
| 下载链接提取 | `pw_kit.extract_download_urls()` | 页面分析确认有链接 |

**如果页面数据不足以确定方案，列出所有选项让用户选择**:

```
第23行 wait_for_timeout(3000) 的替换方案:
  A: expect(page.get_by_text("操作成功")).to_be_visible() — 页面出现此文本
  B: page.wait_for_url("**/result") — 操作可能导致URL变化
  C: for loop 等待进度条 — 页面有进度条
  请选择或告诉我实际等待什么
```