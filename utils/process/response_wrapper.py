def api_response(data=None, status=True, error=False, message="success"):
    
    if data is None:
        data = []
    return {
        "status": status,
        "error": error,
        "message": message,
        "data": data,
    }