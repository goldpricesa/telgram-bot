from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class TokenBucket:
    __slots__ = ("rate", "capacity", "tokens", "last")

    def __init__(self, rate: float, capacity: float):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last = time.monotonic()

    def consume(self, amount: float = 1.0) -> bool:
        now = time.monotonic()
        self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.rate)
        self.last = now
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False


class ThrottleMiddleware(BaseMiddleware):
    """Per-user in-process token bucket. 1 msg/s with burst of 3."""

    def __init__(self, rate: float = 1.0, capacity: float = 3.0):
        self.rate = rate
        self.capacity = capacity
        self._buckets: dict[int, TokenBucket] = defaultdict(lambda: TokenBucket(rate, capacity))

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        bucket = self._buckets[user.id]
        if not bucket.consume():
            data["throttled"] = True
        return await handler(event, data)
