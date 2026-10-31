from app.core.passwords import hash_password, verify_password


def test_hash_and_verify():
    h = hash_password("correct horse")
    assert h.startswith("scrypt$")
    assert verify_password("correct horse", h)
    assert not verify_password("wrong", h)


def test_salt_is_random():
    assert hash_password("same") != hash_password("same")


def test_malformed_hash_returns_false():
    assert not verify_password("x", "garbage")
    assert not verify_password("x", "bcrypt$1$2$3$a$b")