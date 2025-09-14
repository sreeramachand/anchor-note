# main.py -- thin Kivy entry that delegates to anchor_note.platform.kivy_app
# Place in android/main.py

import sys
import os

# Ensure the parent repo root is on sys.path so "anchor_note" package is importable.
# When running in Buildozer, the project root is typically on sys.path already.
here = os.path.dirname(__file__)
if here not in sys.path:
    sys.path.insert(0, here)

# Delegates to the package's Kivy App
try:
    from anchor_note.platform.kivy_app import main as run_app
except Exception as exc:
    # Show helpful error message in case of import failure
    import traceback
    print("Failed to import anchor_note.platform.kivy_app:", exc)
    traceback.print_exc()
    raise

if __name__ == "__main__":
    run_app()
