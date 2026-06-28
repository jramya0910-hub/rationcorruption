def success(data=None, message: str = "") -> dict:
    return {"status": "success", "data": data or {}, "message": message}


def error(message: str, data=None) -> dict:
    return {"status": "error", "data": data or {}, "message": message}
