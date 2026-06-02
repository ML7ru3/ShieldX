import logging
import sys


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logger; safe to call multiple times."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )
