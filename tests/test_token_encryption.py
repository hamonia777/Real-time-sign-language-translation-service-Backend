from main.core.encrypted_type import EncryptedText


def test_token_is_encrypted_and_restored():
    column_type = EncryptedText()
    stored = column_type.process_bind_param("kakao-access-token", None)

    assert stored != "kakao-access-token"
    assert column_type.process_result_value(stored, None) == "kakao-access-token"


def test_none_is_passed_through():
    column_type = EncryptedText()
    assert column_type.process_bind_param(None, None) is None
    assert column_type.process_result_value(None, None) is None


def test_legacy_plaintext_is_readable():
    column_type = EncryptedText()
    assert column_type.process_result_value("legacy-plain-token", None) == "legacy-plain-token"
