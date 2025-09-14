"""Simple logging configuration helper"""

import logging
import sys

def configure_logging(level=logging.INFO):
    root = logging.getLogger()
    if root.handlers:
        return
    fmt = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter(fmt))
    root.addHandler(h)
    root.setLevel(level)
