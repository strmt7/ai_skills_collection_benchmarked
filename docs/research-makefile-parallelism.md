# Makefile generator parallelism review

This partial review concerns the pinned `makefile-generator` skill from
`akin-ozer/cc-devops-skills`, source commit
`7fe7595e4512f8ce43dcf956aa5190b96d627dd1`. Its mirrored entrypoint has
SHA-256 `c0090361f2f9999c81050beb7d65aaf4338094559bd227d944aafbf1500286fe`.
The mirror is unchanged.

## Finding

The skill presents `.NOTPARALLEL: docker-build docker-push docker-run` as a way
to prevent those named targets from running in parallel. With GNU Make 4.4.1,
that declaration instead serializes the *prerequisites of each listed target*;
it does not, by itself, serialize the listed targets with one another. The
[GNU Make 4.4.1 release notes](https://github.com/mirror/make/blob/4.4.1/NEWS)
describe this prerequisite behavior.

The skill also shows `docker-push: docker-build` and
`docker-run: docker-build` as a serialization alternative. Those
dependencies ensure that the build completes before each dependent recipe.
They do not order the push and run recipes relative to one another when both
are requested through a parallel goal.

If operations truly must not overlap, express the actual ordering as
dependencies when that ordering is valid for all affected invocations. An
unqualified `.NOTPARALLEL:` serializes the entire current Make invocation,
with a broader performance cost; choose it only when that scope is intended.
Test the actual goal graph and supported Make versions instead of assuming that
either form provides a global lock.

## Independent control

The [control](../artifacts/research/2026-10-30/make-parallel-controls/reproduce.py)
uses dummy Python recipes named after the skill's three targets. Under
`make -j2`, both dependent recipes started after the shared build completed,
but their measured intervals overlapped with the skill's qualified
`.NOTPARALLEL` declaration. In the control with unqualified
`.NOTPARALLEL:`, those intervals did not overlap. No Docker build, push or
run operation was performed.

The [recorded output](../artifacts/research/2026-10-30/make-parallel-controls/result.json)
is from GNU Make 4.4.1 on x86-64 Alpine Linux with Python 3.13, using container
image `python@sha256:79e7a9b9ff1cbceff819f856fb374477792a5967759d94df266de7b7b4120e6f`.
The container installed Make from its configured Alpine package repository;
the package repository itself was not frozen. To repeat the control in a
disposable Linux environment with Python 3 and GNU Make 4.4.1 available:

```text
python artifacts/research/2026-10-30/make-parallel-controls/reproduce.py
```

The timing intervals demonstrate the observed overlap in this run, not a
performance benchmark. The control does not establish the behavior of older
Make versions, other implementations, recursive builds, or every target graph.

## Evidence and remaining work

The release notes were captured and reviewed with Crawl4AI
`0.9.5+catalog.portable4` on 30 October 2026; the native result returned HTTP
200 with substantive relevant content and SHA-256
`9801109d29ddb131c163b80c7d1a13c8a30366cb8e5a003347e7e9b381864da9`.
The GNU-hosted manual page timed out and its failure was retained. The GitHub
page for the complete manual did not expose the relevant text in its extracted
content and was not accepted as a page source. The exact versioned manual
blob was separately retrieved through the Git Data API, verified against Git
blob ID `aa488eb79b61a70fa887f3303a6a9e039345537f`, and retained locally; its
content SHA-256 is
`4bc3c176c7eacefae7fdafd0665138372943f9e15cf6b6e816ad8062a31689dd`.

This is a source-and-component finding. It does not show whether an agent
following the skill would generate a faulty build, nor does it measure agent
performance. An independently evaluated repair or upstream correction remains
necessary.
