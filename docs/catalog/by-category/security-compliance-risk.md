# Security, compliance & risk

## dependency-update-bot - Varnan-Tech/opendirectory `packages/cli/skills/dependency-update-bot/SKILL.md`

- Skill page: [varnan-tech-opendirectory-packages-cli-skills-dependency-update-bot](../skills/by-category/security-compliance-risk/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-dependency-update-bot.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-dependency-update-bot`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-dependency-update-bot/SKILL.md`
- Source: [Varnan-Tech/opendirectory `packages/cli/skills/dependency-update-bot/SKILL.md`](https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/dependency-update-bot/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `bc01f7c1c31f`
- What it covers: Catalog summary: Scans your project for outdated npm, pip, Cargo, Go, or Ruby packages. Runs a CVE security audit. Fetches changelogs, summarizes breaking changes with Gemini, and opens one PR per risk group (patch, minor, major). Includes Diagnosis Mode for install conflicts. Use when asked to update dependencies, check for outdated packages, open dependency PRs, scan for package updates, audit for CVEs, or flag breaking changes.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Dependency Update Bot, Step 1: Setup Check, Step 2: Detect Outdated Packages, If cargo-outdated not installed: cargo install cargo-outdated, Step 3: Classify by Risk Level. Resources: has_references.
- Notability: Included from Reddit r/codex open-source Codex skills signal; GitHub SKILL.md files verified with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-varnan-tech-opendirectory-packages-cli-skills-dependency-update-bot-skill-md`: Use the immutable source file https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/dependency-update-bot/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## llms-txt-generator - Varnan-Tech/opendirectory `packages/cli/skills/llms-txt-generator/SKILL.md`

- Skill page: [varnan-tech-opendirectory-packages-cli-skills-llms-txt-generator](../skills/by-category/security-compliance-risk/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-llms-txt-generator.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-llms-txt-generator`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-llms-txt-generator/SKILL.md`
- Source: [Varnan-Tech/opendirectory `packages/cli/skills/llms-txt-generator/SKILL.md`](https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/llms-txt-generator/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `bc01f7c1c31f`
- What it covers: Catalog summary: Generates and maintains a standards-compliant llms.txt file for any website — either by crawling the live site OR by reading the website's codebase directly. Use this skill when asked to create an llms.txt, add AI discoverability to a site, improve GEO (Generative Engine Optimization), make a website readable by AI agents, generate an llms-full.txt, check if a site has llms.txt, or audit a site's AI readiness for.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: llms.txt Generator, Workflow, Step 1: Detect Source — Codebase or Live Site?, Step 2A: Codebase Mode — Read the Repo Directly, Step 2B: Live Site Mode — Get Target URL. Resources: has_references.
- Notability: Included from Reddit r/codex open-source Codex skills signal; GitHub SKILL.md files verified with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-varnan-tech-opendirectory-packages-cli-skills-llms-txt-generator-skill-md`: Use the immutable source file https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/llms-txt-generator/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## security-review - affaan-m/everything-claude-code `.agents/skills/security-review/SKILL.md`

- Skill page: [affaan-m-everything-claude-code-agents-skills-security-review](../skills/by-category/security-compliance-risk/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-security-review.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-security-review`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-security-review/SKILL.md`
- Source: [affaan-m/everything-claude-code `.agents/skills/security-review/SKILL.md`](https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/security-review/SKILL.md)
- Selected ref: `v1.10.0`; commit `846ffb75da9a`
- What it covers: Catalog summary: Use this skill when adding authentication, handling user input, working with secrets, creating API endpoints, or implementing payment/sensitive features. Provides comprehensive security checklist and patterns.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Security Review Skill, When to Activate, Security Checklist, 1. Secrets Management, FAIL: NEVER Do This. Resources: has_agents_metadata.
- Notability: Included from selected repository structure reference with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-affaan-m-everything-claude-code-agents-skills-security-review-skill-md`: Use the immutable source file https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/security-review/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## x-api - affaan-m/everything-claude-code `.agents/skills/x-api/SKILL.md`

- Skill page: [affaan-m-everything-claude-code-agents-skills-x-api](../skills/by-category/security-compliance-risk/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-x-api.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-x-api`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-x-api/SKILL.md`
- Source: [affaan-m/everything-claude-code `.agents/skills/x-api/SKILL.md`](https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/x-api/SKILL.md)
- Selected ref: `v1.10.0`; commit `846ffb75da9a`
- What it covers: Catalog summary: X/Twitter API integration for posting tweets, threads, reading timelines, search, and analytics. Covers OAuth auth patterns, rate limits, and platform-native content posting. Use when the user wants to interact with X programmatically.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: X API, When to Activate, Authentication, OAuth 2.0 Bearer Token (App-Only), Environment setup. Resources: has_agents_metadata.
- Notability: Included from selected repository structure reference with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-affaan-m-everything-claude-code-agents-skills-x-api-skill-md`: Use the immutable source file https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/x-api/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## ci-cd - ahmedasmar/devops-claude-skills `ci-cd/skills/SKILL.md`

- Skill page: [ahmedasmar-devops-claude-skills-ci-cd-skills](../skills/by-category/security-compliance-risk/devops-reference/ahmedasmar-devops-claude-skills-ci-cd-skills.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/devops-reference/ahmedasmar-devops-claude-skills-ci-cd-skills`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/devops-reference/ahmedasmar-devops-claude-skills-ci-cd-skills/SKILL.md`
- Source: [ahmedasmar/devops-claude-skills `ci-cd/skills/SKILL.md`](https://github.com/ahmedasmar/devops-claude-skills/blob/1489c33ad8829a11219e423327d6b59f8339cee4/ci-cd/skills/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `1489c33ad882`
- What it covers: Catalog summary: CI/CD pipeline design, optimization, DevSecOps security scanning, and troubleshooting. Use this skill whenever the user mentions CI/CD, GitHub Actions, GitLab CI, pipelines, workflows, builds, or DevSecOps. Triggers include creating new CI/CD workflows, debugging pipeline failures or flaky tests, implementing SAST/DAST/SCA security scanning, optimizing slow builds with caching or parallelization, setting up.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: CI/CD Pipelines, Core Workflows, 1. Creating a New Pipeline, 1. Fast feedback (lint, format) - <1 min, 2. Unit tests - 1-5 min. Resources: has_scripts, has_references, has_assets.
- Notability: Included from DevOps skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-ahmedasmar-devops-claude-skills-ci-cd-skills-skill-md`: Use the immutable source file https://github.com/ahmedasmar/devops-claude-skills/blob/1489c33ad8829a11219e423327d6b59f8339cee4/ci-cd/skills/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## ansible-validator - akin-ozer/cc-devops-skills `devops-skills-plugin/skills/ansible-validator/SKILL.md`

- Skill page: [akin-ozer-cc-devops-skills-devops-skills-plugin-skills-ansible-validator](../skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-ansible-validator.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-ansible-validator`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-ansible-validator/SKILL.md`
- Source: [akin-ozer/cc-devops-skills `devops-skills-plugin/skills/ansible-validator/SKILL.md`](https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/ansible-validator/SKILL.md)
- Selected ref: `v1.0.0`; commit `7fe7595e4512`
- What it covers: Catalog summary: Validate, lint, audit, or debug Ansible playbooks, roles, inventories, FQCN, tasks.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Ansible Validator, Overview, Trigger Guidance, When to Use This Skill, Preflight (Run First). Resources: has_scripts, has_references, has_assets.
- Notability: Included from latest release DevOps skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Move long background material into references/ to keep SKILL.md concise.
- Assigned benchmark scenarios:
  - `skill-proof-akin-ozer-cc-devops-skills-devops-skills-plugin-skills-ansible-validator-skill-md`: Use the immutable source file https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/ansible-validator/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## bash-script-validator - akin-ozer/cc-devops-skills `devops-skills-plugin/skills/bash-script-validator/SKILL.md`

- Skill page: [akin-ozer-cc-devops-skills-devops-skills-plugin-skills-bash-script-validator](../skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-bash-script-validator.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-bash-script-validator`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-bash-script-validator/SKILL.md`
- Source: [akin-ozer/cc-devops-skills `devops-skills-plugin/skills/bash-script-validator/SKILL.md`](https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/bash-script-validator/SKILL.md)
- Selected ref: `v1.0.0`; commit `7fe7595e4512`
- What it covers: Catalog summary: Validate, lint, audit, or fix bash/shell/.sh scripts via ShellCheck.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Bash Script Validator, Overview, Trigger Guidance, Trigger Phrases, Non-Trigger Examples. Resources: has_scripts, has_examples.
- Notability: Included from latest release DevOps skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-akin-ozer-cc-devops-skills-devops-skills-plugin-skills-bash-script-validator-skill-md`: Use the immutable source file https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/bash-script-validator/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## dockerfile-validator - akin-ozer/cc-devops-skills `devops-skills-plugin/skills/dockerfile-validator/SKILL.md`

- Skill page: [akin-ozer-cc-devops-skills-devops-skills-plugin-skills-dockerfile-validator](../skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-dockerfile-validator.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-dockerfile-validator`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-dockerfile-validator/SKILL.md`
- Source: [akin-ozer/cc-devops-skills `devops-skills-plugin/skills/dockerfile-validator/SKILL.md`](https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/dockerfile-validator/SKILL.md)
- Selected ref: `v1.0.0`; commit `7fe7595e4512`
- What it covers: Catalog summary: Validate, lint, audit, or scan a Dockerfile for security and best practices.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Dockerfile Validator, Trigger Phrases, Use / Do Not Use, Local Files In This Skill, Deterministic Execution Flow (Required). Resources: has_scripts, has_references, has_examples.
- Notability: Included from latest release DevOps skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-akin-ozer-cc-devops-skills-devops-skills-plugin-skills-dockerfile-validator-skill-md`: Use the immutable source file https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/dockerfile-validator/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## fluentbit-validator - akin-ozer/cc-devops-skills `devops-skills-plugin/skills/fluentbit-validator/SKILL.md`

- Skill page: [akin-ozer-cc-devops-skills-devops-skills-plugin-skills-fluentbit-validator](../skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-fluentbit-validator.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-fluentbit-validator`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-fluentbit-validator/SKILL.md`
- Source: [akin-ozer/cc-devops-skills `devops-skills-plugin/skills/fluentbit-validator/SKILL.md`](https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/fluentbit-validator/SKILL.md)
- Selected ref: `v1.0.0`; commit `7fe7595e4512`
- What it covers: Catalog summary: Validate, lint, audit, or check Fluent Bit configs (INPUT, FILTER, OUTPUT, tag routing).
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Fluent Bit Validator, Trigger Phrases, Execution Model, Stage 0: Precheck (Required), Stage 1: Static Validation (Required). Resources: has_scripts.
- Notability: Included from latest release DevOps skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-akin-ozer-cc-devops-skills-devops-skills-plugin-skills-fluentbit-validator-skill-md`: Use the immutable source file https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/fluentbit-validator/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## github-actions-validator - akin-ozer/cc-devops-skills `devops-skills-plugin/skills/github-actions-validator/SKILL.md`

- Skill page: [akin-ozer-cc-devops-skills-devops-skills-plugin-skills-github-actions-validator](../skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-github-actions-validator.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-github-actions-validator`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-github-actions-validator/SKILL.md`
- Source: [akin-ozer/cc-devops-skills `devops-skills-plugin/skills/github-actions-validator/SKILL.md`](https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/github-actions-validator/SKILL.md)
- Selected ref: `v1.0.0`; commit `7fe7595e4512`
- What it covers: Catalog summary: Validate, lint, audit, fix GitHub Actions workflows (.github/workflows).
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: GitHub Actions Validator, Overview, Trigger Phrases, When to Use This Skill, Required Execution Flow. Resources: has_scripts, has_references, has_examples.
- Notability: Included from latest release DevOps skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Move long background material into references/ to keep SKILL.md concise.
- Assigned benchmark scenarios:
  - `skill-proof-akin-ozer-cc-devops-skills-devops-skills-plugin-skills-github-actions-validator-skill-md`: Use the immutable source file https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/github-actions-validator/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## gitlab-ci-validator - akin-ozer/cc-devops-skills `devops-skills-plugin/skills/gitlab-ci-validator/SKILL.md`

- Skill page: [akin-ozer-cc-devops-skills-devops-skills-plugin-skills-gitlab-ci-validator](../skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-gitlab-ci-validator.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-gitlab-ci-validator`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-gitlab-ci-validator/SKILL.md`
- Source: [akin-ozer/cc-devops-skills `devops-skills-plugin/skills/gitlab-ci-validator/SKILL.md`](https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/gitlab-ci-validator/SKILL.md)
- Selected ref: `v1.0.0`; commit `7fe7595e4512`
- What it covers: Catalog summary: Validate, lint, audit, or fix .gitlab-ci.yml pipelines, stages, and jobs.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: GitLab CI/CD Validator, Trigger Phrases, Setup And Prerequisites (Run First), Ensure validator scripts are executable, Required runtime. Resources: has_scripts, has_examples.
- Notability: Included from latest release DevOps skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-akin-ozer-cc-devops-skills-devops-skills-plugin-skills-gitlab-ci-validator-skill-md`: Use the immutable source file https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/gitlab-ci-validator/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## helm-validator - akin-ozer/cc-devops-skills `devops-skills-plugin/skills/helm-validator/SKILL.md`

- Skill page: [akin-ozer-cc-devops-skills-devops-skills-plugin-skills-helm-validator](../skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-helm-validator.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-helm-validator`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-helm-validator/SKILL.md`
- Source: [akin-ozer/cc-devops-skills `devops-skills-plugin/skills/helm-validator/SKILL.md`](https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/helm-validator/SKILL.md)
- Selected ref: `v1.0.0`; commit `7fe7595e4512`
- What it covers: Catalog summary: Validate, lint, audit, check Helm charts — Chart.yaml, templates, values.yaml, CRDs, schemas.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Helm Chart Validator & Analysis Toolkit, Overview, Trigger Cases, Role Boundaries, Execution Model. Resources: has_scripts, has_references, has_assets.
- Notability: Included from latest release DevOps skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Move long background material into references/ to keep SKILL.md concise.
- Assigned benchmark scenarios:
  - `skill-proof-akin-ozer-cc-devops-skills-devops-skills-plugin-skills-helm-validator-skill-md`: Use the immutable source file https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/helm-validator/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## jenkinsfile-validator - akin-ozer/cc-devops-skills `devops-skills-plugin/skills/jenkinsfile-validator/SKILL.md`

- Skill page: [akin-ozer-cc-devops-skills-devops-skills-plugin-skills-jenkinsfile-validator](../skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-jenkinsfile-validator.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-jenkinsfile-validator`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-jenkinsfile-validator/SKILL.md`
- Source: [akin-ozer/cc-devops-skills `devops-skills-plugin/skills/jenkinsfile-validator/SKILL.md`](https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/jenkinsfile-validator/SKILL.md)
- Selected ref: `v1.0.0`; commit `7fe7595e4512`
- What it covers: Catalog summary: Validate, lint, audit, or check Jenkinsfiles and shared libraries.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Jenkinsfile Validator Skill, Trigger Phrases, Scope, Prerequisites, Required tools. Resources: has_scripts, has_references, has_examples.
- Notability: Included from latest release DevOps skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-akin-ozer-cc-devops-skills-devops-skills-plugin-skills-jenkinsfile-validator-skill-md`: Use the immutable source file https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/jenkinsfile-validator/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## k8s-yaml-generator - akin-ozer/cc-devops-skills `devops-skills-plugin/skills/k8s-yaml-generator/SKILL.md`

- Skill page: [akin-ozer-cc-devops-skills-devops-skills-plugin-skills-k8s-yaml-generator](../skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-k8s-yaml-generator.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-k8s-yaml-generator`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-k8s-yaml-generator/SKILL.md`
- Source: [akin-ozer/cc-devops-skills `devops-skills-plugin/skills/k8s-yaml-generator/SKILL.md`](https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/k8s-yaml-generator/SKILL.md)
- Selected ref: `v1.0.0`; commit `7fe7595e4512`
- What it covers: Catalog summary: Generate/create/scaffold Kubernetes YAML — Deployment, Service, ConfigMap, Ingress, RBAC, StatefulSet, CRDs.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Kubernetes YAML Generator, Trigger Guidance, Execution Model, 1) Preflight, 2) Capture Required Inputs. Resources: has_references, has_examples.
- Notability: Included from latest release DevOps skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-akin-ozer-cc-devops-skills-devops-skills-plugin-skills-k8s-yaml-generator-skill-md`: Use the immutable source file https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/k8s-yaml-generator/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## k8s-yaml-validator - akin-ozer/cc-devops-skills `devops-skills-plugin/skills/k8s-yaml-validator/SKILL.md`

- Skill page: [akin-ozer-cc-devops-skills-devops-skills-plugin-skills-k8s-yaml-validator](../skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-k8s-yaml-validator.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-k8s-yaml-validator`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-k8s-yaml-validator/SKILL.md`
- Source: [akin-ozer/cc-devops-skills `devops-skills-plugin/skills/k8s-yaml-validator/SKILL.md`](https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/k8s-yaml-validator/SKILL.md)
- Selected ref: `v1.0.0`; commit `7fe7595e4512`
- What it covers: Catalog summary: Validate, lint, audit, or dry-run Kubernetes manifests (Deployment, Service, ConfigMap, CRD).
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Kubernetes YAML Validator, Overview, Trigger Phrases, When to Use This Skill, Read-Only Boundary (Mandatory). Resources: has_scripts, has_references, has_assets.
- Notability: Included from latest release DevOps skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Move long background material into references/ to keep SKILL.md concise.
- Assigned benchmark scenarios:
  - `skill-proof-akin-ozer-cc-devops-skills-devops-skills-plugin-skills-k8s-yaml-validator-skill-md`: Use the immutable source file https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/k8s-yaml-validator/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## makefile-validator - akin-ozer/cc-devops-skills `devops-skills-plugin/skills/makefile-validator/SKILL.md`

- Skill page: [akin-ozer-cc-devops-skills-devops-skills-plugin-skills-makefile-validator](../skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-makefile-validator.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-makefile-validator`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-makefile-validator/SKILL.md`
- Source: [akin-ozer/cc-devops-skills `devops-skills-plugin/skills/makefile-validator/SKILL.md`](https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/makefile-validator/SKILL.md)
- Selected ref: `v1.0.0`; commit `7fe7595e4512`
- What it covers: Catalog summary: Validate, lint, audit, or check Makefiles and .mk files for errors.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Makefile Validator, Overview, Trigger Guidance, Trigger Phrases, Non-Trigger Examples. Resources: has_scripts, has_examples.
- Notability: Included from latest release DevOps skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-akin-ozer-cc-devops-skills-devops-skills-plugin-skills-makefile-validator-skill-md`: Use the immutable source file https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/makefile-validator/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## promql-validator - akin-ozer/cc-devops-skills `devops-skills-plugin/skills/promql-validator/SKILL.md`

- Skill page: [akin-ozer-cc-devops-skills-devops-skills-plugin-skills-promql-validator](../skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-promql-validator.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-promql-validator`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-promql-validator/SKILL.md`
- Source: [akin-ozer/cc-devops-skills `devops-skills-plugin/skills/promql-validator/SKILL.md`](https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/promql-validator/SKILL.md)
- Selected ref: `v1.0.0`; commit `7fe7595e4512`
- What it covers: Catalog summary: Validate, lint, audit, or fix PromQL queries and alerting rules; detects anti-patterns.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: How This Skill Works, Workflow, Working Directory Requirement, Step 1: Validate Syntax, Step 2: Check Best Practices. Resources: has_scripts, has_examples.
- Notability: Included from latest release DevOps skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-akin-ozer-cc-devops-skills-devops-skills-plugin-skills-promql-validator-skill-md`: Use the immutable source file https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/promql-validator/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## terraform-validator - akin-ozer/cc-devops-skills `devops-skills-plugin/skills/terraform-validator/SKILL.md`

- Skill page: [akin-ozer-cc-devops-skills-devops-skills-plugin-skills-terraform-validator](../skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-terraform-validator.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-terraform-validator`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-terraform-validator/SKILL.md`
- Source: [akin-ozer/cc-devops-skills `devops-skills-plugin/skills/terraform-validator/SKILL.md`](https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/terraform-validator/SKILL.md)
- Selected ref: `v1.0.0`; commit `7fe7595e4512`
- What it covers: Catalog summary: Validate, lint, audit, or plan Terraform/.tf/HCL files; runs tflint, checkov, terraform validate.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Terraform Validator, ⚠️ Critical Requirements Checklist, When to Use This Skill, External Documentation, Validation Workflow. Resources: has_scripts, has_references.
- Notability: Included from latest release DevOps skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Move long background material into references/ to keep SKILL.md concise.
- Assigned benchmark scenarios:
  - `skill-proof-akin-ozer-cc-devops-skills-devops-skills-plugin-skills-terraform-validator-skill-md`: Use the immutable source file https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/terraform-validator/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## terragrunt-validator - akin-ozer/cc-devops-skills `devops-skills-plugin/skills/terragrunt-validator/SKILL.md`

- Skill page: [akin-ozer-cc-devops-skills-devops-skills-plugin-skills-terragrunt-validator](../skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-terragrunt-validator.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-terragrunt-validator`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-terragrunt-validator/SKILL.md`
- Source: [akin-ozer/cc-devops-skills `devops-skills-plugin/skills/terragrunt-validator/SKILL.md`](https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/terragrunt-validator/SKILL.md)
- Selected ref: `v1.0.0`; commit `7fe7595e4512`
- What it covers: Catalog summary: Validate, lint, audit, or check Terragrunt .hcl/terragrunt.hcl files, stacks, modules, compliance.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Terragrunt Validator, Overview, Terragrunt Version Compatibility, CLI Command Migration Reference, Key Changes in 0.93+:. Resources: has_scripts, has_references.
- Notability: Included from latest release DevOps skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Move long background material into references/ to keep SKILL.md concise.
- Assigned benchmark scenarios:
  - `skill-proof-akin-ozer-cc-devops-skills-devops-skills-plugin-skills-terragrunt-validator-skill-md`: Use the immutable source file https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/terragrunt-validator/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## customer-winback - composio-community/support-skills `customer-winback/SKILL.md`

- Skill page: [composio-community-support-skills-customer-winback](../skills/by-category/security-compliance-risk/support-reference/composio-community-support-skills-customer-winback.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/support-reference/composio-community-support-skills-customer-winback`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/support-reference/composio-community-support-skills-customer-winback/SKILL.md`
- Source: [composio-community/support-skills `customer-winback/SKILL.md`](https://github.com/composio-community/support-skills/blob/b4f842c3cbdcae0c45771fd996c396aee80dde2e/customer-winback/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `b4f842c3cbdc`
- What it covers: Catalog summary: Identify churned or at-risk customers and draft personalized winback emails
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Customer Winback Campaign, Workflow, Step 1: Discover tools, Step 2: Identify at-risk customers, Step 3: Build risk profiles. Resources: none observed.
- Notability: Included from customer support skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-composio-community-support-skills-customer-winback-skill-md`: Use the immutable source file https://github.com/composio-community/support-skills/blob/b4f842c3cbdcae0c45771fd996c396aee80dde2e/customer-winback/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## sla-monitor - composio-community/support-skills `sla-monitor/SKILL.md`

- Skill page: [composio-community-support-skills-sla-monitor](../skills/by-category/security-compliance-risk/support-reference/composio-community-support-skills-sla-monitor.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/support-reference/composio-community-support-skills-sla-monitor`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/support-reference/composio-community-support-skills-sla-monitor/SKILL.md`
- Source: [composio-community/support-skills `sla-monitor/SKILL.md`](https://github.com/composio-community/support-skills/blob/b4f842c3cbdcae0c45771fd996c396aee80dde2e/sla-monitor/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `b4f842c3cbdc`
- What it covers: Catalog summary: Check SLA compliance across open tickets and flag breaches or at-risk tickets
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: SLA Monitor, Workflow, Step 1: Discover tools, Step 2: Define SLA targets, Step 3: Fetch open tickets. Resources: none observed.
- Notability: Included from customer support skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-composio-community-support-skills-sla-monitor-skill-md`: Use the immutable source file https://github.com/composio-community/support-skills/blob/b4f842c3cbdcae0c45771fd996c396aee80dde2e/sla-monitor/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## ckm:brand - nextlevelbuilder/ui-ux-pro-max-skill `.claude/skills/brand/SKILL.md`

- Skill page: [nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-brand](../skills/by-category/security-compliance-risk/latest-release-creative/nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-brand.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/latest-release-creative/nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-brand`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/latest-release-creative/nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-brand/SKILL.md`
- Source: [nextlevelbuilder/ui-ux-pro-max-skill `.claude/skills/brand/SKILL.md`](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/07f4ef3ac2568c25a3b0c8ef5165a86abc3e56e4/.claude/skills/brand/SKILL.md)
- Selected ref: `v2.5.0`; commit `07f4ef3ac256`
- What it covers: Catalog summary: Brand voice, visual identity, messaging frameworks, asset management, brand consistency. Activate for branded content, tone of voice, marketing assets, brand compliance, style guides.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Brand, When to Use, Quick Start, Brand Sync Workflow, 1. Edit docs/brand-guidelines.md (or use /brand update). Resources: has_scripts, has_references.
- Notability: Included from latest release UI/UX skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-brand-skill-md`: Use the immutable source file https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/07f4ef3ac2568c25a3b0c8ef5165a86abc3e56e4/.claude/skills/brand/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## agentic-actions-auditor - trailofbits/skills `plugins/agentic-actions-auditor/skills/agentic-actions-auditor/SKILL.md`

- Skill page: [trailofbits-skills-plugins-agentic-actions-auditor-skills-agentic-actions-auditor](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-agentic-actions-auditor-skills-agentic-actions-auditor.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-agentic-actions-auditor-skills-agentic-actions-auditor`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-agentic-actions-auditor-skills-agentic-actions-auditor/SKILL.md`
- Source: [trailofbits/skills `plugins/agentic-actions-auditor/skills/agentic-actions-auditor/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/agentic-actions-auditor/skills/agentic-actions-auditor/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Audits GitHub Actions workflows for security vulnerabilities in AI agent integrations including Claude Code Action, Gemini CLI, OpenAI Codex, and GitHub AI Inference. Detects attack vectors where attacker-controlled input reaches AI agents running in CI/CD pipelines, including env var intermediary patterns, direct expression injection, dangerous sandbox configurations, and wildcard user allowlists. Use when.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Agentic Actions Auditor, When to Use, When NOT to Use, Rationalizations to Reject, Audit Methodology. Resources: has_references.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-agentic-actions-auditor-skills-agentic-actions-auditor-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/agentic-actions-auditor/skills/agentic-actions-auditor/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## audit-context-building - trailofbits/skills `plugins/audit-context-building/skills/audit-context-building/SKILL.md`

- Skill page: [trailofbits-skills-plugins-audit-context-building-skills-audit-context-building](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-audit-context-building-skills-audit-context-building.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-audit-context-building-skills-audit-context-building`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-audit-context-building-skills-audit-context-building/SKILL.md`
- Source: [trailofbits/skills `plugins/audit-context-building/skills/audit-context-building/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/audit-context-building/skills/audit-context-building/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Enables ultra-granular, line-by-line code analysis to build deep architectural context before vulnerability or bug finding.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Deep Context Builder Skill (Ultra-Granular Pure Context Mode), 1. Purpose, 2. When to Use This Skill, 3. How This Skill Behaves, Rationalizations (Do Not Skip). Resources: none observed.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-audit-context-building-skills-audit-context-building-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/audit-context-building/skills/audit-context-building/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## algorand-vulnerability-scanner - trailofbits/skills `plugins/building-secure-contracts/skills/algorand-vulnerability-scanner/SKILL.md`

- Skill page: [trailofbits-skills-plugins-building-secure-contracts-skills-algorand-vulnerability-scanner](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-building-secure-contracts-skills-algorand-vulnerability-scanner.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-building-secure-contracts-skills-algorand-vulnerability-scanner`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-building-secure-contracts-skills-algorand-vulnerability-scanner/SKILL.md`
- Source: [trailofbits/skills `plugins/building-secure-contracts/skills/algorand-vulnerability-scanner/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/building-secure-contracts/skills/algorand-vulnerability-scanner/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Scans Algorand smart contracts for 11 common vulnerabilities including rekeying attacks, unchecked transaction fees, missing field validations, and access control issues. Use when auditing Algorand projects (TEAL/PyTeal).
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Algorand Vulnerability Scanner, 1. Purpose, 2. When to Use This Skill, 3. Platform Detection, File Extensions & Indicators. Resources: none observed.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-building-secure-contracts-skills-algorand-vulnerability-scanner-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/building-secure-contracts/skills/algorand-vulnerability-scanner/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## audit-prep-assistant - trailofbits/skills `plugins/building-secure-contracts/skills/audit-prep-assistant/SKILL.md`

- Skill page: [trailofbits-skills-plugins-building-secure-contracts-skills-audit-prep-assistant](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-building-secure-contracts-skills-audit-prep-assistant.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-building-secure-contracts-skills-audit-prep-assistant`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-building-secure-contracts-skills-audit-prep-assistant/SKILL.md`
- Source: [trailofbits/skills `plugins/building-secure-contracts/skills/audit-prep-assistant/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/building-secure-contracts/skills/audit-prep-assistant/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Prepares codebases for security review using Trail of Bits' checklist. Helps set review goals, runs static analysis tools, increases test coverage, removes dead code, ensures accessibility, and generates documentation (flowcharts, user stories, inline comments).
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Audit Prep Assistant, Purpose, The Preparation Process, Step 1: Set Review Goals, Step 2: Resolve Easy Issues. Resources: none observed.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-building-secure-contracts-skills-audit-prep-assistant-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/building-secure-contracts/skills/audit-prep-assistant/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## cairo-vulnerability-scanner - trailofbits/skills `plugins/building-secure-contracts/skills/cairo-vulnerability-scanner/SKILL.md`

- Skill page: [trailofbits-skills-plugins-building-secure-contracts-skills-cairo-vulnerability-scanner](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-building-secure-contracts-skills-cairo-vulnerability-scanner.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-building-secure-contracts-skills-cairo-vulnerability-scanner`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-building-secure-contracts-skills-cairo-vulnerability-scanner/SKILL.md`
- Source: [trailofbits/skills `plugins/building-secure-contracts/skills/cairo-vulnerability-scanner/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/building-secure-contracts/skills/cairo-vulnerability-scanner/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Scans Cairo/StarkNet smart contracts for 6 critical vulnerabilities including felt252 arithmetic overflow, L1-L2 messaging issues, address conversion problems, and signature replay. Use when auditing StarkNet projects.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Cairo/StarkNet Vulnerability Scanner, 1. Purpose, 2. When to Use This Skill, 3. Platform Detection, File Extensions & Indicators. Resources: none observed.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-building-secure-contracts-skills-cairo-vulnerability-scanner-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/building-secure-contracts/skills/cairo-vulnerability-scanner/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## secure-workflow-guide - trailofbits/skills `plugins/building-secure-contracts/skills/secure-workflow-guide/SKILL.md`

- Skill page: [trailofbits-skills-plugins-building-secure-contracts-skills-secure-workflow-guide](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-building-secure-contracts-skills-secure-workflow-guide.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-building-secure-contracts-skills-secure-workflow-guide`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-building-secure-contracts-skills-secure-workflow-guide/SKILL.md`
- Source: [trailofbits/skills `plugins/building-secure-contracts/skills/secure-workflow-guide/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/building-secure-contracts/skills/secure-workflow-guide/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Guides through Trail of Bits' 5-step secure development workflow. Runs Slither scans, checks special features (upgradeability/ERC conformance/token integration), generates visual security diagrams, helps document security properties for fuzzing/verification, and reviews manual security areas.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Secure Workflow Guide, Purpose, The 5-Step Workflow, Step 1: Check for Known Security Issues, Step 2: Check Special Features. Resources: none observed.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-building-secure-contracts-skills-secure-workflow-guide-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/building-secure-contracts/skills/secure-workflow-guide/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## solana-vulnerability-scanner - trailofbits/skills `plugins/building-secure-contracts/skills/solana-vulnerability-scanner/SKILL.md`

- Skill page: [trailofbits-skills-plugins-building-secure-contracts-skills-solana-vulnerability-scanner](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-building-secure-contracts-skills-solana-vulnerability-scanner.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-building-secure-contracts-skills-solana-vulnerability-scanner`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-building-secure-contracts-skills-solana-vulnerability-scanner/SKILL.md`
- Source: [trailofbits/skills `plugins/building-secure-contracts/skills/solana-vulnerability-scanner/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/building-secure-contracts/skills/solana-vulnerability-scanner/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Scans Solana programs for 6 critical vulnerabilities including arbitrary CPI, improper PDA validation, missing signer/ownership checks, and sysvar spoofing. Use when auditing Solana/Anchor programs.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Solana Vulnerability Scanner, 1. Purpose, 2. When to Use This Skill, 3. Platform Detection, File Extensions & Indicators. Resources: none observed.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-building-secure-contracts-skills-solana-vulnerability-scanner-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/building-secure-contracts/skills/solana-vulnerability-scanner/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## substrate-vulnerability-scanner - trailofbits/skills `plugins/building-secure-contracts/skills/substrate-vulnerability-scanner/SKILL.md`

- Skill page: [trailofbits-skills-plugins-building-secure-contracts-skills-substrate-vulnerability-scanner](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-building-secure-contracts-skills-substrate-vulnerability-scanner.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-building-secure-contracts-skills-substrate-vulnerability-scanner`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-building-secure-contracts-skills-substrate-vulnerability-scanner/SKILL.md`
- Source: [trailofbits/skills `plugins/building-secure-contracts/skills/substrate-vulnerability-scanner/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/building-secure-contracts/skills/substrate-vulnerability-scanner/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Scans Substrate/Polkadot pallets for 7 critical vulnerabilities including arithmetic overflow, panic DoS, incorrect weights, and bad origin checks. Use when auditing Substrate runtimes or FRAME pallets.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Substrate Vulnerability Scanner, 1. Purpose, 2. When to Use This Skill, 3. Platform Detection, File Extensions & Indicators. Resources: none observed.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-building-secure-contracts-skills-substrate-vulnerability-scanner-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/building-secure-contracts/skills/substrate-vulnerability-scanner/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## ton-vulnerability-scanner - trailofbits/skills `plugins/building-secure-contracts/skills/ton-vulnerability-scanner/SKILL.md`

- Skill page: [trailofbits-skills-plugins-building-secure-contracts-skills-ton-vulnerability-scanner](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-building-secure-contracts-skills-ton-vulnerability-scanner.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-building-secure-contracts-skills-ton-vulnerability-scanner`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-building-secure-contracts-skills-ton-vulnerability-scanner/SKILL.md`
- Source: [trailofbits/skills `plugins/building-secure-contracts/skills/ton-vulnerability-scanner/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/building-secure-contracts/skills/ton-vulnerability-scanner/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Scans TON (The Open Network) smart contracts for 3 critical vulnerabilities including integer-as-boolean misuse, fake Jetton contracts, and forward TON without gas checks. Use when auditing FunC contracts.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: TON Vulnerability Scanner, 1. Purpose, 2. When to Use This Skill, 3. Platform Detection, File Extensions & Indicators. Resources: none observed.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-building-secure-contracts-skills-ton-vulnerability-scanner-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/building-secure-contracts/skills/ton-vulnerability-scanner/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## burpsuite-project-parser - trailofbits/skills `plugins/burpsuite-project-parser/skills/burpsuite-project-parser/SKILL.md`

- Skill page: [trailofbits-skills-plugins-burpsuite-project-parser-skills-burpsuite-project-parser](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-burpsuite-project-parser-skills-burpsuite-project-parser.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-burpsuite-project-parser-skills-burpsuite-project-parser`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-burpsuite-project-parser-skills-burpsuite-project-parser/SKILL.md`
- Source: [trailofbits/skills `plugins/burpsuite-project-parser/skills/burpsuite-project-parser/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/burpsuite-project-parser/skills/burpsuite-project-parser/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Searches and explores Burp Suite project files (.burp) from the command line. Use when searching response headers or bodies with regex patterns, extracting security audit findings, dumping proxy history or site map data, or analyzing HTTP traffic captured in a Burp project.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Burp Project Parser, When to Use, Prerequisites, Quick Reference, Sub-Component Filters (USE THESE). Resources: has_scripts.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-burpsuite-project-parser-skills-burpsuite-project-parser-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/burpsuite-project-parser/skills/burpsuite-project-parser/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## constant-time-analysis - trailofbits/skills `plugins/constant-time-analysis/skills/constant-time-analysis/SKILL.md`

- Skill page: [trailofbits-skills-plugins-constant-time-analysis-skills-constant-time-analysis](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-constant-time-analysis-skills-constant-time-analysis.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-constant-time-analysis-skills-constant-time-analysis`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-constant-time-analysis-skills-constant-time-analysis/SKILL.md`
- Source: [trailofbits/skills `plugins/constant-time-analysis/skills/constant-time-analysis/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/constant-time-analysis/skills/constant-time-analysis/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Detects timing side-channel vulnerabilities in cryptographic code. Use when implementing or reviewing crypto code, encountering division on secrets, secret-dependent branches, or constant-time programming questions in C, C++, Go, Rust, Swift, Java, Kotlin, C#, PHP, JavaScript, TypeScript, Python, or Ruby.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Constant-Time Analysis, When to Use, When NOT to Use, Language Selection, Quick Start. Resources: has_references.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-constant-time-analysis-skills-constant-time-analysis-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/constant-time-analysis/skills/constant-time-analysis/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## differential-review - trailofbits/skills `plugins/differential-review/skills/differential-review/SKILL.md`

- Skill page: [trailofbits-skills-plugins-differential-review-skills-differential-review](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-differential-review-skills-differential-review.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-differential-review-skills-differential-review`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-differential-review-skills-differential-review/SKILL.md`
- Source: [trailofbits/skills `plugins/differential-review/skills/differential-review/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/differential-review/skills/differential-review/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Performs security-focused differential review of code changes (PRs, commits, diffs). Adapts analysis depth to codebase size, uses git history for context, calculates blast radius, checks test coverage, and generates comprehensive markdown reports. Automatically detects and prevents security regressions.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Differential Security Review, Core Principles, Rationalizations (Do Not Skip), Quick Reference, Codebase Size Strategy. Resources: none observed.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-differential-review-skills-differential-review-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/differential-review/skills/differential-review/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## entry-point-analyzer - trailofbits/skills `plugins/entry-point-analyzer/skills/entry-point-analyzer/SKILL.md`

- Skill page: [trailofbits-skills-plugins-entry-point-analyzer-skills-entry-point-analyzer](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-entry-point-analyzer-skills-entry-point-analyzer.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-entry-point-analyzer-skills-entry-point-analyzer`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-entry-point-analyzer-skills-entry-point-analyzer/SKILL.md`
- Source: [trailofbits/skills `plugins/entry-point-analyzer/skills/entry-point-analyzer/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/entry-point-analyzer/skills/entry-point-analyzer/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Analyzes smart contract codebases to identify state-changing entry points for security auditing. Detects externally callable functions that modify state, categorizes them by access level (public, admin, role-restricted, contract-only), and generates structured audit reports. Excludes view/pure/read-only functions. Use when auditing smart contracts (Solidity, Vyper, Solana/Rust, Move, TON, CosmWasm) or when asked to.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Entry Point Analyzer, When to Use, When NOT to Use, Scope: State-Changing Functions Only, Workflow. Resources: has_references.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-entry-point-analyzer-skills-entry-point-analyzer-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/entry-point-analyzer/skills/entry-point-analyzer/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## fp-check - trailofbits/skills `plugins/fp-check/skills/fp-check/SKILL.md`

- Skill page: [trailofbits-skills-plugins-fp-check-skills-fp-check](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-fp-check-skills-fp-check.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-fp-check-skills-fp-check`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-fp-check-skills-fp-check/SKILL.md`
- Source: [trailofbits/skills `plugins/fp-check/skills/fp-check/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/fp-check/skills/fp-check/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Systematically verifies suspected security bugs to eliminate false positives. Produces TRUE POSITIVE or FALSE POSITIVE verdicts with documented evidence for each bug.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: False Positive Check, When to Use, When NOT to Use, Rationalizations to Reject, Step 0: Understand the Claim and Context. Resources: has_references.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-fp-check-skills-fp-check-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/fp-check/skills/fp-check/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## insecure-defaults - trailofbits/skills `plugins/insecure-defaults/skills/insecure-defaults/SKILL.md`

- Skill page: [trailofbits-skills-plugins-insecure-defaults-skills-insecure-defaults](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-insecure-defaults-skills-insecure-defaults.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-insecure-defaults-skills-insecure-defaults`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-insecure-defaults-skills-insecure-defaults/SKILL.md`
- Source: [trailofbits/skills `plugins/insecure-defaults/skills/insecure-defaults/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/insecure-defaults/skills/insecure-defaults/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Detects fail-open insecure defaults (hardcoded secrets, weak auth, permissive security) that allow apps to run insecurely in production. Use when auditing security, reviewing config management, or analyzing environment variable handling.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Insecure Defaults Detection, When to Use, When NOT to Use, Rationalizations to Reject, Workflow. Resources: has_references.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-insecure-defaults-skills-insecure-defaults-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/insecure-defaults/skills/insecure-defaults/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## seatbelt-sandboxer - trailofbits/skills `plugins/seatbelt-sandboxer/skills/seatbelt-sandboxer/SKILL.md`

- Skill page: [trailofbits-skills-plugins-seatbelt-sandboxer-skills-seatbelt-sandboxer](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-seatbelt-sandboxer-skills-seatbelt-sandboxer.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-seatbelt-sandboxer-skills-seatbelt-sandboxer`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-seatbelt-sandboxer-skills-seatbelt-sandboxer/SKILL.md`
- Source: [trailofbits/skills `plugins/seatbelt-sandboxer/skills/seatbelt-sandboxer/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/seatbelt-sandboxer/skills/seatbelt-sandboxer/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Generates minimal macOS Seatbelt sandbox configurations. Use when sandboxing, isolating, or restricting macOS applications with allowlist-based profiles.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: macOS Seatbelt Sandbox Profiling, When to Use, When NOT to Use, Profiling Methodology, Step 1: Identify Application Requirements. Resources: none observed.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-seatbelt-sandboxer-skills-seatbelt-sandboxer-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/seatbelt-sandboxer/skills/seatbelt-sandboxer/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## semgrep-rule-creator - trailofbits/skills `plugins/semgrep-rule-creator/skills/semgrep-rule-creator/SKILL.md`

- Skill page: [trailofbits-skills-plugins-semgrep-rule-creator-skills-semgrep-rule-creator](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-semgrep-rule-creator-skills-semgrep-rule-creator.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-semgrep-rule-creator-skills-semgrep-rule-creator`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-semgrep-rule-creator-skills-semgrep-rule-creator/SKILL.md`
- Source: [trailofbits/skills `plugins/semgrep-rule-creator/skills/semgrep-rule-creator/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/semgrep-rule-creator/skills/semgrep-rule-creator/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Creates custom Semgrep rules for detecting security vulnerabilities, bug patterns, and code patterns. Use when writing Semgrep rules or building custom static analysis detections.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Semgrep Rule Creator, When to Use, When NOT to Use, Rationalizations to Reject, Anti-Patterns. Resources: has_references.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-semgrep-rule-creator-skills-semgrep-rule-creator-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/semgrep-rule-creator/skills/semgrep-rule-creator/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## semgrep-rule-variant-creator - trailofbits/skills `plugins/semgrep-rule-variant-creator/skills/semgrep-rule-variant-creator/SKILL.md`

- Skill page: [trailofbits-skills-plugins-semgrep-rule-variant-creator-skills-semgrep-rule-variant-creator](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-semgrep-rule-variant-creator-skills-semgrep-rule-variant-creator.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-semgrep-rule-variant-creator-skills-semgrep-rule-variant-creator`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-semgrep-rule-variant-creator-skills-semgrep-rule-variant-creator/SKILL.md`
- Source: [trailofbits/skills `plugins/semgrep-rule-variant-creator/skills/semgrep-rule-variant-creator/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/semgrep-rule-variant-creator/skills/semgrep-rule-variant-creator/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Creates language variants of existing Semgrep rules. Use when porting a Semgrep rule to specified target languages. Takes an existing rule and target languages as input, produces independent rule+test directories for each language.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Semgrep Rule Variant Creator, When to Use, When NOT to Use, Input Specification, Output Specification. Resources: has_references.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-semgrep-rule-variant-creator-skills-semgrep-rule-variant-creator-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/semgrep-rule-variant-creator/skills/semgrep-rule-variant-creator/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## sharp-edges - trailofbits/skills `plugins/sharp-edges/skills/sharp-edges/SKILL.md`

- Skill page: [trailofbits-skills-plugins-sharp-edges-skills-sharp-edges](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-sharp-edges-skills-sharp-edges.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-sharp-edges-skills-sharp-edges`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-sharp-edges-skills-sharp-edges/SKILL.md`
- Source: [trailofbits/skills `plugins/sharp-edges/skills/sharp-edges/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/sharp-edges/skills/sharp-edges/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Identifies error-prone APIs, dangerous configurations, and footgun designs that enable security mistakes. Use when reviewing API designs, configuration schemas, cryptographic library ergonomics, or evaluating whether code follows 'secure by default' and 'pit of success' principles. Triggers: footgun, misuse-resistant, secure defaults, API usability, dangerous configuration.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Sharp Edges Analysis, When to Use, When NOT to Use, Core Principle, Rationalizations to Reject. Resources: has_references.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-sharp-edges-skills-sharp-edges-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/sharp-edges/skills/sharp-edges/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## spec-to-code-compliance - trailofbits/skills `plugins/spec-to-code-compliance/skills/spec-to-code-compliance/SKILL.md`

- Skill page: [trailofbits-skills-plugins-spec-to-code-compliance-skills-spec-to-code-compliance](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-spec-to-code-compliance-skills-spec-to-code-compliance.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-spec-to-code-compliance-skills-spec-to-code-compliance`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-spec-to-code-compliance-skills-spec-to-code-compliance/SKILL.md`
- Source: [trailofbits/skills `plugins/spec-to-code-compliance/skills/spec-to-code-compliance/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/spec-to-code-compliance/skills/spec-to-code-compliance/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Verifies code implements exactly what documentation specifies for blockchain audits. Use when comparing code against whitepapers, finding gaps between specs and implementation, or performing compliance checks for protocol implementations.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: When to Use, When NOT to Use, Spec-to-Code Compliance Checker Skill, GLOBAL RULES, Rationalizations (Do Not Skip). Resources: none observed.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-spec-to-code-compliance-skills-spec-to-code-compliance-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/spec-to-code-compliance/skills/spec-to-code-compliance/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## codeql - trailofbits/skills `plugins/static-analysis/skills/codeql/SKILL.md`

- Skill page: [trailofbits-skills-plugins-static-analysis-skills-codeql](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-static-analysis-skills-codeql.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-static-analysis-skills-codeql`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-static-analysis-skills-codeql/SKILL.md`
- Source: [trailofbits/skills `plugins/static-analysis/skills/codeql/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/static-analysis/skills/codeql/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Scans a codebase for security vulnerabilities using CodeQL's interprocedural data flow and taint tracking analysis. Triggers on "run codeql", "codeql scan", "codeql analysis", "build codeql database", or "find vulnerabilities with codeql". Supports "run all" (security-and-quality + security-experimental suites) and "important only" (high-precision security findings) scan modes. Also handles creating data extension.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: CodeQL Analysis, Essential Principles, Output Directory, Resolve output directory, Database Discovery. Resources: has_references.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-static-analysis-skills-codeql-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/static-analysis/skills/codeql/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## sarif-parsing - trailofbits/skills `plugins/static-analysis/skills/sarif-parsing/SKILL.md`

- Skill page: [trailofbits-skills-plugins-static-analysis-skills-sarif-parsing](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-static-analysis-skills-sarif-parsing.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-static-analysis-skills-sarif-parsing`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-static-analysis-skills-sarif-parsing/SKILL.md`
- Source: [trailofbits/skills `plugins/static-analysis/skills/sarif-parsing/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/static-analysis/skills/sarif-parsing/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Parses and processes SARIF files from static analysis tools like CodeQL, Semgrep, or other scanners. Triggers on "parse sarif", "read scan results", "aggregate findings", "deduplicate alerts", or "process sarif output". Handles filtering, deduplication, format conversion, and CI/CD integration of SARIF data. Does NOT run scans — use the Semgrep or CodeQL skills for that.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: SARIF Parsing Best Practices, When to Use, When NOT to Use, SARIF Structure Overview, Why Fingerprinting Matters. Resources: none observed.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-static-analysis-skills-sarif-parsing-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/static-analysis/skills/sarif-parsing/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## semgrep - trailofbits/skills `plugins/static-analysis/skills/semgrep/SKILL.md`

- Skill page: [trailofbits-skills-plugins-static-analysis-skills-semgrep](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-static-analysis-skills-semgrep.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-static-analysis-skills-semgrep`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-static-analysis-skills-semgrep/SKILL.md`
- Source: [trailofbits/skills `plugins/static-analysis/skills/semgrep/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/static-analysis/skills/semgrep/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Run Semgrep static analysis scan on a codebase using single-session review passes. Supports two scan modes — "run all" (full ruleset coverage) and "important only" (high-confidence security vulnerabilities). Automatically detects and uses Semgrep Pro for cross-file taint analysis when available. Use when asked to scan code for vulnerabilities, run a security audit with Semgrep, find bugs, or perform static.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Semgrep Security Scan, Essential Principles, When to Use, When NOT to Use, Output Directory. Resources: has_scripts, has_references.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-static-analysis-skills-semgrep-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/static-analysis/skills/semgrep/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## supply-chain-risk-auditor - trailofbits/skills `plugins/supply-chain-risk-auditor/skills/supply-chain-risk-auditor/SKILL.md`

- Skill page: [trailofbits-skills-plugins-supply-chain-risk-auditor-skills-supply-chain-risk-auditor](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-supply-chain-risk-auditor-skills-supply-chain-risk-auditor.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-supply-chain-risk-auditor-skills-supply-chain-risk-auditor`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-supply-chain-risk-auditor-skills-supply-chain-risk-auditor/SKILL.md`
- Source: [trailofbits/skills `plugins/supply-chain-risk-auditor/skills/supply-chain-risk-auditor/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/supply-chain-risk-auditor/skills/supply-chain-risk-auditor/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Identifies dependencies at heightened risk of exploitation or takeover. Use when assessing supply chain attack surface, evaluating dependency health, or scoping security engagements.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Supply Chain Risk Auditor, When to Use, When NOT to Use, Purpose, Risk Criteria. Resources: none observed.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-supply-chain-risk-auditor-skills-supply-chain-risk-auditor-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/supply-chain-risk-auditor/skills/supply-chain-risk-auditor/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## cargo-fuzz - trailofbits/skills `plugins/testing-handbook-skills/skills/cargo-fuzz/SKILL.md`

- Skill page: [trailofbits-skills-plugins-testing-handbook-skills-skills-cargo-fuzz](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-testing-handbook-skills-skills-cargo-fuzz.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-testing-handbook-skills-skills-cargo-fuzz`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-testing-handbook-skills-skills-cargo-fuzz/SKILL.md`
- Source: [trailofbits/skills `plugins/testing-handbook-skills/skills/cargo-fuzz/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/testing-handbook-skills/skills/cargo-fuzz/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Cargo-fuzz is the de facto fuzzing tool for Rust projects using Cargo. Use for fuzzing Rust code with libFuzzer backend.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: cargo-fuzz, When to Use, Quick Start, ![no_main], Edit fuzz/fuzz_targets/fuzz_target_1.rs with your harness. Resources: none observed.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-testing-handbook-skills-skills-cargo-fuzz-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/testing-handbook-skills/skills/cargo-fuzz/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## harness-writing - trailofbits/skills `plugins/testing-handbook-skills/skills/harness-writing/SKILL.md`

- Skill page: [trailofbits-skills-plugins-testing-handbook-skills-skills-harness-writing](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-testing-handbook-skills-skills-harness-writing.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-testing-handbook-skills-skills-harness-writing`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-testing-handbook-skills-skills-harness-writing/SKILL.md`
- Source: [trailofbits/skills `plugins/testing-handbook-skills/skills/harness-writing/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/testing-handbook-skills/skills/harness-writing/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Techniques for writing effective fuzzing harnesses across languages. Use when creating new fuzz targets or improving existing harness code.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Writing Fuzzing Harnesses, Overview, Key Concepts, When to Apply, Quick Reference. Resources: none observed.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
  - Move long background material into references/ to keep SKILL.md concise.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-testing-handbook-skills-skills-harness-writing-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/testing-handbook-skills/skills/harness-writing/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## ossfuzz - trailofbits/skills `plugins/testing-handbook-skills/skills/ossfuzz/SKILL.md`

- Skill page: [trailofbits-skills-plugins-testing-handbook-skills-skills-ossfuzz](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-testing-handbook-skills-skills-ossfuzz.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-testing-handbook-skills-skills-ossfuzz`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-testing-handbook-skills-skills-ossfuzz/SKILL.md`
- Source: [trailofbits/skills `plugins/testing-handbook-skills/skills/ossfuzz/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/testing-handbook-skills/skills/ossfuzz/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: OSS-Fuzz provides free continuous fuzzing for open source projects. Use when setting up continuous fuzzing infrastructure or enrolling projects.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: OSS-Fuzz, Overview, Key Concepts, When to Apply, Quick Reference. Resources: none observed.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-testing-handbook-skills-skills-ossfuzz-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/testing-handbook-skills/skills/ossfuzz/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## testing-handbook-generator - trailofbits/skills `plugins/testing-handbook-skills/skills/testing-handbook-generator/SKILL.md`

- Skill page: [trailofbits-skills-plugins-testing-handbook-skills-skills-testing-handbook-generator](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-testing-handbook-skills-skills-testing-handbook-generator.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-testing-handbook-skills-skills-testing-handbook-generator`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-testing-handbook-skills-skills-testing-handbook-generator/SKILL.md`
- Source: [trailofbits/skills `plugins/testing-handbook-skills/skills/testing-handbook-generator/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/testing-handbook-skills/skills/testing-handbook-generator/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Meta-skill that analyzes the Trail of Bits Testing Handbook (appsec.guide) and generates Claude Code skills for security testing tools and techniques. Use when creating new skills based on handbook content.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Testing Handbook Skill Generator, When to Use, Handbook Location, Workflow Overview, Scope Restrictions. Resources: none observed.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-testing-handbook-skills-skills-testing-handbook-generator-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/testing-handbook-skills/skills/testing-handbook-generator/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## audit-augmentation - trailofbits/skills `plugins/trailmark/skills/audit-augmentation/SKILL.md`

- Skill page: [trailofbits-skills-plugins-trailmark-skills-audit-augmentation](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-trailmark-skills-audit-augmentation.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-trailmark-skills-audit-augmentation`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-trailmark-skills-audit-augmentation/SKILL.md`
- Source: [trailofbits/skills `plugins/trailmark/skills/audit-augmentation/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/trailmark/skills/audit-augmentation/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Augments Trailmark code graphs with external audit findings from SARIF static analysis results and weAudit annotation files. Maps findings to graph nodes by file and line overlap, creates severity-based subgraphs, and enables cross-referencing findings with pre-analysis data (blast radius, taint, etc.). Use when projecting SARIF results onto a code graph, overlaying weAudit annotations, cross-referencing Semgrep or.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Audit Augmentation, When to Use, When NOT to Use, Rationalizations to Reject, Installation. Resources: has_references.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-trailmark-skills-audit-augmentation-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/trailmark/skills/audit-augmentation/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## graph-evolution - trailofbits/skills `plugins/trailmark/skills/graph-evolution/SKILL.md`

- Skill page: [trailofbits-skills-plugins-trailmark-skills-graph-evolution](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-trailmark-skills-graph-evolution.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-trailmark-skills-graph-evolution`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-trailmark-skills-graph-evolution/SKILL.md`
- Source: [trailofbits/skills `plugins/trailmark/skills/graph-evolution/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/trailmark/skills/graph-evolution/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Compares Trailmark code graphs at two source code snapshots (git commits, tags, or directories) to surface security-relevant structural changes. Detects new attack paths, complexity shifts, blast radius growth, taint propagation changes, and privilege boundary modifications that text diffs miss. Use when comparing code between commits or tags, analyzing structural evolution, detecting attack surface growth,.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Graph Evolution, When to Use, When NOT to Use, Rationalizations to Reject, Prerequisites. Resources: has_scripts, has_references.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-trailmark-skills-graph-evolution-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/trailmark/skills/graph-evolution/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## mermaid-to-proverif - trailofbits/skills `plugins/trailmark/skills/mermaid-to-proverif/SKILL.md`

- Skill page: [trailofbits-skills-plugins-trailmark-skills-mermaid-to-proverif](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-trailmark-skills-mermaid-to-proverif.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-trailmark-skills-mermaid-to-proverif`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-trailmark-skills-mermaid-to-proverif/SKILL.md`
- Source: [trailofbits/skills `plugins/trailmark/skills/mermaid-to-proverif/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/trailmark/skills/mermaid-to-proverif/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Translates Mermaid sequenceDiagrams describing cryptographic protocols into ProVerif formal verification models (.pv files). Use when generating a ProVerif model, formally verifying a protocol, converting a Mermaid diagram to ProVerif, verifying protocol security properties (secrecy, authentication, forward secrecy), checking for replay attacks, or producing a .pv file from a sequence diagram.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Mermaid to ProVerif, When to Use, When NOT to Use, Rationalizations to Reject, Workflow. Resources: has_references, has_examples.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-trailmark-skills-mermaid-to-proverif-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/trailmark/skills/mermaid-to-proverif/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## trailmark - trailofbits/skills `plugins/trailmark/skills/trailmark/SKILL.md`

- Skill page: [trailofbits-skills-plugins-trailmark-skills-trailmark](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-trailmark-skills-trailmark.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-trailmark-skills-trailmark`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-trailmark-skills-trailmark/SKILL.md`
- Source: [trailofbits/skills `plugins/trailmark/skills/trailmark/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/trailmark/skills/trailmark/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Builds and queries multi-language source code graphs for security analysis. Includes pre-analysis passes for blast radius, taint propagation, privilege boundaries, and entry point enumeration. Use when analyzing call paths, mapping attack surface, finding complexity hotspots, enumerating entry points, tracing taint propagation, measuring blast radius, or building a code graph for audit prioritization. Supports 16.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Trailmark, When to Use, When NOT to Use, Rationalizations to Reject, Installation. Resources: has_references.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-trailmark-skills-trailmark-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/trailmark/skills/trailmark/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## variant-analysis - trailofbits/skills `plugins/variant-analysis/skills/variant-analysis/SKILL.md`

- Skill page: [trailofbits-skills-plugins-variant-analysis-skills-variant-analysis](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-variant-analysis-skills-variant-analysis.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-variant-analysis-skills-variant-analysis`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-variant-analysis-skills-variant-analysis/SKILL.md`
- Source: [trailofbits/skills `plugins/variant-analysis/skills/variant-analysis/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/variant-analysis/skills/variant-analysis/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Find similar vulnerabilities and bugs across codebases using pattern-based analysis. Use when hunting bug variants, building CodeQL/Semgrep queries, analyzing security vulnerabilities, or performing systematic code audits after finding an initial issue.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Variant Analysis, When to Use, When NOT to Use, The Five-Step Process, Step 1: Understand the Original Issue. Resources: none observed.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-variant-analysis-skills-variant-analysis-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/variant-analysis/skills/variant-analysis/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## yara-rule-authoring - trailofbits/skills `plugins/yara-authoring/skills/yara-rule-authoring/SKILL.md`

- Skill page: [trailofbits-skills-plugins-yara-authoring-skills-yara-rule-authoring](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-yara-authoring-skills-yara-rule-authoring.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-yara-authoring-skills-yara-rule-authoring`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-yara-authoring-skills-yara-rule-authoring/SKILL.md`
- Source: [trailofbits/skills `plugins/yara-authoring/skills/yara-rule-authoring/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/yara-authoring/skills/yara-rule-authoring/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Guides authoring of high-quality YARA-X detection rules for malware identification. Use when writing, reviewing, or optimizing YARA rules. Covers naming conventions, string selection, performance optimization, migration from legacy YARA, and false positive reduction. Triggers on: YARA, YARA-X, malware detection, threat hunting, IOC, signature, crx module, dex module.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: YARA-X Rule Authoring, Core Principles, When to Use, When NOT to Use, YARA-X Overview. Resources: has_scripts, has_references, has_examples.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Move long background material into references/ to keep SKILL.md concise.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-yara-authoring-skills-yara-rule-authoring-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/yara-authoring/skills/yara-rule-authoring/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

## zeroize-audit - trailofbits/skills `plugins/zeroize-audit/skills/zeroize-audit/SKILL.md`

- Skill page: [trailofbits-skills-plugins-zeroize-audit-skills-zeroize-audit](../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-zeroize-audit-skills-zeroize-audit.md)
- Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-zeroize-audit-skills-zeroize-audit`
- Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-zeroize-audit-skills-zeroize-audit/SKILL.md`
- Source: [trailofbits/skills `plugins/zeroize-audit/skills/zeroize-audit/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/zeroize-audit/skills/zeroize-audit/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Detects missing zeroization of sensitive data in source code and identifies zeroization removed by compiler optimizations, with assembly-level analysis, and control-flow verification. Use for auditing C/C++/Rust code handling secrets, keys, passwords, or other sensitive data.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: zeroize-audit — Claude Skill, When to Use, When NOT to Use, Purpose, Scope. Resources: has_references.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
  - Add an executable validator or helper script so the workflow has objective checks.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-zeroize-audit-skills-zeroize-audit-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/zeroize-audit/skills/zeroize-audit/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
  - `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
  - `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.
