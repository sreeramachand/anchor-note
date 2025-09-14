"""Module entrypoint for the project.

When installed or present on PYTHONPATH you can run:

    python -m pypi_tool

This file delegates to the package CLI implementation at:
    anchor_note.platform.cli:main

If you prefer the module name `stickyremind` for `python -m`, you can create a
small package named `stickyremind` (or an alias package) that re-exports this
module. Alternatively, keep your `console_scripts` entry points in setup.cfg.
"""

from __future__ import annotations

import sys
import traceback

def main(argv: list[str] | None = None) -> int:
    """Run the project's CLI main. Returns an exit code (0 success)."""
    argv = argv if argv is not None else sys.argv[1:]
    try:
        # Import at runtime so this module can be imported on systems that don't
        # have all optional dependencies installed.
        from anchor_note.platform.cli import main as cli_main
    except Exception as exc:
        # Print a helpful error and exit non-zero so it's obvious in CI/terminals.
        print("Failed to import the anchor_note CLI entrypoint.", file=sys.stderr)
        print("Make sure you installed the package and its dependencies (pip install .).", file=sys.stderr)
        print("Import error:", file=sys.stderr)
        traceback.print_exception(exc, None, exc.__traceback__, file=sys.stderr)
        return 2

    # Delegate to the actual CLI main function. Many CLI mains accept argv parameter;
    # our anchor_note.platform.cli.main above accepts an argv optional arg.
    try:
        # If the underlying main expects argv, pass it. Otherwise it will ignore it.
        return cli_main(argv)
    except TypeError:
        # Fallback: underlying main may not accept an argv parameter.
        try:
            cli_main()
            return 0
        except SystemExit as se:
            return getattr(se, "code", 0) or 0
        except Exception:
            traceback.print_exc()
            return 1
    except SystemExit as se:
        return getattr(se, "code", 0) or 0
    except Exception:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
