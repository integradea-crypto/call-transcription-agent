#!/usr/bin/env python3
from __future__ import annotations

import gzip
import hashlib
import subprocess
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
DIST = ROOT.parent / "call-transcription-agent-dist"
PREFIX = f"call-transcription-agent-{VERSION}"


def included_files() -> list[Path]:
    files = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.name == "MANIFEST.sha256":
            continue
        relative = path.relative_to(ROOT)
        if "__pycache__" in relative.parts or path.suffix == ".pyc":
            continue
        if relative.parts[:2] == ("deploy", "secrets") and path.name != ".gitkeep":
            continue
        # Never ship the private production-literal denylist; only its template is public.
        if relative.as_posix() == "tests/forbidden-literals.txt":
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(ROOT).as_posix())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(files: list[Path]) -> None:
    lines = [f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}" for path in files]
    (ROOT / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_archive(files: list[Path]) -> Path:
    DIST.mkdir(parents=True, exist_ok=True)
    archive = DIST / f"{PREFIX}.tar.gz"
    with archive.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(mode="w", fileobj=compressed, format=tarfile.PAX_FORMAT) as tar:
                for path in [*files, ROOT / "MANIFEST.sha256"]:
                    relative = path.relative_to(ROOT)
                    info = tar.gettarinfo(str(path), arcname=f"{PREFIX}/{relative.as_posix()}")
                    info.uid = 0
                    info.gid = 0
                    info.uname = "root"
                    info.gname = "root"
                    info.mtime = 0
                    with path.open("rb") as handle:
                        tar.addfile(info, handle)
    checksum = sha256(archive)
    archive.with_suffix(archive.suffix + ".sha256").write_text(
        f"{checksum}  {archive.name}\n", encoding="utf-8"
    )
    return archive


def main() -> int:
    subprocess.run(["python3", str(ROOT / "tests/validate_package.py")], check=True)
    files = included_files()
    write_manifest(files)
    archive = build_archive(files)
    print(f"archive={archive}")
    print(f"sha256={sha256(archive)}")
    print(f"files={len(files) + 1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
