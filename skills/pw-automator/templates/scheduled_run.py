"""Scheduled run: execute a script on a schedule using cron or daemon.

Two modes:
- cron: generates a crontab entry (recommended for servers)
- daemon: generates a Python daemon script (for simple setups)
"""

from pw_kit import schedule_run


def setup_cron():
    # Generate crontab entry for daily 09:00 execution
    result = schedule_run(
        script_path="my_download_script.py",
        time="09:00",
        mode="cron",
    )
    print(result)
    # Output:
    # Crontab entry:
    # 0 9 * * * cd /path/to/project && python /path/to/my_download_script.py >> ~/logs/pw-kit-my_download_script.log 2>&1
    #
    # To install, run:
    #   crontab -e
    # Then append the line above and save.


def setup_daemon():
    # Generate a Python daemon script
    result = schedule_run(
        script_path="my_download_script.py",
        time="09:00",
        mode="daemon",
    )
    print(result)
    # Output includes the full daemon script + instructions:
    # Foreground:  python ~/.pw-kit/daemon-my_download_script.py
    # Background:  nohup python ~/.pw-kit/daemon-my_download_script.py &


if __name__ == "__main__":
    setup_cron()