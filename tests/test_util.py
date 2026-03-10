import io
import unittest

from Asterisk.Util import (
    AttributeDict,
    EventCollection,
    SubscriptionError,
    Unspecified,
    dump_human,
    dump_packet,
)


class TestUnspecified(unittest.TestCase):
    def test_is_singleton_like(self):
        assert Unspecified is not None

    def test_repr(self):
        assert "Unspecified" in repr(Unspecified)


class TestAttributeDict(unittest.TestCase):
    def test_basic_dict_access(self):
        d = AttributeDict()
        d["key"] = "value"
        assert d["key"] == "value"

    def test_attribute_access(self):
        d = AttributeDict()
        d["foo"] = "bar"
        assert d.foo == "bar"

    def test_attribute_set(self):
        d = AttributeDict()
        d.foo = "bar"
        assert d["foo"] == "bar"

    def test_copy(self):
        d = AttributeDict()
        d["a"] = "1"
        c = d.copy()
        assert isinstance(c, AttributeDict)
        assert c["a"] == "1"
        c["b"] = "2"
        assert "b" not in d

    def test_chan_variable_multi_value(self):
        d = AttributeDict()
        d["ChanVariable"] = "key1=val1"
        d["ChanVariable"] = "key2=val2"
        assert d["ChanVariable"] == {"key1": "val1", "key2": "val2"}

    def test_dest_chan_variable_multi_value(self):
        d = AttributeDict()
        d["DestChanVariable"] = "x=1"
        d["DestChanVariable"] = "y=2"
        assert d["DestChanVariable"] == {"x": "1", "y": "2"}

    def test_chan_variable_without_equals(self):
        d = AttributeDict()
        d["ChanVariable"] = "noequals"
        assert d["ChanVariable"] == "noequals"

    def test_regular_key_overwrites(self):
        d = AttributeDict()
        d["Status"] = "first"
        d["Status"] = "second"
        assert d["Status"] == "second"


class TestEventCollection(unittest.TestCase):
    def test_subscribe_and_fire(self):
        ec = EventCollection()
        results = []
        ec.subscribe("TestEvent", lambda x: results.append(x))
        ec.fire("TestEvent", 42)
        assert results == [42]

    def test_unsubscribe(self):
        ec = EventCollection()
        handler = lambda: None
        ec.subscribe("Evt", handler)
        ec.unsubscribe("Evt", handler)
        # Fire should not call handler
        ec.fire("Evt")

    def test_clear(self):
        ec = EventCollection()
        ec.subscribe("A", lambda: None)
        ec.subscribe("B", lambda: None)
        ec.clear()
        assert ec.subscriptions == {}

    def test_initial_functions_uses_full_name(self):
        def on_MyEvent():
            pass

        ec = EventCollection([on_MyEvent])
        # Uses func.__name__ as event name
        assert "on_MyEvent" in ec.subscriptions

    def test_fire_returns_last_handler_result(self):
        ec = EventCollection()
        ec.subscribe("Evt", lambda: "result")
        result = ec.fire("Evt")
        assert result == "result"

    def test_fire_nonexistent_event(self):
        ec = EventCollection()
        # Should not raise
        result = ec.fire("NoSuchEvent")
        assert result is None

    def test_iadd(self):
        ec1 = EventCollection()
        ec2 = EventCollection()
        handler = lambda: None
        ec2.subscribe("Evt", handler)
        ec1 += ec2
        assert "Evt" in ec1.subscriptions

    def test_isub(self):
        ec1 = EventCollection()
        ec2 = EventCollection()
        handler = lambda: None
        ec1.subscribe("Evt", handler)
        ec2.subscribe("Evt", handler)
        ec1 -= ec2
        assert ec1.subscriptions.get("Evt", []) == []

    def test_multiple_handlers(self):
        ec = EventCollection()
        results = []
        ec.subscribe("Evt", lambda: results.append(1))
        ec.subscribe("Evt", lambda: results.append(2))
        ec.fire("Evt")
        assert results == [1, 2]


class TestDumpPacket(unittest.TestCase):
    def test_dump_response_packet(self):
        packet = AttributeDict()
        packet["Response"] = "Success"
        packet["Message"] = "Hello"
        out = io.StringIO()
        dump_packet(packet, file=out)
        output = out.getvalue()
        assert "Response" in output
        assert "Hello" in output

    def test_dump_event_packet(self):
        packet = AttributeDict()
        packet["Event"] = "Dial"
        packet["Channel"] = "SIP/100"
        out = io.StringIO()
        dump_packet(packet, file=out)
        output = out.getvalue()
        assert "Dial" in output
        assert "Channel" in output


class TestDumpHuman(unittest.TestCase):
    def test_dump_string(self):
        out = io.StringIO()
        dump_human("hello", file=out)
        assert "hello" in out.getvalue()

    def test_dump_dict(self):
        out = io.StringIO()
        dump_human({"key": "val"}, file=out)
        output = out.getvalue()
        assert "key" in output
        assert "val" in output

    def test_dump_list(self):
        out = io.StringIO()
        dump_human(["a", "b"], file=out)
        output = out.getvalue()
        assert "a" in output
        assert "b" in output

    def test_dump_nested(self):
        out = io.StringIO()
        dump_human({"outer": {"inner": "val"}}, file=out)
        output = out.getvalue()
        assert "outer" in output
        assert "inner" in output

    def test_dump_int(self):
        out = io.StringIO()
        dump_human(42, file=out)
        assert "42" in out.getvalue()


if __name__ == "__main__":
    unittest.main()
