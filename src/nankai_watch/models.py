from dataclasses import dataclass, field
from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class WatchError(Exception):
    """Only fixed, public-safe messages may be passed to this exception."""
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


@dataclass(frozen=True)
class Source:
    source_id: str
    site_id: str
    name: str
    url: str
    source_type: str
    allow_empty: bool
    priority: int
    selectors: dict
    layout_group: str


@dataclass(frozen=True)
class ParsedItem:
    source_id: str
    site_id: str
    title: str
    url: str
    publish_date: str | None


@dataclass
class ParsedPage:
    items: list[ParsedItem]
    next_url: str | None
    valid_empty: bool = False


@dataclass
class FetchResult:
    url: str
    status: int
    body: bytes = b""
    etag: str | None = None
    last_modified: str | None = None


@dataclass
class Report:
    day: str
    payloads: list[dict]
    event_ids: list[str] = field(default_factory=list)
