#!/usr/bin/env python3
"""Validate and package the Hadal Zed extension."""

from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import re
import tarfile
import tomllib


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_MANIFEST_KEYS = {
    "id",
    "name",
    "version",
    "schema_version",
    "authors",
    "description",
    "repository",
}
SEMVER = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")
COLOR = re.compile(r"#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?")
THEME_SCHEMA = "https://zed.dev/schema/themes/v0.2.0.json"
FONT_STYLES = {"normal", "italic", "oblique"}
FONT_WEIGHTS = set(range(100, 1000, 100))
BACKGROUND_APPEARANCES = {"opaque", "transparent", "blurred"}
PACKAGE_FILES = (
    ".github/CODEOWNERS",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/copilot-instructions.md",
    ".github/dependabot.yml",
    ".github/pull_request_template.md",
    ".github/workflows/check.yml",
    "LICENSE",
    "README.md",
    "SECURITY.md",
    "extension.toml",
    "tests/check_extension.py",
    "tests/check_extension_test.py",
    "themes/hadal.json",
)


class ZedExtensionError(ValueError):
    """The Zed extension does not satisfy its package contract."""


def require_string(manifest: dict, key: str) -> str:
    value = manifest.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ZedExtensionError(f"extension.toml: {key} must be a non-empty string")
    return value


def validate_manifest(path: Path) -> dict:
    try:
        manifest = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as error:
        raise ZedExtensionError(f"extension.toml is invalid: {error}") from error

    missing = REQUIRED_MANIFEST_KEYS - set(manifest)
    if missing:
        raise ZedExtensionError(
            "extension.toml missing: " + ", ".join(sorted(missing))
        )
    unexpected = set(manifest) - REQUIRED_MANIFEST_KEYS
    if unexpected:
        raise ZedExtensionError(
            "extension.toml unexpected: " + ", ".join(sorted(unexpected))
        )

    for key in ("id", "name", "description", "repository"):
        require_string(manifest, key)
    if SEMVER.fullmatch(manifest["version"]) is None:
        raise ZedExtensionError("extension.toml: version must be semver X.Y.Z")
    if (
        not isinstance(manifest["schema_version"], int)
        or isinstance(manifest["schema_version"], bool)
        or manifest["schema_version"] != 1
    ):
        raise ZedExtensionError("extension.toml: schema_version must be 1")
    authors = manifest["authors"]
    if (
        not isinstance(authors, list)
        or not authors
        or any(not isinstance(author, str) or not author.strip() for author in authors)
    ):
        raise ZedExtensionError("extension.toml: authors must be a non-empty string list")
    if manifest["id"] != "hadal":
        raise ZedExtensionError("extension.toml: id must remain hadal")
    if manifest["repository"] != "https://github.com/tcagriz/hadal-zed":
        raise ZedExtensionError(
            "extension.toml: repository must point to tcagriz/hadal-zed"
        )
    return manifest


def validate_color(value, path: str) -> None:
    if not isinstance(value, str) or COLOR.fullmatch(value) is None:
        raise ZedExtensionError(f"{path} must be #RRGGBB or #RRGGBBAA")


def validate_nullable_color(value, path: str) -> None:
    if value is not None:
        validate_color(value, path)


def validate_highlight(value, path: str) -> None:
    if not isinstance(value, dict):
        raise ZedExtensionError(f"{path} must be an object")
    allowed = {"background_color", "color", "font_style", "font_weight"}
    unexpected = set(value) - allowed
    if unexpected:
        raise ZedExtensionError(
            f"{path} has unexpected keys: {', '.join(sorted(unexpected))}"
        )
    for key in ("background_color", "color"):
        if key in value:
            validate_nullable_color(value[key], f"{path}.{key}")
    if "font_style" in value and value["font_style"] is not None:
        font_style = value["font_style"]
        if not isinstance(font_style, str) or font_style not in FONT_STYLES:
            raise ZedExtensionError(
                f"{path}.font_style must be one of: "
                f"{', '.join(sorted(FONT_STYLES))}"
            )
    if "font_weight" in value and value["font_weight"] is not None:
        weight = value["font_weight"]
        if (
            not isinstance(weight, int)
            or isinstance(weight, bool)
            or weight not in FONT_WEIGHTS
        ):
            raise ZedExtensionError(
                f"{path}.font_weight must be an integer in 100-step values "
                "from 100 to 900"
            )


