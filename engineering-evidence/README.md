# Reproducible software engineering exercises

This directory showcases a deliberately buggy event-ingestion starter, a golden reference implementation, and behavior-based verification. It is a **portfolio demonstration**, not a production RL evaluation service.

The task tests deduplication by `(client_id, event_id)`, safe retries, conflicting payload detection, input immutability, and validation of JSON-compatible values.

Run locally with Python 3.10+:

```bash
python engineering-evidence/verifier.py engineering-evidence/starter.py  # expected failure
python engineering-evidence/verifier.py engineering-evidence/golden.py   # expected success
```

A real coding-agent assessment needs isolation, restricted network/filesystem access, and resource limits: this example loads candidate Python modules directly and must only be used with trusted local candidate files.

See the [full engineering evidence pack](https://github.com/rathina12/MLPCA-SonarQube-Plugin) for further context. This does **not** claim external third-party PR acceptance.
