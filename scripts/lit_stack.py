#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unified entry point for the integrated literature stack.

Examples:
    python scripts/lit_stack.py doctor
    python scripts/lit_stack.py list
    python scripts/lit_stack.py path nature-downloader
    python scripts/lit_stack.py search "GATA2 half-life" --limit 15 --out candidates.csv
    python scripts/lit_stack.py school show
    python scripts/lit_stack.py download --doi 10.1371/journal.pcbi.1000771 --out-dir pdfs --si

The script has no third-party Python dependencies, so `doctor` still works
before the user installs the report packages.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "literature" / "integrations.json"
DEFAULT_PROXY = "http://127.0.0.1:3456"


def load_manifest() -> dict[str, Any]:
    with MANIFEST_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_entry(manifest: dict[str, Any], name: str) -> dict[str, Any]:
    for entry in manifest.get("skills", []):
        if entry.get("name") == name:
            return entry
    raise KeyError(f"unknown integrated skill: {name}")


def skill_roots() -> list[Path]:
    roots: list[Path] = []
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        roots.append(Path(codex_home).expanduser() / "skills")
    roots.append(Path.home() / ".codex" / "skills")
    roots.append(Path.home() / ".claude" / "skills")

    unique: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        try:
            key = str(root.resolve())
        except OSError:
            key = str(root)
        if key not in seen:
            seen.add(key)
            unique.append(root)
    return unique


def local_skill(name: str) -> Path | None:
    for root in skill_roots():
        candidate = root / name
        if (candidate / "SKILL.md").is_file():
            return candidate
    return None


def bundled_skill(entry: dict[str, Any]) -> Path | None:
    raw = entry.get("path", "")
    if not raw or not str(raw).startswith("literature/"):
        return None
    candidate = (ROOT / raw).resolve()
    if (candidate / "SKILL.md").is_file():
        return candidate
    return None


def resolve_entry(entry: dict[str, Any]) -> Path | None:
    if entry.get("delivery") == "bundled":
        return bundled_skill(entry)
    return local_skill(entry["name"])


def package_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def python_info() -> dict[str, Any]:
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    return {
        "executable": sys.executable,
        "version": version,
        "supported": sys.version_info >= (3, 10),
    }


def node_info() -> dict[str, Any]:
    executable = shutil.which("node")
    if not executable:
        return {"executable": None, "version": None, "supported": False}
    try:
        result = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        version = (result.stdout or result.stderr).strip()
        major = 0
        if version.lower().startswith("v"):
            major = int(version[1:].split(".", 1)[0])
        return {
            "executable": executable,
            "version": version or None,
            "supported": major >= 22,
        }
    except Exception as exc:  # pragma: no cover - environment dependent
        return {
            "executable": executable,
            "version": None,
            "supported": False,
            "error": str(exc),
        }


def package_report() -> dict[str, Any]:
    groups = {
        "core_report": {
            "docx": "python-docx",
            "fitz": "PyMuPDF",
            "PIL": "Pillow",
        },
        "institutional_downloader": {
            "yaml": "PyYAML",
            "pdfplumber": "pdfplumber",
            "pypdf": "pypdf",
            "jsonschema": "jsonschema",
        },
        "local_corpus": {
            "openpyxl": "openpyxl",
        },
    }
    report: dict[str, Any] = {}
    for group, modules in groups.items():
        report[group] = {
            name: {
                "import_name": import_name,
                "available": package_available(name),
            }
            for name, import_name in modules.items()
        }
    return report


def cdp_status(proxy: str = DEFAULT_PROXY) -> dict[str, Any]:
    proxy = proxy.rstrip("/")
    url = proxy + "/targets"
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            body = response.read(2048).decode("utf-8", errors="replace")
        return {
            "proxy": proxy,
            "reachable": 200 <= response.status < 300,
            "status": response.status,
            "sample": body[:180],
        }
    except Exception as exc:
        return {
            "proxy": proxy,
            "reachable": False,
            "status": None,
            "error": str(exc),
        }


def school_config_status() -> dict[str, Any]:
    base = Path(os.environ.get("LIT_DL_CONFIG_DIR", Path.home() / ".config" / "lit-dl"))
    path = base / "school.json"
    return {
        "path": str(path),
        "configured": path.is_file(),
    }


def doctor_data(proxy: str = DEFAULT_PROXY) -> dict[str, Any]:
    manifest = load_manifest()
    packages = package_report()
    components: list[dict[str, Any]] = []
    for entry in manifest.get("skills", []):
        resolved = resolve_entry(entry)
        components.append(
            {
                "name": entry.get("name"),
                "delivery": entry.get("delivery"),
                "license": entry.get("license"),
                "available": resolved is not None,
                "path": str(resolved) if resolved else None,
                "fallback": entry.get("fallback"),
            }
        )

    core_ok = all(item["available"] for item in packages["core_report"].values())
    vendor_ok = all(
        item["available"]
        for item in components
        if item["delivery"] == "bundled"
    )
    optional_available = sum(
        1
        for item in components
        if item["delivery"] == "local-adapter" and item["available"]
    )
    optional_total = sum(1 for item in components if item["delivery"] == "local-adapter")

    return {
        "skill_root": str(ROOT),
        "python": python_info(),
        "node": node_info(),
        "packages": packages,
        "cdp": cdp_status(proxy),
        "school_config": school_config_status(),
        "components": components,
        "summary": {
            "core_report_packages_ready": core_ok,
            "bundled_components_ready": vendor_ok,
            "optional_adapters_available": optional_available,
            "optional_adapters_total": optional_total,
        },
    }


