import logging

from config.logging_config import configure_logging
from agent_orchestrator import main as start_agent

logger = logging.getLogger(__name__)


def main():
    configure_logging()
    logger.info("ShieldX Agent starting...")
    start_agent()


if __name__ == "__main__":
    main()
