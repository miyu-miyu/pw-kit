"""Shared URL helpers for detecting download links and deduplicating URLs."""

import re

DOWNLOAD_URL_EXTENSIONS = re.compile(
    r"\.(pdf|zip|rar|tar|gz|bz2|7z|doc|docx|xls|xlsx|ppt|pptx|exe|msi|dmg|pkg|iso|csv|txt|rtf|odt|ods|odp)(\?|$)",
    re.IGNORECASE,
)

DOWNLOAD_URL_KEYWORDS = re.compile(r"(download|file|attachment|附件)", re.IGNORECASE)


def is_download_url(url: str) -> bool:
    """Check if *url* looks like a downloadable file link."""
    if not url:
        return False
    return bool(DOWNLOAD_URL_EXTENSIONS.search(url) or DOWNLOAD_URL_KEYWORDS.search(url))


def deduplicate_urls(urls: list[str]) -> list[str]:
    """Remove duplicate URLs from *urls* while preserving first-occurrence order."""
    seen: set[str] = set()
    result: list[str] = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            result.append(url)
    return result