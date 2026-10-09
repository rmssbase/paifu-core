from functools import lru_cache

from .common import HONOR_START, YAOCHU_KINDS


@lru_cache(maxsize=1 << 16)
def _group_partitions(counts):
    counts = list(counts)
    start = next((i for i, c in enumerate(counts) if c), None)
    if start is None:
        return ((),)
    results = []
    if counts[start] >= 3:
        counts[start] -= 3
        for rest in _group_partitions(tuple(counts)):
            results.append((("trip", start),) + rest)
        counts[start] += 3
    if start < HONOR_START and start % 9 <= 6 and counts[start + 1] and counts[start + 2]:
        for k in range(3):
            counts[start + k] -= 1
        for rest in _group_partitions(tuple(counts)):
            results.append((("seq", start),) + rest)
        for k in range(3):
            counts[start + k] += 1
    return tuple(results)


def standard_decompositions(counts):
    """Yield (pair_kind, groups) for every way to split concealed counts into a pair plus complete groups."""
    if sum(counts) % 3 != 2:
        return
    counts = list(counts)
    for pair in range(34):
        if counts[pair] < 2:
            continue
        counts[pair] -= 2
        for groups in _group_partitions(tuple(counts)):
            yield pair, groups
        counts[pair] += 2


def is_seven_pairs(counts):
    return sum(counts) == 14 and sum(1 for c in counts if c == 2) == 7


def is_thirteen_orphans(counts):
    if sum(counts) != 14:
        return False
    if any(counts[k] == 0 for k in YAOCHU_KINDS):
        return False
    return all(counts[k] == 0 for k in range(34) if k not in YAOCHU_KINDS)


def is_agari(counts):
    if sum(counts) % 3 != 2:
        return False
    if is_seven_pairs(counts) or is_thirteen_orphans(counts):
        return True
    return next(standard_decompositions(counts), None) is not None


def waits(counts):
    """Kinds that complete a concealed part whose size is 3n+1; a kind already held four times is never a wait."""
    return _waits(tuple(counts))


@lru_cache(maxsize=1 << 16)
def _waits(counts):
    if sum(counts) % 3 != 1:
        return frozenset()
    result = set()
    counts = list(counts)
    for kind in range(34):
        if counts[kind] >= 4:
            continue
        counts[kind] += 1
        if is_agari(counts):
            result.add(kind)
        counts[kind] -= 1
    return frozenset(result)


def yaochu_kind_count(counts):
    return sum(1 for k in YAOCHU_KINDS if counts[k])
