#!/usr/bin/env python3
"""Keep only StrEnum / Enum classes from datamodel-codegen server schema output."""

import argparse
import ast
import sys
from pathlib import Path

_ENUM_BASE_NAMES = frozenset({"StrEnum", "Enum"})


def _is_enum_class(node: ast.ClassDef) -> bool:
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id in _ENUM_BASE_NAMES:
            return True
        if isinstance(base, ast.Attribute) and base.attr in _ENUM_BASE_NAMES:
            return True
    return False


def extract_enum_class_sources(source: str) -> list[str]:
    """Return source text for each top-level enum class, in file order."""
    tree = ast.parse(source)
    segments: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and _is_enum_class(node):
            segment = ast.get_source_segment(source, node)
            if segment is None:
                segment = ast.unparse(node)
            segments.append(segment)
    return segments


def build_module(header: str, enum_sources: list[str]) -> str:
    body = "\n\n".join(enum_sources)
    if body:
        body += "\n"
    # Two blank lines after imports before the first top-level class (PEP 8).
    return f"{header.rstrip()}\n\n\n{body}" if body else f"{header.rstrip()}\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Full datamodel-codegen output file")
    parser.add_argument("output", type=Path, help="Enum-only _server_schemas.py path")
    parser.add_argument(
        "--header",
        type=Path,
        default=None,
        help="File header (default: templates/header.jinja2 next to repo root)",
    )
    args = parser.parse_args(argv)

    header_path = args.header
    if header_path is None:
        header_path = Path(__file__).resolve().parents[1] / "templates" / "header.jinja2"

    source = args.input.read_text(encoding="utf-8")
    enum_sources = extract_enum_class_sources(source)
    if not enum_sources:
        print("No enum classes found in input", file=sys.stderr)
        return 1

    header = header_path.read_text(encoding="utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_module(header, enum_sources), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
