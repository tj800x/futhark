"""Check compiler selection and paths without a Haskell build or GPU."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

VERIFY = Path(__file__).with_name("verify.py")


class Workflow(unittest.TestCase):
    def test_build_and_select_compiler_with_spaces(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            kit = root / "kit with spaces"
            (kit / "scripts").mkdir(parents=True)
            (kit / "Makefile").touch()
            (kit / "scripts/validate_host.py").touch()
            compiler = root / "compiler with spaces"
            compiler.touch()
            log = root / "calls.jsonl"
            tool = (
                f"#!{sys.executable}\n"
                "import json, os, pathlib, sys\n"
                "name = pathlib.Path(sys.argv[0]).name\n"
                "with open(os.environ['WORKFLOW_TEST_LOG'], 'a') as out:\n"
                "    out.write(json.dumps([name, *sys.argv[1:]]) + '\\n')\n"
                "if name == 'cabal' and 'list-bin' in sys.argv:\n"
                "    print(os.environ['WORKFLOW_TEST_COMPILER'])\n"
            )
            for name in ("cabal", "make"):
                executable = root / name
                executable.write_text(tool)
                executable.chmod(0o755)
            env = dict(
                os.environ,
                PATH=str(root) + os.pathsep + os.environ["PATH"],
                WORKFLOW_TEST_LOG=str(log),
                WORKFLOW_TEST_COMPILER=str(compiler),
            )
            for options, targets, builds in [
                ([], ["doctor-gpu", "verify", "build", "libraries"], True),
                (
                    ["--skip-build", "--cpu-only"],
                    ["verify-cpu", "build-c", "build-cpu"],
                    False,
                ),
            ]:
                with self.subTest(options=options):
                    log.write_text("")
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(VERIFY),
                            "--kit",
                            str(kit),
                            "--threads",
                            "3",
                            *options,
                        ],
                        cwd=root,
                        env=env,
                        text=True,
                        capture_output=True,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    calls = [
                        json.loads(line)
                        for line in log.read_text().splitlines()
                    ]
                    self.assertEqual(
                        any(call[:2] == ["cabal", "build"] for call in calls),
                        builds,
                    )
                    self.assertEqual(
                        calls[-1],
                        [
                            "make",
                            "-C",
                            str(kit),
                            *targets,
                            f"FUTRAD={compiler}",
                            "DEVICE=AMD Radeon Pro 5500 XT",
                            "THREADS=3",
                        ],
                    )

    def test_help_and_invalid_input_do_not_require_toolchain(self):
        for options, expected in [
            (["--help"], 0),
            (["--kit", "/missing/kit"], 2),
            (["--kit", "/missing/kit", "--jobs", "0"], 2),
        ]:
            with self.subTest(options=options):
                result = subprocess.run(
                    [sys.executable, str(VERIFY), *options],
                    env=dict(os.environ, PATH=""),
                    capture_output=True,
                )
                self.assertEqual(result.returncode, expected)


if __name__ == "__main__":
    unittest.main()
