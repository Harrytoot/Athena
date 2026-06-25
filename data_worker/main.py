import logging
import signal
import sys

from data_worker.config import LOG_LEVEL
from data_worker.scheduler import build_scheduler

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("data_worker")


def main():
    logger.info("Starting Athena Data Worker...")
    scheduler = build_scheduler()
    scheduler.start()

    def shutdown(signum, frame):
        logger.info("Shutting down...")
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    try:
        while True:
            signal.pause()
    except (KeyboardInterrupt, SystemExit):
        shutdown(None, None)


if __name__ == "__main__":
    main()
