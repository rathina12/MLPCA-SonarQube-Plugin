"""Correctness and characterization checks; run from engineering-evidence/."""
import random
import unittest
from golden import ingest
from verifier import tests as challenge_tests
from intervals import baseline, optimized
from legacy import normalize as legacy
from refactored import normalize as refactored

class EvidenceTests(unittest.TestCase):
    def test_golden(self):
        result = unittest.TestResult()
        challenge_tests(ingest).run(result)
        self.assertFalse(result.failures or result.errors, str(result.failures + result.errors))

    def test_refactor_characterization(self):
        rng = random.Random(48)
        values = [None, "", "a", "0", "-4", -1, 2, 4.5, True]
        for _ in range(1000):
            rows = [{"id": rng.choice(values), "amount": rng.choice(values)}
                    for _ in range(rng.randrange(15))]
            self.assertEqual(legacy(rows), refactored(rows))

    def test_optimized_equivalence(self):
        rng = random.Random(86)
        for _ in range(1000):
            rows = []
            for _ in range(rng.randrange(30)):
                x = rng.randrange(20)
                rows.append((x, x + rng.randrange(5)))
            self.assertEqual(baseline(rows), optimized(rows))
if __name__ == "__main__":
    unittest.main()
