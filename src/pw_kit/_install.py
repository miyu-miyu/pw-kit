"""pw-kit post-install helper — install Playwright browsers.

Run via: pw-kit-install
Or: python -m pw_kit._install

This installs the Playwright browser binaries that pw-kit depends on.
pip install pw-kit only installs the Python package; browser binaries
must be installed separately via `playwright install`.
"""

import subprocess
import sys


def main():
    print("pw-kit: Installing Playwright browser binaries...")
    print("  (This is required — pw-kit depends on Playwright browsers)")
    print()

    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("✓ Chromium installed successfully.")
            print()
            print("Verify: python -c \"from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(); print('OK'); b.close(); p.stop()\"")
        else:
            print(f"✗ Installation failed (exit code {result.returncode}):")
            print(result.stderr)
            print()
            print("Try manually: playwright install chromium")
            print("Or with deps: playwright install-deps chromium  (Linux only)")
            sys.exit(1)
    except FileNotFoundError:
        print("✗ playwright command not found.")
        print("  Make sure playwright is installed: pip install playwright")
        sys.exit(1)


if __name__ == "__main__":
    main()