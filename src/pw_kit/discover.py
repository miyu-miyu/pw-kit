"""Discover interactive elements on a page and generate selector candidates.

Scans a Playwright page for interactive elements (inputs, buttons, links, etc.)
and produces a ranked list of CSS selector candidates with uniqueness ratings.
Inspired by chrome-auto-fetch's Discovery mode, reimplemented with Playwright
locator API.
"""

from typing import Dict, List, Optional

from playwright.sync_api import Page

from .filters import is_stable_class

_DEFAULT_TAGS = ["input", "select", "button", "textarea", "a"]

# JS snippet executed inside the browser to extract element properties.
_PROPS_JS = """() => {
    const el = this;
    const rect = el.getBoundingClientRect();
    const text = (el.textContent || '').trim().slice(0, 80);
    const classes = Array.from(el.classList);
    return {
        tag: el.tagName.toLowerCase(),
        id: el.id || null,
        name: el.name || null,
        placeholder: el.placeholder || null,
        href: el.getAttribute('href') || null,
        aria_label: el.getAttribute('aria-label') || null,
        text: text,
        classes: classes,
        rect: { width: rect.width, height: rect.height, x: rect.x, y: rect.y },
        visible: rect.width > 0 && rect.height > 0 && !el.hidden,
        disabled: el.disabled,
    };
}"""

# JS snippet to compute the nth-child path from root to a given element.
_NTH_PATH_JS = """() => {
    const el = this;
    const parts = [];
    let node = el;
    while (node && node.parentElement) {
        const parent = node.parentElement;
        const siblings = Array.from(parent.children);
        const idx = siblings.indexOf(node) + 1;
        const sameTagSiblings = siblings.filter(s => s.tagName === node.tagName);
        if (sameTagSiblings.length > 1) {
            const tagIdx = sameTagSiblings.indexOf(node) + 1;
            parts.unshift(node.tagName.toLowerCase() + ':nth-of-type(' + tagIdx + ')');
        } else {
            parts.unshift(node.tagName.toLowerCase());
        }
        node = parent;
    }
    return parts.join(' > ');
}"""


def _verify_unique(page: Page, selector: str) -> bool:
    """Return True if *selector* matches exactly one element on the page."""
    try:
        return page.locator(selector).count() == 1
    except Exception:
        return False


def _build_candidates(
    page: Page,
    props: Dict,
    nth_path: str,
) -> List[Dict]:
    """Generate selector candidates ordered by priority.

    Each candidate dict has keys: selector, unique, type.
    """
    candidates: List[Dict] = []

    # 1. ID selector
    if props["id"]:
        sel = f"#{props['id']}"
        candidates.append({"selector": sel, "unique": _verify_unique(page, sel), "type": "id"})

    # 2. href selector (only for <a> elements)
    if props["tag"] == "a" and props["href"]:
        sel = f"a[href='{props['href']}']"
        candidates.append({"selector": sel, "unique": _verify_unique(page, sel), "type": "href"})

    # 3. aria-label selector
    if props["aria_label"]:
        sel = f"[aria-label='{props['aria_label']}']"
        candidates.append({"selector": sel, "unique": _verify_unique(page, sel), "type": "aria-label"})

    # 4. name selector
    if props["name"]:
        sel = f"[name='{props['name']}']"
        candidates.append({"selector": sel, "unique": _verify_unique(page, sel), "type": "name"})

    # 5. placeholder selector
    if props["placeholder"]:
        sel = f"[placeholder='{props['placeholder']}']"
        candidates.append({"selector": sel, "unique": _verify_unique(page, sel), "type": "placeholder"})

    # 6. Combined class selector (stable classes only)
    stable = [c for c in props["classes"] if is_stable_class(c)]
    if len(stable) >= 2:
        sel = "." + ".".join(stable)
        candidates.append({"selector": sel, "unique": _verify_unique(page, sel), "type": "class-combined"})

    # 7. Single class selector (stable classes only)
    for cls in stable:
        sel = f".{cls}"
        candidates.append({"selector": sel, "unique": _verify_unique(page, sel), "type": "class-single"})

    # 8. nth-child path (always unique but fragile)
    if nth_path:
        candidates.append({"selector": nth_path, "unique": True, "type": "nth-child"})

    return candidates


def discover_elements(
    page: Page,
    tags: Optional[List[str]] = None,
    scope: Optional[str] = None,
) -> List[Dict]:
    """Scan a Playwright page for interactive elements and generate selector candidates.

    Args:
        page: A Playwright ``sync_api.Page`` object.
        tags: List of HTML tag types to scan. Defaults to
              ``["input", "select", "button", "textarea", "a"]``.
        scope: CSS selector that limits the search to a subtree. When ``None``
               the entire page is scanned.

    Returns:
        A list of dicts describing each discovered element. Each dict contains
        the element's properties and a ranked list of selector candidates with
        uniqueness ratings. Elements that are invisible (zero-size or hidden)
        or disabled are excluded. Returns an empty list on errors.
    """
    if tags is None:
        tags = _DEFAULT_TAGS

    try:
        # Validate scope exists if provided.
        if scope and page.locator(scope).count() == 0:
            return []

        scope_sel = scope if scope else ""

        results: List[Dict] = []

        for tag in tags:
            # Build the locator: scoped or full-page.
            if scope_sel:
                locator = page.locator(f"{scope_sel} {tag}")
            else:
                locator = page.locator(tag)

            elements = locator.all()

            for element in elements:
                # Extract properties via in-browser JS evaluation.
                try:
                    props = element.evaluate(_PROPS_JS)
                except Exception:
                    continue

                # Skip invisible or disabled elements.
                if not props["visible"] or props["disabled"]:
                    continue

                # Compute nth-child path for fallback selector.
                try:
                    nth_path = element.evaluate(_NTH_PATH_JS)
                except Exception:
                    nth_path = ""

                # Generate selector candidates.
                candidates = _build_candidates(page, props, nth_path)

                # Pick the first unique selector as the suggestion.
                suggested = None
                for c in candidates:
                    if c["unique"]:
                        suggested = c["selector"]
                        break

                results.append({
                    "tag": props["tag"],
                    "id": props["id"],
                    "name": props["name"],
                    "placeholder": props["placeholder"],
                    "href": props["href"],
                    "aria_label": props["aria_label"],
                    "text": props["text"],
                    "classes": props["classes"],
                    "rect": props["rect"],
                    "visible": props["visible"],
                    "disabled": props["disabled"],
                    "selectors": candidates,
                    "suggested": suggested,
                })

        return results

    except Exception:
        return []