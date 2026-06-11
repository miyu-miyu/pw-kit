"""Filter out framework-generated CSS class names that change across builds."""

import re

FRAMEWORK_CLASS_PATTERN = re.compile(
    r"^(devui|ng-|cdk|mat-|Mui|ant-|el-|v-|cdk)",
    re.IGNORECASE,
)


def is_stable_class(class_name: str) -> bool:
    """Return True if *class_name* is NOT a framework-generated class.

    Framework prefixes like ``Mui-``, ``ant-``, ``ng-`` etc. produce
    class names that vary between builds and are unreliable for selectors.
    """
    return not FRAMEWORK_CLASS_PATTERN.match(class_name)


def filter_stable_classes(class_list: list[str]) -> list[str]:
    """Remove framework-generated classes from *class_list*, preserving order."""
    return [c for c in class_list if is_stable_class(c)]