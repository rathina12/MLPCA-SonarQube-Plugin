def ingest(existing, incoming):
    """Broken intentionally: ignores client identity and conflicting retries."""
    result = list(existing)
    seen = {record["event_id"] for record in existing}
    for record in incoming:
        if record["event_id"] not in seen:
            result.append(record)
            seen.add(record["event_id"])
    return result, len(result) - len(existing)
