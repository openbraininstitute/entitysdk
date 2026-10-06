#!/usr/bin/env python3
"""Keep only StrEnum / Enum classes from datamodel-codegen server schema output."""

import argparse
import ast
import sys
from pathlib import Path


def _is_enum_class(node: ast.ClassDef) -> bool:
    for base in node.bases:
        name = base.id if isinstance(base, ast.Name) else getattr(base, "attr", None)
        if name in ("StrEnum", "Enum"):
            return True
    return False


def extract_enum_body(source: str) -> str:
    """Copy enum class source from the codegen file (one class at a time; ruff format follows in tox)."""
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    parts: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and _is_enum_class(node):
            chunk = "".join(lines[node.lineno - 1 : node.end_lineno]).rstrip()
            parts.append(chunk)
    return "\n\n\n".join(parts) + "\n" if parts else ""


def build_module(header: str, enum_body: str) -> str:
    return f"{header.rstrip()}\n\n\n{enum_body}" if enum_body else f"{header.rstrip()}\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--header", type=Path, required=True)
    args = parser.parse_args(argv)

    enum_body = extract_enum_body(args.input.read_text(encoding="utf-8"))
    if not enum_body:
        print("No enum classes found in input", file=sys.stderr)
        return 1

    header = args.header.read_text(encoding="utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_module(header, enum_body), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
