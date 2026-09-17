#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys


def build_remote_command(args: argparse.Namespace) -> str:
    command = [
        *shlex.split(args.docker_command),
        "compose",
        "--env-file",
        args.env_file,
        "-f",
        args.compose_file,
        "exec",
        "-T",
        "call-service",
        "python",
        "-m",
        "app.cli",
        "query",
    ]
    mappings = {
        "activity_id": "--activity-id",
        "employee_id": "--employee-id",
        "stage_id": "--stage-id",
        "deal_id": "--deal-id",
        "contact_id": "--contact-id",
        "date_from": "--from",
        "date_to": "--to",
        "text": "--text",
    }
    for attribute, flag in mappings.items():
        value = getattr(args, attribute)
        if value:
            command.extend([flag, value])
    command.extend(["--limit", str(args.limit)])
    return "cd " + shlex.quote(args.remote_root) + " && " + shlex.join(command)


def main() -> int:
    parser = argparse.ArgumentParser(description="Query call transcripts through the server's read-only CLI")
    parser.add_argument("--ssh-host", required=True, help="Configured SSH host alias")
    parser.add_argument("--remote-root", default="/opt/call-transcription-agent/current/deploy")
    parser.add_argument("--env-file", default="/etc/call-transcription-agent/runtime.env")
    parser.add_argument("--compose-file", default="docker-compose.yml")
    parser.add_argument("--docker-command", default="docker")
    parser.add_argument("--activity-id")
    parser.add_argument("--employee-id")
    parser.add_argument("--stage-id")
    parser.add_argument("--deal-id")
    parser.add_argument("--contact-id")
    parser.add_argument("--from", dest="date_from")
    parser.add_argument("--to", dest="date_to")
    parser.add_argument("--text")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    if not 1 <= args.limit <= 1000:
        parser.error("--limit must be between 1 and 1000")
    if not any(
        getattr(args, name)
        for name in (
            "activity_id",
            "employee_id",
            "stage_id",
            "deal_id",
            "contact_id",
            "date_from",
            "date_to",
            "text",
        )
    ):
        parser.error("provide at least one filter")

    result = subprocess.run(
        ["ssh", args.ssh_host, build_remote_command(args)],
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode:
        print(result.stderr.strip(), file=sys.stderr)
        return result.returncode

    for line in result.stdout.splitlines():
        if line.strip():
            json.loads(line)
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
