from fastapi import Request

from app.core import config


def get_client_ip(request: Request) -> str:
    """The visitor's IP. Reads X-Forwarded-For only when proxies are trusted.

    With N trusted proxies, each appends the address it saw, so the real
    client is the Nth entry from the right. Anything further left is
    client-supplied and can be forged, so it is ignored.
    """
    peer = request.client.host if request.client else "unknown"
    hops = config.TRUSTED_PROXY_HOPS

    if hops <= 0:
        return peer

    header = request.headers.get("x-forwarded-for", "")
    parts = [p.strip() for p in header.split(",") if p.strip()]

    if len(parts) >= hops:
        return parts[-hops]

    return peer