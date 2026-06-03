import pandas as pd
import logging
from config.logging_config import configure_logging
from domains.system_info import collect_system_info


logger = logging.getLogger(__name__)

import subprocess


def initialize():
    configure_logging()
    logger.info("SHIELDX AGENT INITIALIZING")
    # Block well-known DoH providers at startup
    # try:
    #     subprocess.call(["./src/scripts/block_doh.sh"])
    # except Exception as exc:
    #     logger.warning(f"DoH block script failed: {exc}")
    # print(collect_system_info())


def main() -> None:
    initialize()
    # Load the file back to inspect it
    df = pd.read_parquet("./datasets/L2-BenignDoH-MaliciousDoH.parquet")

    print(df.head())
    print(df.info())
    
    


if __name__ == "__main__":
    main()
