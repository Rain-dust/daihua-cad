import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("cad_progid", Path(__file__).resolve().parents[1] / "vendor/cad-mcp/src/cad_progid.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ProgIDTests(unittest.TestCase):
    def test_numeric_order_and_filter(self):
        self.assertEqual(module.autocad_progids(["AutoCAD.Application.9", "AutoCAD.Application.25.1", "AutoCAD.Application.24.3", "Other.Application", "AutoCAD.Application.Evil"], override=""), ["AutoCAD.Application.25.1", "AutoCAD.Application.24.3", "AutoCAD.Application.9", "AutoCAD.Application"])
    def test_explicit_override(self):
        self.assertEqual(module.autocad_progids([], override="AutoCAD.Application.24.3"), ["AutoCAD.Application.24.3"])
    def test_generic_fallback(self):
        self.assertEqual(module.autocad_progids([], override=""), ["AutoCAD.Application"])
