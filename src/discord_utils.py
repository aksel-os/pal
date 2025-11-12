#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import requests

load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def send_discord_message(content):
    r = requests.post(DISCORD_WEBHOOK_URL,
                      json=content,
                      timeout=15)
    r.raise_for_status()


def build_event_embed(event):
    embed = {
        "title": event.title,
        "url": event.url,
        "description": event.description,
        "color": 0x5865F2,
        "timestamp": event.start,
        "fields": [
            {"name": "Organizer", "value": event.organizer, "inline": True},
            {"name": "Location", "value": event.location, "inline": True},
        ],
        "footer": {
            "text": "Peoply event",
            # "icon_url": event.icon,
        },
        "image": {"url": event.image},
    }

    if event.capacity is not None:
        embed["fields"].append(
            {"name": "Capacity", "value": event.capacity, "inline": True},
        )

    return embed


def build_event_webhook(event):
    embed = build_event_embed(event)

    content = {
        "username": "Peoply Event Bot",
        "avatar_url": "https://peoply.app/icons/favicon-32x32.png",
        "embeds": [embed],
    }

    return content


def post_all_events(events):
    embeds = [build_event_webhook(event) for event in events]
    for embed in embeds:
        send_discord_message(embed)
