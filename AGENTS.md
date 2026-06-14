# AGENTS.md — pw-kit

## Project identity

pw-kit is a Playwright developer toolkit: **Python library + opencode Skill**. Two components in one repo:

- `src/pw_kit/` — Python library (install via `pip install -e .`)
- `skills/pw-automator/` — opencode Skill (copy to `~/.config/opencode/skills/`)

Core principle: **only supplement what Playwright lacks.** Never wrap Playwright's built-in navigation, clicks, waits, assertions, or screenshots.

## Setup (two-step, mandatory)

```bash
pip install -e .          # Step 1: Python package (dev mode, run in project root)
pw-kit-install            # Step 2: Chromium browser (~150MB, must install)
```

Missing step 2 causes `Executable doesn't exist` or `Browser closed unexpectedly`.

- Linux: also run `playwright install-deps chromium`
- macOS Gatekeeper blocking: `xattr -d com.apple.quarantine ~/Library/Caches/ms-playwright/chromium-*/chrome-mac/Chromium.app`
- daemon mode needs `pip install -e ".[schedule]"`

## Dev commands

```bash
pip install -e ".[dev]"   # Install pytest + pytest-playwright
pytest                    # Run tests (but see Testing section below)
pw-kit-install            # Re-install browsers if needed
python3 -m playwright codegen <url>   # Record a script
```

No linter, formatter, type checker, or CI is configured.

## Public API (6 functions + 1 constant)

All exported from `src/pw_kit/__init__.py` via `__all__`:

| Export | Module | Returns on success | Returns on error |
|---|---|---|---|
| `extract_download_urls` | `extract.py` | `list[str]` | `[]` |
| `discover_elements` | `discover.py` | `list[dict]` | `[]` |
| `click_with_offset` | `offset.py` | `True` | `False` |
| `schedule_run` | `schedule.py` | `str` (config text) | raises ValueError/ImportError |
| `is_stable_class` | `filters.py` | `bool` | — |
| `filter_stable_classes` | `filters.py` | `list[str]` | — |
| `FRAMEWORK_CLASS_PATTERN` | `filters.py` | compiled regex | — |

**Error convention**: All functions that accept a Playwright `Page` return empty/False on errors rather than raising. Only `schedule_run` raises for invalid inputs.

## Architecture

### Source layout (`src/pw_kit/`)

- `__init__.py` — Package entry, exports all public functions via `__all__`
- `extract.py` — Multi-strategy download URL extraction (css/js/semantic/auto). Contains `find_by_semantic_keywords` (not in `__all__`, used internally by semantic strategy)
- `discover.py` — Element discovery with selector uniqueness ratings. Injects JS (`_PROPS_JS`, `_NTH_PATH_JS`) via `page.evaluate()`
- `offset.py` — CDP-based occluded element clicking. Opens a CDP session (`page.context.new_cdp_session(page)`), always detaches in `finally`
- `filters.py` — Framework class filtering. `FRAMEWORK_CLASS_PATTERN` matches `devui|ng-|cdk|mat-|Mui|ant-|el-|v-|cdk` prefixes
- `schedule.py` — Generates cron/daemon config strings. **Does not execute scheduling itself**. `daemon` mode requires `schedule` pip package
- `utils.py` — URL detection (`is_download_url`) and deduplication (`deduplicate_urls`). Shared by `extract.py`
- `_install.py` — CLI entry point for `pw-kit-install` command. Runs `playwright install chromium`

### JS injection pattern

Multiple modules embed JS strings and evaluate them via `page.evaluate()`:
- `discover.py`: `_PROPS_JS`, `_NTH_PATH_JS`
- `offset.py`: `_JS_FIND_CENTER`
- `extract.py`: `_js_keyword_url_scan`, `_scoped_js_scan`

When writing new extraction/discovery features, follow this pattern: embed JS as a module-level constant string, escape selector/parameter injection via `json.dumps()`.

### sync_api only

pw-kit exclusively uses `playwright.sync_api`. No async support. All public functions take a `sync_api.Page` object.

## Testing

**Important mismatch**: `pyproject.toml` declares `testpaths = ["tests"]`, but the actual directory is `test/` (no `s`). This means `pytest` will find no tests by default.

- `test/my_scripts.py` — Manual Playwright script (not a pytest test), runs via `python3 test/my_scripts.py`
- `test/scripts.py` — Empty file
- No pytest test suite exists yet. The `dev` optional dependency includes `pytest` and `pytest-playwright`, but no `tests/` directory or test files conform to pytest conventions.

To run the manual script:
```bash
python3 test/my_scripts.py
```

## Conventions

