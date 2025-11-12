#!/usr/bin/env python3
import requests
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass

BASE_URL = "https://peoply.app"
BASE_API = "https://api.peoply.app"
MAX_REQUESTS = 42


def parse_utc(iso_str):
    return datetime.fromisoformat(iso_str)


@dataclass
class Event:
    id: str
    title: str
    description: str
    start: str
    url: str
    capacity: str
    last_updated: datetime
    location: str = "TBA"
    organizer: str = "Unknown"
    image: str = ""


class Pal:
    def __init__(self, event_database, logger=None):
        self._logger = logger
        self._event_database = Path(event_database)

        self._already_indexed = self.indexed_events(event_database)

        self._pending_events = self.fetch_events()

        self._log(
            "info",
            "Initialized Pal and loading events"
        )

    def _log(self, level, msg):
        if self._logger:
            getattr(self._logger, level, self._logger.info)(msg)

################################
#                              #
#        Indexed Events        #
#                              #
################################

    def indexed_events(self, event_database):
        indexed = {}

        if not self._event_database.exists():
            self._event_database.parent.mkdir(parents=True, exist_ok=True)
            self._event_database.touch()
            return indexed

        with open(event_database, 'r') as infile:
            for line in infile:
                data = line.strip().split(',')
                if data[0]:
                    indexed[data[0]] = data[1]

        return indexed

    def _save_events(self):
        with open(self._event_database, 'w') as outfile:
            for uid, updated_at in self._already_indexed.items():
                curr_iso_str = datetime.now(timezone.utc) \
                    .isoformat(timespec="milliseconds") \
                    .replace("+00:00", 'Z')

                if updated_at < parse_utc(curr_iso_str):
                    continue

                outfile.write(f"{uid},{parse_utc(updated_at)}\n")

    def _update_index(self, uid, updated_at):
        prev = self._already_indexed.get(uid)

        if prev is None or updated_at > prev:
            self._already_indexed[uid] = updated_at
            self._log(
                "info",
                f"Index updated for event {uid} -> {updated_at}"
            )

################################
#                              #
#         Fetch Events         #
#                              #
################################

    def fetch_events(self):
        time = datetime.now(timezone.utc) \
                       .isoformat(timespec="milliseconds") \
                       .replace("+00:00", 'Z')

        # Take = How many events to recieve from api
        params = {"afterDate": time, "take": MAX_REQUESTS}
        response = requests.get(BASE_API + "/events", params=params)

        data = response.json()

        self._log(
            "info",
            f"Fetched {len(data)} events from API"
        )

        return data

################################
#                              #
#           Helpers            #
#                              #
################################

    def _is_indexed(self, event):
        uid = event.get("id")
        updated_at = event.get("updatedAt")
        prev = self._already_indexed.get(uid)

        if uid not in self._already_indexed:
            return False

        new_time = parse_utc(updated_at)
        indexed_time = parse_utc(prev)

        if new_time > indexed_time:
            return False

        return True

    def _build_event(self, event) -> Event:
        return Event(
            id=event.get("id"),
            title=event.get("title"),
            organizer=self._find_event_org_name(event),
            description=event.get("description"),
            url=BASE_URL + '/events/' + event.get("urlId"),
            start=event.get("startDate"),
            location=event.get("locationName"),
            capacity=event.get("capacity"),
            last_updated=parse_utc(event.get("updatedAt")),
            image=event.get("image"),
        )

    def _find_event_org_name(self, event) -> str:
        arrangers = event.get("eventArrangers")

        for item in arrangers:
            arranger = item.get("arranger")
            org = arranger.get("organization")
            user = arranger.get("user")

            if org:
                return org.get("name")

            elif user:
                return f"{user.get('firstName')} {user.get('lastName')}"

        self._log(
            "error",
            f"Could not find organizer for event {event.get('id')}"
        )

        exit(1)

    def get_new_public_events(self):
        out = list()
        for event in self._pending_events:

            if event["visibility"] != "PUBLIC":
                self._log(
                    "debug",
                    f"Skipping non-public event {event.get('id')}"
                )
                continue

            if self._is_indexed(event):
                self._log(
                    "debug",
                    f"Skipping already indexed event {event.get('id')}"
                )
                continue

            built = self._build_event(event)
            out.append(built)

            self._update_index(built.id, built.last_updated)

        self._log(
            "info",
            f"Prepared {len(out)} new/updated public events"
        )

        return out

    def persist_index(self):
        self._save_events()


def main():
    pal = Pal("./data/indexed_events")

    data = pal.get_new_public_events()

    for event in data:
        print(event)


if __name__ == "__main__":
    main()
