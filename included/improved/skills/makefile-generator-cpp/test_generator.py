"""Exercise file generation separately from actual C++ compiler contracts."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
MAKE = os.environ.get("TASK_MAKE_BIN") or shutil.which("make")
CXX = os.environ.get("TASK_CXX_BIN") or shutil.which("g++")
BUILD_AVAILABLE = bool(MAKE and CXX and sys.platform.startswith("linux"))


def setUpModule() -> None:
    if os.environ.get("TASK_REQUIRE_CPP") == "1" and not BUILD_AVAILABLE:
        raise RuntimeError("Qualification requires GNU Make and GCC-compatible C++ with OpenMP on Linux")


class GeneratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="cpp make controls ")
        self.root = Path(self.temporary.name).resolve()
        if self.root.parent != Path(tempfile.gettempdir()).resolve():
            raise RuntimeError("Fixture directory differs from its explicit temporary parent")
        self.addCleanup(self.temporary.cleanup)
        self.environment = os.environ.copy()
        for name in (
            "CXX",
            "CXXFLAGS",
            "CPPFLAGS",
            "LDFLAGS",
            "LDLIBS",
            "MAKEFLAGS",
            "MFLAGS",
            "GNUMAKEFLAGS",
            "MAKEFILES",
        ):
            self.environment.pop(name, None)
        self.environment.update(OMP_NUM_THREADS="2", PYTHONDONTWRITEBYTECODE="1")
        (self.root / "src").mkdir()

    def run_command(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(args, cwd=self.root, env=self.environment, capture_output=True, text=True, timeout=30)

    def generate(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return self.run_command([sys.executable, "-B", str(PACKAGE / "generate.py"), "--name", "demo", *arguments])

    def make(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        if not MAKE or not CXX:
            self.fail("Compiler qualification prerequisites are missing")
        return self.run_command([str(MAKE), "-j2", "CXX=" + str(CXX), *arguments])

    def executable(self) -> subprocess.CompletedProcess[str]:
        return self.run_command([str(self.root / "build/demo")])

    def test_no_overwrite_invalid_name_and_freshness_check(self) -> None:
        first = self.generate()
        self.assertEqual(first.returncode, 0, first.stderr)
        original = (self.root / "Makefile").read_bytes()
        self.assertNotEqual(self.generate().returncode, 0)
        self.assertEqual((self.root / "Makefile").read_bytes(), original)
        self.assertEqual(self.generate("--check").returncode, 0)
        changed = original + b"\n# Project-specific edit\n"
        (self.root / "Makefile").write_bytes(changed)
        self.assertNotEqual(self.generate("--check").returncode, 0)
        self.assertEqual((self.root / "Makefile").read_bytes(), changed)
        invalid = self.generate("--name", "not a name", "--output", "invalid.mk")
        self.assertNotEqual(invalid.returncode, 0)
        self.assertFalse((self.root / "invalid.mk").exists())

    def test_missing_template_never_creates_output(self) -> None:
        directory = self.root / "isolated"
        directory.mkdir()
        shutil.copyfile(PACKAGE / "generate.py", directory / "generate.py")
        result = self.run_command([sys.executable, "-B", str(directory / "generate.py"), "--name", "demo"])
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(json.loads(result.stdout)["ok"])
        self.assertFalse((self.root / "Makefile").exists())

    @unittest.skipUnless(BUILD_AVAILABLE, "GNU Make and GCC C++ on Linux are required")
    def test_runtime_flags_reach_compilation_and_linking(self) -> None:
        source = (
            "#include <iostream>\n#include <omp.h>\nint main(){long long sum=0;\n"
            "#pragma omp parallel for reduction(+:sum)\n"
            'for(int i=1;i<=10000;++i)sum+=i;std::cout<<sum<<"\\n";return sum==50005000?0:1;}\n'
        )
        (self.root / "src/main.cpp").write_text(source, encoding="utf-8")
        self.assertEqual(self.generate().returncode, 0)
        built = self.make("CXXFLAGS=-O0 -fopenmp")
        self.assertEqual(built.returncode, 0, built.stderr)
        result = self.executable()
        self.assertEqual((result.returncode, result.stdout.strip()), (0, "50005000"))

    @unittest.skipUnless(BUILD_AVAILABLE, "GNU Make and GCC C++ on Linux are required")
    def test_distinct_extensions_keep_same_stem_objects_separate(self) -> None:
        files = {
            "unit.cpp": "int alpha(){return 4;}\n",
            "unit.cc": "int beta(){return 5;}\n",
            "main.cxx": '#include <iostream>\nint alpha();int beta();int main(){std::cout<<alpha()+beta()<<"\\n";}\n',
        }
        for name, text in files.items():
            (self.root / "src" / name).write_text(text, encoding="utf-8")
        self.assertEqual(self.generate().returncode, 0)
        result = self.make()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.executable().stdout.strip(), "9")

    @unittest.skipUnless(BUILD_AVAILABLE, "GNU Make and GCC C++ on Linux are required")
    def test_transitive_header_change_rebuilds_and_unchanged_graph_does_not(self) -> None:
        files = {
            "inner.hpp": "#define VALUE 7\n",
            "outer.hpp": '#include "inner.hpp"\n',
            "main.cpp": '#include "outer.hpp"\n#include <iostream>\nint main(){std::cout<<VALUE<<"\\n";}\n',
        }
        for name, text in files.items():
            (self.root / "src" / name).write_text(text, encoding="utf-8")
        self.assertEqual(self.generate().returncode, 0)
        built = self.make()
        self.assertEqual(built.returncode, 0, built.stderr)
        self.assertEqual(self.executable().stdout.strip(), "7")
        objects = list((self.root / "build").rglob("*.o"))
        before = {path: path.stat().st_mtime_ns for path in objects}
        self.assertEqual(self.make().returncode, 0)
        self.assertEqual(before, {path: path.stat().st_mtime_ns for path in objects})
        # Controlled past timestamps isolate header dependency behavior from
        # source edits, filesystem clock resolution and wall-clock sleeps.
        base = 1_000_000_000_000_000_000
        for name in files:
            os.utime(self.root / "src" / name, ns=(base, base))
        for path in [*objects, self.root / "build/demo"]:
            os.utime(path, ns=(base + 1_000_000_000, base + 1_000_000_000))
        header = self.root / "src/inner.hpp"
        header.write_text("#define VALUE 11\n", encoding="utf-8")
        os.utime(header, ns=(base + 2_000_000_000, base + 2_000_000_000))
        changed = self.make()
        self.assertEqual(changed.returncode, 0, changed.stderr)
        self.assertEqual(self.executable().stdout.strip(), "11")

    @unittest.skipUnless(BUILD_AVAILABLE, "GNU Make and GCC C++ on Linux are required")
    def test_linker_failure_is_preserved_and_no_test_target_is_invented(self) -> None:
        (self.root / "src/main.cpp").write_text("int main(){return 0;}\n", encoding="utf-8")
        self.assertEqual(self.generate().returncode, 0)
        invalid = self.make("LDFLAGS=-Wl,--cpp-control-invalid")
        self.assertNotEqual(invalid.returncode, 0)
        self.assertIn("cpp-control-invalid", invalid.stderr)
        self.assertNotEqual(self.make("test").returncode, 0)


if __name__ == "__main__":
    unittest.main()
