from datetime import timezone


def utc_timestamp(value):
    """Serialize an optional aware timestamp as an ISO 8601 UTC string."""
    return value.astimezone(timezone.utc).isoformat() if value is not None else None
