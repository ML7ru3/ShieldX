import logging

from config.logging_config import configure_logging
from agent_scheduler import main as start_scheduler

logger = logging.getLogger(__name__)


def main():
    configure_logging()
    logger.info("ShieldX Agent starting...")
    start_scheduler()


if __name__ == "__main__":
    main()
