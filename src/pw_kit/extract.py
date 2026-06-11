"""Download URL extraction and semantic keyword search for Playwright pages.

Provides the core download extraction function that supplements Playwright:
- extract_download_urls: Multi-strategy download link extraction (css/js/semantic/auto)

Internal helpers:
- find_by_semantic_keywords: Accessibility-tree-based semantic element search (used by semantic strategy)
"""

import re
from typing import Any, Optional, List, Dict

from playwright.sync_api import Page

from .utils import is_download_url, deduplicate_urls

DEFAULT_KEYWORDS = ["下载", "download", "file", "附件"]


def _extract_css(page: Page, selector: Optional[str], scope: Optional[str]) -> List[str]:
    scope_prefix = f"{scope} " if scope else ""
    if selector:
        full_selector = f"{scope_prefix}{selector} a"
    else:
        full_selector = f"{scope_prefix}a"

    try:
        locator = page.locator(full_selector)
        count = locator.count()
        urls = []
        for i in range(count):
            href = locator.nth(i).get_attribute("href")
            if href and is_download_url(href):
                urls.append(href)
        return urls
    except Exception:
        return []


def _extract_js(page: Page, expr: Optional[str]) -> List[str]:
    if not expr:
        return []
    try:
        result = page.evaluate(expr)
        if result is None:
            return []
        if isinstance(result, str):
            return [result] if result else []
        if isinstance(result, list):
            return [u for u in result if isinstance(u, str) and u]
        return []
    except Exception:
        return []


def _extract_semantic(page: Page, keywords: Optional[List[str]]) -> List[str]:
    kws = keywords or DEFAULT_KEYWORDS
    urls = []

    # --- Part (a): Accessibility tree walk ---
    try:
        snapshot = page.accessibility.snapshot()
        a11y_urls = _walk_a11y_for_urls(snapshot, kws)
        urls.extend(a11y_urls)
    except Exception:
        pass

    # --- Part (b): JS keyword-proximity URL scan ---
    try:
        js_urls = _js_keyword_url_scan(page, kws)
        urls.extend(js_urls)
    except Exception:
        pass

    return urls


def _walk_a11y_for_urls(node: Optional[Dict[str, Any]], keywords: List[str]) -> List[str]:
    """Recursively walk the accessibility tree, collecting URLs from link nodes
    whose name contains any keyword."""
    if node is None:
        return []

    urls = []
    name = node.get("name", "")
    role = node.get("role", "")

    if role == "link":
        url_val = node.get("url", "")
        if url_val and is_download_url(url_val):
            urls.append(url_val)
        elif url_val and any(kw.lower() in name.lower() for kw in keywords):
            urls.append(url_val)

    if any(kw.lower() in name.lower() for kw in keywords) and role != "link":
        # Keyword match on non-link node — check children for links
        for child in node.get("children", []) or []:
            child_role = child.get("role", "")
            child_url = child.get("url", "")
            if child_role == "link" and child_url:
                urls.append(child_url)

    for child in node.get("children", []) or []:
        urls.extend(_walk_a11y_for_urls(child, keywords))

    return urls


def _js_keyword_url_scan(page: Page, keywords: List[str]) -> List[str]:
    js_expr = """
    (() => {
        const keywords = %s;
        const urlRe = /https?:\\/\\/[^\\s<"']+\\/[^\\s<"']*\\.(pdf|zip|rar|tar|gz|doc|xls|ppt|7z|exe|msi|dmg|pkg|iso)/gi;
        const genericUrlRe = /https?:\\/\\/[^\\s<"']+/gi;
        const results = new Set();

        // 1. Find <a> elements whose text or href contains keywords
        const links = document.querySelectorAll('a[href]');
        for (const a of links) {
            const text = (a.textContent || '').toLowerCase();
            const href = (a.href || '').toLowerCase();
            for (const kw of keywords) {
                if (text.includes(kw.toLowerCase()) || href.includes(kw.toLowerCase())) {
                    if (a.href) results.add(a.href);
                    break;
                }
            }
        }

        // 2. Scan visible text for URLs near keyword matches
        const bodyText = document.body.innerText || '';
        const lines = bodyText.split('\\n');
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].toLowerCase();
            for (const kw of keywords) {
                if (line.includes(kw.toLowerCase())) {
                    // Extract URLs from this line and nearby lines
                    const context = (lines[i - 1] || '') + ' ' + lines[i] + ' ' + (lines[i + 1] || '');
                    const found = context.match(genericUrlRe);
                    if (found) {
                        for (const url of found) {
                            results.add(url);
                        }
                    }
                    break;
                }
            }
        }

        return JSON.stringify([...results]);
    })()
    """ % re.sub(
        r"'", r"\\'", str(keywords)
    ).replace("[", "[").replace("]", "]")

    try:
        raw = page.evaluate(js_expr)
        if raw is None:
            return []
        if isinstance(raw, list):
            return [u for u in raw if isinstance(u, str)]
        if isinstance(raw, str):
            # The JS returns JSON.stringify result, but Playwright may parse it
            import json
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [u for u in parsed if isinstance(u, str)]
            except (json.JSONDecodeError, TypeError):
                pass
            return [raw] if raw else []
        return []
    except Exception:
        return []


