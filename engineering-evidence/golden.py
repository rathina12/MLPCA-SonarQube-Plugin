import copy
import json

def ingest(existing, incoming):
    """Return fresh records, count of added events; reject conflicting retries."""
    if not isinstance(existing, list) or not isinstance(incoming, list):
        raise ValueError("Expected lists")
    seen = {}
    result = []
    for index, item in enumerate(existing + incoming):
        if not isinstance(item, dict) or set(item) != {"client_id", "event_id", "payload"}:
            raise ValueError("Invalid record")
        client, event = item["client_id"], item["event_id"]
        if not isinstance(client, str) or not client.strip() or not isinstance(event, str) or not event.strip():
            raise ValueError("Invalid key")
        try:
            payload = json.dumps(item["payload"], sort_keys=True, allow_nan=False)
        except (TypeError, ValueError):
            raise ValueError("Invalid payload")
        key = (client, event)
        if key in seen:
            if index < len(existing) or seen[key] != payload:
                raise ValueError("Duplicate identity with conflicting or preexisting record")
            continue
        seen[key] = payload
        result.append(copy.deepcopy(item))
    return result, len(result) - len(existing)
