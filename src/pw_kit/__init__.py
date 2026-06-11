"""pw-kit: Playwright developer toolkit.

Supplements Playwright with functions for semantic download extraction,
element discovery with uniqueness ratings, occlusion offset click retry,
framework class filtering, and scheduling.

Only wraps what Playwright truly lacks — use Playwright's built-in API
for everything else (navigation, clicks, waits, assertions, etc.).

Usage:
    from pw_kit import (
        extract_download_urls,
        discover_elements,
        click_with_offset,
        schedule_run,
        is_stable_class,
        filter_stable_classes,
    )
"""

from .extract import extract_download_urls
from .discover import discover_elements
from .offset import click_with_offset
from .schedule import schedule_run
from .filters import is_stable_class, filter_stable_classes, FRAMEWORK_CLASS_PATTERN

__all__ = [
    "extract_download_urls",
    "discover_elements",
    "click_with_offset",
    "schedule_run",
    "is_stable_class",
    "filter_stable_classes",
    "FRAMEWORK_CLASS_PATTERN",
]

__version__ = "0.1.0"