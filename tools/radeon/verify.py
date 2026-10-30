#!/usr/bin/env python3
"""Build this Futhark checkout and validate it with an explicitly selected Radeon kit.

Uses the existing OpenCL backend. Does not install a compiler, modify remotes,
push commits, or upload validation data. Run outside restrictive sandboxes for GPU tests.
"""

import argparse
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def positive(value):
    value = int(value)
    if value < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return value


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--kit",
        type=Path,
        required=True,
        help="Path to the standalone futhark_radeon kit",
    )
    parser.add_argument(
        "--cpu-only", action="store_true", help="Validate without OpenCL"
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Use the existing Cabal executable",
    )
    parser.add_argument(
        "--jobs",
        type=positive,
        default=4,
        help="Cabal and GHC build parallelism",
    )
    parser.add_argument(
        "--threads",
        type=positive,
        default=10,
        help="Multicore validation threads",
    )
    parser.add_argument(
        "--device",
        default="AMD Radeon Pro 5500 XT",
        help="OpenCL GPU name substring",
    )
    args = parser.parse_args()
    kit = args.kit.resolve()
    if (
        not (kit / "Makefile").is_file()
        or not (kit / "scripts/validate_host.py").is_file()
    ):
        parser.error("--kit must point to a futhark_radeon source tree")
    if not args.skip_build:
        subprocess.run(
            [
                "cabal",
                "build",
                "exe:futhark",
                f"-j{args.jobs}",
                f"--ghc-options=-j{args.jobs}",
            ],
            cwd=ROOT,
            check=True,
        )
    compiler = Path(
        subprocess.check_output(
            ["cabal", "-v0", "list-bin", "exe:futhark"], cwd=ROOT, text=True
        ).strip()
    )
    if not compiler.is_file():
        parser.error(
            "Compiler executable is missing; rerun without --skip-build"
        )
    print("Compiler:", compiler, flush=True)
    targets = (
        ["verify-cpu", "build-c", "build-cpu"]
        if args.cpu_only
        else ["doctor-gpu", "verify", "build", "libraries"]
    )
    subprocess.run(
        [
            "make",
            "-C",
            str(kit),
            *targets,
            f"FUTRAD={compiler}",
            f"DEVICE={args.device}",
            f"THREADS={args.threads}",
        ],
        check=True,
    )


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode)
