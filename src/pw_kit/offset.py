"""Click elements that may be occluded by overlays, using CDP offset clicks."""

import json
from typing import Any

from playwright.sync_api import Page, TimeoutError


_JS_FIND_CENTER = """
(() => {
  const el = document.querySelector(%s);
  if (!el) return JSON.stringify({error: 'not found'});
  el.scrollIntoView({block: 'center', behavior: 'instant'});
  const rect = el.getBoundingClientRect();
  const cx = Math.round(rect.x + rect.width / 2);
  const cy = Math.round(rect.y + rect.height / 2);
  const hitEl = document.elementFromPoint(cx, cy);
  const isTarget = (hitEl === el || el.contains(hitEl));
  let offsetY = 0;
  let oh = 0;
  if (!isTarget && hitEl) {
    oh = Math.round(hitEl.getBoundingClientRect().height);
    offsetY = cy - oh - 10;
    const hitAfter = document.elementFromPoint(cx, offsetY);
    if (!(hitAfter === el || el.contains(hitAfter))) offsetY = 0;
  }
  return JSON.stringify({
    x: cx, y: cy, isTarget,
    offsetY: offsetY > 0 ? offsetY : cy,
    occluderHeight: oh || 0
  });
})()
"""


def _cdp_click(cdp: Any, x: int, y: int) -> None:
    """Dispatch a left-button click at (x, y) via CDP Input events."""
    for evt_type in ("mousePressed", "mouseReleased"):
        cdp.send("Input.dispatchMouseEvent", {
            "type": evt_type,
            "x": x,
            "y": y,
            "button": "left",
            "clickCount": 1,
        })


def click_with_offset(
    page: Page,
    selector: str,
    max_retries: int = 3,
) -> bool:
    """Click an element, retrying with offset if occluded by an overlay.

    First attempts a normal Playwright click.  If that times out (likely
    due to occlusion), opens a CDP session to compute the element center
    and check what element actually receives the hit.  When an occluder
    is found, clicks at an adjusted Y offset above the occluder.

    Args:
        page: Playwright sync_api Page object.
        selector: CSS selector string.
        max_retries: Maximum retry attempts if offset click also fails.

    Returns:
        True if the click succeeded, False after all retries exhausted.
    """
    locator = page.locator(selector)

    # Try normal Playwright click first.
    try:
        locator.click(timeout=5000)
        return True
    except TimeoutError:
        pass  # Likely occluded — fall through to offset retry.

    # Build JS with safely escaped selector.
    js_selector = json.dumps(selector)
    js_expr = _JS_FIND_CENTER % js_selector

    cdp = page.context.new_cdp_session(page)
    try:
        for attempt in range(max_retries):
            result_raw = page.evaluate(js_expr)
            result = json.loads(result_raw) if isinstance(result_raw, str) else result_raw

            if result.get("error") == "not found":
                return False

            cx, cy = result["x"], result["y"]
            is_target = result["isTarget"]
            offset_y = result["offsetY"]

            # Slight jitter on retries > 0 to vary the hit point.
            if attempt > 0:
                offset_y -= attempt * 2

            click_y = cy if is_target else offset_y
            if click_y <= 0:
                continue

            _cdp_click(cdp, cx, click_y)
            return True
    finally:
        cdp.detach()

    return False