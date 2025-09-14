"""CLI entrypoint used by console_scripts"""

import argparse
import sys
from ..core.settings import load_user_config
from ..core.scheduler import Scheduler

def main(argv=None):
    parser = argparse.ArgumentParser(prog="sticky-remind")
    parser.add_argument("--foreground", action="store_true", help="Run scheduler in foreground")
    parser.add_argument("--gui", action="store_true", help="Start GUI agent (if available)")
    parser.add_argument("--sync-ics", help="Sync an .ics file immediately")
    args = parser.parse_args(argv or sys.argv[1:])

    sched = Scheduler()
    if args.sync_ics:
        from ..core.calendar_sync import sync_from_ics
        sync_from_ics(args.sync_ics)
        print("ICS sync requested.")
        return

    if args.gui:
        try:
            from .gui_agent import main as gui_main
            gui_main()
            return
        except Exception as e:
            print("Failed launching GUI agent:", e)

    if args.foreground:
        sched.start()
        print("Scheduler running in foreground. Ctrl+C to stop.")
        try:
            while True:
                pass
        except KeyboardInterrupt:
            sched.stop()
    else:
        # default to foreground for simplicity
        sched.start()
        print("Scheduler running in foreground (default). Ctrl+C to stop.")
        try:
            while True:
                pass
        except KeyboardInterrupt:
            sched.stop()
