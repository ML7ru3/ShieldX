import logging

from config.logging_config import configure_logging
from agent_orchestrator import main as start_agent
from domains.firewall import FirewallManager

logger = logging.getLogger(__name__)


def main():
    configure_logging()
    logger.info("ShieldX Agent starting...")
    start_agent()


    # FOR TESTING FIREWALL MANAGER
    # Besure you enter the frontend and backend of the server.
    # firewall_mananger = FirewallManager()
    #
    # firewall_mananger.apply_whitelist([
    #     "facebook.com",
    # ])


if __name__ == "__main__":
    main()
