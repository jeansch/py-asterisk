import os
import tempfile
import unittest

from Asterisk.Config import Config, ConfigurationError


class TestConfigurationError(unittest.TestCase):
    def test_str(self):
        e = ConfigurationError("bad config")
        assert "bad config" in str(e)


class TestConfig(unittest.TestCase):
    def test_load_config_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            f.write("[py-asterisk]\n")
            f.write("default connection = test\n")
            f.write("\n")
            f.write("[connection: test]\n")
            f.write("hostname = 127.0.0.1\n")
            f.write("port = 5038\n")
            f.write("username = admin\n")
            f.write("secret = password\n")
            f.flush()
            path = f.name

        try:
            config = Config(path)
            address, username, secret = config.get_connection()
            assert address == ("127.0.0.1", 5038)
            assert username == "admin"
            assert secret == "password"
        finally:
            os.unlink(path)

    def test_no_config_found_raises(self):
        """When no config_pathname is given and no default file exists, raises."""
        import unittest.mock
        with unittest.mock.patch("Asterisk.Config.CONFIG_PATHNAMES", []):
            with self.assertRaises(ConfigurationError):
                Config()

    def test_named_connection(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            f.write("[connection: myconn]\n")
            f.write("hostname = 10.0.0.1\n")
            f.write("port = 5039\n")
            f.write("username = user2\n")
            f.write("secret = pass2\n")
            f.flush()
            path = f.name

        try:
            config = Config(path)
            address, username, secret = config.get_connection("myconn")
            assert address == ("10.0.0.1", 5039)
            assert username == "user2"
            assert secret == "pass2"
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
