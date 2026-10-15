"""Local trusted-code verifier; do not run untrusted submissions unsandboxed."""
import copy
import importlib.util
import sys
import unittest

def load(path):
    spec = importlib.util.spec_from_file_location("candidate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ingest

def tests(fn):
    def r(client, event, payload):
        return {"client_id": client, "event_id": event, "payload": payload}

    class Checks(unittest.TestCase):
        def test_distinct_clients_same_id(self):
            self.assertEqual(fn([], [r("a", "x", 1), r("b", "x", 2)])[1], 2)
        def test_retry_same_payload(self):
            self.assertEqual(fn([r("a", "x", {"x": 1})], [r("a", "x", {"x": 1})])[1], 0)
        def test_conflicting_retry(self):
            with self.assertRaises(ValueError):
                fn([r("a", "x", 1)], [r("a", "x", 2)])
        def test_intrabatch_conflict(self):
            with self.assertRaises(ValueError):
                fn([], [r("a", "x", 1), r("a", "x", 2)])
        def test_batch_duplicate(self):
            self.assertEqual(fn([], [r("a", "x", 1), r("a", "x", 1)])[1], 1)
        def test_bad_record(self):
            with self.assertRaises(ValueError):
                fn([], [{"event_id": "x"}])
        def test_bad_payload(self):
            with self.assertRaises(ValueError):
                fn([], [r("a", "x", {1, 2})])
        def test_reject_nonstring_json_keys(self):
            with self.assertRaises(ValueError):
                fn([], [r("a", "x", {1: "x"})])

        def test_reject_nested_nonstring_keys(self):
            with self.assertRaises(ValueError):
                fn([], [r("a", "x", {"nested": {False: "x"}})])

        def test_reject_nonfinite_numbers(self):
            with self.assertRaises(ValueError):
                fn([], [r("a", "x", [float("inf")])])

        def test_reject_tuple_payload(self):
            with self.assertRaises(ValueError):
                fn([], [r("a", "x", (1, 2))])

        def test_immutable_results(self):
            existing = [r("a", "x", {"items": [1]})]
            result, _ = fn(existing, [])
            result[0]["payload"]["items"].append(2)
            self.assertEqual(existing[0]["payload"]["items"], [1])
        def test_atomic_inputs_on_conflict(self):
            existing = [r("a", "x", 1)]
            incoming = [r("b", "y", 2), r("a", "x", 3)]
            before = copy.deepcopy((existing, incoming))
            with self.assertRaises(ValueError):
                fn(existing, incoming)
            self.assertEqual((existing, incoming), before)
    return unittest.defaultTestLoader.loadTestsFromTestCase(Checks)

if __name__ == "__main__":
    outcome = unittest.TextTestRunner(verbosity=2).run(tests(load(sys.argv[1])))
    raise SystemExit(0 if outcome.wasSuccessful() else 1)
