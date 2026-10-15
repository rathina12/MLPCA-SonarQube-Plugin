import copy
import json
import math


def validate_json(value):
    """Validate the actual JSON data model before serialization."""
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float and math.isfinite(value):
        return
    if type(value) is list:
        for child in value:
            validate_json(child)
        return
    if type(value) is dict and all(type(key) is str for key in value):
        for child in value.values():
            validate_json(child)
        return
    raise ValueError("Invalid JSON payload")

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
        validate_json(item["payload"])
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
