"""Shared MCP configuration with portable paths and explicit CAD selection."""
import copy
import json
import logging
import os
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger("cad_mcp_config")
_CONFIG_PATH = Path(__file__).with_name("config.json")
_PROJECT_ROOT = Path(__file__).resolve().parents[3]

_DEFAULT_CONFIG = {
    "server": {
        "name": "CAD MCP Server",
        "version": "2.0.0",
        "transport": "stdio",
        "host": "127.0.0.1",
        "port": 8000,
    },
    "cad": {"type": "AUTOCAD", "startup_wait_time": 20, "command_delay": 0.5},
    "output": {"directory": "./output", "default_filename": "cad_drawing.dwg"},
}
_CAD_TYPES = {"AUTOCAD", "GCAD", "GSTARCAD", "ZWCAD"}


@lru_cache(maxsize=1)
def get_config() -> dict:
    """Load once; environment overrides also apply when the file is unavailable.

    Relative output paths resolve from this repository, independent of whether
    the client honors its MCP cwd field. This function never creates files.
    """
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8-sig") as stream:
            supplied = json.load(stream)
    except (OSError, ValueError, UnicodeError) as exc:
        logger.warning("Cannot read CAD configuration; using defaults: %s", exc)
        supplied = {}
    if not isinstance(supplied, dict):
        raise ValueError("CAD configuration must be a JSON object")

    config = copy.deepcopy(_DEFAULT_CONFIG)
    for section, values in supplied.items():
        if section in config:
            if not isinstance(values, dict):
                raise ValueError(f"CAD configuration section {section!r} must be an object")
            config[section].update(values)
        else:
            config[section] = values

    cad_type = os.environ.get("DAIHUA_CAD_TYPE", config["cad"]["type"])
    if not isinstance(cad_type, str) or cad_type.upper() not in _CAD_TYPES:
        raise ValueError("Unsupported CAD type. Set DAIHUA_CAD_TYPE to AUTOCAD, GCAD, GSTARCAD, or ZWCAD.")
    config["cad"]["type"] = cad_type.upper()

    output = os.environ.get("DAIHUA_OUTPUT_DIR", config["output"]["directory"])
    if not isinstance(output, str) or not output.strip():
        raise ValueError("CAD output directory must be a non-empty path")
    output_path = Path(os.path.expandvars(output)).expanduser()
    if not output_path.is_absolute():
        output_path = _PROJECT_ROOT / output_path
    config["output"]["directory"] = str(output_path.resolve())
    return config
