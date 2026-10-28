# PPT Master SVG editor security notice

Avoid running the `ppt-master` local SVG editor until a repair has been
qualified. A browser control showed that content served from a different local
port could cause the editor to save staged changes in a temporary presentation.
The control reproduced the behavior in both the pinned v6.6.0 mirror and the
upstream v6.7.3 release checked on October 28, 2026.

The [security control record](../artifacts/research/2026-10-28/ppt-master-origin-security-control.json)
describes the source versions, test scope, evidence digests, and limitations.
An experimental candidate rejected the tested cross-port request, but it is not
distributed or qualified as a complete repair. The upstream mirror is unchanged,
and its existing security findings remain open. This result does not assess the
security of every `ppt-master` feature or measure coding-agent performance.
