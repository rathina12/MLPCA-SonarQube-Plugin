def normalize(rows):
    result = []
    for row in rows:
        if "id" not in row or "amount" not in row:
            result.append({"ok": False, "error": "missing field"})
        else:
            try:
                amount = int(row["amount"])
                if amount < 0:
                    result.append({"ok": False, "error": "negative amount"})
                else:
                    result.append({"ok": True, "id": str(row["id"]).strip(), "amount": amount})
            except (TypeError, ValueError):
                result.append({"ok": False, "error": "invalid amount"})
    return result
