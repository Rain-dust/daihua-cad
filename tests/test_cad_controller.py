"""Portable regression tests. Fake COM objects never start or modify real CAD."""
import importlib.util
from pathlib import Path
import tempfile
from types import ModuleType, SimpleNamespace as NS
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load_controller():
    config = ModuleType("config")
    config.get_config = lambda: {"cad": {"type": "AUTOCAD", "startup_wait_time": 0, "command_delay": 0}}
    progid = ModuleType("cad_progid")
    progid.autocad_progids = lambda: ["AutoCAD.Application"]
    client = ModuleType("win32com.client")
    client.VARIANT = lambda kind, values: tuple(values)
    win32 = ModuleType("win32com")
    win32.client = client
    pythoncom = ModuleType("pythoncom")
    pythoncom.VT_ARRAY, pythoncom.VT_R8, pythoncom.VT_DISPATCH = 8192, 5, 9
    pythoncom.CoInitialize = lambda: None
    stubs = {"config": config, "cad_progid": progid, "win32com": win32,
             "win32com.client": client, "pythoncom": pythoncom}
    spec = importlib.util.spec_from_file_location("review_cad_controller", ROOT / "vendor/cad-mcp/src/cad_controller.py")
    module = importlib.util.module_from_spec(spec)
    with patch.dict("sys.modules", stubs):
        spec.loader.exec_module(module)
    return module


CAD = load_controller()


class FakeEntity:
    def __init__(self, fail_style=False, fail_move=False, fail_linetype=False):
        self.deleted = False
        self.color = 1
        self.Lineweight = 25
        self._linetype = "CENTER"
        self.fail_linetype = fail_linetype
        self.fail_style = fail_style
        self.fail_move = fail_move
        self._layer = "0"

    @property
    def Linetype(self):
        return self._linetype

    @Linetype.setter
    def Linetype(self, value):
        if self.fail_linetype:
            raise RuntimeError("linetype assignment failed")
        self._linetype = value

    @property
    def Layer(self):
        return self._layer

    @Layer.setter
    def Layer(self, value):
        if self.fail_style:
            raise RuntimeError("style assignment failed")
        self._layer = value

    def Delete(self):
        self.deleted = True

    def Move(self, *args):
        if self.fail_move:
            raise RuntimeError("move failed")


