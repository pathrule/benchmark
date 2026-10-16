import os
import re
import unittest

from acme import App
from acme.options import APP_OPTIONS, ROUTE_OPTIONS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class RegistryTests(unittest.TestCase):
    def _documented(self) -> set[str]:
        with open(os.path.join(ROOT, "docs", "options.md")) as f:
            return set(re.findall(r"^\| `([a-z_]+)` \|", f.read(), re.M))

    def test_every_app_option_is_documented(self):
        self.assertTrue(set(APP_OPTIONS) <= self._documented(), set(APP_OPTIONS) - self._documented())

    def test_every_route_option_is_documented(self):
        self.assertTrue(set(ROUTE_OPTIONS) <= self._documented(), set(ROUTE_OPTIONS) - self._documented())

    def test_every_app_option_is_accepted(self):
        for name in APP_OPTIONS:
            App(**{name: App().__dict__.get(name, 0)})

    def test_limits_module_matches_source(self):
        import json

        from acme._limits_gen import LIMITS

        with open(os.path.join(ROOT, "scripts", "gen_limits.py")) as f:
            source = f.read()
        parts = [p.strip().strip('"') for p in re.search(r"SOURCE = os\.path\.join\(ROOT, (.+)\)", source).group(1).split(",")]
        with open(os.path.join(ROOT, *parts)) as f:
            self.assertEqual(LIMITS, json.load(f))
