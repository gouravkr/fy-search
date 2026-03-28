import unittest

from fy_search import __version__
from fy_search.app import main


class EntrypointTests(unittest.TestCase):
    def test_app_exports_version(self):
        self.assertEqual(__version__, "0.1.0")

    def test_main_is_callable(self):
        self.assertTrue(callable(main))
