import logging
import unittest

from Asterisk.Logging import AsteriskLogger, InstanceLogger


class TestCustomLogLevels(unittest.TestCase):
    def test_state_level_exists(self):
        assert hasattr(logging, "STATE")
        assert logging.STATE == logging.INFO - 1

    def test_packet_level_exists(self):
        assert hasattr(logging, "PACKET")
        assert logging.PACKET == logging.DEBUG - 1

    def test_io_level_exists(self):
        assert hasattr(logging, "IO")
        assert logging.IO == logging.PACKET - 1


class TestInstanceLogger(unittest.TestCase):
    def test_get_logger_name(self):

        class MyClass(InstanceLogger):
            pass

        obj = MyClass()
        name = obj.getLoggerName()
        assert "MyClass" in name

    def test_get_logger_returns_logger(self):

        class MyClass(InstanceLogger):
            pass

        obj = MyClass()
        logger = obj.getLogger()
        assert isinstance(logger, logging.Logger)


if __name__ == "__main__":
    unittest.main()
