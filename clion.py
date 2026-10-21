#!/usr/bin/env python3
"""Generate the decomp's CLion project, optionally including individual candidates."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

import kitpaths


def command(args):
    repo = Path(kitpaths.REPO)
    generator = repo / "tools" / "ide_compdb.py"
    if not generator.is_file():
        raise ValueError(f"{repo} needs the decomp's CLion support (tools/ide_compdb.py)")
    result = [sys.executable, str(repo / "tools" / "configure.py"), args.region, "--ide",
              "--ide-compiler", args.compiler, "--ide-build", args.build]
    for source in args.source:
        # Resolve before the subprocess changes into the decomp checkout.
        result.extend(["--ide-source", str(source.expanduser().resolve())])
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("region", nargs="?", choices=("usa", "jpn", "eur"),
                        default=os.environ.get("DQIX_REGION", "usa"))
    parser.add_argument("--compiler", default="clang", help="Path to Clang for code analysis")
    parser.add_argument("--source", type=Path, action="append", default=[], help="Also index this C/C++ candidate (repeatable)")
    parser.add_argument("--build", default="game", help="Build family for external candidates, e.g. game, sdk or runtime")
    args = parser.parse_args(argv)
    if os.path.dirname(args.compiler):
        args.compiler = str(Path(args.compiler).expanduser().resolve())
    try:
        invocation = command(args)
    except ValueError as error:
        parser.error(str(error))
    return subprocess.run(invocation, cwd=kitpaths.REPO).returncode


if __name__ == "__main__":
    sys.exit(main())
