import secrets
from enum import Enum
from typing import Dict
from datetime import datetime, timedelta

class Status(str, Enum):
    CREATED = "CREATED"
    PAID = "PAID"
    REFUNDED = "REFUNDED"
    EXPIRED = "EXPIRED"

class Link:
    def __init__(self, order_id: str, amount: int, ttl: int = 1800):
        self.token = secrets.token_urlsafe(16)
        self.order_id = order_id
        self.amount = amount
        self.status = Status.CREATED
        self.expires_at = datetime.now() + timedelta(seconds=ttl)
        self._payments: set[str] = set()
        self._refunds: set[str] = set()

    @classmethod
    def from_existing(cls, existing_link: "Link", ttl: int = 1800) -> "Link":
        """Create a new Link with same properties but refreshed expiration"""
        new_link = cls.__new__(cls)
        new_link.token = existing_link.token
        new_link.order_id = existing_link.order_id
        new_link.amount = existing_link.amount
        new_link.status = existing_link.status
        new_link.expires_at = datetime.now() + timedelta(seconds=ttl)
        new_link._payments = existing_link._payments.copy()
        new_link._refunds = existing_link._refunds.copy()
        return new_link


class PaymentLinkService:
    """❗ ***NOT*** production-ready.  Your job is to fix it so the tests pass."""
    _storage: Dict[str, Link] = {}              # token  -> Link
    _by_order: Dict[str, Link] = {}             # order_id -> Link

    async def create(self, order_id: str, amount: int, ttl: int = 1800) -> Link:
        if order_id in self._by_order:
            # Instead of updating the existing link, we create a new one
            existing_link = self._by_order[order_id]
            new_link = Link.from_existing(existing_link, ttl)
            self._storage[new_link.token] = new_link
            self._by_order[order_id] = new_link
            return new_link

        link = Link(order_id, amount, ttl)
        self._storage[link.token] = link
        self._by_order[order_id] = link
        return link

    async def pay(self, token: str, idem_key: str) -> Link:
        link = self._storage[token]
        if link.status == Status.EXPIRED:
            raise ValueError("expired")
        if link.status != Status.PAID:
            link.status = Status.PAID
            link._payments.add(idem_key)
        return link

    async def refund(self, token: str, idem_key: str) -> Link:
        link = self._storage[token]
        if link.status != Status.PAID:
            raise ValueError("cannot refund")
        link.status = Status.REFUNDED
        link._refunds.add(idem_key)
        return link
