"""Compile repository Python sources in memory without creating bytecode."""

from __future__ import annotations

import pathlib
import sys
import tokenize


ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE_ROOTS = (ROOT / "backend", ROOT / "tools", ROOT / "tests")


def main() -> int:
    checked = 0
    failed = False
    for source_root in SOURCE_ROOTS:
        for path in sorted(source_root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            relative = path.relative_to(ROOT)
            try:
                with tokenize.open(path) as stream:
                    compile(stream.read(), str(relative), "exec", dont_inherit=True)
                checked += 1
            except (OSError, SyntaxError, UnicodeError) as error:
                failed = True
                print(f"{relative}: {error}", file=sys.stderr)
    if failed:
        return 1
    print(f"Python syntax check passed for {checked} files without writing bytecode.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
