import unittest
from unittest.mock import MagicMock, patch

from Asterisk.Manager import BaseChannel, BaseManager, ZapChannel
from Asterisk.Util import AttributeDict


class TestBaseChannel(unittest.TestCase):
    def setUp(self):
        self.manager = MagicMock()
        self.channel = BaseChannel(self.manager, "SIP/100-0001")

    def test_str(self):
        assert str(self.channel) == "SIP/100-0001"

    def test_repr(self):
        r = repr(self.channel)
        assert "SIP/100-0001" in r

    def test_equality(self):
        ch1 = BaseChannel(self.manager, "SIP/100-0001")
        ch2 = BaseChannel(self.manager, "SIP/100-0001")
        assert ch1 == ch2

    def test_inequality(self):
        ch1 = BaseChannel(self.manager, "SIP/100-0001")
        ch2 = BaseChannel(self.manager, "SIP/200-0002")
        assert ch1 != ch2

    def test_hash(self):
        ch1 = BaseChannel(self.manager, "SIP/100-0001")
        ch2 = BaseChannel(self.manager, "SIP/100-0001")
        assert hash(ch1) == hash(ch2)

    def test_getitem_calls_getvar(self):
        self.channel["myvar"]
        self.manager.Getvar.assert_called_once_with(self.channel, "myvar")

    def test_setitem_calls_setvar(self):
        self.channel["myvar"] = "val"
        self.manager.Setvar.assert_called_once_with(self.channel, "myvar", "val")

    def test_hangup_delegates(self):
        self.channel.Hangup()
        self.manager.Hangup.assert_called_once_with(self.channel)

    def test_redirect_delegates(self):
        self.channel.Redirect("default", "100", 1)
        self.manager.Redirect.assert_called_once_with(
            self.channel, "default", "100", 1, None
        )

    def test_status_delegates(self):
        self.channel.Status()
        self.manager.Status.assert_called_once()

    def test_monitor_delegates(self):
        self.channel.Monitor("/tmp/rec", "wav", True)
        self.manager.Monitor.assert_called_once_with(
            self.channel, "/tmp/rec", "wav", True
        )

    def test_stop_monitor_delegates(self):
        self.channel.StopMonitor()
        self.manager.StopMonitor.assert_called_once_with(self.channel)


class TestZapChannel(unittest.TestCase):
    def setUp(self):
        self.manager = MagicMock()
        self.channel = ZapChannel(self.manager, "Zap/1-1")

    def test_zap_hangup(self):
        self.channel.ZapHangup()
        self.manager.ZapHangup.assert_called_once_with(self.channel)

    def test_zap_dnd_on(self):
        self.channel.ZapDNDon()
        self.manager.ZapDNDon.assert_called_once_with(self.channel)

    def test_zap_dnd_off(self):
        self.channel.ZapDNDoff()
        self.manager.ZapDNDoff.assert_called_once_with(self.channel)


class TestBaseManagerGetChannel(unittest.TestCase):
    @patch.object(BaseManager, "__init__", lambda self, *a, **kw: None)
    def test_get_channel_sip(self):
        mgr = BaseManager.__new__(BaseManager)
        ch = mgr.get_channel("SIP/100-0001")
        assert isinstance(ch, BaseChannel)
        assert not isinstance(ch, ZapChannel)

    @patch.object(BaseManager, "__init__", lambda self, *a, **kw: None)
    def test_get_channel_zap(self):
        mgr = BaseManager.__new__(BaseManager)
        ch = mgr.get_channel("Zap/1-1")
        assert isinstance(ch, ZapChannel)


class TestBaseManagerStripEvinfo(unittest.TestCase):
    @patch.object(BaseManager, "__init__", lambda self, *a, **kw: None)
    def test_strip_evinfo(self):
        mgr = BaseManager.__new__(BaseManager)
        event = AttributeDict()
        event["ActionID"] = "123"
        event["Event"] = "Dial"
        event["Channel"] = "SIP/100"
        result = mgr.strip_evinfo(event)
        assert "ActionID" not in result
        assert "Event" not in result
        assert result["Channel"] == "SIP/100"


if __name__ == "__main__":
    unittest.main()