def validate_style(style: dict) -> None:
    for key, value in style.items():
        path = f"themes[0].style.{key}"
        if key == "background.appearance":
            if value is not None and value not in BACKGROUND_APPEARANCES:
                raise ZedExtensionError(
                    f"{path} must be one of: "
                    f"{', '.join(sorted(BACKGROUND_APPEARANCES))}"
                )
        elif key == "accents":
            if not isinstance(value, list):
                raise ZedExtensionError(f"{path} must be an array")
            for index, color in enumerate(value):
                validate_nullable_color(color, f"{path}[{index}]")
        elif key == "syntax":
            if not isinstance(value, dict):
                raise ZedExtensionError(f"{path} must be an object")
            for syntax_name, highlight in value.items():
                validate_highlight(highlight, f"{path}.{syntax_name}")
        elif key == "players":
            if not isinstance(value, list):
                raise ZedExtensionError(f"{path} must be an array")
            for index, player in enumerate(value):
                if not isinstance(player, dict):
                    raise ZedExtensionError(f"{path}[{index}] must be an object")
                unexpected = set(player) - {"background", "cursor", "selection"}
                if unexpected:
                    raise ZedExtensionError(
                        f"{path}[{index}] has unexpected keys: "
                        f"{', '.join(sorted(unexpected))}"
                    )
                for field, color in player.items():
                    validate_nullable_color(color, f"{path}[{index}].{field}")
        else:
            validate_nullable_color(value, path)


def validate_theme(path: Path, manifest: dict) -> dict:
    try:
        theme = json.loads(path.read_text())
    except json.JSONDecodeError as error:
        raise ZedExtensionError(f"theme JSON is invalid: {error}") from error

    if theme.get("$schema") != THEME_SCHEMA:
        raise ZedExtensionError(f"theme schema must be {THEME_SCHEMA}")
    if theme.get("name") != manifest["name"]:
        raise ZedExtensionError("theme name must match extension.toml")
    if not isinstance(theme.get("author"), str) or not theme["author"].strip():
        raise ZedExtensionError("theme author must be a non-empty string")
    themes = theme.get("themes")
    if not isinstance(themes, list) or len(themes) != 1:
        raise ZedExtensionError("theme file must contain exactly one theme")

    entry = themes[0]
    if entry.get("name") != manifest["name"]:
        raise ZedExtensionError("theme entry name must match extension.toml")
    if entry.get("appearance") != "dark":
        raise ZedExtensionError("theme appearance must be dark")
    style = entry.get("style")
    if not isinstance(style, dict) or not style:
        raise ZedExtensionError("theme style must be a non-empty object")
    validate_style(style)
    return theme


def expected_files(root: Path) -> list[Path]:
    required = {root / relative for relative in PACKAGE_FILES}
    missing = [path for path in required if not path.is_file()]
    if missing:
        raise ZedExtensionError(
            "missing package files: "
            + ", ".join(str(path.relative_to(root)) for path in missing)
        )
    files = []
    for relative in PACKAGE_FILES:
        path = root / relative
        if path.is_symlink():
            raise ZedExtensionError(f"package file must not be a symlink: {relative}")
        try:
            path.resolve().relative_to(root.resolve())
        except ValueError as error:
            raise ZedExtensionError(
                f"package file escapes the Zed package root: {relative}"
            ) from error
        files.append(path)
    return sorted(files)


def package_extension(root: Path, output: Path) -> None:
    files = expected_files(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    with tarfile.open(output, "w:gz") as archive:
        for path in files:
            relative = path.relative_to(root)
            data = path.read_bytes()
            member = tarfile.TarInfo(str(relative))
            member.size = len(data)
            member.mode = 0o644
            member.mtime = 0
            archive.addfile(member, io.BytesIO(data))


def inspect_package(root: Path, output: Path) -> None:
    with tarfile.open(output, "r:gz") as archive:
        members = {member.name: member for member in archive.getmembers()}
    expected = {str(path.relative_to(root)) for path in expected_files(root)}
    if set(members) != expected:
        raise ZedExtensionError(
            f"packaged files differ: missing={sorted(expected - set(members))}, "
            f"extra={sorted(set(members) - expected)}"
        )
    for member in members.values():
        if member.name.startswith("/") or ".." in Path(member.name).parts:
            raise ZedExtensionError(f"unsafe packaged path: {member.name}")
        if not member.isfile():
            raise ZedExtensionError(f"unsafe packaged member type: {member.name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--package", type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    manifest = validate_manifest(root / "extension.toml")
    validate_theme(root / "themes" / "hadal.json", manifest)
    expected_files(root)
    if args.package:
        package_extension(root, args.package)
        inspect_package(root, args.package)
    print(
        f"validated {manifest['id']} {manifest['version']} "
        f"with schema version {manifest['schema_version']}"
    )


if __name__ == "__main__":
    try:
        main()
    except (OSError, ZedExtensionError) as error:
        raise SystemExit(f"Zed extension error: {error}") from error
