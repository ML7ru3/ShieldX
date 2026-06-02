import logging
import pandas as pd
from config.logging_config import configure_logging
from domains.system_info import collect_system_info


logger = logging.getLogger(__name__)

def main() -> None:
    configure_logging()
    logger.info("SHIELDX AGENT INITIALIZING")
    print(collect_system_info())
    
    df = pd.read_parquet("datasets/L2-BenignDoH-MaliciousDoH.parquet")
    print("Columns:", df.columns.tolist())
    print("Info:")
    print(df.info())
    print(df.head())


if __name__ == "__main__":
    main()
