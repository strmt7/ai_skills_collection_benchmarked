# C Makefile generation controls

The pinned Makefile generator's C templates declare `CC ?= gcc`. GNU Make already defines `CC`, so that conditional assignment leaves the built-in value `cc` in place. The versioned [GNU Make manual source](https://gnu.googlesource.com/make/+/refs/tags/4.4.1/doc/make.texi) describes conditional assignments, variable origins, and the built-in compiler default.

The original Linux library template also puts `-fPIC` in the default `CFLAGS` and omits `LDFLAGS` and `LDLIBS` from the shared-library link. Replacing `CFLAGS` can therefore remove the required position-independent compilation, and requested linker settings may be ignored. GCC describes [`-fPIC`](https://gcc.gnu.org/onlinedocs/gcc/Code-Gen-Options.html) as target-dependent position-independent code for shared libraries.

The maintained [C generator](../included/repaired/skills/by-category/coding-refactoring-repository-automation/latest-release-devops/makefile-generator-c/SKILL.md) provides two explicit templates: a C executable and a Linux ELF static/shared library. It preserves user compiler overrides, separates `PICFLAGS` from `CFLAGS`, passes link settings, and tracks header dependencies. It deliberately does not invent a project's test or installation commands. It supports a single `src` directory with C filenames made of letters, digits, dots, underscores, and hyphens; review and adapt the generated build to the actual project. The original mirror and original source are retained.

## Component evidence

A [source-bound control](../artifacts/repaired-skill-readiness/makefile-generator-c-v1/reproduce.py) generated builds from the original helper and the maintained package in separate temporary directories. On Linux x86-64 with GNU Make 4.4.1 and GCC 13.3.0:

| Check | Original | Maintained template |
| --- | --- | --- |
| Default compiler selection | `cc` from Make's built-in default | `gcc` from the template |
| `CFLAGS=-O2` in environment or command line | Shared link failed for the fixture | Shared link succeeded |
| Deliberately invalid `LDFLAGS` or missing `LDLIBS` library | Build succeeded because the settings were omitted | Link failed with the expected diagnostic |

The invalid linker inputs are negative controls; their failures are expected. The maintained package's own tests also check explicit and empty compiler overrides, parallel builds, header changes, shared-library sonames, no-overwrite behavior, and paths containing spaces. The [result and process outputs](../artifacts/repaired-skill-readiness/makefile-generator-c-v1/) describe the tested fixture only. They do not establish behavior for other compilers, platforms, source layouts, or coding agents.

The pinned and observed upstream revisions have the same generator and skill blobs; the [source observation](../artifacts/repaired-skill-readiness/makefile-generator-c-v1/upstream-observation.json) is limited to those files. The tested GNU Make archive came from GNU and its digest matched an independently pinned package recipe. Its manual source was byte-identical to the versioned Git mirror. The web manual pages timed out during the review; those failed Crawl4AI receipts were retained outside the checkout.

## Reproduce on Linux

With Python 3.11+, Bash, GNU Make and GCC installed, run from the repository root:

```bash
probe_dir=$(mktemp -d)
python artifacts/repaired-skill-readiness/makefile-generator-c-v1/reproduce.py \
  --source included/skills/by-category/coding-refactoring-repository-automation/latest-release-devops/makefile-generator/scripts/generate_makefile_template.sh \
  --repair included/repaired/skills/by-category/coding-refactoring-repository-automation/latest-release-devops/makefile-generator-c \
  --make "$(command -v make)" --scratch "$probe_dir/scratch" --output "$probe_dir/output"
```

The control checks the pinned source hash, records tool versions and process output in the temporary directory, and exits nonzero if the expected observations do not occur. It downloads nothing and does not modify the original skill or an existing Makefile. The maintained package's `test_generator.py` runs its broader build controls; On Windows, only the generator-file controls run; Linux build controls are skipped.
