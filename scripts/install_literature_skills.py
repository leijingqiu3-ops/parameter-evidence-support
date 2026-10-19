#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Detect and install the optional literature skills used by this skill.

The bundled components (`nature-downloader` and
`organize-research-literature`) are already inside `literature/vendor/`.
This script only handles the local adapters that are installed under the
user's Codex skills directory.

Examples:
    python scripts/install_literature_skills.py --check
    python scripts/install_literature_skills.py --install
    python scripts/install_literature_skills.py --install --only nature-reader
    python scripts/install_literature_skills.py --install --force
    python scripts/install_literature_skills.py --check --json

The installer downloads public upstream archives at run time. It does not
copy those sources into this repository. Existing skills are skipped unless
`--force` is supplied.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "literature" / "integrations.json"
USER_AGENT = "parameter-evidence-support/1.0 (mailto:research@example.org)"


def load_manifest() -> dict[str, Any]:
    with MANIFEST_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def codex_home(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    env = os.environ.get("CODEX_HOME")
    if env:
        return Path(env).expanduser().resolve()
    return (Path.home() / ".codex").resolve()


def skills_root(home: Path) -> Path:
    return home / "skills"


def installed(target: Path) -> bool:
    return (target / "SKILL.md").is_file()


def archive_url(repo: str, ref: str) -> str:
    return f"https://codeload.github.com/{repo}/zip/refs/heads/{urllib.parse.quote(ref, safe='')}"


def download_archive(repo: str, ref: str, cache_dir: Path, timeout: int = 120) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    safe_name = repo.replace("/", "__") + "__" + ref.replace("/", "__") + ".zip"
    destination = cache_dir / safe_name
    if destination.is_file() and destination.stat().st_size > 0:
        return destination
    request = urllib.request.Request(archive_url(repo, ref), headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response, destination.open("wb") as handle:
        shutil.copyfileobj(response, handle)
    if destination.stat().st_size == 0:
        raise RuntimeError(f"empty archive for {repo}@{ref}")
    return destination


def extract_archive(archive: Path, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(destination)
    roots = [item for item in destination.iterdir() if item.is_dir()]
    if len(roots) == 1:
        return roots[0]
    return destination


def ignore_generated(_directory: str, names: list[str]) -> set[str]:
    return {
        name
        for name in names
        if name in {"__pycache__", ".git"} or name.endswith((".pyc", ".pyo"))
    }


def assert_under(target: Path, root: Path) -> None:
    target = target.resolve()
    root = root.resolve()
    if target != root and root not in target.parents:
        raise RuntimeError(f"refusing to write outside the skills directory: {target}")


def remove_existing(target: Path, root: Path) -> None:
    assert_under(target, root)
    if target.is_symlink() or target.is_file():
        target.unlink()
    elif target.is_dir():
        shutil.rmtree(target)


def merge_shared(source: Path, target: Path, force: bool) -> int:
    """Copy missing shared files without overwriting existing user content."""
    copied = 0
    for item in source.rglob("*"):
        if item.is_dir():
            continue
        relative = item.relative_to(source)
        destination = target / relative
        if destination.exists() and not force:
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, destination)
        copied += 1
    return copied


def entry_installable(entry: dict[str, Any]) -> bool:
    return entry.get("delivery") == "local-adapter" and isinstance(entry.get("install"), dict)


def source_repo(entry: dict[str, Any]) -> str:
    install = entry.get("install") or {}
    return install.get("repo") or entry.get("upstream") or "-"


def selected_entries(manifest: dict[str, Any], only: str | None) -> list[dict[str, Any]]:
    entries = [entry for entry in manifest.get("skills", []) if entry.get("delivery") == "local-adapter"]
    if not only:
        return entries
    wanted = {item.strip() for item in only.split(",") if item.strip()}
    unknown = wanted - {entry["name"] for entry in entries}
    if unknown:
        raise SystemExit(f"unknown adapter(s): {', '.join(sorted(unknown))}")
    return [entry for entry in entries if entry["name"] in wanted]


def check(manifest: dict[str, Any], root: Path, selected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in selected:
        target = root / entry["name"]
        rows.append(
            {
                "name": entry["name"],
                "installed": installed(target),
                "path": str(target),
                "installable": entry_installable(entry),
                "source": source_repo(entry),
                "license": entry.get("license", ""),
            }
        )
    return rows


def print_check(rows: list[dict[str, Any]]) -> None:
    print(f"{'adapter':30} {'status':10} {'auto-install':12} source")
    print("-" * 110)
    for row in rows:
        print(
            f"{row['name'][:30]:30} "
            f"{('installed' if row['installed'] else 'missing'):10} "
            f"{('yes' if row['installable'] else 'manual'):12} "
            f"{row['source']}"
        )
    missing = [row for row in rows if not row["installed"]]
    if missing:
        print()
        print("Missing adapters:")
        for row in missing:
            print(f"  - {row['name']}: {row['path']}")
        print()
        print("Install the automatic ones with:")
        print("  python scripts/install_literature_skills.py --install")


def install_one(
    entry: dict[str, Any],
    archive_root: Path,
    root: Path,
    force: bool,
) -> dict[str, Any]:
    install = entry.get("install") or {}
    source_dir = str(install.get("source_dir") or "").strip("/")
    source = archive_root / source_dir if source_dir else archive_root
    target = root / entry["name"]
    if not (source / "SKILL.md").is_file():
        return {
            "name": entry["name"],
            "status": "failed",
            "reason": f"SKILL.md not found in upstream source: {source}",
            "path": str(target),
        }
    if target.exists() or target.is_symlink():
        if installed(target):
            return {"name": entry["name"], "status": "skipped-existing", "path": str(target)}
        if not force:
            return {
                "name": entry["name"],
                "status": "blocked-existing-invalid",
                "reason": "target exists but has no SKILL.md; rerun with --force to replace it",
                "path": str(target),
            }
        remove_existing(target, root)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, ignore=ignore_generated)
    return {"name": entry["name"], "status": "installed", "path": str(target)}


def install_shared(
    shared: dict[str, Any],
    archive_root: Path,
    root: Path,
    force: bool,
) -> dict[str, Any]:
    source_dir = str(shared.get("source_dir") or "").strip("/")
    source = archive_root / source_dir if source_dir else archive_root
    target = root / shared.get("target_dir", "_shared")
    if not source.is_dir():
        return {"name": shared.get("name", "shared"), "status": "failed", "reason": f"source not found: {source}"}
    if target.exists() and not force and (target / "core" / "terminology-ledger.md").is_file():
        return {"name": shared.get("name", "shared"), "status": "skipped-existing", "path": str(target)}
    copied = merge_shared(source, target, force=force)
    return {"name": shared.get("name", "shared"), "status": "installed", "files": copied, "path": str(target)}


def install_selected(
    manifest: dict[str, Any],
    root: Path,
    selected: list[dict[str, Any]],
    force: bool,
    timeout: int,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    pending = [entry for entry in selected if not installed(root / entry["name"])]
    if not pending:
        return [{"name": entry["name"], "status": "skipped-existing", "path": str(root / entry["name"])} for entry in selected]

    shared_components = manifest.get("shared_components", [])
    shared_needed = any((entry.get("install") or {}).get("requires_shared") for entry in pending)
    shared = shared_components[0] if shared_needed and shared_components else None

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for entry in pending:
        install = entry.get("install") or {}
        repo = install.get("repo")
        ref = install.get("ref", "main")
        if not repo:
            results.append(
                {
                    "name": entry["name"],
                    "status": "manual",
                    "reason": "no automatic install source in integrations.json",
                    "source": entry.get("upstream"),
                }
            )
            continue
        grouped.setdefault((repo, ref), []).append(entry)

    with tempfile.TemporaryDirectory(prefix="pe-literature-install-") as temporary:
        temporary_root = Path(temporary)
        cache = temporary_root / "archives"
        extracted = temporary_root / "extracted"
        for (repo, ref), entries in grouped.items():
            try:
                archive = download_archive(repo, ref, cache, timeout=timeout)
                repo_dir = extract_archive(archive, extracted / (repo.replace("/", "__") + "__" + ref.replace("/", "__")))
                for entry in entries:
                    results.append(install_one(entry, repo_dir, root, force=force))
                if shared and (repo, ref) == (shared.get("repo"), shared.get("ref", "main")):
                    results.append(install_shared(shared, repo_dir, root, force=force))
            except Exception as exc:
                for entry in entries:
                    results.append(
                        {
                            "name": entry["name"],
                            "status": "failed",
                            "reason": str(exc),
                            "source": entry.get("upstream"),
                        }
                    )
    return results


def print_results(results: list[dict[str, Any]]) -> None:
    print()
    print("Results")
    for result in results:
        status = result.get("status")
        name = result.get("name")
        path = result.get("path", "")
        reason = result.get("reason", "")
        print(f"  {name}: {status}" + (f" -> {path}" if path else ""))
        if reason:
            print(f"    {reason}")
    failed = [result for result in results if result.get("status") == "failed"]
    manual = [result for result in results if result.get("status") == "manual"]
    if manual:
        print()
        print("Manual installation required:")
        for result in manual:
            print(f"  - {result.get('name')}: {result.get('source') or 'see literature/adapters/'}")
    if failed:
        print()
        print("Some adapters could not be installed. The core scripts still work; use the fallback listed in literature/router.md.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detect or install optional literature adapters.")
    parser.add_argument("--check", action="store_true", help="Only report which adapters are installed.")
    parser.add_argument("--install", action="store_true", help="Install missing adapters from public upstream archives.")
    parser.add_argument("--only", default=None, help="Comma-separated adapter names; default is all local adapters.")
    parser.add_argument("--force", action="store_true", help="Replace existing targets, including incomplete ones.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output.")
    parser.add_argument("--codex-home", default=None, help="Override CODEX_HOME for testing or isolated installs.")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args(argv)

    manifest = load_manifest()
    home = codex_home(args.codex_home)
    root = skills_root(home)
    selected = selected_entries(manifest, args.only)
    rows = check(manifest, root, selected)

    if not args.install:
        if args.json:
            print(json.dumps(rows, ensure_ascii=False, indent=2))
        else:
            print(f"codex home: {home}")
            print(f"skills dir: {root}")
            print()
            print_check(rows)
        return 0

    results = install_selected(manifest, root, selected, force=args.force, timeout=args.timeout)
    if args.json:
        print(json.dumps({"skills_dir": str(root), "results": results}, ensure_ascii=False, indent=2))
    else:
        print(f"codex home: {home}")
        print(f"skills dir: {root}")
        print_results(results)
    failed = [result for result in results if result.get("status") == "failed"]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