def extract_download_urls(
    page: Page,
    strategy: str = "auto",
    selector: Optional[str] = None,
    expr: Optional[str] = None,
    scope: Optional[str] = None,
    keywords: Optional[List[str]] = None,
) -> List[str]:
    """Extract downloadable URLs from a Playwright page using multiple strategies.

    Strategies:
        css      — Find <a> elements via CSS selector, filter by file extension/download keyword.
        js       — Evaluate a JS expression that returns URL(s).
        semantic — Accessibility tree walk + JS keyword-proximity URL scan.
        auto     — Try css → js → semantic, return first non-empty result.

    Args:
        page:       Playwright sync_api Page object.
        strategy:   Extraction strategy ("css" | "js" | "semantic" | "auto").
        selector:   CSS selector for <a> elements (css strategy).
        expr:       JS expression returning URL(s) (js strategy).
        scope:      CSS selector to limit search range (prepended to all CSS queries).
        keywords:   Search keywords for semantic strategy (default: ["下载","download","file","附件"]).

    Returns:
        List of deduplicated absolute URLs. Empty list on any error.
    """
    try:
        if strategy == "css":
            urls = _extract_css(page, selector, scope)
            return deduplicate_urls(urls)

        if strategy == "js":
            urls = _extract_js(page, expr)
            return deduplicate_urls(urls)

        if strategy == "semantic":
            urls = _extract_semantic(page, keywords)
            return deduplicate_urls(urls)

        # strategy == "auto"
        # Try css first if selector or scope is provided
        if selector or scope:
            urls = _extract_css(page, selector, scope)
            if urls:
                return deduplicate_urls(urls)

        # Try js if expr is provided
        if expr:
            urls = _extract_js(page, expr)
            if urls:
                return deduplicate_urls(urls)

        # Fall back to semantic
        urls = _extract_semantic(page, keywords)
        return deduplicate_urls(urls)

    except Exception:
        return []


def _walk_a11y_nodes(
    node: Optional[Dict[str, Any]],
    keywords: List[str],
    results: List[Dict[str, Any]],
) -> None:
    """Recursively walk the accessibility tree, collecting nodes whose name
    contains any keyword."""
    if node is None:
        return

    name = node.get("name", "")
    role = node.get("role", "")

    if name and any(kw.lower() in name.lower() for kw in keywords):
        url = None
        if role == "link":
            url = node.get("url", "")
        entry = {
            "role": role or "",
            "name": name,
            "url": url,
            "node": node,
        }
        results.append(entry)

    for child in node.get("children", []) or []:
        _walk_a11y_nodes(child, keywords, results)


def find_by_semantic_keywords(
    page: Page,
    keywords: Optional[List[str]] = None,
    scope: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Find page elements by semantic keywords using the accessibility tree.

    Walks the accessibility snapshot recursively, matching nodes whose ``name``
    contains any keyword. Returns structured info for each match including
    role, name, URL (for links), and the raw node dict.

    Args:
        page:     Playwright sync_api Page object.
        keywords: Search keywords (default: ["下载", "download"]).
        scope:    CSS selector to limit search range. When provided, also runs
                  a scoped JS scan to find elements within that container.

    Returns:
        List of dicts: ``[{"role": str, "name": str, "url": str|None, "node": dict}]``
        Empty list on errors or no matches.
    """
    kws = keywords or ["下载", "download"]

    try:
        snapshot = page.accessibility.snapshot()
        if snapshot is None:
            return []

        results: List[Dict[str, Any]] = []
        _walk_a11y_nodes(snapshot, kws, results)

        # If scope is provided, also try a scoped JS scan for additional matches
        if scope:
            try:
                scoped = _scoped_js_scan(page, scope, kws)
                # Merge scoped results, deduplicate by (role, name) combo
                existing_keys = {(r["role"], r["name"]) for r in results}
                for s in scoped:
                    key = (s["role"], s["name"])
                    if key not in existing_keys:
                        results.append(s)
                        existing_keys.add(key)
            except Exception:
                pass

        return results

    except Exception:
        return []


def _scoped_js_scan(
    page: Page,
    scope: str,
    keywords: List[str],
) -> List[Dict[str, Any]]:
    js_expr = """
    (() => {
        const scope = %s;
        const keywords = %s;
        const root = document.querySelector(scope);
        if (!root) return JSON.stringify([]);

        const results = [];
        const els = root.querySelectorAll('a[href], button, [role="button"], [role="link"]');
        for (const el of els) {
            const text = (el.textContent || '').trim();
            const lowerText = text.toLowerCase();
            for (const kw of keywords) {
                if (lowerText.includes(kw.toLowerCase())) {
                    const role = el.getAttribute('role') || el.tagName.toLowerCase();
                    const url = el.getAttribute('href') || el.href || null;
                    results.push({
                        role: role,
                        name: text.substring(0, 200),
                        url: url,
                        node: {role: role, name: text.substring(0, 200)}
                    });
                    break;
                }
            }
        }
        return JSON.stringify(results);
    })()
    """ % (_js_str_escape(scope), _js_str_escape(keywords))

    try:
        raw = page.evaluate(js_expr)
        if raw is None:
            return []
        import json
        if isinstance(raw, str):
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [d for d in parsed if isinstance(d, dict)]
        if isinstance(raw, list):
            return [d for d in raw if isinstance(d, dict)]
        return []
    except Exception:
        return []


def _js_str_escape(value: Any) -> str:
    import json
    return json.dumps(value)