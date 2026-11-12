"""Prepare a synced invoice for later local-model extraction.

Uses Poppler utilities on PATH. This stage does not call a model or delete input.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


SUPPORTED = {".pdf", ".png", ".jpg", ".jpeg"}
TEXT_THRESHOLD = 80  # Conservative indicator, not a proof of OCR quality.


def run_binary(args: list[str], timeout: int = 120) -> bytes:
    result = subprocess.run(
        args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=timeout
    )
    if result.returncode != 0:
        error = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"{' '.join(args[:2])} failed: {error}")
    return result.stdout


def choose_source(explicit: Path | None, intake: Path) -> Path:
    if explicit is not None:
        source = explicit.expanduser().resolve()
    else:
        if not intake.is_dir():
            raise FileNotFoundError(f"Intake folder does not exist: {intake}")
        candidates = [p for p in intake.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED]
        if not candidates:
            raise FileNotFoundError(f"No supported invoice in {intake}")
        source = max(candidates, key=lambda p: p.stat().st_mtime_ns)
    if not source.is_file() or source.suffix.lower() not in SUPPORTED:
        raise ValueError(f"Expected a PDF, PNG, JPG, or JPEG file: {source}")
    return source


def digest_stable_file(path: Path) -> str:
    before = path.stat()
    time.sleep(2)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise RuntimeError("File is still changing. Retry after OneDrive finishes syncing.")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    end = path.stat()
    if (after.st_size, after.st_mtime_ns) != (end.st_size, end.st_mtime_ns):
        raise RuntimeError("File changed while being read. Retry after sync finishes.")
    return digest.hexdigest()


def pdf_page_count(path: Path) -> int:
    info = run_binary(["pdfinfo", str(path)], timeout=120).decode("utf-8", "replace")
    match = re.search(r"^Pages[:]\s+(\d+)\s*$", info, flags=re.MULTILINE)
    if not match or int(match.group(1)) < 1:
        raise RuntimeError("pdfinfo did not report a valid page count")
    return int(match.group(1))


def prepare_pdf(source: Path, folder: Path) -> list[dict]:
    pages = []
    for number in range(1, pdf_page_count(source) + 1):
        text_bytes = run_binary(
            [
                "pdftotext",
                "-f",
                str(number),
                "-l",
                str(number),
                "-layout",
                "-enc",
                "UTF-8",
                str(source),
                "-",
            ],
            timeout=120,
        )
        page_text = text_bytes.decode("utf-8", errors="replace").replace("\f", "")
        text_path = folder / f"page-{number:04d}.txt"
        text_path.write_text(page_text, encoding="utf-8")
        alphanumeric_count = sum(char.isalnum() for char in page_text)
        is_text_candidate = alphanumeric_count >= TEXT_THRESHOLD
        image_name = None
        if not is_text_candidate:
            stem = folder / f"page-{number:04d}"
            run_binary(
                [
                    "pdftoppm",
                    "-f",
                    str(number),
                    "-l",
                    str(number),
                    "-singlefile",
                    "-r",
                    "180",
                    "-png",
                    str(source),
                    str(stem),
                ],
                timeout=300,
            )
            image_path = stem.with_suffix(".png")
            if not image_path.is_file() or image_path.stat().st_size == 0:
                raise RuntimeError(f"Poppler did not render page {number}")
            image_name = image_path.name
        pages.append(
            {
                "page": number,
                "route": "text_candidate" if is_text_candidate else "image_required",
                "alphanumeric_characters": alphanumeric_count,
                "text_file": text_path.name,
                "image_file": image_name,
            }
        )
    return pages


def prepare_image(source: Path, folder: Path) -> list[dict]:
    destination = folder / f"page-0001{source.suffix.lower()}"
    shutil.copyfile(source, destination)
    return [
        {
            "page": 1,
            "route": "image_required",
            "alphanumeric_characters": 0,
            "text_file": None,
            "image_file": destination.name,
        }
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--file", type=Path, help="Process this file instead of the newest intake file"
    )
    parser.add_argument(
        "--intake",
        type=Path,
        help="Use this intake directory instead of the configured OneDrive Incoming directory",
    )
    args = parser.parse_args()

    onedrive = os.environ.get("OneDriveCommercial")
    if args.intake is not None:
        intake = args.intake.expanduser().resolve()
    elif onedrive:
        intake = Path(onedrive) / "InvoiceIntake" / "Incoming"
    elif args.file is None:
        parser.error(
            "OneDriveCommercial is missing; supply --file or --intake, or sign into work OneDrive"
        )
    else:
        intake = Path.cwd()

    engine_root_value = os.environ.get("DATA_HERMETICA_INVOICE_ENGINE_ROOT")
    if not engine_root_value:
        parser.error(
            "DATA_HERMETICA_INVOICE_ENGINE_ROOT is missing. Set it to the engine root directory."
        )

    engine_root = Path(engine_root_value).expanduser().resolve()
    output_root = engine_root / "work" / "prepared"
    output_root.mkdir(parents=True, exist_ok=True)

    source = choose_source(args.file, intake)
    digest = digest_stable_file(source)
    output = output_root / digest
    if output.is_dir() and (output / "manifest.json").is_file():
        print(f"Already prepared: {output / 'manifest.json'}")
        return 0
    with tempfile.TemporaryDirectory(prefix="staging-", dir=output_root) as staging:
        work = Path(staging)
        pages = (
            prepare_pdf(source, work)
            if source.suffix.lower() == ".pdf"
            else prepare_image(source, work)
        )
        manifest = {
            "schema_version": 2,
            "source_file": str(source),
            "sha256": digest,
            "engine_root": str(engine_root),
            "prepared_directory": str(output),
            "page_count": len(pages),
            "pages": pages,
            "note": (
                "text_candidate indicates only a nontrivial text layer; "
                "review quality before model extraction"
            ),
        }
        (work / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        if output.exists():
            raise RuntimeError(f"Incomplete prior output needs review: {output}")
        shutil.copytree(work, output)
    print(f"Source: {source}")
    print(f"Pages: {len(pages)}")
    print(f"Text candidates: {sum(p['route'] == 'text_candidate' for p in pages)}")
    print(f"Images required: {sum(p['route'] == 'image_required' for p in pages)}")
    print(f"Manifest: {output / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
