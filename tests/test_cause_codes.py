import unittest

import Asterisk


class TestCauseCodes(unittest.TestCase):
    def test_cause_codes_is_dict(self):
        assert isinstance(Asterisk.cause_codes, dict)

    def test_known_codes(self):
        assert 0 in Asterisk.cause_codes
        assert 16 in Asterisk.cause_codes
        assert 17 in Asterisk.cause_codes

    def test_code_structure(self):
        for code, value in Asterisk.cause_codes.items():
            assert isinstance(value, tuple)
            assert len(value) == 3
            assert isinstance(value[0], int)
            assert isinstance(value[1], str)
            assert isinstance(value[2], str)

    def test_clear_code(self):
        code, name, desc = Asterisk.cause_codes[16]
        assert name == "CLEAR"


if __name__ == "__main__":
    unittest.main()
