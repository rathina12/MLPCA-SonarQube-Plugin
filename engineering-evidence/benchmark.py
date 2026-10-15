"""Reproducible, machine-dependent benchmarks. Run from engineering-evidence/."""
import random
import statistics
import time
from intervals import baseline, optimized

rng = random.Random(2026)
for size in (250, 500, 1000):
    intervals = [(i * 3, i * 3 + 1) for i in range(size)]
    rng.shuffle(intervals)
    timings = []
    for implementation in (baseline, optimized):
        samples = []
        for _ in range(5):
            start = time.perf_counter()
            result = implementation(intervals)
            samples.append(time.perf_counter() - start)
            assert result is False
        timings.append(statistics.median(samples))
    print(f"n={size}: baseline={timings[0]:.6f}s, "
          f"optimized={timings[1]:.6f}s, speedup={timings[0]/timings[1]:.1f}x")
