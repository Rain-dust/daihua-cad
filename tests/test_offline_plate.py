import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("offline_plate", Path(__file__).resolve().parents[1] / "examples/offline_plate.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class OfflinePlateTests(unittest.TestCase):
    def test_round_trip_and_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "plate.dxf"
            saved = module.create_plate(destination)
            self.assertEqual(len(saved.modelspace().query("CIRCLE")), 4)
            before = destination.read_bytes()
            with self.assertRaises(FileExistsError):
                module.create_plate(destination)
            self.assertEqual(before, destination.read_bytes())
