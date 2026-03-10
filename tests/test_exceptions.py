import unittest

import Asterisk
from Asterisk.Manager import (
    ActionFailed,
    AuthenticationFailure,
    CommunicationError,
    GoneAwayError,
    InternalError,
    PermissionDenied,
)


class TestBaseException(unittest.TestCase):
    def test_str(self):
        e = Asterisk.BaseException("something broke")
        assert "something broke" in str(e)

    def test_inherits_exception(self):
        assert issubclass(Asterisk.BaseException, Exception)

    def test_default_prefix(self):
        e = Asterisk.BaseException("err")
        assert "(Base Exception)" in str(e)


class TestManagerExceptions(unittest.TestCase):
    def test_authentication_failure(self):
        # AuthenticationFailure has a default _error but still requires an arg
        # for BaseException.__init__. Use the class _error.
        e = AuthenticationFailure("Authentication failed.")
        assert "Authentication" in str(e)

    def test_communication_error(self):
        packet = {"Response": "Error", "Message": "bad"}
        e = CommunicationError(packet)
        assert "Unexpected" in str(e)

    def test_communication_error_with_msg(self):
        e = CommunicationError({}, msg="custom")
        assert "custom" in str(e)

    def test_gone_away_error(self):
        e = GoneAwayError("connection lost")
        assert isinstance(e, Exception)

    def test_internal_error(self):
        e = InternalError("oops")
        assert "oops" in str(e)
        assert "internal error" in str(e)

    def test_action_failed(self):
        e = ActionFailed("fail")
        assert "fail" in str(e)

    def test_permission_denied(self):
        e = PermissionDenied("Permission denied")
        assert "Permission" in str(e) or "denied" in str(e)

    def test_hierarchy(self):
        assert issubclass(AuthenticationFailure, Asterisk.BaseException)
        assert issubclass(GoneAwayError, Asterisk.BaseException)
        assert issubclass(ActionFailed, Asterisk.BaseException)


if __name__ == "__main__":
    unittest.main()
