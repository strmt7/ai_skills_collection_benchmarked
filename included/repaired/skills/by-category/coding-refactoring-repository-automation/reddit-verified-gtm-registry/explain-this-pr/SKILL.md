---
name: explain-this-pr
description: Explain a pull request from verified changes, making incomplete review scope explicit and posting only when requested.
---

# Explain a pull request

Before repository work, read and apply Mandatory agent tools in the repository root at `docs/agent-tools.md`: Caveman for every task, CocoIndex Code before broad code navigation, and Crawl4AI for web-page research. Retain actual execution evidence.

Resolve the requested pull request using the available GitHub integration or CLI. Record its repository, state, base and head revisions, title and description. Read the changed-file inventory and relevant commits, then inspect the diff and surrounding code needed to understand each material change. For a large diff, work in bounded sections or by file; a filename list and the first 200 lines cannot establish what later changes do. Check that pagination and the provider's documented limits did not omit files, and treat unavailable binary changes, truncated patches, permissions and other missing content as unreviewed. If the base or head changes during the review, refresh the affected evidence or state that the explanation is for the earlier snapshot.

Explain the observed changes in plain language, naming the affected components and concrete before-and-after behavior when supported. Use the pull-request description or commits as attributed context, not proof of an outcome. Do not claim an exhaustive summary, unchanged behavior, a performance improvement or a reason that the evidence does not establish. When full inspection is impractical, say which parts were reviewed and what remains unknown. Keep the explanation as concise as the change permits.

Return the explanation to the user by default. Post a comment only when the user explicitly requests that action and the current tool and authorization rules permit it. If posting is requested, use a supported integration or safe multi-line input, then report the actual result and link. Do not post, create a pull request, or change its state merely because the user asks for an explanation.

The original upstream instructions and README are preserved under `provenance/`. A synthetic large-diff control demonstrates the excerpt limitation; it does not measure agent effectiveness or GitHub API behavior.
