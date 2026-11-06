#!/usr/bin/env python3
"""Install Daihua CAD's local MCP server and agent skills without starting CAD."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
MCP_ID = "daihua-cad"
STATE = ROOT / ".daihua" / "install-manifest.json"
SKILLS = ("cad-automation", "cad-designer")


class InstallError(Exception):
    pass


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def digest_entry(value):
    return digest_bytes(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode())


def absolute(value):
    return Path(os.path.expandvars(str(value))).expanduser().resolve()


def read_text(path):
    return path.read_text(encoding="utf-8-sig") if path.exists() else ""


def load_state():
    if not STATE.exists():
        return {"version": 1, "installs": {}}
    try:
        state = json.loads(read_text(STATE))
        if not isinstance(state, dict) or state.get("version") != 1 or not isinstance(state.get("installs"), dict):
            raise ValueError("unknown manifest format")
        return state
    except (ValueError, OSError) as exc:
        raise InstallError(f"Cannot read installer ownership manifest {STATE}: {exc}") from exc


def locations(args):
    home = Path.home()
    codex = absolute(os.environ.get("CODEX_HOME", str(home / ".codex")))
    defaults = {
        "codex": (codex / "config.toml", home / ".agents" / "skills"),
        "claude": (home / ".claude.json", home / ".claude" / "skills"),
        "cursor": (home / ".cursor" / "mcp.json", home / ".cursor" / "skills"),
        "generic": (ROOT / ".daihua" / "mcp.json", None),
    }
    config, skills = defaults[args.client]
    config = absolute(args.config or config)
    skills = absolute(args.skills_dir) if args.skills_dir else (absolute(skills) if skills else None)
    return config, skills


def install_key(client, config, skills):
    return json.dumps([client, str(config), str(skills) if skills else None], ensure_ascii=False)


def config_read(path, client):
    content = read_text(path)
    try:
        data = tomllib.loads(content) if client == "codex" else (json.loads(content) if content.strip() else {})
    except (ValueError, tomllib.TOMLDecodeError) as exc:
        raise InstallError(f"Invalid {client} configuration {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise InstallError(f"Configuration must be an object: {path}")
    field = "mcp_servers" if client == "codex" else "mcpServers"
    servers = data.get(field, {})
    if not isinstance(servers, dict):
        raise InstallError(f"{field} must be an object in {path}")
    return content, data, servers.get(MCP_ID)


def config_render(content, data, client, entry):
    field = "mcp_servers" if client == "codex" else "mcpServers"
    updated = copy.deepcopy(data)
    if entry is None:
        updated.get(field, {}).pop(MCP_ID, None)
    else:
        updated.setdefault(field, {})[MCP_ID] = entry
    if client != "codex":
        return json.dumps(updated, ensure_ascii=False, indent=2) + "\n"
    # Replace only our standalone TOML table. Verify all other parsed values survive.
    header = re.compile(r"(?m)^\s*\[mcp_servers\.(?:daihua-cad|\"daihua-cad\"|'daihua-cad')\]\s*(?:#[^\n]*)?$")
    match = header.search(content)
    if match:
        tail = content[match.end():]
        following = re.search(r"(?m)^\s*\[", tail)
        end = match.end() + following.start() if following else len(content)
        content = content[:match.start()] + content[end:]
    elif MCP_ID in data.get(field, {}):
        raise InstallError("The existing daihua-cad TOML entry is not a standalone table; preserve it and remove or rename it manually before installing.")
    if entry is not None:
        section = "[mcp_servers.daihua-cad]\ncommand = " + json.dumps(entry["command"], ensure_ascii=False) + "\nargs = " + json.dumps(entry["args"], ensure_ascii=False) + "\ncwd = " + json.dumps(entry["cwd"], ensure_ascii=False) + "\n"
        content = content.rstrip() + ("\n\n" if content.strip() else "") + section
    try:
        actual = tomllib.loads(content)
    except tomllib.TOMLDecodeError as exc:
        raise InstallError(f"Refusing to rewrite TOML because the result cannot be parsed: {exc}") from exc
    # Leaving an empty parent table is harmless and keeps unrelated table layout intact.
    expected = copy.deepcopy(updated)
    if actual.get(field) == {} and field not in expected:
        expected[field] = {}
    if field in expected and expected[field] == {} and field not in actual:
        actual[field] = {}
    if actual != expected:
        raise InstallError("Refusing to rewrite TOML because unrelated configuration would change. Use a separate --config file or edit the daihua-cad table manually.")
    return content


def write_file(path, data, backup=False):
    encoded = data.encode("utf-8") if isinstance(data, str) else data
    if path.exists() and path.read_bytes() == encoded:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    if backup and path.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        snapshot = path.with_name(path.name + ".daihua-backup-" + stamp)
        shutil.copy2(path, snapshot)
        print(f"Backup: {snapshot}")
    temporary = path.with_name(path.name + ".daihua-tmp")
    temporary.write_bytes(encoded)
    temporary.replace(path)
    return True


def python_path():
    folder = ROOT / ".venv"
    return folder / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def desired_entry():
    return {"command": str(python_path()), "args": ["-u", str(ROOT / "vendor" / "cad-mcp" / "src" / "server.py"), "--transport", "stdio"], "cwd": str(ROOT)}


def source_files():
    result = {}
    for name in SKILLS:
        directory = ROOT / "skills" / name
        if not (directory / "SKILL.md").is_file():
            raise InstallError(f"Missing bundled skill: {directory / 'SKILL.md'}. Clone or download the complete repository.")
        files = {}
        for source in directory.rglob("*"):
            relative = source.relative_to(directory)
            if any(part in ("__pycache__", ".git") for part in relative.parts) or source.suffix == ".pyc":
                continue
            if source.is_symlink():
                raise InstallError(f"Bundled skill contains an unsupported symbolic link: {source}")
            if source.is_file():
                files[str(relative)] = source
        result[name] = files
    return result


def all_owned_files(state, exclude_key=None):
    result = {}
    for key, record in state["installs"].items():
        if key != exclude_key:
            result.update(record.get("files", {}))
    return result


def safe_skill_path(path, skills):
    """Never follow a replaced managed directory outside the chosen skill root."""
    try:
        path.relative_to(skills)
    except ValueError:
        return False
    current = path
    while current != skills:
        if current.is_symlink():
            return False
        current = current.parent
    return True


def preflight_skills(sources, skills, previous, state, key):
    files = {}
    previous_files = previous.get("files", {}) if previous else {}
    others = all_owned_files(state, key)
    if skills is None:
        return files
    for name, bundle in sources.items():
        target = skills / name
        owned_directory = any(Path(p).parent == target or target in Path(p).parents for p in list(previous_files) + list(others))
        if target.exists() and not owned_directory:
            raise InstallError(f"Skill directory already exists and is not managed by Daihua CAD: {target}. Choose --skills-dir with an empty destination or move the existing skill yourself.")
        if target.is_symlink():
            raise InstallError(f"Refusing to write through a skill-directory symbolic link: {target}")
        for relative, source in bundle.items():
            destination = target / relative
            expected = digest_bytes(source.read_bytes())
            if not safe_skill_path(destination, skills):
                raise InstallError(f"Refusing a skill destination through a symbolic link: {destination}")
            if destination.exists():
                if not destination.is_file() or destination.is_symlink():
                    raise InstallError(f"Skill destination is not a regular file: {destination}")
                existing = digest_bytes(destination.read_bytes())
                owned_hash = previous_files.get(str(destination), others.get(str(destination)))
                if owned_hash is None or existing != owned_hash:
                    raise InstallError(f"Skill has local changes or is unmanaged: {destination}. Keep your changes and select another --skills-dir.")
            files[str(destination)] = expected
    return files


def dependencies():
    requirements = ROOT / "requirements-runtime.txt"
    if not requirements.is_file():
        raise InstallError(f"Missing {requirements}; use a complete repository checkout.")
    interpreter = python_path()
    try:
        if not interpreter.is_file():
            subprocess.run([sys.executable, "-m", "venv", str(ROOT / ".venv")], check=True)
        subprocess.run([str(interpreter), "-m", "pip", "install", "-r", str(requirements)], check=True)
    except (subprocess.CalledProcessError, OSError) as exc:
        raise InstallError("Dependency setup failed. Ensure Python 3.11+ includes venv and pip, and network access to your Python package index works; then rerun install.ps1. No agent configuration has been written.") from exc


def prune_empty(path, stop):
    while path != stop and stop in path.parents:
        try:
            path.rmdir()
        except OSError:
            break
        path = path.parent


def uninstall(args, config, skills, state, key):
    previous = state["installs"].get(key)
    if not previous:
        print("No managed installation found for this client and destination; nothing was changed.")
        return 0
    content, data, current = config_read(config, args.client)
    new_content = None
    if current is not None and digest_entry(current) == previous.get("entry_hash"):
        new_content = config_render(content, data, args.client, None)
    elif MCP_ID in data.get("mcp_servers" if args.client == "codex" else "mcpServers", {}):
        print(f"Preserved modified MCP entry: {config}")
    others = all_owned_files(state, key)
    removable = []
    for value, expected in previous.get("files", {}).items():
        path = Path(value)
        if value in others:
            continue
        if skills is None or not safe_skill_path(path, skills):
            print(f"Preserved unsafe or moved skill path: {path}")
            continue
        if path.is_file() and not path.is_symlink() and digest_bytes(path.read_bytes()) == expected:
            removable.append(path)
        elif path.exists():
            print(f"Preserved modified skill file: {path}")
    if args.dry_run:
        print(f"Dry run: would remove {len(removable)} unchanged skill files and " + ("the unchanged MCP entry." if new_content is not None else "no MCP entry."))
        return 0
    if new_content is not None:
        write_file(config, new_content, backup=True)
    for path in removable:
        path.unlink()
        if skills:
            prune_empty(path.parent, skills)
    state["installs"].pop(key)
    write_file(STATE, json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    print("Uninstalled managed configuration and unchanged skill files. Repository and .venv were retained.")
    return 0


def check(args, config, skills, state, key):
    problems = []
    server = ROOT / "vendor" / "cad-mcp" / "src" / "server.py"
    if not server.is_file():
        problems.append(f"missing MCP server: {server}")
    if not python_path().is_file():
        problems.append(f"missing runtime interpreter: {python_path()}")
    else:
        result = subprocess.run([str(python_path()), "-c", "import importlib.util, sys; sys.exit(0 if all(importlib.util.find_spec(m) for m in ('mcp', 'win32com')) else 1)"], capture_output=True, text=True)
        if result.returncode:
            problems.append("runtime dependencies are missing; run installation without --skip-deps")
    _, _, current = config_read(config, args.client)
    record = state["installs"].get(key)
    if not record:
        problems.append("no managed installation for this client and destination")
    if current != desired_entry():
        problems.append(f"MCP entry is absent or differs from this repository: {config}")
    if record:
        for value, expected in record.get("files", {}).items():
            path = Path(value)
            if not path.is_file() or digest_bytes(path.read_bytes()) != expected:
                problems.append(f"missing or modified skill file: {path}")
    print(f"Client: {args.client}\nConfiguration: {config}\nSkills: {skills or '(generic: no skill copy)'}")
    if os.name != "nt":
        problems.append("CAD COM runtime requires Windows and a locally installed supported CAD application")
    for problem in problems:
        print(f"CHECK: {problem}")
    if not problems:
        print("Installation files and runtime imports look ready. CAD was not started; CAD/COM availability must be checked when you first connect.")
    return 1 if problems else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", choices=("codex", "claude", "cursor", "generic"), default="codex")
    parser.add_argument("--config", help="Override the client configuration path")
    parser.add_argument("--skills-dir", help="Override the agent skill directory")
    parser.add_argument("--skip-deps", action="store_true", help="Skip .venv and pip setup; useful for offline preparation and tests")
    parser.add_argument("--dry-run", action="store_true", help="Show planned changes without writing any file")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true", help="Diagnose installed files and runtime imports without writing")
    modes.add_argument("--uninstall", action="store_true", help="Remove only unchanged files and configuration owned by this installer")
    args = parser.parse_args(argv)
    if sys.version_info < (3, 11):
        parser.error("Python 3.11 or newer is required")
    try:
        config, skills = locations(args)
        state = load_state()
        key = install_key(args.client, config, skills)
        if args.uninstall:
            return uninstall(args, config, skills, state, key)
        if args.check:
            return check(args, config, skills, state, key)
        if os.name != "nt" and not args.skip_deps and not args.dry_run:
            raise InstallError("Daihua CAD requires Windows for CAD COM automation. On other platforms you may inspect with --dry-run or prepare configuration with --skip-deps.")
        server = ROOT / "vendor" / "cad-mcp" / "src" / "server.py"
        if not server.is_file():
            raise InstallError(f"Missing MCP server: {server}. Clone the complete repository.")
        sources = source_files() if skills else {}
        previous = state["installs"].get(key)
        content, data, current = config_read(config, args.client)
        field = "mcp_servers" if args.client == "codex" else "mcpServers"
        if MCP_ID in data.get(field, {}):
            if not previous or digest_entry(current) != previous.get("entry_hash"):
                raise InstallError(f"MCP entry '{MCP_ID}' already exists and is unmanaged or modified: {config}. Choose another --config destination or rename the existing entry yourself.")
        # A second install record may never take over another record's config entry.
        for other_key, record in state["installs"].items():
            if other_key != key and record.get("config") == str(config):
                raise InstallError(f"This configuration is already managed with different client/skill settings: {config}. Reuse the original options or uninstall that installation first.")
        files = preflight_skills(sources, skills, previous, state, key)
        entry = desired_entry()
        rendered = config_render(content, data, args.client, entry)
        print(f"Client: {args.client}\nConfiguration: {config}\nSkills: {skills or '(generic: no skill copy)'}\nRuntime: {python_path()}")
        if args.dry_run:
            print(f"Dry run: would configure '{MCP_ID}' and install {len(files)} skill files. No files written; dependencies were not installed.")
            return 0
        if not args.skip_deps:
            dependencies()
        write_file(config, rendered, backup=True)
        if skills:
            for name, bundle in sources.items():
                for relative, source in bundle.items():
                    write_file(skills / name / relative, source.read_bytes())
        # Retire files removed by an updated bundle only when they remain unchanged.
        for value, expected in (previous or {}).get("files", {}).items():
            if value not in files and value not in all_owned_files(state, key):
                path = Path(value)
                if skills and safe_skill_path(path, skills) and path.is_file() and digest_bytes(path.read_bytes()) == expected:
                    path.unlink()
                    if skills:
                        prune_empty(path.parent, skills)
        state["installs"][key] = {"client": args.client, "config": str(config), "skills_dir": str(skills) if skills else None, "entry_hash": digest_entry(entry), "files": files}
        write_file(STATE, json.dumps(state, ensure_ascii=False, indent=2) + "\n")
        if args.skip_deps:
            print("Dependencies skipped: this configuration will work only after .venv and requirements-runtime.txt are installed.")
        print("Daihua CAD configured. Restart or reload your agent client, then ask it to connect to your local CAD application.")
        return 0
    except (InstallError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
