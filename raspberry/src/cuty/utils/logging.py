"""Compact structured console logging."""

import logging


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(level=level, format="[%(name)s] %(message)s", force=True)
    for name in ("primp", "ddgs"):
        logging.getLogger(name).setLevel("DEBUG" if level == "DEBUG" else "WARNING")
