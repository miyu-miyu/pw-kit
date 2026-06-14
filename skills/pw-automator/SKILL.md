---
name: pw-automator
description: "Playwright 浏览器自动化脚本开发助手。核心能力: 验证 codegen 脚本能否运行 → 分析目标网页内容 → 基于真实页面数据给出健壮的优化方案。当用户提到浏览器自动化、playwright脚本、自动化下载、网页自动操作、codegen升级、iterate遍历、定时下载、branch条件分支、语义提取下载链接、pw-kit、动态元素(ng-hide/hover)时，务必使用本 Skill。即使用户只说'帮我写个自动化脚本'而没有提到 Playwright，也应触发本 Skill — 因为 Playwright 是当前最推荐的浏览器自动化方案。"
---

# pw-automator — Playwright 浏览器自动化脚本开发助手

核心价值: **验证 → 分析 → 优化**。先跑一遍看脚本能否执行，再分析网页真实内容，最后基于页面数据给出有依据的优化方案。不看页面就优化 = 凭猜测写代码，可能写出页面上根本不存在的东西。

```python
# codegen 生成的脆弱代码（纯录像回放）
page.locator("div.ng-scope:nth-child(3) > div > button").click()
page.wait_for_timeout(2000)

# pw-automator 改造后的健壮代码（基于页面分析确认按钮文本是"提交"，操作后出现"提交成功")
page.get_by_role("button", name="提交").click()
expect(page.get_by_text("提交成功")).to_be_visible(timeout=5000)
# ← "提交成功" 从页面确认，不是猜测
```

---

## 7 步工作流

按顺序执行。步骤 2 和 3 是新增的关键步骤，**不能跳过**。

| 步骤 | 名称 | 目的 | 详细说明 |
|---|---|---|---|
| 1 | 接收脚本 | 提取 URL 和操作步骤 | — |
| 2 | **执行验证** | 先跑一遍，看脚本本身能否正常执行 | → 读取 `references/workflow-detail.md` Step 2 |
| 3 | **网页分析** | 分阶段扫描页面真实内容 | → 读取 `references/workflow-detail.md` Step 3 |
| 4 | 逐行标注风险 | 结合页面数据标注风险等级 | → 读取 `references/workflow-detail.md` Step 4 |
| 5 | 询问用户 | 附页面证据，列出真实选项 | → 读取 `references/workflow-detail.md` Step 5 |
| 6 | 给出替换方案 | 每个方案标注依据来源 | → 读取 `references/workflow-detail.md` Step 6 |
| 7 | 生成最终脚本 | 应用所有确认的替换 | → 读取 `references/workflow-detail.md` Step 7 |

**步骤 2 和 3 的详细操作方式、脚本模板、页面变化对比规则** 都在 `references/workflow-detail.md`。遇到这些步骤时，必须读取该文件获取完整指令。

---

## 核心纪律

1. **必须验证脚本能否执行** — 步骤 2。无法验证时必须告知用户，标注后续分析的可靠性
2. **必须分析网页内容** — 步骤 3。无法分析时必须告知用户，标注优化建议为"代码模式推断"而非"页面分析确认"
3. **不能凭猜测写等待条件** — 不知道 `wait_for_timeout` 后应等待什么，就问用户或列出选项，不能编造文本
4. **不能凭猜测写语义定位器** — 没有页面数据时不能用 `get_by_role(name="xxx")`，除非用户确认该元素存在
5. **每个优化建议必须有依据** — 标注来源: "页面分析确认" / "代码模式推断" / "用户确认"

---

## 分析维度

按 7 个维度逐行审查，每个维度结合步骤 3 的页面数据:

| 维度 | 目标 | 页面验证 |
|---|---|---|
| 定位稳定性 | 深层路径 → 语义定位 | discover_elements 确认替代选择器存在 |
| 操作可靠性 | `wait_for_timeout` → expect 断言 | 页面确认等待目标确实出现 |
| 模式识别 | 重复操作 → iterate 遍历 | 页面确认实际有多少项 |
| 分支覆盖 | 单一路径 → if/else | 页面确认分支条件确实存在 |
| 容错处理 | 无 try/except → 容错包裹 | 步骤 2 提供失败场景 |
| 功能缺口 | 下载提取/遮挡偏移/定时 | 页面确认下载链接存在/元素被遮挡 |
| 事实验证 | 建议是否与页面一致 | 防止凭猜测优化 |