def _mark(value: bool) -> str:
    return "OK" if value else "MISSING"


def print_doctor(data: dict[str, Any]) -> None:
    print("parameter-evidence-support - literature stack doctor")
    print(f"skill root: {data['skill_root']}")
    print()

    python = data["python"]
    print(f"Python: {python['version']} [{_mark(python['supported'])}]")
    print(f"  executable: {python['executable']}")

    node = data["node"]
    node_text = node.get("version") or "not found"
    print(f"Node.js: {node_text} [{_mark(node['supported'])}]")
    if node.get("executable"):
        print(f"  executable: {node['executable']}")

    print()
    print("Python packages")
    for group, modules in data["packages"].items():
        print(f"  {group}:")
        for label, item in modules.items():
            print(f"    {_mark(item['available']):<7} {label} ({item['import_name']})")

    print()
    print("Browser handoff")
    cdp = data["cdp"]
    print(f"  CDP proxy: {cdp['proxy']} [{_mark(cdp['reachable'])}]")
    if cdp.get("error"):
        print(f"    {cdp['error']}")
    school = data["school_config"]
    print(f"  school config: {school['path']} [{_mark(school['configured'])}]")

    print()
    print("Integrated components")
    for item in data["components"]:
        print(
            f"  {_mark(item['available']):<7} {item['name']} "
            f"({item['delivery']})"
        )
        if item.get("path"):
            print(f"         {item['path']}")
        elif item.get("fallback"):
            print(f"         fallback: {item['fallback']}")

    summary = data["summary"]
    print()
    print("Summary")
    print(f"  core report packages: {_mark(summary['core_report_packages_ready'])}")
    print(f"  bundled components: {_mark(summary['bundled_components_ready'])}")
    print(
        "  optional adapters: "
        f"{summary['optional_adapters_available']}/{summary['optional_adapters_total']} available"
    )

    hints: list[str] = []
    if not python["supported"]:
        hints.append("Install Python 3.10 or later.")
    if not node["supported"]:
        hints.append("Install Node.js 22+ to use the bundled institutional downloader.")
    if not summary["core_report_packages_ready"]:
        hints.append("Run: pip install -r requirements.txt")
    if not summary["bundled_components_ready"]:
        hints.append("Reinstall the skill; literature/vendor is incomplete.")
    if not cdp["reachable"]:
        hints.append("Start Chrome remote debugging and the web-access CDP proxy before an institutional download.")
    if not school["configured"]:
        hints.append("Run: python scripts/lit_stack.py school preset \"上海交通大学\" (or use your real library URL).")
    if summary["optional_adapters_available"] < summary["optional_adapters_total"]:
        hints.append("Optional adapters are absent; the core scripts will be used instead.")
    if hints:
        print()
        print("Next steps")
        for hint in hints:
            print(f"  - {hint}")


def print_list(data: dict[str, Any]) -> None:
    print(f"{'component':32} {'delivery':13} {'status':9} path")
    print("-" * 110)
    for item in data["components"]:
        print(
            f"{item['name'][:32]:32} {item['delivery'][:13]:13} "
            f"{('ready' if item['available'] else 'missing'):9} {item.get('path') or '-'}"
        )


def command_doctor(args: argparse.Namespace) -> int:
    data = doctor_data(args.proxy)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print_doctor(data)
    return 0


def command_list(args: argparse.Namespace) -> int:
    data = doctor_data(args.proxy)
    if args.json:
        print(json.dumps(data["components"], ensure_ascii=False, indent=2))
    else:
        print_list(data)
    return 0


def command_path(args: argparse.Namespace) -> int:
    manifest = load_manifest()
    try:
        entry = get_entry(manifest, args.name)
    except KeyError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    resolved = resolve_entry(entry)
    if resolved is None:
        print(f"{args.name}: not found", file=sys.stderr)
        fallback = entry.get("fallback")
        if fallback:
            print(f"fallback: {fallback}", file=sys.stderr)
        return 1
    print(resolved)
    return 0


def command_search(args: argparse.Namespace) -> int:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "find_papers.py"),
        args.query,
        "--limit",
        str(args.limit),
        "--out",
        args.out,
    ]
    if args.year_from:
        command += ["--year-from", str(args.year_from)]
    if args.mailto:
        command += ["--mailto", args.mailto]
    if args.no_epmc:
        command.append("--no-epmc")
    if args.no_openalex:
        command.append("--no-openalex")
    return subprocess.run(command, cwd=ROOT).returncode


def choose_downloader(backend: str) -> Path | None:
    manifest = load_manifest()
    entry = get_entry(manifest, "nature-downloader")
    bundled = bundled_skill(entry)
    local = local_skill(entry["name"])
    if backend == "bundled":
        return bundled
    if backend == "local":
        return local
    return bundled or local


