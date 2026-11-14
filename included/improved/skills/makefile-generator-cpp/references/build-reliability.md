# Reliable incremental and recursive builds

Keep the existing build system and its supported tools. Inspect the installed
Make implementation, version and help before choosing options. The following
guidance concerns GNU Make with POSIX recipe utilities; native Windows tools
may require different recipes.

Generated files must describe the current inputs exactly. Regenerate the whole
file into an owned temporary output and replace the destination after success.
Appending a new source list to the previous generated translation unit retains
old inclusions and can introduce duplicate definitions. Track the configuration
that defines the source list as well as the current source files: a removed
file cannot invalidate an output merely by disappearing from a wildcard list.
For an explicit list stored in a Makefile, that Makefile is a prerequisite;
other ways of discovering sources need an equivalent change-tracking contract.
Keep distinct outputs for independent builds and configurations.

Check first generation, changed input, source addition/removal and a generation
failure. Confirm output contents and compile the result; a generator's zero exit
status alone does not prove a usable artifact. Preserve header dependencies and
the intended default goal when adding generated dependency files.

Represent required sub-builds as targets with actual prerequisite relationships.
For example, when `app` requires both libraries and each directory has a default
build target, this graph preserves child failures and allows the libraries to
build independently:

```makefile
.PHONY: all lib1 lib2 app
all: app
app: lib1 lib2
lib1 lib2 app:
	+$(MAKE) --no-print-directory -C "$@"
```

Adapt the directories and relationships to the real project. Use `$(MAKE)` for
recursive calls. A shell loop that runs several child builds without checking
each failure can return the final child's success after an earlier failure.
Verify a deliberately failing required child and an all-successful graph under
a bounded parallel invocation. Do not discard a failure to keep later work
running; independent in-flight jobs finishing does not make the build a pass.

Check a directory change before running the next command: `cd subdir && ...`
stops when that directory is unavailable. A semicolon can continue in the parent
directory and return a later command's success. For recursive Make, prefer its
explicit `-C` option when applicable. Verify the intended working directory,
including a missing-directory failure control.

For optional installation rules, stage installation and removal under an owned
temporary `DESTDIR`. Verify the installed filenames: installing `build/demo`
into a binary directory creates `demo`, not `build/demo` beneath that directory.
Uninstall must use the matching destination name and preserve unrelated staged
files. These controls do not justify running privileged installation commands or
changing host loader state.

Measure an optimization only after checking the same outputs and failure
behavior. Declare clean, incremental, changed-input and warm-cache workloads
separately. Hold inputs, compiler options, job count and tool versions constant;
record host contention, repeat comparisons in alternating order and retain all
failures. Do not copy illustrative speedup tables into project claims. A target
that retains object files is not evidence of a clean compilation workload.

Use supported diagnostics for the question being investigated. `--trace` shows
Make's update decisions; it is not a duration profiler. The reviewed GNU Make
4.3 executable rejects `--profile=profile.log`. Check the actual tool rather
than assuming another build debugger's options exist in GNU Make. Recipe timing
and whole-build timing also measure different work.

These recommendations follow source-grounded component controls for regenerated
C translation units and recursive dummy projects on GNU Make 4.3/Linux. They do
not establish C++ unity-build compatibility, faster builds, another Make
implementation's behavior or improved coding-agent performance. The optional
C++ scaffold does not add unity generation, recursive builds or flag tracking.
