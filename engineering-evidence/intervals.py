"""Interval overlap benchmark: half-open time windows [start, end)."""
def baseline(intervals):
    for i, (a, b) in enumerate(intervals):
        for c, d in intervals[i + 1:]:
            if a < b and c < d and max(a, c) < min(b, d):
                return True
    return False

def optimized(intervals):
    last_end = None
    for start, end in sorted(intervals):
        if start >= end:
            continue
        if last_end is not None and start < last_end:
            return True
        last_end = end if last_end is None else max(last_end, end)
    return False
