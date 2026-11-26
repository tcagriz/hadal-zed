#!/usr/bin/env python3
"""Failure-path tests for the Zed extension package contract."""

import importlib.util
import json
from pathlib import Path
import shutil
import tarfile
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_zed_extension", ROOT / "tests" / "check_extension.py"
)
assert SPEC and SPEC.loader
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class ZedExtensionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="hadal-zed-test-")
        self.root = Path(self.temp.name) / "zed"
        self.root.mkdir()
        for relative in CHECK.PACKAGE_FILES:
            source = ROOT / relative
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

    def tearDown(self):
        self.temp.cleanup()

    def assert_invalid(self, message):
        with self.assertRaisesRegex(CHECK.ZedExtensionError, message):
            manifest = CHECK.validate_manifest(self.root / "extension.toml")
            CHECK.validate_theme(self.root / "themes" / "hadal.json", manifest)
            CHECK.expected_files(self.root)

    def test_current_package_is_valid(self):
        cache = self.root / "tests" / "__pycache__"
        cache.mkdir(parents=True)
        (cache / "stale.pyc").write_bytes(b"not package content")
        manifest = CHECK.validate_manifest(self.root / "extension.toml")
        CHECK.validate_theme(self.root / "themes" / "hadal.json", manifest)
        output = Path(self.temp.name) / "hadal-zed.tar.gz"
        CHECK.package_extension(self.root, output)
        CHECK.inspect_package(self.root, output)
        self.assertNotIn(
            "tests/__pycache__/stale.pyc",
            [str(path.relative_to(self.root)) for path in CHECK.expected_files(self.root)],
        )

    def test_invalid_manifest_fails(self):
        (self.root / "extension.toml").write_text('id = "hadal\\n')
        with self.assertRaisesRegex(CHECK.ZedExtensionError, "invalid"):
            CHECK.validate_manifest(self.root / "extension.toml")

        (self.root / "extension.toml").write_text(
            (ROOT / "extension.toml").read_text().replace('version = "0.1.0"', 'version = "bad"')
        )
        self.assert_invalid("version must be semver")

        (self.root / "extension.toml").write_text(
            (ROOT / "extension.toml").read_text().replace(
                "schema_version = 1", "schema_version = true"
            )
        )
        self.assert_invalid("schema_version must be 1")

    def test_missing_manifest_field_fails(self):
        manifest = (ROOT / "extension.toml").read_text()
        (self.root / "extension.toml").write_text(
            "\n".join(line for line in manifest.splitlines() if not line.startswith("repository ="))
        )
        self.assert_invalid("missing: repository")

    def test_invalid_theme_json_fails(self):
        (self.root / "themes" / "hadal.json").write_text("{")
        with self.assertRaisesRegex(CHECK.ZedExtensionError, "invalid"):
            CHECK.validate_theme(
                self.root / "themes" / "hadal.json",
                CHECK.validate_manifest(self.root / "extension.toml"),
            )

    def test_wrong_theme_schema_fails(self):
        theme = json.loads((self.root / "themes" / "hadal.json").read_text())
        theme["$schema"] = "https://example.invalid/schema.json"
        (self.root / "themes" / "hadal.json").write_text(json.dumps(theme))
        self.assert_invalid("theme schema must be")

    def test_invalid_theme_color_fails(self):
        theme = json.loads((self.root / "themes" / "hadal.json").read_text())
        theme["themes"][0]["style"]["background"] = "not-a-color"
        (self.root / "themes" / "hadal.json").write_text(json.dumps(theme))
        self.assert_invalid("must be #RRGGBB")

    def test_invalid_font_style_and_weight_fail(self):
        theme = json.loads((self.root / "themes" / "hadal.json").read_text())
        style = theme["themes"][0]["style"]["syntax"].copy()
        style["comment"] = {"color": "#384887", "font_style": "garbage"}
        theme["themes"][0]["style"]["syntax"] = style
        (self.root / "themes" / "hadal.json").write_text(json.dumps(theme))
        self.assert_invalid("font_style must be one of")

        theme = json.loads((ROOT / "themes" / "hadal.json").read_text())
        style = theme["themes"][0]["style"]["syntax"].copy()
        style["comment"] = {"color": "#384887", "font_weight": 42}
        theme["themes"][0]["style"]["syntax"] = style
        (self.root / "themes" / "hadal.json").write_text(json.dumps(theme))
        self.assert_invalid("100-step values")

    def test_schema_valid_null_and_background_appearance_values_pass(self):
        theme = json.loads((self.root / "themes" / "hadal.json").read_text())
        theme["themes"][0]["style"]["background"] = None
        theme["themes"][0]["style"]["background.appearance"] = "blurred"
        theme["themes"][0]["style"]["syntax"]["comment"] = {
            "color": None,
            "font_style": None,
            "font_weight": None,
        }
        (self.root / "themes" / "hadal.json").write_text(json.dumps(theme))
        manifest = CHECK.validate_manifest(self.root / "extension.toml")
        CHECK.validate_theme(self.root / "themes" / "hadal.json", manifest)

        theme["themes"][0]["style"]["background.appearance"] = "invalid"
        (self.root / "themes" / "hadal.json").write_text(json.dumps(theme))
        self.assert_invalid("background.appearance must be one of")

    def test_container_shapes_match_zed_schema(self):
        for key, invalid, message in (
            ("syntax", None, "syntax must be an object"),
            ("players", [None], "players\\[0\\] must be an object"),
            ("accents", {}, "accents must be an array"),
        ):
            with self.subTest(key=key):
                theme = json.loads((ROOT / "themes" / "hadal.json").read_text())
                theme["themes"][0]["style"][key] = invalid
                (self.root / "themes" / "hadal.json").write_text(json.dumps(theme))
                self.assert_invalid(message)

        theme = json.loads((ROOT / "themes" / "hadal.json").read_text())
        theme["themes"][0]["style"]["syntax"]["comment"] = {
            "color": "#384887",
            "font_style": {},
        }
        (self.root / "themes" / "hadal.json").write_text(json.dumps(theme))
        self.assert_invalid("font_style must be one of")

    def test_missing_license_fails(self):
        (self.root / "LICENSE").unlink()
        with self.assertRaisesRegex(CHECK.ZedExtensionError, "missing package files"):
            CHECK.expected_files(self.root)

    def test_external_symlink_is_not_packaged(self):
        external = Path(self.temp.name) / "private.txt"
        external.write_text("private")
        link = self.root / "private-link"
        link.symlink_to(external)
        CHECK.package_extension(self.root, Path(self.temp.name) / "package.tar.gz")
        with tarfile.open(Path(self.temp.name) / "package.tar.gz", "r:gz") as archive:
            self.assertNotIn("private-link", archive.getnames())

        (self.root / "README.md").unlink()
        (self.root / "README.md").symlink_to(external)
        with self.assertRaisesRegex(CHECK.ZedExtensionError, "must not be a symlink"):
            CHECK.expected_files(self.root)

    def test_missing_manifest_theme_name_match_fails(self):
        theme = json.loads((self.root / "themes" / "hadal.json").read_text())
        theme["themes"][0]["name"] = "Other"
        (self.root / "themes" / "hadal.json").write_text(json.dumps(theme))
        self.assert_invalid("theme entry name must match")


if __name__ == "__main__":
    unittest.main()