def command_school(args: argparse.Namespace) -> int:
    base = choose_downloader("auto")
    if base is None:
        print("nature-downloader is not available.", file=sys.stderr)
        return 1
    script = base / "scripts" / "configure_school.py"
    if not script.is_file():
        print(f"missing configuration script: {script}", file=sys.stderr)
        return 1
    command = [sys.executable, str(script), args.action]
    if args.value:
        command.append(args.value)
    if args.action == "health" and args.force:
        command.append("--force")
    return subprocess.run(command, cwd=base).returncode


def command_download(args: argparse.Namespace) -> int:
    base = choose_downloader(args.backend)
    if base is None:
        print("nature-downloader is not available.", file=sys.stderr)
        print("Install Node.js 22+ and reinstall the skill, or use scripts/download_pdf.py.", file=sys.stderr)
        return 1

    node = shutil.which("node")
    if not node:
        print("Node.js was not found; the bundled institutional downloader cannot run.", file=sys.stderr)
        print("Use scripts/download_pdf.py for an open-access PDF or install Node.js 22+.", file=sys.stderr)
        return 1

    script = base / "scripts" / "batch_download.mjs"
    if not script.is_file():
        print(f"missing batch downloader: {script}", file=sys.stderr)
        return 1

    dois: list[str] = []
    for value in args.doi or []:
        dois.extend(part.strip() for part in value.split(",") if part.strip())

    modes = [bool(dois), bool(args.topic), bool(args.title), bool(args.pdf_url)]
    mode_count = sum(modes)
    if mode_count == 0:
        print("Provide --doi, --topic, --title, or --pdf-url.", file=sys.stderr)
        return 2
    if mode_count > 1 and not (args.topic and args.title and mode_count == 2):
        print("Use one mode: --doi, --topic, --title, --pdf-url (topic+title is allowed).", file=sys.stderr)
        return 2

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    command = [node, str(script)]
    if dois:
        command += ["--dois", ",".join(dois)]
    if args.topic:
        command += ["--topic", args.topic]
    if args.title:
        command += ["--title", args.title]
    if args.pdf_url:
        command += ["--pdf-url", args.pdf_url]
    command += ["--out", str(out_dir)]
    if args.count is not None:
        command += ["--count", str(args.count)]
    if args.si:
        command.append("--si")
    if args.open_access:
        command.append("--open-access")
    if args.proxy:
        command += ["--proxy", args.proxy]
    if args.debug:
        command.append("--debug")
    if args.legacy_status:
        command.append("--legacy-status")

    print("[lit-stack] " + " ".join(command))
    return subprocess.run(command, cwd=base).returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect and run the integrated literature stack."
    )
    sub = parser.add_subparsers(dest="command")

    doctor = sub.add_parser("doctor", help="Check the environment, packages, CDP proxy, and adapters.")
    doctor.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    doctor.add_argument("--proxy", default=DEFAULT_PROXY, help="CDP proxy base URL.")
    doctor.set_defaults(func=command_doctor)

    list_parser = sub.add_parser("list", help="List integrated components and availability.")
    list_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    list_parser.add_argument("--proxy", default=DEFAULT_PROXY, help="CDP proxy base URL.")
    list_parser.set_defaults(func=command_list)

    path_parser = sub.add_parser("path", help="Resolve an integrated skill to a local path.")
    path_parser.add_argument("name")
    path_parser.set_defaults(func=command_path)

    search = sub.add_parser("search", help="Run the core Europe PMC + OpenAlex discovery search.")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=15)
    search.add_argument("--year-from", type=int, default=None)
    search.add_argument("--mailto", default="")
    search.add_argument("--out", default="candidates.csv")
    search.add_argument("--no-epmc", action="store_true")
    search.add_argument("--no-openalex", action="store_true")
    search.set_defaults(func=command_search)

    school = sub.add_parser("school", help="Configure or inspect the bundled library access route.")
    school.add_argument("action", choices=["infer", "url", "preset", "show", "health", "list"])
    school.add_argument("value", nargs="?", help="URL, preset name, or other action argument.")
    school.add_argument("--force", action="store_true", help="Force a health check.")
    school.set_defaults(func=command_school)

    download = sub.add_parser("download", help="Run the bundled institutional/browser-session downloader.")
    download.add_argument("--doi", action="append", default=[], help="DOI; repeat or comma-separate.")
    download.add_argument("--topic")
    download.add_argument("--title")
    download.add_argument("--pdf-url")
    download.add_argument("--out-dir", default="pdfs")
    download.add_argument("--count", type=int, default=None)
    download.add_argument("--si", action="store_true")
    download.add_argument("--open-access", action="store_true")
    download.add_argument("--proxy", default=DEFAULT_PROXY)
    download.add_argument("--debug", action="store_true")
    download.add_argument("--legacy-status", action="store_true")
    download.add_argument("--backend", choices=["auto", "bundled", "local"], default="auto")
    download.set_defaults(func=command_download)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        args = parser.parse_args(["doctor"])
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
