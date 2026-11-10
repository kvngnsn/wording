#!/usr/bin/env python3
"""Validate, install, or package the six Wording skills without dependencies."""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from urllib.parse import unquote, urlparse
import zipfile

NAMES = tuple("wording-" + part for part in (
    "analyze", "correspond", "edit", "explain", "instruct", "persuade"
))
PROVIDERS = {"codex": ".agents", "claude": ".claude"}
ROOT = Path(__file__).resolve().parent.parent


class SkillError(ValueError):
    pass


def scalar(value, label):
    """Parse string scalars from the package's deliberately small YAML subset."""
    if not value:
        raise SkillError(f"{label}: empty value")
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise SkillError(f"{label}: invalid double-quoted string") from exc
        if not isinstance(parsed, str):
            raise SkillError(f"{label}: expected a string")
        return parsed
    if value.startswith("'"):
        if not value.endswith("'") or len(value) < 2:
            raise SkillError(f"{label}: invalid single-quoted string")
        inner = value[1:-1]
        if "'" in inner.replace("''", ""):
            raise SkillError(f"{label}: escape single quotes by doubling them")
        return inner.replace("''", "'")
    if (value.lower() in {"true", "false", "null", "~", "yes", "no"}
            or re.fullmatch(r"[-+]?\d+(?:\.\d+)?", value)
            or value.startswith(("[", "{", "&", "*", "!"))
            or ": " in value or " #" in value):
        raise SkillError(f"{label}: use a quoted string for this YAML value")
    return value


def frontmatter(text, label):
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise SkillError(f"{label}: missing YAML frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise SkillError(f"{label}: unclosed YAML frontmatter") from exc
    values = {}
    i = 1
    while i < end:
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        match = re.fullmatch(r"(name|description):\s*(.*)", line)
        if not match:
            raise SkillError(f"{label}: only top-level name and description are supported")
        key, value = match.groups()
        if key in values:
            raise SkillError(f"{label}: duplicate {key}")
        i += 1
        if value in {">", ">-", "|", "|-"}:
            block = []
            while i < end and (not lines[i].strip() or lines[i].startswith(" ")):
                block.append(lines[i].strip())
                i += 1
            value = (" " if value.startswith(">") else "\n").join(block).strip()
        else:
            value = scalar(value.strip(), f"{label}/{key}")
        values[key] = value
    if set(values) != {"name", "description"}:
        raise SkillError(f"{label}: name and description are both required")
    return values, "\n".join(lines[end + 1:]).strip()


def skill_files(folder):
    files = []
    for path in sorted(folder.rglob("*")):
        if path.is_symlink():
            raise SkillError(f"{folder.name}: symlink inside skill: {path.relative_to(folder)}")
        if path.is_file() and path.name != ".DS_Store" and "__pycache__" not in path.parts:
            files.append(path)
    return files


def validate_skill(folder):
    manifest = folder / "SKILL.md"
    if not manifest.is_file():
        raise SkillError(f"{folder.name}: SKILL.md is missing")
    text = manifest.read_text(encoding="utf-8")
    if len([p for p in folder.iterdir() if p.name.lower() == "skill.md"]) != 1:
        raise SkillError(f"{folder.name}: exactly one SKILL.md manifest is allowed")
    meta, body = frontmatter(text, folder.name)
    name = meta["name"]
    if (not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)
            or len(name) > 64 or name != folder.name):
        raise SkillError(f"{folder.name}: invalid name or folder/name mismatch")
    if not 1 <= len(meta["description"]) <= 200:
        raise SkillError(f"{name}: description must contain 1–200 characters")
    if not body:
        raise SkillError(f"{name}: instructions are empty")
    if re.search(r"\b(?:TODO|FIXME|TBD)\b|lorem ipsum|\[\s*(?:insert|replace)\b", body, re.I):
        raise SkillError(f"{name}: unfinished scaffold found")
    for ref in re.findall(r"\]\(([^)]+)\)", body):
        target = ref.split(" ", 1)[0].strip("<>")
        if not target or target.startswith("#") or urlparse(target).scheme:
            continue
        target = unquote(target.split("#", 1)[0])
        resolved = (folder / target).resolve()
        if not resolved.is_relative_to(folder.resolve()) or not resolved.exists():
            raise SkillError(f"{name}: missing or escaping local reference: {target}")
    skill_files(folder)
    return meta


def sources(root):
    result = []
    for name in NAMES:
        folder = root / "skills" / name
        validate_skill(folder)
        result.append(folder.resolve())
    return result


def destinations(root, scope, home, provider):
    base = root if scope == "project" else home
    chosen = PROVIDERS if provider == "both" else {provider: PROVIDERS[provider]}
    return [base / dirname / "skills" for dirname in chosen.values()]


def check_parents(parent, base):
    """Do not let hidden configuration-directory symlinks redirect an install."""
    path = parent
    while path != base:
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            raise SkillError(f"Destination parent is not a real directory: {path}")
        path = path.parent


