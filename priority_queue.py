from datetime import datetime, UTC

import redis

_Priority = int
_ItemIdentifier = str

def utc_now() -> datetime:
    return datetime.now(UTC)

class PriorityQueue:

    def __init__(self, queue_name: str) -> None:
        self.queue_name = queue_name
        self._client = redis.Redis()

    def set_base_score(self, package_request_uid: str, score: int) -> None:
        self._client.set(
            name=f"{self.queue_name}:max_score:{package_request_uid}",
            value=score,
        )

    def get_base_score(self, package_request_uid: str) -> int:
        package_score = self._client.get(
            f"{self.queue_name}:max_score:{package_request_uid}"
        )
        if package_score:
            return int(package_score)

        highest_priority_items = self._client.zrange(
            self.queue_name, 0, 1, withscores=True
        )
        if highest_priority_items:
            highest_priority_item, minimum_score = highest_priority_items[0]
            return int(minimum_score)

        timestamp = int(utc_now().timestamp())
        return timestamp

    def get_priority_count(self, counter_name: str) -> int:
       return int(self._client.get(counter_name) or 0)

    def incr_priority_count(self, counter_name: str) -> None:
        self._client.incr(counter_name)

    def push(self, items: dict[_ItemIdentifier, _Priority]) -> None:
        for item, priority in items.items():
            self._client.zadd(name=self.queue_name, mapping={item: priority})  # type: ignore

    def pop(self, number_of_items: int = 1) -> list[tuple[_ItemIdentifier, _Priority]]:
        items = self._client.zpopmin(self.queue_name, number_of_items)
        return [(identifier.decode(), int(priority)) for identifier, priority in items]
