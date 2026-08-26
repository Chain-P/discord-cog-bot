from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Song:
    title: str
    webpage_url: str
    stream_url: str | None
    duration: int
    requester_id: int
    requester_name: str
