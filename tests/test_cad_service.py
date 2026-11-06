"""Exercise the actual service class/tool functions without importing COM/server globals."""
import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace as NS
import typing
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_service_definitions():
    source = ROOT / "vendor/cad-mcp/src/server.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    wanted = {"CADService", "_unavailable_message", "_ensure_running", "new_drawing", "open_drawing", "close_drawing"}
    nodes = [node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in wanted]
    for node in nodes:
        node.decorator_list = []
    env = dict(vars(typing))
    env.update(CADController=NS(_safe_attr=lambda obj, name: getattr(obj, name, None)),
               Context=object, ToolResult=lambda **kwargs: NS(**kwargs),
               logger=NS(info=lambda *args: None))
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), "exec"), env)
    return env


class ServiceTests(unittest.TestCase):
    def make_service(self):
        env = load_service_definitions()
        cls = env["CADService"]
        svc = cls.__new__(cls)
        svc.drawing_state = {"entities": [], "current_layer": "OLD", "last_command": "", "last_result": ""}
        svc.controller = NS(is_running=lambda: True)
        env["cad_service"] = svc
        return svc, env

    def test_default_layer_uses_current_target_layer_instead_of_session_cache(self):
        svc, _ = self.make_service()
        layers = []
        svc.controller.get_current_layer_name = lambda: "WALL"
        svc.controller.draw_line = lambda *args: layers.append(args[2])
        svc.draw_line([0, 0], [10, 0])
        svc.controller.get_current_layer_name = lambda: "CEILING"
        svc.draw_line([0, 0], [10, 0])
        svc.draw_line([0, 0], [10, 0], layer="EXPLICIT")
        self.assertEqual(layers, ["WALL", "CEILING", "EXPLICIT"])

    def test_lost_target_needs_explicit_new_or_open(self):
        svc, env = self.make_service()
        attempts, messages = [], []
        svc.controller.is_running = lambda: False
        svc.controller._target_lost = True
        svc.start_cad = lambda: attempts.append("implicit attach")
        async def com(fn, *args):
            return fn(*args)
        async def info(message):
            messages.append(message)
        env["com"] = com
        self.assertFalse(asyncio.run(env["_ensure_running"](NS(info=info))))
        self.assertEqual(attempts, [])
        self.assertIn("new_drawing", messages[-1])

    def test_explicit_new_recovers_lost_target_and_clears_old_session_layer(self):
        svc, env = self.make_service()
        calls = []
        svc.controller.app = None
        svc.controller._target_lost = True
        def start(allow_target_change=False):
            calls.append(allow_target_change)
            svc.controller.app = object()
            return True
        svc.controller.start_cad = start
        svc.controller.new_drawing = lambda: True
        async def com(fn, *args):
            return fn(*args)
        env["com"] = com
        result = asyncio.run(env["new_drawing"](object()))
        self.assertTrue(result.success)
        self.assertEqual(calls, [True])
        self.assertIsNone(svc.drawing_state["current_layer"])


if __name__ == "__main__":
    unittest.main()