---

## 选择器决策树

```
1. data-testid?      → page.get_by_test_id("xxx")
2. 唯一id?            → page.locator("#my-id")
3. ARIA角色+名称?    → page.get_by_role("button", name="提交")
4. 关联 label?        → page.get_by_label("密码")
5. placeholder?       → page.get_by_placeholder("搜索")
6. 唯一可见文本?     → page.get_by_text("xx", exact=True)
7. alt/title?         → page.get_by_alt_text() / get_by_title()
8. 稳定class?         → page.locator(".user-card")
9. 只有位置?          → locator.first / .nth(0) ← 最后手段
10. ng-hide切换?      → locator(".panel:not(.ng-hide)")
11. 多个匹配遍历?    → for item in locator.all(): item.click()
```

⚠️ 每个推荐必须验证: discover_elements 确认页面上有此元素

选择器和 CSS 详细指南: 读取 `references/locators.md`

---

## 模式库

codegen 无法生成的 5 种模式（从脚本分析中发现）。完整代码和适用场景: 读取 `references/patterns.md`

| 模式 | 适用场景 | 页面确认 |
|---|---|---|
| iterate | 表格/列表遍历 | 确认列表实际行数 |
| branch | 条件分支 | 猴认各分支条件存在 |
| loop | 轮询等待 | 猴认等待目标会变化 |
| 语义提取 | 下载链接提取 | 猴认页面有下载链接 |
| 动态元素 | ng-hide/hover/遮挡 | 猴认触发条件和出现条件 |

## 附加功能: 定时执行

⚠️ **这不是从codegen脚本中能分析出的模式** — codegen只记录浏览器操作，不会产生任何"定时运行"的线索。**步骤 7 生成最终脚本后，主动询问用户是否需要定时执行。** 只有当用户确认需要时才使用。

`schedule_run(script_path, time, mode)` → 生成 cron/daemon 配置文本。详细说明: 读取 `references/patterns.md` 定时执行章节

---

## pw-kit API 参考

| 函数 | 返回值 | 说明 |
|---|---|---|
| `extract_download_urls(page, ...)` | `list[str]` | 多策略下载链接提取 (css/js/semantic/auto) |
| `discover_elements(page, tags, scope)` | `list[dict]` | 元素发现+选择器唯一性评级（步骤 3 核心工具） |
| `click_with_offset(page, selector)` | `bool` | 被遮挡时 CDP 偏移重试点击 |
| `schedule_run(script_path, ...)` | `str` | 生成定时配置 (cron/daemon) |
| `is_stable_class(class_name)` | `bool` | 判断 class 是否非框架生成 |
| `filter_stable_classes(class_list)` | `list[str]` | 过滤框架生成的 class |

⚠️ **只使用以上函数** — 不要调用 pw-kit 中不存在的函数。

---

## 规则速查

| 场景 | 做法 | 页面验证 |
|---|---|---|
| 定位元素 | 按决策树选最高优先级 | discover_elements 确认 |
| 等待条件 | expect 断言 | 页面确认等待目标出现 |
| 不确定等待什么 | **问用户**，列出选项 | 列出页面实际变化 |
| 遍历元素 | .all() + for | 确认实际数量 |
| 条件分支 | if/else | 确认分支存在 |
| 下载链接 | pw_kit.extract_download_urls() | 先确认有下载链接 |
| 遮挡点击 | pw_kit.click_with_offset() | 步骤 2 确认是遮挡 |
| 轮询等待 | while + wait_for_timeout | 确认目标会变化 |
| 容错 | try/except + screenshot | 步骤 2 提供失败场景 |
| 脚本验证 | python3 my_script.py | 步骤 2 必做 |