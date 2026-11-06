"""Check MCP protocol; --connect also queries CAD layers.
Default mode does not start CAD. Run with the installed .venv Python.
"""
import argparse
import asyncio
from datetime import timedelta
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

async def verify(args):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    python = Path(args.python) if args.python else ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.is_file():
        raise RuntimeError("Runtime missing. Run install.ps1 or pass --python PATH.")
    output = ROOT / "output"
    output.mkdir(exist_ok=True)
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    params = StdioServerParameters(command=str(python), args=["-u", str(ROOT / "vendor/cad-mcp/src/server.py"), "--transport", "stdio"], cwd=str(ROOT), env=env)
    with (output / "mcp-verification.log").open("w", encoding="utf-8") as log:
        async with stdio_client(params, errlog=log) as (read, send):
            async with ClientSession(read, send, read_timeout_seconds=timedelta(seconds=120)) as session:
                info = await session.initialize()
                result = await session.list_tools()
                names = {tool.name for tool in result.tools}
                required = {"list_layers", "list_entities", "draw_line", "save_drawing", "new_drawing"}
                if not required <= names:
                    raise RuntimeError("Missing MCP tools: " + str(sorted(required - names)))
                report = {"passed": True, "server": info.serverInfo.model_dump(mode="json"), "tool_count": len(names), "cad_connected": False}
                if args.connect:
                    layers = await session.call_tool("list_layers", {})
                    data = layers.structuredContent
                    if data is None:
                        for content in layers.content:
                            if content.type == "text":
                                try:
                                    data = json.loads(content.text)
                                    break
                                except ValueError:
                                    pass
                    if layers.isError or not isinstance(data, dict) or not data.get("success"):
                        raise RuntimeError("CAD layer query failed; inspect output/mcp-verification.log")
                    report["cad_connected"] = True
                    report["layer_count"] = len(data.get("layers", []))
    (output / "mcp-verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--connect", action="store_true", help="Start/attach CAD and query layers. No existing geometry is edited.")
    parser.add_argument("--python", help="MCP subprocess Python; default: repository .venv")
    args = parser.parse_args()
    if sys.platform != "win32":
        parser.exit(1, "The bundled COM MCP requires Windows. Use examples/offline_plate.py for cross-platform DXF.\n")
    try:
        asyncio.run(asyncio.wait_for(verify(args), timeout=180))
    except Exception as exc:
        parser.exit(1, f"Verification failed: {exc}\n")
