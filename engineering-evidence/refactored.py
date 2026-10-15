from dataclasses import dataclass

@dataclass(frozen=True)
class Normalized:
    identifier: str
    amount: int

def parse(row):
    if "id" not in row or "amount" not in row:
        return None, "missing field"
    try:
        amount = int(row["amount"])
    except (TypeError, ValueError):
        return None, "invalid amount"
    if amount < 0:
        return None, "negative amount"
    return Normalized(str(row["id"]).strip(), amount), None

def normalize(rows):
    result = []
    for row in rows:
        item, error = parse(row)
        if error:
            result.append({"ok": False, "error": error})
        else:
            result.append({"ok": True, "id": item.identifier, "amount": item.amount})
    return result
