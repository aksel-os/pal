#!/usr/bin/env python3
import logging
from time import sleep
from src.pal import Pal
from src.discord_utils import post_all_events


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s: %(message)s")
    logger = logging.getLogger("pal")

    pal = Pal("./data/indexed_events", logger)

    while True:
        new_events = pal.get_new_public_events()

        if not new_events:
            logger.info("No new events")

        else:
            post_all_events(new_events)
            pal.persist_index()

        sleep(60)


if __name__ == "__main__":
    main()
