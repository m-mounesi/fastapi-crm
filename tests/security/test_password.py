from security.password import hash_password, verify_password


# ===========================================================================
# hash_password
# ===========================================================================


class TestHashPassword:
    def test_returns_string(self):
        result = hash_password("mypassword")
        assert isinstance(result, str)

    def test_hash_differs_from_plaintext(self):
        hashed = hash_password("mypassword")
        assert hashed != "mypassword"

    def test_hash_is_not_empty(self):
        hashed = hash_password("mypassword")
        assert len(hashed) > 0

    def test_different_inputs_produce_different_hashes(self):
        h1 = hash_password("password1")
        h2 = hash_password("password2")
        assert h1 != h2

    def test_same_input_produces_different_hashes(self):
        h1 = hash_password("mypassword")
        h2 = hash_password("mypassword")
        assert h1 != h2

    def test_empty_password(self):
        hashed = hash_password("")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_long_password(self):
        long_pw = "a" * 10000
        hashed = hash_password(long_pw)
        assert isinstance(hashed, str)
        assert verify_password(long_pw, hashed)

    def test_unicode_password(self):
        hashed = hash_password("parole Unicode !@#$%")
        assert isinstance(hashed, str)
        assert verify_password("parole Unicode !@#$%", hashed)


# ===========================================================================
# verify_password
# ===========================================================================


class TestVerifyPassword:
    def test_correct_password_returns_true(self):
        hashed = hash_password("correcthorse")
        assert verify_password("correcthorse", hashed) is True

    def test_incorrect_password_returns_false(self):
        hashed = hash_password("correcthorse")
        assert verify_password("wronghorse", hashed) is False

    def test_empty_password_matches_empty_hash(self):
        hashed = hash_password("")
        assert verify_password("", hashed) is True

    def test_empty_password_does_not_match_nonempty(self):
        hashed = hash_password("notempty")
        assert verify_password("", hashed) is False

    def test_nonempty_password_does_not_match_empty(self):
        hashed = hash_password("")
        assert verify_password("notempty", hashed) is False

    def test_verify_with_invalid_hash_returns_false(self):
        assert verify_password("password", "not-a-real-hash") is False

    def test_verify_with_empty_hash_returns_false(self):
        assert verify_password("password", "") is False

    def test_verify_with_none_like_hash_returns_false(self):
        assert verify_password("password", "$argon2id$invalid") is False
