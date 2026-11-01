---
name: makefile-generator-c
license: Apache-2.0
description: Generate and validate a focused GNU Make build for a C application or Linux ELF library.
---

# C Makefile generation

Before repository work, read and apply Mandatory agent tools in the repository root at `docs/agent-tools.md`: Caveman for every task, CocoIndex Code before broad code navigation, and Crawl4AI for web-page research. Retain actual execution evidence.

Inspect the actual project, build conventions, compiler, source layout, and requested targets first. This maintained package covers only a single `src` directory of C files whose names use only letters, digits, dots, underscores, and hyphens: a GNU Make C executable or a Linux ELF static/shared library built with GCC-compatible tools. It does not generate installation, deployment, or project-specific test targets. For another layout, language, platform, or toolchain, design and validate the appropriate build for that project instead of assuming these templates apply.

From a writable project directory, run the generator by its actual installed path. Choose an ASCII project name beginning with a letter or digit and containing only letters, digits, dots, underscores, or hyphens:

```text
python <installed-skill-directory>/generate.py --kind c --name demo --output Makefile
python <installed-skill-directory>/generate.py --kind c-lib --name demo --output Makefile
```

Use one command for the intended project. Existing output is never overwritten; the destination directory must already exist. A nonzero exit indicates failure. Review the generated Makefile before running it. The default source directory is `src` and the default output directory is `build`; `clean` removes that build directory. These templates do not infer whether the project has a test suite or fabricate a test command.

The compiler default applies only when GNU Make's `CC` is undefined or still its built-in default; explicit environment and command-line values are preserved. The ELF-library template uses a separate `PICFLAGS` default, so replacing `CFLAGS` alone does not remove position-independent compilation. Shared-library links include `LDFLAGS` and `LDLIBS`; `SOVERSION` and `VERSION` control the soname and output name. Headers use compiler-generated dependency files. When changing compiler or linker flags, clean or otherwise rebuild affected outputs before relying on the result.

Run `python -m unittest discover -s <installed-skill-directory> -p test_generator.py` to exercise the package. The build controls require GNU Make, GCC, `readelf`, and Linux; without those prerequisites the build-dependent tests are explicitly skipped. The recorded controls used GNU Make 4.4.1 and GCC 13.3.0 on Linux, plus Python generation checks on Windows. They do not establish support for every compiler or platform, or an improvement in agent effectiveness.

The original upstream skill is preserved at `provenance/original.SKILL.md`. This maintained package replaces only the two stated C-generation cases; other original templates remain unchanged and unqualified by this repair.
