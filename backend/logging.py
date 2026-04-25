def get_error(e):
    return getattr(e, "message", repr(e))