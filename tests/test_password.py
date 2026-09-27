from app.auth.password import hash_password, verify_password

def test_hash_password_and_verify_correct_password() -> None:
    password = "my_secure_password"
    hashed_password = hash_password(password)
    assert verify_password(password, hashed_password) is True


def test_reject_incorrect_password() -> None:
    password = "my_secure_password"
    hashed_password = hash_password(password)
    assert verify_password("wrong_password", hashed_password) is False