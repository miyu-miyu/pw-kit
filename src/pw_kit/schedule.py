"""Generate scheduling configuration for running Playwright scripts on a schedule."""

import os
import re
from pathlib import Path


_TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def _validate_time(time: str) -> tuple[str, str]:
    """Parse and validate a 24-hour HH:MM time string."""
    if not _TIME_RE.match(time):
        raise ValueError(f"Invalid time format '{time}'; expected HH:MM in 24-hour range.")
    hours, minutes = time.split(":")
    return hours, minutes


def _default_log_path(script_path: str) -> str:
    basename = Path(script_path).stem
    return str(Path.home() / "logs" / f"pw-kit-{basename}.log")


def schedule_run(
    script_path: str,
    time: str = "09:00",
    mode: str = "cron",
    log_path: str | None = None,
) -> str:
    """Generate a scheduling configuration for *script_path*.

    Args:
        script_path: Python script path to execute.
        time: Execution time in 24h format (HH:MM).
        mode: ``"cron"`` generates a crontab entry string;
              ``"daemon"`` generates a Python daemon script.
        log_path: Log file path. Defaults to ``~/logs/pw-kit-<name>.log``.

    Returns:
        A string containing the crontab line or daemon script,
        plus instructions for how to activate it.
    """
    hours, minutes = _validate_time(time)
    if log_path is None:
        log_path = _default_log_path(script_path)

    script_dir = str(Path(script_path).resolve().parent)
    script_abs = str(Path(script_path).resolve())

    if mode == "cron":
        cron_line = f"{minutes} {hours} * * * cd {script_dir} && python {script_abs} >> {log_path} 2>&1"
        return (
            f"Crontab entry:\n{cron_line}\n\n"
            f"To install, run:\n  crontab -e\n"
            f"Then append the line above and save."
        )

    if mode == "daemon":
        try:
            import schedule  # noqa: F401 — presence check only
        except ImportError:
            raise ImportError("Install schedule: pip install schedule")

        daemon_script = f'''\
import schedule
import subprocess
import sys
import time

SCRIPT = "{script_abs}"
LOG = "{log_path}"

def run_script():
    with open(LOG, "a") as log:
        subprocess.run([sys.executable, SCRIPT], stdout=log, stderr=subprocess.STDOUT)

schedule.every().day.at("{time}").do(run_script)

print(f"Daemon scheduled: {SCRIPT} at {time} daily")
while True:
    schedule.run_pending()
    time.sleep(60)
'''
        daemon_path = str(Path.home() / ".pw-kit" / f"daemon-{Path(script_path).stem}.py")
        instructions = (
            f"Daemon script (save to {daemon_path}):\n\n{daemon_script}\n\n"
            f"Foreground:  python {daemon_path}\n"
            f"Background:  nohup python {daemon_path} &"
        )
        return instructions

    raise ValueError(f"Unknown mode '{mode}'; choose 'cron' or 'daemon'.")