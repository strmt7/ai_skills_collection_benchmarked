---
name: makefile-generator-cpp
description: Author or repair GNU Make builds for C++ executables, preserving compiler/linker flags, header dependencies and real project test contracts. Use the optional scaffold for a flat src directory; retain an existing build system unless the task requires changing it.
license: Apache-2.0
---

# C++ Makefile builds

Apply the repository's [mandatory agent tools](../../../../docs/agent-tools.md)
and controlling instructions before relevant work. Original sources are retained
in `provenance/`. This maintained overlay is unbenchmarked for agent efficacy.

Inspect the project's build commands, source graph and supported toolchain first.
Use its actual C++ compiler and standard. Discover tools rather than assuming
`make`, Bash or a compiler is installed. In this collection on Windows x64,
`./dev.ps1 python` supplies an isolated Python runtime for generation. Compiler
qualification uses a separately admitted environment; do not install global
packages or replace an existing build system to make a template applicable.

- Preserve compiler options through compilation and linking. `CXXFLAGS` can
  select language/runtime behavior that also requires link support. Keep
  `LDFLAGS` before object inputs and `LDLIBS` after them; use the C++ driver to
  link C++ objects. Respect project, environment and command-line overrides.
  For flag, configuration or mixed-language changes, check the
  [variable and configuration contracts](references/configuration-and-variables.md).
- Track included headers with compiler-generated dependency files. Build
  directories must exist before their recipes need them. Give distinct source
  files distinct object paths, including equal stems with different extensions.
- Use the project's real test command. An arbitrary executable's `--test`
  option or an echo-only target does not establish that tests ran. Add install,
  packaging or deployment targets only when the project needs and defines them.
  Qualify installation in an owned staging directory; uninstall must remove
  the installed names while preserving unrelated files.
- Before editing existing rules, inspect included Makefiles, expanded target
  names and multi-target rules. A line-based search cannot establish that a
  target is absent. Preserve the existing recipe and failure status; do not
  append generic targets with the original standard-target helper. Check the
  real command's behavior, including a failure control where practical.
- Verify a clean build, an unchanged rebuild, a changed transitive header and
  a failing compiler/linker option where those boundaries changed. Preserve
  independent work under parallel make; do not combine cleanup and a build as
  unordered parallel goals. Rebuild affected outputs after changing flags or
  toolchain settings; this scaffold does not track flag values automatically.
- For generated sources, recursive sub-builds or performance changes, apply
  [build reliability](references/build-reliability.md). Verify regeneration
  and failure propagation before measuring speed; an unchanged build is not a
  clean-build comparison.

For a new, flat `src` directory of `.cpp`, `.cc` and `.cxx` files with names using
letters, digits, dots, underscores or hyphens, an optional scaffold is available:

```text
python <installed-skill-directory>/generate.py --name demo --output Makefile
```

The destination parent must exist. Existing files are never overwritten; review
the Makefile before running it. `--check` compares an unmodified scaffold without
writing. The default C++20 flags are overridable. GNU Make, a GCC-compatible C++
driver and POSIX recipe utilities are required for this scaffold. A project root
containing spaces is supported; whitespace in source filenames, nested source
layouts, MSVC and shared libraries require project-specific rules.

Generation works independently of a compiler. Run package controls with
`python -B -m unittest discover -s <installed-skill-directory> -p test_generator.py`.
Build-dependent controls require GNU Make, GCC C++ and OpenMP on Linux; missing
tools are explicit skips unless `TASK_REQUIRE_CPP=1` requests qualification.
These component controls do not establish model improvement or full upstream
package readiness. The original security guide and other language templates
are outside this overlay's qualified scope.