class ControllerTests(unittest.TestCase):
    def make_controller(self):
        ctl = CAD.CADController.__new__(CAD.CADController)
        ctl.app = NS(Documents=NS(Count=0))
        ctl.doc = NS(StartUndoMark=lambda: None, EndUndoMark=lambda: None,
                     Activate=lambda: None, ActiveLayer=NS(Name="WALL"))
        ctl._target_lost = False
        ctl.command_delay = 0
        ctl.valid_lineweights = [-3, -2, -1, 0, 25]
        return ctl

    def test_save_formats_match_extension(self):
        ctl = self.make_controller()
        calls = []
        ctl.doc.SaveAs = lambda *args: calls.append(args)
        with tempfile.TemporaryDirectory() as directory:
            for suffix, expected in ((".dwg", 64), (".DXF", 65)):
                self.assertTrue(ctl.save_drawing(str(Path(directory) / ("drawing" + suffix))))
                self.assertEqual(calls[-1][1], expected)
            with self.assertRaisesRegex(ValueError, r"\.dwg.*\.dxf"):
                ctl.save_drawing(str(Path(directory) / "drawing.pdf"))
        self.assertEqual(len(calls), 2)

    def test_omitted_styles_override_explicit_user_defaults_with_bylayer(self):
        ctl = self.make_controller()
        entity = FakeEntity()
        ctl._apply_style(entity)
        self.assertEqual((entity.color, entity.Linetype, entity.Lineweight), (256, "ByLayer", -1))
        ctl._apply_style(entity, color=3, lineweight=25)
        self.assertEqual((entity.color, entity.Lineweight), (3, 25))

    def test_failed_new_line_is_removed(self):
        ctl = self.make_controller()
        created = FakeEntity(fail_style=True)
        ctl.doc.ModelSpace = NS(AddLine=lambda *args: created)
        ctl._ensure_layer = lambda name: NS(Name=name)
        self.assertIsNone(ctl.draw_line([0, 0], [10, 0], layer="WALL"))
        self.assertTrue(created.deleted)

    def test_failed_linetype_assignment_is_not_reported_as_success(self):
        ctl = self.make_controller()
        created = FakeEntity(fail_linetype=True)
        ctl.doc.ModelSpace = NS(AddLine=lambda *args: created)
        self.assertIsNone(ctl.draw_line([0, 0], [10, 0]))
        self.assertTrue(created.deleted)

    def test_failed_copy_removes_only_the_new_copy(self):
        ctl = self.make_controller()
        source, copied = FakeEntity(), FakeEntity(fail_move=True)
        source.Copy = lambda: copied
        ctl.doc.HandleToObject = lambda handle: source
        self.assertIsNone(ctl.copy_entity("A", [1, 0]))
        self.assertTrue(copied.deleted)
        self.assertFalse(source.deleted)

    def test_failed_linear_array_removes_every_new_copy_but_not_source(self):
        ctl = self.make_controller()
        source = FakeEntity()
        created = []
        def copy():
            entity = FakeEntity(fail_move=len(created) == 1)
            created.append(entity)
            return entity
        source.Copy = copy
        ctl.doc.HandleToObject = lambda handle: source
        self.assertEqual(ctl.array_linear_entity("A", 4, [10, 0]), [])
        self.assertEqual(len(created), 2)
        self.assertTrue(all(entity.deleted for entity in created))
        self.assertFalse(source.deleted)

    def test_failed_polar_array_removes_every_new_copy_but_not_source(self):
        ctl = self.make_controller()
        source = FakeEntity()
        created = []
        def copy():
            entity = FakeEntity(fail_move=len(created) == 1)
            entity.Rotate = entity.Move
            created.append(entity)
            return entity
        source.Copy = copy
        ctl.doc.HandleToObject = lambda handle: source
        self.assertEqual(ctl.array_polar_entity("A", 4, [0, 0]), [])
        self.assertEqual(len(created), 2)
        self.assertTrue(all(entity.deleted for entity in created))
        self.assertFalse(source.deleted)

    def test_failed_hatch_removes_hatch_and_its_new_boundary(self):
        ctl = self.make_controller()
        boundary, hatch = FakeEntity(), FakeEntity()
        def fail(*args):
            raise RuntimeError("invalid boundary")
        hatch.AppendOuterLoop = fail
        ctl.doc.ModelSpace = NS(AddHatch=lambda *args: hatch)
        ctl.draw_polyline = lambda *args, **kwargs: boundary
        self.assertIsNone(ctl.draw_hatch([[0, 0], [10, 0], [10, 10]]))
        self.assertTrue(boundary.deleted)
        self.assertTrue(hatch.deleted)

    def test_window_and_command_use_pinned_document_after_ui_switch(self):
        ctl = self.make_controller()
        target = ctl.doc
        unrelated = NS(Name="unrelated.dwg")
        ctl.app.ActiveDocument = unrelated
        target.Activate = lambda: setattr(ctl.app, "ActiveDocument", target)
        seen = []
        ctl.app.ZoomExtents = lambda: seen.append(ctl.app.ActiveDocument)
        self.assertTrue(ctl.zoom_extents())
        self.assertIs(seen[-1], target)
        ctl.app.ActiveDocument = unrelated
        target.SendCommand = lambda command: seen.append((ctl.app.ActiveDocument, command))
        self.assertTrue(ctl.send_command("_.ZOOM E"))
        self.assertIs(seen[-1][0], target)

    def test_screenshot_activates_target_before_capture(self):
        ctl = self.make_controller()
        with patch.object(ctl, "_activate_target_document", side_effect=RuntimeError("capture target unavailable")) as activate:
            with self.assertRaisesRegex(RuntimeError, "capture target unavailable"):
                ctl.screenshot()
        activate.assert_called_once()

    def test_closed_target_does_not_adopt_an_unrelated_document(self):
        ctl = self.make_controller()
        unrelated = NS(Name="unrelated.dwg")
        ctl.app.ActiveDocument = unrelated
        ctl.doc.Close = lambda save: None
        self.assertTrue(ctl.close_drawing())
        self.assertIsNone(ctl.doc)
        self.assertTrue(ctl._target_lost)
        self.assertFalse(ctl.start_cad())  # no implicit reconnection/COM call

    def test_failed_explicit_new_never_adopts_a_document_during_reconnect(self):
        ctl = self.make_controller()
        unrelated = NS(Name="unrelated.dwg")
        def fail_add():
            raise RuntimeError("new document failed")
        app = NS(ActiveDocument=unrelated, Documents=NS(Add=fail_add))
        ctl.app = None
        ctl.doc = None
        ctl._target_lost = True
        ctl._get_app_info = lambda: (["Fake.Application"], "Fake CAD")
        with patch.object(CAD.win32com.client, "GetActiveObject", return_value=app, create=True):
            self.assertTrue(ctl.start_cad(True))
        self.assertIsNone(ctl.doc)
        self.assertFalse(ctl.new_drawing())
        self.assertTrue(ctl._target_lost)
        self.assertFalse(ctl.is_running())

    def test_block_query_failure_is_not_reported_as_an_empty_success(self):
        ctl = self.make_controller()
        class BadBlocks:
            @property
            def Count(self):
                raise RuntimeError("block enumeration failed")
        ctl.doc.Blocks = BadBlocks()
        with self.assertRaisesRegex(RuntimeError, "block enumeration failed"):
            ctl.list_blocks()

    def test_dead_method_call_invalidates_target(self):
        ctl = self.make_controller()
        class Disconnected(Exception):
            hresult = -2147417848
        def fail():
            raise Disconnected("CAD exited")
        with self.assertRaises(Disconnected):
            ctl._call_attr(NS(Test=fail), "Test")
        self.assertIsNone(ctl.app)
        self.assertIsNone(ctl.doc)
        self.assertTrue(ctl._target_lost)
        self.assertFalse(ctl.start_cad())


if __name__ == "__main__":
    unittest.main()
