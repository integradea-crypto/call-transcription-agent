#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
from pathlib import Path
from urllib.parse import urlparse


def check_private_file(path_value: str, label: str) -> Path:
    path = Path(path_value).expanduser().resolve()
    if not path.is_file():
        raise ValueError(f"{label}: file does not exist")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        raise ValueError(f"{label}: permissions must not allow group or other access")
    print(f"ready: {label} file exists with protected permissions")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate credential references without printing secrets")
    parser.add_argument("--google-service-account", required=True)
    parser.add_argument("--bitrix-url-file", required=True)
    args = parser.parse_args()

    try:
        google_path = check_private_file(args.google_service_account, "Google service account")
        bitrix_path = check_private_file(args.bitrix_url_file, "Bitrix REST URL")

        google_data = json.loads(google_path.read_text(encoding="utf-8"))
        required = {"type", "project_id", "private_key", "client_email"}
        if google_data.get("type") != "service_account" or not required.issubset(google_data):
            raise ValueError("Google service account: invalid JSON structure")
        print("ready: Google service-account structure is valid")

        bitrix_url = bitrix_path.read_text(encoding="utf-8").strip()
        parsed = urlparse(bitrix_url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("Bitrix REST URL: HTTPS URL required")
        if not re.fullmatch(r"/rest/[^/]+/[^/]+/?", parsed.path):
            raise ValueError("Bitrix REST URL: expected /rest/<user>/<token> path")
        print("ready: Bitrix REST URL structure is valid")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"blocked: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
