from collections import defaultdict
from dataclasses import dataclass
from enum import auto
from itertools import islice
from typing import Iterable, TypeVar

from priority_queue import PriorityQueue

_Priority = int
_ItemIdentifier = str
_ExportIdentifier = str

PRIORITY_BATCH_SIZE = 10
MAX_TASKS_TO_ENQUEUE = 100

T = TypeVar("T")

def batched(iterable: Iterable[T], n: int) -> Iterable[tuple[T, ...]]:
    "Batch data into tuples of length n. The last batch may be shorter."
    if n < 1:
        raise ValueError("n must be at least one")
    it = iter(iterable)
    while batch := tuple(islice(it, n)):
        yield batch

class GenerateReportPriorityQueue:
    def __init__(self, queue_name: str) -> None:
        self._priority_queue = PriorityQueue(queue_name)

    def _serialize_tasks(
        self,
        *,
        batch_numbers: list[int],
        package_request_uid: str,
        priority: int,
    ) -> dict[_ItemIdentifier, _Priority]:
        return {
            f"{package_request_uid}|{batch_number}": priority
            for batch_number in batch_numbers
        }

    def _add_tasks_with_priority(
        self,
        batch_numbers: list[int],
        package_request_uid: str,
        priority: int,
    ) -> None:
        tasks = self._serialize_tasks(
            batch_numbers=batch_numbers,
            package_request_uid=package_request_uid,
            priority=priority,
        )
        self._priority_queue.push(tasks)

    def prioritize_tasks(
        self,
        number_of_tasks: int,
        package_request_uid: str,
    ) -> None:
        priority_spacing = 10
        base_priority = self._priority_queue.get_base_score(package_request_uid)
        priority_factor = 0
        max_priority = base_priority
        tasks = [i for i in range(1, number_of_tasks + 1)]
        for batched_numbers in batched(tasks, PRIORITY_BATCH_SIZE):
            priority = base_priority + priority_factor * priority_spacing
            self._add_tasks_with_priority(
                list(batched_numbers),
                package_request_uid=package_request_uid,
                priority=priority,
            )
            max_priority = priority
            priority_factor += 1
        new_base_priority = max_priority + priority_spacing
        self._priority_queue.set_base_score(package_request_uid, new_base_priority)

