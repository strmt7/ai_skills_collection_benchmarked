from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GENERATOR = ROOT / "generate.py"
MAKE = os.environ.get("TASK_MAKE_BIN") or shutil.which("make")
COMPILER = shutil.which("gcc")


def setUpModule() -> None:
    if os.environ.get("TASK_REQUIRE_GNU") == "1":
        if not (MAKE and COMPILER and shutil.which("readelf") and sys.platform.startswith("linux")):
            raise RuntimeError("GNU make, GCC and readelf on Linux are required for this qualification")
        version = subprocess.run([str(MAKE), "--version"], capture_output=True, text=True, check=True, timeout=20)
        if not version.stdout.startswith("GNU Make "):
            raise RuntimeError("The selected make executable is not GNU make")


class GeneratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="make template test ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = os.environ.copy()
        for key in (
            "CC",
            "CFLAGS",
            "CPPFLAGS",
            "LDFLAGS",
            "LDLIBS",
            "PICFLAGS",
            "MAKEFLAGS",
            "MFLAGS",
            "GNUMAKEFLAGS",
            "MAKEFILES",
        ):
            self.env.pop(key, None)

    def generate(self, kind: str, name: str = "demo", output: str = "Makefile") -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(GENERATOR), "--kind", kind, "--name", name, "--output", output],
            cwd=self.root,
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )

    def test_generation_refuses_overwrite_and_invalid_name(self) -> None:
        first = self.generate("c")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertTrue(json.loads(first.stdout)["ok"])
        original = (self.root / "Makefile").read_bytes()
        repeat = self.generate("c-lib")
        self.assertNotEqual(repeat.returncode, 0)
        self.assertEqual((self.root / "Makefile").read_bytes(), original)
        invalid = self.generate("c", name="bad name", output="invalid.mk")
        self.assertNotEqual(invalid.returncode, 0)
        self.assertFalse((self.root / "invalid.mk").exists())

    def test_invalid_template_fails_without_creating_output(self) -> None:
        isolated = self.root / "generator-copy"
        isolated.mkdir()
        shutil.copyfile(GENERATOR, isolated / "generate.py")
        (isolated / "templates").mkdir()
        (isolated / "templates/c.mk").write_text("missing placeholder", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(isolated / "generate.py"), "--kind", "c", "--name", "demo"],
            cwd=self.root,
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(json.loads(result.stdout)["ok"])
        self.assertFalse((self.root / "Makefile").exists())

    @unittest.skipUnless(MAKE and sys.platform.startswith("linux"), "GNU make on Linux is required")
    def test_compiler_default_and_user_overrides(self) -> None:
        for kind in ("c", "c-lib"):
            path = kind + ".mk"
            self.assertEqual(self.generate(kind, output=path).returncode, 0)
            args = [
                str(MAKE),
                "--no-print-directory",
                "-f",
                path,
                "--eval=probe:;@printf '%s|%s\\n' '$(CC)' '$(origin CC)'",
                "probe",
            ]
            cases = [
                ([], {}, "gcc|file"),
                (["-R"], {}, "gcc|file"),
                ([], {"CC": "clang"}, "clang|environment"),
                (["CC=custom-cc"], {}, "custom-cc|command line"),
                ([], {"CC": ""}, "|environment"),
                (["CC="], {}, "|command line"),
            ]
            for extra, overrides, expected in cases:
                run = subprocess.run(
                    args + extra,
                    cwd=self.root,
                    env=self.env | overrides,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=20,
                )
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertEqual(run.stdout.strip(), expected)

    @unittest.skipUnless(
        MAKE and COMPILER and sys.platform.startswith("linux"), "GNU make and GCC on Linux are required"
    )
    def test_shared_library_honors_cflags_and_linker_overrides(self) -> None:
        for case in ("env_cflags", "cmd_cflags", "no_builtin", "invalid_ldflags", "missing_ldlibs", "empty_picflags"):
            d = self.root / case
            d.mkdir()
            (d / "src").mkdir()
            (d / "src/lib.c").write_text(
                "int shared_global = 42; int *get_global(void) { return &shared_global; }\n", encoding="utf-8"
            )
            created = subprocess.run(
                [sys.executable, str(GENERATOR), "--kind", "c-lib", "--name", "demo"],
                cwd=d,
                env=self.env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            e = self.env.copy()
            args = [str(MAKE), "--no-print-directory", "-j4", "all"]
            if case == "env_cflags":
                e["CFLAGS"] = "-O2"
            if case == "cmd_cflags":
                args.append("CFLAGS=-O2")
            if case == "no_builtin":
                args.append("-R")
            if case == "invalid_ldflags":
                args.append("LDFLAGS=-Wl,--this-option-does-not-exist")
            if case == "missing_ldlibs":
                args.append("LDLIBS=-lthis_library_does_not_exist")
            if case == "empty_picflags":
                args.extend(["CFLAGS=-O2", "PICFLAGS="])
            run = subprocess.run(args, cwd=d, env=e, capture_output=True, text=True, check=False, timeout=60)
            shared = d / "build/libdemo.so.1.0.0"
            if case in ("env_cflags", "cmd_cflags", "no_builtin"):
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertTrue(shared.is_file())
            else:
                self.assertNotEqual(run.returncode, 0)
                self.assertFalse(shared.exists())
                expected = {
                    "invalid_ldflags": "this-option-does-not-exist",
                    "missing_ldlibs": "this_library_does_not_exist",
                    "empty_picflags": "fPIC",
                }[case]
                self.assertIn(expected, run.stderr)

    @unittest.skipUnless(MAKE and sys.platform.startswith("linux"), "GNU make on Linux is required")
    def test_help_and_clean_work_with_a_makefile_name_containing_spaces(self) -> None:
        for kind in ("c", "c-lib"):
            name = kind + " project.mk"
            self.assertEqual(self.generate(kind, output=name).returncode, 0)
            help_run = subprocess.run(
                [str(MAKE), "--no-print-directory", "-R", "-f", name, "help"],
                cwd=self.root,
                env=self.env,
                capture_output=True,
                text=True,
                check=False,
                timeout=20,
            )
            self.assertEqual(help_run.returncode, 0, help_run.stderr)
            self.assertIn("all:", help_run.stdout)
            build = self.root / "build"
            build.mkdir(exist_ok=True)
            (build / "owned.txt").write_text("fixture", encoding="utf-8")
            clean = subprocess.run(
                [str(MAKE), "--no-print-directory", "-R", "-f", name, "clean"],
                cwd=self.root,
                env=self.env,
                capture_output=True,
                text=True,
                check=False,
                timeout=20,
            )
            self.assertEqual(clean.returncode, 0, clean.stderr)
            self.assertFalse(build.exists())

    @unittest.skipUnless(
        MAKE and COMPILER and sys.platform.startswith("linux"), "GNU make and GCC on Linux are required"
    )
    def test_builds_with_a_makefile_name_containing_spaces(self) -> None:
        for kind in ("c", "c-lib"):
            folder = self.root / kind
            folder.mkdir()
            (folder / "src").mkdir()
            (folder / "src/main.c").write_text("int main(void) { return 0; }\n", encoding="utf-8")
            name = "project build.mk"
            generated = subprocess.run(
                [sys.executable, str(GENERATOR), "--kind", kind, "--name", "demo", "--output", name],
                cwd=folder,
                env=self.env,
                capture_output=True,
                text=True,
                check=False,
                timeout=20,
            )
            self.assertEqual(generated.returncode, 0, generated.stderr)
            built = subprocess.run(
                [str(MAKE), "--no-print-directory", "-R", "-j4", "-f", name, "all"],
                cwd=folder,
                env=self.env,
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )
            self.assertEqual(built.returncode, 0, built.stderr)
            expected = "build/demo" if kind == "c" else "build/libdemo.so.1.0.0"
            self.assertTrue((folder / expected).is_file())

    @unittest.skipUnless(
        MAKE and COMPILER and shutil.which("readelf") and sys.platform.startswith("linux"),
        "GNU make, GCC and readelf on Linux are required",
    )
    def test_shared_library_uses_the_requested_soname(self) -> None:
        (self.root / "src").mkdir()
        (self.root / "src/lib.c").write_text("int value(void) { return 1; }\n", encoding="utf-8")
        self.assertEqual(self.generate("c-lib").returncode, 0)
        run = subprocess.run(
            [str(MAKE), "--no-print-directory", "-j4", "all", "SOVERSION=3"],
            cwd=self.root,
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        shared = self.root / "build/libdemo.so.3.0.0"
        self.assertTrue(shared.is_file())
        symbols = subprocess.run(["readelf", "-d", str(shared)], capture_output=True, text=True, check=True, timeout=20)
        self.assertTrue(any("SONAME" in line and "[libdemo.so.3]" in line for line in symbols.stdout.splitlines()))

    @unittest.skipUnless(
        MAKE and COMPILER and sys.platform.startswith("linux"), "GNU make and GCC on Linux are required"
    )
    def test_header_changes_rebuild_c_and_library_outputs(self) -> None:
        for kind in ("c", "c-lib"):
            d = self.root / kind
            d.mkdir()
            (d / "src").mkdir()
            header = d / "src/value.h"
            header.write_text("#define VALUE 1\n", encoding="utf-8")
            source = '#include "value.h"\n' + (
                "int main(void) { return VALUE; }\n"
                if kind == "c"
                else "int shared_global = VALUE; int get_value(void) { return shared_global; }\n"
            )
            (d / "src/main.c").write_text(source, encoding="utf-8")
            created = subprocess.run(
                [sys.executable, str(GENERATOR), "--kind", kind, "--name", "demo"],
                cwd=d,
                env=self.env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(created.returncode, 0, created.stderr)

            def build(directory: Path = d) -> None:
                r = subprocess.run(
                    [str(MAKE), "--no-print-directory", "all"],
                    cwd=directory,
                    env=self.env,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=60,
                )
                self.assertEqual(r.returncode, 0, r.stderr)

            def value(directory: Path = d, project_kind: str = kind) -> int:
                if project_kind == "c":
                    return subprocess.run([str(directory / "build/demo")], check=False).returncode
                code = "import ctypes,sys; print(ctypes.CDLL(sys.argv[1]).get_value())"
                r = subprocess.run(
                    [sys.executable, "-c", code, str(directory / "build/libdemo.so.1.0.0")],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                return int(r.stdout.strip())

            build()
            self.assertEqual(value(), 1)
            obj = d / "build/obj/main.o"
            stamp = obj.stat().st_mtime_ns - 2_000_000_000
            os.utime(obj, ns=(stamp, stamp))
            header.write_text("#define VALUE 2\n", encoding="utf-8")
            build()
            self.assertEqual(value(), 2)


if __name__ == "__main__":
    unittest.main()
