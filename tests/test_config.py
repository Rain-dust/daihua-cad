"""Configuration behavior without a CAD installation or client-specific cwd."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("daihua_config_test", Path(__file__).resolve().parents[1] / "vendor/cad-mcp/src/config.py")
config = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(config)


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.file = self.root / "config.json"
        self.addCleanup(patch.stopall)
        patch.object(config, "_CONFIG_PATH", self.file).start()
        patch.object(config, "_PROJECT_ROOT", self.root, create=True).start()
        patch.dict(os.environ, {}, clear=True).start()
        config.get_config.cache_clear()
        self.addCleanup(config.get_config.cache_clear)

    def test_environment_survives_missing_or_corrupt_config(self):
        for text in (None, "{broken"):
            with self.subTest(text=text):
                if text is not None:
                    self.file.write_text(text, encoding="utf-8")
                config.get_config.cache_clear()
                with patch.dict(os.environ, {"DAIHUA_CAD_TYPE": "zwcad", "DAIHUA_OUTPUT_DIR": str(self.root / "chosen")}):
                    loaded = config.get_config()
                self.assertEqual(loaded["cad"]["type"].lower(), "zwcad")
                self.assertEqual(Path(loaded["output"]["directory"]), self.root / "chosen")

    def test_relative_output_does_not_depend_on_client_working_directory(self):
        self.file.write_text(json.dumps({"output": {"directory": "deliveries"}}), encoding="utf-8")
        loaded = config.get_config()
        self.assertEqual(Path(loaded["output"]["directory"]), self.root / "deliveries")
        self.assertTrue(Path(loaded["output"]["directory"]).is_absolute())

    def test_partial_config_preserves_defaults_and_explicit_values(self):
        self.file.write_text(json.dumps({"cad": {"type": "gcad"}, "server": {"port": 9001}}), encoding="utf-8")
        loaded = config.get_config()
        self.assertEqual(loaded["cad"]["type"].lower(), "gcad")
        self.assertEqual(loaded["cad"]["startup_wait_time"], 20)
        self.assertEqual(loaded["server"]["port"], 9001)
        self.assertEqual(loaded["output"]["default_filename"], "cad_drawing.dwg")

    def test_unknown_cad_type_fails_instead_of_launching_autocad(self):
        with patch.dict(os.environ, {"DAIHUA_CAD_TYPE": "typing-error"}):
            with self.assertRaisesRegex(ValueError, "DAIHUA_CAD_TYPE|CAD type"):
                config.get_config()

    def test_fallback_values_are_not_shared_between_reloads(self):
        loaded = config.get_config()
        loaded["cad"]["startup_wait_time"] = -123
        config.get_config.cache_clear()
        self.assertEqual(config.get_config()["cad"]["startup_wait_time"], 20)

    def test_absolute_output_is_preserved(self):
        destination = self.root / "absolute"
        self.file.write_text(json.dumps({"output": {"directory": str(destination)}}), encoding="utf-8")
        self.assertEqual(Path(config.get_config()["output"]["directory"]), destination)
