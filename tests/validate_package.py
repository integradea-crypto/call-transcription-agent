#!/usr/bin/env python3
from __future__ import annotations

import json
import py_compile
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {"", ".md", ".json", ".yaml", ".yml", ".py", ".sh", ".sql", ".txt", ".example", ".lock"}
REQUIRED = [
    "README.md",
    "deploy/docker-compose.yml",
    "deploy/.env.example",
    "docs/agent-installation.md",
    "docs/server-requirements.md",
    "n8n/workflow.json",
    "schema/bigquery-schema.sql",
    "skill/call-transcription-analytics/SKILL.md",
    "transcriber/app/server.py",
]
FORBIDDEN_LITERALS = [
    "gtm-k4v7jns-mjziz",
    "geohim.bitrix24.ru",
    "gnzokO1kcuWYcu39",
    "metadata.google.internal",
]
SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    re.compile(r"https://[^\s/'\"]+\.bitrix24\.[^\s/'\"]+/rest/\d+/[A-Za-z0-9_-]{12,}"),
]


def fail(message: str) -> None:
    raise AssertionError(message)


def scan_files() -> None:
    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            fail(f"missing required file: {relative}")

    for path in ROOT.rglob("*"):
        if path.is_symlink():
            fail(f"symlink is not allowed in release: {path.relative_to(ROOT)}")
        if not path.is_file() or path.name in {"MANIFEST.sha256", "validate_package.py"}:
            continue
        if path.relative_to(ROOT).parts[:2] == ("deploy", "secrets") and path.name != ".gitkeep":
            fail(f"secret file present: {path.relative_to(ROOT)}")
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"Dockerfile", ".gitignore"}:
            continue
        text = path.read_text(encoding="utf-8")
        for literal in FORBIDDEN_LITERALS:
            if literal in text:
                fail(f"production literal in {path.relative_to(ROOT)}")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                fail(f"secret-like value in {path.relative_to(ROOT)}")
        if "[TODO" in text:
            fail(f"unfinished placeholder in {path.relative_to(ROOT)}")


def validate_workflow() -> None:
    data = json.loads((ROOT / "n8n/workflow.json").read_text(encoding="utf-8"))
    workflows = data if isinstance(data, list) else [data]
    if len(workflows) != 1:
        fail("workflow export must contain exactly one workflow")
    workflow = workflows[0]
    if workflow.get("active") is not False:
        fail("workflow must ship inactive")
    nodes = workflow.get("nodes", [])
    if any(node.get("credentials") for node in nodes):
        fail("workflow contains credential references")
    types = {node.get("type") for node in nodes}
    if "n8n-nodes-base.executeCommand" in types:
        fail("workflow must not execute shell commands")
    names = {node.get("name") for node in nodes}
    for expected in {"Bitrix Call End Webhook", "Transcribe with Local Whisper", "Upsert Call"}:
        if expected not in names:
            fail(f"workflow missing node: {expected}")


def validate_code() -> None:
    for path in ROOT.rglob("*.py"):
        py_compile.compile(str(path), doraise=True)
    for path in ROOT.rglob("*.sh"):
        subprocess.run(["bash", "-n", str(path)], check=True)


def main() -> int:
    try:
        scan_files()
        validate_workflow()
        validate_code()
    except (AssertionError, OSError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    print("PASS: package structure, workflow, code syntax, and secret scan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
