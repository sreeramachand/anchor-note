"""
pypi_tool package shim.

This package is a tiny wrapper used for `python -m pypi_tool` (or can be installed as
the project's module entrypoint). It intentionally keeps almost no logic here,
delegating to the real implementation in `anchor_note.platform.cli`.
"""

__all__ = ["__version__"]
__version__ = "0.1.0"
