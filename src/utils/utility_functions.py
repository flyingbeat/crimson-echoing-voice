from typing import Counter, TypeVar

T = TypeVar("T")


def get_common_values(values: list[T], min_count: int = 1) -> list[tuple[T, int]]:
    value_counts = Counter(values)
    return [
        (value, count)
        for value, count in value_counts.most_common()
        if count >= min_count
    ]
