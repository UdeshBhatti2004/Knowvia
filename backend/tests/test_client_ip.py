from types import SimpleNamespace
from unittest.mock import patch

from app.api.client_ip import get_client_ip
from app.core import config


def make_request(peer="10.0.0.1", forwarded=None):
    headers = {"x-forwarded-for": forwarded} if forwarded else {}
    return SimpleNamespace(client=SimpleNamespace(host=peer), headers=headers)


def test_ignores_header_when_no_proxy_trusted():
    with patch.object(config, "TRUSTED_PROXY_HOPS", 0):
        request = make_request(forwarded="1.2.3.4")
        assert get_client_ip(request) == "10.0.0.1"


def test_one_proxy_uses_last_entry_not_spoofed_one():
    with patch.object(config, "TRUSTED_PROXY_HOPS", 1):
        request = make_request(forwarded="6.6.6.6, 203.0.113.9")
        assert get_client_ip(request) == "203.0.113.9"


def test_two_proxies():
    with patch.object(config, "TRUSTED_PROXY_HOPS", 2):
        request = make_request(forwarded="6.6.6.6, 203.0.113.9, 10.1.1.1")
        assert get_client_ip(request) == "203.0.113.9"


def test_missing_header_falls_back_to_peer():
    with patch.object(config, "TRUSTED_PROXY_HOPS", 1):
        assert get_client_ip(make_request()) == "10.0.0.1"