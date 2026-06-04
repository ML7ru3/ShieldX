import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from pipeline import load_model, capture_and_predict

logger = logging.getLogger(__name__)


def scheduled_task():
    logger.info("=== Scheduled pipeline run started ===")
    try:
        results = capture_and_predict(interface='ens33', sniff_duration=120)
        malicious = sum(1 for _, pred in results if pred == 1)
        logger.info(
            "=== Pipeline finished: %d flows, %d malicious ===",
            len(results), malicious,
        )
    except Exception as exc:
        logger.error("Pipeline failed: %s", exc, exc_info=True)


def main():
    load_model()
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_task, 'interval', minutes=2)
    scheduler.start()
    logger.info("Scheduler started (interval=1 minutes)")

    try:
        while True:
            time.sleep(10)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down scheduler...")
        scheduler.shutdown()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