- **Language**: Documentation, comments, and UI-facing strings are in **Chinese (中文)**. Maintain this for new docs, comments, and user-facing output.
- **Error handling**: Return empty/False, don't raise (except `schedule_run` for invalid args).
- **Type annotations**: Mixed style — some files use `Optional[List[str]]` (typing module), others use `str | None` (3.10+ syntax). Python 3.8 is the declared minimum, so `str | None` is technically incompatible.
- **No new Playwright wrappers**: Before adding a function, verify Playwright doesn't already provide it. Check [Playwright Python API 文档](https://playwright.net.cn/python/docs/api/class-playwright)
- **Private helpers**: Prefix with `_`. Not exported via `__all__`.
- **Download detection**: File extensions and keyword regexes live in `utils.py`. Extend there, not in individual modules.

## Skill directory (`skills/pw-automator/`)

This is an opencode Skill, NOT part of the Python library. Structure:

```
skills/pw-automator/
├── SKILL.md                          # Skill definition (132 lines, 7-step workflow overview)
├── references/
│   ├── workflow-detail.md            # Detailed Step 2-6 instructions + wait operation triggers
│   ├── patterns.md                   # 5 script-analysis patterns + 1 user-request add-on (scheduled run)
│   ├── locators.md                    # Playwright element locating guide (copied from docs/LOCATORS.md)
│   └── playwright-api.md            # Playwright API quick reference
└── templates/                        # 6 automation task templates
    ├── page_analyze.py               # Step 3: multi-stage page analysis (includes wait awareness)
    ├── simple_download.py
    ├── iterate_table.py
    ├── branch_download.py
    ├── loop_progress.py
    └── scheduled_run.py
```

Templates are standalone scripts that users copy into their projects. Each has a header comment describing its use case. They import from `pw_kit`, so the library must be installed first.

The pw-automator workflow now has 7 steps: receive script → **execute validation** → **page analysis** → risk marking → ask user → suggest replacements → generate final script. Steps 2 and 3 are mandatory — the Skill must verify the codegen script can run and must analyze the target webpage before suggesting optimizations.

Step 3 (page analysis) is **multi-stage**: for each `page.goto()` in the script, create a new scan stage; for each click/fill that changes the DOM (without changing URL), create a sub-stage; for each `wait_for_timeout`/`wait_for_load_state`/`wait_for_url`/`wait_for_selector`/`wait_for_function`, create a sub-stage after the wait completes. This captures URL navigation, in-page DOM mutations (AJAX, SPA), and post-wait DOM changes.

## Things agents often miss

- **Two-step install is mandatory** — `pip install -e .` alone won't work; browsers must be installed separately
- **`test/` vs `tests/` mismatch** — pytest won't find tests unless you fix `testpaths` in pyproject.toml or pass the path explicitly (`pytest test/`)
- **`schedule_run` does NOT execute scheduling** — it only generates config strings. Don't confuse it with an actual scheduler
- **`schedule_run` is NOT discoverable from script analysis** — codegen only records browser interactions, no "schedule" signals exist in codegen scripts. Only suggest `schedule_run` when the user explicitly requests scheduled/periodic execution
- **CDP session lifecycle** — `offset.py` opens CDP sessions and detaches in `finally`. Any new CDP usage must follow this pattern
- **`find_by_semantic_keywords` is internal** — not in `__all__`, don't expose it as public API
- **`FRAMEWORK_CLASS_PATTERN` is exported** — it IS in `__all__`, agents can use it directly
- **daemon mode needs extra install** — `pip install pw-kit[schedule]` or `pip install -e ".[schedule]"`
- **pw-automator must verify script execution** — Step 2: run the codegen script first, see if it works. If not, analyze the failure before optimizing
- **pw-automator must analyze the target webpage** — Step 3: use `discover_elements()` and `extract_download_urls()` to see what's actually on the page. Optimizations without page data may suggest elements/text that don't exist
- **Cannot guess wait conditions** — if `wait_for_timeout` appears and page data isn't available, must ask the user what to wait for, not guess
- **Wait operations also trigger page structure changes** — `wait_for_timeout`/`wait_for_load_state`/`wait_for_url`/`wait_for_selector`/`wait_for_function` all mean the page is changing. After each wait completes, scan the page again — DOM may have updated during the wait
- **SKILL.md uses progressive disclosure** — core workflow stays in SKILL.md (~132 lines), detailed step instructions and pattern library moved to `references/workflow-detail.md` and `references/patterns.md`. SKILL.md points to these files at the relevant steps
- **Playwright MCP cannot call pw-kit functions** — MCP only provides `browser_snapshot` (accessibility tree), not `discover_elements()` or `extract_download_urls()` (which need JS injection + multi-strategy scanning). Step 3 方式 B uses pw-kit CLI (bash execute Python scripts) as primary approach, MCP as optional supplementary