def install(root, scope="project", home=None, provider="both", apply=False, copy=False):
    root = Path(root).resolve()
    home = Path(home or Path.home()).resolve()
    srcs = sources(root)
    base = root if scope == "project" else home
    plan = []
    for directory in destinations(root, scope, home, provider):
        check_parents(directory, base)
        for src in srcs:
            dest = directory / src.name
            if dest.is_symlink() and dest.resolve() == src:
                plan.append(("unchanged", src, dest))
            elif os.path.lexists(dest):
                raise SkillError(f"Collision; nothing overwritten: {dest}")
            else:
                plan.append(("copy" if copy else "link", src, dest))
    # Every source and destination is checked before creating any destination.
    for action, src, dest in plan:
        if apply and action != "unchanged":
            dest.parent.mkdir(parents=True, exist_ok=True)
            if action == "copy":
                shutil.copytree(src, dest, symlinks=False)
            else:
                # Creating a symlink is atomic and fails if a racing path appears.
                target = os.path.relpath(src, dest.parent) if scope == "project" else src
                dest.symlink_to(target, target_is_directory=True)
    return plan


def manifest(folder):
    return {str(p.relative_to(folder)): p.read_bytes() for p in skill_files(folder)}


def validate_installed(root, scope="project", home=None, provider="both"):
    root = Path(root).resolve()
    home = Path(home or Path.home()).resolve()
    for directory in destinations(root, scope, home, provider):
        for src in sources(root):
            dest = directory / src.name
            if not dest.is_dir():
                raise SkillError(f"Installed skill is missing or broken: {dest}")
            if dest.is_symlink():
                if dest.resolve() != src:
                    raise SkillError(f"Installed link points elsewhere: {dest}")
            elif manifest(dest) != manifest(src):
                raise SkillError(f"Installed copy differs from source: {dest}")


def validate_zip(path, folder):
    expected = {str(Path(folder.name) / p.relative_to(folder)): p.read_bytes()
                for p in skill_files(folder)}
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if (archive.testzip() is not None or len(names) != len(set(names))
                or set(names) != set(expected)):
            raise SkillError(f"ZIP layout does not match the skill: {path}")
        for name, value in expected.items():
            if archive.read(name) != value:
                raise SkillError(f"ZIP content mismatch: {path}/{name}")


def package(root, output, selected=None):
    folders = [p for p in sources(Path(root).resolve()) if not selected or p.name == selected]
    if not folders:
        raise SkillError(f"Unknown skill: {selected}")
    output = Path(output).resolve()
    for folder in folders:
        if os.path.lexists(output / (folder.name + ".zip")):
            raise SkillError(f"ZIP already exists; nothing overwritten: {folder.name}.zip")
    output.mkdir(parents=True, exist_ok=True)
    written = []
    for folder in folders:
        dest = output / (folder.name + ".zip")
        with tempfile.NamedTemporaryFile(dir=output, suffix=".zip", delete=False) as handle:
            stage = Path(handle.name)
        try:
            with zipfile.ZipFile(stage, "w", zipfile.ZIP_DEFLATED) as archive:
                for path in skill_files(folder):
                    archive.write(path, str(Path(folder.name) / path.relative_to(folder)))
            validate_zip(stage, folder)
            # Hard-link a completed file into place without overwriting a race.
            os.link(stage, dest)
            written.append(dest)
        finally:
            stage.unlink(missing_ok=True)
    return written


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "install"):
        p = commands.add_parser(name)
        p.add_argument("--scope", choices=("project", "user"), default="project")
        p.add_argument("--provider", choices=("both", "codex", "claude"), default="both")
        p.add_argument("--home", type=Path, default=Path.home(), help="Personal destination base; useful for isolated tests")
        if name == "install":
            p.add_argument("--apply", action="store_true", help="Create links/copies; otherwise print a dry-run plan")
            p.add_argument("--copy", action="store_true", help="Create independent snapshots instead of symlinks")
        else:
            p.add_argument("--installed", action="store_true", help="Also verify all selected installed links/copies")
    p = commands.add_parser("package", help="Create per-skill ZIPs on demand for Claude.ai upload")
    p.add_argument("--output", type=Path, help="Destination directory; defaults to <project>/packages")
    p.add_argument("--skill", choices=NAMES)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            validated = sources(args.root)
            if args.installed:
                validate_installed(args.root, args.scope, args.home, args.provider)
            print(f"PASS: {len(validated)} skills" + ("; installed mappings verified" if args.installed else ""))
        elif args.command == "install":
            plan = install(args.root, args.scope, args.home, args.provider, args.apply, args.copy)
            print("APPLIED" if args.apply else "DRY RUN — no files changed; add --apply to install")
            for action, src, dest in plan:
                print(f"{action}: {dest} -> {src}")
            if args.apply:
                validate_installed(args.root, args.scope, args.home, args.provider)
                print("PASS: installed mapping readback")
        else:
            for path in package(args.root, args.output or args.root / "packages", args.skill):
                print(path)
    except (OSError, SkillError, UnicodeError, zipfile.BadZipFile) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
