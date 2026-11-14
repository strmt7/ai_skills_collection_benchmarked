---
name: makefile-generator-go
description: Author or repair GNU Make wrappers for Go modules, retaining Go's dependency discovery and build cache. Use when wrapper timestamps hide embedded-resource changes or build failures; preserve the project's existing build system and real test commands.
license: Apache-2.0
---

# Go build wrappers

Before repository work, read and apply Mandatory agent tools at the repository
root, `docs/agent-tools.md`: Caveman for every task, CocoIndex Code before broad
navigation, and Crawl4AI for web-page research. Retain actual execution evidence.
Original source text is retained in `provenance/`. This repair is unbenchmarked
for agent efficacy.

Inspect the actual Go module/workspace, supported toolchain, build commands,
package paths, output names and versioning first. Retain existing project
wrappers. Discover Go and Make instead of assuming their installation paths.
When missing, provision the project's compatible official SDK in an owned cache,
verify the publisher's archive checksum and tool version, and retain licenses;
do not alter global settings or install unrelated tools. Unsupported platforms
or unqualified setup remain explicit limitations.

Let Go own its dependency graph and compilation cache. A hand-written list of
`.go` files, `go.mod` and `go.sum` omits inputs such as `//go:embed` resources.
An unchanged list can keep an obsolete executable or hide a newly missing input.
Invoke the real Go build for each requested wrapper build, allowing Go to reuse
its own valid cached work. Do not force full recompilation to solve a stale
outer timestamp gate.

For an existing project whose variables already have the stated meanings, the
relevant rule shape is:

```makefile
.PHONY: build
build:
	$(GO) build $(LDFLAGS) -o $(PROJECT) $(GO_MAIN)
```

Here `GO` is the selected Go command, `PROJECT` is the intended output and
`GO_MAIN` is the actual main package. `LDFLAGS` must contain the project's Go
driver arguments if that convention is used; otherwise omit it. Do not invent a
`main.version` variable or copy flags from another project. This example assumes
space-free values; adapt argument quoting to the actual shell and paths.
Inspect and remove an obsolete timestamp gate instead of merely adding another
recipe over inherited prerequisites. Build before installing a binary rather
than installing an old output through the same incomplete dependency list.

Keep real `go test` commands and their failure statuses. Do not invent executable
self-test flags, ignore failures or call an absence of tests a tested result.
`go.sum` can legitimately be absent when a module has no external dependencies.

Verify the executable after changing only an embedded resource. Then remove a
required resource and require a real build failure. Check a genuine passing test
and an intentional test failure where the wrapper boundary changes. Account for
native build caching separately from build-speed comparisons.

The component controls used Go 1.27.4, GNU Make 4.3 and an isolated Linux x64
environment. They do not qualify every module, workspace, dependency graph,
native Windows build, installer or deployment command, or prove agent gains.
Python, Java, generic and security-related source branches are outside this
repair's runtime-qualified scope.
