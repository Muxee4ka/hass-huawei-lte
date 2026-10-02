"""Incoming SMS parsing and seen-message journal for Huawei LTE."""

from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass
import threading
from typing import Any


@dataclass(frozen=True, slots=True)
class Sms:
    """One message from the modem inbox."""

    index: int
    phone: str
    text: str
    date: str
    read: bool

    @property
    def key(self) -> str:
        """Identity that survives modem Index resets."""
        return f"{self.index}|{self.date}|{self.phone}"

    @classmethod
    def from_api(cls, raw: dict[str, Any]) -> "Sms":
        """Build from one sms-list Message item."""
        return cls(
            index=int(raw["Index"]),
            phone=raw.get("Phone") or "",
            text=raw.get("Content") or "",
            date=raw.get("Date") or "",
            read=str(raw.get("Smstat")) == "1",
        )

    def as_event_data(self) -> dict[str, Any]:
        """Data attached to the incoming SMS event."""
        return {
            "phone": self.phone,
            "text": self.text,
            "date": self.date,
            "index": self.index,
        }


def parse_sms_list(response: Any) -> list[Sms]:
    """Parse a get_sms_list response, tolerating empty and single-item shapes."""
    if not isinstance(response, dict):
        return []
    messages = response.get("Messages")
    if not isinstance(messages, dict):
        return []
    items = messages.get("Message") or []
    if isinstance(items, dict):
        items = [items]
    return [Sms.from_api(item) for item in items if isinstance(item, dict)]


class SmsTracker:
    """Remembers seen messages; the first run without a journal is a silent baseline."""

    def __init__(self, seen: Iterable[str] | None, max_seen: int = 200) -> None:
        """Initialize from a stored journal, or None for a first run."""
        self._seen: deque[str] = deque(seen or [], maxlen=max_seen)
        self._baseline = seen is None
        self._lock = threading.Lock()

    def process(self, messages: list[Sms]) -> list[Sms]:
        """Record messages and return the unseen ones, oldest first."""
        with self._lock:
            fresh = sorted(
                (m for m in messages if m.key not in self._seen),
                key=lambda m: (m.date, m.index),
            )
            self._seen.extend(m.key for m in fresh)
            if self._baseline:
                self._baseline = False
                return []
            return fresh

    def as_data(self) -> dict[str, list[str]]:
        """Journal for Store."""
        with self._lock:
            return {"seen": list(self._seen)}
