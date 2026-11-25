"""Channel-agnostic notification transport.

Business services build `OutgoingMessage`s; the active `Notifier` delivers them.
The Telegram bot registers a `TelegramNotifier` at startup; other channels
(push, e-mail, SMS) can be plugged in the same way.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Protocol

log = logging.getLogger(__name__)


@dataclass
class Button:
    text: str
    callback: str | None = None
    url: str | None = None
    webapp_url: str | None = None


@dataclass
class OutgoingMessage:
    chat_id: int
    text: str
    buttons: list[list[Button]] = field(default_factory=list)


class Notifier(Protocol):
    async def send(self, message: OutgoingMessage) -> bool: ...


class MemoryNotifier:
    """Default notifier: logs and keeps messages in memory (dev & tests)."""

    def __init__(self) -> None:
        self.sent: list[OutgoingMessage] = []

    async def send(self, message: OutgoingMessage) -> bool:
        self.sent.append(message)
        log.info("notify chat=%s: %s", message.chat_id, message.text.replace("\n", " | ")[:200])
        return True


_notifier: Notifier = MemoryNotifier()


def set_notifier(notifier: Notifier) -> None:
    global _notifier
    _notifier = notifier


def get_notifier() -> Notifier:
    return _notifier


async def send(chat_id: int | None, text: str, buttons: list[list[Button]] | None = None) -> bool:
    if not chat_id:
        return False
    try:
        return await _notifier.send(OutgoingMessage(chat_id, text, buttons or []))
    except Exception:  # a failed notification must never break a business operation
        log.exception("Notification to %s failed", chat_id)
        return False
