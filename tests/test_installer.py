"""Ownership, preservation, and no-write behavior; no CAD or network needed."""
import contextlib
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("daihua_installer", Path(__file__).resolve().parents[1] / "scripts" / "install.py")
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="daihua cad test ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repository with spaces 中文 🦁"
        (self.repo / "vendor/cad-mcp/src").mkdir(parents=True)
        (self.repo / "vendor/cad-mcp/src/server.py").write_text("# test server\n", encoding="utf-8")
        for skill in installer.SKILLS:
            folder = self.repo / "skills" / skill
            folder.mkdir(parents=True)
            (folder / "SKILL.md").write_text("---\nname: " + skill + "\n---\nCAD skill\n", encoding="utf-8")
            (folder / "references").mkdir()
            (folder / "references" / "guide.txt").write_text("original guide\n", encoding="utf-8")
        self.config = self.root / "client" / "config.toml"
        self.skills = self.root / "client" / "skills"
        self.addCleanup(patch.stopall)
        patch.object(installer, "ROOT", self.repo).start()
        patch.object(installer, "STATE", self.repo / ".daihua/install-manifest.json").start()

    def run_cli(self, *args, client="codex", skills=True, config=None):
        options = ["--client", client, "--config", str(config or self.config), "--skip-deps"]
        if skills:
            options += ["--skills-dir", str(self.skills)]
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            result = installer.main(options + list(args))
        return result, stream.getvalue()

    def write_config(self, text):
        self.config.parent.mkdir(parents=True, exist_ok=True)
        self.config.write_text(text, encoding="utf-8")

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}

    def test_codex_merge_idempotent_and_backup(self):
        self.write_config('# existing comment\nmodel = "gpt-test"\n[mcp_servers.autocad]\ncommand = "keep.exe"\n[profiles.dev]\nmodel = "other"\n')
        result, output = self.run_cli()
        self.assertEqual(result, 0, output)
        data = tomllib.loads(self.config.read_text(encoding="utf-8"))
        self.assertEqual(data["mcp_servers"]["autocad"], {"command": "keep.exe"})
        self.assertEqual(data["profiles"]["dev"]["model"], "other")
        self.assertEqual(data["mcp_servers"]["daihua-cad"]["cwd"], str(self.repo))
        self.assertTrue(Path(data["mcp_servers"]["daihua-cad"]["args"][1]).is_absolute())
        self.assertIn('# existing comment', self.config.read_text(encoding="utf-8"))
        self.assertEqual(len(list(self.config.parent.glob("config.toml.daihua-backup-*"))), 1)
        before = self.snapshot()
        result, output = self.run_cli()
        self.assertEqual(result, 0, output)
        self.assertEqual(self.snapshot(), before)

    def test_json_clients_merge_preserve_settings(self):
        for client in ("claude", "cursor"):
            with self.subTest(client=client):
                config = self.root / client / "config.json"
                config.parent.mkdir()
                config.write_text(json.dumps({"theme": "dark", "mcpServers": {"autocad": {"command": "existing"}}}), encoding="utf-8")
                result, output = self.run_cli(client=client, config=config)
                self.assertEqual(result, 0, output)
                data = json.loads(config.read_text(encoding="utf-8"))
                self.assertEqual(data["theme"], "dark")
                self.assertEqual(data["mcpServers"]["autocad"]["command"], "existing")
                self.assertEqual(data["mcpServers"]["daihua-cad"], installer.desired_entry())

    def test_generic_default_only_writes_config_and_manifest(self):
        with contextlib.redirect_stdout(io.StringIO()):
            result = installer.main(["--client", "generic", "--skip-deps"])
        self.assertEqual(result, 0)
        output = self.repo / ".daihua/mcp.json"
        self.assertTrue(output.is_file())
        self.assertFalse((self.repo / ".daihua/skills").exists())
        self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["mcpServers"]["daihua-cad"], installer.desired_entry())

    def test_unmanaged_mcp_collision_even_if_identical(self):
        self.write_config('[mcp_servers.daihua-cad]\ncommand = "existing.exe"\n')
        before = self.snapshot()
        result, output = self.run_cli()
        self.assertEqual(result, 1)
        self.assertIn("unmanaged or modified", output)
        self.assertEqual(self.snapshot(), before)

    def test_unmanaged_skill_collision(self):
        target = self.skills / "cad-automation"
        target.mkdir(parents=True)
        (target / "SKILL.md").write_text("user's own skill")
        before = self.snapshot()
        result, output = self.run_cli()
        self.assertEqual(result, 1)
        self.assertIn("not managed", output)
        self.assertEqual(self.snapshot(), before)

    def test_dry_run_writes_nothing(self):
        before = self.snapshot()
        result, output = self.run_cli("--dry-run")
        self.assertEqual(result, 0, output)
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(self.config.parent.exists())
        self.assertFalse((self.repo / ".daihua").exists())
        self.assertFalse((self.repo / ".venv").exists())

    def test_uninstall_removes_only_owned_entry_and_unchanged_skills(self):
        self.write_config('[mcp_servers.autocad]\ncommand = "keep"\n')
        self.assertEqual(self.run_cli()[0], 0)
        runtime = self.repo / ".venv/keep.txt"
        runtime.parent.mkdir()
        runtime.write_text("keep runtime")
        changed = self.skills / "cad-automation/SKILL.md"
        changed.write_text("user edited this file", encoding="utf-8")
        extra = self.skills / "cad-designer/private.txt"
        extra.write_text("user addition")
        result, output = self.run_cli("--uninstall")
        self.assertEqual(result, 0, output)
        data = tomllib.loads(self.config.read_text(encoding="utf-8"))
        self.assertEqual(data["mcp_servers"]["autocad"]["command"], "keep")
        self.assertNotIn("daihua-cad", data["mcp_servers"])
        self.assertEqual(changed.read_text(encoding="utf-8"), "user edited this file")
        self.assertTrue(extra.exists())
        self.assertFalse((self.skills / "cad-designer/SKILL.md").exists())
        self.assertTrue(runtime.exists())
        self.assertTrue((self.repo / "vendor/cad-mcp/src/server.py").exists())
        self.assertEqual(json.loads(installer.STATE.read_text(encoding="utf-8"))["installs"], {})

    def test_uninstall_preserves_modified_configuration(self):
        self.assertEqual(self.run_cli()[0], 0)
        text = self.config.read_text(encoding="utf-8").replace('cwd = ', 'custom = "user changed"\ncwd = ')
        self.config.write_text(text, encoding="utf-8")
        result, output = self.run_cli("--uninstall")
        self.assertEqual(result, 0, output)
        self.assertEqual(self.config.read_text(encoding="utf-8"), text)
        self.assertIn("Preserved modified MCP entry", output)

    def test_uninstall_dry_run_changes_nothing(self):
        self.assertEqual(self.run_cli()[0], 0)
        before = self.snapshot()
        result, output = self.run_cli("--uninstall", "--dry-run")
        self.assertEqual(result, 0, output)
        self.assertEqual(self.snapshot(), before)

    def test_shared_skill_destination_owned_until_last_client_uninstalls(self):
        self.assertEqual(self.run_cli()[0], 0)
        cursor = self.root / "cursor.json"
        self.assertEqual(self.run_cli(client="cursor", config=cursor)[0], 0)
        result, output = self.run_cli("--uninstall")
        self.assertEqual(result, 0, output)
        self.assertTrue((self.skills / "cad-automation/SKILL.md").is_file())
        self.assertIn("daihua-cad", json.loads(cursor.read_text(encoding="utf-8"))["mcpServers"])
        self.assertEqual(self.run_cli("--uninstall", client="cursor", config=cursor)[0], 0)
        self.assertFalse((self.skills / "cad-automation").exists())

    def test_install_update_preserves_local_edits(self):
        self.assertEqual(self.run_cli()[0], 0)
        target = self.skills / "cad-automation/SKILL.md"
        target.write_text("local edit")
        before = self.snapshot()
        result, output = self.run_cli()
        self.assertEqual(result, 1)
        self.assertIn("local changes", output)
        self.assertEqual(self.snapshot(), before)

    def test_bundle_update_replaces_owned_and_retires_unchanged_file(self):
        self.assertEqual(self.run_cli()[0], 0)
        (self.repo / "skills/cad-automation/SKILL.md").write_text("new bundle")
        (self.repo / "skills/cad-designer/references/guide.txt").unlink()
        result, output = self.run_cli()
        self.assertEqual(result, 0, output)
        self.assertEqual((self.skills / "cad-automation/SKILL.md").read_text(encoding="utf-8"), "new bundle")
        self.assertFalse((self.skills / "cad-designer/references/guide.txt").exists())

    def test_rejects_non_object_json_and_malformed_toml_without_writing(self):
        for client, text in (("cursor", "[]"), ("cursor", '{"mcpServers": []}'), ("codex", "[broken")):
            with self.subTest(client=client, text=text):
                self.write_config(text)
                before = self.snapshot()
                result, output = self.run_cli(client=client)
                self.assertEqual(result, 1)
                self.assertEqual(self.snapshot(), before)

    def test_quoted_managed_toml_key_and_unrelated_tables_survive(self):
        self.assertEqual(self.run_cli()[0], 0)
        text = self.config.read_text(encoding="utf-8").replace('[mcp_servers.daihua-cad]', '[mcp_servers."daihua-cad"]')
        self.config.write_text(text + '\n[profiles.work]\nmodel = "keep"\n', encoding="utf-8")
        result, output = self.run_cli()
        self.assertEqual(result, 0, output)
        self.assertEqual(tomllib.loads(self.config.read_text(encoding="utf-8"))["profiles"]["work"]["model"], "keep")

    def test_reject_different_skill_target_for_managed_config(self):
        self.assertEqual(self.run_cli()[0], 0)
        before = self.snapshot()
        result, output = self.run_cli("--skills-dir", str(self.root / "new-skills"))
        self.assertEqual(result, 1)
        self.assertEqual(self.snapshot(), before)

    def test_codex_uses_agents_skills_and_respects_codex_home(self):
        args = type("Options", (), {"client": "codex", "config": None, "skills_dir": None})()
        custom = str(self.root / "custom-codex")
        with patch.dict(os.environ, {"CODEX_HOME": custom}):
            config, skills = installer.locations(args)
        self.assertEqual(config, (Path(custom) / "config.toml").resolve())
        self.assertEqual(skills, (Path.home() / ".agents/skills").resolve())

    def test_check_does_not_write_or_start_cad(self):
        before = self.snapshot()
        result, output = self.run_cli("--check")
        self.assertEqual(result, 1)
        self.assertIn("missing runtime interpreter", output)
        self.assertEqual(self.snapshot(), before)


    def test_null_json_mcp_entry_is_an_unmanaged_collision(self):
        self.write_config('{"mcpServers": {"daihua-cad": null}, "keep": true}')
        before = self.snapshot()
        result, output = self.run_cli(client="cursor")
        self.assertEqual(result, 1)
        self.assertIn("unmanaged or modified", output)
        self.assertEqual(self.snapshot(), before)

    def test_dry_run_does_not_attempt_dependency_setup(self):
        before = self.snapshot()
        with patch.object(installer, "dependencies") as setup:
            with contextlib.redirect_stdout(io.StringIO()):
                result = installer.main(["--config", str(self.config), "--skills-dir", str(self.skills), "--dry-run"])
        self.assertEqual(result, 0)
        setup.assert_not_called()
        self.assertEqual(self.snapshot(), before)

    def test_replaced_skill_subdirectory_symlink_is_never_followed(self):
        self.assertEqual(self.run_cli()[0], 0)
        reference = self.skills / "cad-automation/references"
        (reference / "guide.txt").unlink()
        reference.rmdir()
        external = self.root / "external"
        external.mkdir()
        protected = external / "guide.txt"
        protected.write_text("original guide\n", encoding="utf-8")
        try:
            os.symlink(external, reference, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"Directory symlinks unavailable: {exc}")
        result, output = self.run_cli()
        self.assertEqual(result, 1)
        self.assertIn("symbolic link", output)
        self.assertEqual(self.run_cli("--uninstall")[0], 0)
        self.assertEqual(protected.read_text(encoding="utf-8"), "original guide\n")


if __name__ == "__main__":
    unittest.main()
